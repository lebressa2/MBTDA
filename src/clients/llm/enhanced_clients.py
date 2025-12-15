"""
Enhanced LLM clients with XML logging for API calls.

This module provides enhanced versions of Groq and Google LLM clients
with comprehensive XML logging for debugging and monitoring API calls,
including Chain of Thought (COT) logging throughout the process.
"""

from typing import Any, Optional, List, Dict
import os
import json
import xml.etree.ElementTree as ET
from datetime import datetime, timezone
import logging

from interfaces.base import ITextClient

# Import existing clients
from interfaces.base import ITextClient
from src.interfaces.base import ITextClient
from interfaces.base import ITextClient

# Import existing clients
from .groq_client import GroqClient
from .google_client import GoogleClient


class XMLLogger:
    """Utility class for generating XML logs."""
    
    @staticmethod
    def format_messages(messages: List[Any]) -> List[Dict[str, str]]:
        """Format messages for XML output."""
        formatted_messages = []
        for msg in messages:
            # Handle different message formats (BaseMessage, dict, etc.)
            if hasattr(msg, 'content') and hasattr(msg, 'type'):
                formatted_messages.append({
                    "role": getattr(msg, 'type', 'unknown'),
                    "content": str(getattr(msg, 'content', ''))
                })
            elif isinstance(msg, dict):
                formatted_messages.append({
                    "role": msg.get('role', 'unknown'),
                    "content": str(msg.get('content', ''))
                })
            else:
                formatted_messages.append({
                    "role": "unknown",
                    "content": str(msg)
                })
        return formatted_messages
    
    @staticmethod
    def create_llm_request_xml(provider: str, model: str, messages: List[Any], **kwargs) -> str:
        """Create XML representation of LLM request."""
        formatted_messages = XMLLogger.format_messages(messages)
        
        root = ET.Element("llm_request")
        
        # Provider and model info
        provider_elem = ET.SubElement(root, "provider")
        provider_elem.text = provider
        
        model_elem = ET.SubElement(root, "model")
        model_elem.text = model
        
        # Messages
        messages_elem = ET.SubElement(root, "messages")
        for msg in formatted_messages:
            msg_elem = ET.SubElement(messages_elem, "message")
            msg_elem.set("role", msg["role"])
            msg_elem.text = msg["content"]
        
        # Timestamp
        timestamp_elem = ET.SubElement(root, "timestamp")
        timestamp_elem.text = datetime.now(timezone.utc).isoformat()
        
        # Additional parameters
        if kwargs:
            params_elem = ET.SubElement(root, "parameters")
            for key, value in kwargs.items():
                param_elem = ET.SubElement(params_elem, "param")
                param_elem.set("name", key)
                param_elem.text = str(value)
        
        return ET.tostring(root, encoding='unicode', xml_declaration=True)
    
    @staticmethod
    def create_cot_xml(step: int, action: str, thought: str, context: str = "", **kwargs) -> str:
        """Create XML representation of Chain of Thought."""
        root = ET.Element("agent_cot")
        
        step_elem = ET.SubElement(root, "step")
        step_elem.text = str(step)
        
        action_elem = ET.SubElement(root, "action")
        action_elem.text = action
        
        thought_elem = ET.SubElement(root, "thought")
        thought_elem.text = thought
        
        if context:
            context_elem = ET.SubElement(root, "context")
            context_elem.text = context
        
        # Additional metadata
        if kwargs:
            metadata_elem = ET.SubElement(root, "metadata")
            for key, value in kwargs.items():
                meta_elem = ET.SubElement(metadata_elem, key)
                meta_elem.text = str(value)
        
        # Timestamp
        timestamp_elem = ET.SubElement(root, "timestamp")
        timestamp_elem.text = datetime.now(timezone.utc).isoformat()
        
        return ET.tostring(root, encoding='unicode', xml_declaration=True)


