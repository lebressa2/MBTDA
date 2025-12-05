"""
Example usage and demo of the Agent Framework.
"""

from typing import Any, List
from src.agent import Agent
from src.components import (
    ContextManager, StateMachine, Watchdog,
    ConsoleLogger, LifeCycleManager, WorkspaceManager,
    InMemoryManager, ToolManager
)
from src.models import Protocol, ProtocolStep, Transition
from src.clients import MockInboxClient, MockTaskClient


# ==============================================================================
# MOCK LLM CLIENT (for demonstration without actual API calls)
# ==============================================================================

class MockTextClient:
    """Mock LLM client for testing."""
    
    def __init__(self, model_name: str = "mock-model"):
        self._model_name = model_name
        self._tools = []
    
    def invoke(self, messages: List[Any], **kwargs) -> "MockResponse":
        # Extract the last user message
        user_msg = messages[-1].get("content", "") if messages else ""
        
        # Simple mock response logic
        if "email" in user_msg.lower():
            return MockResponse(f"I'll help you handle this email. Let me check the details.")
        elif "task" in user_msg.lower():
            return MockResponse(f"I see there's a task that needs attention. Let me work on it.")
        else:
            return MockResponse(f"I understand. You said: {user_msg[:50]}... Let me help with that.")
    
    def bind_tools(self, tools: List[Any]) -> "MockTextClient":
        new_client = MockTextClient(self._model_name)
        new_client._tools = tools
        return new_client
    
    def get_model_name(self) -> str:
        return self._model_name


class MockResponse:
    """Mock response object."""
    def __init__(self, content: str):
        self.content = content
        self.tool_calls = None
    
    def __str__(self):
        return self.content


# ==============================================================================
# DEMO FUNCTIONS
# ==============================================================================

def demo_synchronous_mode():
    """Demonstrate synchronous mode (request/response)."""
    print("\n" + "="*60)
    print("DEMO: Synchronous Mode (Request/Response)")
    print("="*60 + "\n")
    
    # Create components
    text_client = MockTextClient("gpt-4")
    logger = ConsoleLogger(name="SyncAgent")
    memory = InMemoryManager()
    
    # Create agent
    agent = Agent(
        text_provider=text_client,
        logger=logger,
        memory=memory
    )
    
    # Add a protocol
    analysis_protocol = Protocol(
        protocol_name="analysis",
        description="Protocol for analyzing user requests",
        steps=[
            ProtocolStep(
                name="understand",
                goal="Understand the user's request",
                instructions=["Read the message carefully", "Identify key points"]
            ),
            ProtocolStep(
                name="plan",
                goal="Create an action plan",
                instructions=["List possible actions", "Choose the best approach"]
            ),
            ProtocolStep(
                name="execute",
                goal="Execute the plan",
                instructions=["Perform the actions", "Verify results"]
            )
        ]
    )
    agent.add_protocol(analysis_protocol)
    
    # Process some messages
    messages = [
        "Hello! Can you help me organize my tasks?",
        "What's the status of my project?",
        "Send a reminder to the team about the meeting."
    ]
    
    for msg in messages:
        print(f"\n[USER]: {msg}")
        response = agent.process_message(msg)
        print(f"[AGENT]: {response}")
    
    # Show status
    print(f"\nAgent Status: {agent.get_status()}")


def demo_reactive_mode():
    """Demonstrate reactive mode (monitoring)."""
    print("\n" + "="*60)
    print("DEMO: Reactive Mode (Monitoring/Event-Driven)")
    print("="*60 + "\n")
    
    # Create components
    text_client = MockTextClient("gpt-4")
    logger = ConsoleLogger(name="ReactiveAgent")
    memory = InMemoryManager()
    watchdog = Watchdog(poll_interval=2.0)  # Fast polling for demo
    
    # Create mock clients with sample data
    inbox_client = MockInboxClient()
    inbox_client.add_mock_email(
        subject="Urgent: Project Deadline",
        sender="manager@company.com",
        body="The deadline for the project has been moved up.",
        is_urgent=True
    )
    
    task_client = MockTaskClient()
    task_client.create_task(
        title="Review code changes",
        due_date="2024-12-01",  # Past date = overdue
        priority=4
    )
    
    # Create agent
    agent = Agent(
        text_provider=text_client,
        logger=logger,
        memory=memory,
        watchdog=watchdog,
        inbox_client=inbox_client,
        task_manager=task_client
    )
    
    print("Starting monitoring mode (will run for 5 seconds)...")
    print("Press Ctrl+C to stop early.\n")
    
    # Run monitoring in a limited way for demo
    import threading
    import time
    
    def stop_after_delay():
        time.sleep(5)
        agent.stop_monitoring()
    
    stop_thread = threading.Thread(target=stop_after_delay)
    stop_thread.start()
    
    try:
        agent.start_monitoring(sources=['inbox', 'tasks'])
    except KeyboardInterrupt:
        pass
    
    stop_thread.join()
    print("\nMonitoring stopped.")


def demo_state_machine():
    """Demonstrate state machine transitions."""
    print("\n" + "="*60)
    print("DEMO: State Machine Transitions")
    print("="*60 + "\n")
    
    # Create state machine
    sm = StateMachine()
    
    # Register custom state
    sm.register_state(
        name="CUSTOM_STATE",
        instruction="This is a custom state for special processing.",
        required_tools=["special_tool"],
        on_enter=lambda ag: print("  -> Entered CUSTOM_STATE"),
        on_exit=lambda ag: print("  <- Exited CUSTOM_STATE")
    )
    
    # Add custom transition
    sm.add_transition(Transition(
        source="IDLE",
        target="CUSTOM_STATE",
        trigger="custom:activate"
    ))
    
    sm.add_transition(Transition(
        source="CUSTOM_STATE",
        target="IDLE",
        trigger="custom:deactivate"
    ))
    
    print(f"Initial State: {sm.current_state}")
    print(f"Available States: {sm.get_all_states()}\n")
    
    # Demonstrate transitions
    print("Triggering 'custom:activate'...")
    sm.trigger("custom:activate")
    print(f"Current State: {sm.current_state}")
    
    print("\nTriggering 'custom:deactivate'...")
    sm.trigger("custom:deactivate")
    print(f"Current State: {sm.current_state}")
    
    print(f"\nState History: {sm.get_history()}")


def demo_context_manager():
    """Demonstrate context manager functionality."""
    print("\n" + "="*60)
    print("DEMO: Context Manager")
    print("="*60 + "\n")
    
    ctx = ContextManager()
    
    # Add context entries
    ctx.add("agent_name", "AssistantBot")
    ctx.add("capabilities", ["text_analysis", "task_management", "email_handling"])
    ctx.add("settings", {"temperature": 0.7, "max_tokens": 1000})
    
    # Add a protocol
    protocol = Protocol(
        protocol_name="greeting",
        description="How to greet users",
        steps=[
            ProtocolStep(name="welcome", goal="Welcome the user", instructions=["Say hello", "Introduce yourself"])
        ]
    )
    ctx.add_protocol(protocol)
    
    # Generate system prompt
    system_prompt = ctx.populate_system_message()
    print("Generated System Prompt:")
    print("-" * 40)
    print(system_prompt)
    print("-" * 40)


if __name__ == "__main__":
    demo_context_manager()
    demo_state_machine()
    demo_synchronous_mode()
    demo_reactive_mode()
    
    print("\n" + "="*60)
    print("All demos completed!")
    print("="*60)
