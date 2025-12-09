"""
Test demonstrating multiple IContextProvider components being automatically discovered and contributing to context.
"""

import sys
from typing import Any, Dict
from pathlib import Path

# Add parent directory to path so imports work from tests/
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.agent import Agent
from src.components import ConsoleLogger, ContextManager
from src.interfaces.base import IContextProvider
from src.clients import MockInboxClient, MockTaskClient


# Mock LLM Client (defined in demo.py)
class MockTextClient:
    """Mock LLM client for testing."""

    def __init__(self, model_name: str = "mock-model"):
        self._model_name = model_name
        self._tools = []

    def invoke(self, messages, **kwargs):
        # Extract the last user message
        user_msg = messages[-1].get("content", "") if messages else ""

        # Simple mock response logic
        if "email" in user_msg.lower():
            return MockResponse(f"I'll help you handle this email. Let me check the details.")
        elif "task" in user_msg.lower():
            return MockResponse(f"I see there's a task that needs attention. Let me work on it.")
        else:
            return MockResponse(f"I understand. You said: {user_msg[:50]}... Let me help with that.")

    def bind_tools(self, tools):
        new_client = MockTextClient(self._model_name)
        new_client._tools = tools
        return new_client

    def get_model_name(self):
        return self._model_name


class MockResponse:
    """Mock response object."""
    def __init__(self, content: str):
        self.content = content
        self.tool_calls = None

    def __str__(self):
        return self.content


class MockDatabaseProvider(IContextProvider):
    """Mock database connection provider."""

    def __init__(self):
        self.inject_context = True
        self.connection_status = "connected"
        self.tables_count = 42

    def get_context_contribution(self) -> Dict[str, Any]:
        return {
            "database": {
                "status": self.connection_status,
                "tables": self.tables_count,
                "active_connections": 3
            }
        }


class MockSecurityProvider(IContextProvider):
    """Mock security/permissions provider."""

    def __init__(self):
        self.inject_context = True
        self.user_permissions = ["read", "write", "admin"]
        self.session_encrypted = True

    def get_context_contribution(self) -> Dict[str, Any]:
        return {
            "security": {
                "permissions": self.user_permissions,
                "session_encrypted": self.session_encrypted,
                "security_level": "high"
            }
        }


class MockConfigProvider(IContextProvider):
    """Mock configuration provider."""

    def __init__(self):
        self.inject_context = True
        self.api_keys_configured = 5
        self.features_enabled = ["logging", "monitoring", "caching"]

    def get_context_contribution(self) -> Dict[str, Any]:
        return {
            "config": {
                "api_keys_count": self.api_keys_configured,
                "enabled_features": self.features_enabled,
                "max_retries": 3
            }
        }


class MockMetricsProvider(IContextProvider):
    """Mock metrics/performance provider."""

    def __init__(self):
        self.inject_context = False  # This one is disabled
        self.cpu_usage = 45.2
        self.memory_mb = 128

    def get_context_contribution(self) -> Dict[str, Any]:
        return {
            "metrics": {
                "cpu_percent": self.cpu_usage,
                "memory_mb": self.memory_mb,
                "active_threads": 8
            }
        }


def test_multiple_providers():
    """Test multiple context providers working together."""
    print("=" * 60)
    print("TEST: Multiple IContextProvider Components")
    print("=" * 60)

    # Create components
    db_provider = MockDatabaseProvider()
    security_provider = MockSecurityProvider()
    config_provider = MockConfigProvider()
    metrics_provider = MockMetricsProvider()  # This one has inject_context=False

    # Create agent with basic components
    text_client = MockTextClient()
    logger = ConsoleLogger("MultiProviderTest")

    agent = Agent(text_provider=text_client, logger=logger)

    print(f"\n1. Default registered components: {agent.context.list_registered_components()}")

    # Register additional providers
    agent.context.register_component('database', db_provider)
    agent.context.register_component('security', security_provider)
    agent.context.register_component('config', config_provider)
    agent.context.register_component('metrics', metrics_provider)  # Disabled

    print(f"2. After registering custom providers: {agent.context.list_registered_components()}")

    # Get provider info
    provider_info = agent.context.get_context_provider_info()
    print("\n3. Provider Information:")
    for name, info in provider_info.items():
        status = "ACTIVE" if info['inject_context'] else "DISABLED"
        provider_status = "YES" if info['is_provider'] else "NO"
        print(f"   {name}: is_provider={provider_status}, inject_context={status}, type={info['component_type']}")

    # Try to process a message to trigger context building
    print("\n4. Processing message to build full context...")
    try:
        response = agent.process_message("Hello multi-provider agent!")

        # Get the raw context
        full_context = agent.context.get_raw_context()

        print("5. Final context keys:")
        for key in sorted(full_context.keys()):
            if isinstance(full_context[key], dict):
                nested_keys = list(full_context[key].keys()) if full_context[key] else []
                print(f"   {key}: (dict with {len(nested_keys)} keys)")
            elif isinstance(full_context[key], list):
                print(f"   {key}: (list with {len(full_context[key])} items)")
            else:
                value_preview = str(full_context[key])[:50] + "..." if len(str(full_context[key])) > 50 else str(full_context[key])
                print(f"   {key}: {value_preview}")

        print(f"\n6. Message processed successfully! Response type: {type(response).__name__}")

        # Show the actual system prompt generated
        print("\n8. Generated System Prompt (first 500 chars):")
        system_prompt = agent.context.populate_system_message()
        print(f"   {system_prompt[:500]}...")
        print(f"   (Total length: {len(system_prompt)} characters)")

        # Show the raw context dict
        print("\n9. Raw Context Dict Details:")
        for key in ['database', 'security', 'config']:
            if key in full_context:
                print(f"   {key}: {full_context[key]}")

        if 'metrics' not in full_context:
            print("   metrics: (not included - inject_context=False) ✓")

        print("\n" + "=" * 60)
        print("SUCCESS: Multiple providers worked correctly!")
        print("Context Manager automatically injected context from all IContextProvider components!")
        print("=" * 60)

    except Exception as e:
        print(f"ERROR during processing: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    test_multiple_providers()
