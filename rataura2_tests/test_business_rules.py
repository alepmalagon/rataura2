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
    get_business_rules_transition,
    delete_business_rules_transition,
    TransitionController,
)
from rataura2.transitions.web_ui import (
    generate_ui_config,
    rules_to_json,
    json_to_rules,
)
from rataura2.transitions.api import (
    get_transition_rules,
    create_or_update_transition_rules,
    delete_transition_rules,
    get_agent_transitions_with_rules,
    check_transition,
)


class TestBusinessRulesTransitions(unittest.TestCase):
    """Test case for Business Rules transitions."""
    
    def setUp(self):
        """Set up the test case."""
        # Create an in-memory SQLite database
        self.engine = create_engine("sqlite:///:memory:")
        
        # Create all tables
        Base.metadata.create_all(self.engine)
        
        # Create a session factory
        self.SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=self.engine)
        
        # Create a session
        self.db = self.SessionLocal()
        
        # Create test agents
        self.general_agent = Agent(
            name="Test General Agent",
            description="A test general-purpose agent",
            instructions="You are a test general-purpose assistant.",
            agent_type=AgentType.GENERAL.value,
            llm_provider=LLMProvider.GEMINI.value,
            llm_model="flash",
        )
        self.db.add(self.general_agent)
        
        self.combat_agent = Agent(
            name="Test Combat Agent",
            description="A test combat agent",
            instructions="You are a test combat specialist.",
            agent_type=AgentType.COMBAT.value,
            llm_provider=LLMProvider.GEMINI.value,
            llm_model="flash",
        )
        self.db.add(self.combat_agent)
        
        # Commit to get IDs
        self.db.commit()
        
        # Create a test transition
        self.transition = Transition(
            source_agent_id=self.general_agent.id,
            target_agent_id=self.combat_agent.id,
            condition_type="business_rules",
            priority=10,
            description="Test transition",
        )
        self.db.add(self.transition)
        self.db.commit()
        
        # Create test rules
        self.rules = [
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
    
    def tearDown(self):
        """Tear down the test case."""
        self.db.close()
    
    def test_create_business_rules_transition(self):
        """Test creating a Business Rules transition."""
        br_transition = create_business_rules_transition(
            self.db, self.transition.id, self.rules
        )
        
        self.assertIsNotNone(br_transition)
        self.assertEqual(br_transition.transition_id, self.transition.id)
        self.assertEqual(br_transition.rules_definition, self.rules)
        
        # Check that the transition condition_type was updated
        transition = self.db.query(Transition).filter(
            Transition.id == self.transition.id
        ).first()
        self.assertEqual(transition.condition_type, "business_rules")
    
    def test_get_business_rules_transition(self):
        """Test getting a Business Rules transition."""
        # Create a Business Rules transition
        create_business_rules_transition(
            self.db, self.transition.id, self.rules
        )
        
        # Get the Business Rules transition
        br_transition = get_business_rules_transition(
            self.db, self.transition.id
        )
        
        self.assertIsNotNone(br_transition)
        self.assertEqual(br_transition.transition_id, self.transition.id)
        self.assertEqual(br_transition.rules_definition, self.rules)
    
    def test_delete_business_rules_transition(self):
        """Test deleting a Business Rules transition."""
        # Create a Business Rules transition
        create_business_rules_transition(
            self.db, self.transition.id, self.rules
        )
        
        # Delete the Business Rules transition
        result = delete_business_rules_transition(
            self.db, self.transition.id
        )
        
        self.assertTrue(result)
        
        # Check that the Business Rules transition was deleted
        br_transition = get_business_rules_transition(
            self.db, self.transition.id
        )
        self.assertIsNone(br_transition)
    
    def test_check_transitions(self):
        """Test checking transitions."""
        # Create a Business Rules transition
        create_business_rules_transition(
            self.db, self.transition.id, self.rules
        )
        
        # Create a controller
        controller = TransitionController(self.db)
        
        # Test with matching input
        context = {
            "user_input": "Tell me about combat in EVE Online",
            "current_agent_name": self.general_agent.name,
            "current_agent_type": self.general_agent.agent_type,
            "turn_count": 1,
        }
        
        result = controller.check_transitions(self.general_agent.id, context)
        
        self.assertIsNotNone(result)
        self.assertEqual(result["next_agent_id"], self.combat_agent.id)
        
        # Test with non-matching input
        context = {
            "user_input": "Tell me about EVE Online",
            "current_agent_name": self.general_agent.name,
            "current_agent_type": self.general_agent.agent_type,
            "turn_count": 1,
        }
        
        result = controller.check_transitions(self.general_agent.id, context)
        
        self.assertEqual(result, {})
    
    def test_web_ui_functions(self):
        """Test web UI functions."""
        # Create a Business Rules transition
        br_transition = create_business_rules_transition(
            self.db, self.transition.id, self.rules
        )
        
        # Test generate_ui_config
        config = generate_ui_config()
        self.assertIsNotNone(config)
        self.assertIn("variables", config)
        self.assertIn("actions", config)
        
        # Test rules_to_json
        json_str = rules_to_json(br_transition)
        self.assertIsNotNone(json_str)
        
        # Test json_to_rules
        rules = json_to_rules(json_str)
        self.assertEqual(rules, self.rules)
    
    def test_api_functions(self):
        """Test API functions."""
        # Create a Business Rules transition
        create_business_rules_transition(
            self.db, self.transition.id, self.rules
        )
        
        # Test get_transition_rules
        rules = get_transition_rules(self.db, self.transition.id)
        self.assertIsNotNone(rules)
        self.assertEqual(rules["transition_id"], self.transition.id)
        self.assertEqual(rules["rules_definition"], self.rules)
        
        # Test create_or_update_transition_rules
        new_rules = [
            {
                "conditions": {
                    "all": [
                        {
                            "name": "user_input",
                            "operator": "contains",
                            "value": "pvp"
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
        
        rules = create_or_update_transition_rules(
            self.db, self.transition.id, json.dumps(new_rules)
        )
        self.assertEqual(rules["rules_definition"], new_rules)
        
        # Test get_agent_transitions_with_rules
        transitions = get_agent_transitions_with_rules(self.db, self.general_agent.id)
        self.assertEqual(len(transitions), 1)
        self.assertEqual(transitions[0]["id"], self.transition.id)
        self.assertTrue(transitions[0]["has_business_rules"])
        self.assertEqual(transitions[0]["business_rules"]["rules_definition"], new_rules)
        
        # Test check_transition
        context = {
            "user_input": "Tell me about pvp in EVE Online",
            "current_agent_name": self.general_agent.name,
            "current_agent_type": self.general_agent.agent_type,
            "turn_count": 1,
        }
        
        result = check_transition(self.db, self.general_agent.id, context)
        self.assertIsNotNone(result)
        self.assertEqual(result["next_agent_id"], self.combat_agent.id)
        
        # Test delete_transition_rules
        result = delete_transition_rules(self.db, self.transition.id)
        self.assertTrue(result)
        
        rules = get_transition_rules(self.db, self.transition.id)
        self.assertIsNone(rules)


if __name__ == "__main__":
    unittest.main()
