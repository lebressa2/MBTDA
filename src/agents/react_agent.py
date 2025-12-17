"""
Simple Agent Implementation.

This module provides a simple agent creator for basic interactions.
"""

from typing import Any

from ..agent import Agent
from ..interfaces.base import (
    ITextClient,
    IMemoryManager,
    IToolManager,
    ILogger,
    IWorkspaceManager,
    IRunner,
)
from ..runners.sync_runner import SyncRunner

def create_simple_agent(
    text_provider: ITextClient,
    tools: IToolManager | None = None,
    memory: IMemoryManager | None = None,
    workspace_manager: IWorkspaceManager | None = None,
    logger: ILogger | None = None,
    runner: IRunner | None = None,
    **kwargs
) -> Agent:
    """
    Create a simple agent for basic interactions.

    Uses SyncRunner by default for request/response behavior.

    Args:
        text_provider: LLM client for text generation
        tools: Tool manager (optional)
        memory: Memory manager (optional)
        workspace_manager: Workspace manager (optional)
        logger: Logger (optional)
        runner: Execution strategy (defaults to SyncRunner)

    Returns:
        Simple agent configured for basic interactions
    """
    # Use SyncRunner by default
    if runner is None:
        runner = SyncRunner()

    agent = Agent(
        text_provider=text_provider,
        tools=tools,
        memory=memory,
        workspace_manager=workspace_manager,
        logger=logger,
        runner=runner,
        **kwargs
    )

    return agent


def chat(message: str, text_provider: ITextClient, **kwargs) -> str:
    """
    Convenience function to create a simple agent and chat immediately.

    Args:
        message: User message to process
        text_provider: LLM client
        **kwargs: Additional arguments for create_simple_agent

    Returns:
        Agent response
    """
    agent = create_simple_agent(text_provider=text_provider, **kwargs)
    return agent.chat(message)
