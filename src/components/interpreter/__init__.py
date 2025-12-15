"""
Interpreter Components Package.

Provides code execution in a sandboxed environment:
- SandboxInterpreter: Execute Python with pre-configured modules
"""

from .sandbox import SandboxInterpreter

__all__ = ["SandboxInterpreter"]
