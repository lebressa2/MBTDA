# Relatório de Análise da Arquitetura: Caminho para "Pure Python" Framework

## 1. Status Atual
A arquitetura atual do `MBTDA` já está **extremamente alinhada** com os princípios de *Ports and Adapters* (Arquitetura Hexagonal). O núcleo do sistema (`Agent`, `StateMachine`, `ContextManager`) está desacoplado de implementações específicas de IA.

### O Que Já Temos (Pontos Fortes)
*   **Independência do Core:** O `Agent` em `src/agent.py` não importa `openai` ou `langchain`. Ele depende estritamente das interfaces definidas em `src/interfaces/base.py`.
*   **Injeção de Dependência:** O `Agent` recebe `text_provider` e `tools` no construtor, permitindo que qualquqer implementação seja injetada.
*   **Abstrações Claras:** As interfaces `ITextClient`, `IToolManager`, `IContextProvider` fornecem fronteiras claras.

## 2. Análise de Gaps (O Que Falta)

### A. Dependência de Pydantic (O "Gap" Aceitável)
O núcleo (`src/models/data_models.py` e `src/components/context/manager.py`) depende fortemente de `pydantic`.
*   **Veredito:** Embora tecnicamente seja uma "lib externa", o Pydantic é considerado infraestrutura leve no ecosistema moderno de Python.
*   **Recomendação:** **Manter.** Tentar remover o Pydantic em favor de `dataclasses` puro traria uma complexidade de validação e serialização desnecessária. O ganho de ser "pure python" não compensa a perda de robustez aqui.

### B. Ausência de Adaptadores Padronizados
Atualmente, não existem implementações concretas (Adaptadores) dentro de `src/`. Se um usuário baixar o framework, ele tem as interfaces, mas não tem como "ligar" no OpenAI facilmente sem escrever sua própria classe.
*   **Gap:** Falta uma camada de `adapters` ou `plugins` que forneça as implementações padrão.

### C. Estratégia de Imports
Para que o framework seja instalável *sem* dependências pesadas (ex: `pip install mbtda`), mas funcione *com* elas se o usuário quiser (ex: `pip install mbtda[openai]`), precisamos ajustar como os adaptadores são expostos.

## 3. Plano de Ação

### Passo 1: Criar Estrutura de Adaptadores
Mover ou criar as implementações concretas para uma pasta dedicada que não é importada pelo `__init__.py` raiz por padrão.

```
src/
├── core/ (Agent, StateMachine - Zero Deps)
├── interfaces/ (Protocolos - Zero Deps)
└── adapters/ (Onde o "Caos" vive)
    ├── llm/
    │   ├── openai_adapter.py (Importa openai)
    │   └── anthropic_adapter.py (Importa anthropic)
    └── tools/
        └── langchain_adapter.py (Importa langchain)
```

### Passo 2: Implementar Lazy/Optional Imports
Esta é a chave para o seu objetivo. Nos arquivos de adaptadores, devemos usar imports dentro de blocos `try/except` ou verificações de tipo.

**Exemplo de Recomendação para `src/adapters/llm/openai_adapter.py`:**

```python
from typing import TYPE_CHECKING
from ...interfaces.base import ITextClient

# Lazy Import Strategy
try:
    import openai
    HAS_OPENAI = True
except ImportError:
    HAS_OPENAI = False

class OpenAIClient(ITextClient):
    def __init__(self, api_key: str):
        if not HAS_OPENAI:
            raise ImportError(
                "A biblioteca 'openai' é necessária para usar este adaptador. "
                "Instale com: pip install openai"
            )
        self.client = openai.Client(api_key=api_key)
```

## 4. Conclusão
Estamos a **90% do caminho**. O código "difícil" (o desacoplamento lógico) já foi feito. O trabalho restante é puramente de reorganização de arquivos e gestão de dependências opcionais.

### Roadmap Sugerido:
1.  **Reforçar o Core:** Garantir que `src/components` não vaze abstrações (ex: verificar se `context_manager.py` não está importando nada indevido).
2.  **Criar `src/adapters`:** Centralizar todas as integrações de terceiros lá.
3.  **Configurar `pyproject.toml`:** Definir *extras* para instalação opcional (ex: `pip install .[all]`).
