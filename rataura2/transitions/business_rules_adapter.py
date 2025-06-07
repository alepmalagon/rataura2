"""
Business Rules adapter for agent transitions.

This module provides classes and functions to integrate the Business Rules library
with our agent transition system.
"""
from typing import Dict, List, Any, Optional, Type, Union
import json
import logging

from sqlalchemy import Column, String, Integer, Boolean, ForeignKey, Text, JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship, Session
from pydantic import BaseModel as PydanticBaseModel, Field, validator

from business_rules.engine import run_all
from business_rules.actions import BaseActions, rule_action
from business_rules.variables import (
    BaseVariables, 
    string_rule_variable,
    numeric_rule_variable,
    boolean_rule_variable,
    select_rule_variable,
)

from rataura2.db.models.base import BaseModel
from rataura2.db.models.agent import Transition, Agent, Tool

logger = logging.getLogger(__name__)


class BusinessRulesTransition(BaseModel):
    """
    Model for storing Business Rules transition rules.
    
    This model extends the existing Transition model by adding a field for
    storing Business Rules rule definitions.
    """
    
    __tablename__ = "BusinessRulesTransition"
    
    transition_id: Mapped[int] = mapped_column(Integer, ForeignKey("Transition.id"), nullable=False, unique=True)
    rules_definition: Mapped[Dict] = mapped_column(JSON, nullable=False)
    
    # Relationship to the base Transition model
    transition: Mapped[Transition] = relationship("Transition", backref="business_rules_transition")


class BusinessRulesTransitionSchema(PydanticBaseModel):
    """Pydantic model for BusinessRulesTransition validation and serialization."""
    
    id: Optional[int] = None
    transition_id: int
    rules_definition: Dict[str, Any]
    
    class Config:
        orm_mode = True


class ConversationVariables(BaseVariables):
    """
    Variables for Business Rules conditions based on conversation context.
    
    This class defines the variables that can be used in Business Rules conditions.
    Each method decorated with *_rule_variable returns a value from the context
    that can be used in conditions.
    """
    
    def __init__(self, context: Dict[str, Any]):
        """
        Initialize with conversation context.
        
        Args:
            context: The conversation context containing all data needed for rule evaluation
        """
        self.context = context
    
    @string_rule_variable
    def user_input(self) -> str:
        """
        Get the user's input text.
        
        Returns:
            str: The user's input text or empty string if not available
        """
        return self.context.get("user_input", "")
    
    @string_rule_variable
    def current_agent_name(self) -> str:
        """
        Get the name of the current agent.
        
        Returns:
            str: The name of the current agent or empty string if not available
        """
        return self.context.get("current_agent_name", "")
    
    @string_rule_variable
    def current_agent_type(self) -> str:
        """
        Get the type of the current agent.
        
        Returns:
            str: The type of the current agent or empty string if not available
        """
        return self.context.get("current_agent_type", "")
    
    @numeric_rule_variable
    def conversation_turn_count(self) -> int:
        """
        Get the number of turns in the conversation.
        
        Returns:
            int: The number of turns or 0 if not available
        """
        return self.context.get("turn_count", 0)
    
    @boolean_rule_variable
    def is_first_turn(self) -> bool:
        """
        Check if this is the first turn in the conversation.
        
        Returns:
            bool: True if this is the first turn, False otherwise
        """
        return self.context.get("turn_count", 0) <= 1
    
    @select_rule_variable(options=["question", "statement", "command", "unknown"])
    def user_input_type(self) -> str:
        """
        Get the type of the user's input.
        
        Returns:
            str: The type of the user's input or "unknown" if not available
        """
        return self.context.get("user_input_type", "unknown")
    
    @string_rule_variable
    def last_tool_name(self) -> str:
        """
        Get the name of the last tool used.
        
        Returns:
            str: The name of the last tool used or empty string if not available
        """
        return self.context.get("last_tool_name", "")
    
    @string_rule_variable
    def last_tool_result(self) -> str:
        """
        Get the result of the last tool used as a JSON string.
        
        Returns:
            str: The result of the last tool used as a JSON string or empty string if not available
        """
        tool_result = self.context.get("last_tool_result", {})
        if isinstance(tool_result, dict):
            return json.dumps(tool_result)
        return str(tool_result)
    
    def get_tool_result_value(self, tool_name: str, key_path: str) -> Any:
        """
        Get a specific value from a tool result using a dot-notation path.
        
        Args:
            tool_name: The name of the tool
            key_path: The path to the value in dot notation (e.g., "data.items.0.name")
            
        Returns:
            Any: The value at the specified path or None if not found
        """
        tool_results = self.context.get("tool_results", {})
        if tool_name not in tool_results:
            return None
        
        result = tool_results[tool_name]
        if not key_path:
            return result
        
        # Navigate through the path
        keys = key_path.split(".")
        current = result
        for key in keys:
            if isinstance(current, dict) and key in current:
                current = current[key]
            elif isinstance(current, list) and key.isdigit() and int(key) < len(current):
                current = current[int(key)]
            else:
                return None
        
        return current


