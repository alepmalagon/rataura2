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
from business_rules.fields import FIELD_NUMERIC, FIELD_TEXT, FIELD_NO_INPUT
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
    """Business Rules transition model."""

    __tablename__ = "business_rules_transition"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    transition_id: Mapped[int] = mapped_column(Integer, ForeignKey("transition.id", ondelete="CASCADE"), index=True)
    rules: Mapped[str] = mapped_column(Text, nullable=False)

    # Relationships
    transition: Mapped[Transition] = relationship("Transition", back_populates="business_rules_transition")


class TransitionVariables(BaseVariables):
    """Variables for the Business Rules engine."""

    def __init__(self, context: Dict[str, Any]):
        """Initialize the variables with the context."""
        self.context = context

    @string_rule_variable
    def user_input(self) -> str:
        """Get the user input."""
        return self.context.get("user_input", "")

    @string_rule_variable
    def current_agent_name(self) -> str:
        """Get the current agent name."""
        return self.context.get("current_agent_name", "")

    @string_rule_variable
    def current_agent_type(self) -> str:
        """Get the current agent type."""
        return self.context.get("current_agent_type", "")

    @numeric_rule_variable
    def turn_count(self) -> int:
        """Get the turn count."""
        return self.context.get("turn_count", 0)


class TransitionActions(BaseActions):
    """Actions for the Business Rules engine."""

    def __init__(self, agent_id: int):
        """Initialize the actions with the agent ID."""
        self.agent_id = agent_id
        self.triggered = False

    @rule_action(params={"agent_id": FIELD_NUMERIC})
    def transition_to_agent(self, agent_id: int):
        """Transition to the specified agent."""
        self.triggered = True
        self.agent_id = agent_id


def create_business_rules_transition(db: Session, transition_id: int, rules: List[Dict[str, Any]]) -> BusinessRulesTransition:
    """Create a business rules transition."""
    # Check if the transition exists
    transition = db.query(Transition).filter(Transition.id == transition_id).first()
    if not transition:
        raise ValueError(f"Transition with ID {transition_id} not found")

    # Check if a business rules transition already exists for this transition
    existing = db.query(BusinessRulesTransition).filter(
        BusinessRulesTransition.transition_id == transition_id
    ).first()

    if existing:
        # Update the existing business rules transition
        existing.rules = json.dumps(rules)
        db.commit()
        return existing
    else:
        # Create a new business rules transition
        business_rules_transition = BusinessRulesTransition(
            transition_id=transition_id,
            rules=json.dumps(rules),
        )
        db.add(business_rules_transition)
        db.commit()
        return business_rules_transition


class TransitionController:
    """Controller for checking transitions."""

    def __init__(self, db: Session):
        """Initialize the controller with the database session."""
        self.db = db

    def check_transitions(self, agent_id: int, context: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Check if any transitions should be triggered."""
        # Get all transitions for the agent
        transitions = self.db.query(Transition).filter(
            Transition.source_agent_id == agent_id
        ).order_by(Transition.priority.desc()).all()

        if not transitions:
            return None

        # Check each transition
        for transition in transitions:
            if transition.condition_type == "business_rules":
                result = self._check_business_rules_transition(transition, context)
                if result:
                    return {
                        "transition_id": transition.id,
                        "next_agent_id": result,
                    }

        return None

    def _check_business_rules_transition(self, transition: Transition, context: Dict[str, Any]) -> Optional[int]:
        """Check if a business rules transition should be triggered."""
        # Get the business rules transition
        business_rules_transition = self.db.query(BusinessRulesTransition).filter(
            BusinessRulesTransition.transition_id == transition.id
        ).first()

        if not business_rules_transition:
            return None

        # Parse the rules
        rules = json.loads(business_rules_transition.rules)

        # Create the variables and actions
        variables = TransitionVariables(context)
        actions = TransitionActions(transition.target_agent_id)

        # Run the rules
        run_all(
            rule_list=rules,
            defined_variables=variables,
            defined_actions=actions,
            stop_on_first_trigger=True,
        )

        # Check if a transition was triggered
        if actions.triggered:
            return actions.agent_id
        else:
            return None

