"""
Agent models for SQLAlchemy ORM.
"""
from enum import Enum
from typing import Dict, List, Optional, Any, Set
import json

from sqlalchemy import Column, String, Integer, Boolean, ForeignKey, Text, JSON, Table
from sqlalchemy.orm import Mapped, mapped_column, relationship
from pydantic import BaseModel as PydanticBaseModel, Field, validator

from rataura2.db.models.base import BaseModel


class AgentType(str, Enum):
    """Enumeration of agent types."""
    GENERAL = "general"
    COMBAT = "combat"
    INDUSTRY = "industry"
    MARKET = "market"
    EXPLORATION = "exploration"
    FACTION_WARFARE = "faction_warfare"
    CORPORATION = "corporation"
    ALLIANCE = "alliance"
    CUSTOM = "custom"


class LLMProvider(str, Enum):
    """Enumeration of LLM providers."""
    GEMINI = "gemini"
    OPENAI = "openai"
    ANTHROPIC = "anthropic"
    CUSTOM = "custom"


class STTProvider(str, Enum):
    """Enumeration of Speech-to-Text providers."""
    GOOGLE = "google"
    DEEPGRAM = "deepgram"
    WHISPER = "whisper"
    NONE = "none"


class TTSProvider(str, Enum):
    """Enumeration of Text-to-Speech providers."""
    GOOGLE = "google"
    ELEVENLABS = "elevenlabs"
    NONE = "none"


# Association table for many-to-many relationship between Agent and Tool
agent_tool_association = Table(
    "agent_tool_association",
    BaseModel.metadata,
    Column("agent_id", Integer, ForeignKey("Agent.id"), primary_key=True),
    Column("tool_id", Integer, ForeignKey("Tool.id"), primary_key=True)
)


class Tool(BaseModel):
    """Model for a tool that can be used by an agent."""
    
    __tablename__ = "Tool"
    
    name: Mapped[str] = mapped_column(String(255), nullable=False, unique=True)
    description: Mapped[str] = mapped_column(Text, nullable=True)
    function_name: Mapped[str] = mapped_column(String(255), nullable=False)
    parameters_schema: Mapped[Dict] = mapped_column(JSON, nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    
    # Relationships
    agents: Mapped[List["Agent"]] = relationship(
        "Agent",
        secondary=agent_tool_association,
        back_populates="tools"
    )
    
    transitions: Mapped[List["Transition"]] = relationship(
        "Transition",
        back_populates="tool",
        cascade="all, delete-orphan"
    )


class Agent(BaseModel):
    """Model for an agent that can be used in a conversation."""
    
    __tablename__ = "Agent"
    
    name: Mapped[str] = mapped_column(String(255), nullable=False, unique=True)
    description: Mapped[str] = mapped_column(Text, nullable=True)
    instructions: Mapped[str] = mapped_column(Text, nullable=False)
    agent_type: Mapped[str] = mapped_column(String(50), nullable=False, default=AgentType.GENERAL.value)
    llm_provider: Mapped[str] = mapped_column(String(50), nullable=False, default=LLMProvider.GEMINI.value)
    llm_model: Mapped[str] = mapped_column(String(255), nullable=False, default="flash")
    stt_provider: Mapped[str] = mapped_column(String(50), nullable=False, default=STTProvider.NONE.value)
    tts_provider: Mapped[str] = mapped_column(String(50), nullable=False, default=TTSProvider.NONE.value)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    
    # Additional configuration options stored as JSON
    config: Mapped[Dict] = mapped_column(JSON, nullable=True)
    
    # Relationships
    tools: Mapped[List[Tool]] = relationship(
        "Tool",
        secondary=agent_tool_association,
        back_populates="agents"
    )
    
    # Relationships for directed graph
    outgoing_transitions: Mapped[List["Transition"]] = relationship(
        "Transition",
        foreign_keys="[Transition.source_agent_id]",
        back_populates="source_agent",
        cascade="all, delete-orphan"
    )
    
    incoming_transitions: Mapped[List["Transition"]] = relationship(
        "Transition",
        foreign_keys="[Transition.target_agent_id]",
        back_populates="target_agent"
    )
    
    # Relationship to Conversation
    conversations: Mapped[List["Conversation"]] = relationship(
        "Conversation",
        secondary="conversation_agent_association",
        back_populates="agents"
    )


class TransitionConditionType(str, Enum):
    """Enumeration of transition condition types."""
    TOOL_RESULT = "tool_result"
    USER_INPUT = "user_input"
    AGENT_DECISION = "agent_decision"
    EVENT = "event"
    CUSTOM = "custom"


class Transition(BaseModel):
    """Model for a transition between agents in a directed graph."""
    
    __tablename__ = "Transition"
    
    source_agent_id: Mapped[int] = mapped_column(Integer, ForeignKey("Agent.id"), nullable=False)
    target_agent_id: Mapped[int] = mapped_column(Integer, ForeignKey("Agent.id"), nullable=False)
    condition_type: Mapped[str] = mapped_column(String(50), nullable=False)
    condition_data: Mapped[Dict] = mapped_column(JSON, nullable=True)
    priority: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=True)
    
    # Optional tool that triggers this transition
    tool_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey("Tool.id"), nullable=True)
    
    # Relationships
    source_agent: Mapped[Agent] = relationship(
        "Agent", 
        foreign_keys=[source_agent_id],
        back_populates="outgoing_transitions"
    )
    
    target_agent: Mapped[Agent] = relationship(
        "Agent", 
        foreign_keys=[target_agent_id],
        back_populates="incoming_transitions"
    )
    
    tool: Mapped[Optional[Tool]] = relationship(
        "Tool",
        back_populates="transitions"
    )


