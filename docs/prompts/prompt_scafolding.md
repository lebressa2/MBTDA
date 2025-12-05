# 📝 Especificação Completa da Classe `Agent` com Componentes `Inbox` e `TaskManager`


-----

### \#INSTRUÇÕES

Quero que faça uma classe Agent, bem encapsulada, que suporte os modos de operação Síncrono e Reativo, com os seguintes requisitos e componentes:

````python
class Agent:

# ------------------
# CORE COMPONENTS
# ------------------

- text_provider : ITextClient # Na aplicação pode usar langchain-groq, langchain-google dentro de um objeto, trabalha com langchain.BaseMessage

- context : ContextManager # Um objeto para controlar o dicionário python que será o prompt do sistema do agente:
```python
from pydantic import BaseModel
from typing import List, Optional, Dict

class ProtocolStep(BaseModel):
    name: str
    goal: str
    instructions: List[str]
    notes: Optional[str] = None

class Protocol(BaseModel):
    protocol_name: str
    description: str
    steps: List[ProtocolStep]

class ContextManager:
    base_formatter = DictToXMLFormatter()
    def __init__(self, formatter : IFormatter = base_formatter):
        # Correção: Inicializar protocols como um dicionário vazio
        self.context = {}
        self.protocols: Dict[str, Protocol] = {} # Dicionário de Protocolos
    def add(self, key, value):
        self.context[key] = value
    def get(self, key):
        return self.context.get(key, None)
    def remove(self, key):
        if key in self.context:
            del self.context[key]
    def populate_system_message(self, formatter : IFormatter) -> AIMessage:
        # A responsabilidade do ContextManager é formatar o contexto atual (incluindo protocolos e estado)
        return formatter.format(self.context) 

    def add_protocol(self, protocol : Protocol):
        self.protocols[protocol.protocol_name] = protocol
    
    def get_protocols(self, query : str) -> List[Protocol]:
        # Correção: Usar list comprehension para retornar uma lista válida
        return [ptc for ptc in self.protocols.values() if query.lower() in ptc.protocol_name.lower()]

    def remove_protocol(self, protocol_name : str):
        if protocol_name in self.protocols:
            del self.protocols[protocol_name]   
````

  - memory : IMemoryManager \# Preenche a chave 'memory' do Contexto, aplicação deve incluir Retrievers, short term memory, long term memory, etc

  - tools : IToolManager = [] \# register\_tool(context='retriever\_funcs', tool : langchain\_core.tools=Tool(...)). O Agente deve coletar as descrições das ferramentas disponíveis e injetá-las no prompt.

  - state\_machine : StateMachine \# Objeto essencial. Cada estado (ex: `THINKING`, `MONITORING`, `REQUEST_RECEIVED`) possui uma macro instrução.

<!-- end list -->

```python
# A StateMachine deve incluir estados para os dois modos de operação (IDLE, MONITORING, REQUEST_RECEIVED)
agent.state_machine.register_state('THINKING', 'Você é um Agente ReAct e está entrando no modo THINKING. Analise o contexto, formule hipóteses, avalie opções e planeje passos lógicos para decidir a próxima ação. Mantenha todo o raciocínio interno e não o revele ao usuário.', required_tools=['check_inbox'], protocols='my_protocol_query_here')

agent.state_machine.add_transition(
    Transition(
        source="WORKING",
        target="THINKING",
        condition=lambda ag: ag.protocols["analysis"].current_step_complete(),
        trigger="protocol:analysis",
        on_exit=lambda ag: ag.logger.debug("Análise concluída"),
        on_enter=lambda ag: ag.logger.debug("Voltando ao raciocínio..."),
    )
)

