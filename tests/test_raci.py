"""
Tests for RACI (Retrieval Augmented Code Interpreter) components.
"""

import tempfile
from pathlib import Path

import pytest


class TestWorkspaceLayer:
    """Tests for WorkspaceLayer enum."""
    
    def test_workspace_layers_exist(self):
        """Test that all workspace layers are defined."""
        from src.interfaces.raci import WorkspaceLayer
        
        assert WorkspaceLayer.PROJECT.value == "project"
        assert WorkspaceLayer.OFFICE.value == "office"
        assert WorkspaceLayer.INTERPRETER.value == "interpreter"


class TestExecutionResult:
    """Tests for ExecutionResult dataclass."""
    
    def test_success_result(self):
        """Test successful execution result."""
        from src.interfaces.raci import ExecutionResult
        
        result = ExecutionResult(
            success=True,
            output="Hello, World!",
            execution_time=0.1
        )
        
        assert result.success is True
        assert result.output == "Hello, World!"
        assert result.error is None
        assert str(result) == "Hello, World!"
    
    def test_error_result(self):
        """Test error execution result."""
        from src.interfaces.raci import ExecutionResult
        
        result = ExecutionResult(
            success=False,
            output="",
            error="NameError: name 'x' is not defined"
        )
        
        assert result.success is False
        assert "NameError" in str(result)
    
    def test_to_dict(self):
        """Test conversion to dictionary."""
        from src.interfaces.raci import ExecutionResult
        
        result = ExecutionResult(
            success=True,
            output="test",
            artifacts=["file.txt"],
            execution_time=0.5
        )
        
        d = result.to_dict()
        assert d["success"] is True
        assert d["output"] == "test"
        assert "file.txt" in d["artifacts"]


class TestLayeredWorkspace:
    """Tests for LayeredWorkspace implementation."""
    
    @pytest.fixture
    def workspace(self, tmp_path):
        """Create a temporary workspace for testing."""
        from src.components.raci import LayeredWorkspace
        
        project_dir = tmp_path / "project"
        project_dir.mkdir()
        
        office_dir = tmp_path / "office"
        
        return LayeredWorkspace(
            project_root=project_dir,
            agent_id="test_agent",
            office_base=office_dir
        )
    
    def test_layer_roots(self, workspace):
        """Test that layer roots are correctly set."""
        from src.interfaces.raci import WorkspaceLayer
        
        assert workspace.get_layer_root(WorkspaceLayer.PROJECT).exists()
        assert workspace.get_layer_root(WorkspaceLayer.OFFICE).exists()
        assert workspace.get_layer_root(WorkspaceLayer.INTERPRETER).exists()
    
    def test_write_and_read_project(self, workspace):
        """Test writing and reading from project layer."""
        from src.interfaces.raci import WorkspaceLayer
        
        # Write
        success = workspace.write("test.txt", "Hello, Project!", WorkspaceLayer.PROJECT)
        assert success is True
        
        # Read
        content = workspace.read("test.txt", WorkspaceLayer.PROJECT)
        assert content == "Hello, Project!"
    
    def test_write_and_read_office(self, workspace):
        """Test writing and reading from office layer."""
        from src.interfaces.raci import WorkspaceLayer
        
        success = workspace.write("notes.md", "# Notes", WorkspaceLayer.OFFICE)
        assert success is True
        
        content = workspace.read("notes.md", WorkspaceLayer.OFFICE)
        assert content == "# Notes"
    
    def test_write_and_read_interpreter(self, workspace):
        """Test writing and reading from interpreter layer."""
        from src.interfaces.raci import WorkspaceLayer
        
        success = workspace.write("temp.txt", "Temporary", WorkspaceLayer.INTERPRETER)
        assert success is True
        
        content = workspace.read("temp.txt", WorkspaceLayer.INTERPRETER)
        assert content == "Temporary"
    
    def test_list_dir(self, workspace):
        """Test directory listing."""
        from src.interfaces.raci import WorkspaceLayer
        
        workspace.write("file1.txt", "1", WorkspaceLayer.PROJECT)
        workspace.write("file2.txt", "2", WorkspaceLayer.PROJECT)
        workspace.write("subdir/file3.txt", "3", WorkspaceLayer.PROJECT)
        
        files = workspace.list_dir(".", WorkspaceLayer.PROJECT)
        assert len(files) >= 2
    
    def test_exists(self, workspace):
        """Test file existence check."""
        from src.interfaces.raci import WorkspaceLayer
        
        workspace.write("exists.txt", "I exist", WorkspaceLayer.PROJECT)
        
        assert workspace.exists("exists.txt", WorkspaceLayer.PROJECT) is True
        assert workspace.exists("not_exists.txt", WorkspaceLayer.PROJECT) is False
    
    def test_delete(self, workspace):
        """Test file deletion."""
        from src.interfaces.raci import WorkspaceLayer
        
        workspace.write("to_delete.txt", "Delete me", WorkspaceLayer.PROJECT)
        assert workspace.exists("to_delete.txt", WorkspaceLayer.PROJECT) is True
        
        success = workspace.delete("to_delete.txt", WorkspaceLayer.PROJECT)
        assert success is True
        assert workspace.exists("to_delete.txt", WorkspaceLayer.PROJECT) is False
    
    def test_copy_between_layers(self, workspace):
        """Test copying files between layers."""
        from src.interfaces.raci import WorkspaceLayer
        
        # Write to interpreter
        workspace.write("output.txt", "Result data", WorkspaceLayer.INTERPRETER)
        
        # Copy to project
        success = workspace.copy_between_layers(
            "output.txt", WorkspaceLayer.INTERPRETER,
            "data/output.txt", WorkspaceLayer.PROJECT
        )
        assert success is True
        
        # Verify copy
        content = workspace.read("data/output.txt", WorkspaceLayer.PROJECT)
        assert content == "Result data"
    
    def test_path_security(self, workspace):
        """Test that path traversal is prevented."""
        from src.interfaces.raci import WorkspaceLayer
        
        # Attempt path traversal - should return None (safe behavior)
        result = workspace.read("../../../etc/passwd", WorkspaceLayer.PROJECT)
        assert result is None


