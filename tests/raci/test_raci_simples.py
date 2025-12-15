#!/usr/bin/env python3
"""
Teste simplificado do agente RACI - apenas inicialização e configuração.

Mostra os logs XML e COT durante a configuração, sem executar mensagens caras.
"""

import sys
import os
import logging
import traceback

# DEBUG: Mostrar caminhos antes de modificar
print(f"DEBUG: PYTHONPATH atual: {os.environ.get('PYTHONPATH', 'Nao definido')}")
print(f"DEBUG: sys.path[:3]: {sys.path[:3]}")

# Forçar inclusão do caminho src no sys.path
# Mesmo que PYTHONPATH esteja correto, garantir que o caminho está disponível
script_dir = os.path.dirname(os.path.abspath(__file__))  # tests/raci
tests_dir = os.path.dirname(script_dir)                   # tests
project_root = os.path.dirname(tests_dir)                 # raiz do projeto
src_path = os.path.join(project_root, 'src')

if src_path not in sys.path:
    sys.path.insert(0, src_path)

print(f"DEBUG: Caminho src adicionado: {src_path}")
print(f"DEBUG: sys.path apos modificacao: {sys.path[:3]}")

# Configure logging to write to file and console
logging.basicConfig(
    filename='teste_raci_simples.log',
    level=logging.DEBUG,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

console = logging.StreamHandler()
console.setLevel(logging.INFO)
formatter = logging.Formatter('%(levelname)s - %(message)s')
console.setFormatter(formatter)
logging.getLogger('').addHandler(console)

logger = logging.getLogger(__name__)

# Load .env
try:
    from dotenv import load_dotenv
    load_dotenv()
    logger.info(".env carregado com sucesso")
except ImportError:
    logger.warning("dotnet não disponível, usando variáveis de ambiente")

print("Iniciando teste simplificado do Agente RACI")

# Test imports RACI
logger.info("Testando imports RACI...")
try:
    # Import apenas os componentes RACI necessários
    from src.clients.llm.enhanced_clients import create_fallback_client
    from src.components.tools.raci_manager import RACIToolManager
    from src.components.interpreter.sandbox import SandboxInterpreter
    from src.components.workspace.layered import LayeredWorkspaceManager, WorkspaceLayer

    print("Imports RACI bem-sucedidos")
except ImportError as e:
    print(f"Erro nos imports RACI: {e}")
    logger.error(f"Erro nos imports RACI: {e}")
    logger.error(traceback.format_exc())
    sys.exit(1)
except Exception as e:
    logger.error(f"Erro geral nos imports: {e}")
    print(f"Erro geral nos imports: {e}")
    sys.exit(1)

print("\n=== Inicializando componentes ===")

try:
    # 1. Workspace em camadas
    print("Iniciando LayeredWorkspaceManager...")
    workspace = LayeredWorkspaceManager(
        base_path=".",
        agent_id="teste_raci_simples"
    )
    print(f"Workspace criado - Project root: {workspace.get_layer_root(WorkspaceLayer.PROJECT)}")

    # 2. Sandbox Interpreter
    print("Iniciando SandboxInterpreter...")
    interpreter = SandboxInterpreter(workspace)
    print(f"Interpreter criado com {len(interpreter.get_available_modules())} modulos")

    # 3. RACI Tool Manager
    print("Iniciando RACIToolManager...")
    tools = RACIToolManager(interpreter=interpreter, workspace=workspace)
    print(f"RACI Tools criado com {len(tools.get_tools())} ferramentas")

    # 4. LLM Client com fallback (esta parte gera XML/COT logs)
    print("Iniciando FallbackLLMClient...")
    llm_client = create_fallback_client(enable_logging=True, fallback_enabled=True)
    print(f"LLM Client criado - Provider: {llm_client.get_current_provider()}, Modelo: {llm_client.get_model_name()}")

    # Simular alguns testes básicos
    print("\\nTESTES BASICOS:")

    # Testar funcionalidades básicas
    print("Testando funcionalidades RACI...")

    # Test 1: Ver se o LLM client foi criado
    print(f"✓ LLM Client: {llm_client is not None}")

    # Test 2: Ver se as ferramentas foram criadas
    tool_names = [getattr(t, 'name', str(t)) for t in tools.get_tools()]
    print(f"✓ Ferramentas RACI: {tool_names}")

    # Test 3: Ver se o interpreter tem módulos
    modules = interpreter.get_available_modules()
    print(f"✓ Modulos do interpreter: {len(modules)} (ex: {[m.name for m in modules[:3]]})")

    print("\\nCOMPONENTES INICIALIZADOS COM SUCESSO!")

    print("\n" + "="*60)
    print("CONFIGURACAO CONCLUIDA COM SUCESSO!")
    print("="*60)
    print("\nLogs XML e COT salvos em 'teste_raci_simples.log'")

    print("\nArquivos criados no workspace:")
    files = workspace.list_directory(".", WorkspaceLayer.PROJECT)
    if files:
        for f in files:
            print(f"  - {f}")
    else:
        print("  (nenhum arquivo criado ainda)")

    print("\nFerramentas RACI disponiveis:")
    for tool_info in tools.get_tool_descriptions().split('\n- '):
        if tool_info.strip():
            print(f"  - {tool_info.strip()}")

except Exception as e:
    logger.error(f"Erro durante configuração: {e}")
    logger.error(traceback.format_exc())
    print(f"Erro durante configuração: {e}")
    traceback.print_exc()

print("\n[Teste simplificado concluido!]")
print("Veja o arquivo 'teste_raci_simples.log' para logs detalhados incluindo XML e COT.")
