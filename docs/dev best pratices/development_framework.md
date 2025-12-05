# 🏢 Guia Completo: Organização de Projeto Como Equipe Real

## 📋 Índice

1. [Estrutura de Papéis](#estrutura-de-papéis)
2. [Estrutura de Repositório](#estrutura-de-repositório)
3. [Git Workflow](#git-workflow)
4. [Architecture Decision Records (ADRs)](#adrs)
5. [Testing Strategy](#testing-strategy)
6. [CI/CD - Guia Completo para Iniciantes](#cicd-guia-completo)
7. [Gestão de Projeto](#gestão-de-projeto)
8. [Segredos e Configuração](#segredos-e-configuração)
9. [Monitoramento](#monitoramento)
10. [Ritmo de Trabalho](#ritmo-de-trabalho)
11. [Release Management](#release-management)
12. [Checklist Final](#checklist-final)

---

## 1. 🎭 Estrutura de Papéis {#estrutura-de-papéis}

Mesmo trabalhando solo, você precisa **separar responsabilidades mentalmente**:

### **Segunda/Quarta: Founder/PM Hat** 🎯

**O que faz:** Decide o QUE construir e POR QUÊ

- **Manhã (2h):** Conversar com usuários, validar hipóteses
- **Tarde (1h):** Priorizar roadmap, criar/atualizar issues no GitHub
- **Output:** Issues priorizados, decisões documentadas

**Pergunta-chave:** "Isso resolve um problema real do usuário?"

---

### **Terça/Quinta: Tech Lead Hat** 👨‍💻

**O que faz:** Decide COMO construir

- **Manhã (3h):** Programação focada (deep work, sem distrações)
- **Tarde (1h):** Revisar próprio código de ontem
- **Output:** Pull Requests com testes, documentação técnica

**Pergunta-chave:** "Isso é maintainable e escalável?"

---

### **Sexta: DevOps/QA Hat** 🔧

**O que faz:** Garante que FUNCIONA em produção

- **Manhã (2h):** Monitorar logs, erros, custos de API
- **Tarde (1h):** Refactoring, pagar dívida técnica
- **Output:** Sistema estável, CI/CD funcionando

**Pergunta-chave:** "Se isso quebrar às 3h da manhã, eu vou saber?"

---

## 2. 📁 Estrutura de Repositório {#estrutura-de-repositório}

```
agent-framework/
├── .github/                    # Configurações do GitHub
│   ├── workflows/              # CI/CD (explicado na seção 6)
│   │   ├── tests.yml           # Roda testes automaticamente
│   │   ├── deploy.yml          # Deploy automático
│   │   └── cost-report.yml     # Relatório semanal de custos
│   └── PULL_REQUEST_TEMPLATE.md # Template de PR
│
├── docs/                       # Documentação
│   ├── architecture/
│   │   ├── decisions/          # ADRs (seção 4)
│   │   │   ├── 001-why-state-machine.md
│   │   │   ├── 002-multi-llm-strategy.md
│   │   │   └── 003-memory-architecture.md
│   │   └── diagrams/           # Diagramas (draw.io, mermaid)
│   ├── api/                    # Documentação da API
│   └── guides/                 # Tutoriais de uso
│
├── src/                        # Código-fonte
│   ├── agent_framework/
│   │   ├── __init__.py
│   │   ├── core/               # Componentes principais
│   │   │   ├── agent.py
│   │   │   ├── state_machine.py
│   │   │   └── context.py
│   │   ├── providers/          # Implementações
│   │   │   ├── llm/            # Clientes de LLM
│   │   │   │   ├── base.py     # Interface
│   │   │   │   ├── claude.py
│   │   │   │   ├── gemini.py
│   │   │   │   └── groq.py
│   │   │   ├── memory/
│   │   │   │   ├── base.py
│   │   │   │   ├── in_memory.py
│   │   │   │   └── supabase.py
│   │   │   └── workspace/
│   │   │       ├── base.py
│   │   │       ├── local.py
│   │   │       └── docker.py
│   │   ├── tools/              # Ferramentas (Gmail, Todoist, etc)
│   │   │   ├── base.py
│   │   │   ├── gmail.py
│   │   │   └── todoist.py
│   │   └── utils/              # Utilitários
│   │       ├── logger.py
│   │       ├── lifecycle.py
│   │       └── watchdog.py
│   └── cli/                    # Interface de linha de comando
│       └── main.py
│
├── templates/                  # Templates de agentes prontos
│   ├── email_triage/
│   │   ├── config.yaml
│   │   ├── states.yaml
│   │   └── protocols.yaml
│   └── meeting_prep/
│
├── tests/                      # Testes (seção 5)
│   ├── unit/                   # Rápidos, sem APIs reais
│   ├── integration/            # Com APIs reais
│   └── e2e/                    # Fluxo completo
│
├── examples/                   # Exemplos de uso
│   └── quickstart.ipynb
│
├── .env.example                # Template de variáveis de ambiente
├── .gitignore                  # Arquivos ignorados pelo Git
├── pyproject.toml              # Dependências do projeto (Poetry)
├── Makefile                    # Comandos úteis
├── README.md                   # Documentação principal
└── CHANGELOG.md                # Histórico de mudanças
```

---

## 3. 🔄 Git Workflow {#git-workflow}

### **O que é Git?**

Git é um sistema de controle de versão. Pense nele como um "histórico de Ctrl+Z infinito" para seu código.

### **Estrutura de Branches (Galhos)**

```
main              # Produção (código que está rodando de verdade)
├── develop       # Integração (código pronto mas em testes)
└── feature/*     # Features individuais (ex: feature/add-protocols)
```

**Analogia:** Imagine que `main` é a versão publicada do seu livro, `develop` é o rascunho quase pronto, e `feature/novo-capitulo` é onde você escreve um capítulo específico.

---

### **Workflow Diário (Passo a Passo)**

#### **1. Começar uma nova feature**

```bash
# 1. Ir para a branch develop
git checkout develop

# 2. Baixar últimas mudanças
git pull

# 3. Criar nova branch para sua feature
git checkout -b feature/add-protocol-system

# Agora você está em uma "cópia isolada" do código
# Pode fazer mudanças sem afetar o código principal
```

**No GitHub:** Criar issue correspondente

- Título: `[FEATURE] Add Protocol System to ContextManager`
- Labels: `enhancement`, `priority:high`
- Assignee: você

---

#### **2. Fazer commits (salvar progresso)**

```bash
# Após escrever código, salvar mudanças:
git add .                              # Adiciona todos arquivos modificados
git commit -m "feat(context): add Protocol model"

# Tipos de commit (Conventional Commits):
# feat:     nova funcionalidade
# fix:      correção de bug
# docs:     documentação
# test:     testes
# refactor: melhorar código sem mudar comportamento
# chore:    tarefas de manutenção (atualizar deps, etc)
```

**Exemplo de sequência de commits:**

```bash
git commit -m "feat(context): add Protocol and ProtocolStep models"
git commit -m "feat(context): implement add_protocol method"
git commit -m "test(context): add unit tests for protocols"
git commit -m "docs(context): document protocol system"
```

**Por que isso importa?**

- Histórico organizado
- Fácil entender o que mudou
- Possível reverter mudanças específicas

---

#### **3. Abrir Pull Request (PR)**

**O que é um PR?**
É um pedido para "juntar" seu código na branch principal. Mesmo trabalhando solo, PRs são úteis para:

- Forçar você a revisar próprio código
- Rodar testes automaticamente (CI)
- Documentar mudanças

```bash
# 1. Enviar branch para GitHub
git push origin feature/add-protocol-system

# 2. No GitHub, clicar em "Compare & Pull Request"

# 3. Preencher template:
```

**Template de PR:**

```markdown
## O que mudou?

Adicionei sistema de Protocols ao ContextManager para permitir
agentes usarem protocolos reutilizáveis.

## Por quê?

Issue #12 - usuários pediam forma de compartilhar "receitas"
entre agentes.

## Como testar?

python -m pytest tests/unit/test_context.py

## Checklist

- [x] Testes adicionados
- [x] Documentação atualizada
- [x] Sem breaking changes
```

---

#### **4. Code Review (revisar próprio código)**

**Truque:** Espere 24h antes de revisar. Seu cérebro vai encontrar problemas que você não viu quando escreveu.

**O que verificar:**

- [ ] Código fácil de entender?
- [ ] Nomes de variáveis claros?
- [ ] Funções pequenas (<50 linhas)?
- [ ] Testes cobrem casos importantes?
- [ ] Documentação explica o "por quê"?

---

#### **5. Merge (juntar código)**

```bash
# Após PR aprovado (por você mesmo 😄):
# No GitHub, clicar "Merge Pull Request"

# Depois, atualizar sua branch local:
git checkout develop
git pull
```

---

### **Comandos Git Essenciais**

```bash
# Ver status (arquivos modificados)
git status

# Ver histórico de commits
git log --oneline

# Ver mudanças não commitadas
git diff

# Desfazer mudanças (antes de commit)
git checkout -- arquivo.py

# Desfazer último commit (mantém mudanças)
git reset --soft HEAD~1

# Atualizar branch com mudanças do develop
git checkout feature/minha-feature
git merge develop

# Ver todas branches
git branch -a
```

---

## 4. 📝 Architecture Decision Records (ADRs) {#adrs}

### **O que são ADRs?**

Documentos curtos explicando **por que** você tomou uma decisão técnica importante.

**Quando criar um ADR:**

- Escolheu usar X em vez de Y (ex: Docker vs VM)
- Mudou arquitetura significativamente
- Decisão que vai impactar o projeto por meses

---

### **Template de ADR**

**Arquivo:** `docs/architecture/decisions/002-multi-llm-strategy.md`

```markdown
# ADR-002: Multi-LLM Strategy por Estado

## Status

Accepted ✅
(Outros status possíveis: Proposed, Rejected, Deprecated)

## Context

Por que essa decisão foi necessária?

Agentes precisam otimizar custo vs performance. Observamos que:

- Claude Opus 4.5: excelente raciocínio, mas $15/1M tokens input
- Gemini Flash 2.0: rápido e barato, mas raciocínio mais fraco
- Groq Llama 3.3: inference grátis, mas sem suporte a tools complexos

## Decision

O que decidimos fazer?

Permitir configurar LLM diferente por estado da StateMachine:

- Estado THINKING → Claude Opus 4.5 (raciocínio profundo)
- Estado MONITORING → Gemini Flash (polling barato)
- Estado WORKING → Groq (tool calling veloz)

## Consequences

Que impacto isso tem?

### Positivo ✅

- Usuários podem otimizar custo (polling 24/7 não fica caro)
- Flexibilidade para adicionar novos LLMs no futuro
- Performance melhor (estado certo usa LLM certo)

### Negativo ⚠️

- Complexidade aumenta (precisa gerenciar 3+ clientes LLM)
- Testes precisam rodar em cada LLM
- Usuários podem se confundir com muitas opções

## Implementation

Onde está implementado?

- PR #23: `src/agent_framework/providers/llm/`
- Tests: `tests/integration/test_multi_llm.py`
- Docs: Atualizado README com exemplos

## Alternatives Considered

Que outras opções avaliamos?

### Opção 1: Usar só Claude Opus

**Prós:** Simples, melhor qualidade
**Contras:** Custo alto para polling ($150/mês por agente)
**Por que não:** Inviável para scale

### Opção 2: Deixar usuário escolher 1 LLM global

**Prós:** UI mais simples
**Contras:** Sem otimização de custo
**Por que não:** Perde principal benefício da arquitetura
```

---

### **ADRs Sugeridos para seu Projeto**

1. **ADR-001:** Por que State Machines em vez de código imperativo?
2. **ADR-002:** Multi-LLM strategy (exemplo acima)
3. **ADR-003:** Memory architecture (short-term vs long-term)
4. **ADR-004:** Protocol system design
5. **ADR-005:** Workspace isolation (Docker vs local filesystem)

---

## 5. 🧪 Testing Strategy {#testing-strategy}

### **Pirâmide de Testes**

```
         /\
        /E2E\        ← 10% dos testes (caros, lentos, frágeis)
       /------\         Testam fluxo completo do usuário
      /  INT   \     ← 20% dos testes (médios, com APIs reais)
     /----------\        Testam integração entre componentes
    /   UNIT     \   ← 70% dos testes (rápidos, isolados)
   /--------------\      Testam funções individuais
```

**Por que essa proporção?**

- Testes unitários são rápidos (rodam em segundos)
- Testes E2E são lentos (rodam em minutos) e quebram fácil
- Você quer feedback rápido no dia-a-dia

---

### **1. Testes Unitários (70% dos testes)**

**Características:**

- Testam 1 função/classe isoladamente
- Não chamam APIs reais (usam mocks)
- Rodam em <5 segundos

**Exemplo:** `tests/unit/test_state_machine.py`

```python
import pytest
from agent_framework.core.state_machine import StateMachine, State

def test_state_registration():
    """Testa se consegue registrar um estado"""
    sm = StateMachine()
    sm.register_state('THINKING', 'Analyze and plan')

    # Assertions (verificações)
    assert 'THINKING' in sm.states
    assert sm.states['THINKING'].instruction == 'Analyze and plan'

def test_transition_triggers():
    """Testa se transições funcionam"""
    sm = StateMachine()
    sm.register_state('IDLE', '')
    sm.register_state('THINKING', '')
    sm.add_transition('IDLE', 'THINKING', trigger='input:user_message')

    assert sm.can_transition('IDLE', 'input:user_message')
    assert not sm.can_transition('IDLE', 'event:random')

def test_invalid_transition():
    """Testa que transição inválida lança erro"""
    sm = StateMachine()
    sm.register_state('IDLE', '')

    with pytest.raises(ValueError):
        sm.transition_to('NONEXISTENT_STATE')
```

**Como rodar:**

```bash
pytest tests/unit -v
# -v = verbose (mostra detalhes)
```

---

### **2. Testes de Integração (20% dos testes)**

**Características:**

- Testam integração entre componentes
- Chamam APIs reais (Gmail, Anthropic, etc)
- Rodam em ~30 segundos

**Exemplo:** `tests/integration/test_gmail_tool.py`

```python
import pytest
import os

# Marca teste como "integration" (explicado depois)
@pytest.mark.integration
# Pula teste se não tiver credenciais
@pytest.mark.skipif(
    not os.getenv('GMAIL_CREDENTIALS'),
    reason="No Gmail credentials"
)
def test_gmail_check_inbox():
    """Testa se consegue ler inbox real do Gmail"""
    from agent_framework.tools.gmail import GmailTool

    tool = GmailTool(credentials=os.getenv('GMAIL_CREDENTIALS'))
    emails = tool.check_new_emails(limit=5)

    # Verificações
    assert isinstance(emails, list)
    if emails:  # Se tiver emails
        assert 'subject' in emails[0]
        assert 'sender' in emails[0]
        assert 'body_snippet' in emails[0]

@pytest.mark.integration
def test_claude_reasoning():
    """Testa se Claude consegue raciocinar"""
    from agent_framework.providers.llm.claude import ClaudeClient

    client = ClaudeClient(api_key=os.getenv('ANTHROPIC_API_KEY'))
    response = client.generate(
        messages=[{"role": "user", "content": "What is 2+2?"}]
    )

    assert '4' in response.content
```

**Como rodar:**

```bash
# Só testes de integração
pytest tests/integration -v -m integration

# Com variáveis de ambiente
ANTHROPIC_API_KEY=sk-ant-... pytest tests/integration -v
```

---

### **3. Testes E2E (10% dos testes)**

**Características:**

- Testam fluxo completo do usuário
- Simulam uso real do sistema
- Rodam em minutos

**Exemplo:** `tests/e2e/test_email_agent_flow.py`

```python
import pytest
from agent_framework import Agent
from agent_framework.providers.llm.claude import ClaudeClient
from agent_framework.tools.gmail import GmailTool

@pytest.mark.e2e
@pytest.mark.slow
def test_email_triage_agent_full_flow():
    """
    Testa fluxo completo:
    1. Agente inicia monitoring
    2. Detecta email novo
    3. Decide criar task no Todoist
    4. Executa ação
    """
    # Setup
    agent = Agent(
        text_provider=ClaudeClient(),
        tools=[GmailTool(), TodoistTool()]
    )

    # Simular email novo chegando
    agent.start_monitoring(sources=['inbox'])

    # Aguardar processamento (max 30 segundos)
    import time
    timeout = 30
    start = time.time()

    while time.time() - start < timeout:
        if agent.state == 'IDLE':  # Processou e voltou
            break
        time.sleep(1)

    # Verificações
    assert agent.last_action == 'create_task'
    assert len(agent.memory.get('tasks_created')) > 0
```

**Como rodar:**

```bash
pytest tests/e2e -v --slow
```

---

### **Organizando Testes com Makefile**

**Arquivo:** `Makefile`

```makefile
.PHONY: test test-unit test-integration test-e2e test-watch

# Roda só testes unitários (rápido, dia-a-dia)
test-unit:
	pytest tests/unit -v

# Roda testes de integração (APIs reais)
test-integration:
	pytest tests/integration -v -m integration

# Roda testes E2E (fluxo completo)
test-e2e:
	pytest tests/e2e -v --slow

# Roda tudo (CI vai usar esse)
test: test-unit test-integration

# Watch mode (re-roda testes quando código muda)
test-watch:
	pytest-watch tests/unit
```

**Uso:**

```bash
make test-unit           # Desenvolvimento diário
make test                # Antes de fazer PR
make test-e2e            # Antes de deploy
```

---

### **pytest.ini (Configuração de Testes)**

**Arquivo:** `pytest.ini`

```ini
[pytest]
# Markers (tags) para organizar testes
markers =
    unit: Testes unitários rápidos
    integration: Testes com APIs reais
    e2e: Testes end-to-end completos
    slow: Testes que demoram >10 segundos

# Onde procurar testes
testpaths = tests

# Opções padrão
addopts =
    --strict-markers
    --tb=short
    -ra
```

**Agora você pode rodar:**

```bash
pytest -m unit              # Só unitários
pytest -m integration       # Só integração
pytest -m "not slow"        # Tudo exceto lentos
```

---

## 6. 🚀 CI/CD - Guia Completo para Iniciantes {#cicd-guia-completo}

### **O que é CI/CD?**

**CI (Continuous Integration):**
"Integração Contínua" - toda vez que você faz um commit, testes rodam automaticamente.

**CD (Continuous Deployment):**
"Deploy Contínuo" - se testes passarem, código vai automaticamente para produção.

**Analogia:**
Imagine uma fábrica onde:

- **CI:** Cada peça nova é testada imediatamente (não espera o final do dia)
- **CD:** Se passar nos testes, já vai direto para a loja

---

### **Como Funciona GitHub Actions?**

GitHub Actions são "robôs" que executam tarefas automaticamente quando algo acontece no GitHub.

**Triggers (gatilhos):**

- Você faz push para uma branch
- Você abre um Pull Request
- Todo dia às 9h da manhã (scheduled)
- Quando alguém cria uma issue

**Actions executam:**

- Testes
- Deploy
- Enviar notificações
- Gerar relatórios

---

### **Estrutura de um Workflow**

**Arquivo:** `.github/workflows/tests.yml`

```yaml
name: Tests # Nome do workflow (aparece no GitHub)

# Quando esse workflow deve rodar?
on:
  pull_request: # Quando abrir/atualizar PR
    branches: [develop, main]
  push: # Quando fizer push
    branches: [develop, main]

# O que fazer?
jobs:
  unit-tests: # Nome do job
    runs-on: ubuntu-latest # Sistema operacional

    steps: # Sequência de comandos
      - name: Checkout code
        uses: actions/checkout@v3 # Baixa código do repo

      - name: Setup Python
        uses: actions/setup-python@v4
        with:
          python-version: "3.11"

      - name: Install dependencies
        run: |
          pip install poetry
          poetry install

      - name: Run unit tests
        run: poetry run pytest tests/unit -v
```

---

### **Explicando Cada Parte**

#### **1. Trigger (on:)**

```yaml
on:
  pull_request:
    branches: [develop, main] # Só PRs para essas branches
  push:
    branches: [develop] # Só pushes diretos para develop
```

**Tradução:** "Execute quando alguém abrir PR para develop/main, ou fizer push direto para develop"

---

#### **2. Jobs (jobs:)**

```yaml
jobs:
  unit-tests: # Nome do job (escolha você)
    runs-on: ubuntu-latest # Onde rodar (ubuntu, windows, macos)
```

**Tradução:** "Crie uma máquina Ubuntu virtual e execute os comandos"

---

#### **3. Steps (steps:)**

Cada step é um comando executado em sequência:

```yaml
steps:
  # Step 1: Baixar código
  - name: Checkout code
    uses: actions/checkout@v3
    # "uses" = usa uma action pronta (feita por outros)

  # Step 2: Instalar Python
  - name: Setup Python
    uses: actions/setup-python@v4
    with:
      python-version: "3.11"
    # "with" = parâmetros para a action

  # Step 3: Rodar comandos customizados
  - name: Run tests
    run: |
      pip install poetry
      poetry run pytest
    # "run" = comandos bash que você escreveria no terminal
```

---

### **Workflow Completo: Tests + Integration**

**Arquivo:** `.github/workflows/tests.yml`

```yaml
name: Tests

on:
  pull_request:
    branches: [develop, main]
  push:
    branches: [develop, main]

jobs:
  # Job 1: Testes unitários (sempre roda)
  unit-tests:
    runs-on: ubuntu-latest

    steps:
      - uses: actions/checkout@v3

      - name: Setup Python
        uses: actions/setup-python@v4
        with:
          python-version: "3.11"

      - name: Cache dependencies
        uses: actions/cache@v3
        with:
          path: ~/.cache/pypoetry
          key: ${{ runner.os }}-poetry-${{ hashFiles('**/poetry.lock') }}
        # Cache = salva dependências para próxima vez (mais rápido)

      - name: Install dependencies
        run: |
          pip install poetry
          poetry install

      - name: Run unit tests
        run: poetry run pytest tests/unit -v

      - name: Upload coverage
        uses: codecov/codecov-action@v3
        # Envia cobertura de testes para codecov.io (opcional)

  # Job 2: Testes de integração (só em push, não PR)
  integration-tests:
    runs-on: ubuntu-latest
    if: github.event_name == 'push' # Condição

    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-python@v4
        with:
          python-version: "3.11"

      - name: Install dependencies
        run: |
          pip install poetry
          poetry install

      - name: Run integration tests
        env:
          # Secrets são configurados no GitHub (explicado abaixo)
          ANTHROPIC_API_KEY: ${{ secrets.ANTHROPIC_API_KEY }}
          GMAIL_CREDENTIALS: ${{ secrets.GMAIL_CREDENTIALS }}
        run: poetry run pytest tests/integration -v -m integration
```

---

### **Como Configurar Secrets no GitHub**

**Secrets** são variáveis secretas (API keys, senhas) que o GitHub guarda de forma segura.

#### **Passo 1: Adicionar Secret no GitHub**

1. Vá no seu repositório no GitHub
2. Click em **Settings** (configurações)
3. Na barra lateral: **Secrets and variables** → **Actions**
4. Click em **New repository secret**
5. Preencha:
   - **Name:** `ANTHROPIC_API_KEY`
   - **Value:** `sk-ant-api03-...` (sua chave real)
6. Click em **Add secret**

#### **Passo 2: Usar no Workflow**

```yaml
- name: Run tests
  env:
    ANTHROPIC_API_KEY: ${{ secrets.ANTHROPIC_API_KEY }}
  run: pytest tests/integration
```

**Segurança:**

- Secrets nunca aparecem nos logs
- Se tentar fazer `echo $ANTHROPIC_API_KEY`, GitHub esconde automaticamente

---

### **Workflow: Deploy Automático**

**Arquivo:** `.github/workflows/deploy.yml`

```yaml
name: Deploy to Production

on:
  push:
    branches: [main] # Só quando merge para main
    tags:
      - "v*" # Ou quando criar tag v1.0.0, v0.2.0, etc

jobs:
  deploy:
    runs-on: ubuntu-latest

    steps:
      - uses: actions/checkout@v3

      - name: Setup Python
        uses: actions/setup-python@v4
        with:
          python-version: "3.11"

      - name: Install dependencies
        run: |
          pip install poetry
          poetry install

      - name: Build package
        run: poetry build

      - name: Publish to PyPI
        env:
          POETRY_PYPI_TOKEN_PYPI: ${{ secrets.PYPI_TOKEN }}
        run: poetry publish

      - name: Deploy to server
        uses: appleboy/ssh-action@master
        with:
          host: ${{ secrets.SERVER_HOST }}
          username: ${{ secrets.SERVER_USER }}
          key: ${{ secrets.SSH_PRIVATE_KEY }}
          script: |
            cd /app/agent-framework
            git pull origin main
            poetry install
            systemctl restart agent-service
```

---

### **Workflow: Relatório Semanal de Custos**

**Arquivo:** `.github/workflows/cost-report.yml`

```yaml
name: Weekly Cost Report

on:
  schedule:
    - cron: "0 9 * * 1" # Segunda-feira às 9h UTC
    # Formato: minuto hora dia mês dia-da-semana
    # 0 9 * * 1 = 9h de segunda
    # 0 0 * * * = meia-noite todo dia
    # 0 */6 * * * = a cada 6 horas

jobs:
  cost-report:
    runs-on: ubuntu-latest

    steps:
      - uses: actions/checkout@v3

      - name: Setup Python
        uses: actions/setup-python@v4
        with:
          python-version: "3.11"

      - name: Install dependencies
```
