"""
Agent orchestration for managing transitions between agents.

This module provides the main orchestration logic for managing agent transitions
based on events and business rules.
"""
from typing import Dict, List, Optional, Any, Callable, Set, Type
import logging
import time
import threading
from enum import Enum

from sqlalchemy.orm import Session

from livekit.agents import Agent as LivekitAgent
from livekit.agents.events import Event as LivekitEvent

from rataura2.db.models import Agent, Conversation
from rataura2.graph.manager import AgentGraphManager
from rataura2.graph.business_rules_integration import BusinessRulesAgentGraphManager
from rataura2.livekit_agent.factory import AgentFactory, ConversationController, DynamicAgent
from rataura2.livekit_agent.events import (
    EventManager, EventHandler, LivekitEventHandler, 
    SessionEventHandler, AgentEventHandler, EventData, EventType
)

logger = logging.getLogger(__name__)


class TransitionResult(str, Enum):
    """Enumeration of transition result types."""
    SUCCESS = "success"
    NO_TRANSITION = "no_transition"
    ERROR = "error"


class AgentOrchestrator:
    """
    Orchestrator for managing agent transitions.
    
    This class coordinates the event system, graph manager, and agent factory
    to manage transitions between agents based on events and business rules.
    """
    
    def __init__(self, db: Session, conversation_id: int, use_business_rules: bool = True):
        """
        Initialize the agent orchestrator.
        
        Args:
            db: SQLAlchemy database session
            conversation_id: ID of the conversation to orchestrate
            use_business_rules: Whether to use business rules for transitions
        """
        self.db = db
        self.conversation_id = conversation_id
        
        # Create the graph manager
        if use_business_rules:
            self.graph_manager = BusinessRulesAgentGraphManager(conversation_id, db)
        else:
            self.graph_manager = AgentGraphManager(conversation_id, db)
        
        # Create the agent factory
        self.agent_factory = AgentFactory(db)
        
        # Create the conversation controller
        self.conversation = self.db.query(Conversation).filter(
            Conversation.id == conversation_id
        ).first()
        
        if not self.conversation:
            raise ValueError(f"Conversation with ID {conversation_id} not found")
        
        self.controller = ConversationController(
            self.conversation, self.graph_manager, self.agent_factory
        )
        
        # Create the event manager
        self.event_manager = EventManager()
        
        # Register event handlers
        self.event_manager.register_handler("livekit", LivekitEventHandler())
        self.event_manager.register_handler("session", SessionEventHandler())
        self.event_manager.register_handler("agent", AgentEventHandler())
        
        # Initialize the context
        self._initialize_context()
        
        # Set up transition checking
        self._setup_transition_checking()
        
        # Flag to track if the orchestrator is running
        self.running = False
        
        # Lock for thread safety
        self.lock = threading.Lock()
        
        # Transition check thread
        self.transition_check_thread = None
        self.transition_check_interval = 1.0  # seconds
    
    def _initialize_context(self) -> None:
        """Initialize the context with conversation and agent information."""
        context = self.event_manager.get_context()
        
        # Add conversation information
        context["conversation_id"] = self.conversation_id
        context["conversation_name"] = self.conversation.name
        context["conversation_description"] = self.conversation.description
        
        # Add initial agent information
        initial_agent = self.graph_manager.get_initial_agent()
        context["initial_agent_id"] = initial_agent.id
        context["initial_agent_name"] = initial_agent.name
        context["current_agent_id"] = initial_agent.id
        context["current_agent_name"] = initial_agent.name
        
        # Initialize other context fields
        context["turn_count"] = 0
        context["events"] = []
        context["tool_results"] = {}
        context["agent_decisions"] = {}
        
        # Update the controller's context
        self.controller.context = context
    
    def _setup_transition_checking(self) -> None:
        """Set up callbacks for checking transitions after relevant events."""
        # Get the agent event handler
        agent_handler = None
        for name, handler in self.event_manager.handlers.items():
            if isinstance(handler, AgentEventHandler):
                agent_handler = handler
                break
        
        if agent_handler:
            # Register callbacks for events that should trigger transition checks
            agent_handler.register_callback(
                EventType.USER_MESSAGE, self._check_transition_after_event
            )
            agent_handler.register_callback(
                EventType.TOOL_RESULT, self._check_transition_after_event
            )
            agent_handler.register_callback(
                EventType.AGENT_MESSAGE, self._check_transition_after_event
            )
    
    def _check_transition_after_event(self, event: EventData, context: Dict[str, Any]) -> None:
        """
        Check for transitions after an event.
        
        Args:
            event: Event data
            context: Context object
        """
        # Check for transitions
        self.check_and_execute_transition()
    
    def start(self) -> None:
        """Start the orchestrator."""
        with self.lock:
            if self.running:
                return
            
            self.running = True
            
            # Start the transition check thread
            self.transition_check_thread = threading.Thread(
                target=self._transition_check_loop,
                daemon=True
            )
            self.transition_check_thread.start()
            
            logger.info(f"Started orchestrator for conversation {self.conversation_id}")
    
    def stop(self) -> None:
        """Stop the orchestrator."""
        with self.lock:
            if not self.running:
                return
            
            self.running = False
            
            # Wait for the transition check thread to stop
            if self.transition_check_thread:
                self.transition_check_thread.join(timeout=5.0)
                self.transition_check_thread = None
            
            logger.info(f"Stopped orchestrator for conversation {self.conversation_id}")
    
    def _transition_check_loop(self) -> None:
        """Background thread for periodically checking transitions."""
        while self.running:
            try:
                # Check for transitions
                self.check_and_execute_transition()
                
                # Sleep for the check interval
                time.sleep(self.transition_check_interval)
            except Exception as e:
                logger.error(f"Error in transition check loop: {e}")
    
    def process_livekit_event(self, livekit_event: LivekitEvent) -> None:
        """
        Process a Livekit event.
        
        Args:
            livekit_event: Livekit event to process
        """
        # Process the event
        self.event_manager.process_livekit_event(livekit_event)
    
    def process_event(self, event: EventData) -> None:
        """
        Process an event.
        
        Args:
            event: Event data to process
        """
        # Process the event
        self.event_manager.process_event(event)
    
    def check_transition(self) -> Optional[int]:
        """
        Check if a transition should be triggered.
        
        Returns:
            Optional[int]: ID of the target agent if a transition should be triggered, None otherwise
        """
        # Get the current context
        context = self.event_manager.get_context()
        
        # Get the current agent ID
        current_agent_id = context.get("current_agent_id")
        if not current_agent_id:
            return None
        
        # Check for transitions
        return self.graph_manager.check_transitions(current_agent_id, context)
    
    def execute_transition(self, target_agent_id: int) -> TransitionResult:
        """
        Execute a transition to a new agent.
        
        Args:
            target_agent_id: ID of the target agent
        
        Returns:
            TransitionResult: Result of the transition
        """
        try:
            # Get the current context
            context = self.event_manager.get_context()
            
            # Get the current agent ID
            current_agent_id = context.get("current_agent_id")
            if not current_agent_id:
                return TransitionResult.ERROR
            
            # Skip if the target is the same as the current agent
            if target_agent_id == current_agent_id:
                return TransitionResult.NO_TRANSITION
            
            # Get the target agent
            target_agent = self.db.query(Agent).filter(Agent.id == target_agent_id).first()
            if not target_agent:
                logger.error(f"Target agent with ID {target_agent_id} not found")
                return TransitionResult.ERROR
            
            # Log the transition
            logger.info(f"Transitioning from agent {current_agent_id} to agent {target_agent_id}")
            
            # Update the context
            context["previous_agent_id"] = current_agent_id
            context["current_agent_id"] = target_agent_id
            context["current_agent_name"] = target_agent.name
            
            # Create an event for the transition
            transition_event = EventData(
                type=EventType.CUSTOM,
                timestamp=time.time(),
                data={
                    "previous_agent_id": current_agent_id,
                    "target_agent_id": target_agent_id,
                    "transition_type": "orchestrator"
                },
                source="orchestrator"
            )
            
            # Process the transition event
            self.event_manager.process_event(transition_event)
            
            # Update the controller
            self.controller.current_agent_id = target_agent_id
            self.controller.context = context
            self.controller._create_current_agent()
            
            return TransitionResult.SUCCESS
        
        except Exception as e:
            logger.error(f"Error executing transition: {e}")
            return TransitionResult.ERROR
    
    def check_and_execute_transition(self) -> TransitionResult:
        """
        Check for and execute a transition if needed.
        
        Returns:
            TransitionResult: Result of the transition check and execution
        """
        # Check for transitions
        target_agent_id = self.check_transition()
        
        # If a transition is needed, execute it
        if target_agent_id is not None:
            return self.execute_transition(target_agent_id)
        
        return TransitionResult.NO_TRANSITION
    
    def get_current_agent(self) -> LivekitAgent:
        """
        Get the current active agent.
        
        Returns:
            LivekitAgent: The current Livekit agent
        """
        return self.controller.get_current_agent()
    
    def get_context(self) -> Dict[str, Any]:
        """
        Get the current context.
        
        Returns:
            Dict[str, Any]: Current context
        """
        return self.event_manager.get_context()
    
    def update_context(self, key: str, value: Any) -> None:
        """
        Update the context with a new key-value pair.
        
        Args:
            key: Context key
            value: Context value
        """
        self.event_manager.update_context(key, value)
        self.controller.context = self.event_manager.get_context()


