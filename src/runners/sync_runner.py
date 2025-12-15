from typing import Any

from ..agent import Agent
from ..interfaces.base import IRunner

class SyncRunner(IRunner):
    """
    Runner for synchronous mode - processes single messages.

    Use for request/response interactions, chatbots, or API endpoints.
    Processes one message and returns the response immediately.

    Recebe uma string de mensagem, adiciona ao memory (se existir),
    chama state_machine.trigger("message", self.agent),
    aguarda o loop ReAct terminar (até IDLE),
    retorna a última resposta do memory ou "No response".

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

        # Trigger the message event
        self.agent.state_machine.trigger("message", self.agent)

        # Wait for the ReAct loop to complete (until IDLE)
        while not self.agent.state_machine.current_state == "IDLE":
            pass  # Wait for completion

        # Return the last message from memory as the response
        if self.agent.memory:
            messages = self.agent.memory.get_recent_messages()
            if messages:
                last_msg = messages[-1]
                if isinstance(last_msg, dict):
                    return last_msg.get("content") or "No response"
                return getattr(last_msg, 'content', "No response") or "No response"

        return "No response"

    def stop(self) -> None:
        # For sync, nothing to stop
        pass
