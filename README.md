# Rataura2

Rataura2 is a Livekit 1.x project for AI conversational agents specialized in the EVE Online universe. The project supports switching between agents using a directed graph for transitions, allowing for specialized handling of different knowledge fields about the game.

## Features

- **Agent Switching**: Transition between specialized agents based on conversation context
- **Directed Graph**: Map agents as nodes and transitions as edges using networkx.DiGraph
- **Business Rules**: Define transition conditions using the business-rules library
- **Database Storage**: Store agent configurations, tools, and transitions in SQLite
- **Livekit Integration**: Handle Livekit events and trigger agent transitions

## Architecture

The project follows this logical architecture:

1. **Directed Graphs**: Managed by the networkx.DiGraph Python tool
2. **Graph Visualization**: Using networkx.draw for graphical representation and editing
3. **Database**: SQLite for storing agent configurations, tools, and transitions
4. **Agent Factory**: Generates Livekit agents with data loaded from the database
5. **Transition System**: Implements a "check_for_transition" algorithm to switch the active agent

## Project Structure

```
rataura2/
├── db/
│   ├── models/
│   │   ├── base.py         # SQLAlchemy base models and mixins
│   │   └── agent.py        # Agent, Tool, and Transition models
├── transitions/
│   ├── business_rules_adapter.py  # Business Rules integration
│   ├── web_ui.py                  # UI configuration and utilities
│   └── api.py                     # API functions for managing transitions
└── tests/
    ├── test_business_rules.py     # Tests for Business Rules transitions
    └── test_simple.py             # Simple tests for package structure
```

## Installation

1. Clone the repository:
   ```bash
   git clone https://github.com/alepmalagon/rataura2.git
   cd rataura2
   ```

2. Install dependencies:
   ```bash
   pip install sqlalchemy pydantic business-rules networkx
   ```

## Usage

The project is designed to be used as a library for building Livekit agents with transition capabilities. Here's a basic example of how to use it:

```python
from rataura2.db.models.agent import Agent, Transition
from rataura2.transitions.business_rules_adapter import TransitionController

# Create a database session
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
engine = create_engine("sqlite:///rataura2.db")
Session = sessionmaker(bind=engine)
db = Session()

# Check for transitions
controller = TransitionController(db)
context = {
    "user_input": "Tell me about combat in EVE Online",
    "current_agent_name": "General Agent",
    "current_agent_type": "general",
    "turn_count": 1,
}
result = controller.check_transitions(current_agent_id, context)

if result:
    # Switch to the new agent
    next_agent_id = result["next_agent_id"]
    # Load the new agent and continue the conversation
```

## Testing

Run the tests using unittest:

```bash
python -m unittest discover tests
```

## License

This project is licensed under the MIT License - see the LICENSE file for details.