class EnhancedGroqClient(GroqClient):
    """Enhanced Groq client with XML logging capabilities."""
    
    def __init__(self, model_name: Optional[str] = None, api_key: Optional[str] = None, 
                 enable_logging: bool = True):
        """
        Initialize enhanced Groq client.
        
        Args:
            model_name: Model name (defaults to BASE_GROQ_TEXT_MODEL from env)
            api_key: API key (defaults to GROQ_API_KEY from env)
            enable_logging: Whether to enable XML logging
        """
        # Get model from environment if not provided
        if model_name is None:
            model_name = os.getenv("BASE_GROQ_TEXT_MODEL", "qwen/qwen3-32b")
        
        super().__init__(model_name, api_key)
        self.enable_logging = enable_logging
        self._cot_step = 0
        
        # Set up logging
        self.logger = logging.getLogger(f"{__name__}.EnhancedGroqClient")
        if not self.logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
            handler.setFormatter(formatter)
            self.logger.addHandler(handler)
            self.logger.setLevel(logging.INFO)
    
    def _log_cot(self, action: str, thought: str, context: str = "", **kwargs):
        """Log Chain of Thought with XML formatting."""
        if not self.enable_logging:
            return
            
        self._cot_step += 1
        cot_xml = XMLLogger.create_cot_xml(
            step=self._cot_step,
            action=action,
            thought=thought,
            context=context,
            **kwargs
        )
        self.logger.info(f"COT Log:\n{cot_xml}")
    
    def _log_request(self, messages: List[Any], **kwargs):
        """Log LLM request with XML formatting."""
        if not self.enable_logging:
            return
            
        request_xml = XMLLogger.create_llm_request_xml(
            provider="groq",
            model=self.model_name,
            messages=messages,
            **kwargs
        )
        self.logger.info(f"Request Log:\n{request_xml}")
    
    def invoke(self, messages: List[Any], **kwargs) -> Any:
        """Invoke LLM with XML logging."""
        # Log request
        self._log_request(messages, **kwargs)
        
        # Log COT: Request preparation
        self._log_cot(
            action="preparing_request",
            thought=f"Preparing to send {len(messages)} messages to Groq model {self.model_name}",
            context=f"Temperature: {kwargs.get('temperature', 'default')}, Max tokens: {kwargs.get('max_tokens', 'default')}"
        )
        
        try:
            # Call parent method
            result = super().invoke(messages, **kwargs)
            
            # Log COT: Request successful
            self._log_cot(
                action="request_successful",
                thought="Successfully received response from Groq API",
                context=f"Response type: {type(result).__name__}"
            )
            
            return result
            
        except Exception as e:
            # Log COT: Request failed
            self._log_cot(
                action="request_failed",
                thought=f"API request failed with error: {str(e)}",
                context=f"Error type: {type(e).__name__}",
                error_details=str(e)
            )
            raise
    
    def bind_tools(self, tools: List[Any]) -> "EnhancedGroqClient":
        """Bind tools with logging."""
        self._log_cot(
            action="binding_tools",
            thought=f"Binding {len(tools)} tools to the client",
            context="Preparing for function calling"
        )
        
        enhanced_client = EnhancedGroqClient(self.model_name, self.api_key, self.enable_logging)
        enhanced_client.client = self.client.bind_tools(tools)
        enhanced_client._cot_step = self._cot_step
        
        return enhanced_client


