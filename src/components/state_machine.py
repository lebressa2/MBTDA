"""
State Machine for the Agent Framework.

Manages agent states and transitions, providing the core flow control
for both synchronous and reactive operation modes.
"""

from typing import Dict, List, Any, Optional, Callable, Set
from ..models.data_models import Transition, AgentState, Protocol


class StateConfig:
    """
    Configuration for a state in the state machine.
    
    Each state has a macro instruction, required tools, and optional
    protocols that guide the agent's behavior while in that state.
    """
    
    def __init__(
        self,
        name: str,
        instruction: str,
        required_tools: Optional[List[str]] = None,
        protocols: Optional[str] = None,
        on_enter: Optional[Callable] = None,
        on_exit: Optional[Callable] = None,
        timeout_seconds: Optional[float] = None
    ):
        """
        Initialize state configuration.
        
        Args:
            name: State name/identifier
            instruction: Macro instruction for the agent in this state
            required_tools: List of tool names required for this state
            protocols: Query string to find relevant protocols
            on_enter: Callback when entering this state
            on_exit: Callback when leaving this state
            timeout_seconds: Optional timeout for this state
        """
        self.name = name
        self.instruction = instruction
        self.required_tools = required_tools or []
        self.protocols = protocols
        self.on_enter = on_enter
        self.on_exit = on_exit
        self.timeout_seconds = timeout_seconds
    
    def get_instruction(self) -> str:
        """Get the macro instruction for this state."""
        return self.instruction


