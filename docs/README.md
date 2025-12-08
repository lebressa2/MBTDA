# 🤖 Agent Framework

**O 'React' da Engenharia de Contexto.**

## 📋 Visão Geral

Este framework não é apenas mais uma ferramenta para criar agentes; é uma mudança de paradigma na forma como lidamos com LLMs.

Assim como o **React** transformou o desenvolvimento frontend de páginas estáticas para interfaces dinâmicas e reativas baseadas em componentes, este framework visa transformar a **Engenharia de Contexto**.

Na abordagem tradicional, agentes operam com um contexto predominantemente estático (um System Prompt fixo somado a um histórico linear de mensagens). Este framework propõe um contexto **dinâmico e vivo**.

Através de **Estados** e **Componentes** especializados que contribuem em *realtime* para a construção do prompt, o contexto do agente é "renderizado" dinamicamente a cada ciclo. Isso permite que o agente adapte sua persona, recursos disponíveis, memórias relevantes e instruções sistema, momento a momento, dependendo do estado atual da aplicação.

### Modos de Operação

| Modo | Descrição | Método Principal |
|------|-----------|------------------|
| **Síncrono** | Request/Response - Processa mensagens individuais | `process_message()` |
| **Reativo** | Monitoring/Event-Driven - Observa fontes de eventos continuamente | `start_monitoring()` |

## 🏗️ Arquitetura

```
src/
├── agent.py              # Classe principal Agent
├── interfaces/           # Interfaces (Protocolos ABC)
│   └── base.py          # ITextClient, IToolManager, ILogger, etc.
├── models/              # Modelos Pydantic
│   └── data_models.py   # EmailMessage, TaskItem, Protocol, Transition
├── components/          # Implementações dos componentes
│   ├── context_manager.py
│   ├── state_machine.py
│   ├── watchdog.py
│   ├── logger.py
│   ├── lifecycle.py
│   ├── workspace.py
│   ├── memory.py
│   └── tools.py
└── clients/             # Clientes de monitoramento
    ├── inbox_client.py
    └── task_client.py
```

## 🧩 Componentes

### Core Components

| Componente | Interface | Descrição |
|------------|-----------|-----------|
| `text_provider` | `ITextClient` | Cliente LLM (langchain-groq, langchain-google, etc.) |
| `context` | `ContextManager` | **Renderizador de Contexto**. Centraliza a montagem do System Prompt. |
| `memory` | `IMemoryManager` | Injeta memórias e contexto relevante dinamicamente. |
| `tools` | `IToolManager` | Registro e execução de ferramentas |
| `state_machine` | `StateMachine` | Gerencia **Estados** que alteram radicalmente o comportamento/instruções. |
| `watchdog` | `IWatchdog` | Timer e controle de polling |
| `logger` | `ILogger` | Logging de thinking tokens e tool calls |
| `life_manager` | `ILifeCycle` | Token counting, rate limits, recursos |
| `workspace_manager` | `IWorkspaceManager` | Ambiente isolado para operações |

### Monitoring Components

| Componente | Interface | Descrição |
|------------|-----------|-----------|
| `inbox_client` | `IInboxClient` | Monitoramento de emails |
| `task_client` | `ITaskManager` | Gerenciamento de tarefas |

## 📖 Uso

### Modo Síncrono

```python
from src.agent import Agent
from src.components import ConsoleLogger, InMemoryManager

# Criar agente
agent = Agent(
    text_provider=my_llm_client,
    logger=ConsoleLogger(),
    memory=InMemoryManager()
)

# Processar mensagem
response = agent.process_message("Olá, como você pode me ajudar?")
print(response)
```

### Modo Reativo

```python
from src.agent import Agent
from src.components import Watchdog
from src.clients import MockInboxClient, MockTaskClient

# Criar agente com clientes de monitoramento
agent = Agent(
    text_provider=my_llm_client,
    watchdog=Watchdog(poll_interval=30.0),
    inbox_client=MockInboxClient(),
    task_manager=MockTaskClient()
)

# Iniciar monitoramento
agent.start_monitoring(sources=['inbox', 'tasks'])
```

