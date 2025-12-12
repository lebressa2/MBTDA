"""
Tests for RACI (Retrieval Augmented Code Interpreter) components.

Tests the modular architecture where:
- LayeredWorkspaceManager implements IWorkspaceManager (drop-in replacement)
- RACIToolManager implements IToolManager (drop-in replacement)
- SandboxInterpreter is a new component
"""

import tempfile
from pathlib import Path

import pytest


class TestWorkspaceLayer:
    """Tests for WorkspaceLayer enum."""
    
    def test_workspace_layers_exist(self):
        """Test that all workspace layers are defined."""
        from src.components.workspace import WorkspaceLayer
        
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


class TestLayeredWorkspaceManager:
    """Tests for LayeredWorkspaceManager implementation."""
    
    @pytest.fixture
    def workspace(self, tmp_path):
        """Create a temporary workspace for testing."""
        from src.components.workspace import LayeredWorkspaceManager
        
        project_dir = tmp_path / "project"
        project_dir.mkdir()
        
        office_dir = tmp_path / "office"
        
        return LayeredWorkspaceManager(
            base_path=str(project_dir),
            agent_id="test_agent",
            office_base=office_dir
        )
    
    def test_layer_roots(self, workspace):
        """Test that layer roots are correctly set."""
        from src.components.workspace import WorkspaceLayer
        
        assert workspace.get_layer_root(WorkspaceLayer.PROJECT).exists()
        assert workspace.get_layer_root(WorkspaceLayer.OFFICE).exists()
        assert workspace.get_layer_root(WorkspaceLayer.INTERPRETER).exists()
    
    def test_write_and_read_project(self, workspace):
        """Test writing and reading from project layer."""
        from src.components.workspace import WorkspaceLayer
        
        # Write (using IWorkspaceManager interface)
        success = workspace.create_file("test.txt", "Hello, Project!", WorkspaceLayer.PROJECT)
        assert success is True
        
        # Read
        content = workspace.read_file("test.txt", WorkspaceLayer.PROJECT)
        assert content == "Hello, Project!"
    
    def test_write_and_read_office(self, workspace):
        """Test writing and reading from office layer."""
        from src.components.workspace import WorkspaceLayer
        
        success = workspace.create_file("notes.md", "# Notes", WorkspaceLayer.OFFICE)
        assert success is True
        
        content = workspace.read_file("notes.md", WorkspaceLayer.OFFICE)
        assert content == "# Notes"
    
    def test_write_and_read_interpreter(self, workspace):
        """Test writing and reading from interpreter layer."""
        from src.components.workspace import WorkspaceLayer
        
        success = workspace.create_file("temp.txt", "Temporary", WorkspaceLayer.INTERPRETER)
        assert success is True
        
        content = workspace.read_file("temp.txt", WorkspaceLayer.INTERPRETER)
        assert content == "Temporary"
    
    def test_list_dir(self, workspace):
        """Test directory listing."""
        from src.components.workspace import WorkspaceLayer
        
        workspace.create_file("file1.txt", "1", WorkspaceLayer.PROJECT)
        workspace.create_file("file2.txt", "2", WorkspaceLayer.PROJECT)
        
        files = workspace.list_directory(".", WorkspaceLayer.PROJECT)
        assert len(files) >= 2
    
    def test_exists(self, workspace):
        """Test file existence check."""
        from src.components.workspace import WorkspaceLayer
        
        workspace.create_file("exists.txt", "I exist", WorkspaceLayer.PROJECT)
        
        assert workspace.file_exists("exists.txt", WorkspaceLayer.PROJECT) is True
        assert workspace.file_exists("not_exists.txt", WorkspaceLayer.PROJECT) is False
    
    def test_delete(self, workspace):
        """Test file deletion."""
        from src.components.workspace import WorkspaceLayer
        
        workspace.create_file("to_delete.txt", "Delete me", WorkspaceLayer.PROJECT)
        assert workspace.file_exists("to_delete.txt", WorkspaceLayer.PROJECT) is True
        
        success = workspace.delete_file("to_delete.txt", WorkspaceLayer.PROJECT)
        assert success is True
        assert workspace.file_exists("to_delete.txt", WorkspaceLayer.PROJECT) is False
    
    def test_copy_between_layers(self, workspace):
        """Test copying files between layers."""
        from src.components.workspace import WorkspaceLayer
        
        # Write to interpreter
        workspace.create_file("output.txt", "Result data", WorkspaceLayer.INTERPRETER)
        
        # Copy to project
        success = workspace.copy_between_layers(
            "output.txt", WorkspaceLayer.INTERPRETER,
            "data/output.txt", WorkspaceLayer.PROJECT
        )
        assert success is True
        
        # Verify copy
        content = workspace.read_file("data/output.txt", WorkspaceLayer.PROJECT)
        assert content == "Result data"
    
    def test_path_security(self, workspace):
        """Test that path traversal is prevented."""
        # Path traversal should raise or return None
        result = workspace.read_file("../../../etc/passwd")
        assert result is None
    
    def test_iworkspace_interface_compatibility(self, workspace):
        """Test that LayeredWorkspaceManager works as IWorkspaceManager."""
        # Default layer is PROJECT - should work like regular WorkspaceManager
        success = workspace.create_file("test.txt", "content")
        assert success is True
        
        content = workspace.read_file("test.txt")
        assert content == "content"
        
        files = workspace.list_directory(".")
        assert "test.txt" in files


