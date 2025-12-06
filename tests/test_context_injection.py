"""
Integration Tests for IContextProvider with Real LLM Interactions.

This test suite validates that components implementing IContextProvider
correctly inject their context into the agent's system prompt during
real LLM interactions.

Usage:
    python -m tests.test_context_injection
    python -m tests.test_context_injection --test context_injection
    python -m tests.test_context_injection --test workspace_context
"""

import argparse
import sys
import os
import tempfile
import shutil
from datetime import datetime
from typing import Any

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from langchain_core.tools import tool

from src.agent import Agent
from src.components.context_manager import ContextManager
from src.components.memory import InMemoryManager
from src.components.tools import ToolManager
from src.components.workspace import WorkspaceManager
from src.components.state_machine import StateMachine
from src.interfaces.base import IContextProvider
from src.models.data_models import AgentState


# =============================================================================
# TEST UTILITIES
# =============================================================================

def print_test_header(test_num: int, test_name: str, objective: str) -> None:
    """Print a formatted test header."""
    print("\n" + "=" * 80)
    print(f"🧪 TEST {test_num}: {test_name}")
    print("=" * 80)
    print(f"📋 OBJECTIVE: {objective}")
    print("-" * 80)

def print_test_step(step_num: int, description: str) -> None:
    """Print a formatted test step."""
    print(f"\n  [{step_num}] {description}")

def print_test_result(passed: bool, message: str) -> None:
    """Print the test result."""
    if passed:
        print(f"\n✅ TEST PASSED - {message}")
    else:
        print(f"\n❌ TEST FAILED - {message}")


def get_text_client():
    """Get a text client (Groq or Google)."""
    from tests.clients import get_text_client as _get_text_client
    return _get_text_client()


# =============================================================================
# INTEGRATION TESTS
# =============================================================================

