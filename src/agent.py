"""
Agent Manifesto and Configuration Models.

This module defines the declarative state of an agent using Pydantic models.
The AgentManifest serves as the single source of truth for identity and configuration.
"""

import uuid
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class ContextConfig(BaseModel):
    """Configuration for the agent's context and system prompt."""
    # The dict allows fine-grained control (e.g., "persona", "rules", "extra_context" blocks)
    system_prompt_blocks: Dict[str, str] = Field(default_factory=dict)
    max_tokens_history: int = 2000
    use_rag: bool = False


class ToolConfig(BaseModel):
    """Configuration for a specific tool."""
    name: str
    enabled: bool = True
    timeout: int = 30
    parameters: Dict[str, Any] = Field(default_factory=dict)


class MemoryConfig(BaseModel):
    """Configuration for the agent's memory."""
    memory_type: str = "in_memory"
    short_term_limit: int = 20
    long_term_enabled: bool = False


class WorkspaceConfig(BaseModel):
    """Configuration for the agent's workspace."""
    root_directory: Optional[str] = None
    allowed_extensions: List[str] = Field(default_factory=list)
    read_only: bool = False


class AgentManifest(BaseModel):
    """
    The Agent Manifesto.
    
    This is a pure data model that defines what an agent IS and how it is configured.
    It does not contain execution logic, which is delegated to Runtime components.
    """
    agent_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    agent_name: str
    version: str = "1.0.0"
    description: Optional[str] = None
    
    model_name: str = "qwen/qwen3-32b"
    provider: str = "groq"
    
    context_config: ContextConfig = Field(default_factory=ContextConfig)
    tools: List[ToolConfig] = Field(default_factory=list)
    memory_config: MemoryConfig = Field(default_factory=MemoryConfig)
    workspace_config: WorkspaceConfig = Field(default_factory=WorkspaceConfig)
    
    metadata: Dict[str, Any] = Field(default_factory=dict)


class AgentRuntime:
    """
    A simple Runtime for executing an AgentManifest.
    
    This class bridges the declarative Manifesto with the imperative execution logic.
    """
    
    def __init__(
        self, 
        manifest: AgentManifest,
        text_provider: Any,  # ITextClient
        memory: Optional[Any] = None,  # IMemoryManager
        tools: Optional[Any] = None,   # IToolManager
        logger: Optional[Any] = None   # ILogger
    ):
        self.manifest = manifest
        self.text_provider = text_provider
        self.memory = memory
        self.tools = tools
        self.logger = logger
        
        # Auto-configure components based on manifest
        self._apply_manifest()

    def _apply_manifest(self):
        """Apply manifest configurations to components."""
        if self.logger:
            self.logger.info(f"Initializing Runtime for Agent: {self.manifest.agent_name} (v{self.manifest.version})")
        
        # In a real implementation, components would configure themselves
        # based on self.manifest. For now, we just ensure they exist if needed.
        pass

    def build_system_prompt(self) -> str:
        """Build the system prompt from manifest blocks."""
        blocks = self.manifest.context_config.system_prompt_blocks
        if not blocks:
            return "You are a helpful AI assistant."
        
        # Order: persona -> tone -> constraints -> others
        ordered_keys = ["persona", "tone", "constraints"]
        prompt_parts = []
        
        for key in ordered_keys:
            if key in blocks:
                prompt_parts.append(blocks[key])
        
        for key, value in blocks.items():
            if key not in ordered_keys:
                prompt_parts.append(value)
                
        return "\n\n".join(prompt_parts)

    def chat(self, message: str) -> str:
        """Process a user message synchronously."""
        if self.logger:
            self.logger.info(f"[{self.manifest.agent_name}] Processing: {message[:50]}...")

        # Store message in memory
        if self.memory:
            self.memory.add_message("user", message)

        # Prepare messages
        system_prompt = self.build_system_prompt()
        messages = [{"role": "system", "content": system_prompt}]

        if self.memory:
            mem_msgs = self.memory.get_recent_messages()
            # Sanitize messages
            clean_msgs = []
            for m in mem_msgs:
                if isinstance(m, dict):
                    clean_m = {
                        k: v for k, v in m.items()
                        if k in ['role', 'content', 'tool_calls', 'tool_call_id', 'name']
                    }
                    clean_msgs.append(clean_m)
                else:
                    clean_msgs.append(m)
            messages.extend(clean_msgs)

        # Invoke LLM
        try:
            # Bind tools if available and enabled in manifest
            llm = self.text_provider
            if self.tools:
                enabled_tools = [t.name for t in self.manifest.tools if t.enabled]
                available_tools = self.tools.get_tools()
                # Filter tools based on manifest
                tools_to_bind = [t for t in available_tools if t.name in enabled_tools]
                if tools_to_bind:
                    llm = llm.bind_tools(tools_to_bind)

            response = llm.invoke(messages)

            # Store response
            if self.memory:
                self.memory.add_message("assistant", response.content or "")

            # Check for tool calls
            if hasattr(response, 'tool_calls') and response.tool_calls:
                if self.logger:
                    self.logger.info(f"🛠️ Tool calls detected: {len(response.tool_calls)}")

                # Execute tools
                if self.tools:
                    results = self.tools.execute_tool_calls(response.tool_calls)

                    # Add results to memory
                    for result in results:
                        if self.memory:
                            self.memory.add_message("tool", result["content"], tool_call_id=result["tool_call_id"])

                    # For single-turn, we return the tool results as the response
                    tool_outputs = [r["content"] for r in results]
                    return "\n".join(tool_outputs) if tool_outputs else "Tools executed successfully"
                else:
                    return response.content or "No response"
            else:
                # Return the direct response
                return response.content or "No response"

        except Exception as e:
            if self.logger:
                self.logger.error(f"Error in processing: {e}")
            return f"Error: {e}"