class TestSandboxInterpreter:
    """Tests for SandboxInterpreter implementation."""
    
    @pytest.fixture
    def interpreter(self, tmp_path):
        """Create a temporary interpreter for testing."""
        from src.components.workspace import WorkspaceManager
        from src.components.interpreter import SandboxInterpreter
        
        workspace = WorkspaceManager(str(tmp_path / "project"))
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
write("test_file.txt", "Hello from interpreter")
content = read("test_file.txt")
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
        from src.components.workspace import WorkspaceManager
        from src.components.interpreter import SandboxInterpreter
        from src.components.tools import RACIToolManager
        
        workspace = WorkspaceManager(str(tmp_path / "project"))
        (tmp_path / "project").mkdir(exist_ok=True)
        
        interpreter = SandboxInterpreter(workspace)
        return RACIToolManager(interpreter, workspace)
    
    def test_get_tools_minimal(self, tool_manager):
        """Test that tool manager returns minimal tools."""
        tools = tool_manager.get_tools()
        
        # Should have exactly 3 tools
        assert len(tools) == 3
        
        # Check tool names
        tool_names = [getattr(t, 'name', str(t)) for t in tools]
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
        
        assert "available_tools" in context
        assert "tool_mode" in context
        assert context["tool_mode"] == "raci_interpreter"
    
    def test_unknown_tool(self, tool_manager):
        """Test handling of unknown tool."""
        with pytest.raises(ValueError, match="not found"):
            tool_manager.execute_tool("unknown_tool")
    
    def test_itool_manager_interface_compatibility(self, tool_manager):
        """Test that RACIToolManager works as IToolManager."""
        # get_tools should work
        tools = tool_manager.get_tools()
        assert len(tools) > 0
        
        # get_tool_descriptions should work
        descriptions = tool_manager.get_tool_descriptions()
        assert "execute_code" in descriptions
        
        # Can register additional tools
        class CustomTool:
            name = "custom_tool"
            description = "A custom tool"
            def invoke(self, args):
                return {"result": "custom"}
        
        tool_manager.register_tool("custom", CustomTool())
        tools = tool_manager.get_tools()
        assert len(tools) == 4  # 3 RACI + 1 custom


