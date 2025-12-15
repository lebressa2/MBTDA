"""
Simple Sync Runner for RACI-style agents.

A minimal runner that:
1. Builds system prompt from context
2. Invokes LLM with tools
3. Executes tool calls if any
4. Returns the response

No state machine dependency - just prompt + tools primitives.
"""

from typing import Any

from ..agent import Agent
from ..interfaces.base import IRunner


class SimpleSyncRunner(IRunner):
    """
    Simple synchronous runner - one message in, one response out.
    
    Works with the two primitives: system prompt and tools.
    No state machine complexity.
    """
    
    def __init__(self, message: str, max_tool_iterations: int = 3, debug: bool = False):
        self.message = message
        self.max_tool_iterations = max_tool_iterations
        self.debug = debug
        self.agent = None
    
    def set_agent_reference(self, agent: Agent):
        self.agent = agent
    
    def start(self) -> str:
        """Process message and return response."""
        from langchain_core.messages import SystemMessage, HumanMessage, AIMessage, ToolMessage
        
        # 1. Build system prompt (the first primitive)
        system_prompt = self.agent.build_system_prompt()
        
        # 2. Get tools (the second primitive)
        tools = []
        if self.agent.tools:
            # Use LangChain-compatible tools if available
            if hasattr(self.agent.tools, 'get_tools_for_langchain'):
                tools = self.agent.tools.get_tools_for_langchain()
            else:
                tools = self.agent.tools.get_tools()
        
        # 3. Build messages
        messages = [SystemMessage(content=system_prompt)]
        
        # Add history from memory if exists
        if self.agent.memory:
            for msg in self.agent.memory.get_recent_messages():
                if isinstance(msg, dict):
                    role = msg.get("role", "user")
                    content = msg.get("content", "")
                    if role == "user":
                        messages.append(HumanMessage(content=content))
                    elif role == "assistant":
                        messages.append(AIMessage(content=content))
        
        # Add current message
        messages.append(HumanMessage(content=self.message))
        if self.agent.memory:
            self.agent.memory.add_message("user", self.message)
        
        # 4. Bind tools to LLM
        llm = self.agent.text_provider
        if tools:
            llm = llm.bind_tools(tools)
        
        # 5. Debug print
        if self.debug:
            self._debug_print(messages, tools)
        
        # 6. Invoke LLM with tool loop
        final_response = ""
        for iteration in range(self.max_tool_iterations):
            try:
                response = llm.invoke(messages)
                
                # Check for tool calls
                if hasattr(response, 'tool_calls') and response.tool_calls:
                    # Execute tools
                    messages.append(response)  # Add AI message with tool_calls
                    
                    for tool_call in response.tool_calls:
                        tool_name = tool_call.get("name", "")
                        args = tool_call.get("args", {})
                        tool_call_id = tool_call.get("id", "")
                        
                        if self.debug:
                            print(f"\n🔧 Tool: {tool_name}({args})")
                        
                        # Execute tool
                        if self.agent.tools:
                            result = self.agent.tools.execute_tool(tool_name, **args)
                            output = result.get("output", str(result))
                            
                            if self.debug:
                                print(f"📤 Output: {output}")
                            
                            # Add tool result to messages
                            messages.append(ToolMessage(
                                content=output,
                                tool_call_id=tool_call_id
                            ))
                else:
                    # No tool calls - this is the final response
                    final_response = response.content
                    break
                    
            except Exception as e:
                if self.debug:
                    import traceback
                    traceback.print_exc()
                final_response = f"Error: {e}"
                break
        
        # Save response to memory
        if self.agent.memory and final_response:
            self.agent.memory.add_message("assistant", final_response)
        
        return final_response or "No response"
    
    def stop(self) -> None:
        pass
    
    def _debug_print(self, messages, tools):
        """Print XML debug info."""
        print("\n" + "=" * 50)
        print("🔍 DEBUG: API Call")
        print("=" * 50)
        print("<api_call>")
        print("  <messages>")
        for i, msg in enumerate(messages):
            msg_type = type(msg).__name__
            content = getattr(msg, 'content', '')
            print(f"    <msg type=\"{msg_type}\">{content}</msg>")
        print("  </messages>")
        print(f"  <tools count=\"{len(tools)}\">")
        for t in tools:
            print(f"    <tool name=\"{getattr(t, 'name', str(t))}\"/>")
        print("  </tools>")
        print("</api_call>")
        print("=" * 50)