class TransitionActions(BaseActions):
    """
    Actions for Business Rules that can be triggered by conditions.
    
    This class defines the actions that can be performed when a Business Rules
    condition is met. In our case, the main action is to transition to a new agent.
    """
    
    def __init__(self, transition_controller):
        """
        Initialize with a transition controller.
        
        Args:
            transition_controller: The controller that handles transitions
        """
        self.transition_controller = transition_controller
    
    @rule_action(params={"agent_id": int})
    def transition_to_agent(self, agent_id: int):
        """
        Transition to a specific agent.
        
        Args:
            agent_id: The ID of the agent to transition to
        """
        self.transition_controller.set_next_agent_id(agent_id)
    
    @rule_action(params={"key": str, "value": str})
    def set_context_value(self, key: str, value: str):
        """
        Set a value in the context.
        
        Args:
            key: The key to set
            value: The value to set
        """
        self.transition_controller.set_context_value(key, value)
    
    @rule_action(params={})
    def log_transition(self):
        """Log that a transition was triggered."""
        logger.info(f"Transition triggered by Business Rules")


class TransitionController:
    """
    Controller for handling transitions based on Business Rules.
    
    This class is responsible for evaluating Business Rules conditions and
    triggering transitions when conditions are met.
    """
    
    def __init__(self, db: Session):
        """
        Initialize the transition controller.
        
        Args:
            db: SQLAlchemy database session
        """
        self.db = db
        self.next_agent_id = None
        self.context_updates = {}
    
    def set_next_agent_id(self, agent_id: int):
        """
        Set the next agent ID.
        
        Args:
            agent_id: The ID of the next agent
        """
        self.next_agent_id = agent_id
    
    def set_context_value(self, key: str, value: str):
        """
        Set a value in the context.
        
        Args:
            key: The key to set
            value: The value to set
        """
        self.context_updates[key] = value
    
    def reset(self):
        """Reset the controller state."""
        self.next_agent_id = None
        self.context_updates = {}
    
    def check_transitions(self, agent_id: int, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Check if any transitions should be triggered based on the context.
        
        Args:
            agent_id: ID of the current agent
            context: Context data to check against transition conditions
            
        Returns:
            Dict[str, Any]: Result containing next_agent_id and context_updates if a transition
                           should be triggered, or empty dict otherwise
        """
        # Reset controller state
        self.reset()
        
        # Get all transitions for the current agent
        transitions = self.db.query(Transition).filter(
            Transition.source_agent_id == agent_id,
            Transition.condition_type == "business_rules"
        ).all()
        
        if not transitions:
            return {}
        
        # Get Business Rules definitions for these transitions
        br_transitions = self.db.query(BusinessRulesTransition).filter(
            BusinessRulesTransition.transition_id.in_([t.id for t in transitions])
        ).all()
        
        # Create a mapping of transition_id to rules_definition
        rules_map = {br.transition_id: br.rules_definition for br in br_transitions}
        
        # Check each transition in priority order
        for transition in sorted(transitions, key=lambda t: t.priority, reverse=True):
            if transition.id not in rules_map:
                continue
            
            rules = rules_map[transition.id]
            
            # Run the rules
            run_all(
                rule_list=rules,
                variables=ConversationVariables(context),
                actions=TransitionActions(self),
                stop_on_first_trigger=True
            )
            
            # If a transition was triggered, return the result
            if self.next_agent_id is not None:
                return {
                    "next_agent_id": self.next_agent_id,
                    "context_updates": self.context_updates
                }
        
        return {}


def create_business_rules_transition(
    db: Session,
    transition_id: int,
    rules_definition: List[Dict[str, Any]]
) -> BusinessRulesTransition:
    """
    Create a new BusinessRulesTransition.
    
    Args:
        db: SQLAlchemy database session
        transition_id: ID of the base Transition
        rules_definition: Business Rules definition
        
    Returns:
        BusinessRulesTransition: The created BusinessRulesTransition
    """
    # Check if the transition exists
    transition = db.query(Transition).filter(Transition.id == transition_id).first()
    if not transition:
        raise ValueError(f"Transition with ID {transition_id} not found")
    
    # Check if a BusinessRulesTransition already exists for this transition
    existing = db.query(BusinessRulesTransition).filter(
        BusinessRulesTransition.transition_id == transition_id
    ).first()
    
    if existing:
        # Update the existing BusinessRulesTransition
        existing.rules_definition = rules_definition
        db.commit()
        return existing
    
    # Create a new BusinessRulesTransition
    br_transition = BusinessRulesTransition(
        transition_id=transition_id,
        rules_definition=rules_definition
    )
    
    # Update the base transition to use business_rules condition type
    transition.condition_type = "business_rules"
    
    db.add(br_transition)
    db.commit()
    db.refresh(br_transition)
    
    return br_transition


def get_business_rules_transition(
    db: Session,
    transition_id: int
) -> Optional[BusinessRulesTransition]:
    """
    Get a BusinessRulesTransition by transition_id.
    
    Args:
        db: SQLAlchemy database session
        transition_id: ID of the base Transition
        
    Returns:
        Optional[BusinessRulesTransition]: The BusinessRulesTransition if found, None otherwise
    """
    return db.query(BusinessRulesTransition).filter(
        BusinessRulesTransition.transition_id == transition_id
    ).first()


def delete_business_rules_transition(
    db: Session,
    transition_id: int
) -> bool:
    """
    Delete a BusinessRulesTransition by transition_id.
    
    Args:
        db: SQLAlchemy database session
        transition_id: ID of the base Transition
        
    Returns:
        bool: True if deleted, False otherwise
    """
    br_transition = get_business_rules_transition(db, transition_id)
    if not br_transition:
        return False
    
    db.delete(br_transition)
    db.commit()
    
    return True

