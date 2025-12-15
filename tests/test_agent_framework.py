"""
Agent Framework Tests - Real API Integration.

Tests the Agent class with real LLM APIs (Groq/Google) to validate:
- Synchronous mode (process_message)
- State machine transitions
- Context management
- Memory management
- Tool execution
- Protocols
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from typing import Dict, Any, List, Optional
from dotenv import load_dotenv
load_dotenv()

from src.interfaces.base import ITextClient, LogLevel
from src.agent import Agent
from src.agents.react_agent import create_react_agent
from src.components import (
    ContextManager, StateMachine, ConsoleLogger,
    InMemoryManager, ToolManager, WorkspaceManager, LocalWorkspaceManager, Watchdog
)
from src.models import Protocol, ProtocolStep, AgentState, Transition

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


# ==============================================================================
# TEST 1: Basic Agent with Real LLM
# ==============================================================================

def test_basic_agent():
    """Test basic agent functionality with real LLM."""
    print("\n" + "="*60)
    print("🧪 TEST: Basic Agent with Real LLM")
    print("="*60)
    
    try:
        # Get real LLM client
        text_client = get_text_client()
        
        # Create agent with minimal components
        # Use create_react_agent to get the standard behavior
        agent = create_react_agent(
            text_provider=text_client,
            logger=ConsoleLogger(min_level=LogLevel.INFO)
        )
        
        print(f"\n📊 Initial State: {agent.get_current_state()}")
        
        # Process a simple message
        response = agent.process_message("What is 2 + 2? Answer briefly.")
        
        print(f"\n💬 Response: {response}")
        print(f"📊 Final State: {agent.get_current_state()}")
        
        # Verify state transition
        assert agent.get_current_state() == AgentState.IDLE.value, "Agent should return to IDLE"
        
        print("\n✅ Basic Agent Test PASSED")
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
    print("\n" + "="*60)
    print("🧪 TEST: Agent with Memory")
    print("="*60)
    
    try:
        text_client = get_text_client()
        memory = InMemoryManager(short_term_limit=10)
        
        agent = create_react_agent(
            text_provider=text_client,
            memory=memory,
            logger=ConsoleLogger(min_level=LogLevel.INFO)
        )
        
        # First message
        print("\n📝 Sending first message...")
        response1 = agent.process_message("My name is Carlos. Remember that.")
        print(f"💬 Response 1: {response1}")
        
        # Second message - should remember context
        print("\n📝 Sending second message...")
        response2 = agent.process_message("What is my name?")
        print(f"💬 Response 2: {response2}")
        
        # Check memory
        short_term = memory.get_recent_messages()
        print(f"\n🧠 Short-term memory has {len(short_term)} items")
        
        # Verify memory contains our messages
        assert len(short_term) >= 2, "Memory should contain at least 2 messages"
        
        print("\n✅ Memory Test PASSED")
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
    print("\n" + "="*60)
    print("🧪 TEST: Agent with Tools")
    print("="*60)
    
    try:
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
        
        agent = create_react_agent(
            text_provider=text_client,
            tools=tool_manager,
            logger=ConsoleLogger(min_level=LogLevel.INFO)
        )
        
        # Test tool descriptions are available
        descriptions = tool_manager.get_tool_descriptions()
        print(f"\n🔧 Available tools: {descriptions}")
        
        # Execute tool directly
        result = tool_manager.execute_tool("add", a=5, b=3)
        print(f"📊 Direct tool execution (5+3): {result}")
        assert result == 8, "Tool execution failed"
        
        # Ask agent to use tool (note: may not trigger tool call depending on LLM)
        response = agent.process_message("What is 15 multiplied by 7? Calculate it.")
        print(f"\n💬 Response: {response}")
        
        print("\n✅ Tools Test PASSED")
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
    print("\n" + "="*60)
    print("🧪 TEST: Agent with Workspace")
    print("="*60)
    
    try:
        import tempfile
        import shutil
        
        text_client = get_text_client()
        
        # Use local workspaces directory
        workspaces_root = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "workspaces")
        print(f"📁 Using workspaces root: {workspaces_root}")
        
        # workspace = WorkspaceManager(base_path=workspace_path)
        workspace = LocalWorkspaceManager(agent_name="test_agent", base_path=workspaces_root)
        print(f"📁 Workspace initialized at: {workspace.base_path}")
        
        # Ensure clean state for test
        if os.path.exists(workspace.base_path):
            shutil.rmtree(workspace.base_path)
        
        agent = create_react_agent(
            text_provider=text_client,
            workspace_manager=workspace,
            logger=ConsoleLogger(min_level=LogLevel.INFO)
        )
        
        # Test workspace operations
        workspace.create_file("test.txt", "Hello, World!")
        content = workspace.read_file("test.txt")
        print(f"📄 Created file with content: {content}")
        
        workspace.create_directory("subdir")
        workspace.create_file("subdir/nested.txt", "Nested content")
        
        files = workspace.list_directory(".")
        print(f"📁 Files in workspace: {files}")
        
        # Create snapshot
        snapshot_id = workspace.create_snapshot("test_snapshot")
        print(f"📸 Created snapshot: {snapshot_id}")
        
        # Get audit log
        audit_log = workspace.get_audit_log()
        print(f"📋 Audit log has {len(audit_log)} entries")
        
        # Cleanup - COMMENTED OUT to allow user inspection
        # shutil.rmtree(workspace.base_path)
        # print(f"🗑️ Cleaned up workspace")
        print(f"👀 Workspace left for inspection at: {workspace.base_path}")
        
        print("\n✅ Workspace Test PASSED")
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
    print("\n" + "="*60)
    print("🧪 TEST: Agent with Protocol")
    print("="*60)
    
    try:
        text_client = get_text_client()
        
        agent = create_react_agent(
            text_provider=text_client,
            logger=ConsoleLogger(min_level=LogLevel.INFO)
        )
        
        # Create a protocol
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
        
        # Add protocol to agent
        agent.add_protocol(analysis_protocol)
        
        # Verify protocol was added
        retrieved = agent.get_protocol("code_review")
        assert retrieved is not None, "Protocol should be retrievable"
        assert retrieved.protocol_name == "code_review"
        print(f"📋 Protocol '{retrieved.protocol_name}' added with {len(retrieved.steps)} steps")
        
        # Get agent status
        status = agent.get_status()
        print(f"📊 Agent status: {status}")
        assert "code_review" in status["protocols"], "Protocol should be in status"
        
        print("\n✅ Protocol Test PASSED")
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
    print("\n" + "="*60)
    print("🧪 TEST: State Machine Transitions")
    print("="*60)
    
    try:
        text_client = get_text_client()
        
        # Use create_react_agent to ensure we have transitions
        agent = create_react_agent(
            text_provider=text_client,
            logger=ConsoleLogger(min_level=LogLevel.DEBUG)
        )
        
        print(f"📊 Initial state: {agent.get_current_state()}")
        assert agent.get_current_state() == AgentState.IDLE.value
        
        # Track state changes during message processing
        states_visited = [agent.get_current_state()]
        
        # Process message (will trigger state transitions)
        response = agent.process_message("Hello!")
        
        # After processing, should be back to IDLE
        final_state = agent.get_current_state()
        print(f"📊 Final state: {final_state}")
        assert final_state == AgentState.IDLE.value, f"Expected IDLE, got {final_state}"
        
        print("\n✅ State Machine Test PASSED")
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
    print("\n" + "="*60)
    print("🧪 TEST: Full Agent Integration")
    print("="*60)
    
    try:
        import tempfile
        import shutil
        
        # Setup all components
        text_client = get_text_client()
        memory = InMemoryManager()
        tool_manager = ToolManager()
        logger = ConsoleLogger(min_level=LogLevel.INFO)
        
        # Use local workspaces directory
        workspaces_root = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "workspaces")
        workspace = LocalWorkspaceManager(agent_name="full_test_agent", base_path=workspaces_root)
        
        # Ensure clean state for test
        if os.path.exists(workspace.base_path):
            shutil.rmtree(workspace.base_path)
        
        from langchain_core.tools import StructuredTool

        # Register tools
        tool_manager.register_tool(
            context="workspace",
            tool=StructuredTool.from_function(
                func=lambda text: workspace.create_file("notes.txt", text) or "Saved",
                name="save_note",
                description="Save a note to file"
            )
        )
        
        # Create fully configured agent
        agent = create_react_agent(
            text_provider=text_client,
            memory=memory,
            tools=tool_manager,
            workspace_manager=workspace,
            logger=logger
        )
        
        print(f"🤖 Agent created with all components")
        print(f"📊 Status: {agent.get_status()}")
        
        # Test conversation
        response = agent.process_message(
            "I'm testing the agent framework. Tell me something interesting about AI."
        )
        print(f"\n💬 Response: {str(response)[:200]}...")
        
        # Verify all components worked
        assert agent.get_current_state() == AgentState.IDLE.value
        assert len(memory.get_recent_messages()) >= 2  # User + Assistant messages
        
        # Cleanup - COMMENTED OUT to allow user inspection
        # shutil.rmtree(workspace.base_path)
        print(f"👀 Workspace left for inspection at: {workspace.base_path}")
        
        print("\n✅ Full Integration Test PASSED")
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
    print("\n" + "="*60)
    print("🧪 TEST: Advanced State Machine")
    print("="*60)
    
    try:
        text_client = get_text_client()
        agent = Agent(
            text_provider=text_client,
            logger=ConsoleLogger(min_level=LogLevel.DEBUG)
        )
        
        # Track callbacks
        callbacks = {"on_enter": False, "on_exit": False, "condition_checked": False}
        
        # 1. Register a custom state
        agent.state_machine.register_state(
            name="CUSTOM_STATE",
            instruction="Custom state instruction",
            on_enter=lambda ag: callbacks.update({"on_enter": True}),
            on_exit=lambda ag: callbacks.update({"on_exit": True})
        )
        
        # 2. Add transition with condition
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
        
        # 3. Trigger transition
        print("🔄 Triggering transition to CUSTOM_STATE...")
        success = agent.state_machine.trigger("custom_trigger", agent)
        
        print(f"📊 Transition success: {success}")
        print(f"📊 Current State: {agent.get_current_state()}")
        print(f"📊 Callbacks: {callbacks}")
        
        # Verify
        assert success, "Transition should succeed"
        assert agent.get_current_state() == "CUSTOM_STATE", "Should be in CUSTOM_STATE"
        assert callbacks["condition_checked"], "Condition should be checked"
        assert callbacks["on_enter"], "on_enter should be called"
        
        # 4. Transition back (trigger exit callback)
        print("🔄 Forcing transition back to IDLE...")
        agent.state_machine.force_transition(AgentState.IDLE.value, agent)
        
        print(f"📊 Callbacks after exit: {callbacks}")
        assert callbacks["on_exit"], "on_exit should be called"
        
        print("\n✅ Advanced State Machine Test PASSED")
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
    print("\n" + "🔥"*30)
    print("\n   AGENT FRAMEWORK - REAL API TESTS")
    print("\n" + "🔥"*30)
    
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
    ]
    
    for test_name, test_func in tests:
        try:
            results[test_name] = test_func()
        except Exception as e:
            print(f"\n❌ {test_name} crashed: {e}")
            results[test_name] = False
    
    # Summary
    print("\n" + "="*60)
    print("   TEST RESULTS SUMMARY")
    print("="*60)
    
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
    else:
        success = run_all_tests()
        sys.exit(0 if success else 1)
