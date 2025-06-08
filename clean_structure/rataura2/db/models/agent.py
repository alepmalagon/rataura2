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


class Agent(BaseModel):
    """Agent model."""

    __tablename__ = "agent"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=True)
    instructions: Mapped[str] = mapped_column(Text, nullable=True)
    agent_type: Mapped[str] = mapped_column(String(50), nullable=False)
    llm_provider: Mapped[str] = mapped_column(String(50), nullable=False)
    llm_model: Mapped[str] = mapped_column(String(50), nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    agent_metadata: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSON, nullable=True)

    # Relationships
    source_transitions: Mapped[List["Transition"]] = relationship(
        "Transition", 
        foreign_keys="[Transition.source_agent_id]",
        back_populates="source_agent",
        cascade="all, delete-orphan",
    )
    target_transitions: Mapped[List["Transition"]] = relationship(
        "Transition", 
        foreign_keys="[Transition.target_agent_id]",
        back_populates="target_agent",
    )
    tools: Mapped[List["Tool"]] = relationship(
        "Tool",
        secondary="agent_tool",
        back_populates="agents",
    )


class Transition(BaseModel):
    """Transition model."""

    __tablename__ = "transition"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    source_agent_id: Mapped[int] = mapped_column(Integer, ForeignKey("agent.id", ondelete="CASCADE"), index=True)
    target_agent_id: Mapped[int] = mapped_column(Integer, ForeignKey("agent.id", ondelete="CASCADE"), index=True)
    condition_type: Mapped[str] = mapped_column(String(50), nullable=False)
    priority: Mapped[int] = mapped_column(Integer, default=0)
    description: Mapped[str] = mapped_column(Text, nullable=True)
    transition_metadata: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSON, nullable=True)

    # Relationships
    source_agent: Mapped[Agent] = relationship(
        "Agent", 
        foreign_keys=[source_agent_id],
        back_populates="source_transitions",
    )
    target_agent: Mapped[Agent] = relationship(
        "Agent", 
        foreign_keys=[target_agent_id],
        back_populates="target_transitions",
    )
    business_rules_transition: Mapped[List["BusinessRulesTransition"]] = relationship(
        "BusinessRulesTransition",
        back_populates="transition",
        cascade="all, delete-orphan",
    )


class Tool(BaseModel):
    """Tool model."""

    __tablename__ = "tool"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=True)
    function_name: Mapped[str] = mapped_column(String(255), nullable=False)
    parameters: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSON, nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    tool_metadata: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSON, nullable=True)

    # Relationships
    agents: Mapped[List[Agent]] = relationship(
        "Agent",
        secondary="agent_tool",
        back_populates="tools",
    )


# Association table for many-to-many relationship between Agent and Tool
agent_tool = Table(
    "agent_tool",
    BaseModel.metadata,
    Column("agent_id", Integer, ForeignKey("agent.id", ondelete="CASCADE"), primary_key=True),
    Column("tool_id", Integer, ForeignKey("tool.id", ondelete="CASCADE"), primary_key=True),
)

