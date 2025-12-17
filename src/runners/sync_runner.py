from typing import Any

from ..agent import Agent
from ..interfaces.base import IRunner

class SyncRunner(IRunner):
    """
    Runner for synchronous mode - processes single messages.

    Use for request/response interactions, chatbots, or API endpoints.
    Processes one message and returns the response immediately.

    Performs a single LLM call with tool support.

    Example:
        agent = Agent(text_provider=llm_client)
        response = agent.chat("Hello, how are you?")  # direct chat method

        # or using runner directly:
        agent.run_with(SyncRunner("What is the capital of France?"))
    """

    def __init__(self, message: str):
        self.message = message
        self.agent = None  # será definido por set_agent_reference

    def set_agent_reference(self, agent: Agent):
        """Define a referência do agente"""
        self.agent = agent

    def start(self) -> str:
        if self.agent.logger:
            self.agent.logger.info(f"Processing message: {self.message[:50]}...")

        # Store message in memory
        if self.agent.memory:
            self.agent.memory.add_message("user", self.message)

        # Prepare messages
        system_prompt = self.agent.build_system_prompt()
        messages = [{"role": "system", "content": system_prompt}]

        if self.agent.memory:
            mem_msgs = self.agent.memory.get_recent_messages()
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
            response = self.agent.invoke_llm(messages)

            # Store response
            if self.agent.memory:
                self.agent.memory.add_message("assistant", response.content)

            # Check for tool calls
            if hasattr(response, 'tool_calls') and response.tool_calls:
                if self.agent.logger:
                    self.agent.logger.info(f"🛠️ Tool calls detected: {len(response.tool_calls)}")

                # Execute tools
                if self.agent.tools:
                    results = self.agent.tools.execute_tool_calls(response.tool_calls)

                    # Add results to memory
                    for result in results:
                        if self.agent.memory:
                            self.agent.memory.add_message("tool", result["content"], tool_call_id=result["tool_call_id"])

                    # For single-turn, we return the tool results as the response
                    tool_outputs = [r["content"] for r in results]
                    return "\n".join(tool_outputs) if tool_outputs else "Tools executed successfully"
                else:
                    return response.content or "No response"
            else:
                # Return the direct response
                return response.content or "No response"

        except Exception as e:
            if self.agent.logger:
                self.agent.logger.error(f"Error in processing: {e}")
            return f"Error: {e}"

    def stop(self) -> None:
        # For sync, nothing to stop
        pass