class TestSandboxInterpreter:
    """Tests for SandboxInterpreter implementation."""
    
    @pytest.fixture
    def interpreter(self, tmp_path):
        """Create a temporary interpreter for testing."""
        from src.components.raci import LayeredWorkspace, SandboxInterpreter
        
        workspace = LayeredWorkspace(
            project_root=tmp_path / "project",
            agent_id="test",
            office_base=tmp_path / "office"
        )
        (tmp_path / "project").mkdir(exist_ok=True)
        
        return SandboxInterpreter(workspace)
    
    def test_simple_execution(self, interpreter):
        """Test simple code execution."""
        result = interpreter.execute('print("Hello, RACI!")')
        
        assert result.success is True
        assert "Hello, RACI!" in result.output
    
    def test_math_execution(self, interpreter):
        """Test mathematical operations."""
        result = interpreter.execute('''
x = 2 + 2
print(f"2 + 2 = {x}")
''')
        
        assert result.success is True
        assert "4" in result.output
    
    def test_error_handling(self, interpreter):
        """Test error handling in code execution."""
        result = interpreter.execute('undefined_variable')
        
        assert result.success is False
        assert result.error is not None
        assert "NameError" in result.error
    
    def test_module_search_available(self, interpreter):
        """Test that search module is available."""
        result = interpreter.execute('''
from search import web
results = web("test query")
print(type(results))
''')
        
        assert result.success is True
        assert "list" in result.output
    
    def test_module_data_available(self, interpreter):
        """Test that data module is available."""
        result = interpreter.execute('''
from data import parse_json, to_json
obj = parse_json('{"key": "value"}')
print(obj["key"])
''')
        
        assert result.success is True
        assert "value" in result.output
    
    def test_module_files_available(self, interpreter):
        """Test that files module is available."""
        result = interpreter.execute('''
from files import write, read
write("test_file.txt", "Hello from interpreter", layer="interpreter")
content = read("test_file.txt", layer="interpreter")
print(content)
''')
        
        assert result.success is True
        assert "Hello from interpreter" in result.output
    
    def test_state_persistence(self, interpreter):
        """Test that state persists between executions."""
        # First execution - define variable
        result1 = interpreter.execute('my_var = 42')
        assert result1.success is True
        
        # Second execution - use variable
        result2 = interpreter.execute('print(my_var)')
        assert result2.success is True
        assert "42" in result2.output
    
    def test_reset_clears_state(self, interpreter):
        """Test that reset clears interpreter state."""
        # Define variable
        interpreter.execute('persistent_var = 100')
        
        # Reset
        interpreter.reset()
        
        # Variable should not exist
        result = interpreter.execute('print(persistent_var)')
        assert result.success is False
        assert "NameError" in result.error
    
    def test_get_available_modules(self, interpreter):
        """Test listing available modules."""
        modules = interpreter.get_available_modules()
        
        module_names = [m.name for m in modules]
        assert "search" in module_names
        assert "http" in module_names
        assert "data" in module_names
        assert "files" in module_names
    
    def test_get_modules_context(self, interpreter):
        """Test getting modules context for system prompt."""
        context = interpreter.get_modules_context()
        
        assert "search" in context
        assert "http" in context
        assert "web" in context  # Function from search module


