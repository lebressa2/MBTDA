"""
ReAct Agent Implementation.

This module implements the ReAct (Reasoning + Acting) pattern using the
generic Agent framework and StateMachine.
"""

from typing import Any

from ..agent import Agent
from ..components.state.machine import StateConfig
from ..models.data_models import AgentState, Transition
from ..interfaces.base import (
    ITextClient,
    IMemoryManager,
    IToolManager,
    ILogger,
    IWorkspaceManager,
)

def create_react_agent(
    text_provider: ITextClient,
    tools: IToolManager | None = None,
    memory: IMemoryManager | None = None,
    workspace_manager: IWorkspaceManager | None = None,
    logger: ILogger | None = None,
    **kwargs
) -> Agent:
    """
    Create an Agent configured with the ReAct pattern.
    """
    agent = Agent(
        text_provider=text_provider,
        tools=tools,
        memory=memory,
        workspace_manager=workspace_manager,
        logger=logger,
        **kwargs
    )
    
    sm = agent.state_machine
    
    # --- ReAct Logic Callbacks ---
    
    def reset_steps(agent_instance: Agent):
        """Reset the step counter."""
        agent_instance.context.add("react_step_count", 0)

    def on_enter_thinking(agent_instance: Agent):
        """
        Logic for THINKING state:
        1. Check step limit.
        2. Build system prompt (with context).
        3. Invoke LLM with history.
        4. Parse response.
        5. Transition.
        """
        # Check step limit
        current_step = agent_instance.context.get("react_step_count") or 0
        if current_step > 15:
            if agent_instance.logger:
                agent_instance.logger.error("❌ Max ReAct steps reached. Stopping.")
            agent_instance.state_machine.force_transition(AgentState.IDLE.value, agent_instance)
            return

        agent_instance.context.add("react_step_count", current_step + 1)

        if agent_instance.logger:
            agent_instance.logger.info(f"🤔 Entering THINKING mode (Step {current_step + 1})...")
            
        # Prepare messages
        system_prompt = agent_instance.build_system_prompt()
        messages = [{"role": "system", "content": system_prompt}]
        
        if agent_instance.memory:
            mem_msgs = agent_instance.memory.get_recent_messages()
            # Sanitize messages to remove internal fields like 'metadata' that APIs might reject
            clean_msgs = []
            for m in mem_msgs:
                if isinstance(m, dict):
                    # Keep only standard chat completion fields
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
            response = agent_instance.invoke_llm(messages)
            
            # Store response
            if agent_instance.memory:
                agent_instance.memory.add_message("assistant", response.content)
                
            # Check for tool calls
            if hasattr(response, 'tool_calls') and response.tool_calls:
                if agent_instance.logger:
                    agent_instance.logger.info(f"🛠️ Tool calls detected: {len(response.tool_calls)}")
                agent_instance.state_machine.trigger("decide_act", agent_instance)
            else:
                if agent_instance.logger:
                    agent_instance.logger.info("✅ Final answer generated.")
                agent_instance.state_machine.trigger("decide_finish", agent_instance)
                
        except Exception as e:
            if agent_instance.logger:
                agent_instance.logger.error(f"Error in THINKING: {e}")
            agent_instance.state_machine.force_transition(AgentState.ERROR.value, agent_instance)

    def on_enter_working(agent_instance: Agent):
        """
        Logic for WORKING state:
        1. Execute pending tool calls.
        2. Add results to memory.
        3. Transition back to THINKING.
        """
        if agent_instance.logger:
            agent_instance.logger.info("⚙️ Entering WORKING mode...")
            
        # Get last message to find tool calls
        last_message = None
        if agent_instance.memory:
            messages = agent_instance.memory.get_recent_messages()
            if messages:
                last_message = messages[-1]
                
        if last_message and hasattr(last_message, 'tool_calls') and last_message.tool_calls:
            # Execute tools
            if agent_instance.tools:
                results = agent_instance.tools.execute_tool_calls(last_message.tool_calls)
                
                # Add results to memory
                for result in results:
                    if agent_instance.memory:
                        agent_instance.memory.add_message("tool", result["content"], tool_call_id=result["tool_call_id"])
            
            # Transition back to THINKING
            agent_instance.state_machine.trigger("action_done", agent_instance)
        else:
            # No tools to execute? Should not happen if we transitioned here.
            agent_instance.state_machine.trigger("action_done", agent_instance)

    # --- Register States ---

    sm.register_state(
        name=AgentState.THINKING.value,
        instruction=(
            "Você é um Agente ReAct. Analise o pedido, pense passo a passo "
            "e decida se precisa usar ferramentas ou responder."
        ),
        on_enter=on_enter_thinking,
        required_tools=["check_inbox"] if agent.inbox_client else []
    )
    
    sm.register_state(
        name=AgentState.WORKING.value,
        instruction="Executando ferramentas...",
        on_enter=on_enter_working
    )
    
    sm.register_state(
        name=AgentState.MONITORING.value,
        instruction="Monitorando eventos..."
    )

    # --- Register Transitions ---
    
    # IDLE -> THINKING (Triggered by process_message)
    sm.add_transition(Transition(
        source=AgentState.IDLE.value,
        target=AgentState.THINKING.value,
        trigger="message",
        priority=10,
        on_enter=reset_steps # Reset steps when starting new task
    ))
    
    # THINKING -> WORKING (If tool calls)
    sm.add_transition(Transition(
        source=AgentState.THINKING.value,
        target=AgentState.WORKING.value,
        trigger="decide_act",
        priority=10
    ))
    
    # THINKING -> IDLE (If final answer)
    sm.add_transition(Transition(
        source=AgentState.THINKING.value,
        target=AgentState.IDLE.value,
        trigger="decide_finish",
        priority=10
    ))
    
    # WORKING -> THINKING (After execution)
    sm.add_transition(Transition(
        source=AgentState.WORKING.value,
        target=AgentState.THINKING.value,
        trigger="action_done",
        priority=10
    ))
    
    # MONITORING -> THINKING (On event)
    sm.add_transition(Transition(
        source=AgentState.MONITORING.value,
        target=AgentState.THINKING.value,
        trigger="event:inbox_activity",
        priority=10
    ))
    
    return agent
