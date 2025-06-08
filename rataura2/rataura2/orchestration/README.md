# Agent Orchestration System

This module provides a system for orchestrating transitions between agents based on events and business rules. It integrates with Livekit to handle real-time communication and uses a directed graph approach to manage agent transitions.

## Overview

The agent orchestration system consists of several components:

1. **Event System**: Handles events from Livekit and other sources, updating the context object with event data.
2. **Context Management**: Maintains a context object that carries data about the session and is used for transition decisions.
3. **Graph Manager**: Uses a directed graph to represent agents and transitions between them.
4. **Business Rules Integration**: Evaluates business rules to determine when transitions should occur.
5. **Session Management**: Manages active sessions and their associated orchestrators.
6. **Livekit Integration**: Integrates with Livekit to handle real-time communication.

## Components

### Event System

The event system is responsible for handling events from Livekit and other sources. It consists of:

- `EventData`: Data structure for event information.
- `EventHandler`: Base class for event handlers.
- `LivekitEventHandler`: Handler for Livekit events.
- `SessionEventHandler`: Handler for session events.
- `AgentEventHandler`: Handler for agent events.
- `EventManager`: Manager for event handlers.

### Context Management

The context management system maintains a context object that carries data about the session. It consists of:

- `ContextValue`: Data structure for a context value.
- `SessionContext`: Context object for a session.
- `ContextManager`: Manager for session contexts.

### Orchestrator

The orchestrator is the main component of the system. It coordinates the event system, graph manager, and agent factory to manage transitions between agents. It consists of:

- `AgentOrchestrator`: Orchestrator for managing agent transitions.
- `SessionManager`: Manager for active sessions.

### Livekit Integration

The Livekit integration components handle the integration with Livekit. They consist of:

- `LivekitSessionHandler`: Handler for Livekit sessions.
- `LivekitAgentFactory`: Factory for creating Livekit agents with orchestration support.

## Usage

To use the agent orchestration system, you need to:

1. Create a database session.
2. Create a session manager.
3. Create a session with a conversation ID.
4. Process events through the orchestrator.

Here's a simple example:

```python
from sqlalchemy.orm import Session
from rataura2.orchestration.orchestrator import SessionManager
from rataura2.livekit_agent.events import EventData, EventType

# Create a database session
db = Session()

# Create a session manager
session_manager = SessionManager(db)

# Create a session
session_id = "example:123"
conversation_id = 1
orchestrator = session_manager.create_session(session_id, conversation_id)

# Process events
event = EventData(
    type=EventType.USER_MESSAGE,
    timestamp=time.time(),
    data={"message": "Hello, I'm interested in combat in EVE Online."},
    source="user"
)
orchestrator.process_event(event)

# Check for transitions
orchestrator.check_and_execute_transition()

# Get the current agent
current_agent = orchestrator.get_current_agent()
```

For a more complete example, see the `examples/agent_orchestration_example.py` file.

## Business Rules Integration

The system integrates with the business rules engine to determine when transitions should occur. Business rules are defined in the database and are evaluated against the context object.

To create a business rule transition:

```python
from rataura2.transitions.business_rules_adapter import create_business_rules_transition

# Create a business rule transition
rules = [
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

create_business_rules_transition(db, transition.id, rules)
```

## Livekit Integration

The system integrates with Livekit to handle real-time communication. It processes Livekit events and forwards them to the appropriate orchestrator.

To use the Livekit integration:

```python
from rataura2.orchestration.livekit_integration import LivekitSessionHandler

# Create a Livekit session handler
livekit_handler = LivekitSessionHandler(db, session_manager)

# Register a room
livekit_handler.register_room(room)

# Handle room events
await livekit_handler.handle_room_event(room, event)

# Handle participant events
await livekit_handler.handle_participant_event(room, participant, event)

# Handle agent events
await livekit_handler.handle_agent_event(room, agent, event)
```

## Event Types

The system supports the following event types:

- **Session Events**: `SESSION_CREATED`, `SESSION_ENDED`, `USER_JOINED`, `USER_LEFT`
- **Agent Events**: `AGENT_STARTED`, `AGENT_STOPPED`, `AGENT_ERROR`
- **Conversation Events**: `USER_MESSAGE`, `AGENT_MESSAGE`, `TOOL_CALLED`, `TOOL_RESULT`
- **Custom Events**: `CUSTOM`

## Context Structure

The context object has the following structure:

- `conversation_id`: ID of the conversation.
- `conversation_name`: Name of the conversation.
- `conversation_description`: Description of the conversation.
- `initial_agent_id`: ID of the initial agent.
- `initial_agent_name`: Name of the initial agent.
- `current_agent_id`: ID of the current agent.
- `current_agent_name`: Name of the current agent.
- `turn_count`: Number of turns in the conversation.
- `events`: List of events that have occurred.
- `tool_results`: Results of tool calls.
- `agent_decisions`: Decisions made by agents.
- `user_input`: The most recent user input.
- `session`: Information about the session.
- `agents`: Information about the agents in the conversation.
- `conversation`: The conversation history.

## Transition Conditions

Transitions can be triggered by the following conditions:

- **Event Conditions**: Triggered when an event matches the specified criteria.
- **Tool Result Conditions**: Triggered when a tool result matches the specified criteria.
- **User Input Conditions**: Triggered when user input matches the specified criteria.
- **Agent Decision Conditions**: Triggered when an agent makes a decision.
- **Business Rules Conditions**: Triggered when a business rule evaluates to true.

## Example

For a complete example of how to use the agent orchestration system, see the `examples/agent_orchestration_example.py` file. This example creates a simulated conversation with multiple agents and shows how transitions between agents are triggered by events.