class EnhancedGoogleClient(GoogleClient):
    """Enhanced Google client with XML logging capabilities."""
    
    def __init__(self, model_name: Optional[str] = None, api_key: Optional[str] = None,
                 enable_logging: bool = True):
        """
        Initialize enhanced Google client.
        
        Args:
            model_name: Model name (defaults to BASE_GOOGLE_TEXT_MODEL from env)
            api_key: API key (defaults to GOOGLE_API_KEY from env)
            enable_logging: Whether to enable XML logging
        """
        # Get model from environment if not provided
        if model_name is None:
            model_name = os.getenv("BASE_GOOGLE_TEXT_MODEL", "google/gemini-2.5-flash")
        
        super().__init__(model_name, api_key)
        self.enable_logging = enable_logging
        self._cot_step = 0
        
        # Set up logging
        self.logger = logging.getLogger(f"{__name__}.EnhancedGoogleClient")
        if not self.logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
            handler.setFormatter(formatter)
            self.logger.addHandler(handler)
            self.logger.setLevel(logging.INFO)
    
    def _log_cot(self, action: str, thought: str, context: str = "", **kwargs):
        """Log Chain of Thought with XML formatting."""
        if not self.enable_logging:
            return
            
        self._cot_step += 1
        cot_xml = XMLLogger.create_cot_xml(
            step=self._cot_step,
            action=action,
            thought=thought,
            context=context,
            **kwargs
        )
        self.logger.info(f"COT Log:\n{cot_xml}")
    
    def _log_request(self, messages: List[Any], **kwargs):
        """Log LLM request with XML formatting."""
        if not self.enable_logging:
            return
            
        request_xml = XMLLogger.create_llm_request_xml(
            provider="google",
            model=self.model_name,
            messages=messages,
            **kwargs
        )
        self.logger.info(f"Request Log:\n{request_xml}")
    
    def invoke(self, messages: List[Any], **kwargs) -> Any:
        """Invoke LLM with XML logging."""
        # Log request
        self._log_request(messages, **kwargs)
        
        # Log COT: Request preparation
        self._log_cot(
            action="preparing_request",
            thought=f"Preparing to send {len(messages)} messages to Google model {self.model_name}",
            context=f"Temperature: {kwargs.get('temperature', 'default')}, Max tokens: {kwargs.get('max_tokens', 'default')}"
        )
        
        try:
            # Call parent method
            result = super().invoke(messages, **kwargs)
            
            # Log COT: Request successful
            self._log_cot(
                action="request_successful",
                thought="Successfully received response from Google API",
                context=f"Response type: {type(result).__name__}"
            )
            
            return result
            
        except Exception as e:
            # Log COT: Request failed
            self._log_cot(
                action="request_failed",
                thought=f"API request failed with error: {str(e)}",
                context=f"Error type: {type(e).__name__}",
                error_details=str(e)
            )
            raise
    
    def bind_tools(self, tools: List[Any]) -> "EnhancedGoogleClient":
        """Bind tools with logging."""
        self._log_cot(
            action="binding_tools",
            thought=f"Binding {len(tools)} tools to the client",
            context="Preparing for function calling"
        )
        
        enhanced_client = EnhancedGoogleClient(self.model_name, self.api_key, self.enable_logging)
        enhanced_client.client = self.client.bind_tools(tools)
        enhanced_client._cot_step = self._cot_step
        
        return enhanced_client


