# Rataura2

A Livekit conversational agent with tools for EVE Online using directed graphs.

## Overview

Rataura2 is a framework for building conversational agents specialized in the EVE Online universe. It uses a directed graph approach to manage transitions between specialized agents, allowing for a seamless user experience while leveraging domain-specific knowledge.

## Features

- **Directed Graph Agent Management**: Uses NetworkX to model agent transitions
- **Database-Driven Configuration**: Stores agent configurations and transition conditions in SQLite
- **Factory Pattern**: Dynamically generates Livekit agents from database configurations
- **Event-Driven Transitions**: Transitions between agents based on events, tool results, or user input
- **Visualization**: Graph visualization for agent transitions

## Architecture

The system is built with the following components:

1. **Database Models**: SQLAlchemy models for agents, tools, transitions, and meta-agents
2. **Graph Management**: NetworkX-based directed graph for agent transitions
3. **Agent Factory**: Creates Livekit agents from database configurations
4. **Meta-Agent Controller**: Manages transitions between agents

## Installation

```bash
# Clone the repository
git clone https://github.com/alepmalagon/rataura2.git
cd rataura2

# Install the package
pip install -e .
```

## Configuration

Create a `.env` file in the root directory with the following variables:

```
# Database settings
DATABASE_URL=sqlite:///./rataura.db

# Livekit settings
LIVEKIT_URL=ws://localhost:7880
LIVEKIT_API_KEY=your_api_key
LIVEKIT_API_SECRET=your_api_secret

# LLM provider settings
GEMINI_API_KEY=your_gemini_api_key
```

## Usage

[Coming soon]

## License

MIT