### State Machine

```python
from src.components import StateMachine
from src.models import Transition

# Registrar estado customizado
agent.state_machine.register_state(
    name='CUSTOM_STATE',
    instruction='Instrução para este estado...',
    required_tools=['tool_name'],
    protocols='query_protocols'
)

# Adicionar transição
agent.state_machine.add_transition(Transition(
    source="THINKING",
    target="CUSTOM_STATE",
    trigger="custom:trigger",
    condition=lambda ag: some_condition(ag)
))
```

### Protocolos

```python
from src.models import Protocol, ProtocolStep

# Criar protocolo
protocol = Protocol(
    protocol_name="analysis",
    description="Protocolo para análise de dados",
    steps=[
        ProtocolStep(
            name="collect",
            goal="Coletar dados necessários",
            instructions=["Identificar fontes", "Extrair dados"]
        ),
        ProtocolStep(
            name="analyze",
            goal="Analisar os dados",
            instructions=["Aplicar métodos", "Gerar insights"]
        )
    ]
)

agent.add_protocol(protocol)
```

## 🚀 Demo

Execute o script de demonstração:

```bash
python demo.py
```

## 📄 Modelos de Dados

### EmailMessage
```python
class EmailMessage(BaseModel):
    subject: str
    sender: str
    body_snippet: str
    is_urgent: bool
    thread_id: str
```

### TaskItem
```python
class TaskItem(BaseModel):
    task_id: str
    title: str
    due_date: Optional[str]
    priority: int  # 1-5
    status: str    # pending, in_progress, completed
```

### Protocol & ProtocolStep
```python
class ProtocolStep(BaseModel):
    name: str
    goal: str
    instructions: List[str]
    notes: Optional[str]

class Protocol(BaseModel):
    protocol_name: str
    description: str
    steps: List[ProtocolStep]
```

## 🔧 Estados Padrão

| Estado | Descrição |
|--------|-----------|
| `IDLE` | Aguardando instruções |
| `THINKING` | Modo ReAct - análise e planejamento |
| `WORKING` | Executando ações |
| `MONITORING` | Observando fontes de eventos |
| `REQUEST_RECEIVED` | Nova requisição recebida |
| `INTERRUPTED` | Operação interrompida |
| `ERROR` | Estado de erro |
| `SHUTDOWN` | Encerrando |

## 🧪 Testes

O framework inclui uma suíte completa de testes que valida a integração de todos os componentes usando APIs reais de LLM (Groq e Google).

### Estrutura de Testes

```
tests/
├── clients.py               # Implementações reais de ITextClient (Groq/Google)
├── test_agent_framework.py  # Testes de integração do framework
└── run_all_tests.py         # Runner de todos os testes
```

### Cobertura de Testes

Os testes validam os seguintes cenários usando modelos reais (Qwen/Llama via Groq ou Gemini via Google):

1. **Agente Básico**: Ciclo de vida request/response simples.
2. **Memória**: Persistência de contexto e recuperação de informações (Short-term/Long-term).
3. **Ferramentas**: Registro e execução de ferramentas (Math, Utility) via function calling.
4. **Workspace**: Operações de arquivo e diretório em ambiente isolado.
5. **Protocolos**: Gerenciamento e execução de protocolos definidos.
6. **Máquina de Estados**: Transições corretas entre estados (IDLE -> THINKING -> WORKING).
7. **Integração Completa**: Agente com todos os componentes ativos simultaneamente.

### Executando os Testes

Certifique-se de ter as chaves de API configuradas no `.env`:

```env
GROQ_API_KEY=seu_key_aqui
GOOGLE_API_KEY=seu_key_aqui
```

Execute a suíte completa:

```bash
python tests/run_all_tests.py
```

Ou testes específicos:

```bash
python tests/test_agent_framework.py --full
python tests/test_agent_framework.py --memory
python tests/test_agent_framework.py --tools
```

## 📦 Dependências

```
pydantic>=2.0.0
langchain>=0.1.0
langchain-groq>=0.1.0
langchain-google-genai>=0.1.0
```

## 📝 Licença

MIT License