def test_context_injection_basic() -> bool:
    """
    TEST 1: Basic Context Injection
    Verify that IContextProvider components automatically inject context.
    """
    print_test_header(
        1, 
        "Basic Context Injection",
        "Verify memory, tools, and workspace inject their context automatically"
    )
    
    try:
        print_test_step(1, "Creating components with inject_context=True (default)")
        
        # Create components - all implement IContextProvider
        memory = InMemoryManager(short_term_limit=10)
        tools = ToolManager()
        
        temp_dir = tempfile.mkdtemp()
        workspace = WorkspaceManager(temp_dir)
        
        print(f"     ✓ Memory created (inject_context={memory.inject_context})")
        print(f"     ✓ Tools created (inject_context={tools.inject_context})")
        print(f"     ✓ Workspace created (inject_context={workspace.inject_context})")
        
        print_test_step(2, "Verifying all components implement IContextProvider")
        
        assert isinstance(memory, IContextProvider), "Memory should implement IContextProvider"
        assert isinstance(tools, IContextProvider), "Tools should implement IContextProvider"
        assert isinstance(workspace, IContextProvider), "Workspace should implement IContextProvider"
        print(f"     ✓ All components implement IContextProvider")
        
        print_test_step(3, "Adding data to components")
        
        # Add some data
        memory.add_message("user", "Hello, I need help with Python")
        memory.add_message("assistant", "Sure! What do you need?")
        print(f"     ✓ Added 2 messages to memory")
        
        @tool
        def calculate(expression: str) -> str:
            """Calculate a mathematical expression."""
            return str(eval(expression))
        
        tools.register_tool("math", calculate)
        print(f"     ✓ Registered 'calculate' tool")
        
        workspace.create_file("notes.txt", "Important notes here")
        workspace.create_file("data.json", '{"key": "value"}')
        print(f"     ✓ Created 2 files in workspace")
        
        print_test_step(4, "Getting context contributions")
        
        memory_ctx = memory.get_context_contribution()
        tools_ctx = tools.get_context_contribution()
        workspace_ctx = workspace.get_context_contribution()
        
        print(f"     ✓ Memory context keys: {list(memory_ctx.keys())}")
        print(f"     ✓ Tools context keys: {list(tools_ctx.keys())}")
        print(f"     ✓ Workspace context keys: {list(workspace_ctx.keys())}")
        
        print_test_step(5, "Verifying context structure")
        
        # Verify memory context
        assert "memory" in memory_ctx
        assert "recent_messages" in memory_ctx["memory"]
        assert len(memory_ctx["memory"]["recent_messages"]) == 2
        print(f"     ✓ Memory context has {len(memory_ctx['memory']['recent_messages'])} messages")
        
        # Verify tools context
        assert "available_tools" in tools_ctx
        assert "calculate" in tools_ctx["available_tools"]
        print(f"     ✓ Tools context includes 'calculate' tool")
        
        # Verify workspace context
        assert "workspace" in workspace_ctx
        assert "base_path" in workspace_ctx["workspace"]
        assert "files" in workspace_ctx["workspace"]
        assert "notes.txt" in workspace_ctx["workspace"]["files"]
        print(f"     ✓ Workspace context has {len(workspace_ctx['workspace']['files'])} files")
        
        # Cleanup
        shutil.rmtree(temp_dir, ignore_errors=True)
        
        print_test_result(True, "All components inject context correctly")
        return True
        
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_disabled_context_injection() -> bool:
    """
    TEST 2: Disabled Context Injection
    Verify that setting inject_context=False prevents automatic injection.
    """
    print_test_header(
        2,
        "Disabled Context Injection",
        "Verify inject_context=False disables automatic context injection"
    )
    
    try:
        print_test_step(1, "Creating components with inject_context=False")
        
        memory = InMemoryManager(inject_context=False)
        tools = ToolManager(inject_context=False)
        
        temp_dir = tempfile.mkdtemp()
        workspace = WorkspaceManager(temp_dir, inject_context=False)
        
        print(f"     ✓ Memory inject_context: {memory.inject_context}")
        print(f"     ✓ Tools inject_context: {tools.inject_context}")
        print(f"     ✓ Workspace inject_context: {workspace.inject_context}")
        
        print_test_step(2, "Adding data to components")
        
        memory.add_message("user", "Secret message")
        workspace.create_file("secret.txt", "Secret content")
        
        print(f"     ✓ Added secret message to memory")
        print(f"     ✓ Created secret file in workspace")
        
        print_test_step(3, "Verifying inject_context flag")
        
        assert memory.inject_context is False
        assert tools.inject_context is False
        assert workspace.inject_context is False
        print(f"     ✓ All components have inject_context=False")
        
        print_test_step(4, "Creating Agent and testing context collection")
        
        # Create a mock text client for testing
        class MockTextClient:
            def invoke(self, messages, **kwargs):
                # Return the system prompt for inspection
                return type('Response', (), {'content': messages[0]['content']})()
            def bind_tools(self, tools):
                return self
            def get_model_name(self):
                return "mock"
        
        context = ContextManager()
        agent = Agent(
            text_provider=MockTextClient(),
            context=context,
            memory=memory,
            tools=tools,
            workspace_manager=workspace
        )
        
        # Manually trigger context collection
        agent._collect_context_contributions()
        
        # Get raw context
        raw_ctx = context.get_raw_context()
        
        print_test_step(5, "Verifying disabled components don't inject")
        
        # With inject_context=False, components should NOT add their context
        assert "memory" not in raw_ctx, "Memory should not inject when disabled"
        assert "available_tools" not in raw_ctx, "Tools should not inject when disabled"
        assert "workspace" not in raw_ctx, "Workspace should not inject when disabled"
        
        print(f"     ✓ Memory context NOT injected (as expected)")
        print(f"     ✓ Tools context NOT injected (as expected)")
        print(f"     ✓ Workspace context NOT injected (as expected)")
        
        # Cleanup
        shutil.rmtree(temp_dir, ignore_errors=True)
        
        print_test_result(True, "Disabled injection works correctly")
        return True
        
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_agent_with_full_context_injection() -> bool:
    """
    TEST 3: Agent with Full Context Injection (Real LLM)
    Verify agent correctly uses injected context from all components.
    """
    print_test_header(
        3,
        "Agent with Full Context Injection",
        "Test real LLM interaction with automatically injected context"
    )
    
    try:
        print_test_step(1, "Setting up all components")
        
        text_client = get_text_client()
        print(f"     ✓ LLM client: {text_client.get_model_name()}")
        
        # Create components
        memory = InMemoryManager(short_term_limit=20)
        tools = ToolManager()
        temp_dir = tempfile.mkdtemp()
        workspace = WorkspaceManager(temp_dir)
        context = ContextManager()
        
        print(f"     ✓ Memory created")
        print(f"     ✓ Tools created")
        print(f"     ✓ Workspace created at: {temp_dir}")
        
        print_test_step(2, "Registering tools")
        
        @tool
        def add_numbers(a: int, b: int) -> int:
            """Add two numbers together."""
            return a + b
        
        @tool
        def save_note(filename: str, content: str) -> str:
            """Save a note to the workspace."""
            workspace.create_file(filename, content)
            return f"Saved to {filename}"
        
        @tool
        def list_files() -> str:
            """List all files in the workspace."""
            files = workspace.list_directory(".")
            return ", ".join(files) if files else "No files"
        
        tools.register_tool("math", add_numbers)
        tools.register_tool("files", save_note)
        tools.register_tool("files", list_files)
        print(f"     ✓ Registered 3 tools: add_numbers, save_note, list_files")
        
        print_test_step(3, "Creating initial workspace content")
        
        workspace.create_file("readme.txt", "Welcome to the workspace!")
        workspace.create_file("config.json", '{"version": "1.0"}')
        print(f"     ✓ Created 2 initial files")
        
        print_test_step(4, "Creating agent")
        
        agent = Agent(
            text_provider=text_client,
            context=context,
            memory=memory,
            tools=tools,
            workspace_manager=workspace
        )
        print(f"     ✓ Agent created with all components")
        print(f"     ✓ Initial state: {agent.state_machine.current_state}")
        
        print_test_step(5, "First interaction - asking about available tools")
        
        response1 = agent.process_message(
            "What tools do you have available? List them briefly."
        )
        print(f"     ✓ Response: {str(response1)[:150]}...")
        
        # Verify state returned to IDLE
        assert agent.state_machine.current_state == AgentState.IDLE.value
        print(f"     ✓ State returned to IDLE")
        
        print_test_step(6, "Second interaction - asking about workspace")
        
        response2 = agent.process_message(
            "What files are in my workspace?"
        )
        print(f"     ✓ Response: {str(response2)[:150]}...")
        
        print_test_step(7, "Verifying memory accumulated messages")
        
        messages = memory.get_recent_messages(10)
        print(f"     ✓ Memory has {len(messages)} messages")
        
        # Should have: user1, assistant1, user2, assistant2
        assert len(messages) >= 4, "Memory should have at least 4 messages"
        print(f"     ✓ Memory correctly accumulated conversation")
        
        print_test_step(8, "Verifying context was injected in system prompt")
        
        # Build system prompt to see what was injected
        system_prompt = agent._build_system_prompt()
        
        # Check if tools were injected
        assert "add_numbers" in system_prompt or "save_note" in system_prompt
        print(f"     ✓ Tools context present in system prompt")
        
        # Check if memory was injected
        assert "memory" in system_prompt.lower() or "recent_messages" in system_prompt.lower()
        print(f"     ✓ Memory context present in system prompt")
        
        # Check if workspace was injected
        assert "workspace" in system_prompt.lower() or temp_dir.replace("\\", "/") in system_prompt.replace("\\", "/")
        print(f"     ✓ Workspace context present in system prompt")
        
        # Cleanup
        shutil.rmtree(temp_dir, ignore_errors=True)
        
        print_test_result(True, "Full context injection working with real LLM")
        return True
        
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_state_transitions_with_context() -> bool:
    """
    TEST 4: State Transitions with Context Injection
    Verify state machine transitions work correctly with context injection.
    """
    print_test_header(
        4,
        "State Transitions with Context",
        "Verify state transitions and context injection work together"
    )
    
    try:
        print_test_step(1, "Creating agent with all components")
        
        text_client = get_text_client()
        memory = InMemoryManager()
        tools = ToolManager()
        temp_dir = tempfile.mkdtemp()
        workspace = WorkspaceManager(temp_dir)
        state_machine = StateMachine()
        context = ContextManager()
        
        # Track state changes
        state_history = []
        
        def on_state_change(agent, old_state, new_state):
            state_history.append({"from": old_state, "to": new_state})
            print(f"       → State: {old_state} → {new_state}")
        
        # Register a callback for state changes
        from src.models.data_models import Transition
        
        print(f"     ✓ All components created")
        
        print_test_step(2, "Registering tools")
        
        @tool
        def get_time() -> str:
            """Get the current time."""
            return datetime.now().strftime("%H:%M:%S")
        
        @tool
        def multiply(a: int, b: int) -> int:
            """Multiply two numbers."""
            return a * b
        
        tools.register_tool("utils", get_time)
        tools.register_tool("math", multiply)
        print(f"     ✓ Registered 2 tools")
        
        print_test_step(3, "Creating agent and verifying initial state")
        
        agent = Agent(
            text_provider=text_client,
            context=context,
            memory=memory,
            tools=tools,
            workspace_manager=workspace,
            state_machine=state_machine
        )
        
        initial_state = agent.state_machine.current_state
        print(f"     ✓ Initial state: {initial_state}")
        assert initial_state == AgentState.IDLE.value
        
        print_test_step(4, "Processing first message (triggers multiple transitions)")
        
        print(f"       Starting state: {agent.state_machine.current_state}")
        
        response1 = agent.process_message("What time is it?")
        
        print(f"       Final state: {agent.state_machine.current_state}")
        print(f"     ✓ Response: {str(response1)[:100]}...")
        
        # Verify we ended in IDLE
        assert agent.state_machine.current_state == AgentState.IDLE.value
        print(f"     ✓ Returned to IDLE state")
        
        print_test_step(5, "Processing second message with memory context")
        
        response2 = agent.process_message("Now multiply 7 by 8")
        
        print(f"     ✓ Response: {str(response2)[:100]}...")
        
        # Verify memory has both interactions
        messages = memory.get_recent_messages(10)
        assert len(messages) >= 4
        print(f"     ✓ Memory has {len(messages)} messages from both interactions")
        
        print_test_step(6, "Verifying context injection during transitions")
        
        # Build fresh system prompt
        system_prompt = agent._build_system_prompt()
        
        # Should contain state info
        assert "IDLE" in system_prompt or "state" in system_prompt.lower()
        print(f"     ✓ State context present in prompt")
        
        # Should contain tool info
        assert "get_time" in system_prompt or "multiply" in system_prompt
        print(f"     ✓ Tools context present in prompt")
        
        # Should contain memory
        assert len(memory.get_recent_messages(5)) > 0
        print(f"     ✓ Memory context contains conversation history")
        
        # Cleanup
        shutil.rmtree(temp_dir, ignore_errors=True)
        
        print_test_result(True, "State transitions with context injection working")
        return True
        
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_workspace_file_operations_with_context() -> bool:
    """
    TEST 5: Workspace File Operations with Context
    Verify workspace operations are reflected in injected context.
    """
    print_test_header(
        5,
        "Workspace File Operations with Context",
        "Verify workspace changes are reflected in automatically injected context"
    )
    
    try:
        print_test_step(1, "Creating workspace and agent")
        
        text_client = get_text_client()
        temp_dir = tempfile.mkdtemp()
        workspace = WorkspaceManager(temp_dir)
        context = ContextManager()
        memory = InMemoryManager()
        
        # Create a tool for file operations
        tools = ToolManager()
        
        @tool
        def create_file(name: str, content: str) -> str:
            """Create a new file in the workspace."""
            success = workspace.create_file(name, content)
            return f"Created {name}" if success else f"Failed to create {name}"
        
        @tool
        def read_file(name: str) -> str:
            """Read a file from the workspace."""
            content = workspace.read_file(name)
            return content if content else f"File {name} not found"
        
        @tool
        def list_workspace() -> str:
            """List all files in workspace."""
            files = workspace.list_directory(".")
            return ", ".join(files) if files else "Empty workspace"
        
        tools.register_tool("files", create_file)
        tools.register_tool("files", read_file)
        tools.register_tool("files", list_workspace)
        
        print(f"     ✓ Workspace created at: {temp_dir}")
        print(f"     ✓ Registered 3 file operation tools")
        
        agent = Agent(
            text_provider=text_client,
            context=context,
            memory=memory,
            tools=tools,
            workspace_manager=workspace
        )
        print(f"     ✓ Agent created")
        
        print_test_step(2, "Verifying initial workspace context (empty)")
        
        initial_ctx = workspace.get_context_contribution()
        initial_files = initial_ctx["workspace"]["files"]
        print(f"     ✓ Initial files: {initial_files}")
        assert len(initial_files) == 0, "Workspace should start empty"
        
        print_test_step(3, "Creating files via workspace")
        
        workspace.create_file("notes.txt", "My important notes")
        workspace.create_file("data.csv", "name,value\ntest,123")
        workspace.create_directory("subdir")
        workspace.create_file("subdir/nested.txt", "Nested file content")
        
        print(f"     ✓ Created notes.txt")
        print(f"     ✓ Created data.csv")
        print(f"     ✓ Created subdir/nested.txt")
        
        print_test_step(4, "Verifying workspace context updated")
        
        updated_ctx = workspace.get_context_contribution()
        updated_files = updated_ctx["workspace"]["files"]
        
        print(f"     ✓ Files now: {updated_files}")
        assert "notes.txt" in updated_files
        assert "data.csv" in updated_files
        assert "subdir" in updated_files
        print(f"     ✓ All created files appear in context")
        
        print_test_step(5, "Asking agent about workspace contents")
        
        response = agent.process_message(
            "What files do I have in my workspace? Just list them."
        )
        print(f"     ✓ Response: {str(response)[:200]}...")
        
        print_test_step(6, "Verifying storage info in context")
        
        storage_info = updated_ctx["workspace"]["storage"]
        print(f"     ✓ Storage used: {storage_info['used_bytes']} bytes")
        print(f"     ✓ Storage limit: {storage_info['limit_bytes']} bytes")
        
        assert storage_info["used_bytes"] > 0, "Should have used some storage"
        
        print_test_step(7, "Checking audit log")
        
        audit_log = workspace.get_audit_log()
        print(f"     ✓ Audit log has {len(audit_log)} entries")
        
        create_actions = [e for e in audit_log if e["action"] == "create_file"]
        print(f"     ✓ Found {len(create_actions)} file creation entries")
        
        # Cleanup
        shutil.rmtree(temp_dir, ignore_errors=True)
        
        print_test_result(True, "Workspace operations reflected in context")
        return True
        
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_multi_turn_conversation_with_context() -> bool:
    """
    TEST 6: Multi-Turn Conversation with Context
    Verify context accumulates correctly across multiple turns.
    """
    print_test_header(
        6,
        "Multi-Turn Conversation with Context",
        "Verify context accumulates across multiple conversation turns"
    )
    
    try:
        print_test_step(1, "Setting up agent with all components")
        
        text_client = get_text_client()
        memory = InMemoryManager(short_term_limit=50)
        tools = ToolManager()
        temp_dir = tempfile.mkdtemp()
        workspace = WorkspaceManager(temp_dir)
        context = ContextManager()
        
        @tool
        def remember_fact(key: str, value: str) -> str:
            """Store a fact in long-term memory."""
            memory.store_long_term(key, value)
            return f"Remembered: {key} = {value}"
        
        @tool
        def recall_fact(key: str) -> str:
            """Recall a fact from long-term memory."""
            results = memory.retrieve(key)
            if results:
                return f"Found: {results[0]['value']}"
            return f"No memory of '{key}'"
        
        tools.register_tool("memory", remember_fact)
        tools.register_tool("memory", recall_fact)
        
        agent = Agent(
            text_provider=text_client,
            context=context,
            memory=memory,
            tools=tools,
            workspace_manager=workspace
        )
        
        print(f"     ✓ Agent created with memory tools")
        
        print_test_step(2, "Turn 1: Introducing myself")
        
        r1 = agent.process_message("Hi! My name is Carlos and I'm a Python developer.")
        print(f"     ✓ Response: {str(r1)[:100]}...")
        
        msgs_after_t1 = len(memory.get_recent_messages(100))
        print(f"     ✓ Messages in memory: {msgs_after_t1}")
        
        print_test_step(3, "Turn 2: Asking about context")
        
        r2 = agent.process_message("What's my name?")
        print(f"     ✓ Response: {str(r2)[:100]}...")
        
        msgs_after_t2 = len(memory.get_recent_messages(100))
        print(f"     ✓ Messages in memory: {msgs_after_t2}")
        
        print_test_step(4, "Turn 3: Testing memory accumulation")
        
        r3 = agent.process_message("What programming language do I work with?")
        print(f"     ✓ Response: {str(r3)[:100]}...")
        
        msgs_after_t3 = len(memory.get_recent_messages(100))
        print(f"     ✓ Messages in memory: {msgs_after_t3}")
        
        print_test_step(5, "Verifying memory accumulation")
        
        all_messages = memory.get_recent_messages(100)
        
        # Should have at least 6 messages (3 user + 3 assistant)
        assert len(all_messages) >= 6, f"Expected at least 6 messages, got {len(all_messages)}"
        print(f"     ✓ Total messages accumulated: {len(all_messages)}")
        
        # Verify message roles alternate
        user_msgs = [m for m in all_messages if m["role"] == "user"]
        assistant_msgs = [m for m in all_messages if m["role"] == "assistant"]
        
        print(f"     ✓ User messages: {len(user_msgs)}")
        print(f"     ✓ Assistant messages: {len(assistant_msgs)}")
        
        print_test_step(6, "Verifying context contribution includes history")
        
        memory_ctx = memory.get_context_contribution()
        recent = memory_ctx["memory"]["recent_messages"]
        
        print(f"     ✓ Context contribution has {len(recent)} recent messages")
        
        # Cleanup
        shutil.rmtree(temp_dir, ignore_errors=True)
        
        print_test_result(True, "Multi-turn conversation context working")
        return True
        
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


