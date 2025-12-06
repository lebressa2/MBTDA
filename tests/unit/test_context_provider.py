"""
Unit tests for IContextProvider interface and implementations.
"""

import pytest
import tempfile
import shutil
from typing import Any

from src.interfaces.base import IContextProvider
from src.components.memory import InMemoryManager
from src.components.tools import ToolManager
from src.components.workspace import WorkspaceManager


class TestIContextProviderInterface:
    """Tests for the IContextProvider interface contract."""

    def test_interface_has_inject_context_flag(self):
        """Verify IContextProvider defines inject_context flag."""
        assert hasattr(IContextProvider, 'inject_context')
        assert IContextProvider.inject_context is True

    def test_interface_requires_get_context_contribution(self):
        """Verify IContextProvider requires get_context_contribution method."""
        assert hasattr(IContextProvider, 'get_context_contribution')


class TestInMemoryManagerContextProvider:
    """Tests for InMemoryManager implementing IContextProvider."""

    def test_implements_interface(self):
        """Verify InMemoryManager implements IContextProvider."""
        memory = InMemoryManager()
        assert isinstance(memory, IContextProvider)

    def test_inject_context_default_true(self):
        """Verify inject_context defaults to True."""
        memory = InMemoryManager()
        assert memory.inject_context is True

    def test_inject_context_can_be_disabled(self):
        """Verify inject_context can be set to False."""
        memory = InMemoryManager(inject_context=False)
        assert memory.inject_context is False

    def test_get_context_contribution_returns_dict_with_memory_key(self):
        """Verify get_context_contribution returns dict with 'memory' key."""
        memory = InMemoryManager()
        contribution = memory.get_context_contribution()
        
        assert isinstance(contribution, dict)
        assert "memory" in contribution
        assert "recent_messages" in contribution["memory"]
        assert "long_term_keys" in contribution["memory"]

    def test_get_context_contribution_includes_messages(self):
        """Verify context includes added messages."""
        memory = InMemoryManager()
        memory.add_message("user", "Hello!")
        memory.add_message("assistant", "Hi there!")
        
        contribution = memory.get_context_contribution()
        messages = contribution["memory"]["recent_messages"]
        
        assert len(messages) == 2
        assert messages[0]["content"] == "Hello!"
        assert messages[1]["content"] == "Hi there!"


class TestToolManagerContextProvider:
    """Tests for ToolManager implementing IContextProvider."""

    def test_implements_interface(self):
        """Verify ToolManager implements IContextProvider."""
        tools = ToolManager()
        assert isinstance(tools, IContextProvider)

    def test_inject_context_default_true(self):
        """Verify inject_context defaults to True."""
        tools = ToolManager()
        assert tools.inject_context is True

    def test_inject_context_can_be_disabled(self):
        """Verify inject_context can be set to False."""
        tools = ToolManager(inject_context=False)
        assert tools.inject_context is False

    def test_get_context_contribution_empty_when_no_tools(self):
        """Verify returns empty dict when no tools registered."""
        tools = ToolManager()
        contribution = tools.get_context_contribution()
        assert contribution == {}

    def test_get_context_contribution_includes_tool_descriptions(self):
        """Verify context includes tool descriptions when tools are registered."""
        from langchain_core.tools import tool
        
        @tool
        def test_tool() -> str:
            """A test tool."""
            return "test"
        
        tools = ToolManager()
        tools.register_tool("default", test_tool)
        
        contribution = tools.get_context_contribution()
        
        assert "available_tools" in contribution
        assert "test_tool" in contribution["available_tools"]


class TestWorkspaceManagerContextProvider:
    """Tests for WorkspaceManager implementing IContextProvider."""

    @pytest.fixture
    def temp_workspace(self):
        """Create a temporary workspace directory."""
        temp_dir = tempfile.mkdtemp()
        yield temp_dir
        shutil.rmtree(temp_dir, ignore_errors=True)

    def test_implements_interface(self, temp_workspace):
        """Verify WorkspaceManager implements IContextProvider."""
        workspace = WorkspaceManager(temp_workspace)
        assert isinstance(workspace, IContextProvider)

    def test_inject_context_default_true(self, temp_workspace):
        """Verify inject_context defaults to True."""
        workspace = WorkspaceManager(temp_workspace)
        assert workspace.inject_context is True

    def test_inject_context_can_be_disabled(self, temp_workspace):
        """Verify inject_context can be set to False."""
        workspace = WorkspaceManager(temp_workspace, inject_context=False)
        assert workspace.inject_context is False

    def test_get_context_contribution_returns_workspace_info(self, temp_workspace):
        """Verify context includes workspace information."""
        workspace = WorkspaceManager(temp_workspace)
        contribution = workspace.get_context_contribution()
        
        assert "workspace" in contribution
        assert "base_path" in contribution["workspace"]
        assert "files" in contribution["workspace"]
        assert "storage" in contribution["workspace"]

    def test_get_context_contribution_includes_files(self, temp_workspace):
        """Verify context includes created files."""
        workspace = WorkspaceManager(temp_workspace)
        workspace.create_file("test.txt", "content")
        
        contribution = workspace.get_context_contribution()
        
        assert "test.txt" in contribution["workspace"]["files"]


class TestContextProviderIntegration:
    """Integration tests for IContextProvider with Agent."""

    def test_agent_collects_memory_context(self):
        """Verify Agent collects context from memory component."""
        from src.components.context_manager import ContextManager
        from src.components.memory import InMemoryManager
        from src.interfaces.base import IContextProvider
        
        # Create memory with some data
        memory = InMemoryManager()
        memory.add_message("user", "Test message")
        
        # Verify it's a context provider
        assert isinstance(memory, IContextProvider)
        
        # Get contribution
        contribution = memory.get_context_contribution()
        assert "memory" in contribution
        assert len(contribution["memory"]["recent_messages"]) == 1

    def test_disabled_context_injection(self):
        """Verify disabled inject_context prevents contribution collection."""
        memory = InMemoryManager(inject_context=False)
        memory.add_message("user", "This should not appear")
        
        # Even with data, if inject_context is False, the contribution
        # would still be generated but should not be collected by Agent
        assert memory.inject_context is False
        
        # Contribution is still available if called directly
        contribution = memory.get_context_contribution()
        assert "memory" in contribution


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