# Association table for many-to-many relationship between Conversation and Agent
conversation_agent_association = Table(
    "conversation_agent_association",
    BaseModel.metadata,
    Column("conversation_id", Integer, ForeignKey("Conversation.id"), primary_key=True),
    Column("agent_id", Integer, ForeignKey("Agent.id"), primary_key=True)
)


class Conversation(BaseModel):
    """
    Model for a conversation that represents a collection of agents connected by transitions.
    This is the agent experienced from the user's perspective when simple agents are cycled
    using directed graphs.
    """
    
    __tablename__ = "Conversation"
    
    name: Mapped[str] = mapped_column(String(255), nullable=False, unique=True)
    description: Mapped[str] = mapped_column(Text, nullable=True)
    initial_agent_id: Mapped[int] = mapped_column(Integer, ForeignKey("Agent.id"), nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    
    # Additional configuration options stored as JSON
    config: Mapped[Dict] = mapped_column(JSON, nullable=True)
    
    # Relationships
    initial_agent: Mapped[Agent] = relationship("Agent", foreign_keys=[initial_agent_id])
    
    agents: Mapped[List[Agent]] = relationship(
        "Agent",
        secondary=conversation_agent_association,
        back_populates="conversations"
    )


# Pydantic models for validation and serialization

class ToolSchema(PydanticBaseModel):
    """Pydantic model for Tool validation and serialization."""
    
    id: Optional[int] = None
    name: str
    description: Optional[str] = None
    function_name: str
    parameters_schema: Optional[Dict[str, Any]] = None
    is_active: bool = True
    
    class Config:
        orm_mode = True


class TransitionSchema(PydanticBaseModel):
    """Pydantic model for Transition validation and serialization."""
    
    id: Optional[int] = None
    source_agent_id: int
    target_agent_id: int
    condition_type: str
    condition_data: Optional[Dict[str, Any]] = None
    priority: int = 0
    description: Optional[str] = None
    tool_id: Optional[int] = None
    
    class Config:
        orm_mode = True
        
    @validator('condition_type')
    def validate_condition_type(cls, v):
        if v not in [t.value for t in TransitionConditionType]:
            raise ValueError(f"Invalid condition type: {v}")
        return v


class AgentSchema(PydanticBaseModel):
    """Pydantic model for Agent validation and serialization."""
    
    id: Optional[int] = None
    name: str
    description: Optional[str] = None
    instructions: str
    agent_type: str = AgentType.GENERAL.value
    llm_provider: str = LLMProvider.GEMINI.value
    llm_model: str = "flash"
    stt_provider: str = STTProvider.NONE.value
    tts_provider: str = TTSProvider.NONE.value
    is_active: bool = True
    config: Optional[Dict[str, Any]] = None
    tools: Optional[List[ToolSchema]] = None
    
    class Config:
        orm_mode = True
        
    @validator('agent_type')
    def validate_agent_type(cls, v):
        if v not in [t.value for t in AgentType]:
            raise ValueError(f"Invalid agent type: {v}")
        return v
        
    @validator('llm_provider')
    def validate_llm_provider(cls, v):
        if v not in [p.value for p in LLMProvider]:
            raise ValueError(f"Invalid LLM provider: {v}")
        return v
        
    @validator('stt_provider')
    def validate_stt_provider(cls, v):
        if v not in [p.value for p in STTProvider]:
            raise ValueError(f"Invalid STT provider: {v}")
        return v
        
    @validator('tts_provider')
    def validate_tts_provider(cls, v):
        if v not in [p.value for p in TTSProvider]:
            raise ValueError(f"Invalid TTS provider: {v}")
        return v


class ConversationSchema(PydanticBaseModel):
    """Pydantic model for Conversation validation and serialization."""
    
    id: Optional[int] = None
    name: str
    description: Optional[str] = None
    initial_agent_id: int
    is_active: bool = True
    config: Optional[Dict[str, Any]] = None
    agents: Optional[List[AgentSchema]] = None
    
    class Config:
        orm_mode = True