class TestIntegration:
    """Integration tests for RACI components."""
    
    def test_full_workflow(self, tmp_path):
        """Test a complete RACI workflow."""
        from src.components.workspace import WorkspaceManager
        from src.components.interpreter import SandboxInterpreter
        from src.components.tools import RACIToolManager
        
        # Setup
        project_root = tmp_path / "project"
        project_root.mkdir()
        (project_root / "data.json").write_text('{"items": [1, 2, 3]}')
        
        workspace = WorkspaceManager(str(project_root))
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
    
    def test_drop_in_replacement_workspace(self, tmp_path):
        """Test LayeredWorkspaceManager as drop-in for WorkspaceManager."""
        from src.components.workspace import WorkspaceManager, LayeredWorkspaceManager
        
        # Both should work the same for basic operations
        simple = WorkspaceManager(str(tmp_path / "simple"))
        layered = LayeredWorkspaceManager(str(tmp_path / "layered"))
        
        # Same interface
        simple.create_file("test.txt", "hello")
        layered.create_file("test.txt", "hello")
        
        assert simple.read_file("test.txt") == layered.read_file("test.txt")
    
    def test_drop_in_replacement_tools(self, tmp_path):
        """Test RACIToolManager as drop-in for ToolManager."""
        from src.components.tools import ToolManager, RACIToolManager
        from src.components.workspace import WorkspaceManager
        from src.components.interpreter import SandboxInterpreter
        
        # Both implement IToolManager
        traditional = ToolManager()
        
        workspace = WorkspaceManager(str(tmp_path))
        interpreter = SandboxInterpreter(workspace)
        raci = RACIToolManager(interpreter, workspace)
        
        # Both have get_tools
        assert hasattr(traditional, 'get_tools')
        assert hasattr(raci, 'get_tools')
        
        # Both have get_tool_descriptions
        assert hasattr(traditional, 'get_tool_descriptions')
        assert hasattr(raci, 'get_tool_descriptions')


class TestSecurityFeatures:
    """Tests for security features in LayeredWorkspaceManager."""
    
    @pytest.fixture
    def workspace(self, tmp_path):
        """Create a temporary workspace for testing."""
        from src.components.workspace import LayeredWorkspaceManager
        
        project_dir = tmp_path / "project"
        project_dir.mkdir()
        
        office_dir = tmp_path / "office"
        
        return LayeredWorkspaceManager(
            base_path=str(project_dir),
            agent_id="test_agent",
            office_base=office_dir
        )
    
    def test_security_error_exists(self):
        """Test that SecurityError is exported."""
        from src.components.workspace import SecurityError
        
        assert SecurityError is not None
        
        # Can be raised
        with pytest.raises(SecurityError):
            raise SecurityError("Test error")
    
    def test_enforce_layer_3_path_traversal_blocked(self, workspace):
        """Test that path traversal is blocked."""
        from src.components.workspace import SecurityError
        
        # Path with .. should raise SecurityError
        with pytest.raises(SecurityError):
            workspace.enforce_layer_3_operation("test", "../../etc/passwd")
        
        with pytest.raises(SecurityError):
            workspace.enforce_layer_3_operation("test", "../secret")
    
    def test_enforce_layer_3_absolute_path_blocked(self, workspace):
        """Test that absolute paths are blocked."""
        from src.components.workspace import SecurityError
        
        # Absolute path should raise SecurityError
        with pytest.raises(SecurityError):
            workspace.enforce_layer_3_operation("test", "/etc/passwd")
    
    def test_enforce_layer_3_valid_path(self, workspace):
        """Test that valid paths work correctly."""
        from src.components.workspace import WorkspaceLayer
        
        # Valid relative path should return resolved path in INTERPRETER layer
        result = workspace.enforce_layer_3_operation("test", "data.json")
        
        # Should be within INTERPRETER layer
        interpreter_root = workspace.get_layer_root(WorkspaceLayer.INTERPRETER)
        assert result.parent == interpreter_root
        assert result.name == "data.json"
    
    def test_promote_file_to_project(self, workspace):
        """Test file promotion from INTERPRETER to PROJECT."""
        from src.components.workspace import WorkspaceLayer
        
        # Create file in INTERPRETER
        workspace.create_file("result.txt", "Test result", WorkspaceLayer.INTERPRETER)
        
        # Promote to PROJECT
        success = workspace.promote_file_to_project("result.txt", "output/result.txt")
        
        assert success is True
        assert workspace.file_exists("output/result.txt", WorkspaceLayer.PROJECT)
        
        # Content should match
        content = workspace.read_file("output/result.txt", WorkspaceLayer.PROJECT)
        assert content == "Test result"
    
    def test_promote_nonexistent_file(self, workspace):
        """Test promoting a file that doesn't exist."""
        success = workspace.promote_file_to_project("nonexistent.txt", "output.txt")
        assert success is False
    
    def test_audit_log_with_operation_type(self, workspace):
        """Test that audit log includes operation_type and security_level."""
        from src.components.workspace import WorkspaceLayer
        
        # Perform an operation
        workspace.create_file("test.txt", "content", WorkspaceLayer.INTERPRETER)
        
        # Check audit log
        log = workspace.get_audit_log()
        assert len(log) > 0
        
        last_entry = log[-1]
        assert "operation_type" in last_entry
        assert "security_level" in last_entry
        assert last_entry["security_level"] == "high"  # INTERPRETER layer


