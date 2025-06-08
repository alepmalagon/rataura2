"""
API for Business Rules transitions.

This module provides API functions for managing Business Rules transitions.
"""
from typing import Dict, List, Any, Optional
from sqlalchemy.orm import Session

from rataura2.db.models.agent import Transition, Agent
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


def get_transition_rules(db: Session, transition_id: int) -> Optional[Dict[str, Any]]:
    """
    Get the Business Rules for a transition.
    
    Args:
        db: SQLAlchemy database session
        transition_id: ID of the transition
        
    Returns:
        Optional[Dict[str, Any]]: The rules if found, None otherwise
    """
    br_transition = get_business_rules_transition(db, transition_id)
    if not br_transition:
        return None
    
    return {
        "id": br_transition.id,
        "transition_id": br_transition.transition_id,
        "rules_definition": br_transition.rules_definition,
        "rules_json": rules_to_json(br_transition),
    }


def create_or_update_transition_rules(
    db: Session,
    transition_id: int,
    rules_json: str
) -> Dict[str, Any]:
    """
    Create or update the Business Rules for a transition.
    
    Args:
        db: SQLAlchemy database session
        transition_id: ID of the transition
        rules_json: JSON string representation of the rules
        
    Returns:
        Dict[str, Any]: The created or updated rules
    """
    rules = json_to_rules(rules_json)
    br_transition = create_business_rules_transition(db, transition_id, rules)
    
    return {
        "id": br_transition.id,
        "transition_id": br_transition.transition_id,
        "rules_definition": br_transition.rules_definition,
        "rules_json": rules_to_json(br_transition),
    }


def delete_transition_rules(db: Session, transition_id: int) -> bool:
    """
    Delete the Business Rules for a transition.
    
    Args:
        db: SQLAlchemy database session
        transition_id: ID of the transition
        
    Returns:
        bool: True if deleted, False otherwise
    """
    return delete_business_rules_transition(db, transition_id)


def get_ui_config() -> Dict[str, Any]:
    """
    Get the configuration for the Business Rules UI.
    
    Returns:
        Dict[str, Any]: Configuration for the Business Rules UI
    """
    return generate_ui_config()


def check_transition(
    db: Session,
    agent_id: int,
    context: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Check if a transition should be triggered based on the context.
    
    Args:
        db: SQLAlchemy database session
        agent_id: ID of the current agent
        context: Context data to check against transition conditions
        
    Returns:
        Dict[str, Any]: Result containing next_agent_id and context_updates if a transition
                       should be triggered, or empty dict otherwise
    """
    controller = TransitionController(db)
    return controller.check_transitions(agent_id, context)


def get_agent_transitions_with_rules(db: Session, agent_id: int) -> List[Dict[str, Any]]:
    """
    Get all transitions for an agent with their Business Rules.
    
    Args:
        db: SQLAlchemy database session
        agent_id: ID of the agent
        
    Returns:
        List[Dict[str, Any]]: List of transitions with their Business Rules
    """
    # Get all transitions for the agent
    transitions = db.query(Transition).filter(
        Transition.source_agent_id == agent_id
    ).all()
    
    # Get all BusinessRulesTransitions for these transitions
    transition_ids = [t.id for t in transitions]
    br_transitions = db.query(BusinessRulesTransition).filter(
        BusinessRulesTransition.transition_id.in_(transition_ids)
    ).all()
    
    # Create a mapping of transition_id to BusinessRulesTransition
    br_map = {br.transition_id: br for br in br_transitions}
    
    # Build the result
    result = []
    for transition in transitions:
        target_agent = db.query(Agent).filter(Agent.id == transition.target_agent_id).first()
        
        transition_data = {
            "id": transition.id,
            "source_agent_id": transition.source_agent_id,
            "target_agent_id": transition.target_agent_id,
            "target_agent_name": target_agent.name if target_agent else "Unknown",
            "condition_type": transition.condition_type,
            "priority": transition.priority,
            "description": transition.description,
            "tool_id": transition.tool_id,
            "has_business_rules": transition.id in br_map,
        }
        
        if transition.id in br_map:
            br_transition = br_map[transition.id]
            transition_data["business_rules"] = {
                "id": br_transition.id,
                "rules_definition": br_transition.rules_definition,
                "rules_json": rules_to_json(br_transition),
            }
        
        result.append(transition_data)
    
    return result

