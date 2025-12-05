"""
Main Agent Class for the Agent Framework.

Supports both Synchronous (Request/Response) and Reactive (Monitoring/Event-Driven) modes.
"""

import time
from typing import Any, List, Optional, Dict
from .interfaces.base import (
    ITextClient, IMemoryManager, IToolManager, IWatchdog,
    ILogger, ILifeCycle, IWorkspaceManager, IInboxClient, ITaskManager
)
from .models.data_models import (
    Protocol, AgentState, AgentEvent, Transition, EmailMessage, TaskItem
)
from .components.context_manager import ContextManager
from .components.state_machine import StateMachine


class Agent:
    """
    Main Agent class with Synchronous and Reactive operation modes.
    
    The Agent orchestrates all components to provide intelligent behavior
    through LLM-powered reasoning and tool execution.
    
    Attributes:
        text_provider: LLM client for text generation
        context: ContextManager for system prompt management
        memory: Memory manager for conversation history
        tools: Tool manager for available actions
        state_machine: State machine for operation flow control
        watchdog: Timer and polling control for reactive mode
        logger: Logging interface
        life_manager: Resource and lifecycle management
        workspace_manager: Isolated workspace for file operations
    """
    
    def __init__(
        self,
        text_provider: ITextClient,
        context: Optional[ContextManager] = None,
        memory: Optional[IMemoryManager] = None,
        tools: Optional[IToolManager] = None,
        state_machine: Optional[StateMachine] = None,
        watchdog: Optional[IWatchdog] = None,
        logger: Optional[ILogger] = None,
        life_manager: Optional[ILifeCycle] = None,
        workspace_manager: Optional[IWorkspaceManager] = None,
        inbox_client: Optional[IInboxClient] = None,
        task_manager: Optional[ITaskManager] = None
    ):
        """
        Initialize the Agent with all components.
        
        Args:
            text_provider: Required LLM client
            context: Optional ContextManager (creates default if None)
            memory: Optional memory manager
            tools: Optional tool manager
            state_machine: Optional state machine (creates default if None)
            watchdog: Optional watchdog for reactive mode
            logger: Optional logger
            life_manager: Optional lifecycle manager
            workspace_manager: Optional workspace manager
            inbox_client: Optional inbox client for email monitoring
            task_manager: Optional task manager for task monitoring
        """
        # Core components
        self.text_provider = text_provider
        self.context = context or ContextManager()
        self.memory = memory
        self.tools = tools
        self.state_machine = state_machine or StateMachine()
        self.watchdog = watchdog
        self.logger = logger
        self.life_manager = life_manager
        self.workspace_manager = workspace_manager
        
        # Monitoring clients
        self.inbox_client = inbox_client
        self.task_client = task_manager
        
        # Internal state
        self._is_monitoring = False
        self._event_queue: List[AgentEvent] = []
        self._protocols: Dict[str, Protocol] = {}
        
        # Set agent reference in state machine
        self.state_machine.set_agent_reference(self)
        
        # Setup default transitions
        self._setup_default_transitions()
    
    def _setup_default_transitions(self) -> None:
        """Configure default state machine transitions."""
        # User input triggers thinking
        self.state_machine.add_transition(Transition(
            source=AgentState.IDLE.value,
            target=AgentState.REQUEST_RECEIVED.value,
            trigger="input:user_message"
        ))
        
        self.state_machine.add_transition(Transition(
            source=AgentState.REQUEST_RECEIVED.value,
            target=AgentState.THINKING.value,
            trigger="process:start"
        ))
        
        # Thinking to working
        self.state_machine.add_transition(Transition(
            source=AgentState.THINKING.value,
            target=AgentState.WORKING.value,
            trigger="action:execute"
        ))
        
        # Working back to thinking
        self.state_machine.add_transition(Transition(
            source=AgentState.WORKING.value,
            target=AgentState.THINKING.value,
            trigger="action:complete"
        ))
        
        # Complete to idle
        self.state_machine.add_transition(Transition(
            source=AgentState.THINKING.value,
            target=AgentState.IDLE.value,
            trigger="process:complete"
        ))
        
        # Monitoring mode
        self.state_machine.add_transition(Transition(
            source=AgentState.IDLE.value,
            target=AgentState.MONITORING.value,
            trigger="mode:monitoring"
        ))
        
        self.state_machine.add_transition(Transition(
            source=AgentState.MONITORING.value,
            target=AgentState.THINKING.value,
            trigger="event:inbox_activity"
        ))
        
        # Timeout handling
        self.state_machine.add_transition(Transition(
            source=AgentState.THINKING.value,
            target=AgentState.INTERRUPTED.value,
            trigger="watchdog:timeout"
        ))
    
    # ==========================================================================
    # SYNCHRONOUS MODE - Request/Response
    # ==========================================================================
    
    def process_message(
        self,
        input_message: str,
        chat_history: Optional[List[Any]] = None
    ) -> Any:
        """
        SYNCHRONOUS MODE (Request/Response).
        
        Executes a single iteration or complete ReAct loop to generate a response.
        
        Args:
            input_message: User's input message
            chat_history: Optional previous conversation history
            
        Returns:
            BaseMessage: The agent's response
        """
        if self.logger:
            self.logger.info(f"Processing message: {input_message[:50]}...")
        
        # 1. Transition to REQUEST_RECEIVED
        self.state_machine.trigger("input:user_message", self)
        
        # 2. Store message in memory
        if self.memory:
            self.memory.add_message("user", input_message)
        
        # 3. Transition to THINKING
        self.state_machine.trigger("process:start", self)
        
        # 4. Build system prompt
        system_prompt = self._build_system_prompt()
        
        # 5. Build messages for LLM
        messages = self._build_messages(system_prompt, input_message, chat_history)
        
        # 6. Execute ReAct loop
        response = self._execute_react_loop(messages)
        
        # 7. Store response in memory
        if self.memory:
            self.memory.add_message("assistant", str(response))
        
        # 8. Complete processing
        self.state_machine.trigger("process:complete", self)
        
        return response
    
    def _build_system_prompt(self) -> str:
        """Build the system prompt from context and current state."""
        # Add state instruction to context
        state_instruction = self.state_machine.get_current_instruction()
        self.context.add("current_state", self.state_machine.current_state)
        self.context.add("state_instruction", state_instruction)
        
        # Add tool descriptions if available
        if self.tools:
            tool_descriptions = self.tools.get_tool_descriptions()
            self.context.add("available_tools", tool_descriptions)
        
        # Add memory context if available
        if self.memory:
            memory_context = self.memory.get_memory_context()
            self.context.add("memory", memory_context)
        
        # Add relevant protocols
        protocol_query = self.state_machine.get_protocol_query()
        if protocol_query:
            protocols = self.context.get_protocols(protocol_query)
            if protocols:
                self.context.add("active_protocols", [p.model_dump() for p in protocols])
        
        return self.context.populate_system_message()
    
    def _build_messages(
        self,
        system_prompt: str,
        user_message: str,
        chat_history: Optional[List[Any]] = None
    ) -> List[Dict[str, str]]:
        """Build message list for LLM invocation."""
        messages = [{"role": "system", "content": system_prompt}]
        
        # Add chat history if provided
        if chat_history:
            for msg in chat_history:
                if hasattr(msg, 'type') and hasattr(msg, 'content'):
                    messages.append({"role": msg.type, "content": msg.content})
                elif isinstance(msg, dict):
                    messages.append(msg)
        
        # Add current user message
        messages.append({"role": "user", "content": user_message})
        
        return messages
    
    def _execute_react_loop(self, messages: List[Dict], max_iterations: int = 10) -> Any:
        """Execute the ReAct reasoning loop."""
        iteration = 0
        
        while iteration < max_iterations:
            iteration += 1
            
            # Check rate limits
            if self.life_manager and not self.life_manager.check_rate_limit():
                if self.logger:
                    self.logger.warning("Rate limit reached, waiting...")
                time.sleep(1)
            
            # Check watchdog timeout
            if self.watchdog and self.watchdog.is_timed_out():
                self.state_machine.trigger("watchdog:timeout", self)
                raise TimeoutError("Agent operation timed out")
            
            # Invoke LLM
            try:
                # Bind tools if available
                llm = self.text_provider
                if self.tools:
                    tools = self.tools.get_tools()
                    if tools:
                        llm = llm.bind_tools(tools)
                
                response = llm.invoke(messages)
                
                # Record token usage
                if self.life_manager:
                    token_estimate = len(str(response)) // 4
                    self.life_manager.record_request(token_estimate)
                
                # Log thinking
                if self.logger and hasattr(response, 'content'):
                    self.logger.log_thinking(str(response.content)[:200])
                
                # Check for tool calls
                if hasattr(response, 'tool_calls') and response.tool_calls:
                    self.state_machine.trigger("action:execute", self)
                    
                    # Append assistant message with tool calls
                    assistant_msg = {
                        "role": "assistant",
                        "content": str(response.content) if response.content else None,
                        "tool_calls": response.tool_calls
                    }
                    messages.append(assistant_msg)
                    
                    for tool_call in response.tool_calls:
                        # Handle object (Pydantic/SDK) or dict
                        if hasattr(tool_call, 'function'):
                            tool_name = tool_call.function.name
                            tool_args = tool_call.function.arguments
                            # Parse JSON arguments if string
                            if isinstance(tool_args, str):
                                import json
                                try:
                                    tool_args = json.loads(tool_args)
                                except Exception:
                                    pass
                        else:
                            # Handle dict
                            tool_name = tool_call.get('name', tool_call.get('function', {}).get('name'))
                            tool_args = tool_call.get('args', tool_call.get('function', {}).get('arguments', {}))
                        
                        try:
                            result = self.tools.execute_tool(tool_name, **tool_args)
                            if self.logger:
                                self.logger.log_tool_call(tool_name, tool_args, result)
                            
                            # Get tool call ID safely
                            if hasattr(tool_call, 'id'):
                                tool_call_id = tool_call.id
                            else:
                                tool_call_id = tool_call.get('id')
                            
                            messages.append({
                                "role": "tool", 
                                "content": str(result), 
                                "name": tool_name,
                                "tool_call_id": tool_call_id
                            })
                        except Exception as e:
                            if self.logger:
                                self.logger.error(f"Tool execution failed: {e}")
                            
                            # Get ID safely for error message too
                            if hasattr(tool_call, 'id'):
                                err_id = tool_call.id
                            else:
                                err_id = tool_call.get('id')
                                
                            messages.append({
                                "role": "tool", 
                                "content": f"Error: {e}", 
                                "name": tool_name,
                                "tool_call_id": err_id
                            })
                    
                    self.state_machine.trigger("action:complete", self)
                    continue  # Continue loop for more reasoning
                
                # No tool calls - return final response
                return response
                
            except Exception as e:
                if self.life_manager and self.life_manager.handle_api_error(e):
                    continue  # Retry
                raise
        
        raise RuntimeError(f"ReAct loop exceeded maximum iterations ({max_iterations})")
    
    # ==========================================================================
    # REACTIVE MODE - Monitoring/Event-Driven
    # ==========================================================================
    
    def start_monitoring(self, sources: List[str] = ['inbox', 'tasks']) -> None:
        """
        REACTIVE MODE (Monitoring/Event-Driven).
        
        Starts a continuous observation loop for inbox and tasks.
        
        Args:
            sources: List of sources to monitor ('inbox', 'tasks')
        """
        if self.logger:
            self.logger.info(f"Starting monitoring mode for: {sources}")
        
        # Transition to MONITORING state
        self.state_machine.trigger("mode:monitoring", self)
        self._is_monitoring = True
        
        poll_interval = self.watchdog.get_poll_interval() if self.watchdog else 30.0
        
        try:
            while self._is_monitoring:
                events_detected = []
                
                # Check inbox
                if 'inbox' in sources and self.inbox_client:
                    new_emails = self.inbox_client.check_new_emails()
                    for email in new_emails:
                        events_detected.append(AgentEvent.from_email(email))
                        if self.logger:
                            self.logger.info(f"New email detected: {email.subject}")
                
                # Check tasks
                if 'tasks' in sources and self.task_client:
                    pending_tasks = self.task_client.get_pending_tasks()
                    overdue_tasks = self.task_client.get_overdue_tasks()
                    
                    for task in overdue_tasks:
                        events_detected.append(AgentEvent.from_task(task))
                        if self.logger:
                            self.logger.warning(f"Overdue task: {task.title}")
                
                # Process detected events
                for event in sorted(events_detected, key=lambda e: e.priority, reverse=True):
                    self.process_event(event)
                
                # Wait for next poll
                if self._is_monitoring:
                    time.sleep(poll_interval)
                    
        except KeyboardInterrupt:
            if self.logger:
                self.logger.info("Monitoring stopped by user")
        finally:
            self._is_monitoring = False
            self.state_machine.force_transition(AgentState.IDLE.value, self)
    
    def stop_monitoring(self) -> None:
        """Stop the monitoring loop."""
        self._is_monitoring = False
        if self.logger:
            self.logger.info("Monitoring stopped")
    
    def process_event(self, event: AgentEvent) -> Any:
        """
        Process a detected event in reactive mode.
        
        Triggers the ReAct reasoning cycle for the received event.
        
        Args:
            event: The event to process
            
        Returns:
            The agent's response/action for the event
        """
        if self.logger:
            self.logger.info(f"Processing event: {event.event_type} from {event.source}")
        
        # Trigger transition based on event type
        if event.event_type == "inbox":
            self.state_machine.trigger("event:inbox_activity", self)
        else:
            self.state_machine.force_transition(AgentState.THINKING.value, self)
        
        # Update context with event data
        self.context.add("current_event", event.model_dump())
        
        # Build event-specific message
        if event.event_type == "inbox":
            message = f"New email received. Subject: {event.data.get('subject')}. From: {event.data.get('sender')}. Preview: {event.data.get('body_snippet')}"
        elif event.event_type == "task":
            message = f"Task requires attention. Title: {event.data.get('title')}. Priority: {event.data.get('priority')}. Status: {event.data.get('status')}"
        else:
            message = f"Event received: {event.event_type} - {event.data}"
        
        # Process through the regular message pipeline
        response = self.process_message(message)
        
        # Return to monitoring if still active
        if self._is_monitoring:
            self.state_machine.force_transition(AgentState.MONITORING.value, self)
        
        return response
    
    # ==========================================================================
    # PROTOCOL MANAGEMENT
    # ==========================================================================
    
    def add_protocol(self, protocol: Protocol) -> None:
        """Add a protocol to the agent."""
        self._protocols[protocol.protocol_name] = protocol
        self.context.add_protocol(protocol)
    
    def get_protocol(self, name: str) -> Optional[Protocol]:
        """Get a protocol by name."""
        return self._protocols.get(name)
    
    # ==========================================================================
    # UTILITY METHODS
    # ==========================================================================
    
    def get_current_state(self) -> str:
        """Get the current agent state."""
        return self.state_machine.current_state
    
    def is_monitoring(self) -> bool:
        """Check if agent is in monitoring mode."""
        return self._is_monitoring
    
    def get_status(self) -> Dict[str, Any]:
        """Get a summary of the agent's current status."""
        status = {
            "state": self.state_machine.current_state,
            "is_monitoring": self._is_monitoring,
            "protocols": list(self._protocols.keys())
        }
        
        if self.life_manager:
            status["guardrails"] = self.life_manager.check_guardrails()
            status["token_usage"] = self.life_manager.get_token_usage()
        
        return status
