# =============================================================================
# 🛠️ MAKEFILE - MBTDA (SIMPLIFIED STANDALONE ARCHITECTURE)
# =============================================================================

PYTHON = python
SRC_DIR = src

.PHONY: help lint format clean install

help:
	@echo ""
	@echo "╔════════════════════════════════════════════════════════════════╗"
	@echo "║  🛠️  MBTDA - COMANDOS DISPONÍVEIS                                ║"
	@echo "╠════════════════════════════════════════════════════════════════╣"
	@echo "║                                                                ║"
	@echo "║  📦 SETUP                                                      ║"
	@echo "║  make install        → Instala dependências do projeto        ║"
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

install:
	@echo "📦 Instalando dependências..."
	$(PYTHON) -m pip install --upgrade pip
	pip install -r requirements.txt
	@echo "✅ Dependências instaladas!"

lint:
	@echo "🔍 Verificando qualidade do código..."
	ruff check $(SRC_DIR)/ --output-format=full
	@echo "✅ Verificação concluída!"

format:
	@echo "🎨 Formatando código..."
	ruff format $(SRC_DIR)/
	ruff check $(SRC_DIR)/ --fix
	@echo "✅ Código formatado!"

clean:
	@echo "🧹 Limpando arquivos temporários..."
	$(PYTHON) -c "import shutil, pathlib; [shutil.rmtree(p) for p in pathlib.Path('.').rglob('__pycache__')]"
	$(PYTHON) -c "import shutil, pathlib; [shutil.rmtree(p) for p in pathlib.Path('.').rglob('.pytest_cache')]"
	@echo "✅ Limpeza concluída!"