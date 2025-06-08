"""
Event handling for Livekit agents.

This module provides classes and functions for handling Livekit events
and integrating them with the agent orchestration system.
"""
from typing import Dict, List, Any, Optional, Callable, Set, Type
import logging
import json
from enum import Enum
from dataclasses import dataclass

from livekit.agents import Agent as LivekitAgent
from livekit.agents.events import Event as LivekitEvent

logger = logging.getLogger(__name__)


class EventType(str, Enum):
    """Enumeration of event types that can trigger agent transitions."""
    # Session events
    SESSION_CREATED = "session_created"
    SESSION_ENDED = "session_ended"
    USER_JOINED = "user_joined"
    USER_LEFT = "user_left"
    
    # Agent events
    AGENT_STARTED = "agent_started"
    AGENT_STOPPED = "agent_stopped"
    AGENT_ERROR = "agent_error"
    
    # Conversation events
    USER_MESSAGE = "user_message"
    AGENT_MESSAGE = "agent_message"
    TOOL_CALLED = "tool_called"
    TOOL_RESULT = "tool_result"
    
    # Custom events
    CUSTOM = "custom"


@dataclass
class EventData:
    """Data structure for event information."""
    type: EventType
    timestamp: float
    data: Dict[str, Any]
    source: str  # 'session', 'agent', 'user', etc.


class EventHandler:
    """
    Base class for event handlers.
    
    Event handlers process events and update the context object.
    """
    
    def __init__(self):
        """Initialize the event handler."""
        self.callbacks: Dict[EventType, List[Callable[[EventData, Dict[str, Any]], None]]] = {}
    
    def register_callback(self, event_type: EventType, 
                         callback: Callable[[EventData, Dict[str, Any]], None]) -> None:
        """
        Register a callback for a specific event type.
        
        Args:
            event_type: Type of event to register for
            callback: Function to call when the event occurs
        """
        if event_type not in self.callbacks:
            self.callbacks[event_type] = []
        
        self.callbacks[event_type].append(callback)
    
    def handle_event(self, event: EventData, context: Dict[str, Any]) -> None:
        """
        Handle an event by updating the context and calling registered callbacks.
        
        Args:
            event: Event data
            context: Context object to update
        """
        # Add the event to the context
        if "events" not in context:
            context["events"] = []
        
        # Add the event to the events list
        context["events"].append({
            "type": event.type,
            "timestamp": event.timestamp,
            "data": event.data,
            "source": event.source
        })
        
        # Limit the events list to the last 100 events
        context["events"] = context["events"][-100:]
        
        # Call registered callbacks
        if event.type in self.callbacks:
            for callback in self.callbacks[event.type]:
                try:
                    callback(event, context)
                except Exception as e:
                    logger.error(f"Error in event callback: {e}")


class LivekitEventHandler(EventHandler):
    """
    Handler for Livekit events.
    
    This class processes Livekit events and converts them to the internal
    event format used by the agent orchestration system.
    """
    
    def __init__(self):
        """Initialize the Livekit event handler."""
        super().__init__()
        self.event_mapping = self._create_event_mapping()
    
    def _create_event_mapping(self) -> Dict[str, EventType]:
        """
        Create a mapping from Livekit event types to internal event types.
        
        Returns:
            Dict[str, EventType]: Mapping from Livekit event types to internal event types
        """
        # This mapping would be based on the actual Livekit event types
        # For now, we're using placeholder mappings
        return {
            "session:created": EventType.SESSION_CREATED,
            "session:ended": EventType.SESSION_ENDED,
            "participant:joined": EventType.USER_JOINED,
            "participant:left": EventType.USER_LEFT,
            "agent:started": EventType.AGENT_STARTED,
            "agent:stopped": EventType.AGENT_STOPPED,
            "agent:error": EventType.AGENT_ERROR,
            "message:received": EventType.USER_MESSAGE,
            "message:sent": EventType.AGENT_MESSAGE,
            "tool:called": EventType.TOOL_CALLED,
            "tool:result": EventType.TOOL_RESULT,
        }
    
    def process_livekit_event(self, livekit_event: LivekitEvent, context: Dict[str, Any]) -> None:
        """
        Process a Livekit event and update the context.
        
        Args:
            livekit_event: Livekit event to process
            context: Context object to update
        """
        # Extract event type and data from the Livekit event
        event_type_str = getattr(livekit_event, "type", "unknown")
        
        # Map the Livekit event type to our internal event type
        event_type = self.event_mapping.get(event_type_str, EventType.CUSTOM)
        
        # Extract event data
        event_data = {}
        for key, value in vars(livekit_event).items():
            if key != "type" and not key.startswith("_"):
                event_data[key] = value
        
        # Create an internal event
        event = EventData(
            type=event_type,
            timestamp=getattr(livekit_event, "timestamp", 0.0),
            data=event_data,
            source="livekit"
        )
        
        # Handle the event
        self.handle_event(event, context)


