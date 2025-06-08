"""
Example script demonstrating how to use the agent orchestration system.

This script creates a simulated conversation with multiple agents and shows
how transitions between agents are triggered by events.
"""
import sys
import os
from pathlib import Path
import time
import asyncio
import logging
from typing import Dict, Any

# Add the parent directory to the path so we can import the rataura2 package
sys.path.append(str(Path(__file__).parent.parent))

from sqlalchemy.orm import Session

from rataura2.db.session import SessionLocal, create_tables
from rataura2.db.models.agent import Agent, Transition, AgentType, LLMProvider
from rataura2.orchestration.orchestrator import SessionManager, AgentOrchestrator
from rataura2.livekit_agent.events import EventData, EventType
from rataura2.transitions.business_rules_adapter import create_business_rules_transition

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s %(name)s - %(message)s",
)
logger = logging.getLogger("agent_orchestration_example")


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


def create_example_conversation(db: Session, general_agent):
    """Create an example conversation for the demonstration."""
    from rataura2.db.models.agent import Conversation
    
    # Create a conversation
    conversation = Conversation(
        name="Example Conversation",
        description="An example conversation for demonstrating agent orchestration",
        initial_agent_id=general_agent.id,
    )
    db.add(conversation)
    
    # Add agents to the conversation
    conversation.agents.append(general_agent)
    
    # Commit to get ID
    db.commit()
    
    return conversation


def create_example_transitions(db: Session, general_agent, combat_agent, market_agent):
    """Create example transitions between the agents."""
    # Create transition from general to combat
    general_to_combat = Transition(
        source_agent_id=general_agent.id,
        target_agent_id=combat_agent.id,
        condition_type="event",
        condition_data={
            "event_type": "user_message",
            "event_data": {}
        },
        priority=10,
        description="Transition to combat agent when user asks about combat",
    )
    db.add(general_to_combat)
    
    # Create transition from general to market
    general_to_market = Transition(
        source_agent_id=general_agent.id,
        target_agent_id=market_agent.id,
        condition_type="event",
        condition_data={
            "event_type": "user_message",
            "event_data": {}
        },
        priority=10,
        description="Transition to market agent when user asks about market",
    )
    db.add(general_to_market)
    
    # Create transition from combat to general
    combat_to_general = Transition(
        source_agent_id=combat_agent.id,
        target_agent_id=general_agent.id,
        condition_type="event",
        condition_data={
            "event_type": "user_message",
            "event_data": {}
        },
        priority=10,
        description="Transition to general agent when user asks about non-combat topics",
    )
    db.add(combat_to_general)
    
    # Create transition from market to general
    market_to_general = Transition(
        source_agent_id=market_agent.id,
        target_agent_id=general_agent.id,
        condition_type="event",
        condition_data={
            "event_type": "user_message",
            "event_data": {}
        },
        priority=10,
        description="Transition to general agent when user asks about non-market topics",
    )
    db.add(market_to_general)
    
    # Commit to get IDs
    db.commit()
    
    return general_to_combat, general_to_market, combat_to_general, market_to_general


def create_example_business_rules(db: Session, general_to_combat, general_to_market, combat_to_general, market_to_general):
    """Create example business rules for the transitions."""
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
    
    # Rules for combat to general transition
    combat_to_general_rules = [
        {
            "conditions": {
                "all": [
                    {
                        "name": "user_input",
                        "operator": "not_contains",
                        "value": "combat"
                    },
                    {
                        "name": "user_input",
                        "operator": "not_contains",
                        "value": "ship"
                    },
                    {
                        "name": "user_input",
                        "operator": "not_contains",
                        "value": "pvp"
                    },
                    {
                        "name": "user_input",
                        "operator": "not_contains",
                        "value": "battle"
                    }
                ]
            },
            "actions": [
                {
                    "name": "transition_to_agent",
                    "params": {
                        "agent_id": combat_to_general.target_agent_id
                    }
                },
                {
                    "name": "log_transition"
                }
            ]
        }
    ]
    
    # Rules for market to general transition
    market_to_general_rules = [
        {
            "conditions": {
                "all": [
                    {
                        "name": "user_input",
                        "operator": "not_contains",
                        "value": "market"
                    },
                    {
                        "name": "user_input",
                        "operator": "not_contains",
                        "value": "trading"
                    },
                    {
                        "name": "user_input",
                        "operator": "not_contains",
                        "value": "economy"
                    },
                    {
                        "name": "user_input",
                        "operator": "not_contains",
                        "value": "price"
                    }
                ]
            },
            "actions": [
                {
                    "name": "transition_to_agent",
                    "params": {
                        "agent_id": market_to_general.target_agent_id
                    }
                },
                {
                    "name": "log_transition"
                }
            ]
        }
    ]
    
    # Create the business rules transitions
    create_business_rules_transition(db, general_to_combat.id, combat_rules)
    create_business_rules_transition(db, general_to_market.id, market_rules)
    create_business_rules_transition(db, combat_to_general.id, combat_to_general_rules)
    create_business_rules_transition(db, market_to_general.id, market_to_general_rules)


