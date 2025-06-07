"""
Graph manager for agent transitions using NetworkX.
"""
from typing import Dict, List, Optional, Any, Tuple
import json
import networkx as nx
from sqlalchemy.orm import Session

from rataura2.db.models import Agent, Transition, Conversation


class AgentGraphManager:
    """
    Manager for agent transition graphs using NetworkX.
    This class provides methods to build, visualize, and manage directed graphs
    of agents and their transitions.
    """
    
    def __init__(self, conversation_id: int, db: Session):
        """
        Initialize the graph manager.
        
        Args:
            conversation_id: ID of the conversation to build the graph for
            db: SQLAlchemy database session
        """
        self.conversation_id = conversation_id
        self.db = db
        self.graph = nx.DiGraph()
        self.conversation = None
        self.agents = {}
        self.transitions = []
        
        # Build the graph
        self._build_graph()
    
    def _build_graph(self) -> None:
        """Build the directed graph from the database."""
        # Get the conversation
        self.conversation = self.db.query(Conversation).filter(Conversation.id == self.conversation_id).first()
        if not self.conversation:
            raise ValueError(f"Conversation with ID {self.conversation_id} not found")
        
        # Get all agents associated with this conversation
        agents = self.db.query(Agent).join(
            Conversation.agents
        ).filter(
            Conversation.id == self.conversation_id
        ).all()
        
        # Add agents as nodes
        for agent in agents:
            self.agents[agent.id] = agent
            self.graph.add_node(
                agent.id,
                name=agent.name,
                agent_type=agent.agent_type,
                llm_provider=agent.llm_provider,
                llm_model=agent.llm_model,
            )
        
        # Get all transitions between these agents
        transitions = self.db.query(Transition).filter(
            Transition.source_agent_id.in_([a.id for a in agents]),
            Transition.target_agent_id.in_([a.id for a in agents])
        ).all()
        
        # Add transitions as edges
        for transition in transitions:
            self.transitions.append(transition)
            self.graph.add_edge(
                transition.source_agent_id,
                transition.target_agent_id,
                id=transition.id,
                condition_type=transition.condition_type,
                condition_data=transition.condition_data,
                priority=transition.priority,
                description=transition.description,
                tool_id=transition.tool_id
            )
    
    def get_initial_agent(self) -> Agent:
        """
        Get the initial agent for the conversation.
        
        Returns:
            Agent: The initial agent
        """
        if not self.conversation:
            raise ValueError("Conversation not loaded")
        
        return self.agents.get(self.conversation.initial_agent_id)
    
    def get_agent_transitions(self, agent_id: int) -> List[Dict[str, Any]]:
        """
        Get all transitions from a specific agent.
        
        Args:
            agent_id: ID of the agent
            
        Returns:
            List[Dict[str, Any]]: List of transitions as dictionaries
        """
        if agent_id not in self.graph:
            raise ValueError(f"Agent with ID {agent_id} not found in the graph")
        
        transitions = []
        for _, target, data in self.graph.out_edges(agent_id, data=True):
            transitions.append({
                "id": data.get("id"),
                "target_agent_id": target,
                "target_agent_name": self.agents[target].name,
                "condition_type": data.get("condition_type"),
                "condition_data": data.get("condition_data"),
                "priority": data.get("priority", 0),
                "description": data.get("description"),
                "tool_id": data.get("tool_id")
            })
        
        # Sort by priority (higher first)
        return sorted(transitions, key=lambda x: x["priority"], reverse=True)
    
    def check_transitions(self, agent_id: int, context: Dict[str, Any]) -> Optional[int]:
        """
        Check if any transitions should be triggered based on the context.
        
        Args:
            agent_id: ID of the current agent
            context: Context data to check against transition conditions
            
        Returns:
            Optional[int]: ID of the target agent if a transition should be triggered, None otherwise
        """
        transitions = self.get_agent_transitions(agent_id)
        
        for transition in transitions:
            condition_type = transition["condition_type"]
            condition_data = transition["condition_data"] or {}
            
            if self._check_condition(condition_type, condition_data, context):
                return transition["target_agent_id"]
        
        return None
    
    def _check_condition(self, condition_type: str, condition_data: Dict[str, Any], 
                         context: Dict[str, Any]) -> bool:
        """
        Check if a condition is met based on the context.
        
        Args:
            condition_type: Type of condition
            condition_data: Condition data
            context: Context data to check against
            
        Returns:
            bool: True if the condition is met, False otherwise
        """
        if condition_type == "tool_result":
            # Check if a tool result matches the condition
            tool_id = condition_data.get("tool_id")
            result_key = condition_data.get("result_key")
            expected_value = condition_data.get("expected_value")
            operator = condition_data.get("operator", "eq")
            
            if "tool_results" not in context:
                return False
            
            tool_results = context.get("tool_results", {})
            if str(tool_id) not in tool_results:
                return False
            
            result = tool_results[str(tool_id)]
            if result_key not in result:
                return False
            
            actual_value = result[result_key]
            
            # Compare based on operator
            if operator == "eq":
                return actual_value == expected_value
            elif operator == "neq":
                return actual_value != expected_value
            elif operator == "gt":
                return actual_value > expected_value
            elif operator == "lt":
                return actual_value < expected_value
            elif operator == "contains":
                return expected_value in actual_value
            elif operator == "not_contains":
                return expected_value not in actual_value
            
        elif condition_type == "user_input":
            # Check if user input matches the condition
            pattern = condition_data.get("pattern")
            if not pattern or "user_input" not in context:
                return False
            
            user_input = context.get("user_input", "")
            
            # Simple pattern matching (could be enhanced with regex)
            return pattern.lower() in user_input.lower()
            
        elif condition_type == "agent_decision":
            # Check if the agent has decided to transition
            decision_key = condition_data.get("decision_key", "transition_to")
            expected_value = condition_data.get("expected_value")
            
            if "agent_decisions" not in context:
                return False
            
            agent_decisions = context.get("agent_decisions", {})
            if decision_key not in agent_decisions:
                return False
            
            return agent_decisions[decision_key] == expected_value
            
        elif condition_type == "event":
            # Check if an event matches the condition
            event_type = condition_data.get("event_type")
            event_data = condition_data.get("event_data", {})
            
            if "events" not in context:
                return False
            
            events = context.get("events", [])
            for event in events:
                if event.get("type") != event_type:
                    continue
                
                # Check if all event_data keys match
                match = True
                for key, value in event_data.items():
                    if key not in event or event[key] != value:
                        match = False
                        break
                
                if match:
                    return True
            
            return False
            
        elif condition_type == "custom":
            # Custom condition logic would be implemented here
            # This could involve calling a custom function or evaluating a DSL
            condition_code = condition_data.get("condition_code")
            if not condition_code:
                return False
            
            # For security reasons, we're not executing arbitrary code here
            # In a real implementation, this would use a safe evaluation mechanism
            return False
        
        return False
    
    def draw_graph(self, filename: str = "agent_graph.png") -> None:
        """
        Draw the graph and save it to a file.
        
        Args:
            filename: Name of the file to save the graph to
        """
        import matplotlib.pyplot as plt
        
        # Create a copy of the graph with agent names as labels
        graph = self.graph.copy()
        
        # Relabel nodes with agent names
        mapping = {agent_id: agent.name for agent_id, agent in self.agents.items()}
        graph = nx.relabel_nodes(graph, mapping)
        
        # Set up the plot
        plt.figure(figsize=(12, 8))
        
        # Use spring layout for node positioning
        pos = nx.spring_layout(graph, seed=42)
        
        # Draw nodes
        nx.draw_networkx_nodes(graph, pos, node_size=2000, node_color="lightblue", alpha=0.8)
        
        # Draw edges
        nx.draw_networkx_edges(graph, pos, width=2, alpha=0.5, edge_color="gray", 
                              arrowsize=20, connectionstyle="arc3,rad=0.1")
        
        # Draw labels
        nx.draw_networkx_labels(graph, pos, font_size=10, font_family="sans-serif")
        
        # Draw edge labels (transition types)
        edge_labels = {(u, v): d.get("condition_type", "") 
                      for u, v, d in graph.edges(data=True)}
        nx.draw_networkx_edge_labels(graph, pos, edge_labels=edge_labels, font_size=8)
        
        # Set title
        plt.title(f"Agent Transition Graph for {self.conversation.name}", size=15)
        
        # Remove axis
        plt.axis("off")
        
        # Save the figure
        plt.tight_layout()
        plt.savefig(filename, dpi=300, bbox_inches="tight")
        plt.close()
    
    def to_json(self) -> str:
        """
        Convert the graph to a JSON string.
        
        Returns:
            str: JSON representation of the graph
        """
        data = {
            "conversation": {
                "id": self.conversation.id,
                "name": self.conversation.name,
                "description": self.conversation.description,
                "initial_agent_id": self.conversation.initial_agent_id
            },
            "nodes": [],
            "edges": []
        }
        
        # Add nodes
        for agent_id, agent in self.agents.items():
            data["nodes"].append({
                "id": agent.id,
                "name": agent.name,
                "agent_type": agent.agent_type,
                "llm_provider": agent.llm_provider,
                "llm_model": agent.llm_model
            })
        
        # Add edges
        for source, target, attrs in self.graph.edges(data=True):
            data["edges"].append({
                "source": source,
                "target": target,
                "id": attrs.get("id"),
                "condition_type": attrs.get("condition_type"),
                "condition_data": attrs.get("condition_data"),
                "priority": attrs.get("priority", 0),
                "description": attrs.get("description"),
                "tool_id": attrs.get("tool_id")
            })
        
        return json.dumps(data, indent=2)
    
    @classmethod
    def from_json(cls, json_str: str, db: Session) -> "AgentGraphManager":
        """
        Create a graph manager from a JSON string.
        
        Args:
            json_str: JSON representation of the graph
            db: SQLAlchemy database session
            
        Returns:
            AgentGraphManager: A new graph manager instance
        """
        data = json.loads(json_str)
        
        # Create a new instance
        conversation_id = data["conversation"]["id"]
        manager = cls(conversation_id, db)
        
        # Clear the existing graph
        manager.graph.clear()
        
        # Add nodes
        for node in data["nodes"]:
            manager.graph.add_node(
                node["id"],
                name=node["name"],
                agent_type=node["agent_type"],
                llm_provider=node["llm_provider"],
                llm_model=node["llm_model"]
            )
        
        # Add edges
        for edge in data["edges"]:
            manager.graph.add_edge(
                edge["source"],
                edge["target"],
                id=edge["id"],
                condition_type=edge["condition_type"],
                condition_data=edge["condition_data"],
                priority=edge["priority"],
                description=edge["description"],
                tool_id=edge["tool_id"]
            )
        
        return manager

