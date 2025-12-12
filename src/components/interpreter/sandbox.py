"""
Sandbox Interpreter Component for the Agent Framework.

Provides a Python code interpreter that executes in an isolated environment
with pre-configured modules (search, http, data, files).

This is a NEW component that requires its own interface (ICodeInterpreter).
It can be used with any IWorkspaceManager implementation.
"""

import io
import sys
import time
import traceback
import types
from contextlib import redirect_stdout, redirect_stderr
from pathlib import Path
from typing import Any

from ...interfaces.raci import ExecutionResult, ModuleInfo
from ...interfaces.base import IWorkspaceManager, IContextProvider


class SandboxInterpreter(IContextProvider):
    """
    Sandbox Python interpreter with pre-configured modules.
    
    Executes Python code in a controlled environment with access to:
    - Built-in modules: search, http, data, files
    - Custom modules: user-defined or agent-created
    - Workspace: read/write via IWorkspaceManager
    
    The interpreter maintains state between executions within a session,
    allowing for iterative development and debugging.
    
    Example:
        from src.components.interpreter import SandboxInterpreter
        from src.components.workspace import WorkspaceManager
        
        workspace = WorkspaceManager("/path/to/project")
        interpreter = SandboxInterpreter(workspace)
        
        # Simple execution
        result = interpreter.execute('print("Hello, World!")')
        
        # With modules
        result = interpreter.execute('''
            from search import web
            results = web("Python tutorials")
            print(results)
        ''')
    """
    
    # Flag for automatic context injection
    inject_context: bool = True
    
    def __init__(
        self,
        workspace: IWorkspaceManager,
        timeout_default: float = 30.0,
        allowed_imports: list[str] | None = None,
        inject_context: bool = True
    ):
        """
        Initialize the sandbox interpreter.
        
        Args:
            workspace: Any IWorkspaceManager implementation
            timeout_default: Default execution timeout in seconds
            allowed_imports: List of allowed import names (None = all allowed)
            inject_context: Whether to contribute context to system prompt
        """
        self._workspace = workspace
        self._timeout_default = timeout_default
        self._allowed_imports = allowed_imports
        self.inject_context = inject_context
        
        # Persistent namespace for the session
        self._namespace: dict[str, Any] = {}
        
        # Custom modules registry
        self._custom_modules: dict[str, ModuleInfo] = {}
        
        # Initialize built-in modules
        self._init_builtin_modules()
    
    def _init_builtin_modules(self) -> None:
        """Initialize the built-in interpreter modules."""
        # Create the modules namespace (classes that will become modules)
        self._modules_namespace = {
            "search": self._create_search_module(),
            "http": self._create_http_module(),
            "data": self._create_data_module(),
            "files": self._create_files_module(),
            "weather": self._create_weather_module(),
        }
        
        # Module documentation
        self._builtin_modules = [
            ModuleInfo(
                name="search",
                description="Web search and knowledge retrieval",
                functions={
                    "web(query, num_results=5)": "Search the web, returns list of {title, url, snippet}",
                    "knowledge(query)": "Search agent's knowledge base",
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
                    "get(url, **kwargs)": "GET request, returns response dict",
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
                    "read(path, layer=None)": "Read file. Optional layer: 'project', 'office', 'interpreter'",
                    "write(path, content, layer='project')": "Write file. Default: project (or interpreter if enforced)",
                    "move(src, s_layer, dest, d_layer, copy=False)": "Move/Copy between layers",
                    "list_dir(path='.', layer='project')": "List directory contents",
                    "exists(path)": "Check if path exists",
                },
                examples=[
                    'from files import read, write; content = read("README.md")',
                    'write("notes.md", "# My Notes", layer="office")',
                    'from files import move; move("output.json", "interpreter", "data/output.json", "project", copy=True)',
                ]
            ),
            ModuleInfo(
                name="weather",
                description="Weather data (mock)",
                functions={
                    "get(location)": "Get current weather for location, returns {temp, condition, humidity}",
                    "forecast(location, days=3)": "Get weather forecast",
                },
                examples=[
                    'from weather import get; w = get("Tokyo"); print(f"{w[\"temp\"]}°C")',
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
                # Placeholder - integrate with DuckDuckGo, Tavily, etc.
                if isinstance(query, str):
                    queries = [query]
                else:
                    queries = query
                
                results = []
                for q in queries:
                    results.append({
                        "query": q,
                        "results": [
                            {
                                "title": f"Result for: {q}",
                                "url": f"https://example.com/search?q={q}",
                                "snippet": f"Placeholder result for '{q}'. Integrate with a real search API."
                            }
                        ]
                    })
                
                return results if len(queries) > 1 else results[0]["results"]
            
            @staticmethod
            def knowledge(query: str) -> list[dict[str, Any]]:
                """Search the agent's workspace for relevant files."""
                files = workspace.list_directory(".")
                
                # Simple text search (replace with semantic search)
                results = []
                for file_path in files[:10]:
                    content = workspace.read_file(file_path)
                    if content and query.lower() in content.lower():
                        results.append({
                            "path": file_path,
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
                    return {"error": "requests library not installed", "status": -1, "ok": False}
                except Exception as e:
                    return {"error": str(e), "status": -1, "ok": False}
        
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
            def read(path: str, layer: str | None = None) -> str | None:
                """Read a file from the workspace (optional: specify layer)."""
                if layer and hasattr(workspace, 'read_file_from_layer'):
                    from ..workspace.layered import WorkspaceLayer
                    try:
                        return workspace.read_file_from_layer(path, WorkspaceLayer(layer.lower()))
                    except (ValueError, AttributeError):
                        pass
                return workspace.read_file(path)
            
            @staticmethod
            def write(path: str, content: str, layer: str | None = None) -> bool:
                """Write a file to the workspace (optional: specifying layer)."""
                if layer and hasattr(workspace, 'write_file_to_layer'):
                    from ..workspace.layered import WorkspaceLayer
                    try:
                         return workspace.write_file_to_layer(path, content, WorkspaceLayer(layer.lower()))
                    except (ValueError, AttributeError):
                         pass
                
                # Check for enforcement if no layer specified (default behavior)
                if hasattr(workspace, 'enforce_layer_3_operation'):
                     try:
                         safe_path = workspace.enforce_layer_3_operation("write_file", path)
                         safe_path.parent.mkdir(parents=True, exist_ok=True)
                         safe_path.write_text(content, encoding='utf-8')
                         return True
                     except Exception:
                         return False

                return workspace.create_file(path, content)
            
            @staticmethod
            def move(source: str, s_layer: str, dest: str, d_layer: str, copy: bool = False) -> bool:
                """Move or copy files between layers."""
                if not hasattr(workspace, 'move_between_layers'):
                    return False
                
                from ..workspace.layered import WorkspaceLayer
                try:
                    return workspace.move_between_layers(
                        source, WorkspaceLayer(s_layer.lower()),
                        dest, WorkspaceLayer(d_layer.lower()),
                        copy_only=copy
                    )
                except (ValueError, AttributeError):
                    return False

            @staticmethod
            def list_dir(path: str = ".", layer: str | None = None) -> list[str]:
                """List directory contents."""
                if layer and hasattr(workspace, 'list_directory'):
                     from ..workspace.layered import WorkspaceLayer
                     try:
                         return workspace.list_directory(path, WorkspaceLayer(layer.lower()))
                     except (ValueError, AttributeError):
                         pass
                return workspace.list_directory(path)
            
            @staticmethod
            def exists(path: str) -> bool:
                """Check if a path exists."""
                return workspace.file_exists(path)
            
            @staticmethod
            def delete(path: str) -> bool:
                """Delete a file."""
                return workspace.delete_file(path)
        
        return FilesModule
    
    def _create_weather_module(self) -> type:
        """Create the weather module with mock weather data."""
        import random
        
        class WeatherModule:
            """Weather data module (mock implementation)."""
            
            @staticmethod
            def get(location: str) -> dict:
                """Get current weather for a location (mock data)."""
                # Mock weather data
                conditions = ["Sunny", "Cloudy", "Rainy", "Partly Cloudy", "Windy"]
                return {
                    "location": location,
                    "temp": random.randint(10, 30),
                    "condition": random.choice(conditions),
                    "humidity": random.randint(40, 90),
                    "wind_speed": random.randint(5, 25),
                }
            
            @staticmethod
            def forecast(location: str, days: int = 3) -> list[dict]:
                """Get weather forecast for upcoming days (mock data)."""
                conditions = ["Sunny", "Cloudy", "Rainy", "Partly Cloudy"]
                forecast_data = []
                for day in range(1, days + 1):
                    forecast_data.append({
                        "day": day,
                        "location": location,
                        "temp_high": random.randint(20, 35),
                        "temp_low": random.randint(10, 20),
                        "condition": random.choice(conditions),
                    })
                return forecast_data
        
        return WeatherModule
    
    def _build_execution_namespace(self) -> dict[str, Any]:
        """Build the namespace for code execution."""
        # Create proper module objects for import support
        def class_to_module(name: str, cls: type) -> types.ModuleType:
            """Convert a class to a module-like object."""
            module = types.ModuleType(name)
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
        sys.modules["search"] = search_module
        sys.modules["http"] = http_module
        sys.modules["data"] = data_module
        sys.modules["files"] = files_module
        
        namespace = {
            "__builtins__": __builtins__,
            "search": search_module,
            "http": http_module,
            "data": data_module,
            "files": files_module,
        }
        
        # Add custom modules
        for name, _ in self._custom_modules.items():
            module_path = Path.home() / ".agent" / "modules" / f"{name}.py"
            if module_path.exists():
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
        """
        Execute Python code in the sandbox.
        
        Args:
            code: Python code to execute
            timeout: Maximum execution time in seconds
            capture_variables: Whether to capture variables after execution
            
        Returns:
            ExecutionResult with output, errors, and artifacts
        """
        if timeout is None:
            timeout = self._timeout_default
        
        start_time = time.time()
        stdout_capture = io.StringIO()
        stderr_capture = io.StringIO()
        
        namespace = self._build_execution_namespace()
        
        try:
            with redirect_stdout(stdout_capture), redirect_stderr(stderr_capture):
                exec(code, namespace)
            
            execution_time = time.time() - start_time
            output = stdout_capture.getvalue()
            stderr = stderr_capture.getvalue()
            
            if stderr:
                output += f"\n[stderr]: {stderr}"
            
            # Update persistent namespace
            for key, value in namespace.items():
                if not key.startswith("_") and key not in {"search", "http", "data", "files"}:
                    self._namespace[key] = value
            
            # Capture variables if requested
            captured_vars = {}
            if capture_variables:
                for key, value in namespace.items():
                    if not key.startswith("_"):
                        try:
                            repr(value)
                            captured_vars[key] = value
                        except Exception:
                            captured_vars[key] = f"<{type(value).__name__}>"
            
            return ExecutionResult(
                success=True,
                output=output,
                error=None,
                artifacts=[],
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
            "# Interpreter Modules",
            "",
            "Execute Python code using these pre-configured modules:",
            ""
        ]
        
        for module in self.get_available_modules():
            lines.append(module.to_context_string())
            lines.append("")
        
        lines.extend([
            "## Usage",
            "```python",
            "from search import web",
            "results = web('your query')",
            "print(results)",
            "```",
        ])
        
        return "\n".join(lines)
    
    def install_module(self, name: str, code: str, description: str = "") -> bool:
        """Install a custom module."""
        try:
            module_dir = Path.home() / ".agent" / "modules"
            module_dir.mkdir(parents=True, exist_ok=True)
            
            module_path = module_dir / f"{name}.py"
            module_path.write_text(code, encoding="utf-8")
            
            self._custom_modules[name] = ModuleInfo(
                name=name,
                description=description or f"Custom module: {name}",
                functions={},
                examples=[]
            )
            
            return True
        except Exception:
            return False
    
    def uninstall_module(self, name: str) -> bool:
        """Remove a custom module."""
        try:
            if name in self._custom_modules:
                del self._custom_modules[name]
                module_path = Path.home() / ".agent" / "modules" / f"{name}.py"
                if module_path.exists():
                    module_path.unlink()
                return True
            return False
        except Exception:
            return False
    
    def reset(self) -> None:
        """Reset the interpreter state (clear variables)."""
        self._namespace.clear()
    
    def get_context_contribution(self) -> dict[str, Any]:
        """Get context contribution for the agent's system prompt."""
        # Get module documentation
        modules_doc = {}
        for mod in self._builtin_modules:
            # Include functions as description
            funcs = ", ".join(mod.functions.keys()) if mod.functions else ""
            modules_doc[mod.name] = f"{mod.description}. Functions: {funcs}"
        
        return {
            "interpreter": {
                "status": "ready",
                "instruction": (
                    "Use execute_code tool to run Python code. "
                    "Import modules directly (from weather import get). "
                    "Always use print() to show results."
                ),
                "modules": modules_doc,
                "custom_modules": list(self._custom_modules.keys()),
            }
        }
