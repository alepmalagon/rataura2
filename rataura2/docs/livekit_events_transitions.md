# Using Livekit Events for Agent Transitions

This document explains how to use Livekit events to trigger agent transitions in the rataura2 project.

## Overview

The rataura2 project includes a comprehensive event system that can be used to trigger transitions between different agents based on various conditions. One of the supported condition types is `livekit_event`, which allows transitions to be triggered based on events from the Livekit framework.

## Livekit Event Types

The following Livekit event types are supported:

### Session Events
- `session:created` - Triggered when a new session is created
- `session:ended` - Triggered when a session ends

### Participant Events
- `participant:joined` - Triggered when a participant joins a room
- `participant:left` - Triggered when a participant leaves a room

### Agent Lifecycle Events
- `agent:started` - Triggered when an agent starts
- `agent:stopped` - Triggered when an agent stops
- `agent:error` - Triggered when an agent encounters an error

### Conversation Events
- `message:received` - Triggered when a user sends a message
- `message:sent` - Triggered when the agent sends a message
- `tool:called` - Triggered when the agent calls a tool
- `tool:result` - Triggered when a tool returns a result

## Internal Event Mapping

These Livekit events are mapped to internal event types in the `LivekitEventHandler` class:

```python
{
    "session:created": EventType.SESSION_CREATED,
    "session:ended": EventType.SESSION_ENDED,
    "participant:joined": EventType.USER_JOINED,
    "participant:left": EventType.USER_LEFT,
    "agent:started": EventType.AGENT_STARTED,
    "agent:stopped": EventType.AGENT_STOPPED,
    "agent:error": EventType.AGENT_ERROR,
    "message:received": EventType.USER_MESSAGE,
    "message:sent": EventType.AGENT_MESSAGE,
    "tool:called": EventType.TOOL_CALLED,
    "tool:result": EventType.TOOL_RESULT,
}
```

## Setting Up Livekit Event Transitions

To set up a transition based on a Livekit event, you need to:

1. Create a transition in the database with the condition type `livekit_event`
2. Specify the event name and any additional conditions in the condition data

### Example Transition Configuration

Here's an example of how to configure a transition based on a Livekit event:

```python
# Transition when a user leaves the room
transition = Transition(
    source_agent_id=1,  # ID of the source agent
    target_agent_id=2,  # ID of the target agent
    condition_type="livekit_event",
    condition_data={
        "event_name": "USER_LEFT",
        "event_data": {
            "participant_id": "specific_user_id"  # Optional: only trigger for a specific user
        }
    }
)
```

### Condition Data Structure

The condition data for a `livekit_event` transition should have the following structure:

```python
{
    "event_name": str,  # Required: The name of the event (e.g., "USER_LEFT")
    "event_data": {     # Optional: Additional conditions on event data
        "key1": "value1",
        "key2": "value2",
        # ...
    }
}
```

The `event_name` should be one of the internal event types (e.g., `USER_LEFT`, `AGENT_STARTED`, etc.).

The `event_data` is optional and can contain key-value pairs that must match the data in the event for the transition to be triggered.

## Implementation Details

The `livekit_event` condition type is implemented in the `_check_condition` method of the `GraphManager` class. It checks if an event with the specified name and data exists in the context's event history.

All Livekit events are processed by the `LivekitEventHandler` class, which converts them to the internal event format and adds them to the context.

## Example Use Cases

Here are some example use cases for Livekit event-based transitions:

1. **Handoff to a specialized agent**: Transition to a specialized agent when a specific tool is called
   ```python
   {
       "event_name": "TOOL_CALLED",
       "event_data": {
           "tool_name": "specialized_tool"
       }
   }
   ```

2. **Cleanup agent**: Transition to a cleanup agent when a session ends
   ```python
   {
       "event_name": "SESSION_ENDED"
   }
   ```

3. **Error recovery**: Transition to an error recovery agent when an agent error occurs
   ```python
   {
       "event_name": "AGENT_ERROR"
   }
   ```

4. **Welcome agent**: Transition to a welcome agent when a new user joins
   ```python
   {
       "event_name": "USER_JOINED"
   }
   ```

## Debugging

To debug Livekit event transitions, you can:

1. Check the context's event history to see if the expected events are being recorded
2. Add logging to the `_check_condition` method to see which conditions are being evaluated
3. Verify that the event handler is correctly processing Livekit events

## Conclusion

Using Livekit events for agent transitions provides a powerful way to create dynamic, responsive agent behaviors based on real-time events in the Livekit framework. This can be used to create more natural and context-aware conversational experiences.

