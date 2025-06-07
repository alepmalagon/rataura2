# Business Rules Transitions

This module provides integration between the Business Rules library and our agent transition system. It allows for defining complex transition rules using a user-friendly web interface.

## Overview

The Business Rules transitions system consists of the following components:

1. **BusinessRulesTransition Model**: Extends the base Transition model to store Business Rules definitions.
2. **ConversationVariables**: Defines variables that can be used in Business Rules conditions, based on conversation context.
3. **TransitionActions**: Defines actions that can be triggered when conditions are met.
4. **TransitionController**: Handles the evaluation of Business Rules and triggers transitions.
5. **Web UI Integration**: Provides functions for integrating with the Business Rules UI.

## Usage

### Creating a Business Rules Transition

```python
from sqlalchemy.orm import Session
from rataura2.transitions.business_rules_adapter import create_business_rules_transition

# Define the rules
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
                    "agent_id": target_agent_id
                }
            }
        ]
    }
]

# Create the Business Rules transition
br_transition = create_business_rules_transition(db, transition_id, rules)
```

### Checking Transitions

```python
from rataura2.transitions.business_rules_adapter import TransitionController

# Create a controller
controller = TransitionController(db)

# Define the context
context = {
    "user_input": "Can you help me with ship fittings for PvP combat?",
    "current_agent_name": "General Agent",
    "current_agent_type": "general",
    "turn_count": 1,
}

# Check transitions
result = controller.check_transitions(agent_id, context)

# If a transition should be triggered, result will contain:
# {
#     "next_agent_id": 123,
#     "context_updates": {"key": "value"}
# }
```

### Web UI Integration

To integrate with the Business Rules UI, you can use the functions in the `web_ui` module:

```python
from rataura2.transitions.web_ui import generate_ui_config, rules_to_json, json_to_rules

# Get the UI configuration
config = generate_ui_config()

# Convert a BusinessRulesTransition to JSON for the UI
json_str = rules_to_json(br_transition)

# Convert JSON from the UI to a rules definition
rules = json_to_rules(json_str)
```

## Available Variables

The following variables are available for use in Business Rules conditions:

- `user_input`: The user's input text
- `current_agent_name`: The name of the current agent
- `current_agent_type`: The type of the current agent
- `conversation_turn_count`: The number of turns in the conversation
- `is_first_turn`: Whether this is the first turn in the conversation
- `user_input_type`: The type of the user's input (question, statement, command, unknown)
- `last_tool_name`: The name of the last tool used
- `last_tool_result`: The result of the last tool used as a JSON string

## Available Actions

The following actions are available for use in Business Rules:

- `transition_to_agent`: Transition to a specific agent
- `set_context_value`: Set a value in the context
- `log_transition`: Log that a transition was triggered

## Example

See the `examples/business_rules_example.py` file for a complete example of how to use Business Rules transitions.

## Web UI

To use the Business Rules UI, you need to include the following JavaScript libraries in your web application:

- [business-rules-ui](https://github.com/venmo/business-rules-ui): The Business Rules UI library

You can then use the API functions in the `api` module to interact with the Business Rules transitions:

```python
from rataura2.transitions.api import (
    get_ui_config,
    get_transition_rules,
    create_or_update_transition_rules,
    delete_transition_rules,
    get_agent_transitions_with_rules,
)

# Get the UI configuration
config = get_ui_config()

# Get the rules for a transition
rules = get_transition_rules(db, transition_id)

# Create or update rules for a transition
rules = create_or_update_transition_rules(db, transition_id, rules_json)

# Delete rules for a transition
success = delete_transition_rules(db, transition_id)

# Get all transitions for an agent with their rules
transitions = get_agent_transitions_with_rules(db, agent_id)
```