class SessionManager:
    """
    Manager for active sessions.
    
    This class manages active sessions and their associated orchestrators.
    """
    
    def __init__(self, db: Session):
        """
        Initialize the session manager.
        
        Args:
            db: SQLAlchemy database session
        """
        self.db = db
        self.orchestrators: Dict[str, AgentOrchestrator] = {}
        self.session_to_conversation: Dict[str, int] = {}
        self.lock = threading.Lock()
    
    def create_session(self, session_id: str, conversation_id: int) -> AgentOrchestrator:
        """
        Create a new session.
        
        Args:
            session_id: ID of the session
            conversation_id: ID of the conversation
        
        Returns:
            AgentOrchestrator: The orchestrator for the session
        """
        with self.lock:
            # Check if the session already exists
            if session_id in self.orchestrators:
                return self.orchestrators[session_id]
            
            # Create a new orchestrator
            orchestrator = AgentOrchestrator(self.db, conversation_id)
            
            # Store the orchestrator
            self.orchestrators[session_id] = orchestrator
            self.session_to_conversation[session_id] = conversation_id
            
            # Start the orchestrator
            orchestrator.start()
            
            # Create a session created event
            event = EventData(
                type=EventType.SESSION_CREATED,
                timestamp=time.time(),
                data={"session_id": session_id, "conversation_id": conversation_id},
                source="session_manager"
            )
            
            # Process the event
            orchestrator.process_event(event)
            
            return orchestrator
    
    def get_orchestrator(self, session_id: str) -> Optional[AgentOrchestrator]:
        """
        Get the orchestrator for a session.
        
        Args:
            session_id: ID of the session
        
        Returns:
            Optional[AgentOrchestrator]: The orchestrator for the session, or None if not found
        """
        with self.lock:
            return self.orchestrators.get(session_id)
    
    def end_session(self, session_id: str) -> bool:
        """
        End a session.
        
        Args:
            session_id: ID of the session
        
        Returns:
            bool: True if the session was ended, False if it wasn't found
        """
        with self.lock:
            # Check if the session exists
            if session_id not in self.orchestrators:
                return False
            
            # Get the orchestrator
            orchestrator = self.orchestrators[session_id]
            
            # Create a session ended event
            event = EventData(
                type=EventType.SESSION_ENDED,
                timestamp=time.time(),
                data={"session_id": session_id},
                source="session_manager"
            )
            
            # Process the event
            orchestrator.process_event(event)
            
            # Stop the orchestrator
            orchestrator.stop()
            
            # Remove the orchestrator
            del self.orchestrators[session_id]
            del self.session_to_conversation[session_id]
            
            return True
    
    def process_livekit_event(self, session_id: str, livekit_event: LivekitEvent) -> bool:
        """
        Process a Livekit event for a session.
        
        Args:
            session_id: ID of the session
            livekit_event: Livekit event to process
        
        Returns:
            bool: True if the event was processed, False if the session wasn't found
        """
        with self.lock:
            # Check if the session exists
            if session_id not in self.orchestrators:
                return False
            
            # Get the orchestrator
            orchestrator = self.orchestrators[session_id]
            
            # Process the event
            orchestrator.process_livekit_event(livekit_event)
            
            return True
    
    def get_active_sessions(self) -> List[str]:
        """
        Get the IDs of all active sessions.
        
        Returns:
            List[str]: List of active session IDs
        """
        with self.lock:
            return list(self.orchestrators.keys())
    
    def shutdown(self) -> None:
        """Shut down all orchestrators."""
        with self.lock:
            # End all sessions
            for session_id in list(self.orchestrators.keys()):
                self.end_session(session_id)
"""