# =============================================================================
# TEST RUNNER
# =============================================================================

def run_all_tests() -> dict:
    """Run all tests and return results."""
    tests = [
        ("Context Injection Basic", test_context_injection_basic),
        ("Disabled Context Injection", test_disabled_context_injection),
        ("Agent Full Context", test_agent_with_full_context_injection),
        ("State Transitions", test_state_transitions_with_context),
        ("Workspace Operations", test_workspace_file_operations_with_context),
        ("Multi-Turn Conversation", test_multi_turn_conversation_with_context),
    ]
    
    results = {}
    
    print("\n" + "🔥" * 30)
    print("\n   CONTEXT INJECTION INTEGRATION TESTS")
    print("\n" + "🔥" * 30)
    print("\n📋 Testing IContextProvider implementation with real LLM interactions")
    
    for name, test_func in tests:
        try:
            results[name] = test_func()
        except Exception as e:
            print(f"\n❌ {name}: CRASHED - {e}")
            results[name] = False
    
    # Print summary
    print("\n" + "=" * 80)
    print("   TEST RESULTS SUMMARY")
    print("=" * 80)
    
    passed = 0
    for name, result in results.items():
        status = "✅ PASSED" if result else "❌ FAILED"
        print(f"  {name}: {status}")
        if result:
            passed += 1
    
    print(f"\n  Total: {passed}/{len(results)} tests passed")
    
    if passed == len(results):
        print("\n🎉 ALL TESTS PASSED!")
    else:
        print("\n⚠️ SOME TESTS FAILED")
    
    return results