class FallbackLLMClient(ITextClient):
    """
    Fallback LLM client that tries Groq first, then Google.
    
    This client provides automatic failover with comprehensive XML logging
    for debugging the RACI interpreter workflow.
    """
    
    def __init__(self, enable_logging: bool = True, fallback_enabled: bool = True):
        """
        Initialize fallback client.
        
        Args:
            enable_logging: Whether to enable XML logging
            fallback_enabled: Whether to enable automatic fallback
        """
        self.enable_logging = enable_logging
        self.fallback_enabled = fallback_enabled
        self._cot_step = 0
        
        # Initialize clients
        self.groq_client = None
        self.google_client = None
        self.current_client = None
        self.current_provider = None
        
        # Set up logging
        self.logger = logging.getLogger(f"{__name__}.FallbackLLMClient")
        if not self.logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
            handler.setFormatter(formatter)
            self.logger.addHandler(handler)
            self.logger.setLevel(logging.INFO)
        
        # Initialize clients
        self._initialize_clients()
    
    def _initialize_clients(self):
        """Initialize Groq and Google clients."""
        self._log_cot(
            action="initializing_clients",
            thought="Initializing Groq and Google LLM clients from environment configuration"
        )
        
        try:
            self.groq_client = EnhancedGroqClient(enable_logging=self.enable_logging)
            self._log_cot(
                action="groq_client_initialized",
                thought=f"Successfully initialized Groq client with model: {self.groq_client.model_name}"
            )
        except Exception as e:
            self._log_cot(
                action="groq_client_failed",
                thought=f"Failed to initialize Groq client: {str(e)}",
                context="Will rely on Google client only"
            )
            self.groq_client = None
        
        try:
            self.google_client = EnhancedGoogleClient(enable_logging=self.enable_logging)
            self._log_cot(
                action="google_client_initialized",
                thought=f"Successfully initialized Google client with model: {self.google_client.model_name}"
            )
        except Exception as e:
            self._log_cot(
                action="google_client_failed",
                thought=f"Failed to initialize Google client: {str(e)}",
                context="Will rely on Groq client only"
            )
            self.google_client = None
        
        # Set initial provider (Groq first if available)
        if self.groq_client:
            self.current_client = self.groq_client
            self.current_provider = "groq"
        elif self.google_client:
            self.current_client = self.google_client
            self.current_provider = "google"
        else:
            raise ValueError("No LLM clients could be initialized. Check API keys and environment configuration.")
    
    def _log_cot(self, action: str, thought: str, context: str = "", **kwargs):
        """Log Chain of Thought with XML formatting."""
        if not self.enable_logging:
            return
            
        self._cot_step += 1
        cot_xml = XMLLogger.create_cot_xml(
            step=self._cot_step,
            action=action,
            thought=thought,
            context=context,
            **kwargs
        )
        self.logger.info(f"COT Log:\n{cot_xml}")
    
    def _log_request(self, messages: List[Any], provider: str, **kwargs):
        """Log LLM request with XML formatting."""
        if not self.enable_logging:
            return
            
        model_name = self.current_client.model_name if self.current_client else "unknown"
        request_xml = XMLLogger.create_llm_request_xml(
            provider=provider,
            model=model_name,
            messages=messages,
            **kwargs
        )
        self.logger.info(f"Request Log:\n{request_xml}")
    
    def invoke(self, messages: List[Any], **kwargs) -> Any:
        """Invoke LLM with automatic fallback and comprehensive logging."""
        
        # Log RACI workflow context
        self._log_cot(
            action="raci_workflow_start",
            thought="Starting RACI interpreter workflow with fallback LLM client",
            context="Will attempt Groq first, then Google if Groq fails",
            available_providers=[p for p in ["groq", "google"] if (self.groq_client if p == "groq" else self.google_client)]
        )
        
        # Try Groq first if available
        if self.groq_client and self.current_provider == "groq":
            self._log_request(messages, "groq", **kwargs)
            self._log_cot(
                action="attempting_groq",
                thought=f"Attempting to use Groq client with model {self.groq_client.model_name}",
                context="Primary provider"
            )
            
            try:
                result = self.groq_client.invoke(messages, **kwargs)
                self._log_cot(
                    action="groq_success",
                    thought="Successfully used Groq client",
                    context="Primary provider working correctly"
                )
                return result
            except Exception as e:
                self._log_cot(
                    action="groq_failed",
                    thought=f"Groq client failed: {str(e)}",
                    context="Will attempt fallback to Google"
                )
                
                if self.fallback_enabled and self.google_client:
                    self._log_cot(
                        action="switching_to_google",
                        thought="Switching to Google client as fallback",
                        context="Automatic failover initiated"
                    )
                    self.current_client = self.google_client
                    self.current_provider = "google"
                else:
                    raise
        
        # Try Google if Groq failed or wasn't primary
        if self.google_client:
            self._log_request(messages, "google", **kwargs)
            self._log_cot(
                action="attempting_google",
                thought=f"Attempting to use Google client with model {self.google_client.model_name}",
                context="Fallback provider"
            )
            
            try:
                result = self.google_client.invoke(messages, **kwargs)
                self._log_cot(
                    action="google_success",
                    thought="Successfully used Google client",
                    context="Fallback provider working correctly"
                )
                return result
            except Exception as e:
                self._log_cot(
                    action="google_failed",
                    thought=f"Google client failed: {str(e)}",
                    context="Both providers failed"
                )
                raise
        
        raise ValueError("No LLM clients available or all failed")
    
    def bind_tools(self, tools: List[Any]) -> "FallbackLLMClient":
        """Bind tools to current client."""
        self._log_cot(
            action="binding_tools_fallback",
            thought=f"Binding {len(tools)} tools to fallback client",
            context=f"Current provider: {self.current_provider}"
        )
        
        # Create new instance with bound tools
        new_client = FallbackLLMClient(self.enable_logging, self.fallback_enabled)
        
        if self.groq_client:
            new_client.groq_client = self.groq_client.bind_tools(tools)
        if self.google_client:
            new_client.google_client = self.google_client.bind_tools(tools)
        
        # Update current client reference
        if self.current_provider == "groq" and new_client.groq_client:
            new_client.current_client = new_client.groq_client
        elif self.current_provider == "google" and new_client.google_client:
            new_client.current_client = new_client.google_client
        
        return new_client
    
    def get_model_name(self) -> str:
        """Get current model name."""
        if self.current_client:
            return self.current_client.model_name
        return "unknown"
    
    def get_current_provider(self) -> str:
        """Get current provider name."""
        return self.current_provider or "unknown"
    
    def switch_provider(self, provider: str):
        """Manually switch to a specific provider."""
        if provider == "groq" and self.groq_client:
            self.current_client = self.groq_client
            self.current_provider = "groq"
            self._log_cot(
                action="manual_provider_switch",
                thought=f"Manually switched to Groq provider",
                context=f"Model: {self.groq_client.model_name}"
            )
        elif provider == "google" and self.google_client:
            self.current_client = self.google_client
            self.current_provider = "google"
            self._log_cot(
                action="manual_provider_switch",
                thought=f"Manually switched to Google provider",
                context=f"Model: {self.google_client.model_name}"
            )
        else:
            raise ValueError(f"Provider {provider} not available")