class StateMachine:
    """
    State machine for managing agent operation modes.
    
    The state machine handles transitions between different agent states
    (THINKING, MONITORING, WORKING, etc.) based on triggers and conditions.
    It is the central orchestrator for both synchronous and reactive modes.
    
    Attributes:
        states: Dictionary of registered state configurations
        transitions: List of registered transitions
        current_state: Name of the current state
        previous_state: Name of the previous state (for history)
        state_history: List of state transitions for debugging
    """
    
    def __init__(self, initial_state: str = AgentState.IDLE.value):
        """
        Initialize the state machine.
        
        Args:
            initial_state: The starting state (defaults to IDLE)
        """
        self.states: Dict[str, StateConfig] = {}
        self.transitions: List[Transition] = []
        self.current_state: str = initial_state
        self.previous_state: Optional[str] = None
        self.state_history: List[Dict[str, Any]] = []
        self._agent_ref: Optional[Any] = None
        
        # Register default states
        self._register_default_states()
    
    def _register_default_states(self) -> None:
        """Register the default agent states."""
        default_states = {
            AgentState.IDLE.value: StateConfig(
                name=AgentState.IDLE.value,
                instruction="Você está no estado IDLE. Aguardando instruções ou eventos.",
            ),
            AgentState.THINKING.value: StateConfig(
                name=AgentState.THINKING.value,
                instruction=(
                    "Você é um Agente ReAct e está entrando no modo THINKING. "
                    "Analise o contexto, formule hipóteses, avalie opções e planeje "
                    "passos lógicos para decidir a próxima ação. Mantenha todo o "
                    "raciocínio interno e não o revele ao usuário."
                ),
                required_tools=["check_inbox"],
            ),
            AgentState.WORKING.value: StateConfig(
                name=AgentState.WORKING.value,
                instruction=(
                    "Você está no modo WORKING. Execute as ações planejadas "
                    "usando as ferramentas disponíveis. Documente cada passo."
                ),
            ),
            AgentState.MONITORING.value: StateConfig(
                name=AgentState.MONITORING.value,
                instruction=(
                    "Você está no modo MONITORING. Observe continuamente as fontes "
                    "de eventos (inbox, tasks) e responda a novos eventos."
                ),
            ),
            AgentState.REQUEST_RECEIVED.value: StateConfig(
                name=AgentState.REQUEST_RECEIVED.value,
                instruction=(
                    "Uma nova requisição foi recebida. Processar a entrada do usuário "
                    "e preparar para transição ao modo THINKING."
                ),
            ),
            AgentState.INTERRUPTED.value: StateConfig(
                name=AgentState.INTERRUPTED.value,
                instruction=(
                    "O agente foi interrompido. Salvar estado atual e preparar "
                    "para retomar ou encerrar."
                ),
            ),
            AgentState.ERROR.value: StateConfig(
                name=AgentState.ERROR.value,
                instruction=(
                    "Um erro ocorreu. Avaliar a situação e decidir sobre recuperação "
                    "ou escalação."
                ),
            ),
            AgentState.SHUTDOWN.value: StateConfig(
                name=AgentState.SHUTDOWN.value,
                instruction="O agente está encerrando. Finalizar processos pendentes.",
            ),
        }
        
        for name, config in default_states.items():
            self.states[name] = config
    
    # ==========================================================================
    # STATE REGISTRATION
    # ==========================================================================
    
    def register_state(
        self,
        name: str,
        instruction: str,
        required_tools: Optional[List[str]] = None,
        protocols: Optional[str] = None,
        on_enter: Optional[Callable] = None,
        on_exit: Optional[Callable] = None,
        timeout_seconds: Optional[float] = None
    ) -> None:
        """
        Register or update a state configuration.
        
        Args:
            name: State name/identifier
            instruction: Macro instruction for this state
            required_tools: List of required tool names
            protocols: Protocol query string
            on_enter: Callback when entering this state
            on_exit: Callback when leaving this state
            timeout_seconds: Optional timeout for this state
        """
        self.states[name] = StateConfig(
            name=name,
            instruction=instruction,
            required_tools=required_tools,
            protocols=protocols,
            on_enter=on_enter,
            on_exit=on_exit,
            timeout_seconds=timeout_seconds
        )
    
    def unregister_state(self, name: str) -> bool:
        """
        Remove a state from the machine.
        
        Args:
            name: State name to remove
            
        Returns:
            bool: True if the state was removed
        """
        if name in self.states and name != self.current_state:
            del self.states[name]
            # Also remove any transitions involving this state
            self.transitions = [
                t for t in self.transitions
                if t.source != name and t.target != name
            ]
            return True
        return False
    
    def get_state_config(self, name: str) -> Optional[StateConfig]:
        """Get the configuration for a specific state."""
        return self.states.get(name)
    
    def get_current_state_config(self) -> Optional[StateConfig]:
        """Get the configuration for the current state."""
        return self.states.get(self.current_state)
    
    # ==========================================================================
    # TRANSITION MANAGEMENT
    # ==========================================================================
    
    def add_transition(self, transition: Transition) -> None:
        """
        Add a transition to the state machine.
        
        Args:
            transition: Transition object defining the state change
        """
        # Validate states exist
        if transition.source not in self.states:
            raise ValueError(f"Source state '{transition.source}' not registered")
        if transition.target not in self.states:
            raise ValueError(f"Target state '{transition.target}' not registered")
        
        self.transitions.append(transition)
        # Sort by priority (higher priority first)
        self.transitions.sort(key=lambda t: t.priority, reverse=True)
    
    def remove_transition(self, source: str, target: str, trigger: str) -> bool:
        """
        Remove a specific transition.
        
        Args:
            source: Source state name
            target: Target state name
            trigger: Trigger string
            
        Returns:
            bool: True if the transition was removed
        """
        initial_count = len(self.transitions)
        self.transitions = [
            t for t in self.transitions
            if not (t.source == source and t.target == target and t.trigger == trigger)
        ]
        return len(self.transitions) < initial_count
    
    def get_available_transitions(self, agent: Optional[Any] = None) -> List[Transition]:
        """
        Get all currently available transitions from the current state.
        
        Args:
            agent: Optional agent reference for condition evaluation
            
        Returns:
            List of transitions that can be taken
        """
        agent = agent or self._agent_ref
        available = []
        
        for transition in self.transitions:
            if transition.source == self.current_state:
                if transition.can_transition(agent):
                    available.append(transition)
        
        return available
    
    # ==========================================================================
    # TRIGGER HANDLING
    # ==========================================================================
    
    def trigger(self, trigger_name: str, agent: Optional[Any] = None) -> bool:
        """
        Fire a trigger event and potentially transition states.
        
        Args:
            trigger_name: Name of the trigger (e.g., 'input:user_message')
            agent: Optional agent reference for callbacks
            
        Returns:
            bool: True if a transition occurred
        """
        agent = agent or self._agent_ref
        
        for transition in self.transitions:
            if (transition.source == self.current_state and 
                transition.trigger == trigger_name and
                transition.can_transition(agent)):
                
                return self._execute_transition(transition, agent)
        
        return False
    
    def force_transition(self, target_state: str, agent: Optional[Any] = None) -> bool:
        """
        Force a transition to a target state without checking conditions.
        
        Args:
            target_state: State to transition to
            agent: Optional agent reference for callbacks
            
        Returns:
            bool: True if the transition occurred
        """
        if target_state not in self.states:
            return False
        
        agent = agent or self._agent_ref
        current_config = self.states.get(self.current_state)
        target_config = self.states.get(target_state)
        
        # Execute exit callback
        if current_config and current_config.on_exit:
            try:
                current_config.on_exit(agent)
            except Exception:
                pass
        
        # Update state
        self.previous_state = self.current_state
        self.current_state = target_state
        
        # Record history
        self._record_transition(
            self.previous_state, 
            self.current_state, 
            "forced"
        )
        
        # Execute enter callback
        if target_config and target_config.on_enter:
            try:
                target_config.on_enter(agent)
            except Exception:
                pass
        
        return True
    
    def _execute_transition(self, transition: Transition, agent: Any) -> bool:
        """Execute a transition and its callbacks."""
        current_config = self.states.get(self.current_state)
        
        # Execute on_exit for current state config
        if current_config and current_config.on_exit:
            try:
                current_config.on_exit(agent)
            except Exception:
                pass
        
        # Execute transition on_exit
        transition.execute_on_exit(agent)
        
        # Update state
        self.previous_state = self.current_state
        self.current_state = transition.target
        
        # Record history
        self._record_transition(
            self.previous_state,
            self.current_state,
            transition.trigger
        )
        
        # Execute transition on_enter
        transition.execute_on_enter(agent)
        
        # Execute on_enter for new state config
        target_config = self.states.get(self.current_state)
        if target_config and target_config.on_enter:
            try:
                target_config.on_enter(agent)
            except Exception:
                pass
        
        return True
    
    def _record_transition(self, source: str, target: str, trigger: str) -> None:
        """Record a transition in the history."""
        from datetime import datetime
        
        self.state_history.append({
            "from": source,
            "to": target,
            "trigger": trigger,
            "timestamp": datetime.now().isoformat()
        })
        
        # Keep history bounded
        if len(self.state_history) > 100:
            self.state_history = self.state_history[-50:]
    
    # ==========================================================================
    # UTILITY METHODS
    # ==========================================================================
    
    def set_agent_reference(self, agent: Any) -> None:
        """Set a reference to the agent for condition evaluation."""
        self._agent_ref = agent
    
    def get_current_instruction(self) -> str:
        """Get the instruction for the current state."""
        config = self.states.get(self.current_state)
        return config.instruction if config else ""
    
    def get_required_tools(self) -> List[str]:
        """Get the required tools for the current state."""
        config = self.states.get(self.current_state)
        return config.required_tools if config else []
    
    def get_protocol_query(self) -> Optional[str]:
        """Get the protocol query for the current state."""
        config = self.states.get(self.current_state)
        return config.protocols if config else None
    
    def get_state_timeout(self) -> Optional[float]:
        """Get the timeout for the current state."""
        config = self.states.get(self.current_state)
        return config.timeout_seconds if config else None
    
    def is_in_state(self, state_name: str) -> bool:
        """Check if currently in a specific state."""
        return self.current_state == state_name
    
    def get_all_states(self) -> List[str]:
        """Get a list of all registered state names."""
        return list(self.states.keys())
    
    def get_history(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Get recent state transition history."""
        return self.state_history[-limit:]
    
    def reset(self, initial_state: str = AgentState.IDLE.value) -> None:
        """
        Reset the state machine to an initial state.
        
        Args:
            initial_state: State to reset to
        """
        self.current_state = initial_state
        self.previous_state = None
        self.state_history.clear()
