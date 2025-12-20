"""
RACI - Retrieval Augmented Code Interpreter

This module provides the Code Interpreter component for the agent framework.
The interpreter executes Python code in a sandbox with pre-configured modules.

Design Philosophy:
- SandboxInterpreter is the ONLY new component
- Uses existing WorkspaceManager for file operations
- Uses existing ToolManager for tool registration
- Agent remains a "dumb LEGO piece" - just plug components together
"""

from dataclasses import dataclass, field
from typing import Any


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