class SessionEventHandler(EventHandler):
    """
    Handler for session events.
    
    This class processes session-related events and updates the context
    with session information.
    """
    
    def __init__(self):
        """Initialize the session event handler."""
        super().__init__()
        
        # Register callbacks for session events
        self.register_callback(EventType.SESSION_CREATED, self._handle_session_created)
        self.register_callback(EventType.SESSION_ENDED, self._handle_session_ended)
        self.register_callback(EventType.USER_JOINED, self._handle_user_joined)
        self.register_callback(EventType.USER_LEFT, self._handle_user_left)
    
    def _handle_session_created(self, event: EventData, context: Dict[str, Any]) -> None:
        """
        Handle a session created event.
        
        Args:
            event: Event data
            context: Context object to update
        """
        # Update the context with session information
        context["session"] = {
            "id": event.data.get("session_id", "unknown"),
            "created_at": event.timestamp,
            "active": True,
            "participants": []
        }
    
    def _handle_session_ended(self, event: EventData, context: Dict[str, Any]) -> None:
        """
        Handle a session ended event.
        
        Args:
            event: Event data
            context: Context object to update
        """
        # Update the session status
        if "session" in context:
            context["session"]["active"] = False
            context["session"]["ended_at"] = event.timestamp
    
    def _handle_user_joined(self, event: EventData, context: Dict[str, Any]) -> None:
        """
        Handle a user joined event.
        
        Args:
            event: Event data
            context: Context object to update
        """
        # Add the user to the session participants
        if "session" in context:
            participant = {
                "id": event.data.get("participant_id", "unknown"),
                "name": event.data.get("participant_name", "unknown"),
                "joined_at": event.timestamp
            }
            
            if "participants" not in context["session"]:
                context["session"]["participants"] = []
            
            context["session"]["participants"].append(participant)
    
    def _handle_user_left(self, event: EventData, context: Dict[str, Any]) -> None:
        """
        Handle a user left event.
        
        Args:
            event: Event data
            context: Context object to update
        """
        # Update the participant status
        if "session" in context and "participants" in context["session"]:
            participant_id = event.data.get("participant_id", "unknown")
            
            for participant in context["session"]["participants"]:
                if participant["id"] == participant_id:
                    participant["active"] = False
                    participant["left_at"] = event.timestamp
                    break