class TestRACIToolManager:
    """Tests for RACIToolManager implementation."""
    
    @pytest.fixture
    def tool_manager(self, tmp_path):
        """Create a temporary tool manager for testing."""
        from src.components.raci import LayeredWorkspace, SandboxInterpreter, RACIToolManager
        
        workspace = LayeredWorkspace(
            project_root=tmp_path / "project",
            agent_id="test",
            office_base=tmp_path / "office"
        )
        (tmp_path / "project").mkdir(exist_ok=True)
        
        interpreter = SandboxInterpreter(workspace)
        return RACIToolManager(interpreter, workspace)
    
    def test_get_tools_minimal(self, tool_manager):
        """Test that tool manager returns minimal tools."""
        tools = tool_manager.get_tools()
        
        # Should have exactly 3 tools
        assert len(tools) == 3
        
        # Check tool names
        tool_names = [t["function"]["name"] for t in tools]
        assert "execute_code" in tool_names
        assert "read_file" in tool_names
        assert "write_file" in tool_names
    
    def test_execute_code_tool(self, tool_manager):
        """Test execute_code tool."""
        result = tool_manager.execute_tool(
            "execute_code",
            code='print("Tool execution works!")'
        )
        
        assert result["success"] is True
        assert "Tool execution works!" in result["output"]
    
    def test_read_file_tool(self, tool_manager, tmp_path):
        """Test read_file tool."""
        # Create a file in project
        (tmp_path / "project" / "readme.md").write_text("# README")
        
        result = tool_manager.execute_tool("read_file", path="readme.md")
        
        assert result["success"] is True
        assert result["content"] == "# README"
    
    def test_write_file_tool(self, tool_manager, tmp_path):
        """Test write_file tool."""
        result = tool_manager.execute_tool(
            "write_file",
            path="new_file.txt",
            content="New content"
        )
        
        assert result["success"] is True
        assert (tmp_path / "project" / "new_file.txt").exists()
    
    def test_get_context_contribution(self, tool_manager):
        """Test context contribution for system prompt."""
        context = tool_manager.get_context_contribution()
        
        assert "raci" in context
        assert context["raci"]["mode"] == "code_interpreter"
        assert "execute_code" in context["raci"]["tools"]
    
    def test_unknown_tool(self, tool_manager):
        """Test handling of unknown tool."""
        result = tool_manager.execute_tool("unknown_tool")
        
        assert "error" in result
        assert "Unknown tool" in result["error"]


class TestIntegration:
    """Integration tests for RACI components."""
    
    def test_full_workflow(self, tmp_path):
        """Test a complete RACI workflow."""
        from src.components.raci import LayeredWorkspace, SandboxInterpreter, RACIToolManager
        
        # Setup
        project_root = tmp_path / "project"
        project_root.mkdir()
        (project_root / "data.json").write_text('{"items": [1, 2, 3]}')
        
        workspace = LayeredWorkspace(
            project_root=project_root,
            agent_id="test",
            office_base=tmp_path / "office"
        )
        interpreter = SandboxInterpreter(workspace)
        tools = RACIToolManager(interpreter, workspace)
        
        # Read, process, and write using code
        result = tools.execute_tool("execute_code", code='''
from files import read, write
from data import parse_json, to_json

# Read data
raw = read("data.json")
data = parse_json(raw)

# Process
data["items"].append(4)
data["processed"] = True

# Write result
write("processed.json", to_json(data, pretty=True))
print("Processing complete!")
''')
        
        assert result["success"] is True
        assert "Processing complete!" in result["output"]
        
        # Verify output
        processed = (project_root / "processed.json").read_text()
        assert "processed" in processed
        assert "4" in processed


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
