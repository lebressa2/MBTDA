# TRANSITIONS HANDLING
Eu estava pensando em criar dois modos de transição de estado. O modo atual onde o próprio agente usa self.state_machine.trigger('flag') Este seria o modo declativo onde o agente tem um workflow claro e definido, tipo sempre:

## GRAPH MODE

QUESTIONING -> SEARCHING -> PLANNING -> ACTION -> TESTING -> REVIEWING -> DOCUMENTING -> DEV OPS

- Example:
```python
from src.agent import Agent
from src.clients.llm.google_client import GoogleClient
from src.models.data_models import Transition

# Create agent
developer = Agent(text_provider=GoogleClient())

# Register GRAPH mode states
developer.state_machine.register_state(
    "QUESTIONING",
    "Clarifying requirements",
    required_tools=["ask_questions"]
)
developer.state_machine.register_state(
    "SEARCHING",
    "Finding information",
    required_tools=["web_search", "code_search"]
)
developer.state_machine.register_state(
    "PLANNING",
    "Creating strategy",
    required_tools=["analyze_requirements"]
)
developer.state_machine.register_state(
    "ACTION",
    "Implementing solution",
    required_tools=["code_generator", "file_writer"]
)
developer.state_machine.register_state(
    "TESTING",
    "Validating implementation",
    required_tools=["run_tests", "validate_code"]
)
developer.state_machine.register_state(
    "REVIEWING",
    "Code review process",
    required_tools=["code_analyzer"]
)
developer.state_machine.register_state(
    "DOCUMENTING",
    "Writing documentation",
    required_tools=["doc_generator"]
)
developer.state_machine.register_state(
    "DEV OPS",
    "Deployment operations",
    required_tools=["deploy_app", "monitor_logs"]
)

# Add transitions for the GRAPH mode workflow
developer.state_machine.add_transition(Transition(
    source="QUESTIONING",
    target="SEARCHING",
    trigger="goto_searching"
))
# ... outras transições
```

*But also thought about a more flexible mode where the agent can transit between states freely.*

## AUTO MODE

Este modo opera com base em uma segunda chamada de LLM, onde um modelo mais barato recebe um resumo do estado atual do agente e preenche essa ficha:

```python
class AgentStateCard(BaseModel):

    """Representa o estado atual e intenção do agente."""
    current_state: AgentState = Field(..., description="Estado atual do agente")
    
    desired_next_state: AgentState | None = Field(None, description="Estado desejado do agente")

    transition_reasoning: str = Field(..., description="Motivo da transição")
    
    state_confidence: float = Field(..., description="Quão 'certo' o agente está", ge=0, le=1)

    urgency_level: int = Field(..., description="Prioridade da transição", ge=1, le=5)

    contextual_factors: dict[str, Any] = Field(default_factory=dict, description="Fatores contextuais")

    should_continue_monitoring: bool = Field(..., description="Continuar monitorando")

    task_completion_estimate: int = Field(..., description="Estimativa de conclusão", ge=0, le=10)

    needs_human_intervention: bool = Field(..., description="Necessidade de intervenção humana")
```