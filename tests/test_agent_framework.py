"""
Agent Framework Tests - Real API Integration.

Tests the Agent class with real LLM APIs (Groq/Google) to validate:
- Synchronous mode (process_message)
- State machine transitions
- Context management and dynamic templates
- Memory management
- Tool execution
- Protocols and state transitions with protocols
- Dynamic component configuration
- Template deep merge and override behavior
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from typing import Dict, Any, List, Optional
from dotenv import load_dotenv
load_dotenv()

from src.interfaces.base import ITextClient, LogLevel
from src.agent import Agent
from src.components import (
    ContextManager, StateMachine, ConsoleLogger,
    InMemoryManager, ToolManager, WorkspaceManager, Watchdog
)
from src.models import Protocol, ProtocolStep, AgentState

# Import real clients
from tests.clients import get_text_client, GroqTextClient, GoogleTextClient


class DebugAgent(Agent):
    """Agent subclass that prints the system prompt before LLM calls."""

    def _build_messages(self, system_prompt, user_message, chat_history=None):
        print("\n🔍 SYSTEM PROMPT SENT TO LLM:")
        print("-" * 40)
        print(system_prompt)
        print("-" * 40)
        return super()._build_messages(system_prompt, user_message, chat_history)


# Helper to print raw context (kept for manual inspection if needed)
def print_context(agent, label="Context"):
    """Print the raw context dictionary."""
    import json
    print(f"\n🔍 {label}:")
    try:
        raw = agent.context.get_raw_context()
        print(json.dumps(raw, indent=2, default=str))
    except Exception as e:
        print(f"Error printing context: {e}")


def print_test_header(test_num: int, test_name: str, objective: str):
    """Print a clear test header with objective."""
    print("\n" + "=" * 80)
    print(f"🧪 TEST {test_num}: {test_name}")
    print("=" * 80)
    print(f"📋 OBJECTIVE: {objective}")
    print("-" * 80)


def print_test_step(step_num: int, description: str):
    """Print a test step."""
    print(f"\n  [{step_num}] {description}")


def print_test_result(passed: bool, message: str = ""):
    """Print test result."""
    if passed:
        print(f"\n✅ TEST PASSED {f'- {message}' if message else ''}")
    else:
        print(f"\n❌ TEST FAILED {f'- {message}' if message else ''}")


# ==============================================================================
# TEST 1: Basic Agent with Real LLM
# ==============================================================================

def test_basic_agent():
    """Test basic agent functionality with real LLM."""
    print_test_header(
        1,
        "Basic Agent with Real LLM",
        "Verify agent can process messages and maintain state transitions"
    )

    try:
        print_test_step(1, "Creating agent with minimal components")
        text_client = get_text_client()

        agent = DebugAgent(
            text_provider=text_client,
            logger=ConsoleLogger(min_level=LogLevel.INFO)
        )

        print(f"     ✓ Agent created successfully")
        print(f"     ✓ Initial State: {agent.get_current_state()}")

        print_test_step(2, "Processing simple message")
        response = agent.process_message("What is 2 + 2? Answer briefly.")

        print(f"     ✓ Response received: {str(response)[:100]}...")
        print(f"     ✓ Final State: {agent.get_current_state()}")

        print_test_step(3, "Verifying state transition")
        assert agent.get_current_state() == AgentState.IDLE.value, "Agent should return to IDLE"
        print(f"     ✓ State transition verified: IDLE")

        print_test_result(True, "Basic agent functionality working")
        return True

    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


# ==============================================================================
# TEST 2: Agent with Memory
# ==============================================================================

def test_agent_with_memory():
    """Test agent memory functionality."""
    print_test_header(
        2,
        "Agent with Memory",
        "Verify agent can remember context across multiple messages"
    )

    try:
        print_test_step(1, "Creating agent with memory component")
        text_client = get_text_client()
        memory = InMemoryManager(short_term_limit=10)

        agent = DebugAgent(
            text_provider=text_client,
            memory=memory,
            logger=ConsoleLogger(min_level=LogLevel.INFO)
        )
        print(f"     ✓ Agent created with memory (limit: 10 messages)")

        print_test_step(2, "Sending first message with information to remember")
        response1 = agent.process_message("My name is Carlos. Remember that.")
        print(f"     ✓ Response 1: {str(response1)[:80]}...")

        print_test_step(3, "Sending second message that requires memory")
        response2 = agent.process_message("What is my name?")
        print(f"     ✓ Response 2: {str(response2)[:80]}...")

        print_test_step(4, "Verifying memory storage")
        short_term = memory.get_recent_messages()
        print(f"     ✓ Short-term memory has {len(short_term)} items")

        assert len(short_term) >= 2, "Memory should contain at least 2 messages"
        print(f"     ✓ Memory verification passed")

        print_test_result(True, "Memory functionality working")
        return True

    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


# ==============================================================================
# TEST 3: Agent with Tools
# ==============================================================================

def test_agent_with_tools():
    """Test agent tool execution."""
    print_test_header(
        3,
        "Agent with Tools",
        "Verify agent can register and execute tools"
    )

    try:
        print_test_step(1, "Creating tool manager and registering tools")
        text_client = get_text_client()
        tool_manager = ToolManager()

        from langchain_core.tools import StructuredTool

        # Register simple tools
        def calculator_add(a: int, b: int) -> int:
            """Add two numbers."""
            return a + b

        def calculator_multiply(a: int, b: int) -> int:
            """Multiply two numbers."""
            return a * b

        def get_current_time() -> str:
            """Get the current time."""
            from datetime import datetime
            return datetime.now().strftime("%H:%M:%S")

        tool_manager.register_tool(
            context="math",
            tool=StructuredTool.from_function(
                func=calculator_add,
                name="add",
                description="Add two numbers together"
            )
        )

        tool_manager.register_tool(
            context="math",
            tool=StructuredTool.from_function(
                func=calculator_multiply,
                name="multiply",
                description="Multiply two numbers"
            )
        )

        tool_manager.register_tool(
            context="utility",
            tool=StructuredTool.from_function(
                func=get_current_time,
                name="get_time",
                description="Get the current time"
            )
        )

        print(f"     ✓ Registered 3 tools (add, multiply, get_time)")

        print_test_step(2, "Creating agent with tools")
        agent = DebugAgent(
            text_provider=text_client,
            tools=tool_manager,
            logger=ConsoleLogger(min_level=LogLevel.INFO)
        )
        print(f"     ✓ Agent created with tool manager")

        print_test_step(3, "Testing direct tool execution")
        result = tool_manager.execute_tool("add", a=5, b=3)
        print(f"     ✓ Direct tool execution (5+3): {result}")
        assert result == 8, "Tool execution failed"

        print_test_step(4, "Testing agent tool usage via message")
        response = agent.process_message("What is 15 multiplied by 7? Calculate it.")
        print(f"     ✓ Response: {str(response)[:100]}...")

        print_test_result(True, "Tool functionality working")
        return True

    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


# ==============================================================================
# TEST 4: Agent with Workspace
# ==============================================================================

def test_agent_with_workspace():
    """Test agent workspace functionality."""
    print_test_header(
        4,
        "Agent with Workspace",
        "Verify agent can perform file operations in isolated workspace"
    )

    try:
        import tempfile
        import shutil

        print_test_step(1, "Creating temporary workspace")
        text_client = get_text_client()

        workspace_path = tempfile.mkdtemp(prefix="agent_test_")
        print(f"     ✓ Workspace created: {workspace_path}")

        workspace = WorkspaceManager(base_path=workspace_path)

        agent = DebugAgent(
            text_provider=text_client,
            workspace_manager=workspace,
            logger=ConsoleLogger(min_level=LogLevel.INFO)
        )
        print(f"     ✓ Agent created with workspace manager")

        print_test_step(2, "Testing workspace file operations")
        workspace.create_file("test.txt", "Hello, World!")
        content = workspace.read_file("test.txt")
        print(f"     ✓ Created file with content: {content}")

        workspace.create_directory("subdir")
        workspace.create_file("subdir/nested.txt", "Nested content")
        print(f"     ✓ Created nested directory and file")

        print_test_step(3, "Listing workspace contents")
        files = workspace.list_directory(".")
        print(f"     ✓ Files in workspace: {files}")

        print_test_step(4, "Creating snapshot")
        snapshot_id = workspace.create_snapshot("test_snapshot")
        print(f"     ✓ Snapshot created: {snapshot_id}")

        print_test_step(5, "Checking audit log")
        audit_log = workspace.get_audit_log()
        print(f"     ✓ Audit log has {len(audit_log)} entries")

        print_test_step(6, "Cleaning up workspace")
        shutil.rmtree(workspace_path)
        print(f"     ✓ Workspace cleaned up")

        print_test_result(True, "Workspace functionality working")
        return True

    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


# ==============================================================================
# TEST 5: Agent with Protocol
# ==============================================================================

def test_agent_with_protocol():
    """Test agent protocol functionality."""
    print_test_header(
        5,
        "Agent with Protocol",
        "Verify agent can register and use protocols for structured tasks"
    )

    try:
        print_test_step(1, "Creating agent")
        text_client = get_text_client()

        agent = DebugAgent(
            text_provider=text_client,
            logger=ConsoleLogger(min_level=LogLevel.INFO)
        )
        print(f"     ✓ Agent created")

        print_test_step(2, "Creating code review protocol with 3 steps")
        analysis_protocol = Protocol(
            protocol_name="code_review",
            description="Protocol for reviewing code",
            steps=[
                ProtocolStep(
                    name="understand",
                    goal="Understand the code structure",
                    instructions=["Read the code", "Identify main components"]
                ),
                ProtocolStep(
                    name="analyze",
                    goal="Analyze code quality",
                    instructions=["Check for bugs", "Review best practices"]
                ),
                ProtocolStep(
                    name="report",
                    goal="Generate review report",
                    instructions=["Summarize findings", "Provide recommendations"]
                )
            ]
        )
        print(f"     ✓ Protocol created with {len(analysis_protocol.steps)} steps")

        print_test_step(3, "Adding protocol to agent")
        agent.add_protocol(analysis_protocol)
        print(f"     ✓ Protocol added")

        print_test_step(4, "Verifying protocol retrieval")
        retrieved = agent.get_protocol("code_review")
        assert retrieved is not None, "Protocol should be retrievable"
        assert retrieved.protocol_name == "code_review"
        print(f"     ✓ Protocol '{retrieved.protocol_name}' verified")

        print_test_step(5, "Checking agent status")
        status = agent.get_status()
        print(f"     ✓ Agent status retrieved")
        assert "code_review" in status["protocols"], "Protocol should be in status"
        print(f"     ✓ Protocol appears in agent status")

        print_test_result(True, "Protocol functionality working")
        return True

    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


# ==============================================================================
# TEST 6: State Machine Transitions
# ==============================================================================

def test_state_machine():
    """Test state machine transitions."""
    print_test_header(
        6,
        "State Machine Transitions",
        "Verify agent transitions through states correctly during message processing"
    )

    try:
        print_test_step(1, "Creating agent")
        text_client = get_text_client()

        agent = DebugAgent(
            text_provider=text_client,
            logger=ConsoleLogger(min_level=LogLevel.DEBUG)
        )

        print(f"     ✓ Initial state: {agent.get_current_state()}")
        assert agent.get_current_state() == AgentState.IDLE.value
        print(f"     ✓ Verified initial state is IDLE")

        print_test_step(2, "Processing message (will trigger state transitions)")
        response = agent.process_message("Hello!")
        print(f"     ✓ Message processed")

        print_test_step(3, "Verifying final state")
        final_state = agent.get_current_state()
        print(f"     ✓ Final state: {final_state}")
        assert final_state == AgentState.IDLE.value, f"Expected IDLE, got {final_state}"
        print(f"     ✓ Agent returned to IDLE state")

        print_test_result(True, "State transitions working correctly")
        return True

    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


# ==============================================================================
# TEST 7: Full Agent Integration
# ==============================================================================

def test_full_integration():
    """Test full agent with all components."""
    print_test_header(
        7,
        "Full Agent Integration",
        "Verify all components work together harmoniously"
    )

    try:
        import tempfile
        import shutil

        print_test_step(1, "Setting up all components")
        text_client = get_text_client()
        memory = InMemoryManager()
        tool_manager = ToolManager()
        logger = ConsoleLogger(min_level=LogLevel.INFO)

        workspace_path = tempfile.mkdtemp(prefix="agent_full_test_")
        workspace = WorkspaceManager(base_path=workspace_path)
        print(f"     ✓ All components initialized")

        print_test_step(2, "Registering workspace tool")
        from langchain_core.tools import StructuredTool

        tool_manager.register_tool(
            context="workspace",
            tool=StructuredTool.from_function(
                func=lambda text: workspace.create_file("notes.txt", text) or "Saved",
                name="save_note",
                description="Save a note to file"
            )
        )
        print(f"     ✓ Tool registered")

        print_test_step(3, "Creating fully configured agent")
        agent = DebugAgent(
            text_provider=text_client,
            memory=memory,
            tools=tool_manager,
            workspace_manager=workspace,
            logger=logger
        )
        print(f"     ✓ Agent created with all components")
        print(f"     ✓ Status: {agent.get_status()}")

        print_test_step(4, "Testing conversation")
        response = agent.process_message(
            "I'm testing the agent framework. Tell me something interesting about AI."
        )
        print(f"     ✓ Response received: {str(response)[:100]}...")

        print_test_step(5, "Verifying component integration")
        assert agent.get_current_state() == AgentState.IDLE.value
        assert len(memory.get_recent_messages()) >= 2
        print(f"     ✓ State: {agent.get_current_state()}")
        print(f"     ✓ Memory: {len(memory.get_recent_messages())} messages")

        print_test_step(6, "Cleanup")
        shutil.rmtree(workspace_path)
        print(f"     ✓ Workspace cleaned up")

        print_test_result(True, "Full integration working")
        return True

    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


# ==============================================================================
# TEST 8: Advanced State Machine
# ==============================================================================

def test_advanced_state_machine():
    """Test advanced state machine features (callbacks, conditions, dynamic states)."""
    print_test_header(
        8,
        "Advanced State Machine",
        "Verify custom states, callbacks, and conditional transitions"
    )

    try:
        print_test_step(1, "Creating agent")
        text_client = get_text_client()
        agent = DebugAgent(
            text_provider=text_client,
            logger=ConsoleLogger(min_level=LogLevel.DEBUG)
        )
        print(f"     ✓ Agent created")

        print_test_step(2, "Setting up callback tracking")
        callbacks = {"on_enter": False, "on_exit": False, "condition_checked": False}

        agent.state_machine.register_state(
            name="CUSTOM_STATE",
            instruction="Custom state instruction",
            on_enter=lambda ag: callbacks.update({"on_enter": True}),
            on_exit=lambda ag: callbacks.update({"on_exit": True})
        )
        print(f"     ✓ Custom state registered with callbacks")

        print_test_step(3, "Adding conditional transition")
        from src.models.data_models import Transition

        def check_condition(ag):
            callbacks["condition_checked"] = True
            return True

        agent.state_machine.add_transition(Transition(
            source=AgentState.IDLE.value,
            target="CUSTOM_STATE",
            trigger="custom_trigger",
            condition=check_condition
        ))
        print(f"     ✓ Transition with condition added")

        print_test_step(4, "Triggering custom transition")
        success = agent.state_machine.trigger("custom_trigger", agent)
        print(f"     ✓ Transition triggered: {success}")
        print(f"     ✓ Current State: {agent.get_current_state()}")
        print(f"     ✓ Callbacks: {callbacks}")

        print_test_step(5, "Verifying callbacks and state")
        assert success, "Transition should succeed"
        assert agent.get_current_state() == "CUSTOM_STATE", "Should be in CUSTOM_STATE"
        assert callbacks["condition_checked"], "Condition should be checked"
        assert callbacks["on_enter"], "on_enter should be called"
        print(f"     ✓ All verifications passed")

        print_test_step(6, "Transitioning back to trigger exit callback")
        agent.state_machine.force_transition(AgentState.IDLE.value, agent)
        print(f"     ✓ Forced transition to IDLE")
        print(f"     ✓ Callbacks after exit: {callbacks}")
        assert callbacks["on_exit"], "on_exit should be called"
        print(f"     ✓ Exit callback verified")

        print_test_result(True, "Advanced state machine features working")
        return True

    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


# ==============================================================================
# TEST 9: Agent with Dynamic Templates
# ==============================================================================

def test_agent_with_dynamic_templates():
    """Test agent with dynamic template system (context.add() + templates)."""
    print_test_header(
        9,
        "Agent with Dynamic Templates",
        "Verify template + context.add() work in harmony (deep merge)"
    )

    try:
        print_test_step(1, "Creating context with general_assistant template")
        text_client = get_text_client()

        from src.components import TemplateRegistry

        context = ContextManager.create_general_assistant(
            agent_name="TemplateBot",
            user_name="Alice"
        )
        print(f"     ✓ Context created with template")

        print_test_step(2, "Adding dynamic content using context.add()")
        context.add("current_task", "Task: Analyze data trends")
        context.add("data_context", {
            "dataset_size": "10GB",
            "time_range": "Q1 2025",
            "metrics": ["accuracy", "precision", "recall"]
        })
        print(f"     ✓ Dynamic content added")

        print_test_step(3, "Verifying template + dynamic content merge")
        raw_context = context.get_raw_context()

        # Verify template structure
        assert "identity" in raw_context, "Template identity section should exist"
        assert "session" in raw_context, "Template session section should exist"
        assert "states_explanation" in raw_context, "Template states section should exist"
        print(f"     ✓ Template structure verified")

        # Verify dynamic content
        assert raw_context["current_task"] == "Task: Analyze data trends", "Dynamic task should be added"
        assert "data_context" in raw_context, "Dynamic data context should be added"
        assert raw_context["data_context"]["dataset_size"] == "10GB", "Nested dynamic content should work"
        print(f"     ✓ Dynamic content verified")

        print_test_step(4, "Verifying meta variable interpolation")
        assert "TemplateBot" in raw_context["identity"]["name"], "Meta agent_name should be interpolated"
        assert "Alice" in raw_context["session"]["user"], "Meta user_name should be interpolated"
        print(f"     ✓ Meta variables interpolated correctly")
        print(f"     ✓ Raw context has {len(raw_context)} top-level sections")

        print_test_step(5, "Creating agent with custom context")
        agent = DebugAgent(
            text_provider=text_client,
            context=context,
            logger=ConsoleLogger(min_level=LogLevel.INFO)
        )
        print(f"     ✓ Agent created")

        print_test_step(6, "Processing message to verify template is used")
        response = agent.process_message("What should I do with this data? Keep it brief.")
        print(f"     ✓ Response: {str(response)[:100]}...")

        print_test_step(7, "Verifying context persistence")
        final_context = agent.context.get_raw_context()
        assert "current_task" in final_context, "Context should persist across message processing"
        print(f"     ✓ Context persisted correctly")

        print_test_result(True, "Dynamic templates working")
        return True

    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


# ==============================================================================
# TEST 10: Agent with Custom Templates
# ==============================================================================

def test_agent_with_custom_templates():
    """Test agent using custom templates from TemplateRegistry."""
    print_test_header(
        10,
        "Agent with Custom Templates",
        "Verify TemplateRegistry allows custom template registration and usage"
    )

    try:
        from src.components import TemplateRegistry

        print_test_step(1, "Registering custom template")
        custom_template = {
            "agent_personality": {
                "role": "Data Analyst Expert",
                "style": "analytical and precise"
            },
            "task_context": {
                "current_focus": "{meta.agent_role}",
                "capabilities": ["SQL", "Python", "Statistics"],
                "tools_available": ["database_query", "chart_generation"]
            },
            "response_format": {
                "structure": "Use structured analysis",
                "format": "markdown with sections"
            }
        }

        TemplateRegistry.register("data_analyst", custom_template)
        print(f"     ✓ Custom template registered")

        print_test_step(2, "Verifying template registration")
        available = TemplateRegistry.list_templates()
        assert "data_analyst" in available, "Custom template should be available"
        print(f"     ✓ Available templates: {available}")

        print_test_step(3, "Creating context with custom template")
        context = ContextManager.create_from_template(
            template="data_analyst",
            agent_name="AnalystBot",
            agent_role="Data Analysis Specialist",
            custom_analysis_mode="detailed"
        )
        print(f"     ✓ Context created from custom template")

        print_test_step(4, "Adding dynamic content")
        context.add("current_query", "Analyze customer churn patterns")
        context.add("data_summary", {
            "total_customers": 10000,
            "churn_rate": "15%",
            "key_insights": ["seasonal patterns", "age groups"]
        })
        print(f"     ✓ Dynamic content added")

        print_test_step(5, "Verifying merge works")
        raw_context = context.get_raw_context()
        assert "agent_personality" in raw_context, "Custom template section should exist"
        assert "current_query" in raw_context, "Dynamic content should be merged"
        assert isinstance(raw_context["data_summary"], dict), "Complex dynamic objects should work"
        print(f"     ✓ Template + dynamic content merged successfully")

        print_test_step(6, "Verifying meta interpolation")
        assert "Data Analysis Specialist" in str(raw_context), "Meta role should be interpolated"
        print(f"     ✓ Meta interpolation working")
        print(f"     ✓ Context sections merged: {len(raw_context)}")

        print_test_step(7, "Creating agent with custom template")
        text_client = get_text_client()
        agent = DebugAgent(
            text_provider=text_client,
            context=context,
            logger=ConsoleLogger(min_level=LogLevel.INFO)
        )
        print(f"     ✓ Agent created")

        print_test_step(8, "Testing with real LLM")
        response = agent.process_message("Describe this customer data briefly.")
        print(f"     ✓ Response: {str(response)[:100]}...")

        print_test_step(9, "Cleanup")
        TemplateRegistry.unregister("data_analyst")
        print(f"     ✓ Custom template unregistered")

        print_test_result(True, "Custom templates working")
        return True

    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


# ==============================================================================
# TEST 11: Agent State Transitions with Protocol
# ==============================================================================

def test_agent_state_transitions_with_protocol():
    """Test state transitions when agent has active protocol."""
    print_test_header(
        11,
        "Agent State Transitions with Protocol",
        "Verify protocols integrate correctly with state machine"
    )

    try:
        from src.models import ProtocolStep

        print_test_step(1, "Creating task execution protocol")
        task_protocol = Protocol(
            protocol_name="task_execution",
            description="Execute complex tasks methodically",
            steps=[
                ProtocolStep(
                    name="analyze",
                    goal="Understand the task requirements",
                    instructions=[
                        "Read task description carefully",
                        "Identify required skills and resources",
                        "Break down into subtasks"
                    ]
                ),
                ProtocolStep(
                    name="execute",
                    goal="Execute the main work",
                    instructions=[
                        "Follow step-by-step instructions",
                        "Use available tools when needed",
                        "Document progress"
                    ]
                ),
                ProtocolStep(
                    name="verify",
                    goal="Verify completion and quality",
                    instructions=[
                        "Check if all requirements are met",
                        "Test the solution if applicable",
                        "Prepare summary"
                    ]
                )
            ]
        )
        print(f"     ✓ Protocol created with {len(task_protocol.steps)} steps")

        print_test_step(2, "Creating agent and adding protocol")
        text_client = get_text_client()
        agent = DebugAgent(
            text_provider=text_client,
            logger=ConsoleLogger(min_level=LogLevel.DEBUG)
        )

        agent.add_protocol(task_protocol)
        initial_state = agent.get_current_state()
        print(f"     ✓ Protocol added")
        print(f"     ✓ Initial agent state: {initial_state}")
        assert initial_state == AgentState.IDLE.value
        print(f"     ✓ Verified initial state is IDLE")

        print_test_step(3, "Starting protocol execution (step 1: analyze)")
        response1 = agent.process_message(
            "I need to create a Python function to calculate Fibonacci numbers. Help me with this task."
        )
        print(f"     ✓ Response 1: {str(response1)[:100]}...")
        print(f"     ✓ State after step 1: {agent.get_current_state()}")

        print_test_step(4, "Verifying protocol is active in context")
        context = agent.context.get_raw_context()
        assert "active_protocols" in context, "Active protocols should be in context"
        assert "task_execution" in context["active_protocols"], "Our protocol should be active"
        print(f"     ✓ Protocol active in context")

        protocol_data = context["active_protocols"]["task_execution"]
        print(f"     ✓ Protocol progress: {protocol_data['progress']}")
        print(f"     ✓ Current step: {protocol_data['current_step']}")

        print_test_step(5, "Continuing protocol (step 2: execute)")
        response2 = agent.process_message("Now write the Fibonacci function implementation.")
        print(f"     ✓ Response 2: {str(response2)[:100]}...")
        print(f"     ✓ State after step 2: {agent.get_current_state()}")

        print_test_step(6, "Verifying protocol persistence")
        updated_context = agent.context.get_raw_context()
        updated_protocol_data = updated_context["active_protocols"]["task_execution"]
        print(f"     ✓ Updated progress: {updated_protocol_data['progress']}")

        print_test_result(True, "Protocol + state transitions working")
        return True

    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


# ==============================================================================
# TEST 12: Template Deep Merge (GAP - HIGH PRIORITY)
# ==============================================================================

def test_template_deep_merge():
    """Test that context.add() deep merges with template dictionaries."""
    print_test_header(
        12,
        "Template Deep Merge",
        "🔴 HIGH PRIORITY GAP - Verify deep merge preserves nested template values"
    )

    try:
        print_test_step(1, "Creating context with nested template structure")
        template = {
            "config": {
                "level1": {
                    "a": 1,
                    "b": 2,
                    "nested": {
                        "x": 10,
                        "y": 20
                    }
                },
                "level2": {
                    "setting": "original"
                }
            },
            "identity": {
                "name": "Original"
            }
        }

        context = ContextManager(template=template)
        print(f"     ✓ Context created with nested template")
        print(f"     ✓ Template structure: config.level1 has keys: a, b, nested")

        print_test_step(2, "Adding new nested values (should merge, not replace)")
        context.add("config", {
            "level1": {
                "c": 3,  # New key
                "nested": {
                    "z": 30  # New nested key
                }
            }
        })
        print(f"     ✓ Added config.level1.c = 3")
        print(f"     ✓ Added config.level1.nested.z = 30")

        print_test_step(3, "Verifying deep merge preserved original values")
        raw = context.get_raw_context()

        # Original values should still exist
        assert raw["config"]["level1"]["a"] == 1, "Original 'a' should be preserved"
        assert raw["config"]["level1"]["b"] == 2, "Original 'b' should be preserved"
        print(f"     ✓ Original values preserved: a=1, b=2")

        # New values should be added
        assert raw["config"]["level1"]["c"] == 3, "New 'c' should be added"
        print(f"     ✓ New value added: c=3")

        # Nested original values should be preserved
        assert raw["config"]["level1"]["nested"]["x"] == 10, "Nested 'x' should be preserved"
        assert raw["config"]["level1"]["nested"]["y"] == 20, "Nested 'y' should be preserved"
        print(f"     ✓ Nested original values preserved: x=10, y=20")

        # New nested value should be added
        assert raw["config"]["level1"]["nested"]["z"] == 30, "New nested 'z' should be added"
        print(f"     ✓ New nested value added: z=30")

        # Untouched sections should remain
        assert raw["config"]["level2"]["setting"] == "original", "Untouched section should remain"
        assert raw["identity"]["name"] == "Original", "Untouched identity should remain"
        print(f"     ✓ Untouched sections preserved")

        print_test_result(True, "Deep merge working correctly")
        return True

    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


# ==============================================================================
# TEST 13: Meta Custom Fields Interpolation (GAP - MEDIUM PRIORITY)
# ==============================================================================

def test_meta_custom_fields_interpolation():
    """Test {meta.custom.field} interpolation."""
    print_test_header(
        13,
        "Meta Custom Fields Interpolation",
        "🟡 MEDIUM PRIORITY GAP - Verify custom meta fields are interpolated"
    )

    try:
        print_test_step(1, "Creating context and setting custom meta fields")
        context = ContextManager()
        context.meta.custom["project"] = "MBTDA"
        context.meta.custom["environment"] = "production"
        context.meta.custom["version"] = "2.0.1"
        print(f"     ✓ Set custom fields: project, environment, version")

        print_test_step(2, "Adding content with custom field interpolation")
        context.add("project_info", "Project: {meta.custom.project}")
        context.add("deployment", "Env: {meta.custom.environment}, Version: {meta.custom.version}")
        context.add("full_context", {
            "details": "Running {meta.custom.project} on {meta.custom.environment}",
            "metadata": {
                "version": "{meta.custom.version}",
                "project": "{meta.custom.project}"
            }
        })
        print(f"     ✓ Added content with {meta.custom.field} placeholders")

        print_test_step(3, "Verifying interpolation in simple strings")
        raw = context.get_raw_context()

        assert raw["project_info"] == "Project: MBTDA", "Simple custom field should interpolate"
        print(f"     ✓ Simple interpolation: {raw['project_info']}")

        assert raw["deployment"] == "Env: production, Version: 2.0.1", "Multiple custom fields should interpolate"
        print(f"     ✓ Multiple interpolation: {raw['deployment']}")

        print_test_step(4, "Verifying interpolation in nested structures")
        assert raw["full_context"]["details"] == "Running MBTDA on production", "Nested string should interpolate"
        print(f"     ✓ Nested string: {raw['full_context']['details']}")

        assert raw["full_context"]["metadata"]["version"] == "2.0.1", "Deeply nested should interpolate"
        assert raw["full_context"]["metadata"]["project"] == "MBTDA", "Deeply nested should interpolate"
        print(f"     ✓ Deeply nested interpolation working")

        print_test_step(5, "Verifying non-existent custom fields are kept as-is")
        context.add("unknown", "Field: {meta.custom.nonexistent}")
        raw = context.get_raw_context()
        assert raw["unknown"] == "Field: {meta.custom.nonexistent}", "Unknown fields should remain unchanged"
        print(f"     ✓ Unknown fields preserved: {raw['unknown']}")

        print_test_result(True, "Custom field interpolation working")
        return True

    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


# ==============================================================================
# TEST 14: Template Override (GAP - MEDIUM PRIORITY)
# ==============================================================================

def test_template_override():
    """Test that context.add() can completely override template sections."""
    print_test_header(
        14,
        "Template Override",
        "🟡 MEDIUM PRIORITY GAP - Verify context.add() can override entire template sections"
    )

    try:
        print_test_step(1, "Creating context with template")
        template = {
            "identity": {
                "name": "OriginalBot",
                "role": "Original Role",
                "description": "Original description"
            },
            "config": {
                "mode": "standard",
                "level": 1
            }
        }

        context = ContextManager(template=template)
        print(f"     ✓ Template created with identity and config sections")
        print(f"     ✓ Original identity: name=OriginalBot, role=Original Role")

        print_test_step(2, "Overriding identity section completely")
        context.add("identity", {
            "name": "OverrideBot",
            "custom_field": "This is new"
        })
        print(f"     ✓ Added new identity (should replace, not merge)")

        print_test_step(3, "Verifying complete override")
        raw = context.get_raw_context()

        # New values should exist
        assert raw["identity"]["name"] == "OverrideBot", "Name should be overridden"
        assert raw["identity"]["custom_field"] == "This is new", "New field should exist"
        print(f"     ✓ New values present: name=OverrideBot, custom_field exists")

        # Old values should NOT exist (complete replacement)
        assert "role" not in raw["identity"], "Old 'role' should not exist (was replaced)"
        assert "description" not in raw["identity"], "Old 'description' should not exist (was replaced)"
        print(f"     ✓ Old values removed: role and description gone")

        print_test_step(4, "Verifying other sections untouched")
        assert raw["config"]["mode"] == "standard", "Untouched config should remain"
        assert raw["config"]["level"] == 1, "Untouched config should remain"
        print(f"     ✓ Other sections preserved: config intact")

        print_test_step(5, "Testing partial override (merge behavior)")
        # When we want to merge, we need to get current value first
        current_config = raw["config"].copy()
        current_config["new_setting"] = "added"
        context.add("config", current_config)

        raw = context.get_raw_context()
        assert raw["config"]["mode"] == "standard", "Original mode preserved"
        assert raw["config"]["new_setting"] == "added", "New setting added"
        print(f"     ✓ Partial override (manual merge) working")

        print_test_result(True, "Template override working correctly")
        return True

    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


# ==============================================================================
# TEST 15: Agent Dynamic Components Integration
# ==============================================================================

def test_agent_dynamic_components():
    """Test agent with components passed dynamically (custom memory, context, tools)."""
    print_test_header(
        15,
        "Agent Dynamic Components",
        "Verify agent works with dynamically configured components"
    )

    try:
        from langchain_core.tools import StructuredTool

        print_test_step(1, "Creating custom context manager")
        context = ContextManager.create_task_agent(
            agent_name="DynamicBot",
            session_id="session-123"
        )

        context.add("workspace_config", {
            "project_name": "Dynamic Test",
            "access_level": "admin",
            "enabled_features": ["memory", "tools", "protocol"]
        })
        print(f"     ✓ Custom context created with dynamic config")

        print_test_step(2, "Creating custom memory with limited capacity")
        from src.components import InMemoryManager
        custom_memory = InMemoryManager(short_term_limit=5)
        print(f"     ✓ Memory created (limit: 5 messages)")

        print_test_step(3, "Creating custom tool manager")
        tool_manager = ToolManager()

        def test_calculator(a: int, b: int, operation: str) -> str:
            """Simple calculator for testing."""
            if operation == "add":
                return str(a + b)
            elif operation == "multiply":
                return str(a * b)
            return "Unknown operation"

        def get_current_timestamp() -> str:
            """Get current timestamp for testing."""
            import datetime
            return datetime.datetime.now().isoformat()

        tool_manager.register_tool(
            context="math",
            tool=StructuredTool.from_function(
                func=test_calculator,
                name="calculator",
                description="Basic calculator operations"
            )
        )

        tool_manager.register_tool(
            context="utility",
            tool=StructuredTool.from_function(
                func=get_current_timestamp,
                name="timestamp",
                description="Get current timestamp"
            )
        )
        print(f"     ✓ Tools registered: calculator, timestamp")

        print_test_step(4, "Creating custom state machine")
        state_machine = StateMachine()
        state_callbacks = []

        def log_state_change(agent_ref):
            current_state = "unknown"
            try:
                current_state = agent_ref.get_current_state()
            except:
                pass
            state_callbacks.append(current_state)

        state_machine.register_state(
            name="TEST_MODE",
            instruction="Bot is in test mode - respond with analysis",
            on_enter=log_state_change
        )
        print(f"     ✓ Custom state registered: TEST_MODE")

        print_test_step(5, "Creating agent with all dynamic components")
        text_client = get_text_client()

        agent = DebugAgent(
            text_provider=text_client,
            context=context,
            memory=custom_memory,
            tools=tool_manager,
            state_machine=state_machine,
            logger=ConsoleLogger(min_level=LogLevel.INFO)
        )
        print(f"     ✓ Agent created with {len(tool_manager.list_tools())} tools")
        print(f"     ✓ Context has {len(context.get_raw_context())} sections")

        print_test_step(6, "Testing component integration")
        response = agent.process_message(
            "Hello, I'm testing the dynamic components. What's the current time and 15+27?"
        )
        print(f"     ✓ Response: {str(response)[:100]}...")
        print(f"     ✓ Memory has {len(custom_memory.get_recent_messages())} messages")

        print_test_step(7, "Verifying components worked together")
        context_data = agent.context.get_raw_context()
        assert "workspace_config" in context_data, "Dynamic context should be present"
        assert context_data["workspace_config"]["project_name"] == "Dynamic Test", "Context config should be preserved"
        print(f"     ✓ Context preserved")

        assert len(custom_memory.get_recent_messages()) <= 5, "Memory limit should be respected"
        print(f"     ✓ Memory limit respected")

        print_test_result(True, "Dynamic components working")
        return True

    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


# ==============================================================================
# MAIN
# ==============================================================================

def run_all_tests():
    """Run all framework tests."""
    print("\n" + "🔥" * 30)
    print("\n   AGENT FRAMEWORK - REAL API TESTS")
    print("\n" + "🔥" * 30)

    print("\n📋 Testing Agent Framework with real LLM APIs")
    print("   - Groq (qwen/qwen3-32b) - Primary")
    print("   - Google Gemini (gemini-2.5-flash) - Fallback\n")

    results = {}

    tests = [
        ("Basic Agent", test_basic_agent),
        ("Agent with Memory", test_agent_with_memory),
        ("Agent with Tools", test_agent_with_tools),
        ("Agent with Workspace", test_agent_with_workspace),
        ("Agent with Protocol", test_agent_with_protocol),
        ("State Machine", test_state_machine),
        ("Full Integration", test_full_integration),
        ("Advanced State Machine", test_advanced_state_machine),
        ("Dynamic Templates", test_agent_with_dynamic_templates),
        ("Custom Templates", test_agent_with_custom_templates),
        ("State Transitions with Protocol", test_agent_state_transitions_with_protocol),
        ("🔴 Template Deep Merge (GAP)", test_template_deep_merge),
        ("🟡 Meta Custom Fields (GAP)", test_meta_custom_fields_interpolation),
        ("🟡 Template Override (GAP)", test_template_override),
        ("Dynamic Components", test_agent_dynamic_components),
    ]

    for test_name, test_func in tests:
        try:
            results[test_name] = test_func()
        except Exception as e:
            print(f"\n❌ {test_name} crashed: {e}")
            results[test_name] = False

    # Summary
    print("\n" + "=" * 80)
    print("   TEST RESULTS SUMMARY")
    print("=" * 80)

    for test_name, passed in results.items():
        status = "✅ PASSED" if passed else "❌ FAILED"
        print(f"  {test_name}: {status}")

    total_passed = sum(1 for v in results.values() if v)
    total_tests = len(results)
    print(f"\n  Total: {total_passed}/{total_tests} tests passed")

    if total_passed == total_tests:
        print("\n🎉 ALL TESTS PASSED!")
        return True
    else:
        print("\n⚠️ SOME TESTS FAILED")
        return False


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Run Agent Framework tests")
    parser.add_argument("--basic", action="store_true", help="Run only basic test")
    parser.add_argument("--memory", action="store_true", help="Run only memory test")
    parser.add_argument("--tools", action="store_true", help="Run only tools test")
    parser.add_argument("--workspace", action="store_true", help="Run only workspace test")
    parser.add_argument("--protocol", action="store_true", help="Run only protocol test")
    parser.add_argument("--state", action="store_true", help="Run only state machine test")
    parser.add_argument("--full", action="store_true", help="Run only full integration test")
    parser.add_argument("--advanced-state", action="store_true", help="Run only advanced state machine test")
    parser.add_argument("--dynamic-templates", action="store_true", help="Run only dynamic templates test")
    parser.add_argument("--custom-templates", action="store_true", help="Run only custom templates test")
    parser.add_argument("--protocol-state", action="store_true", help="Run only state transitions with protocol test")
    parser.add_argument("--deep-merge", action="store_true", help="Run only template deep merge test (GAP)")
    parser.add_argument("--meta-custom", action="store_true", help="Run only meta custom fields test (GAP)")
    parser.add_argument("--template-override", action="store_true", help="Run only template override test (GAP)")
    parser.add_argument("--dynamic-components", action="store_true", help="Run only dynamic components test")

    args = parser.parse_args()

    if args.basic:
        test_basic_agent()
    elif args.memory:
        test_agent_with_memory()
    elif args.tools:
        test_agent_with_tools()
    elif args.workspace:
        test_agent_with_workspace()
    elif args.protocol:
        test_agent_with_protocol()
    elif args.state:
        test_state_machine()
    elif args.full:
        test_full_integration()
    elif args.advanced_state:
        test_advanced_state_machine()
    elif args.dynamic_templates:
        test_agent_with_dynamic_templates()
    elif args.custom_templates:
        test_agent_with_custom_templates()
    elif args.protocol_state:
        test_agent_state_transitions_with_protocol()
    elif args.deep_merge:
        test_template_deep_merge()
    elif args.meta_custom:
        test_meta_custom_fields_interpolation()
    elif args.template_override:
        test_template_override()
    elif args.dynamic_components:
        test_agent_dynamic_components()
    else:
        success = run_all_tests()
        sys.exit(0 if success else 1)