class AgentEventHandler(EventHandler):
    """
    Handler for agent events.
    
    This class processes agent-related events and updates the context
    with agent information.
    """
    
    def __init__(self):
        """Initialize the agent event handler."""
        super().__init__()
        
        # Register callbacks for agent events
        self.register_callback(EventType.AGENT_STARTED, self._handle_agent_started)
        self.register_callback(EventType.AGENT_STOPPED, self._handle_agent_stopped)
        self.register_callback(EventType.AGENT_ERROR, self._handle_agent_error)
        self.register_callback(EventType.USER_MESSAGE, self._handle_user_message)
        self.register_callback(EventType.AGENT_MESSAGE, self._handle_agent_message)
        self.register_callback(EventType.TOOL_CALLED, self._handle_tool_called)
        self.register_callback(EventType.TOOL_RESULT, self._handle_tool_result)
    
    def _handle_agent_started(self, event: EventData, context: Dict[str, Any]) -> None:
        """
        Handle an agent started event.
        
        Args:
            event: Event data
            context: Context object to update
        """
        # Update the context with agent information
        agent_id = event.data.get("agent_id", "unknown")
        agent_name = event.data.get("agent_name", "unknown")
        
        if "agents" not in context:
            context["agents"] = {}
        
        context["agents"][agent_id] = {
            "id": agent_id,
            "name": agent_name,
            "started_at": event.timestamp,
            "active": True,
            "messages": [],
            "tools": []
        }
        
        # Update the current agent
        context["current_agent_id"] = agent_id
        context["current_agent_name"] = agent_name
    
    def _handle_agent_stopped(self, event: EventData, context: Dict[str, Any]) -> None:
        """
        Handle an agent stopped event.
        
        Args:
            event: Event data
            context: Context object to update
        """
        # Update the agent status
        agent_id = event.data.get("agent_id", "unknown")
        
        if "agents" in context and agent_id in context["agents"]:
            context["agents"][agent_id]["active"] = False
            context["agents"][agent_id]["stopped_at"] = event.timestamp
    
    def _handle_agent_error(self, event: EventData, context: Dict[str, Any]) -> None:
        """
        Handle an agent error event.
        
        Args:
            event: Event data
            context: Context object to update
        """
        # Update the agent status
        agent_id = event.data.get("agent_id", "unknown")
        error = event.data.get("error", "Unknown error")
        
        if "agents" in context and agent_id in context["agents"]:
            if "errors" not in context["agents"][agent_id]:
                context["agents"][agent_id]["errors"] = []
            
            context["agents"][agent_id]["errors"].append({
                "timestamp": event.timestamp,
                "error": error
            })
    
    def _handle_user_message(self, event: EventData, context: Dict[str, Any]) -> None:
        """
        Handle a user message event.
        
        Args:
            event: Event data
            context: Context object to update
        """
        # Update the context with the user message
        message = event.data.get("message", "")
        
        # Add to the conversation history
        if "conversation" not in context:
            context["conversation"] = []
        
        context["conversation"].append({
            "role": "user",
            "content": message,
            "timestamp": event.timestamp
        })
        
        # Update the user input for transition conditions
        context["user_input"] = message
        
        # Update the turn count
        if "turn_count" not in context:
            context["turn_count"] = 0
        
        context["turn_count"] += 1
    
    def _handle_agent_message(self, event: EventData, context: Dict[str, Any]) -> None:
        """
        Handle an agent message event.
        
        Args:
            event: Event data
            context: Context object to update
        """
        # Update the context with the agent message
        agent_id = event.data.get("agent_id", "unknown")
        message = event.data.get("message", "")
        
        # Add to the conversation history
        if "conversation" not in context:
            context["conversation"] = []
        
        context["conversation"].append({
            "role": "assistant",
            "content": message,
            "timestamp": event.timestamp,
            "agent_id": agent_id
        })
        
        # Add to the agent's messages
        if "agents" in context and agent_id in context["agents"]:
            if "messages" not in context["agents"][agent_id]:
                context["agents"][agent_id]["messages"] = []
            
            context["agents"][agent_id]["messages"].append({
                "content": message,
                "timestamp": event.timestamp
            })
    
    def _handle_tool_called(self, event: EventData, context: Dict[str, Any]) -> None:
        """
        Handle a tool called event.
        
        Args:
            event: Event data
            context: Context object to update
        """
        # Update the context with the tool call
        agent_id = event.data.get("agent_id", "unknown")
        tool_name = event.data.get("tool_name", "unknown")
        tool_input = event.data.get("tool_input", {})
        
        # Add to the agent's tools
        if "agents" in context and agent_id in context["agents"]:
            if "tools" not in context["agents"][agent_id]:
                context["agents"][agent_id]["tools"] = []
            
            tool_call = {
                "name": tool_name,
                "input": tool_input,
                "timestamp": event.timestamp,
                "status": "called"
            }
            
            context["agents"][agent_id]["tools"].append(tool_call)
            
            # Update the last tool name
            context["last_tool_name"] = tool_name
            context["last_tool_input"] = tool_input
    
    def _handle_tool_result(self, event: EventData, context: Dict[str, Any]) -> None:
        """
        Handle a tool result event.
        
        Args:
            event: Event data
            context: Context object to update
        """
        # Update the context with the tool result
        agent_id = event.data.get("agent_id", "unknown")
        tool_name = event.data.get("tool_name", "unknown")
        tool_result = event.data.get("tool_result", {})
        
        # Update the agent's tool call
        if "agents" in context and agent_id in context["agents"]:
            if "tools" in context["agents"][agent_id]:
                # Find the matching tool call
                for tool_call in reversed(context["agents"][agent_id]["tools"]):
                    if tool_call["name"] == tool_name and tool_call["status"] == "called":
                        tool_call["result"] = tool_result
                        tool_call["status"] = "completed"
                        tool_call["completed_at"] = event.timestamp
                        break
        
        # Add to the tool results
        if "tool_results" not in context:
            context["tool_results"] = {}
        
        if tool_name not in context["tool_results"]:
            context["tool_results"][tool_name] = []
        
        context["tool_results"][tool_name].append(tool_result)
        
        # Update the last tool result
        context["last_tool_result"] = tool_result


class EventManager:
    """
    Manager for event handlers.
    
    This class coordinates multiple event handlers and provides a single
    interface for processing events.
    """
    
    def __init__(self):
        """Initialize the event manager."""
        self.handlers: Dict[str, EventHandler] = {}
        self.context: Dict[str, Any] = {}
    
    def register_handler(self, name: str, handler: EventHandler) -> None:
        """
        Register an event handler.
        
        Args:
            name: Name of the handler
            handler: Event handler instance
        """
        self.handlers[name] = handler
    
    def process_event(self, event: EventData) -> None:
        """
        Process an event using all registered handlers.
        
        Args:
            event: Event data
        """
        for handler in self.handlers.values():
            handler.handle_event(event, self.context)
    
    def process_livekit_event(self, livekit_event: LivekitEvent) -> None:
        """
        Process a Livekit event.
        
        Args:
            livekit_event: Livekit event to process
        """
        # Find the Livekit event handler
        for handler in self.handlers.values():
            if isinstance(handler, LivekitEventHandler):
                handler.process_livekit_event(livekit_event, self.context)
                break
    
    def get_context(self) -> Dict[str, Any]:
        """
        Get the current context.
        
        Returns:
            Dict[str, Any]: Current context
        """
        return self.context
    
    def update_context(self, key: str, value: Any) -> None:
        """
        Update the context with a new key-value pair.
        
        Args:
            key: Context key
            value: Context value
        """
        self.context[key] = value
    
    def clear_context(self) -> None:
        """Clear the context."""
        self.context = {}
"""

