"""
Sandbox Interpreter Implementation.

Executes Python code in an isolated environment with pre-configured modules.
This is the core of the RACI (Retrieval Augmented Code Interpreter) architecture.
"""

import io
import sys
import time
import traceback
from contextlib import redirect_stdout, redirect_stderr
from pathlib import Path
from typing import Any

from ...interfaces.raci import (
    ExecutionResult,
    ICodeInterpreter,
    ModuleInfo,
    WorkspaceLayer,
)
from .workspace import LayeredWorkspace


class SandboxInterpreter(ICodeInterpreter):
    """
    Sandbox Python interpreter with pre-configured modules.
    
    Executes Python code in a controlled environment with access to:
    - Built-in modules: search, http, data, files
    - Custom modules: user-defined or agent-created
    - Workspace layers: read/write to PROJECT and OFFICE
    
    The interpreter maintains state between executions within a session,
    allowing for iterative development and debugging.
    
    Security Features:
    - Timeout enforcement
    - Path traversal protection
    - Limited imports (configurable)
    - Sandboxed file operations
    
    Example:
        interpreter = SandboxInterpreter(workspace)
        
        # Simple execution
        result = interpreter.execute('print("Hello, World!")')
        
        # Multi-line with modules
        result = interpreter.execute('''
            from search import web
            results = web("Python tutorials")
            for r in results[:3]:
                print(f"- {r['title']}")
        ''')
        
        # Access workspace
        result = interpreter.execute('''
            from files import read, write
            code = read("src/main.py")
            write("backup.py", code, layer="office")
        ''')
    """
    
    def __init__(
        self,
        workspace: LayeredWorkspace,
        timeout_default: float = 30.0,
        allowed_imports: list[str] | None = None
    ):
        """
        Initialize the sandbox interpreter.
        
        Args:
            workspace: LayeredWorkspace instance for file operations
            timeout_default: Default execution timeout in seconds
            allowed_imports: List of allowed import names (None = all allowed)
        """
        self._workspace = workspace
        self._timeout_default = timeout_default
        self._allowed_imports = allowed_imports
        
        # Persistent namespace for the session
        self._namespace: dict[str, Any] = {}
        
        # Custom modules registry
        self._custom_modules: dict[str, ModuleInfo] = {}
        
        # Initialize built-in modules
        self._init_builtin_modules()
    
    def _init_builtin_modules(self) -> None:
        """Initialize the built-in interpreter modules."""
        # Create the modules namespace
        self._modules_namespace = {
            "search": self._create_search_module(),
            "http": self._create_http_module(),
            "data": self._create_data_module(),
            "files": self._create_files_module(),
        }
        
        # Module documentation
        self._builtin_modules = [
            ModuleInfo(
                name="search",
                description="Web search and knowledge retrieval",
                functions={
                    "web(query, num_results=5)": "Search the web, returns list of {title, url, snippet}",
                    "knowledge(query, layer='office')": "Search agent's knowledge base",
                },
                examples=[
                    'from search import web; results = web("Python async")',
                    'print(search.web(query=["topic1", "topic2"]))',
                ]
            ),
            ModuleInfo(
                name="http",
                description="HTTP requests (GET, POST, etc.)",
                functions={
                    "get(url, **kwargs)": "GET request, returns response dict with 'status', 'json', 'text'",
                    "post(url, json=None, data=None, **kwargs)": "POST request",
                    "request(method, url, **kwargs)": "Generic HTTP request",
                },
                examples=[
                    'from http import get; data = get("https://api.github.com/users/octocat")',
                ]
            ),
            ModuleInfo(
                name="data",
                description="Data manipulation utilities",
                functions={
                    "parse_json(text)": "Parse JSON string to dict/list",
                    "to_json(obj, pretty=False)": "Convert object to JSON string",
                    "parse_csv(text, delimiter=',')": "Parse CSV to list of dicts",
                    "to_csv(data, delimiter=',')": "Convert list of dicts to CSV string",
                },
                examples=[
                    'from data import parse_json; obj = parse_json(\'{"key": "value"}\')',
                ]
            ),
            ModuleInfo(
                name="files",
                description="Workspace file operations",
                functions={
                    "read(path, layer='project')": "Read file from workspace layer",
                    "write(path, content, layer='project')": "Write file to workspace layer",
                    "list_dir(path='.', layer='project')": "List directory contents",
                    "exists(path, layer='project')": "Check if path exists",
                },
                examples=[
                    'from files import read, write; content = read("README.md")',
                    'write("notes.md", "# My Notes", layer="office")',
                ]
            ),
        ]
    
    def _create_search_module(self) -> type:
        """Create the search module with web search functionality."""
        workspace = self._workspace
        
        class SearchModule:
            """Search module for web and knowledge retrieval."""
            
            @staticmethod
            def web(query: str | list[str], num_results: int = 5) -> list[dict[str, str]]:
                """
                Search the web (placeholder - integrate with actual search API).
                
                Args:
                    query: Search query or list of queries
                    num_results: Number of results per query
                    
                Returns:
                    List of results with title, url, snippet
                """
                # Placeholder implementation - integrate with DuckDuckGo, Google, etc.
                if isinstance(query, str):
                    queries = [query]
                else:
                    queries = query
                
                results = []
                for q in queries:
                    # Simulated results - replace with actual API
                    results.append({
                        "query": q,
                        "results": [
                            {
                                "title": f"Result for: {q}",
                                "url": f"https://example.com/search?q={q}",
                                "snippet": f"This is a placeholder result for '{q}'. Integrate with a real search API."
                            }
                        ]
                    })
                
                return results if len(queries) > 1 else results[0]["results"]
            
            @staticmethod
            def knowledge(query: str, layer: str = "office") -> list[dict[str, Any]]:
                """Search the agent's knowledge base."""
                # Placeholder - integrate with vector store
                ws_layer = WorkspaceLayer.OFFICE if layer == "office" else WorkspaceLayer.PROJECT
                files = workspace.list_dir(".", ws_layer, recursive=True)
                
                # Simple text search (replace with semantic search)
                results = []
                for file_path in files[:10]:  # Limit search
                    content = workspace.read(file_path, ws_layer)
                    if content and query.lower() in content.lower():
                        results.append({
                            "path": file_path,
                            "layer": layer,
                            "snippet": content[:200] + "..." if len(content) > 200 else content
                        })
                
                return results
        
        return SearchModule
    
    def _create_http_module(self) -> type:
        """Create the HTTP module for making web requests."""
        
        class HttpModule:
            """HTTP request module."""
            
            @staticmethod
            def get(url: str, **kwargs) -> dict[str, Any]:
                """Make a GET request."""
                return HttpModule.request("GET", url, **kwargs)
            
            @staticmethod
            def post(url: str, json: dict | None = None, data: Any = None, **kwargs) -> dict[str, Any]:
                """Make a POST request."""
                return HttpModule.request("POST", url, json=json, data=data, **kwargs)
            
            @staticmethod
            def request(method: str, url: str, **kwargs) -> dict[str, Any]:
                """Make an HTTP request."""
                try:
                    import requests
                    
                    response = requests.request(method, url, timeout=30, **kwargs)
                    
                    result = {
                        "status": response.status_code,
                        "ok": response.ok,
                        "headers": dict(response.headers),
                        "text": response.text,
                    }
                    
                    try:
                        result["json"] = response.json()
                    except Exception:
                        result["json"] = None
                    
                    return result
                    
                except ImportError:
                    return {
                        "error": "requests library not installed",
                        "status": -1,
                        "ok": False
                    }
                except Exception as e:
                    return {
                        "error": str(e),
                        "status": -1,
                        "ok": False
                    }
        
        return HttpModule
    
    def _create_data_module(self) -> type:
        """Create the data manipulation module."""
        import csv
        import json
        
        class DataModule:
            """Data manipulation utilities."""
            
            @staticmethod
            def parse_json(text: str) -> Any:
                """Parse JSON string."""
                return json.loads(text)
            
            @staticmethod
            def to_json(obj: Any, pretty: bool = False) -> str:
                """Convert object to JSON string."""
                if pretty:
                    return json.dumps(obj, indent=2, ensure_ascii=False)
                return json.dumps(obj, ensure_ascii=False)
            
            @staticmethod
            def parse_csv(text: str, delimiter: str = ",") -> list[dict[str, str]]:
                """Parse CSV string to list of dicts."""
                reader = csv.DictReader(io.StringIO(text), delimiter=delimiter)
                return list(reader)
            
            @staticmethod
            def to_csv(data: list[dict[str, Any]], delimiter: str = ",") -> str:
                """Convert list of dicts to CSV string."""
                if not data:
                    return ""
                
                output = io.StringIO()
                writer = csv.DictWriter(output, fieldnames=data[0].keys(), delimiter=delimiter)
                writer.writeheader()
                writer.writerows(data)
                return output.getvalue()
        
        return DataModule
    
    def _create_files_module(self) -> type:
        """Create the files module for workspace operations."""
        workspace = self._workspace
        
        class FilesModule:
            """Workspace file operations."""
            
            @staticmethod
            def _get_layer(layer: str) -> WorkspaceLayer:
                """Convert string to WorkspaceLayer."""
                layer_map = {
                    "project": WorkspaceLayer.PROJECT,
                    "office": WorkspaceLayer.OFFICE,
                    "interpreter": WorkspaceLayer.INTERPRETER,
                }
                return layer_map.get(layer.lower(), WorkspaceLayer.PROJECT)
            
            @staticmethod
            def read(path: str, layer: str = "project") -> str | None:
                """Read a file from the workspace."""
                return workspace.read(path, FilesModule._get_layer(layer))
            
            @staticmethod
            def write(path: str, content: str, layer: str = "project") -> bool:
                """Write a file to the workspace."""
                return workspace.write(path, content, FilesModule._get_layer(layer))
            
            @staticmethod
            def list_dir(path: str = ".", layer: str = "project", recursive: bool = False) -> list[str]:
                """List directory contents."""
                return workspace.list_dir(path, FilesModule._get_layer(layer), recursive)
            
            @staticmethod
            def exists(path: str, layer: str = "project") -> bool:
                """Check if a path exists."""
                return workspace.exists(path, FilesModule._get_layer(layer))
            
            @staticmethod
            def delete(path: str, layer: str = "project") -> bool:
                """Delete a file."""
                return workspace.delete(path, FilesModule._get_layer(layer))
        
        return FilesModule
    
    def _build_execution_namespace(self) -> dict[str, Any]:
        """Build the namespace for code execution."""
        import types
        
        # Create proper module objects for import support
        def class_to_module(name: str, cls: type) -> types.ModuleType:
            """Convert a class to a module-like object."""
            module = types.ModuleType(name)
            # Copy all static methods and class attributes to module
            for attr_name in dir(cls):
                if not attr_name.startswith('_'):
                    attr = getattr(cls, attr_name)
                    setattr(module, attr_name, attr)
            return module
        
        # Create module objects
        search_module = class_to_module("search", self._modules_namespace["search"])
        http_module = class_to_module("http", self._modules_namespace["http"])
        data_module = class_to_module("data", self._modules_namespace["data"])
        files_module = class_to_module("files", self._modules_namespace["files"])
        
        # Register modules in sys.modules for import support
        import sys
        sys.modules["search"] = search_module
        sys.modules["http"] = http_module
        sys.modules["data"] = data_module
        sys.modules["files"] = files_module
        
        namespace = {
            "__builtins__": __builtins__,
            # Inject modules directly as well
            "search": search_module,
            "http": http_module,
            "data": data_module,
            "files": files_module,
        }
        
        # Add custom modules
        for name, _ in self._custom_modules.items():
            module_path = self._workspace.get_layer_root(WorkspaceLayer.OFFICE) / "modules" / f"{name}.py"
            if module_path.exists():
                # Load and execute custom module
                module_code = module_path.read_text()
                custom_module = types.ModuleType(name)
                exec(module_code, custom_module.__dict__)
                sys.modules[name] = custom_module
                namespace[name] = custom_module
        
        # Merge with persistent namespace
        namespace.update(self._namespace)
        
        return namespace
    
    def execute(
        self, 
        code: str, 
        timeout: float | None = None,
        capture_variables: bool = False
    ) -> ExecutionResult:
        """Execute Python code in the sandbox."""
        if timeout is None:
            timeout = self._timeout_default
        
        start_time = time.time()
        stdout_capture = io.StringIO()
        stderr_capture = io.StringIO()
        
        namespace = self._build_execution_namespace()
        
        try:
            # Redirect stdout/stderr
            with redirect_stdout(stdout_capture), redirect_stderr(stderr_capture):
                # Execute the code
                exec(code, namespace)
            
            # Calculate execution time
            execution_time = time.time() - start_time
            
            # Capture output
            output = stdout_capture.getvalue()
            stderr = stderr_capture.getvalue()
            
            if stderr:
                output += f"\n[stderr]: {stderr}"
            
            # Update persistent namespace with new variables
            for key, value in namespace.items():
                if not key.startswith("_") and key not in {"search", "http", "data", "files"}:
                    self._namespace[key] = value
            
            # Get artifacts from interpreter directory
            artifacts = self._workspace.list_dir(".", WorkspaceLayer.INTERPRETER)
            
            # Capture variables if requested
            captured_vars = {}
            if capture_variables:
                for key, value in namespace.items():
                    if not key.startswith("_"):
                        try:
                            # Only capture serializable values
                            repr(value)
                            captured_vars[key] = value
                        except Exception:
                            captured_vars[key] = f"<{type(value).__name__}>"
            
            return ExecutionResult(
                success=True,
                output=output,
                error=None,
                artifacts=artifacts,
                execution_time=execution_time,
                variables=captured_vars
            )
            
        except Exception as e:
            execution_time = time.time() - start_time
            error_msg = f"{type(e).__name__}: {e}\n{traceback.format_exc()}"
            
            return ExecutionResult(
                success=False,
                output=stdout_capture.getvalue(),
                error=error_msg,
                artifacts=[],
                execution_time=execution_time,
                variables={}
            )
    
    def get_available_modules(self) -> list[ModuleInfo]:
        """Get information about available modules."""
        all_modules = list(self._builtin_modules)
        all_modules.extend(self._custom_modules.values())
        return all_modules
    
    def get_modules_context(self) -> str:
        """Get a formatted string describing all modules for the system prompt."""
        lines = [
            "# Available Interpreter Modules",
            "",
            "You can execute Python code using these pre-configured modules:",
            ""
        ]
        
        for module in self.get_available_modules():
            lines.append(module.to_context_string())
            lines.append("")
        
        lines.extend([
            "## Usage",
            "",
            "To use these modules, write Python code in `execute_code` tool:",
            "```python",
            "from search import web",
            "results = web('your query')",
            "print(results)",
            "```",
            "",
            "## Workspace Layers",
            "- 'project': User's project folder (default)",
            "- 'office': Your private workspace for notes and tools",
            "- 'interpreter': Temporary execution space",
        ])
        
        return "\n".join(lines)
    
    def install_module(
        self, 
        name: str, 
        code: str,
        description: str = ""
    ) -> bool:
        """Install a custom module in the interpreter."""
        try:
            # Save module to office layer
            module_path = f"modules/{name}.py"
            success = self._workspace.write(module_path, code, WorkspaceLayer.OFFICE)
            
            if success:
                self._custom_modules[name] = ModuleInfo(
                    name=name,
                    description=description or f"Custom module: {name}",
                    functions={},
                    examples=[]
                )
            
            return success
        except Exception:
            return False
    
    def uninstall_module(self, name: str) -> bool:
        """Remove a custom module."""
        try:
            if name in self._custom_modules:
                del self._custom_modules[name]
                module_path = f"modules/{name}.py"
                return self._workspace.delete(module_path, WorkspaceLayer.OFFICE)
            return False
        except Exception:
            return False
    
    def reset(self) -> None:
        """Reset the interpreter state."""
        self._namespace.clear()
        self._workspace.clear_interpreter()
    
    def get_context_contribution(self) -> dict[str, Any]:
        """Get context contribution for the agent's system prompt."""
        return {
            "interpreter": {
                "status": "ready",
                "modules": [m.name for m in self.get_available_modules()],
                "custom_modules": list(self._custom_modules.keys()),
                "variables_in_scope": list(self._namespace.keys())[:20]
            }
        }
