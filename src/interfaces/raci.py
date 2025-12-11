"""
RACI - Retrieval Augmented Code Interpreter

This module implements the RACI architecture, which provides a code interpreter
sandbox with pre-configured modules instead of traditional tool schemas.

The RACI approach offers several advantages:
- Minimal context window usage (only 2-3 tools vs dozens)
- Natural composition through Python code
- Infinite flexibility
- Self-learning capabilities (agents can create new abstractions)

Workspace Layers:
- Layer 1 (PROJECT): User's project folder, integrated with git
- Layer 2 (OFFICE): Agent's private workspace for notes and custom tools
- Layer 3 (INTERPRETER): Ephemeral sandbox for code execution
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any


# ==============================================================================
# WORKSPACE LAYERS
# ==============================================================================

class WorkspaceLayer(Enum):
    """
    The three layers of the agent's workspace.
    
    PROJECT: User's project folder (e.g., VSCode workspace, git repo)
             - Read/Write with user confirmation
             - Final output destination
             - Integrated with version control
    
    OFFICE: Agent's private workspace
            - Persistent storage for agent's notes, drafts, custom tools
            - Invisible to PROJECT layer
            - Enables infinite context and self-learning
            - Location: ~/.agent/office/<agent_id>/
    
    INTERPRETER: Ephemeral code execution sandbox
                 - Pre-installed libraries and modules
                 - Nothing persists between executions
                 - Location: temporary directory or container
    """
    PROJECT = "project"
    OFFICE = "office"
    INTERPRETER = "interpreter"


# ==============================================================================
# EXECUTION RESULT
# ==============================================================================

@dataclass
class ExecutionResult:
    """
    Result of code execution in the interpreter.
    
    Attributes:
        success: Whether execution completed without errors
        output: Combined stdout and final expression result
        error: Error message if execution failed
        artifacts: List of files generated (images, CSVs, etc.)
        execution_time: Time taken in seconds
        variables: Dictionary of variables in scope after execution
    """
    success: bool
    output: str
    error: str | None = None
    artifacts: list[str] = field(default_factory=list)
    execution_time: float = 0.0
    variables: dict[str, Any] = field(default_factory=dict)
    
    def __str__(self) -> str:
        if self.success:
            return self.output
        return f"Error: {self.error}"
    
    def to_dict(self) -> dict[str, Any]:
        return {
            "success": self.success,
            "output": self.output,
            "error": self.error,
            "artifacts": self.artifacts,
            "execution_time": self.execution_time
        }


# ==============================================================================
# MODULE INFO
# ==============================================================================

@dataclass
class ModuleInfo:
    """
    Information about an available interpreter module.
    
    Attributes:
        name: Module name (e.g., 'search', 'http')
        description: Brief description of the module
        functions: Dict of function names to their signatures/docstrings
        examples: List of usage examples
    """
    name: str
    description: str
    functions: dict[str, str] = field(default_factory=dict)
    examples: list[str] = field(default_factory=list)
    
    def to_context_string(self) -> str:
        """Generate a concise context string for the agent."""
        lines = [f"## {self.name}", f"{self.description}", ""]
        
        if self.functions:
            lines.append("Functions:")
            for func_name, signature in self.functions.items():
                lines.append(f"  - {func_name}: {signature}")
        
        if self.examples:
            lines.append("")
            lines.append("Examples:")
            for example in self.examples[:2]:  # Limit examples
                lines.append(f"  {example}")
        
        return "\n".join(lines)


# ==============================================================================
# INTERFACES
# ==============================================================================

class ICodeInterpreter(ABC):
    """
    RACI - Retrieval Augmented Code Interpreter Interface.
    
    Executes Python code in an isolated sandbox with pre-configured modules.
    The environment is ephemeral - nothing persists between executions.
    
    Available modules (configurable):
    - search: Web search, knowledge retrieval, academic papers
    - http: Simplified HTTP requests
    - data: Data manipulation (pandas, json, csv)
    - files: Read/write to PROJECT and OFFICE layers
    
    Example:
        result = interpreter.execute('''
            from search import web
            results = web("Python async best practices", num_results=3)
            print(results)
        ''')
    """
    
    @abstractmethod
    def execute(
        self, 
        code: str, 
        timeout: float = 30.0,
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
        pass
    
    @abstractmethod
    def get_available_modules(self) -> list[ModuleInfo]:
        """
        Get information about available modules.
        
        Returns:
            List of ModuleInfo describing available modules
        """
        pass
    
    @abstractmethod
    def get_modules_context(self) -> str:
        """
        Get a formatted string describing all modules for the system prompt.
        
        This is optimized for minimal token usage while providing enough
        information for the agent to use the modules effectively.
        
        Returns:
            Formatted string for inclusion in system prompt
        """
        pass
    
    @abstractmethod
    def install_module(
        self, 
        name: str, 
        code: str,
        description: str = ""
    ) -> bool:
        """
        Install a custom module in the interpreter.
        
        Allows the agent to create and persist custom abstractions
        in the OFFICE layer.
        
        Args:
            name: Module name
            code: Python code for the module
            description: Human-readable description
            
        Returns:
            True if module was installed successfully
        """
        pass
    
    @abstractmethod
    def uninstall_module(self, name: str) -> bool:
        """Remove a custom module."""
        pass
    
    @abstractmethod
    def reset(self) -> None:
        """Reset the interpreter state (clear variables, temp files)."""
        pass


class ILayeredWorkspace(ABC):
    """
    Interface for the 3-layer workspace architecture.
    
    Manages three distinct workspace layers:
    1. PROJECT: User's project (git integrated)
    2. OFFICE: Agent's private workspace
    3. INTERPRETER: Ephemeral execution sandbox
    
    Each layer has different access patterns and persistence characteristics.
    """
    
    @abstractmethod
    def get_layer_root(self, layer: WorkspaceLayer) -> Path:
        """
        Get the root path for a workspace layer.
        
        Args:
            layer: The workspace layer
            
        Returns:
            Path to the layer's root directory
        """
        pass
    
    @abstractmethod
    def read(
        self, 
        path: str, 
        layer: WorkspaceLayer = WorkspaceLayer.PROJECT
    ) -> str | None:
        """
        Read a file from the specified layer.
        
        Args:
            path: Relative path within the layer
            layer: Workspace layer to read from
            
        Returns:
            File contents or None if not found
        """
        pass
    
    @abstractmethod
    def write(
        self, 
        path: str, 
        content: str,
        layer: WorkspaceLayer = WorkspaceLayer.PROJECT
    ) -> bool:
        """
        Write a file to the specified layer.
        
        For PROJECT layer, may require user confirmation depending
        on the implementation.
        
        Args:
            path: Relative path within the layer
            content: File contents
            layer: Workspace layer to write to
            
        Returns:
            True if write was successful
        """
        pass
    
    @abstractmethod
    def delete(
        self, 
        path: str, 
        layer: WorkspaceLayer = WorkspaceLayer.PROJECT
    ) -> bool:
        """Delete a file from the specified layer."""
        pass
    
    @abstractmethod
    def list_dir(
        self, 
        path: str = ".",
        layer: WorkspaceLayer = WorkspaceLayer.PROJECT,
        recursive: bool = False
    ) -> list[str]:
        """
        List directory contents.
        
        Args:
            path: Relative path within the layer
            layer: Workspace layer
            recursive: Whether to list recursively
            
        Returns:
            List of file/directory paths
        """
        pass
    
    @abstractmethod
    def exists(
        self, 
        path: str, 
        layer: WorkspaceLayer = WorkspaceLayer.PROJECT
    ) -> bool:
        """Check if a path exists in the specified layer."""
        pass
    
    @abstractmethod
    def copy_between_layers(
        self,
        source_path: str,
        source_layer: WorkspaceLayer,
        dest_path: str,
        dest_layer: WorkspaceLayer
    ) -> bool:
        """
        Copy a file between layers.
        
        Useful for promoting artifacts from INTERPRETER to PROJECT/OFFICE.
        
        Args:
            source_path: Path in source layer
            source_layer: Source workspace layer
            dest_path: Path in destination layer
            dest_layer: Destination workspace layer
            
        Returns:
            True if copy was successful
        """
        pass
    
    @abstractmethod
    def get_layer_info(self, layer: WorkspaceLayer) -> dict[str, Any]:
        """
        Get information about a layer.
        
        Returns:
            Dict with root_path, total_size, file_count, etc.
        """
        pass


class IRACIToolManager(ABC):
    """
    Minimal tool manager for RACI architecture.
    
    Instead of dozens of tool schemas, RACI uses only 2-3 core tools:
    1. execute_code: Run Python in the interpreter
    2. read_file: Read from PROJECT layer
    3. write_file: Write to PROJECT layer
    
    All other functionality is accessed through interpreter modules.
    """
    
    @abstractmethod
    def get_tools(self) -> list[dict[str, Any]]:
        """
        Get the minimal tool schemas.
        
        Returns:
            List of tool schema dictionaries (typically 2-3 tools)
        """
        pass
    
    @abstractmethod
    def execute_tool(self, name: str, **kwargs) -> Any:
        """
        Execute a tool by name.
        
        Args:
            name: Tool name ('execute_code', 'read_file', 'write_file')
            **kwargs: Tool arguments
            
        Returns:
            Tool execution result
        """
        pass
    
    @abstractmethod
    def get_context_contribution(self) -> dict[str, Any]:
        """
        Get context for the system prompt.
        
        Instead of tool schemas, returns module documentation
        and usage examples.
        """
        pass
