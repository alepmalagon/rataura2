"""
Example script demonstrating how to use Business Rules transitions.
"""
import sys
import os
from pathlib import Path
import json

# Add the parent directory to the path so we can import the rataura2 package
sys.path.append(str(Path(__file__).parent.parent))

from sqlalchemy.orm import Session

from rataura2.db.session import SessionLocal, create_tables
from rataura2.db.models.agent import Agent, Transition, AgentType, LLMProvider
from rataura2.transitions.business_rules_adapter import (
    create_business_rules_transition,
    TransitionController,
)
from rataura2.transitions.web_ui import generate_ui_config


def create_example_agents(db: Session):
    """Create example agents for the demonstration."""
    # Create general agent
    general_agent = Agent(
        name="General Agent",
        description="A general-purpose agent for handling various queries",
        instructions="You are a general-purpose assistant. Answer questions to the best of your ability.",
        agent_type=AgentType.GENERAL.value,
        llm_provider=LLMProvider.GEMINI.value,
        llm_model="flash",
    )
    db.add(general_agent)
    
    # Create combat agent
    combat_agent = Agent(
        name="Combat Agent",
        description="An agent specialized in EVE Online combat mechanics",
        instructions="You are a combat specialist for EVE Online. Provide detailed advice on ship fittings, combat tactics, and PvP strategies.",
        agent_type=AgentType.COMBAT.value,
        llm_provider=LLMProvider.GEMINI.value,
        llm_model="flash",
    )
    db.add(combat_agent)
    
    # Create market agent
    market_agent = Agent(
        name="Market Agent",
        description="An agent specialized in EVE Online market and economy",
        instructions="You are a market specialist for EVE Online. Provide detailed advice on trading, market trends, and economic strategies.",
        agent_type=AgentType.MARKET.value,
        llm_provider=LLMProvider.GEMINI.value,
        llm_model="flash",
    )
    db.add(market_agent)
    
    # Commit to get IDs
    db.commit()
    
    return general_agent, combat_agent, market_agent


def create_example_transitions(db: Session, general_agent, combat_agent, market_agent):
    """Create example transitions between the agents."""
    # Create transition from general to combat
    general_to_combat = Transition(
        source_agent_id=general_agent.id,
        target_agent_id=combat_agent.id,
        condition_type="business_rules",
        priority=10,
        description="Transition to combat agent when user asks about combat",
    )
    db.add(general_to_combat)
    
    # Create transition from general to market
    general_to_market = Transition(
        source_agent_id=general_agent.id,
        target_agent_id=market_agent.id,
        condition_type="business_rules",
        priority=10,
        description="Transition to market agent when user asks about market",
    )
    db.add(general_to_market)
    
    # Create transition from combat to general
    combat_to_general = Transition(
        source_agent_id=combat_agent.id,
        target_agent_id=general_agent.id,
        condition_type="business_rules",
        priority=10,
        description="Transition to general agent when user asks about non-combat topics",
    )
    db.add(combat_to_general)
    
    # Create transition from market to general
    market_to_general = Transition(
        source_agent_id=market_agent.id,
        target_agent_id=general_agent.id,
        condition_type="business_rules",
        priority=10,
        description="Transition to general agent when user asks about non-market topics",
    )
    db.add(market_to_general)
    
    # Commit to get IDs
    db.commit()
    
    return general_to_combat, general_to_market, combat_to_general, market_to_general


def create_example_rules(db: Session, general_to_combat, general_to_market):
    """Create example Business Rules for the transitions."""
    # Rules for general to combat transition
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
                        "agent_id": general_to_combat.target_agent_id
                    }
                },
                {
                    "name": "log_transition"
                }
            ]
        },
        {
            "conditions": {
                "any": [
                    {
                        "name": "user_input",
                        "operator": "contains",
                        "value": "ship fitting"
                    },
                    {
                        "name": "user_input",
                        "operator": "contains",
                        "value": "pvp"
                    },
                    {
                        "name": "user_input",
                        "operator": "contains",
                        "value": "battle"
                    }
                ]
            },
            "actions": [
                {
                    "name": "transition_to_agent",
                    "params": {
                        "agent_id": general_to_combat.target_agent_id
                    }
                },
                {
                    "name": "log_transition"
                }
            ]
        }
    ]
    
    # Rules for general to market transition
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
                        "agent_id": general_to_market.target_agent_id
                    }
                },
                {
                    "name": "log_transition"
                }
            ]
        },
        {
            "conditions": {
                "any": [
                    {
                        "name": "user_input",
                        "operator": "contains",
                        "value": "trading"
                    },
                    {
                        "name": "user_input",
                        "operator": "contains",
                        "value": "economy"
                    },
                    {
                        "name": "user_input",
                        "operator": "contains",
                        "value": "price"
                    }
                ]
            },
            "actions": [
                {
                    "name": "transition_to_agent",
                    "params": {
                        "agent_id": general_to_market.target_agent_id
                    }
                },
                {
                    "name": "log_transition"
                }
            ]
        }
    ]
    
    # Create the Business Rules transitions
    create_business_rules_transition(db, general_to_combat.id, combat_rules)
    create_business_rules_transition(db, general_to_market.id, market_rules)


def test_transitions(db: Session, general_agent):
    """Test the transitions with example user inputs."""
    controller = TransitionController(db)
    
    # Test with combat-related input
    combat_context = {
        "user_input": "Can you help me with ship fittings for PvP combat?",
        "current_agent_name": general_agent.name,
        "current_agent_type": general_agent.agent_type,
        "turn_count": 1,
    }
    
    combat_result = controller.check_transitions(general_agent.id, combat_context)
    print(f"Combat input result: {combat_result}")
    
    # Test with market-related input
    market_context = {
        "user_input": "What's the current market price of PLEX?",
        "current_agent_name": general_agent.name,
        "current_agent_type": general_agent.agent_type,
        "turn_count": 1,
    }
    
    market_result = controller.check_transitions(general_agent.id, market_context)
    print(f"Market input result: {market_result}")
    
    # Test with general input
    general_context = {
        "user_input": "Tell me about the history of EVE Online",
        "current_agent_name": general_agent.name,
        "current_agent_type": general_agent.agent_type,
        "turn_count": 1,
    }
    
    general_result = controller.check_transitions(general_agent.id, general_context)
    print(f"General input result: {general_result}")


def print_ui_config():
    """Print the UI configuration for the Business Rules UI."""
    config = generate_ui_config()
    print(json.dumps(config, indent=2))


def main():
    """Main function to run the example."""
    # Create tables if they don't exist
    create_tables()
    
    # Create a database session
    db = SessionLocal()
    
    try:
        # Create example agents
        general_agent, combat_agent, market_agent = create_example_agents(db)
        print(f"Created agents: {general_agent.name}, {combat_agent.name}, {market_agent.name}")
        
        # Create example transitions
        general_to_combat, general_to_market, combat_to_general, market_to_general = create_example_transitions(
            db, general_agent, combat_agent, market_agent
        )
        print(f"Created transitions between agents")
        
        # Create example rules
        create_example_rules(db, general_to_combat, general_to_market)
        print(f"Created Business Rules for transitions")
        
        # Test the transitions
        print("\nTesting transitions:")
        test_transitions(db, general_agent)
        
        # Print UI configuration
        print("\nUI Configuration:")
        print_ui_config()
        
    finally:
        db.close()


if __name__ == "__main__":
    main()

