"""
Atomic Data Models for the Agent Framework.

This module contains the core models for tools and execution,
following the standalone atomic component architecture.
"""

from typing import Any, Callable, Type, List, Optional
from pydantic import BaseModel, Field

# ==============================================================================
# TOOL MODELS (Atomic Core)
# ==============================================================================

class Tool(BaseModel):
    """
    Represents an atomic tool that can be executed by the agent.
    
    A tool combines metadata (name, description), an input validation 
    schema (Pydantic model), and the actual execution logic.
    """
    name: str = Field(..., description="Unique name of the tool")
    description: str = Field(..., description="Clear description of what the tool does")
    args_schema: Type[BaseModel] = Field(..., description="Pydantic model for input validation")
    func: Callable = Field(..., description="The atomic function to execute")

    def execute(self, **kwargs) -> Any:
        """
        Validate arguments and execute the tool.
        """
        # Validate using the schema
        validated_args = self.args_schema(**kwargs)
        # Execute with validated dictionary
        return self.func(**validated_args.model_dump())

    def get_schema(self) -> dict[str, Any]:
        """Get the JSON schema for this tool (OpenAI/LangChain compatible)."""
        return {
            "name": self.name,
            "description": self.description,
            "parameters": self.args_schema.model_json_schema()
        }

class ToolCall(BaseModel):
    """Represents a request from an LLM to execute a tool."""
    id: str = Field(..., description="Unique identifier for the tool call")
    name: str = Field(..., description="Name of the tool to call")
    args: dict[str, Any] = Field(default_factory=dict, description="Arguments for the tool")

class ToolResult(BaseModel):
    """Represents the result of a tool execution."""
    tool_call_id: str
    name: str
    content: str
    is_error: bool = False

    def to_dict(self) -> dict[str, Any]:
        return {
            "role": "tool",
            "tool_call_id": self.tool_call_id,
            "name": self.name,
            "content": self.content
        }