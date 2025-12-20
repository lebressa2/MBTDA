# 📋 Plano de Implementação: MBTDA Gut Cut (Manifest Edition)

## 🎯 Visão Geral
Evoluir a arquitetura do framework de um modelo imperativo ("Agente como Objeto Vivo") para um modelo **Declarativo e Orientado a Manifesto**. 

O `Agent` deixa de ser uma classe orquestradora e passa a ser um **Manifesto (Pydantic Model)**. Este manifesto é o "DNA" (Single Source of Truth) que define a identidade e capacidades do agente. O estado vivo e a orquestração são movidos para a **Session**, que atua como o meio-campo entre o Manifesto estático e os componentes de Runtime.

### 🏗️ Arquitetura Proposta: Stateless vs Stateful
Para evitar overengineering, não utilizaremos interfaces complexas para distinguir tipos de componentes. A distinção será lógica e baseada na responsabilidade:

1.  **Stateless Components**: Processam dados baseados apenas na configuração do Manifesto (ex: `TextClient`, `ContextFormatter`).
2.  **Stateful Components**: Gerenciam dados que persistem entre execuções (ex: `MemoryManager`, `WorkspaceManager`), utilizando o `agent_id` ou `session_id` como chave.
3.  **Session (Mediador)**: O "Agente Vivo". Carrega o manifesto, inicializa os componentes necessários baseados nas configurações e mantém o vínculo com o estado persistente.

---

## 🧱 Fase 1: O Agente como Manifesto (Pydantic)
**Objetivo:** Transformar `src/agent.py` em um modelo de dados puro e exaustivo.

1.  **Definição do `AgentManifest`**:
    *   **Identidade**: `agent_id` (UUID), `agent_name`, `version`, `metadata`.
    *   **LLMConfig**: Provedor, modelo, temperatura, top_p, max_tokens.
    *   **ContextConfig**: Blocos de prompt (`persona`, `tone`, `constraints`, `custom_blocks`).
    *   **ToolConfig**: Schemas das ferramentas, permissões e política de execução.
    *   **MemoryConfig**: Estratégia de persistência, limites e política de retenção.
    *   **WorkspaceConfig**: Caminhos, restrições de sandbox e extensões permitidas.

2.  **Serialização Total**: Métodos `to_json()` e `from_json()` robustos para permitir o congelamento absoluto de agentes.

---

## 🔗 Fase 2: Session e Inicialização Dinâmica
**Objetivo:** Criar o mediador de estado que "hidrata" o Manifesto.

1.  **Implementação da `AgentSession`**:
    *   Atuar como o ponto de entrada principal para execução.
    *   Receber um `AgentManifest` e um `session_id`.
    *   **Auto-Configuração**: Inicializar os componentes (Memory, Workspace, Tools) lendo diretamente as configurações contidas no Manifesto.
    *   **Lifecycle**: Gerenciar o "warm-up" e "cool-down" dos componentes stateful.

2.  **Componentes "Agent-Aware"**:
    *   Refatorar os managers para que operem baseados em chaves de estado (`agent_id`/`session_id`).
    *   Eliminar métodos imperativos de registro (`register_tool`, `set_prompt`) em favor da leitura do manifesto no momento da criação da sessão.

---

## ⚙️ Fase 3: Runtime de Execução (Executor Procedural)
**Objetivo:** Isolar a lógica de processamento do LLM em um executor stateless.

1.  **AgentRuntime**:
    *   Transformar em um executor procedural que recebe a `Session` (ou o Manifesto + Componentes).
    *   Focar puramente no loop: `Context Build -> LLM Invoke -> Tool Logic -> Observation -> Memory Save`.

2.  **Multi-Instância e Idempotência**:
    *   Garantir que múltiplas sessões possam rodar o mesmo Manifesto simultaneamente sem colisão de estado, graças ao isolamento via `session_id`.

---

## 🛠️ Fase 4: Persistência e Registro (Fleet Management)
**Objetivo:** Gerenciar a frota de manifestos e a recuperação de estado.

1.  **Agent Registry**:
    *   Sistema para carregar manifestos de arquivos `.json` ou bancos de dados.
    *   Validação estrita de schemas antes da inicialização.

2.  **Persistence Layer**:
    *   Garantir que um componente stateful (ex: `MemoryManager`) consiga recuperar as mensagens de um `agent_id` específico mesmo após um restart completo do sistema.

---

## 📂 Fase 5: Limpeza e Estabilização
**Objetivo:** Remover o "código morto" da arquitetura antiga.

1.  **Remoção de Interfaces Obsoletas**: Deletar `IRunner` e as implementações imperativas de `Agent`.
2.  **Ajuste da Suite de Testes**: Focar na validação da serialização (Manifesto) e da correta reidratação do estado via Session.
3.  **Documentação de Componentes**: Documentar como cada componente lê sua fatia do DNA no manifesto.