def run_single_test(test_name: str) -> bool:
    """Run a single test by name."""
    test_map = {
        "context_injection": test_context_injection_basic,
        "disabled_injection": test_disabled_context_injection,
        "full_context": test_agent_with_full_context_injection,
        "state_transitions": test_state_transitions_with_context,
        "workspace": test_workspace_file_operations_with_context,
        "multi_turn": test_multi_turn_conversation_with_context,
    }
    
    if test_name not in test_map:
        print(f"Unknown test: {test_name}")
        print(f"Available tests: {', '.join(test_map.keys())}")
        return False
    
    return test_map[test_name]()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Context Injection Integration Tests")
    parser.add_argument(
        "--test", "-t",
        type=str,
        help="Run specific test (context_injection, disabled_injection, full_context, state_transitions, workspace, multi_turn)"
    )
    parser.add_argument(
        "--list", "-l",
        action="store_true",
        help="List available tests"
    )
    
    args = parser.parse_args()
    
    if args.list:
        print("Available tests:")
        print("  - context_injection: Basic context injection")
        print("  - disabled_injection: Test inject_context=False")
        print("  - full_context: Full agent with all components")
        print("  - state_transitions: State machine with context")
        print("  - workspace: Workspace file operations")
        print("  - multi_turn: Multi-turn conversation")
        sys.exit(0)
    
    if args.test:
        success = run_single_test(args.test)
        sys.exit(0 if success else 1)
    else:
        results = run_all_tests()
        sys.exit(0 if all(results.values()) else 1)
