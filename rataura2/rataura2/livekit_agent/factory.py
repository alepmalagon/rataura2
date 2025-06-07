"""
Factory for creating Livekit agents from database models.
"""
from typing import Dict, List, Optional, Any, Type
import logging
from sqlalchemy.orm import Session

from livekit.agents import Agent as LivekitAgent
from livekit.plugins import google, silero

from rataura2.db.models import Agent, Conversation, Tool
from rataura2.graph.manager import AgentGraphManager

logger = logging.getLogger(__name__)


class AgentFactory:
    """
    Factory for creating Livekit agents from database models.
    """
    
    def __init__(self, db: Session):
        """
        Initialize the agent factory.
        
        Args:
            db: SQLAlchemy database session
        """
        self.db = db
    
    def create_agent(self, agent_id: int) -> LivekitAgent:
        """
        Create a Livekit agent from a database agent model.
        
        Args:
            agent_id: ID of the agent to create
            
        Returns:
            LivekitAgent: A Livekit agent instance
        """
        # Get the agent from the database
        agent = self.db.query(Agent).filter(Agent.id == agent_id).first()
        if not agent:
            raise ValueError(f"Agent with ID {agent_id} not found")
        
        # Get the agent's tools
        tools = agent.tools
        
        # Create the agent
        logger.info(f"Creating agent {agent.name} with {len(tools)} tools")
        
        # Configure agent arguments based on the agent model
        agent_args = {
            "instructions": agent.instructions,
        }
        
        # Configure LLM provider
        if agent.llm_provider == "gemini":
            agent_args["llm"] = google.beta.realtime.RealtimeModel()
        elif agent.llm_provider == "openai":
            # This would be configured based on the agent's config
            # For now, we're just using a placeholder
            from livekit.plugins import openai
            agent_args["llm"] = openai.ChatModel()
        elif agent.llm_provider == "anthropic":
            # This would be configured based on the agent's config
            # For now, we're just using a placeholder
            from livekit.plugins import anthropic
            agent_args["llm"] = anthropic.ChatModel()
        
        # Configure STT provider if not "none"
        if agent.stt_provider != "none":
            if agent.stt_provider == "google":
                from livekit.plugins import google
                agent_args["stt"] = google.STT()
            elif agent.stt_provider == "deepgram":
                from livekit.plugins import deepgram
                agent_args["stt"] = deepgram.STT()
            elif agent.stt_provider == "whisper":
                from livekit.plugins import openai
                agent_args["stt"] = openai.WhisperSTT()
        
        # Configure TTS provider if not "none"
        if agent.tts_provider != "none":
            if agent.tts_provider == "google":
                from livekit.plugins import google
                agent_args["tts"] = google.TTS()
            elif agent.tts_provider == "elevenlabs":
                from livekit.plugins import elevenlabs
                agent_args["tts"] = elevenlabs.TTS()
        
        # Add VAD if voice is enabled
        if agent.stt_provider != "none" or agent.tts_provider != "none":
            agent_args["vad"] = silero.VAD.load()
        
        # Create the Livekit agent
        livekit_agent = DynamicAgent(**agent_args)
        
        # Add tools to the agent
        for tool in tools:
            # This would load the actual tool function from a registry
            # For now, we're just creating a placeholder
            livekit_agent.add_tool(tool.name, tool.function_name, tool.description)
        
        return livekit_agent
    
    def create_conversation(self, conversation_id: int) -> "ConversationController":
        """
        Create a conversation controller from a database conversation model.
        
        Args:
            conversation_id: ID of the conversation to create
            
        Returns:
            ConversationController: A conversation controller instance
        """
        # Get the conversation from the database
        conversation = self.db.query(Conversation).filter(Conversation.id == conversation_id).first()
        if not conversation:
            raise ValueError(f"Conversation with ID {conversation_id} not found")
        
        # Create the graph manager
        graph_manager = AgentGraphManager(conversation_id, self.db)
        
        # Create the conversation controller
        return ConversationController(conversation, graph_manager, self)


class DynamicAgent(LivekitAgent):
    """
    Dynamic agent that can be configured at runtime.
    """
    
    def __init__(self, **kwargs):
        """
        Initialize the dynamic agent.
        
        Args:
            **kwargs: Arguments to pass to the Livekit Agent constructor
        """
        super().__init__(**kwargs)
        self.tools = {}
    
    def add_tool(self, name: str, function_name: str, description: str = None):
        """
        Add a tool to the agent.
        
        Args:
            name: Name of the tool
            function_name: Name of the function to call
            description: Description of the tool
        """
        # In a real implementation, this would dynamically create and register
        # a function tool with the agent. For now, we're just storing the tool info.
        self.tools[name] = {
            "function_name": function_name,
            "description": description
        }
        logger.info(f"Added tool {name} to agent")


class ConversationController:
    """
    Controller for a conversation that manages transitions between agents.
    """
    
    def __init__(self, conversation: Conversation, graph_manager: AgentGraphManager, 
                 factory: AgentFactory):
        """
        Initialize the conversation controller.
        
        Args:
            conversation: Conversation model
            graph_manager: Graph manager for agent transitions
            factory: Agent factory for creating Livekit agents
        """
        self.conversation = conversation
        self.graph_manager = graph_manager
        self.factory = factory
        self.current_agent_id = conversation.initial_agent_id
        self.current_agent = None
        self.context = {}
        
        # Create the initial agent
        self._create_current_agent()
    
    def _create_current_agent(self):
        """Create the current agent."""
        self.current_agent = self.factory.create_agent(self.current_agent_id)
    
    def get_current_agent(self) -> LivekitAgent:
        """
        Get the current active agent.
        
        Returns:
            LivekitAgent: The current Livekit agent
        """
        return self.current_agent
    
    def update_context(self, key: str, value: Any):
        """
        Update the context with a new key-value pair.
        
        Args:
            key: Context key
            value: Context value
        """
        self.context[key] = value
    
    def check_transitions(self) -> bool:
        """
        Check if any transitions should be triggered based on the current context.
        
        Returns:
            bool: True if a transition was triggered, False otherwise
        """
        # Check for transitions
        next_agent_id = self.graph_manager.check_transitions(self.current_agent_id, self.context)
        
        if next_agent_id is not None and next_agent_id != self.current_agent_id:
            logger.info(f"Transitioning from agent {self.current_agent_id} to agent {next_agent_id}")
            self.current_agent_id = next_agent_id
            self._create_current_agent()
            return True
        
        return False

