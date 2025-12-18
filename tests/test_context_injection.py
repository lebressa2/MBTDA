"""
Integration Tests for Context Injection with Real LLM Interactions.

This test suite validates that components correctly provide their context
via get_snapshot() and that it can be explicitly added to the agent's
system prompt.
"""

import argparse
import sys
import os
import tempfile
import shutil
from datetime import datetime
from typing import Any, List, Dict

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from langchain_core.tools import tool

from src.agent import Agent
from src.components import ContextManager
from src.components import InMemoryManager
from src.components import ToolManager
from src.components import WorkspaceManager


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
    Verify that components provide snapshots correctly.
    """
    print_test_header(
        1, 
        "Basic Context Snapshot",
        "Verify memory, tools, and workspace provide their context snapshots"
    )
    
    try:
        print_test_step(1, "Creating components")
        
        memory = InMemoryManager(short_term_limit=10)
        tools = ToolManager()
        
        temp_dir = tempfile.mkdtemp()
        workspace = WorkspaceManager(temp_dir)
        
        print(f"     ✓ Memory created")
        print(f"     ✓ Tools created")
        print(f"     ✓ Workspace created")
        
        print_test_step(2, "Adding data to components")
        
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
        
        print_test_step(3, "Getting snapshots")
        
        memory_snap = memory.get_snapshot()
        tools_snap = tools.get_snapshot()
        workspace_snap = workspace.get_snapshot()
        
        print(f"     ✓ Memory snapshot keys: {list(memory_snap.keys())}")
        print(f"     ✓ Tools snapshot keys: {list(tools_snap.keys())}")
        print(f"     ✓ Workspace snapshot keys: {list(workspace_snap.keys())}")
        
        print_test_step(4, "Verifying snapshot structure")
        
        # Verify memory snapshot
        assert "recent_messages" in memory_snap
        assert len(memory_snap["recent_messages"]) == 2
        print(f"     ✓ Memory snapshot has {len(memory_snap['recent_messages'])} messages")
        
        # Verify tools snapshot
        assert "calculate" in tools_snap
        print(f"     ✓ Tools snapshot includes 'calculate' tool")
        
        # Verify workspace snapshot
        assert "base_path" in workspace_snap
        assert "files" in workspace_snap
        assert "notes.txt" in workspace_snap["files"]
        print(f"     ✓ Workspace snapshot has {len(workspace_snap['files'])} files")
        
        # Cleanup
        shutil.rmtree(temp_dir, ignore_errors=True)
        
        print_test_result(True, "All components provide snapshots correctly")
        return True
        
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_disabled_context_injection() -> bool:
    """
    TEST 2: Disabled Context Injection (Explicit Model)
    Verify that context is NOT present unless explicitly added.
    """
    print_test_header(
        2,
        "Disabled Context Injection",
        "Verify context is only present if explicitly added"
    )
    
    try:
        print_test_step(1, "Creating components and agent")
        
        memory = InMemoryManager()
        tools = ToolManager()
        
        temp_dir = tempfile.mkdtemp()
        workspace = WorkspaceManager(temp_dir)
        
        print_test_step(2, "Adding data to components")
        
        memory.add_message("user", "Secret message")
        workspace.create_file("secret.txt", "Secret content")
        
        print_test_step(3, "Creating Agent and testing system prompt")
        
        # Create a mock text client for testing
        class MockTextClient:
            def invoke(self, messages, **kwargs):
                return type('Response', (), {'content': messages[0]['content']})()
            def bind_tools(self, tools):
                return self
            def get_model_name(self):
                return "mock"
            async def ainvoke(self, messages, **kwargs):
                return self.invoke(messages, **kwargs)
        
        context = ContextManager()
        agent = Agent(
            text_provider=MockTextClient(),
            context=context,
            memory=memory
        )
        
        # Get system prompt
        system_prompt = agent.build_system_prompt()
        
        print_test_step(4, "Verifying context is NOT present")
        
        assert "Secret message" not in system_prompt
        assert "secret.txt" not in system_prompt
        assert "memory" not in system_prompt.lower()
        
        print(f"     ✓ Context NOT present in system prompt (as expected)")
        
        print_test_step(5, "Explicitly adding context and verifying")
        
        agent.context.add("memory", memory.get_snapshot())
        agent.context.add("workspace", workspace.get_snapshot())
        
        updated_prompt = agent.build_system_prompt()
        
        assert "Secret message" in updated_prompt
        assert "secret.txt" in updated_prompt
        
        print(f"     ✓ Context present after explicit add")
        
        # Cleanup
        shutil.rmtree(temp_dir, ignore_errors=True)
        
        print_test_result(True, "Explicit context model works correctly")
        return True
        
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_agent_with_full_context_injection() -> bool:
    """
    TEST 3: Agent with Full Context (Real LLM)
    Verify agent correctly uses explicitly added context.
    """
    print_test_header(
        3,
        "Agent with Full Context",
        "Test real LLM interaction with explicitly added context"
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
        
        print_test_step(2, "Registering tools")
        
        @tool
        def add_numbers(a: int, b: int) -> int:
            """Add two numbers together."""
            return a + b
        
        tools.register_tool("math", add_numbers)
        print(f"     ✓ Registered 'add_numbers' tool")
        
        print_test_step(3, "Creating initial workspace content")
        
        workspace.create_file("readme.txt", "Welcome to the workspace!")
        print(f"     ✓ Created readme.txt")
        
        print_test_step(4, "Creating agent and adding context")
        
        agent = Agent(
            text_provider=text_client,
            context=context,
            memory=memory,
            tools=tools
        )
        
        # Explicitly add context
        agent.context.add("memory", memory.get_snapshot())
        agent.context.add("available_tools", tools.get_snapshot())
        agent.context.add("workspace", workspace.get_snapshot())
        
        print(f"     ✓ Agent created and context added")
        
        print_test_step(5, "Interaction - asking about workspace")
        
        response = agent.chat(
            "What files are in my workspace?"
        )
        print(f"     ✓ Response: {str(response)[:150]}...")
        
        assert "readme.txt" in str(response).lower()
        print(f"     ✓ Agent correctly identified the file")
        
        # Cleanup
        shutil.rmtree(temp_dir, ignore_errors=True)
        
        print_test_result(True, "Full context working with real LLM")
        return True
        
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def run_all_tests() -> dict:
    """Run all tests and return results."""
    tests = [
        ("Basic Context Snapshot", test_context_injection_basic),
        ("Disabled Context Injection", test_disabled_context_injection),
        ("Agent Full Context", test_agent_with_full_context_injection),
    ]
    
    results = {}
    
    print("\n" + "🔥" * 30)
    print("\n   CONTEXT INJECTION INTEGRATION TESTS")
    print("\n" + "🔥" * 30)
    
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
    
    return results


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Context Injection Integration Tests")
    parser.add_argument(
        "--test", "-t",
        type=str,
        help="Run specific test"
    )
    
    args = parser.parse_args()
    
    if args.test:
        test_map = {
            "basic": test_context_injection_basic,
            "disabled": test_disabled_context_injection,
            "full": test_agent_with_full_context_injection,
        }
        if args.test in test_map:
            success = test_map[args.test]()
            sys.exit(0 if success else 1)
        else:
            print(f"Unknown test: {args.test}")
            sys.exit(1)
    else:
        results = run_all_tests()
        sys.exit(0 if all(results.values()) else 1)
