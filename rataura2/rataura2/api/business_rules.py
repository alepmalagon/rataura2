"""
FastAPI endpoints for Business Rules transitions.

This module provides FastAPI endpoints for managing Business Rules transitions.
"""
from typing import Dict, List, Any, Optional
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from rataura2.db.session import get_db
from rataura2.transitions.api import (
    get_ui_config,
    get_transition_rules,
    create_or_update_transition_rules,
    delete_transition_rules,
    get_agent_transitions_with_rules,
)

router = APIRouter(
    prefix="/business-rules",
    tags=["business-rules"],
)


@router.get("/ui-config")
def get_business_rules_ui_config() -> Dict[str, Any]:
    """
    Get the configuration for the Business Rules UI.
    
    Returns:
        Dict[str, Any]: Configuration for the Business Rules UI
    """
    return get_ui_config()


@router.get("/transitions/{agent_id}")
def get_agent_transitions(
    agent_id: int,
    db: Session = Depends(get_db)
) -> List[Dict[str, Any]]:
    """
    Get all transitions for an agent with their Business Rules.
    
    Args:
        agent_id: ID of the agent
        db: SQLAlchemy database session
        
    Returns:
        List[Dict[str, Any]]: List of transitions with their Business Rules
    """
    return get_agent_transitions_with_rules(db, agent_id)


@router.get("/transition/{transition_id}/rules")
def get_transition_rules_endpoint(
    transition_id: int,
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """
    Get the Business Rules for a transition.
    
    Args:
        transition_id: ID of the transition
        db: SQLAlchemy database session
        
    Returns:
        Dict[str, Any]: The rules if found
    """
    rules = get_transition_rules(db, transition_id)
    if not rules:
        raise HTTPException(status_code=404, detail="Rules not found")
    
    return rules


@router.post("/transition/{transition_id}/rules")
def create_or_update_transition_rules_endpoint(
    transition_id: int,
    rules_json: str,
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """
    Create or update the Business Rules for a transition.
    
    Args:
        transition_id: ID of the transition
        rules_json: JSON string representation of the rules
        db: SQLAlchemy database session
        
    Returns:
        Dict[str, Any]: The created or updated rules
    """
    try:
        return create_or_update_transition_rules(db, transition_id, rules_json)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.delete("/transition/{transition_id}/rules")
def delete_transition_rules_endpoint(
    transition_id: int,
    db: Session = Depends(get_db)
) -> Dict[str, bool]:
    """
    Delete the Business Rules for a transition.
    
    Args:
        transition_id: ID of the transition
        db: SQLAlchemy database session
        
    Returns:
        Dict[str, bool]: {"success": True} if deleted
    """
    success = delete_transition_rules(db, transition_id)
    if not success:
        raise HTTPException(status_code=404, detail="Rules not found")
    
    return {"success": True}

