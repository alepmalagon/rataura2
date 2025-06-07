"""
Integration between the graph manager and Business Rules transitions.

This module provides functions to integrate the graph manager with Business Rules transitions.
"""
from typing import Dict, List, Any, Optional
from sqlalchemy.orm import Session

from rataura2.graph.manager import AgentGraphManager
from rataura2.transitions.business_rules_adapter import TransitionController


class BusinessRulesAgentGraphManager(AgentGraphManager):
    """
    Extended graph manager with Business Rules transition support.
    
    This class extends the base AgentGraphManager to add support for Business Rules transitions.
    """
    
    def check_transitions(self, agent_id: int, context: Dict[str, Any]) -> Optional[int]:
        """
        Check if any transitions should be triggered based on the context.
        
        This method first checks for Business Rules transitions, and if none are triggered,
        falls back to the base implementation.
        
        Args:
            agent_id: ID of the current agent
            context: Context data to check against transition conditions
            
        Returns:
            Optional[int]: ID of the target agent if a transition should be triggered, None otherwise
        """
        # Check for Business Rules transitions
        controller = TransitionController(self.db)
        result = controller.check_transitions(agent_id, context)
        
        if result and "next_agent_id" in result:
            # Update context with any context updates from the Business Rules transition
            if "context_updates" in result and result["context_updates"]:
                context.update(result["context_updates"])
            
            return result["next_agent_id"]
        
        # Fall back to the base implementation
        return super().check_transitions(agent_id, context)


def create_business_rules_graph_manager(meta_agent_id: int, db: Session) -> BusinessRulesAgentGraphManager:
    """
    Create a BusinessRulesAgentGraphManager.
    
    Args:
        meta_agent_id: ID of the meta-agent to build the graph for
        db: SQLAlchemy database session
        
    Returns:
        BusinessRulesAgentGraphManager: A new graph manager instance with Business Rules support
    """
    return BusinessRulesAgentGraphManager(meta_agent_id, db)

