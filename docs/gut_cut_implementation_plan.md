# 📋 Plano de Implementação: MBTDA Gut Cut (Manifest Edition)

## 🎯 Visão Geral
Evoluir a arquitetura do framework de um modelo imperativo ("Agente como Objeto Vivo") para um modelo **Declarativo e Orientado a Manifesto**. 

O `Agent` deixa de ser uma classe orquestradora e passa a ser um **Manifesto (Pydantic Model)**. Este manifesto é a "Palavra-Chave" (Single Source of Truth) que define a identidade, persona e capacidades do agente. Os componentes de Runtime (Memória, Workspace, Ferramentas) tornam-se responsáveis por rastrear e manter o estado de cada agente através de seu `agent_id`.

---

## 🧱 Fase 1: O Agente como Manifesto (Pydantic)
**Objetivo:** Transformar `src/agent.py` em um modelo de dados puro que define o "DNA" do agente.

1.  **Definição do `AgentManifest`**:
    *   Implementar como `pydantic.BaseModel`.
    *   **Identidade**: `agent_id` (UUID), `agent_name`, `version`.
    *   **Configuração Global de Componentes**: O manifesto deve conter a configuração completa de cada componente que o agente utilizará:
        *   **Contexto**: Blocos de prompt (`persona`, `tone`, `constraints`).
        *   **Ferramentas (ToolManager)**: Schemas das ferramentas, permissões e limites.
        *   **Intérprete (Sandbox)**: Caminhos de execução, módulos permitidos e restrições de segurança.
        *   **Memória**: Tipo de persistência, limites de tokens e política de retenção.
        *   **Modelos**: Provedor (Groq/Google), modelo específico e hiperparâmetros (temp, top_p).
        **E QUAISQUER OUTROS COMPONENTES QUE O AGENTE PODE UTILIZAR**
2.  **Serialização Total**: Garantir que o agente possa ser salvo em disco ou banco de dados apenas como um JSON/YAML, permitindo "congelar" e "descongelar" agentes sem dor de cabeça.

---

## 🧩 Fase 2: Componentes "Agent-Aware"
**Objetivo:** Refatorar componentes para que sejam orientados a configuração e usem o `agent_id` como chave de estado.

1.  **Tracking por ID**:
    *   Componentes como `MemoryManager` e `WorkspaceManager` deixam de ser "possuídos" pelo agente.
    *   Eles passam a receber o `AgentManifest` e usam o `agent_id` para localizar e gerenciar os dados específicos daquele agente.
2.  **Configuração Declarativa (Zero Imperatividade)**:
    *   Eliminar métodos como `set_system_prompt()` ou `register_tool()` em tempo de execução.
    *   O componente lê o Manifesto e se auto-configura inteiramente. Se algo não está no Manifesto, não existe para o componente.

---

## ⚙️ Fase 3: Runtime e Orquestração (Stateless)
**Objetivo:** Criar a camada de execução que processa o Manifesto.

1.  **AgentRuntime / Executor**:
    *   Uma classe leve que recebe um `AgentManifest` e as instâncias dos componentes de Runtime.
    *   Responsável apenas por executar o loop de raciocínio (LLM -> Tool -> LLM).
2.  **Multi-Instância Nativa**:
    *   A arquitetura permite que um mesmo Manifesto seja usado por múltiplos executores simultaneamente, ou que um executor troque de Manifesto "on the fly" apenas mudando a referência de dados.

---

## 🛠️ Fase 4: Persistência e Ciclo de Vida
**Objetivo:** Gerenciar a frota de agentes de forma persistente.

1.  **Agent Registry**: Sistema para carregar, validar e listar Manifestos disponíveis no sistema.
2.  **Vínculo de Estado Persistente**: Garantir que, ao reiniciar o sistema, o `agent_id` recupere automaticamente o histórico de mensagens e arquivos do workspace corretos.

---

## 📂 Fase 5: Limpeza de Interfaces e Código Morto
**Objetivo:** Remover as abstrações que se tornaram obsoletas com o modelo declarativo.

1.  **Remover `IRunner` e `Agent` antigo**: Deletar as implementações imperativas.
2.  **Simplificar `ITextClient`**: Ajustar para que o cliente LLM receba apenas o que o Manifesto dita.
3.  **Ajustar Testes**: Migrar toda a suíte de testes para validar Manifestos e a correta recuperação de estado via ID.
