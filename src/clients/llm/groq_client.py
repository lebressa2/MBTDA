from typing import Any, Optional
import os

from ..interfaces.base import ITextClient

# Lazy Import Strategy
try:
    from langchain_groq import ChatGroq
    from langchain_core.messages import BaseMessage
    HAS_GROQ = True
except ImportError:
    HAS_GROQ = False


class GroqClient(ITextClient):
    """
    Client for Groq API using LangChain.
    Requires 'langchain-groq' package.
    """

    def __init__(self, model_name: str = "llama3-70b-8192", api_key: Optional[str] = None):
        """
        Initialize the Groq client.

        Args:
            model_name: Name of the model to use
            api_key: Groq API key (optional if GROQ_API_KEY env var is set)
        """
        if not HAS_GROQ:
            raise ImportError(
                "The 'langchain-groq' package is required to use GroqClient. "
                "Please install it with: pip install langchain-groq"
            )

        self.model_name = model_name
        self.api_key = api_key or os.getenv("GROQ_API_KEY")
        
        if not self.api_key:
            raise ValueError("Groq API key not found. Please provide it or set GROQ_API_KEY environment variable.")

        self.client = ChatGroq(
            model_name=model_name,
            api_key=self.api_key,
            temperature=0
        )

    def invoke(self, messages: list[Any], **kwargs) -> Any:
        return self.client.invoke(messages, **kwargs)

    def bind_tools(self, tools: list[Any]) -> "ITextClient":
        # Create a new instance with tools bound
        # Note: ChatGroq.bind_tools returns a Runnable, not the client itself.
        # We need to wrap it to maintain ITextClient interface or adjust the design.
        # For simplicity in this adaptation, we'll store the bound runnable.
        new_client = GroqClient(self.model_name, self.api_key)
        new_client.client = self.client.bind_tools(tools)
        return new_client

    def get_model_name(self) -> str:
        return self.model_name
