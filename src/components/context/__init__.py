"""
Context component for the Agent Framework.
"""

from .composer import PromptComposer, MetaData
from .templates.registry import TemplateRegistry

__all__ = [
    "PromptComposer",
    "MetaData",
    "TemplateRegistry",
]