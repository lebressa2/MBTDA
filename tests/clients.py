"""
Real LLM Client Implementations for Agent Framework.

Implements ITextClient interface using Groq and Google APIs.
"""

import os
from typing import List, Dict, Any, Optional
from dotenv import load_dotenv

load_dotenv()

import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.interfaces.base import ITextClient


class GroqTextClient(ITextClient):
    """
    Real implementation of ITextClient using Groq API.
    
    Uses qwen/qwen3-32b model by default.
    """
    
    def __init__(self, model: str = "qwen/qwen3-32b"):
        from groq import Groq
        
        api_key = os.getenv("GROQ_API_KEY")
        if not api_key:
            raise ValueError("GROQ_API_KEY not found in environment")
        
        self.client = Groq(api_key=api_key)
        self.model = model
        self._tools = []
    
    def invoke(self, messages: List[Dict[str, str]]) -> Any:
        """Invoke the LLM with messages."""
        from langchain_core.utils.function_calling import convert_to_openai_tool
        
        request_kwargs = {
            "model": self.model,
            "messages": messages,
            "temperature": 0.3,
            "max_completion_tokens": 2048,
            "top_p": 0.95,
            "stream": False
        }
        
        # Convert and attach tools if bound
        if self._tools:
            formatted_tools = [convert_to_openai_tool(t) for t in self._tools]
            request_kwargs["tools"] = formatted_tools
            request_kwargs["tool_choice"] = "auto"
            
        completion = self.client.chat.completions.create(**request_kwargs)
        return GroqResponse(completion.choices[0].message)
    
    def bind_tools(self, tools: List[Any]) -> "GroqTextClient":
        """Bind tools to the client (returns self for chaining)."""
        self._tools = tools
        return self
    
    def get_model_name(self) -> str:
        return self.model


class GoogleTextClient(ITextClient):
    """
    Real implementation of ITextClient using Google Gemini API.
    
    Uses gemini-2.5-flash model by default.
    """
    
    def __init__(self, model: str = "gemini-2.5-flash"):
        import google.generativeai as genai
        
        api_key = os.getenv("GOOGLE_API_KEY")
        if not api_key:
            raise ValueError("GOOGLE_API_KEY not found in environment")
        
        genai.configure(api_key=api_key)
        self._model = genai.GenerativeModel(model)
        self.model_name = model
        self._tools = []
    
    def invoke(self, messages: List[Dict[str, str]]) -> Any:
        """Invoke the LLM with messages."""
        # Convert messages to Gemini format
        prompt_parts = []
        for msg in messages:
            role = msg.get("role", "user")
            content = msg.get("content", "")
            if role == "system":
                prompt_parts.append(f"System Instructions: {content}\n\n")
            elif role == "assistant":
                prompt_parts.append(f"Assistant: {content}\n")
            elif role == "tool":
                prompt_parts.append(f"Tool Result ({msg.get('name', 'unknown')}): {content}\n")
            else:
                prompt_parts.append(f"User: {content}\n")
        
        full_prompt = "".join(prompt_parts)
        response = self._model.generate_content(full_prompt)
        return GoogleResponse(response.text)
    
    def bind_tools(self, tools: List[Any]) -> "GoogleTextClient":
        """Bind tools to the client."""
        self._tools = tools
        return self
    
    def get_model_name(self) -> str:
        return self.model_name


class GroqResponse:
    """Wrapper for Groq API response to match expected interface."""
    
    def __init__(self, message):
        self.content = message.content
        self.tool_calls = getattr(message, 'tool_calls', None)
    
    def __str__(self):
        return self.content or ""


class GoogleResponse:
    """Wrapper for Google API response to match expected interface."""
    
    def __init__(self, text: str):
        self.content = text
        self.tool_calls = None  # Google doesn't have native tool calls in this simple impl
    
    def __str__(self):
        return self.content or ""


def get_text_client(prefer_groq: bool = True) -> ITextClient:
    """
    Get the best available text client with fallback.
    
    Args:
        prefer_groq: If True, try Groq first, then Google. Otherwise reverse.
    
    Returns:
        ITextClient implementation
    """
    if prefer_groq:
        try:
            client = GroqTextClient()
            # Quick test
            test = client.invoke([{"role": "user", "content": "Say OK"}])
            print(f"✅ Using Groq API ({client.model})")
            return client
        except Exception as e:
            print(f"⚠️ Groq unavailable: {e}")
    
    try:
        client = GoogleTextClient()
        test = client.invoke([{"role": "user", "content": "Say OK"}])
        print(f"✅ Using Google API ({client.model_name})")
        return client
    except Exception as e:
        print(f"⚠️ Google unavailable: {e}")
    
    if not prefer_groq:
        try:
            client = GroqTextClient()
            test = client.invoke([{"role": "user", "content": "Say OK"}])
            print(f"✅ Using Groq API ({client.model})")
            return client
        except Exception as e:
            print(f"⚠️ Groq unavailable: {e}")
    
    raise RuntimeError("No LLM API available. Check GROQ_API_KEY or GOOGLE_API_KEY in .env")
