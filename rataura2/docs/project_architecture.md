# Rataura2 Project Architecture Report

## 1. Introduction

Rataura2 is a sophisticated agent orchestration system built on top of the Livekit framework. It enables the creation of dynamic, context-aware conversational agents that can transition between different specialized behaviors based on various conditions. This report provides a detailed overview of the project's architecture, focusing on the business logic, agent storage in the digraph, and transition mechanisms.

## 2. Core Components

### 2.1 Database Models

The system uses SQLAlchemy ORM with several key models:

#### Agent Model
```python
class Agent(BaseModel):
    name: Mapped[str]
    description: Mapped[str]
    instructions: Mapped[str]
    agent_type: Mapped[str]  # general, combat, industry, market, etc.
    llm_provider: Mapped[str]  # gemini, openai, anthropic
    llm_model: Mapped[str]
    stt_provider: Mapped[str]  # google, deepgram, whisper, none
    tts_provider: Mapped[str]  # google, elevenlabs, none
    is_active: Mapped[bool]
    config: Mapped[Dict]
    
    # Relationships
    tools: Mapped[List[Tool]]
    outgoing_transitions: Mapped[List[Transition]]
    incoming_transitions: Mapped[List[Transition]]
    meta_agents: Mapped[List[MetaAgent]]
```

#### Tool Model
```python
class Tool(BaseModel):
    name: Mapped[str]
    description: Mapped[str]
    function_name: Mapped[str]
    parameters_schema: Mapped[Dict]
    is_active: Mapped[bool]
    
    # Relationships
    agents: Mapped[List[Agent]]
    transitions: Mapped[List[Transition]]
```

#### Transition Model
```python
class Transition(BaseModel):
    source_agent_id: Mapped[int]
    target_agent_id: Mapped[int]
    condition_type: Mapped[str]  # tool_result, user_input, agent_decision, event, custom, livekit_event
    condition_data: Mapped[Dict]
    priority: Mapped[int]
    description: Mapped[str]
    tool_id: Mapped[Optional[int]]
    
    # Relationships
    source_agent: Mapped[Agent]
    target_agent: Mapped[Agent]
    tool: Mapped[Optional[Tool]]
```

#### MetaAgent Model
```python
class MetaAgent(BaseModel):
    name: Mapped[str]
    description: Mapped[str]
    initial_agent_id: Mapped[int]
    is_active: Mapped[bool]
    config: Mapped[Dict]
    
    # Relationships
    initial_agent: Mapped[Agent]
    agents: Mapped[List[Agent]]
```

### 2.2 Agent Factory

The `AgentFactory` class is responsible for creating Livekit agent instances from database models:

```python
class AgentFactory:
    def create_agent(self, agent_id: int) -> LivekitAgent:
        # Get the agent from the database
        agent = self.db.query(Agent).filter(Agent.id == agent_id).first()
        
        # Configure agent arguments based on the agent model
        agent_args = {
            "instructions": agent.instructions,
        }
        
        # Configure LLM provider (gemini, openai, anthropic)
        # Configure STT provider (google, deepgram, whisper)
        # Configure TTS provider (google, elevenlabs)
        
        # Create the Livekit agent
        livekit_agent = DynamicAgent(**agent_args)
        
        # Add tools to the agent
        for tool in tools:
            livekit_agent.add_tool(tool.name, tool.function_name, tool.description)
        
        return livekit_agent
```

### 2.3 Event System

The event system is responsible for processing events and updating the context:

#### Event Types
```python
class EventType(str, Enum):
    # Session events
    SESSION_CREATED = "session_created"
    SESSION_ENDED = "session_ended"
    USER_JOINED = "user_joined"
    USER_LEFT = "user_left"
    
    # Agent events
    AGENT_STARTED = "agent_started"
    AGENT_STOPPED = "agent_stopped"
    AGENT_ERROR = "agent_error"
    
    # Conversation events
    USER_MESSAGE = "user_message"
    AGENT_MESSAGE = "agent_message"
    TOOL_CALLED = "tool_called"
    TOOL_RESULT = "tool_result"
    
    # Custom events
    CUSTOM = "custom"
```