# Convenience functions for easy usage
def create_enhanced_groq_client(model_name: Optional[str] = None, 
                               api_key: Optional[str] = None,
                               enable_logging: bool = True) -> EnhancedGroqClient:
    """Create enhanced Groq client with logging."""
    return EnhancedGroqClient(model_name, api_key, enable_logging)


def create_enhanced_google_client(model_name: Optional[str] = None,
                                api_key: Optional[str] = None,
                                enable_logging: bool = True) -> EnhancedGoogleClient:
    """Create enhanced Google client with logging."""
    return EnhancedGoogleClient(model_name, api_key, enable_logging)


def create_fallback_client(enable_logging: bool = True,
                         fallback_enabled: bool = True) -> FallbackLLMClient:
    """Create fallback LLM client with automatic failover."""
    return FallbackLLMClient(enable_logging, fallback_enabled)


if __name__ == "__main__":
    # Example usage and testing
    print("Enhanced LLM Clients with XML Logging")
    print("=" * 50)
    
    try:
        # Test fallback client
        client = create_fallback_client(enable_logging=True)
        print(f"Current provider: {client.get_current_provider()}")
        print(f"Current model: {client.get_model_name()}")
        
        # Test message
        test_messages = [
            {"role": "system", "content": "You are a helpful assistant."},
            {"role": "user", "content": "Hello, how are you?"}
        ]
        
        print("\nTesting with sample message...")
        result = client.invoke(test_messages)
        print(f"Response: {result}")
        
    except Exception as e:
        print(f"Test failed: {e}")