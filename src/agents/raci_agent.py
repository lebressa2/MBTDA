"""
RACI Agent - Simple Retrieval Augmented Code Interpreter Agent.

Uses the framework's thin Agent container with injected components.
RACIToolManager provides execute_code, read_file, write_file tools.

Usage:
    python -m src.agents.raci_agent          # Demo mode (no LLM)
    python -m src.agents.raci_agent --real   # Interactive with real LLM
"""

import os
import sys
from pathlib import Path

from dotenv import load_dotenv

from ..agent import Agent
from ..components.workspace import LayeredWorkspaceManager
from ..components.interpreter import SandboxInterpreter
from ..components.tools import RACIToolManager
from ..components import ContextManager, InMemoryManager
from ..runners.simple_sync_runner import SimpleSyncRunner


def create_raci_agent(workspace_path: str = "./raci_workspace", debug: bool = False):
    """
    Create a RACI agent with all components injected.
    
    Returns:
        tuple: (agent, workspace, tools)
    """
    load_dotenv()
    
    # 1. Workspace (3-layer)
    workspace = LayeredWorkspaceManager(
        base_path=workspace_path,
        agent_id="raci_agent",
        office_base=Path(workspace_path) / ".office"
    )
    
    # 2. Interpreter
    interpreter = SandboxInterpreter(workspace)
    
    # 3. RACI Tools
    tools = RACIToolManager(interpreter, workspace)
    
    # 4. LLM Client
    llm = None
    if os.getenv("GROQ_API_KEY"):
        from ..clients.llm.groq_client import GroqClient
        model = os.getenv("BASE_GROQ_TEXT_MODEL") or "llama3-70b-8192"
        print(f"⏳ Loading Groq client ({model})...")
        llm = GroqClient(model_name=model, api_key=os.getenv("GROQ_API_KEY"))
        print(f"✅ LLM: Groq ({model})")
    elif os.getenv("GOOGLE_API_KEY"):
        from ..clients.llm.google_client import GoogleClient
        model = os.getenv("BASE_GOOGLE_TEXT_MODEL") or "gemini-1.5-pro"
        llm = GoogleClient(model_name=model, api_key=os.getenv("GOOGLE_API_KEY"))
        print(f"✅ LLM: Google ({model})")
    
    if not llm:
        print("❌ No LLM. Set GROQ_API_KEY or GOOGLE_API_KEY")
        return None, workspace, tools
    
    agent = Agent(
        text_provider=llm,
        context=ContextManager(initial_context={
            "layer_instructions": (
                "You are operating in a 3-layer workspace:\n"
                "1. **PROJECT**: The user's codebase (Source of Truth). Read/Write here.\n"
                "2. **OFFICE**: Your private workspace for notes, plans, and custom tools. "
                "   You can import python files created here. Use this for intermediate work.\n"
                "3. **INTERPRETER**: Ephemeral execution sandbox. Files here are temporary.\n"
                "\n"
                "Use 'move_file' to promote artifacts from INTERPRETER -> PROJECT, "
                "or to save useful tools to OFFICE."
            )
        }),
        memory=InMemoryManager(),
        tools=tools,
        workspace_manager=workspace,
    )
    
    # DEBUG: Show registered components
    if debug:
        print(f"\n🔍 Registered components: {agent.context.list_registered_components()}")
        print(f"🔍 Provider info: {agent.context.get_context_provider_info()}")
    
    return agent, workspace, tools


def demo_mode():
    """Test tools without LLM."""
    print("=" * 50)
    print("🧪 RACI Demo Mode")
    print("=" * 50)
    
    workspace = LayeredWorkspaceManager(
        base_path="./raci_workspace",
        agent_id="demo"
    )
    interpreter = SandboxInterpreter(workspace)
    tools = RACIToolManager(interpreter, workspace)
    
    result = tools.execute_tool("execute_code", code="""
from weather import get
print(get("Tokyo"))
""")
    print(result.get("output", result.get("error")))


def interactive_mode():
    """Interactive chat using SimpleSyncRunner."""
    agent, workspace, tools = create_raci_agent(debug=True)
    
    if not agent:
        return
    
    print("\n" + "=" * 50)
    print("💬 RACI Chat (quit to exit)")
    print("=" * 50)
    
    while True:
        try:
            user_input = input("\n👤 You: ").strip()
            if not user_input or user_input.lower() in ["quit", "exit", "q"]:
                print("👋 Bye!")
                break
            
            # Use SimpleSyncRunner with run_with
            runner = SimpleSyncRunner(user_input, debug=True)
            agent.run_with(runner)
            
            # Get response from runner result
            response = runner.start()  # Already ran via run_with, but this returns the result
            print(f"\n🤖 Agent: {response}")
            
        except KeyboardInterrupt:
            print("\n👋 Bye!")
            break


if __name__ == "__main__":
    if "--real" in sys.argv:
        interactive_mode()
    else:
        demo_mode()
        print("\n💡 Use --real for LLM mode")
