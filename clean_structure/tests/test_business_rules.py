"""
Tests for the Business Rules transitions module.
"""
import sys
import os
from pathlib import Path
import unittest
import json

# Add the parent directory to the path so we can import the rataura2 package
sys.path.append(str(Path(__file__).parent.parent))

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session

from rataura2.db.models.base import Base
from rataura2.db.models.agent import Agent, Transition, AgentType, LLMProvider
from rataura2.transitions.business_rules_adapter import (
    BusinessRulesTransition,
    create_business_rules_transition,
    TransitionController,
)


class TestBusinessRules(unittest.TestCase):
    """Test the Business Rules transitions module."""

    def setUp(self):
        """Set up the test environment."""
        # Create an in-memory SQLite database
        self.engine = create_engine("sqlite:///:memory:")
        
        # Create all tables
        Base.metadata.create_all(self.engine)
        
        # Create a session factory
        SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=self.engine)
        
        # Create a session
        self.db = SessionLocal()
        
        # Create test agents
        self.general_agent = Agent(
            name="General Agent",
            description="A general-purpose agent for EVE Online",
            instructions="You are a general-purpose assistant for EVE Online.",
            agent_type=AgentType.GENERAL.value,
            llm_provider=LLMProvider.GEMINI.value,
            llm_model="flash",
        )
        self.db.add(self.general_agent)
        
        self.combat_agent = Agent(
            name="Combat Agent",
            description="A combat specialist for EVE Online",
            instructions="You are a combat specialist for EVE Online.",
            agent_type=AgentType.COMBAT.value,
            llm_provider=LLMProvider.GEMINI.value,
            llm_model="flash",
        )
        self.db.add(self.combat_agent)
        
        self.market_agent = Agent(
            name="Market Agent",
            description="A market specialist for EVE Online",
            instructions="You are a market specialist for EVE Online.",
            agent_type=AgentType.MARKET.value,
            llm_provider=LLMProvider.GEMINI.value,
            llm_model="flash",
        )
        self.db.add(self.market_agent)
        
        # Commit to get IDs
        self.db.commit()
        
        # Create transitions
        self.combat_transition = Transition(
            source_agent_id=self.general_agent.id,
            target_agent_id=self.combat_agent.id,
            condition_type="business_rules",
            priority=10,
            description="Transition to combat agent",
        )
        self.db.add(self.combat_transition)
        
        self.market_transition = Transition(
            source_agent_id=self.general_agent.id,
            target_agent_id=self.market_agent.id,
            condition_type="business_rules",
            priority=10,
            description="Transition to market agent",
        )
        self.db.add(self.market_transition)
        
        self.db.commit()
        
        # Create business rules for transitions
        self.combat_rules = [
            {
                "conditions": {
                    "all": [
                        {
                            "name": "user_input",
                            "operator": "contains",
                            "value": "combat"
                        }
                    ]
                },
                "actions": [
                    {
                        "name": "transition_to_agent",
                        "params": {
                            "agent_id": self.combat_agent.id
                        }
                    }
                ]
            }
        ]
        
        self.market_rules = [
            {
                "conditions": {
                    "all": [
                        {
                            "name": "user_input",
                            "operator": "contains",
                            "value": "market"
                        }
                    ]
                },
                "actions": [
                    {
                        "name": "transition_to_agent",
                        "params": {
                            "agent_id": self.market_agent.id
                        }
                    }
                ]
            }
        ]
        
        create_business_rules_transition(self.db, self.combat_transition.id, self.combat_rules)
        create_business_rules_transition(self.db, self.market_transition.id, self.market_rules)
        
        # Create a controller
        self.controller = TransitionController(self.db)

    def tearDown(self):
        """Clean up after the test."""
        self.db.close()

    def test_create_business_rules_transition(self):
        """Test creating a business rules transition."""
        # Get the business rules transition
        transition = self.db.query(BusinessRulesTransition).filter(
            BusinessRulesTransition.transition_id == self.combat_transition.id
        ).first()
        
        # Check that the transition was created
        self.assertIsNotNone(transition)
        
        # Check that the rules were saved
        self.assertEqual(transition.rules, json.dumps(self.combat_rules))

    def test_check_transitions_combat(self):
        """Test checking transitions with combat input."""
        context = {
            "user_input": "Tell me about combat in EVE Online",
            "current_agent_name": "General Agent",
            "current_agent_type": AgentType.GENERAL.value,
            "turn_count": 1,
        }
        
        result = self.controller.check_transitions(self.general_agent.id, context)
        
        # Check that the transition was triggered
        self.assertIsNotNone(result)
        
        # Check that the next agent is the combat agent
        self.assertEqual(result["next_agent_id"], self.combat_agent.id)

    def test_check_transitions_market(self):
        """Test checking transitions with market input."""
        context = {
            "user_input": "Tell me about the market in EVE Online",
            "current_agent_name": "General Agent",
            "current_agent_type": AgentType.GENERAL.value,
            "turn_count": 1,
        }
        
        result = self.controller.check_transitions(self.general_agent.id, context)
        
        # Check that the transition was triggered
        self.assertIsNotNone(result)
        
        # Check that the next agent is the market agent
        self.assertEqual(result["next_agent_id"], self.market_agent.id)

    def test_check_transitions_no_match(self):
        """Test checking transitions with no matching input."""
        context = {
            "user_input": "Tell me about EVE Online",
            "current_agent_name": "General Agent",
            "current_agent_type": AgentType.GENERAL.value,
            "turn_count": 1,
        }
        
        result = self.controller.check_transitions(self.general_agent.id, context)
        
        # Check that no transition was triggered
        self.assertIsNone(result)

    def test_check_transitions_priority(self):
        """Test checking transitions with priority."""
        # Create a new transition with higher priority
        high_priority_transition = Transition(
            source_agent_id=self.general_agent.id,
            target_agent_id=self.combat_agent.id,
            condition_type="business_rules",
            priority=20,
            description="High priority transition to combat agent",
        )
        self.db.add(high_priority_transition)
        self.db.commit()
        
        # Create business rules for the high priority transition
        high_priority_rules = [
            {
                "conditions": {
                    "all": [
                        {
                            "name": "user_input",
                            "operator": "contains",
                            "value": "high priority"
                        }
                    ]
                },
                "actions": [
                    {
                        "name": "transition_to_agent",
                        "params": {
                            "agent_id": self.combat_agent.id
                        }
                    }
                ]
            }
        ]
        
        create_business_rules_transition(self.db, high_priority_transition.id, high_priority_rules)
        
        # Test with input that matches both transitions
        context = {
            "user_input": "Tell me about high priority combat in EVE Online",
            "current_agent_name": "General Agent",
            "current_agent_type": AgentType.GENERAL.value,
            "turn_count": 1,
        }
        
        result = self.controller.check_transitions(self.general_agent.id, context)
        
        # Check that the transition was triggered
        self.assertIsNotNone(result)
        
        # Check that the next agent is the combat agent
        self.assertEqual(result["next_agent_id"], self.combat_agent.id)
        
        # Check that the transition ID is the high priority transition
        self.assertEqual(result["transition_id"], high_priority_transition.id)


if __name__ == "__main__":
    unittest.main()