#### Event Handlers

1. **EventHandler (Base Class)**
   - Manages event callbacks
   - Maintains event history in context
   - Limits history to last 100 events

2. **LivekitEventHandler**
   - Maps Livekit events to internal event types
   - Processes Livekit events into internal format

3. **SessionEventHandler**
   - Manages session lifecycle events
   - Tracks participant joins/leaves

4. **AgentEventHandler**
   - Manages agent lifecycle events
   - Tracks messages and tool usage

#### Event Manager

The `EventManager` class coordinates multiple event handlers and provides a single interface for processing events:

```python
class EventManager:
    def register_handler(self, name: str, handler: EventHandler) -> None:
        self.handlers[name] = handler
    
    def process_event(self, event: EventData) -> None:
        for handler in self.handlers.values():
            handler.handle_event(event, self.context)
    
    def process_livekit_event(self, livekit_event: LivekitEvent) -> None:
        # Find the Livekit event handler
        for handler in self.handlers.values():
            if isinstance(handler, LivekitEventHandler):
                handler.process_livekit_event(livekit_event, self.context)
                break
```

## 3. Agent Graph and Transitions

### 3.1 Agent Graph Manager

The `AgentGraphManager` class is responsible for building, visualizing, and managing directed graphs of agents and their transitions using NetworkX:

```python
class AgentGraphManager:
    def _build_graph(self) -> None:
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
```

### 3.2 Transition Conditions

The system supports multiple transition condition types:

1. **Tool Result Based**
   ```python
   {
       "condition_type": "tool_result",
       "condition_data": {
           "tool_id": "123",
           "result_key": "status",
           "expected_value": "success",
           "operator": "eq"
       }
   }
   ```

2. **User Input Based**
   ```python
   {
       "condition_type": "user_input",
       "condition_data": {
           "pattern": "help"
       }
   }
   ```

3. **Agent Decision Based**
   ```python
   {
       "condition_type": "agent_decision",
       "condition_data": {
           "decision_key": "transition_to",
           "expected_value": "target_agent_id"
       }
   }
   ```

4. **Event Based**
   ```python
   {
       "condition_type": "event",
       "condition_data": {
           "event_type": "USER_LEFT",
           "event_data": {
               "participant_id": "specific_user"
           }
       }
   }
   ```

5. **Livekit Event Based**
   ```python
   {
       "condition_type": "livekit_event",
       "condition_data": {
           "event_name": "USER_LEFT",
           "event_data": {
               "participant_id": "specific_user_id"
           }
       }
   }
   ```

6. **Custom**
   ```python
   {
       "condition_type": "custom",
       "condition_data": {
           "condition_code": "custom_condition_logic"
       }
   }
   ```

### 3.3 Transition Checking Process

The `check_transitions` method in `AgentGraphManager` is responsible for checking if any transitions should be triggered:

```python
def check_transitions(self, agent_id: int, context: Dict[str, Any]) -> Optional[int]:
    transitions = self.get_agent_transitions(agent_id)
    
    for transition in transitions:
        condition_type = transition["condition_type"]
        condition_data = transition["condition_data"] or {}
        
        if self._check_condition(condition_type, condition_data, context):
            return transition["target_agent_id"]
    
    return None
```

The `_check_condition` method evaluates different condition types:

```python
def _check_condition(self, condition_type: str, condition_data: Dict[str, Any], 
                     context: Dict[str, Any]) -> bool:
    if condition_type == "tool_result":
        # Check if a tool result matches the condition
        # ...
    elif condition_type == "user_input":
        # Check if user input matches the condition
        # ...
    elif condition_type == "agent_decision":
        # Check if the agent has decided to transition
        # ...
    elif condition_type == "event":
        # Check if an event matches the condition
        # ...
    elif condition_type == "livekit_event":
        # Check if a Livekit event matches the condition
        # ...
    elif condition_type == "custom":
        # Custom condition logic
        # ...
    
    return False
```

