# =============================================================================
# 🛠️ MAKEFILE - COMANDOS ÚTEIS DO PROJETO
# =============================================================================
#
# 📖 O QUE É UM MAKEFILE?
# É um arquivo que define "atalhos" para comandos longos.
# Em vez de digitar "pytest tests/unit -v --tb=short", você digita "make test-unit"
#
# 🚀 COMO USAR?
# No terminal, digite: make <comando>
# Exemplo: make test
#
# 📋 VER TODOS OS COMANDOS DISPONÍVEIS:
# Digite: make help
#
# ⚠️ NOTA PARA WINDOWS:
# Se 'make' não funcionar, instale via: choco install make
# Ou use os comandos diretamente (mostrados abaixo de cada target)
# =============================================================================

# Variáveis (podem ser alteradas)
PYTHON = python
PYTEST = pytest
SRC_DIR = src
TEST_DIR = tests

# .PHONY diz ao make que esses não são arquivos, são comandos
.PHONY: help test test-unit test-integration lint format clean install

# =============================================================================
# 📚 HELP - Mostra todos os comandos disponíveis
# =============================================================================
help:
	@echo ""
	@echo "╔════════════════════════════════════════════════════════════════╗"
	@echo "║  🛠️  COMANDOS DISPONÍVEIS                                       ║"
	@echo "╠════════════════════════════════════════════════════════════════╣"
	@echo "║                                                                ║"
	@echo "║  📦 SETUP                                                      ║"
	@echo "║  make install        → Instala dependências do projeto        ║"
	@echo "║                                                                ║"
	@echo "║  🧪 TESTES                                                     ║"
	@echo "║  make test           → Roda TODOS os testes                   ║"
	@echo "║  make test-unit      → Roda só testes unitários (rápido)      ║"
	@echo "║  make test-cov       → Testes + relatório de cobertura        ║"
	@echo "║                                                                ║"
	@echo "║  ✨ QUALIDADE DE CÓDIGO                                        ║"
	@echo "║  make lint           → Verifica problemas no código           ║"
	@echo "║  make format         → Formata código automaticamente         ║"
	@echo "║                                                                ║"
	@echo "║  🧹 LIMPEZA                                                    ║"
	@echo "║  make clean          → Remove arquivos temporários            ║"
	@echo "║                                                                ║"
	@echo "╚════════════════════════════════════════════════════════════════╝"
	@echo ""

# =============================================================================
# 📦 INSTALL - Instala dependências
# =============================================================================
# Comando equivalente: pip install -r requirements.txt
# =============================================================================
install:
	@echo "📦 Instalando dependências..."
	$(PYTHON) -m pip install --upgrade pip
	pip install -r requirements.txt
	pip install pytest pytest-cov ruff
	@echo "✅ Dependências instaladas!"

# =============================================================================
# 🧪 TEST - Roda todos os testes
# =============================================================================
# Comando equivalente: pytest tests/ -v
# 
# Flags explicadas:
#   -v          = verbose (mostra nome de cada teste)
#   --tb=short  = traceback curto (menos spam se falhar)
# =============================================================================
test:
	@echo "🧪 Rodando todos os testes..."
	$(PYTEST) $(TEST_DIR)/ -v --tb=short
	@echo "✅ Testes concluídos!"

# =============================================================================
# 🔬 TEST-UNIT - Roda só testes unitários (rápido!)
# =============================================================================
# Use isso no dia-a-dia enquanto desenvolve.
# Testes unitários são rápidos porque não chamam APIs reais.
# =============================================================================
test-unit:
	@echo "🔬 Rodando testes unitários..."
	$(PYTEST) $(TEST_DIR)/ -v -m "not integration and not e2e" --tb=short
	@echo "✅ Testes unitários concluídos!"

# =============================================================================
# 📊 TEST-COV - Testes com relatório de cobertura
# =============================================================================
# Mostra quanto % do seu código é coberto por testes.
# Meta: >80% de cobertura
# =============================================================================
test-cov:
	@echo "📊 Rodando testes com cobertura..."
	$(PYTEST) $(TEST_DIR)/ -v --cov=$(SRC_DIR) --cov-report=term-missing
	@echo "✅ Relatório de cobertura gerado!"

# =============================================================================
# ✨ LINT - Verifica qualidade do código
# =============================================================================
# Ruff verifica:
#   - Variáveis não usadas
#   - Imports desnecessários
#   - Código que pode dar erro
#   - Boas práticas de Python
# =============================================================================
lint:
	@echo "🔍 Verificando qualidade do código..."
	ruff check $(SRC_DIR)/ --output-format=full
	@echo "✅ Verificação concluída!"

# =============================================================================
# 🎨 FORMAT - Formata código automaticamente
# =============================================================================
# Ruff format: formata código seguindo PEP 8 (estilo padrão Python)
# Similar ao Black, mas mais rápido
# =============================================================================
format:
	@echo "🎨 Formatando código..."
	ruff format $(SRC_DIR)/
	ruff check $(SRC_DIR)/ --fix
	@echo "✅ Código formatado!"

# =============================================================================
# 🧹 CLEAN - Remove arquivos temporários
# =============================================================================
# Remove:
#   - __pycache__/  = cache de Python
#   - .pytest_cache/ = cache do pytest
#   - *.pyc         = bytecode compilado
#   - .coverage     = dados de cobertura
# =============================================================================
clean:
	@echo "🧹 Limpando arquivos temporários..."
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".pytest_cache" -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete 2>/dev/null || true
	find . -type f -name ".coverage" -delete 2>/dev/null || true
	@echo "✅ Limpeza concluída!"

# =============================================================================
# 🚀 PRE-COMMIT - Roda antes de fazer commit
# =============================================================================
# Use isso antes de fazer git commit para garantir qualidade.
# =============================================================================
pre-commit: lint test
	@echo ""
	@echo "╔════════════════════════════════════════════════════════════════╗"
	@echo "║  ✅ PRONTO PARA COMMIT!                                         ║"
	@echo "║                                                                ║"
	@echo "║  Lint passou ✓                                                 ║"
	@echo "║  Testes passaram ✓                                             ║"
	@echo "║                                                                ║"
	@echo "║  Próximo passo: git add . && git commit -m 'sua mensagem'     ║"
	@echo "╚════════════════════════════════════════════════════════════════╝"
	@echo ""
