"""
Simple example of using the transition system.
"""
import sys
import os
from pathlib import Path
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


def main():
    """Main function."""
    # Create an in-memory SQLite database
    engine = create_engine("sqlite:///:memory:")
    
    # Create all tables
    Base.metadata.create_all(engine)
    
    # Create a session factory
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    
    # Create a session
    db = SessionLocal()
    
    # Create test agents
    general_agent = Agent(
        name="General Agent",
        description="A general-purpose agent for EVE Online",
        instructions="You are a general-purpose assistant for EVE Online.",
        agent_type=AgentType.GENERAL.value,
        llm_provider=LLMProvider.GEMINI.value,
        llm_model="flash",
    )
    db.add(general_agent)
    
    combat_agent = Agent(
        name="Combat Agent",
        description="A combat specialist for EVE Online",
        instructions="You are a combat specialist for EVE Online.",
        agent_type=AgentType.COMBAT.value,
        llm_provider=LLMProvider.GEMINI.value,
        llm_model="flash",
    )
    db.add(combat_agent)
    
    market_agent = Agent(
        name="Market Agent",
        description="A market specialist for EVE Online",
        instructions="You are a market specialist for EVE Online.",
        agent_type=AgentType.MARKET.value,
        llm_provider=LLMProvider.GEMINI.value,
        llm_model="flash",
    )
    db.add(market_agent)
    
    # Commit to get IDs
    db.commit()
    
    # Create transitions
    combat_transition = Transition(
        source_agent_id=general_agent.id,
        target_agent_id=combat_agent.id,
        condition_type="business_rules",
        priority=10,
        description="Transition to combat agent",
    )
    db.add(combat_transition)
    
    market_transition = Transition(
        source_agent_id=general_agent.id,
        target_agent_id=market_agent.id,
        condition_type="business_rules",
        priority=10,
        description="Transition to market agent",
    )
    db.add(market_transition)
    
    db.commit()
    
    # Create business rules for transitions
    combat_rules = [
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
                        "agent_id": combat_agent.id
                    }
                }
            ]
        }
    ]
    
    market_rules = [
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
                        "agent_id": market_agent.id
                    }
                }
            ]
        }
    ]
    
    create_business_rules_transition(db, combat_transition.id, combat_rules)
    create_business_rules_transition(db, market_transition.id, market_rules)
    
    # Create a controller
    controller = TransitionController(db)
    
    # Test with different inputs
    test_inputs = [
        "Tell me about EVE Online",
        "Tell me about combat in EVE Online",
        "Tell me about the market in EVE Online",
    ]
    
    current_agent_id = general_agent.id
    current_agent_name = general_agent.name
    
    for user_input in test_inputs:
        print(f"\nUser: {user_input}")
        print(f"Current Agent: {current_agent_name}")
        
        context = {
            "user_input": user_input,
            "current_agent_name": current_agent_name,
            "current_agent_type": AgentType.GENERAL.value,
            "turn_count": 1,
        }
        
        result = controller.check_transitions(current_agent_id, context)
        
        if result:
            next_agent_id = result["next_agent_id"]
            next_agent = db.query(Agent).filter(Agent.id == next_agent_id).first()
            print(f"Transition to: {next_agent.name}")
            current_agent_id = next_agent_id
            current_agent_name = next_agent.name
        else:
            print("No transition triggered")


if __name__ == "__main__":
    main()