## 4. Orchestration

### 4.1 Agent Orchestrator

The `AgentOrchestrator` class coordinates the event system, graph manager, and agent factory to manage transitions between agents:

```python
class AgentOrchestrator:
    def __init__(self, db: Session, conversation_id: int, use_business_rules: bool = True):
        # Create the graph manager
        if use_business_rules:
            self.graph_manager = BusinessRulesAgentGraphManager(conversation_id, db)
        else:
            self.graph_manager = AgentGraphManager(conversation_id, db)
        
        # Create the agent factory
        self.agent_factory = AgentFactory(db)
        
        # Create the conversation controller
        self.conversation = self.db.query(Conversation).filter(
            Conversation.id == conversation_id
        ).first()
        
        self.controller = ConversationController(
            self.conversation, self.graph_manager, self.agent_factory
        )
        
        # Create the event manager
        self.event_manager = EventManager()
        
        # Register event handlers
        self.event_manager.register_handler("livekit", LivekitEventHandler())
        self.event_manager.register_handler("session", SessionEventHandler())
        self.event_manager.register_handler("agent", AgentEventHandler())
```

### 4.2 Transition Execution

The `execute_transition` method in `AgentOrchestrator` is responsible for executing a transition to a new agent:

```python
def execute_transition(self, target_agent_id: int) -> TransitionResult:
    try:
        # Get the current context
        context = self.event_manager.get_context()
        
        # Get the current agent ID
        current_agent_id = context.get("current_agent_id")
        if not current_agent_id:
            return TransitionResult.ERROR
        
        # Skip if the target is the same as the current agent
        if target_agent_id == current_agent_id:
            return TransitionResult.NO_TRANSITION
        
        # Get the target agent
        target_agent = self.db.query(Agent).filter(Agent.id == target_agent_id).first()
        if not target_agent:
            logger.error(f"Target agent with ID {target_agent_id} not found")
            return TransitionResult.ERROR
        
        # Log the transition
        logger.info(f"Transitioning from agent {current_agent_id} to agent {target_agent_id}")
        
        # Update the context
        context["previous_agent_id"] = current_agent_id
        context["current_agent_id"] = target_agent_id
        context["current_agent_name"] = target_agent.name
        
        # Create an event for the transition
        transition_event = EventData(
            type=EventType.CUSTOM,
            timestamp=time.time(),
            data={
                "previous_agent_id": current_agent_id,
                "target_agent_id": target_agent_id,
                "transition_type": "orchestrator"
            },
            source="orchestrator"
        )
        
        # Process the transition event
        self.event_manager.process_event(transition_event)
        
        # Update the controller
        self.controller.current_agent_id = target_agent_id
        self.controller.context = context
        self.controller._create_current_agent()
        
        return TransitionResult.SUCCESS
    
    except Exception as e:
        logger.error(f"Error executing transition: {e}")
        return TransitionResult.ERROR
```

### 4.3 Event-Triggered Transitions

The system registers callbacks for various events to trigger transition checks:

