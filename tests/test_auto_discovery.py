"""
Test to demonstrate automatic component discovery with IContextProvider.

This test shows that components implementing IContextProvider are automatically
discovered without needing to be hardcoded in a list.
"""

import sys
import os
import tempfile
import shutil
from typing import Any

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.agent import Agent
from src.components.context_manager import ContextManager
from src.components.memory import InMemoryManager
from src.components.tools import ToolManager
from src.components.workspace import WorkspaceManager
from src.interfaces.base import IContextProvider


class CustomAnalyticsComponent(IContextProvider):
    """Custom component that tracks analytics and contributes to context."""
    
    inject_context: bool = True
    
    def __init__(self):
        self.page_views = 0
        self.user_actions = []
    
    def track_view(self, page: str):
        """Track a page view."""
        self.page_views += 1
        self.user_actions.append(f"Viewed {page}")
    
    def track_action(self, action: str):
        """Track a user action."""
        self.user_actions.append(action)
    
    def get_context_contribution(self) -> dict[str, Any]:
        """Contribute analytics data to the agent's context."""
        return {
            "analytics": {
                "total_page_views": self.page_views,
                "recent_actions": self.user_actions[-5:],  # Last 5 actions
                "total_actions": len(self.user_actions)
            }
        }


class CustomConfigComponent(IContextProvider):
    """Custom component that manages configuration."""
    
    inject_context: bool = True
    
    def __init__(self):
        self.config = {
            "theme": "dark",
            "language": "pt-BR",
            "timezone": "America/Sao_Paulo"
        }
    
    def update_config(self, key: str, value: str):
        """Update a configuration value."""
        self.config[key] = value
    
    def get_context_contribution(self) -> dict[str, Any]:
        """Contribute configuration to the agent's context."""
        return {
            "user_config": self.config
        }


def test_automatic_discovery():
    """Test that custom components are automatically discovered."""
    
    print("\n" + "="*80)
    print("🔍 AUTOMATIC COMPONENT DISCOVERY TEST")
    print("="*80)
    
    print("\n[1] Creating standard components...")
    memory = InMemoryManager()
    tools = ToolManager()
    
    # Add a simple tool so ToolManager has something to contribute
    from langchain_core.tools import tool
    
    @tool
    def example_tool(text: str) -> str:
        """An example tool for testing."""
        return f"Processed: {text}"
    
    tools.register_tool("test", example_tool)
    
    temp_dir = tempfile.mkdtemp()
    workspace = WorkspaceManager(temp_dir)
    print("    ✓ Memory, Tools, Workspace created")
    
    print("\n[2] Creating custom components...")
    analytics = CustomAnalyticsComponent()
    config = CustomConfigComponent()
    print("    ✓ Analytics component created")
    print("    ✓ Config component created")
    
    print("\n[3] Adding data to custom components...")
    analytics.track_view("homepage")
    analytics.track_view("dashboard")
    analytics.track_action("clicked_button")
    config.update_config("theme", "light")
    print("    ✓ Tracked 2 page views and 1 action")
    print("    ✓ Updated config theme to 'light'")
    
    print("\n[4] Creating mock text client...")
    class MockTextClient:
        def invoke(self, messages, **kwargs):
            return type('Response', (), {'content': messages[0]['content']})()
        def bind_tools(self, tools):
            return self
        def get_model_name(self):
            return "mock"
    
    print("\n[5] Creating agent with standard components...")
    context = ContextManager()
    agent = Agent(
        text_provider=MockTextClient(),
        context=context,
        memory=memory,
        tools=tools,
        workspace_manager=workspace
    )
    print("    ✓ Agent created with standard components")
    
    print("\n[6] Adding custom components as attributes (will be auto-discovered)...")
    # Add custom components as agent attributes
    # They will be automatically discovered by _collect_context_contributions()
    agent.analytics = analytics
    agent.config = config
    print("    ✓ Added analytics component")
    print("    ✓ Added config component")
    
    print("\n[7] Triggering automatic context collection...")
    agent._collect_context_contributions()
    print("    ✓ Context collection completed")
    
    print("\n[8] Verifying ALL components contributed to context...")
    raw_ctx = context.get_raw_context()
    
    # Check standard components
    assert "memory" in raw_ctx, "Memory should contribute"
    print("    ✓ Memory context found")
    
    assert "available_tools" in raw_ctx, "Tools should contribute"
    print("    ✓ Tools context found")
    
    assert "workspace" in raw_ctx, "Workspace should contribute"
    print("    ✓ Workspace context found")
    
    # Check custom components - THIS IS THE KEY TEST!
    assert "analytics" in raw_ctx, "Analytics should be auto-discovered!"
    print("    ✓ Analytics context found (AUTO-DISCOVERED!)")
    
    assert "user_config" in raw_ctx, "Config should be auto-discovered!"
    print("    ✓ Config context found (AUTO-DISCOVERED!)")
    
    print("\n[9] Verifying custom component data...")
    assert raw_ctx["analytics"]["total_page_views"] == 2
    print(f"    ✓ Analytics: {raw_ctx['analytics']['total_page_views']} page views")
    
    assert raw_ctx["analytics"]["total_actions"] == 3
    print(f"    ✓ Analytics: {raw_ctx['analytics']['total_actions']} total actions")
    
    assert raw_ctx["user_config"]["theme"] == "light"
    print(f"    ✓ Config: theme = {raw_ctx['user_config']['theme']}")
    
    assert raw_ctx["user_config"]["language"] == "pt-BR"
    print(f"    ✓ Config: language = {raw_ctx['user_config']['language']}")
    
    print("\n[10] Listing all discovered components...")
    discovered = []
    for attr_name in dir(agent):
        if not attr_name.startswith('_'):
            try:
                component = getattr(agent, attr_name)
                if component is not None and not callable(component):
                    if isinstance(component, IContextProvider):
                        discovered.append((attr_name, type(component).__name__))
            except AttributeError:
                pass
    
    print(f"    ✓ Found {len(discovered)} IContextProvider components:")
    for attr_name, class_name in discovered:
        print(f"      - {attr_name}: {class_name}")
    
    # Cleanup
    shutil.rmtree(temp_dir, ignore_errors=True)
    
    print("\n" + "="*80)
    print("✅ TEST PASSED - Automatic discovery works perfectly!")
    print("="*80)
    print("\n💡 KEY INSIGHT:")
    print("   No hardcoded list needed! Just implement IContextProvider and")
    print("   the component will be automatically discovered and contribute")
    print("   its context to the agent's system prompt.")
    print("="*80 + "\n")
    
    return True


if __name__ == "__main__":
    try:
        success = test_automatic_discovery()
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"\n❌ TEST FAILED: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
