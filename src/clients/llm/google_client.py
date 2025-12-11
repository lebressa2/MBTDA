from typing import Any, Optional
import os

from ..interfaces.base import ITextClient

# Lazy Import Strategy
try:
    from langchain_google_genai import ChatGoogleGenerativeAI
    from langchain_core.messages import BaseMessage
    HAS_GOOGLE = True
except ImportError:
    HAS_GOOGLE = False


class GoogleClient(ITextClient):
    """
    Client for Google Gemini API using LangChain.
    Requires 'langchain-google-genai' package.
    """

    def __init__(self, model_name: str = "gemini-1.5-pro", api_key: Optional[str] = None):
        """
        Initialize the Google client.

        Args:
            model_name: Name of the model to use
            api_key: Google API key (optional if GOOGLE_API_KEY env var is set)
        """
        if not HAS_GOOGLE:
            raise ImportError(
                "The 'langchain-google-genai' package is required to use GoogleClient. "
                "Please install it with: pip install langchain-google-genai"
            )

        self.model_name = model_name
        self.api_key = api_key or os.getenv("GOOGLE_API_KEY")
        
        if not self.api_key:
            raise ValueError("Google API key not found. Please provide it or set GOOGLE_API_KEY environment variable.")

        self.client = ChatGoogleGenerativeAI(
            model=model_name,
            google_api_key=self.api_key,
            temperature=0
        )

    def invoke(self, messages: list[Any], **kwargs) -> Any:
        return self.client.invoke(messages, **kwargs)

    def bind_tools(self, tools: list[Any]) -> "ITextClient":
        new_client = GoogleClient(self.model_name, self.api_key)
        new_client.client = self.client.bind_tools(tools)
        return new_client

    def get_model_name(self) -> str:
        return self.model_name
