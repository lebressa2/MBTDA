"""
Main Agent Class for the Agent Framework.

Supports both Synchronous (Request/Response) and Reactive (Monitoring/Event-Driven) modes.
"""

from typing import Any

from .components import ContextManager
from .interfaces.base import (
    IInboxClient,
    ILifeCycle,
    ILogger,
    IMemoryManager,
    IRunner,
    ITaskManager,
    ITextClient,
    IToolManager,
    IWatchdog,
    IWorkspaceManager,
)


class Agent:
    """
    Main Agent class with Synchronous and Reactive operation modes.

    The Agent is a thin container that orchestrates all components to provide
    intelligent behavior through LLM-powered reasoning and tool execution.

    Responsibilities are delegated to specialized components:
    - ContextManager: System prompt building, context contributions
    - Runner: Execution logic for synchronous and reactive modes
    - Memory/Tools/Workspace: Data management and operations

    Attributes:
        text_provider: LLM client for text generation
        context: ContextManager for system prompt management
        memory: Memory manager for conversation history
        tools: Tool manager for available actions
        runner: Execution strategy (sync/async)
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
        watchdog: IWatchdog | None = None,
        logger: ILogger | None = None,
        life_manager: ILifeCycle | None = None,
        workspace_manager: IWorkspaceManager | None = None,
        runner: IRunner | None = None,
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
        self.watchdog = watchdog
        self.logger = logger
        self.life_manager = life_manager
        self.workspace_manager = workspace_manager
        self.runner = runner

        # Monitoring clients
        self.inbox_client = inbox_client
        self.task_client = task_manager

        # Register components for automatic context contribution
        self.context.discover_components(self)

        # Set agent reference in runner
        if self.runner:
            self.runner.set_agent_reference(self)

    # ==========================================================================
    # MESSAGE HANDLING
    # ==========================================================================



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
        return self.context.build_system_prompt()








    def run_with(self, runner: IRunner) -> None:
        """Execute agent with specified runner strategy.

        Args:
            runner: Execution strategy (SyncRunner or ReactiveRunner)
        """
        self.runner = runner
        runner.set_agent_reference(self)
        runner.start()

    def stop(self) -> None:
        """Stop current runner if running."""
        if self.runner:
            self.runner.stop()

    def chat(self, message: str) -> str:
        """Convenience method for synchronous chat (single message).

        Args:
            message: User message to process

        Returns:
            str: Agent response
        """
        from .runners.sync_runner import SyncRunner
        runner = SyncRunner(message)
        runner.set_agent_reference(self)
        return runner.start()

    def process_event(self, event: Any) -> None:
        """Process an event (for reactive mode).

        Args:
            event: Event to process (AgentEvent or similar)
        """
        # Convert event to message and process
        if hasattr(event, 'data') and isinstance(event.data, dict):
            message = event.data.get('message', str(event))
        else:
            message = str(event)

        if self.logger:
            self.logger.info(f"Processing event: {message[:50]}...")

        # Use sync runner to process the event as a message
        from .runners.sync_runner import SyncRunner
        runner = SyncRunner(message)
        runner.set_agent_reference(self)
        response = runner.start()

        if self.logger:
            self.logger.info(f"Event processed: {response[:50]}...")

    def get_status(self) -> dict[str, Any]:
        """Get a summary of the agent's current status."""
        status = {
            "components": {
                "text_provider": self.text_provider is not None,
                "context": self.context is not None,
                "memory": self.memory is not None,
                "tools": self.tools is not None,
                "runner": self.runner is not None,
                "watchdog": self.watchdog is not None,
                "logger": self.logger is not None,
                "life_manager": self.life_manager is not None,
                "workspace_manager": self.workspace_manager is not None,
                "inbox_client": self.inbox_client is not None,
                "task_client": self.task_client is not None,
            }
        }
        if self.life_manager:
            status["guardrails"] = self.life_manager.check_guardrails()
            status["token_usage"] = self.life_manager.get_token_usage()
        return status