agent.state_machine.add_transition(
    Transition(
        source="THINKING",
        target="INTERRUPTED",
        trigger="watchdog:timeout",
        on_enter=lambda ag: ag.logger.warn("Agente excedeu tempo"),
    )
)
# A StateMachine deve ser configurada para transicionar entre os estados MONITORING e THINKING (via 'event:inbox_activity')
# e entre REQUEST_RECEIVED e THINKING (via 'input:user_message').
```

  - whatchdog : IWatchdog \# Interface deve incluir: `start_timer(duration_seconds)`, `stop_timer()`, `is_timed_out() -> bool` e `get_poll_interval() -> float` (para o modo reativo).

  - logger : ILogger \# Aplicação desse componente pode ser localhost, terminal, subprocess, etc (mas deve ter como ver os Thinking Tokens do agente, e as tool calls)

  - life\_manager : ILifeCycle \# Token Couting, Rate Limits, Resource Usage(memória, gpu para local), API Errors, message limits, etc. Deve ter métodos para configurar limites e guardrails focadas em recursos limitados

  - workspace\_manager : IWorkspaceManager

Responsável por gerenciar o ambiente isolado — físico ou virtual — em que o agente trabalha. Ele fornece ao agente uma sandbox controlada, permitindo criar, modificar e organizar arquivos, diretórios, branches de projeto, ou até operar dentro de ambientes computacionais dedicados, como shells virtuais, containers ou VMs leves.

Deve oferecer métodos para: criar, ler, editar e excluir arquivos e diretórios; realizar versionamento interno; operar ambientes computacionais isolados; registrar ações; impor limites de armazenamento e custo; permitir auditoria.

-----

### 🆕 Componentes de Monitoramento e Modelos de Dados

Para dar suporte aos requisitos de `Inbox` e `Tasks` no modo reativo, o agente deve usar as seguintes estruturas de dados e interfaces (via `IToolManager`):

#### 1\. Modelos de Dados (BaseModels)

Define a estrutura dos dados que ativam o modo reativo:

```python
class EmailMessage(BaseModel):
    subject: str
    sender: str
    body_snippet: str
    is_urgent: bool
    thread_id: str

class TaskItem(BaseModel):
    task_id: str
    title: str
    due_date: Optional[str]
    priority: int
    status: str
```

#### 2\. Interfaces de Observação (Integração com Tools)

O acesso à Inbox e Tasks deve ser fornecido por **Ferramentas** registradas no `IToolManager`, mas a interface lógica pode ser definida:

  - **inbox\_tool:** Uma ferramenta no `IToolManager` que usa a interface `IInboxClient`.
  - **task\_tool:** Uma ferramenta no `IToolManager` que usa a interface `ITaskManager`.

A ferramenta (`Tool`) deve encapsular os seguintes métodos/capacidades:

  - **IInboxClient (Capacidade):**
      - `check_new_emails() -> List[EmailMessage]`
      - `send_email(...)`
  - **ITaskManager (Capacidade):**
      - `get_pending_tasks() -> List[TaskItem]`
      - `create_task(...)`
      - `update_task_status(...)`

-----

### 3\. ⚙️ Métodos de Execução (Controle de Fluxo)

A classe `Agent` é o orquestrador dos dois modos de operação, ambos utilizando o *kernel* de raciocínio da `StateMachine`.

```python
# MÉTODOS DE EXECUÇÃO ADICIONAIS NA CLASSE AGENT

def process_message(self, input_message: str, chat_history: Optional[List[BaseMessage]] = None) -> BaseMessage:
    """
    MODO SÍNCRONO (Request/Response).
    Executa uma única iteração (ou loop ReAct completo) para gerar uma resposta ao usuário.
    1. O método deve transicionar a StateMachine (e.g., disparar o 'input:user_message').
    2. Orquestra o ciclo LLM -> Tools -> LLM.
    """
    pass # Implementação deve orquestrar LLM, Tools e StateMachine.

def start_monitoring(self, sources: List[str] = ['inbox', 'tasks']):
    """
    MODO REATIVO (Monitoring/Event-Driven).
    Inicia um loop contínuo de observação (polling/eventos) focado em fontes como Inbox e Tasks.
    
    1. O método é responsável por transicionar a StateMachine para o estado 'MONITORING'.
    2. Utiliza o IWatchdog para controle de polling/loop e intervalos de verificação.
    3. **Deve observar explicitamente a Inbox e Tasks** usando as ferramentas/clientes apropriados.
    4. Se um evento for detectado (e.g., email novo ou Task vencida), deve chamar o self.process_event(event).
    """
    pass # Implementação deve usar o IWatchdog para controle de polling/loop.

def process_event(self, event: Any):
    """
    Método auxiliar chamado pelo start_monitoring() quando um evento (EmailMessage ou TaskItem) é detectado.
    Dispara o ciclo de raciocínio ReAct (THINKING -> WORKING) focado no evento recebido, atualizando a StateMachine e a Memória.
    """
    pass # Implementação
```