"""
Context management for agent orchestration.

This module provides classes and functions for managing the context object
that carries data about the session and is used for transition decisions.
"""
from typing import Dict, List, Optional, Any, Set, Type
import logging
import json
import time
from dataclasses import dataclass, field, asdict
from enum import Enum

logger = logging.getLogger(__name__)


class ContextScope(str, Enum):
    """Enumeration of context scopes."""
    SESSION = "session"
    CONVERSATION = "conversation"
    AGENT = "agent"
    USER = "user"
    TOOL = "tool"
    CUSTOM = "custom"


@dataclass
class ContextValue:
    """Data structure for a context value."""
    value: Any
    scope: ContextScope
    timestamp: float = field(default_factory=time.time)
    ttl: Optional[float] = None  # Time to live in seconds, None for no expiration
    metadata: Dict[str, Any] = field(default_factory=dict)


class SessionContext:
    """
    Context object for a session.
    
    This class provides a structured way to store and retrieve context data
    for a session, with support for scoping, expiration, and serialization.
    """
    
    def __init__(self):
        """Initialize the session context."""
        self.data: Dict[str, ContextValue] = {}
    
    def set(self, key: str, value: Any, scope: ContextScope = ContextScope.SESSION,
            ttl: Optional[float] = None, metadata: Optional[Dict[str, Any]] = None) -> None:
        """
        Set a value in the context.
        
        Args:
            key: Context key
            value: Context value
            scope: Scope of the value
            ttl: Time to live in seconds, None for no expiration
            metadata: Additional metadata for the value
        """
        self.data[key] = ContextValue(
            value=value,
            scope=scope,
            timestamp=time.time(),
            ttl=ttl,
            metadata=metadata or {}
        )
    
    def get(self, key: str, default: Any = None) -> Any:
        """
        Get a value from the context.
        
        Args:
            key: Context key
            default: Default value to return if the key is not found or expired
            
        Returns:
            Any: The context value, or the default if not found or expired
        """
        # Check if the key exists
        if key not in self.data:
            return default
        
        # Get the context value
        context_value = self.data[key]
        
        # Check if the value has expired
        if context_value.ttl is not None:
            expiration_time = context_value.timestamp + context_value.ttl
            if time.time() > expiration_time:
                # Remove the expired value
                del self.data[key]
                return default
        
        return context_value.value
    
    def get_all(self, scope: Optional[ContextScope] = None) -> Dict[str, Any]:
        """
        Get all values in the context, optionally filtered by scope.
        
        Args:
            scope: Scope to filter by, or None for all scopes
            
        Returns:
            Dict[str, Any]: Dictionary of context values
        """
        result = {}
        
        # Check for expired values and filter by scope
        for key, context_value in list(self.data.items()):
            # Check if the value has expired
            if context_value.ttl is not None:
                expiration_time = context_value.timestamp + context_value.ttl
                if time.time() > expiration_time:
                    # Remove the expired value
                    del self.data[key]
                    continue
            
            # Filter by scope
            if scope is None or context_value.scope == scope:
                result[key] = context_value.value
        
        return result
    
    def remove(self, key: str) -> bool:
        """
        Remove a value from the context.
        
        Args:
            key: Context key
            
        Returns:
            bool: True if the key was removed, False if it wasn't found
        """
        if key in self.data:
            del self.data[key]
            return True
        
        return False
    
    def clear(self, scope: Optional[ContextScope] = None) -> None:
        """
        Clear all values in the context, optionally filtered by scope.
        
        Args:
            scope: Scope to filter by, or None for all scopes
        """
        if scope is None:
            self.data.clear()
        else:
            # Remove values with the specified scope
            for key, context_value in list(self.data.items()):
                if context_value.scope == scope:
                    del self.data[key]
    
    def update_from_dict(self, data: Dict[str, Any], scope: ContextScope = ContextScope.SESSION,
                        ttl: Optional[float] = None, metadata: Optional[Dict[str, Any]] = None) -> None:
        """
        Update the context from a dictionary.
        
        Args:
            data: Dictionary of values to update
            scope: Scope for the values
            ttl: Time to live in seconds, None for no expiration
            metadata: Additional metadata for the values
        """
        for key, value in data.items():
            self.set(key, value, scope, ttl, metadata)
    
    def to_dict(self) -> Dict[str, Any]:
        """
        Convert the context to a dictionary.
        
        Returns:
            Dict[str, Any]: Dictionary representation of the context
        """
        # Create a dictionary with just the values
        result = {}
        
        # Check for expired values
        for key, context_value in list(self.data.items()):
            # Check if the value has expired
            if context_value.ttl is not None:
                expiration_time = context_value.timestamp + context_value.ttl
                if time.time() > expiration_time:
                    # Remove the expired value
                    del self.data[key]
                    continue
            
            result[key] = context_value.value
        
        return result
    
    def to_json(self) -> str:
        """
        Convert the context to a JSON string.
        
        Returns:
            str: JSON representation of the context
        """
        # Convert to a serializable format
        serializable_data = {}
        
        # Check for expired values
        for key, context_value in list(self.data.items()):
            # Check if the value has expired
            if context_value.ttl is not None:
                expiration_time = context_value.timestamp + context_value.ttl
                if time.time() > expiration_time:
                    # Remove the expired value
                    del self.data[key]
                    continue
            
            # Convert the context value to a dictionary
            serializable_data[key] = {
                "value": context_value.value,
                "scope": context_value.scope,
                "timestamp": context_value.timestamp,
                "ttl": context_value.ttl,
                "metadata": context_value.metadata
            }
        
        return json.dumps(serializable_data)
    
    @classmethod
    def from_json(cls, json_str: str) -> "SessionContext":
        """
        Create a session context from a JSON string.
        
        Args:
            json_str: JSON representation of the context
            
        Returns:
            SessionContext: A new session context instance
        """
        # Create a new instance
        context = cls()
        
        # Parse the JSON
        data = json.loads(json_str)
        
        # Add the values to the context
        for key, value_data in data.items():
            context.data[key] = ContextValue(
                value=value_data["value"],
                scope=value_data["scope"],
                timestamp=value_data["timestamp"],
                ttl=value_data["ttl"],
                metadata=value_data["metadata"]
            )
        
        return context


class ContextManager:
    """
    Manager for session contexts.
    
    This class manages multiple session contexts and provides a single
    interface for accessing and updating them.
    """
    
    def __init__(self):
        """Initialize the context manager."""
        self.contexts: Dict[str, SessionContext] = {}
    
    def get_context(self, session_id: str) -> SessionContext:
        """
        Get the context for a session.
        
        Args:
            session_id: ID of the session
            
        Returns:
            SessionContext: The session context
        """
        # Create the context if it doesn't exist
        if session_id not in self.contexts:
            self.contexts[session_id] = SessionContext()
        
        return self.contexts[session_id]
    
    def set_context(self, session_id: str, context: SessionContext) -> None:
        """
        Set the context for a session.
        
        Args:
            session_id: ID of the session
            context: Session context
        """
        self.contexts[session_id] = context
    
    def remove_context(self, session_id: str) -> bool:
        """
        Remove the context for a session.
        
        Args:
            session_id: ID of the session
            
        Returns:
            bool: True if the context was removed, False if it wasn't found
        """
        if session_id in self.contexts:
            del self.contexts[session_id]
            return True
        
        return False
    
    def get_all_session_ids(self) -> List[str]:
        """
        Get the IDs of all sessions with contexts.
        
        Returns:
            List[str]: List of session IDs
        """
        return list(self.contexts.keys())
"""