class TestRACILayerIntegration:
    """Tests for RACI integration with layered workspace."""
    
    @pytest.fixture
    def raci_with_layered_workspace(self, tmp_path):
        """Create RACI with LayeredWorkspaceManager."""
        from src.components.workspace import LayeredWorkspaceManager
        from src.components.interpreter import SandboxInterpreter
        from src.components.tools import RACIToolManager
        
        project_dir = tmp_path / "project"
        project_dir.mkdir()
        
        workspace = LayeredWorkspaceManager(
            base_path=str(project_dir),
            agent_id="test_agent",
            office_base=tmp_path / "office"
        )
        
        interpreter = SandboxInterpreter(workspace)
        tools = RACIToolManager(interpreter, workspace)
        
        return tools, workspace
    
    def test_execute_code_returns_layer(self, raci_with_layered_workspace):
        """Test that execute_code returns layer information."""
        tools, _ = raci_with_layered_workspace
        
        result = tools.execute_tool("execute_code", code="print('hello')")
        
        assert "layer" in result
        assert result["layer"] == "INTERPRETER"
    
    def test_write_file_uses_interpreter_layer(self, raci_with_layered_workspace):
        """Test that write_file uses INTERPRETER layer."""
        from src.components.workspace import WorkspaceLayer
        
        tools, workspace = raci_with_layered_workspace
        
        result = tools.execute_tool("write_file", path="output.txt", content="test data")
        
        assert result["success"] is True
        assert result["layer"] == "INTERPRETER"
        
        # File should exist in INTERPRETER layer
        assert workspace.file_exists("output.txt", WorkspaceLayer.INTERPRETER)
        
        # File should NOT exist in PROJECT layer (isolated)
        assert not workspace.file_exists("output.txt", WorkspaceLayer.PROJECT)
    
    def test_read_file_uses_interpreter_layer(self, raci_with_layered_workspace):
        """Test that read_file uses INTERPRETER layer."""
        from src.components.workspace import WorkspaceLayer
        
        tools, workspace = raci_with_layered_workspace
        
        # Create file in INTERPRETER layer
        workspace.create_file("data.txt", "secret data", WorkspaceLayer.INTERPRETER)
        
        result = tools.execute_tool("read_file", path="data.txt")
        
        assert result["success"] is True
        assert result["content"] == "secret data"
        assert result["layer"] == "INTERPRETER"
    
    def test_path_traversal_blocked_in_raci(self, raci_with_layered_workspace):
        """Test that path traversal is blocked in RACI operations."""
        tools, _ = raci_with_layered_workspace
        
        # Attempt path traversal
        result = tools.execute_tool("read_file", path="../../etc/passwd")
        
        assert result["success"] is False
        assert "error" in result


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

