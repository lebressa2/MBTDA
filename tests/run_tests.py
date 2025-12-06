"""
Agent Framework Test Suite - 3-Level Testing Strategy

Level 1: Atomic Operations (fast, no LLM)
Level 2: Context Analysis (inspect system prompts, custom states)
Level 3: Real Chatbot (full LLM interaction, thinking chain)

Usage:
    python -m tests.run_tests --level 1        # Fast atomic tests
    python -m tests.run_tests --level 2        # Context analysis
    python -m tests.run_tests --level 3        # Real chatbot
    python -m tests.run_tests --all            # All levels
    python -m tests.run_tests --test <name>    # Single test
"""

import argparse
import sys
import os
import tempfile
import shutil
from datetime import datetime
from typing import Any, Callable
from enum import Enum

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
from src.models.data_models import AgentState, Protocol, ProtocolStep, Transition


# =============================================================================
# UTILITIES
# =============================================================================

class Colors:
    """Terminal colors for output."""
    HEADER = '\033[95m'
    BLUE = '\033[94m'
    CYAN = '\033[96m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    DIM = '\033[2m'


def print_header(level: int, test_name: str, objective: str) -> None:
    """Print formatted test header."""
    print(f"\n{'='*80}")
    print(f"{Colors.BOLD}🧪 [LEVEL {level}] {test_name}{Colors.ENDC}")
    print(f"{'='*80}")
    print(f"{Colors.CYAN}📋 OBJECTIVE: {objective}{Colors.ENDC}")
    print(f"{'-'*80}")


def print_step(num: int, description: str) -> None:
    """Print numbered step."""
    print(f"\n  {Colors.BLUE}[{num}]{Colors.ENDC} {description}")


def print_success(msg: str) -> None:
    """Print success message."""
    print(f"     {Colors.GREEN}✓ {msg}{Colors.ENDC}")


def print_fail(msg: str) -> None:
    """Print failure message."""
    print(f"     {Colors.RED}✗ {msg}{Colors.ENDC}")


def print_xml(title: str, content: str) -> None:
    """Print XML content with formatting."""
    print(f"\n  {Colors.YELLOW}📄 {title}:{Colors.ENDC}")
    print(f"  {Colors.DIM}{'─'*76}{Colors.ENDC}")
    for line in content.split('\n'):
        print(f"  {Colors.DIM}│{Colors.ENDC} {line}")
    print(f"  {Colors.DIM}{'─'*76}{Colors.ENDC}")


def print_thinking(content: str) -> None:
    """Print thinking tokens."""
    print(f"\n  {Colors.CYAN}💭 THINKING:{Colors.ENDC}")
    print(f"  {Colors.DIM}{'─'*76}{Colors.ENDC}")
    for line in content.split('\n')[:10]:  # Limit to 10 lines
        print(f"  {Colors.DIM}│{Colors.ENDC} {line}")
    if len(content.split('\n')) > 10:
        print(f"  {Colors.DIM}│ ... (truncated){Colors.ENDC}")
    print(f"  {Colors.DIM}{'─'*76}{Colors.ENDC}")


def print_result(passed: bool, message: str) -> None:
    """Print test result."""
    if passed:
        print(f"\n{Colors.GREEN}✅ TEST PASSED - {message}{Colors.ENDC}")
    else:
        print(f"\n{Colors.RED}❌ TEST FAILED - {message}{Colors.ENDC}")


def get_text_client():
    """Get LLM text client."""
    from tests.clients import get_text_client as _get
    return _get()


# =============================================================================
# LEVEL 1: ATOMIC OPERATIONS
# =============================================================================

def test_interface_implementation() -> bool:
    """Verify all components implement IContextProvider correctly."""
    print_header(1, "Interface Implementation", 
                 "Verify components implement IContextProvider")
    
    try:
        print_step(1, "Creating components")
        memory = InMemoryManager()
        tools = ToolManager()
        temp_dir = tempfile.mkdtemp()
        workspace = WorkspaceManager(temp_dir)
        
        print_step(2, "Checking IContextProvider implementation")
        
        assert isinstance(memory, IContextProvider)
        print_success("InMemoryManager implements IContextProvider")
        
        assert isinstance(tools, IContextProvider)
        print_success("ToolManager implements IContextProvider")
        
        assert isinstance(workspace, IContextProvider)
        print_success("WorkspaceManager implements IContextProvider")
        
        print_step(3, "Checking inject_context flag")
        
        assert memory.inject_context is True
        assert tools.inject_context is True
        assert workspace.inject_context is True
        print_success("All components have inject_context=True by default")
        
        print_step(4, "Checking get_context_contribution method")
        
        assert hasattr(memory, 'get_context_contribution')
        assert hasattr(tools, 'get_context_contribution')
        assert hasattr(workspace, 'get_context_contribution')
        print_success("All components have get_context_contribution method")
        
        shutil.rmtree(temp_dir, ignore_errors=True)
        print_result(True, "All interfaces correctly implemented")
        return True
        
    except Exception as e:
        print_fail(str(e))
        return False


def test_context_contribution_structure() -> bool:
    """Verify context contribution returns correct structure."""
    print_header(1, "Context Contribution Structure",
                 "Verify each component returns properly structured context")
    
    try:
        print_step(1, "Creating and populating components")
        
        memory = InMemoryManager()
        memory.add_message("user", "Hello")
        memory.add_message("assistant", "Hi there!")
        
        tools = ToolManager()
        @tool
        def test_tool() -> str:
            """A test tool."""
            return "test"
        tools.register_tool("default", test_tool)
        
        temp_dir = tempfile.mkdtemp()
        workspace = WorkspaceManager(temp_dir)
        workspace.create_file("test.txt", "content")
        
        print_step(2, "Getting contributions")
        
        mem_ctx = memory.get_context_contribution()
        tool_ctx = tools.get_context_contribution()
        ws_ctx = workspace.get_context_contribution()
        
        print_step(3, "Verifying memory structure")
        assert "memory" in mem_ctx
        assert "recent_messages" in mem_ctx["memory"]
        assert "long_term_keys" in mem_ctx["memory"]
        print_success(f"Memory keys: {list(mem_ctx['memory'].keys())}")
        
        print_step(4, "Verifying tools structure")
        assert "available_tools" in tool_ctx
        print_success(f"Tools: {tool_ctx['available_tools'][:50]}...")
        
        print_step(5, "Verifying workspace structure")
        assert "workspace" in ws_ctx
        assert "base_path" in ws_ctx["workspace"]
        assert "files" in ws_ctx["workspace"]
        assert "storage" in ws_ctx["workspace"]
        print_success(f"Workspace keys: {list(ws_ctx['workspace'].keys())}")
        
        shutil.rmtree(temp_dir, ignore_errors=True)
        print_result(True, "All structures correct")
        return True
        
    except Exception as e:
        print_fail(str(e))
        return False


def test_disabled_injection() -> bool:
    """Verify inject_context=False prevents injection."""
    print_header(1, "Disabled Context Injection",
                 "Verify inject_context=False prevents automatic injection")
    
    try:
        print_step(1, "Creating components with inject_context=False")
        
        memory = InMemoryManager(inject_context=False)
        tools = ToolManager(inject_context=False)
        temp_dir = tempfile.mkdtemp()
        workspace = WorkspaceManager(temp_dir, inject_context=False)
        
        print_success(f"Memory: inject_context={memory.inject_context}")
        print_success(f"Tools: inject_context={tools.inject_context}")
        print_success(f"Workspace: inject_context={workspace.inject_context}")
        
        print_step(2, "Adding data to components")
        memory.add_message("user", "secret")
        workspace.create_file("secret.txt", "content")
        
        print_step(3, "Creating Agent and collecting context")
        
        class MockClient:
            def invoke(self, m, **k): return type('R', (), {'content': 'ok'})()
            def bind_tools(self, t): return self
            def get_model_name(self): return "mock"
        
        context = ContextManager()
        agent = Agent(
            text_provider=MockClient(),
            context=context,
            memory=memory,
            tools=tools,
            workspace_manager=workspace
        )
        
        agent._collect_context_contributions()
        raw = context.get_raw_context()
        
        print_step(4, "Verifying no injection occurred")
        
        assert "memory" not in raw
        print_success("Memory NOT injected")
        
        assert "available_tools" not in raw
        print_success("Tools NOT injected")
        
        assert "workspace" not in raw
        print_success("Workspace NOT injected")
        
        shutil.rmtree(temp_dir, ignore_errors=True)
        print_result(True, "Disabled injection working correctly")
        return True
        
    except Exception as e:
        print_fail(str(e))
        return False


def test_state_machine_basic() -> bool:
    """Test basic state machine transitions."""
    print_header(1, "State Machine Basic",
                 "Verify basic state transitions work correctly")
    
    try:
        print_step(1, "Creating state machine")
        sm = StateMachine()
        print_success(f"Initial state: {sm.current_state}")
        
        print_step(2, "Adding custom state")
        
        class CustomState(Enum):
            ANALYZING = "ANALYZING"
            EXECUTING = "EXECUTING"
        
        sm.register_state(
            "ANALYZING",
            "Agent is analyzing the problem deeply"
        )
        sm.register_state(
            "EXECUTING",
            "Agent is executing a plan"
        )
        print_success("Registered ANALYZING and EXECUTING states")
        
        print_step(3, "Adding transitions")
        
        sm.add_transition(Transition(
            source=AgentState.IDLE.value,
            target="ANALYZING",
            trigger="start:analysis"
        ))
        sm.add_transition(Transition(
            source="ANALYZING",
            target="EXECUTING",
            trigger="plan:ready"
        ))
        sm.add_transition(Transition(
            source="EXECUTING",
            target=AgentState.IDLE.value,
            trigger="task:complete"
        ))
        print_success("Added 3 custom transitions")
        
        print_step(4, "Testing transitions")
        
        # Create mock agent for trigger
        class MockAgent:
            pass
        agent = MockAgent()
        
        sm.trigger("start:analysis", agent)
        assert sm.current_state == "ANALYZING"
        print_success(f"IDLE → ANALYZING: {sm.current_state}")
        
        sm.trigger("plan:ready", agent)
        assert sm.current_state == "EXECUTING"
        print_success(f"ANALYZING → EXECUTING: {sm.current_state}")
        
        sm.trigger("task:complete", agent)
        assert sm.current_state == AgentState.IDLE.value
        print_success(f"EXECUTING → IDLE: {sm.current_state}")
        
        print_result(True, "State machine transitions working")
        return True
        
    except Exception as e:
        print_fail(str(e))
        import traceback
        traceback.print_exc()
        return False


# =============================================================================
# LEVEL 2: CONTEXT ANALYSIS
# =============================================================================

def test_system_prompt_xml_structure() -> bool:
    """Analyze the raw XML structure of system prompts."""
    print_header(2, "System Prompt XML Structure",
                 "Inspect raw XML being sent to LLM")
    
    try:
        print_step(1, "Creating fully configured agent")
        
        text_client = get_text_client()
        memory = InMemoryManager()
        memory.add_message("user", "Previous message from user")
        memory.add_message("assistant", "Previous response from assistant")
        
        tools = ToolManager()
        
        @tool
        def calculate(expr: str) -> str:
            """Calculate a math expression."""
            return str(eval(expr))
        
        @tool
        def get_time() -> str:
            """Get current time."""
            return datetime.now().strftime("%H:%M:%S")
        
        tools.register_tool("math", calculate)
        tools.register_tool("utils", get_time)
        
        temp_dir = tempfile.mkdtemp()
        workspace = WorkspaceManager(temp_dir)
        workspace.create_file("notes.txt", "Important notes")
        
        context = ContextManager()
        
        agent = Agent(
            text_provider=text_client,
            context=context,
            memory=memory,
            tools=tools,
            workspace_manager=workspace
        )
        
        print_success(f"Agent created with all components")
        
        print_step(2, "Building system prompt (without LLM call)")
        
        system_prompt = agent._build_system_prompt()
        
        print_xml("RAW SYSTEM PROMPT", system_prompt)
        
        print_step(3, "Verifying XML elements present")
        
        # Check for key XML tags
        assert "<current_state>" in system_prompt
        print_success("Found <current_state> tag")
        
        assert "<state_instruction>" in system_prompt
        print_success("Found <state_instruction> tag")
        
        assert "<memory>" in system_prompt or "recent_messages" in system_prompt
        print_success("Found memory section")
        
        assert "calculate" in system_prompt or "get_time" in system_prompt
        print_success("Found tools section")
        
        assert "workspace" in system_prompt.lower() or "notes.txt" in system_prompt
        print_success("Found workspace section")
        
        shutil.rmtree(temp_dir, ignore_errors=True)
        print_result(True, "XML structure verified")
        return True
        
    except Exception as e:
        print_fail(str(e))
        import traceback
        traceback.print_exc()
        return False


def test_custom_states_injection() -> bool:
    """Test custom states with specific instructions."""
    print_header(2, "Custom States Injection",
                 "Verify custom state instructions appear in system prompt")
    
    try:
        print_step(1, "Creating state machine with custom states")
        
        sm = StateMachine()
        
        # Register detailed custom states
        sm.register_state(
            "DEEP_ANALYSIS",
            """You are in DEEP_ANALYSIS mode. In this state:
1. Break down the problem into components
2. Identify potential solutions
3. Evaluate trade-offs
4. Do NOT take action yet - only analyze"""
        )
        
        sm.register_state(
            "CODE_GENERATION",
            """You are in CODE_GENERATION mode. In this state:
1. Write clean, documented code
2. Include error handling
3. Add unit tests if applicable
4. Explain your implementation choices"""
        )
        
        sm.register_state(
            "VALIDATION",
            """You are in VALIDATION mode. In this state:
1. Review the generated code/solution
2. Check for edge cases
3. Verify correctness
4. Suggest improvements if needed"""
        )
        
        print_success("Registered 3 custom states with detailed instructions")
        
        print_step(2, "Adding transitions between states")
        
        sm.add_transition(Transition(
            source=AgentState.IDLE.value,
            target="DEEP_ANALYSIS",
            trigger="task:analyze"
        ))
        sm.add_transition(Transition(
            source="DEEP_ANALYSIS",
            target="CODE_GENERATION",
            trigger="analysis:complete"
        ))
        sm.add_transition(Transition(
            source="CODE_GENERATION",
            target="VALIDATION",
            trigger="code:ready"
        ))
        
        print_step(3, "Creating agent with custom state machine")
        
        text_client = get_text_client()
        context = ContextManager()
        
        agent = Agent(
            text_provider=text_client,
            context=context,
            state_machine=sm
        )
        
        print_step(4, "Testing each state's system prompt")
        
        # Test DEEP_ANALYSIS state
        class MockAgent:
            pass
        sm.trigger("task:analyze", MockAgent())
        
        prompt1 = agent._build_system_prompt()
        print_xml("DEEP_ANALYSIS STATE PROMPT", prompt1)
        
        assert "DEEP_ANALYSIS" in prompt1
        assert "Break down the problem" in prompt1
        print_success("DEEP_ANALYSIS instruction injected correctly")
        
        # Test CODE_GENERATION state
        sm.trigger("analysis:complete", MockAgent())
        
        # Need to reset context for new prompt
        context = ContextManager()
        agent.context = context
        
        prompt2 = agent._build_system_prompt()
        print_xml("CODE_GENERATION STATE PROMPT", prompt2)
        
        assert "CODE_GENERATION" in prompt2
        assert "Write clean" in prompt2 or "documented code" in prompt2
        print_success("CODE_GENERATION instruction injected correctly")
        
        print_result(True, "Custom states working correctly")
        return True
        
    except Exception as e:
        print_fail(str(e))
        import traceback
        traceback.print_exc()
        return False


def test_protocol_context_injection() -> bool:
    """Test protocol injection into context."""
    print_header(2, "Protocol Context Injection",
                 "Verify protocols appear correctly in system prompt")
    
    try:
        print_step(1, "Creating agent with protocol")
        
        text_client = get_text_client()
        context = ContextManager()
        
        agent = Agent(
            text_provider=text_client,
            context=context
        )
        
        print_step(2, "Creating and adding protocol")
        
        protocol = Protocol(
            protocol_name="code_review",
            description="Standard code review process",
            steps=[
                ProtocolStep(
                    name="check_syntax",
                    goal="Verify code syntax is correct",
                    instructions=["Run linters and check for syntax errors"]
                ),
                ProtocolStep(
                    name="check_logic",
                    goal="Review business logic",
                    instructions=["Ensure the logic is correct and handles edge cases"]
                ),
                ProtocolStep(
                    name="check_tests",
                    goal="Verify test coverage",
                    instructions=["Check that all critical paths have tests"]
                )
            ]
        )
        
        agent.add_protocol(protocol)
        print_success(f"Added protocol: {protocol.protocol_name} with {len(protocol.steps)} steps")
        
        print_step(3, "Injecting protocol into context")
        
        # Manually add protocol to context
        context.add("active_protocols", [protocol.model_dump()])
        
        prompt = agent._build_system_prompt()
        print_xml("SYSTEM PROMPT WITH PROTOCOL", prompt)
        
        print_step(4, "Verifying protocol in prompt")
        
        assert "code_review" in prompt or "active_protocols" in prompt
        print_success("Protocol name found in prompt")
        
        assert "check_syntax" in prompt or "syntax" in prompt.lower()
        print_success("Protocol steps referenced in prompt")
        
        print_result(True, "Protocol injection working")
        return True
        
    except Exception as e:
        print_fail(str(e))
        import traceback
        traceback.print_exc()
        return False


# =============================================================================
# LEVEL 3: REAL CHATBOT SIMULATION
# =============================================================================

def test_chatbot_multi_turn() -> bool:
    """Simulate a real chatbot with multiple conversation turns."""
    print_header(3, "Multi-Turn Chatbot Simulation",
                 "Real chatbot with memory, tools, thinking chain visible")
    
    try:
        print_step(1, "Setting up chatbot environment")
        
        text_client = get_text_client()
        memory = InMemoryManager(short_term_limit=50)
        tools = ToolManager()
        temp_dir = tempfile.mkdtemp()
        workspace = WorkspaceManager(temp_dir)
        context = ContextManager()
        
        # Register useful tools
        @tool
        def add(a: int, b: int) -> int:
            """Add two numbers."""
            return a + b
        
        @tool
        def save_note(title: str, content: str) -> str:
            """Save a note to workspace."""
            workspace.create_file(f"{title}.txt", content)
            return f"Saved note: {title}"
        
        @tool
        def list_notes() -> str:
            """List all saved notes."""
            files = workspace.list_directory(".")
            return ", ".join(files) if files else "No notes yet"
        
        tools.register_tool("math", add)
        tools.register_tool("notes", save_note)
        tools.register_tool("notes", list_notes)
        
        print_success("Created: memory, tools (add, save_note, list_notes), workspace")
        
        agent = Agent(
            text_provider=text_client,
            context=context,
            memory=memory,
            tools=tools,
            workspace_manager=workspace
        )
        
        print_success(f"Agent ready. Initial state: {agent.state_machine.current_state}")
        
        # Conversation simulation
        conversations = [
            ("User introduces themselves", "Hi! My name is Carlos. I'm a Python developer."),
            ("User asks for calculation", "What is 15 + 27?"),
            ("User asks about memory", "Do you remember my name?"),
        ]
        
        for turn_num, (description, user_msg) in enumerate(conversations, 1):
            print(f"\n  {'═'*76}")
            print(f"  {Colors.BOLD}📍 TURN {turn_num}: {description}{Colors.ENDC}")
            print(f"  {'═'*76}")
            
            print(f"\n  {Colors.YELLOW}👤 USER:{Colors.ENDC} {user_msg}")
            
            # Show system prompt before call
            pre_prompt = agent._build_system_prompt()
            print_xml(f"SYSTEM PROMPT (Turn {turn_num})", pre_prompt[:1500] + "..." if len(pre_prompt) > 1500 else pre_prompt)
            
            # Process message
            print(f"\n  {Colors.CYAN}⏳ Processing...{Colors.ENDC}")
            response = agent.process_message(user_msg)
            response_text = str(response.content if hasattr(response, 'content') else response)
            
            # Show thinking (if visible in response)
            if "<think>" in response_text or "thinking" in response_text.lower():
                print_thinking(response_text[:500])
            
            print(f"\n  {Colors.GREEN}🤖 ASSISTANT:{Colors.ENDC} {response_text[:300]}...")
            
            # Show state
            print(f"\n  {Colors.DIM}📊 State: {agent.state_machine.current_state} | Memory: {len(memory.get_recent_messages(100))} msgs{Colors.ENDC}")
        
        print_step(4, "Final memory state")
        messages = memory.get_recent_messages(10)
        for i, msg in enumerate(messages):
            role = msg["role"].upper()
            content = msg["content"][:60] + "..." if len(msg["content"]) > 60 else msg["content"]
            print(f"     {i+1}. [{role}] {content}")
        
        shutil.rmtree(temp_dir, ignore_errors=True)
        print_result(True, "Multi-turn chatbot working")
        return True
        
    except Exception as e:
        print_fail(str(e))
        import traceback
        traceback.print_exc()
        return False


def test_tool_usage_chain() -> bool:
    """Test agent using tools in a chain."""
    print_header(3, "Tool Usage Chain",
                 "Agent uses multiple tools to complete a task")
    
    try:
        print_step(1, "Setting up agent with tools")
        
        text_client = get_text_client()
        memory = InMemoryManager()
        tools = ToolManager()
        temp_dir = tempfile.mkdtemp()
        workspace = WorkspaceManager(temp_dir)
        context = ContextManager()
        
        # Create a chain of tools
        @tool
        def get_data() -> str:
            """Fetch some data for processing."""
            return "Temperature: 25°C, Humidity: 60%, Wind: 10km/h"
        
        @tool
        def analyze_data(data: str) -> str:
            """Analyze the weather data."""
            return f"Analysis: Weather is pleasant. {data}"
        
        @tool
        def save_report(content: str) -> str:
            """Save a report to file."""
            workspace.create_file("weather_report.txt", content)
            return "Report saved to weather_report.txt"
        
        tools.register_tool("data", get_data)
        tools.register_tool("analysis", analyze_data)
        tools.register_tool("reports", save_report)
        
        print_success("Registered tool chain: get_data → analyze_data → save_report")
        
        agent = Agent(
            text_provider=text_client,
            context=context,
            memory=memory,
            tools=tools,
            workspace_manager=workspace
        )
        
        print_step(2, "Showing initial system prompt")
        
        prompt = agent._build_system_prompt()
        print_xml("SYSTEM PROMPT WITH TOOLS", prompt)
        
        print_step(3, "Asking agent to use tools")
        
        print(f"\n  {Colors.YELLOW}👤 USER:{Colors.ENDC} Get the weather data, analyze it, and save a report.")
        
        response = agent.process_message(
            "Get the weather data, analyze it, and save a report."
        )
        
        response_text = str(response.content if hasattr(response, 'content') else response)
        print(f"\n  {Colors.GREEN}🤖 ASSISTANT:{Colors.ENDC}")
        print(f"     {response_text}")
        
        print_step(4, "Checking if report was created")
        
        files = workspace.list_directory(".")
        print_success(f"Files in workspace: {files}")
        
        if "weather_report.txt" in files:
            content = workspace.read_file("weather_report.txt")
            print_success(f"Report content: {content[:100]}...")
        
        shutil.rmtree(temp_dir, ignore_errors=True)
        print_result(True, "Tool chain executed")
        return True
        
    except Exception as e:
        print_fail(str(e))
        import traceback
        traceback.print_exc()
        return False


def test_full_react_loop() -> bool:
    """Test full ReAct reasoning loop with visibility."""
    print_header(3, "Full ReAct Loop",
                 "Observe complete reasoning-action-observation cycle")
    
    try:
        print_step(1, "Setting up complex scenario")
        
        text_client = get_text_client()
        memory = InMemoryManager()
        tools = ToolManager()
        temp_dir = tempfile.mkdtemp()
        workspace = WorkspaceManager(temp_dir)
        
        # Create initial files
        workspace.create_file("project/main.py", "def hello(): pass")
        workspace.create_file("project/test.py", "def test_hello(): pass")
        workspace.create_directory("project/utils")
        
        context = ContextManager()
        
        @tool
        def read_file(path: str) -> str:
            """Read a file from workspace."""
            content = workspace.read_file(path)
            return content if content else f"File not found: {path}"
        
        @tool
        def list_files(directory: str = ".") -> str:
            """List files in a directory."""
            files = workspace.list_directory(directory)
            return ", ".join(files) if files else "Empty directory"
        
        @tool
        def create_file(path: str, content: str) -> str:
            """Create or update a file."""
            success = workspace.create_file(path, content)
            return f"Created: {path}" if success else f"Failed to create: {path}"
        
        tools.register_tool("files", read_file)
        tools.register_tool("files", list_files)
        tools.register_tool("files", create_file)
        
        print_success("Created project structure with files")
        print_success("Registered file operation tools")
        
        # Setup custom states for ReAct
        sm = StateMachine()
        sm.register_state(
            "REASONING",
            "You are REASONING about the problem. Think step by step. Explain your thought process."
        )
        sm.register_state(
            "ACTING",
            "You are ACTING on your plan. Use tools to make progress."
        )
        sm.register_state(
            "OBSERVING",
            "You are OBSERVING the results. Analyze what happened and plan next steps."
        )
        
        agent = Agent(
            text_provider=text_client,
            context=context,
            memory=memory,
            tools=tools,
            workspace_manager=workspace,
            state_machine=sm
        )
        
        print_step(2, "Showing full system prompt")
        
        prompt = agent._build_system_prompt()
        print_xml("COMPLETE SYSTEM PROMPT", prompt)
        
        print_step(3, "Complex task requiring reasoning")
        
        task = "List all files in the project directory, read main.py, and create a README.md summarizing what the project does."
        
        print(f"\n  {Colors.YELLOW}👤 USER:{Colors.ENDC} {task}")
        
        print(f"\n  {Colors.CYAN}⏳ Agent processing (ReAct loop)...{Colors.ENDC}")
        
        response = agent.process_message(task)
        
        response_text = str(response.content if hasattr(response, 'content') else response)
        
        print(f"\n  {Colors.GREEN}🤖 ASSISTANT RESPONSE:{Colors.ENDC}")
        # Format response nicely
        for line in response_text.split('\n'):
            print(f"     {line}")
        
        print_step(4, "Checking workspace state after task")
        
        all_files = workspace.list_directory(".")
        print_success(f"Root files: {all_files}")
        
        if workspace.file_exists("README.md"):
            readme = workspace.read_file("README.md")
            print_success(f"README.md created with {len(readme)} chars")
        
        print_step(5, "Showing conversation history")
        
        messages = memory.get_recent_messages(10)
        print(f"\n  {Colors.DIM}Conversation history ({len(messages)} messages):{Colors.ENDC}")
        for msg in messages:
            role = msg["role"]
            content = msg["content"][:80] + "..." if len(msg["content"]) > 80 else msg["content"]
            print(f"     [{role.upper()}] {content}")
        
        shutil.rmtree(temp_dir, ignore_errors=True)
        print_result(True, "ReAct loop completed")
        return True
        
    except Exception as e:
        print_fail(str(e))
        import traceback
        traceback.print_exc()
        return False


# =============================================================================
# TEST RUNNER
# =============================================================================

LEVEL_1_TESTS = {
    "interface_implementation": test_interface_implementation,
    "context_contribution_structure": test_context_contribution_structure,
    "disabled_injection": test_disabled_injection,
    "state_machine_basic": test_state_machine_basic,
}

LEVEL_2_TESTS = {
    "system_prompt_xml_structure": test_system_prompt_xml_structure,
    "custom_states_injection": test_custom_states_injection,
    "protocol_context_injection": test_protocol_context_injection,
}

LEVEL_3_TESTS = {
    "chatbot_multi_turn": test_chatbot_multi_turn,
    "tool_usage_chain": test_tool_usage_chain,
    "full_react_loop": test_full_react_loop,
}

ALL_TESTS = {**LEVEL_1_TESTS, **LEVEL_2_TESTS, **LEVEL_3_TESTS}


def run_level(level: int) -> dict:
    """Run all tests for a specific level."""
    tests = {1: LEVEL_1_TESTS, 2: LEVEL_2_TESTS, 3: LEVEL_3_TESTS}.get(level, {})
    
    print(f"\n{'🔥'*30}")
    print(f"\n   LEVEL {level} TESTS")
    print(f"\n{'🔥'*30}")
    
    results = {}
    for name, func in tests.items():
        try:
            results[name] = func()
        except Exception as e:
            print(f"\n❌ {name}: CRASHED - {e}")
            results[name] = False
    
    return results


def run_all() -> dict:
    """Run all tests at all levels."""
    results = {}
    for level in [1, 2, 3]:
        results.update(run_level(level))
    return results


def print_summary(results: dict) -> None:
    """Print test summary."""
    print(f"\n{'='*80}")
    print("   TEST RESULTS SUMMARY")
    print(f"{'='*80}")
    
    passed = sum(1 for r in results.values() if r)
    total = len(results)
    
    for name, result in results.items():
        status = f"{Colors.GREEN}✅ PASSED{Colors.ENDC}" if result else f"{Colors.RED}❌ FAILED{Colors.ENDC}"
        print(f"  {name}: {status}")
    
    print(f"\n  Total: {passed}/{total} tests passed")
    
    if passed == total:
        print(f"\n{Colors.GREEN}🎉 ALL TESTS PASSED!{Colors.ENDC}")
    else:
        print(f"\n{Colors.YELLOW}⚠️ SOME TESTS FAILED{Colors.ENDC}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Agent Framework Test Suite")
    parser.add_argument("--level", "-l", type=int, choices=[1, 2, 3],
                       help="Run tests at specific level (1, 2, or 3)")
    parser.add_argument("--all", "-a", action="store_true",
                       help="Run all tests at all levels")
    parser.add_argument("--test", "-t", type=str,
                       help="Run specific test by name")
    parser.add_argument("--list", action="store_true",
                       help="List all available tests")
    
    args = parser.parse_args()
    
    if args.list:
        print("\nAvailable tests:")
        print("\nLevel 1 (Atomic):")
        for name in LEVEL_1_TESTS:
            print(f"  - {name}")
        print("\nLevel 2 (Context Analysis):")
        for name in LEVEL_2_TESTS:
            print(f"  - {name}")
        print("\nLevel 3 (Real Chatbot):")
        for name in LEVEL_3_TESTS:
            print(f"  - {name}")
        sys.exit(0)
    
    if args.test:
        if args.test in ALL_TESTS:
            success = ALL_TESTS[args.test]()
            sys.exit(0 if success else 1)
        else:
            print(f"Unknown test: {args.test}")
            print(f"Use --list to see available tests")
            sys.exit(1)
    
    if args.level:
        results = run_level(args.level)
    elif args.all:
        results = run_all()
    else:
        # Default: run all tests
        results = run_all()
    
    print_summary(results)
    sys.exit(0 if all(results.values()) else 1)