```python
def _setup_transition_checking(self) -> None:
    # Get the agent event handler
    agent_handler = None
    for name, handler in self.event_manager.handlers.items():
        if isinstance(handler, AgentEventHandler):
            agent_handler = handler
            break
    
    if agent_handler:
        # Register callbacks for events that should trigger transition checks
        agent_handler.register_callback(
            EventType.USER_MESSAGE, self._check_transition_after_event
        )
        agent_handler.register_callback(
            EventType.TOOL_RESULT, self._check_transition_after_event
        )
        agent_handler.register_callback(
            EventType.AGENT_MESSAGE, self._check_transition_after_event
        )
        
        # Register callbacks for Livekit events
        agent_handler.register_callback(
            EventType.SESSION_CREATED, self._check_transition_after_event
        )
        agent_handler.register_callback(
            EventType.SESSION_ENDED, self._check_transition_after_event
        )
        agent_handler.register_callback(
            EventType.USER_JOINED, self._check_transition_after_event
        )
        agent_handler.register_callback(
            EventType.USER_LEFT, self._check_transition_after_event
        )
        agent_handler.register_callback(
            EventType.AGENT_STARTED, self._check_transition_after_event
        )
        agent_handler.register_callback(
            EventType.AGENT_STOPPED, self._check_transition_after_event
        )
        agent_handler.register_callback(
            EventType.AGENT_ERROR, self._check_transition_after_event
        )
        agent_handler.register_callback(
            EventType.TOOL_CALLED, self._check_transition_after_event
        )
```

### 4.4 Periodic Transition Checks

In addition to event-triggered checks, the system also performs periodic transition checks in a background thread:

```python
def _transition_check_loop(self) -> None:
    while self.running:
        try:
            # Check for transitions
            self.check_and_execute_transition()
            
            # Sleep for the check interval
            time.sleep(self.transition_check_interval)
        except Exception as e:
            logger.error(f"Error in transition check loop: {e}")
```

## 5. Business Rules Integration

### 5.1 Business Rules Graph Manager

The system supports business rules through an extended graph manager:

```python
class BusinessRulesAgentGraphManager(AgentGraphManager):
    def check_transitions(self, agent_id: int, context: Dict[str, Any]) -> Optional[int]:
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
```

### 5.2 Business Rules Transitions

The system uses the Business Rules library to define and evaluate complex transition conditions:

```python
class ConversationVariables(BaseVariables):
    def __init__(self, context: Dict[str, Any]):
        self.context = context
    
    @string_rule_variable
    def user_input(self) -> str:
        return self.context.get("user_input", "")
    
    @numeric_rule_variable
    def conversation_turn_count(self) -> int:
        return self.context.get("turn_count", 0)
    
    @boolean_rule_variable
    def is_first_turn(self) -> bool:
        return self.context.get("turn_count", 0) <= 1
    
    # ... more variables ...

class TransitionActions(BaseActions):
    def __init__(self, transition_controller):
        self.transition_controller = transition_controller
    
    @rule_action(params={"agent_id": FIELD_NUMERIC})
    def transition_to_agent(self, agent_id: int):
        self.transition_controller.set_next_agent_id(agent_id)
    
    @rule_action(params={"key": FIELD_TEXT, "value": FIELD_TEXT})
    def set_context_value(self, key: str, value: str):
        self.transition_controller.set_context_value(key, value)
    
    # ... more actions ...
```

## 6. Context Management

The system maintains a rich context object that includes:

### 6.1 Session Information
- Session ID and status
- Participant list
- Timestamps

### 6.2 Agent Information
- Current and previous agents
- Agent messages
- Tool usage history

### 6.3 Conversation History
- User and agent messages
- Turn count
- Tool calls and results

### 6.4 Events
- Event history
- Event data
- Event timestamps

## 7. Conclusion

The Rataura2 project implements a sophisticated agent orchestration system that enables dynamic transitions between specialized agents based on various conditions. The key components of the system include:

1. **Database Models**: Define agents, tools, transitions, and meta-agents
2. **Agent Factory**: Creates Livekit agent instances from database models
3. **Event System**: Processes events and updates the context
4. **Agent Graph Manager**: Manages directed graphs of agents and their transitions
5. **Transition Conditions**: Define when transitions should occur
6. **Orchestration**: Coordinates the event system, graph manager, and agent factory
7. **Business Rules Integration**: Enables complex transition conditions

This architecture enables complex agent behaviors and transitions based on various triggers and conditions, with full integration with the Livekit framework and business rules engine.

