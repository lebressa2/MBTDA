"""
Main Agent Class for the Agent Framework.

Supports both Synchronous (Request/Response) and Reactive (Monitoring/Event-Driven) modes.
"""

import time
from typing import Any

from .components import ContextManager, StateMachine
from .interfaces.base import (
    IInboxClient,
    ILifeCycle,
    ILogger,
    IMemoryManager,
    ITaskManager,
    ITextClient,
    IToolManager,
    IWatchdog,
    IWorkspaceManager,
)
from .models.data_models import AgentEvent, Protocol


class Agent:
    """
    Main Agent class with Synchronous and Reactive operation modes.

    The Agent is a thin container that orchestrates all components to provide
    intelligent behavior through LLM-powered reasoning and tool execution.
    
    Responsibilities are delegated to specialized components:
    - ContextManager: System prompt building, protocol management, context contributions
    - StateMachine: State transitions, monitoring mode control, status reporting
    - Memory/Tools/Workspace: Data management and operations

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
        context: ContextManager | None = None,
        memory: IMemoryManager | None = None,
        tools: IToolManager | None = None,
        state_machine: StateMachine | None = None,
        watchdog: IWatchdog | None = None,
        logger: ILogger | None = None,
        life_manager: ILifeCycle | None = None,
        workspace_manager: IWorkspaceManager | None = None,
        inbox_client: IInboxClient | None = None,
        task_manager: ITaskManager | None = None
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
        self._event_queue: list[AgentEvent] = []

        # Register components for automatic context contribution
        self.context.discover_components(self)

        # Set agent reference in state machine
        self.state_machine.set_agent_reference(self)

    # ==========================================================================
    # MESSAGE HANDLING (Thin interface - delegates to StateMachine)
    # ==========================================================================

    def process_message(self, input_message: str, **kwargs) -> Any:
        """
        Process an incoming message.
        
        This initiates the agent's processing loop by triggering the 'message' event.
        The StateMachine controls the flow (e.g., THINKING -> WORKING -> THINKING).

        Args:
            input_message: The message to process
            **kwargs: Additional context

        Returns:
            The final response from the agent
        """
        if self.logger:
            self.logger.info(f"Processing message: {input_message[:50]}...")

        # Store message in memory
        if self.memory:
            self.memory.add_message("user", input_message)

        # Trigger the message event
        # This should transition IDLE -> THINKING (if configured)
        self.state_machine.trigger("message", self)
        
        # In a synchronous implementation using callbacks (like ReActAgent),
        # the trigger chain (THINKING -> WORKING -> THINKING...) will run recursively
        # until it hits a state that stops (IDLE).
        # So when trigger returns, the work is done.
        
        # We return the last message from memory as the response
        if self.memory:
            messages = self.memory.get_recent_messages()
            if messages:
                last_msg = messages[-1]
                if isinstance(last_msg, dict):
                    return last_msg.get("content")
                return last_msg.content
        
        return "No response generated."

    def invoke_llm(self, messages: list[dict], **kwargs) -> Any:
        """
        Invoke the LLM directly (utility for state machine callbacks).

        Args:
            messages: Messages to send to LLM
            **kwargs: Additional parameters

        Returns:
            LLM response
        """
        # Bind tools if available
        llm = self.text_provider
        if self.tools:
            tools = self.tools.get_tools()
            if tools:
                llm = llm.bind_tools(tools)

        return llm.invoke(messages, **kwargs)

    def build_system_prompt(self) -> str:
        """
        Build the system prompt.

        Returns:
            str: The formatted system prompt
        """
        return self.context.build_system_prompt(self.state_machine)

    # ==========================================================================
    # REACTIVE MODE - Monitoring/Event-Driven
    # ==========================================================================

    def start_monitoring(self, sources: list[str] | None = None) -> None:
        """
        REACTIVE MODE (Monitoring/Event-Driven).

        Starts a continuous observation loop for inbox and tasks.

        Args:
            sources: List of sources to monitor ('inbox', 'tasks')
        """
        if sources is None:
            sources = ['inbox', 'tasks']
        if self.logger:
            self.logger.info(f"Starting monitoring mode for: {sources}")

        # Transition to MONITORING state (delegated to StateMachine)
        self.state_machine.start_monitoring(self)

        poll_interval = self.watchdog.get_poll_interval() if self.watchdog else 30.0

        try:
            while self.state_machine.is_monitoring():
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
                    self.task_client.get_pending_tasks()  # Check for pending tasks
                    overdue_tasks = self.task_client.get_overdue_tasks()

                    for task in overdue_tasks:
                        events_detected.append(AgentEvent.from_task(task))
                        if self.logger:
                            self.logger.warning(f"Overdue task: {task.title}")

                # Process detected events
                for event in sorted(events_detected, key=lambda e: e.priority, reverse=True):
                    self.process_event(event)

                # Wait for next poll
                if self.state_machine.is_monitoring():
                    time.sleep(poll_interval)

        except KeyboardInterrupt:
            if self.logger:
                self.logger.info("Monitoring stopped by user")
        finally:
            self.state_machine.stop_monitoring(self)

    def stop_monitoring(self) -> None:
        """Stop the monitoring loop (delegated to StateMachine)."""
        self.state_machine.stop_monitoring(self)
        if self.logger:
            self.logger.info("Monitoring stopped")

    def process_event(self, event: AgentEvent) -> Any:
        """
        Process a detected event.
        
        Delegates to the state machine to handle the event.

        Args:
            event: The event to process

        Returns:
            The agent's response/action for the event
        """
        if self.logger:
            self.logger.info(f"Processing event: {event.event_type} from {event.source}")

        # Update context with event data
        self.context.add("current_event", event.model_dump())

        # Trigger event in state machine
        # The StateMachine configuration determines what happens next
        # (e.g., transition to THINKING, or handle immediately)
        trigger_name = f"event:{event.event_type}"
        transitioned = self.state_machine.trigger(trigger_name, self)
        
        if not transitioned:
             # Fallback if no specific transition is defined
             # We treat it as a message to be processed if possible, or just log it
             pass

        # Build event-specific message for the LLM/Processing loop
        if event.event_type == "inbox":
            message = f"New email received. Subject: {event.data.get('subject')}. From: {event.data.get('sender')}. Preview: {event.data.get('body_snippet')}"
        elif event.event_type == "task":
            message = f"Task requires attention. Title: {event.data.get('title')}. Priority: {event.data.get('priority')}. Status: {event.data.get('status')}"
        else:
            message = f"Event received: {event.event_type} - {event.data}"

        # If the state machine transitioned to a state that handles processing (like THINKING),
        # we might want to invoke the processing loop.
        # For a generic Agent, we can just return the message or delegate.
        # Here we assume if we transitioned, we might want to 'handle_message' or similar.
        
        # For now, we'll just return the message as a signal.
        # The ReAct specific logic of "force_transition(THINKING)" is removed.
        
        return message

    # ==========================================================================
    # PROTOCOL MANAGEMENT (delegated to ContextManager)
    # ==========================================================================

    def add_protocol(self, protocol: Protocol) -> None:
        """Add a protocol to the agent (delegated to ContextManager)."""
        self.context.add_protocol(protocol)

    def get_protocol(self, name: str) -> Protocol | None:
        """Get a protocol by name (delegated to ContextManager)."""
        return self.context.get_protocol(name)

    # ==========================================================================
    # UTILITY METHODS (delegated to StateMachine)
    # ==========================================================================

    def get_current_state(self) -> str:
        """Get the current agent state (delegated to StateMachine)."""
        return self.state_machine.current_state

    def is_monitoring(self) -> bool:
        """Check if agent is in monitoring mode (delegated to StateMachine)."""
        return self.state_machine.is_monitoring()

    def get_status(self) -> dict[str, Any]:
        """Get a summary of the agent's current status (delegated to StateMachine)."""
        status = self.state_machine.get_status(self.life_manager)
        # Add protocol info from context
        status["protocols"] = list(self.context.protocols.keys())
        return status