def simulate_conversation(session_manager: SessionManager, conversation_id: int):
    """Simulate a conversation with the orchestration system."""
    # Create a session
    session_id = f"example:{conversation_id}"
    orchestrator = session_manager.create_session(session_id, conversation_id)
    
    # Get the initial agent
    initial_agent = orchestrator.get_current_agent()
    logger.info(f"Initial agent: {orchestrator.get_context()['current_agent_name']}")
    
    # Simulate user messages
    user_messages = [
        "Hello, I'm new to EVE Online. Can you help me?",
        "I'm interested in combat. What ships are good for PvP?",
        "How much does a good combat ship cost?",
        "What are the best markets to buy ships?",
        "Tell me about trading strategies in EVE Online.",
        "I want to go back to combat. How do I fit a Rifter for PvP?",
        "Thank you for your help!"
    ]
    
    for message in user_messages:
        logger.info(f"\nUser: {message}")
        
        # Create a user message event
        event = EventData(
            type=EventType.USER_MESSAGE,
            timestamp=time.time(),
            data={"message": message},
            source="user"
        )
        
        # Process the event
        orchestrator.process_event(event)
        
        # Check for transitions
        orchestrator.check_and_execute_transition()
        
        # Get the current agent
        current_agent_name = orchestrator.get_context()["current_agent_name"]
        logger.info(f"Current agent: {current_agent_name}")
        
        # Simulate agent response
        agent_response = f"[{current_agent_name}] Response to: {message}"
        logger.info(f"Agent: {agent_response}")
        
        # Create an agent message event
        event = EventData(
            type=EventType.AGENT_MESSAGE,
            timestamp=time.time(),
            data={
                "agent_id": orchestrator.get_context()["current_agent_id"],
                "message": agent_response
            },
            source="agent"
        )
        
        # Process the event
        orchestrator.process_event(event)
        
        # Check for transitions
        orchestrator.check_and_execute_transition()
        
        # Pause for readability
        time.sleep(1)
    
    # End the session
    session_manager.end_session(session_id)
    logger.info("Session ended")


def main():
    """Main function to run the example."""
    # Create tables if they don't exist
    create_tables()
    
    # Create a database session
    db = SessionLocal()
    
    try:
        # Create example agents
        general_agent, combat_agent, market_agent = create_example_agents(db)
        logger.info(f"Created agents: {general_agent.name}, {combat_agent.name}, {market_agent.name}")
        
        # Create example conversation
        conversation = create_example_conversation(db, general_agent)
        logger.info(f"Created conversation: {conversation.name}")
        
        # Add agents to the conversation
        conversation.agents.append(combat_agent)
        conversation.agents.append(market_agent)
        db.commit()
        
        # Create example transitions
        general_to_combat, general_to_market, combat_to_general, market_to_general = create_example_transitions(
            db, general_agent, combat_agent, market_agent
        )
        logger.info(f"Created transitions between agents")
        
        # Create example business rules
        create_example_business_rules(
            db, general_to_combat, general_to_market, combat_to_general, market_to_general
        )
        logger.info(f"Created business rules for transitions")
        
        # Create a session manager
        session_manager = SessionManager(db)
        
        # Simulate a conversation
        logger.info("\nSimulating conversation:")
        simulate_conversation(session_manager, conversation.id)
        
    finally:
        db.close()


if __name__ == "__main__":
    main()
"""

