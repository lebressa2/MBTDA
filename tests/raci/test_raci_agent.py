#!/usr/bin/env python3
"""
Teste local do agente usando RACI interpreter.

Este script demonstra o agente executando código Python através do RACI interpreter,
usando modelos Groq com fallback para Google, mostrando logs XML e COT.
"""

import sys
import os
import logging
import traceback

# Configure logging
logging.basicConfig(
    filename='teste_raci_resultado.log',
    level=logging.DEBUG,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

console = logging.StreamHandler()
console.setLevel(logging.INFO)
formatter = logging.Formatter('%(levelname)s - %(message)s')
console.setFormatter(formatter)
logging.getLogger('').addHandler(console)

logger = logging.getLogger(__name__)

# Set PYTHONPATH (three levels up: tests/raci -> tests -> project_root -> src)
project_root = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
src_path = os.path.join(project_root, 'src')
sys.path.insert(0, src_path)

# Ensure .env is loaded
try:
    from dotenv import load_dotenv
    load_dotenv()
    logger.info(".env loaded successfully")
except ImportError:
    logger.warning("dotenv not available, using environment variables")

# Test imports one by one
logger.info("Testing imports...")

imports_ok = True
try:
    from src.clients.llm.enhanced_clients import create_fallback_client
    from src.components.tools.raci_manager import RACIToolManager
    from src.components.interpreter.sandbox import SandboxInterpreter
    from src.components.workspace.layered import LayeredWorkspaceManager, WorkspaceLayer
    from src.components.context import ContextManager
    from src.models.data_models import Protocol
    from src.agent import Agent
    logger.info("All imports successful")
except Exception as e:
    logger.error(f"Import error: {e}")
    logger.error(traceback.format_exc())
    imports_ok = False

if not imports_ok:
    logger.error("Exiting due to import errors")
    sys.exit(1)


def criar_agente_teste():
    """Cria e configura o agente para teste com RACI."""

    print("=== Inicializando Agente com RACI ===")

    # 1. Configurar workspace em camadas
    workspace = LayeredWorkspaceManager(
        base_path=".",  # Usar diretório atual para PROJECT layer
        agent_id="teste_raci_agent"
    )

    # 2. Configurar interpreter
    interpreter = SandboxInterpreter(workspace)

    # 3. Configurar tool manager RACI
    tools = RACIToolManager(
        interpreter=interpreter,
        workspace=workspace
    )

    # 4. Configurar cliente LLM com fallback Groq -> Google
    llm_client = create_fallback_client(
        enable_logging=True,  # Habilita XML logging e COT
        fallback_enabled=True
    )

    # 5. Configurar context manager
    context = ContextManager()

    from src.models.data_models import ProtocolStep

    step1 = ProtocolStep(
        name="execute_raci",
        goal="Execute Python code using RACI interpreter",
        instructions=["Use execute_code tool to run Python", "Read/write files as needed"]
    )

    protocol = Protocol(
        protocol_name="raci_interpreter",
        description="Protocolo para usar código Python via RACI interpreter",
        steps=[step1]
    )
    context.add_protocol(protocol)

    # 6. Criar agente
    agent = Agent(
        text_provider=llm_client,
        context=context,
        tools=tools,
        workspace_manager=workspace
    )

    print(f"✓ Agente criado com provider: {llm_client.get_current_provider()}")
    print(f"✓ Modelo atual: {llm_client.get_model_name()}")
    print(f"✓ Workspace configurado em camadas")
    print(f"✓ RACI tools registradas: {tools.get_tools()}")

    return agent


def testar_agente_codigo_pythom():
    """Testa o agente executando código Python via RACI."""

    print("\n=== Teste: Execução de código Python ===")
    print("Tarefa: Calcular estatísticas de uma lista de números")

    agent = criar_agente_teste()

    # Instrução para o agente
    instrucao = """
Calcule e mostre estatísticas básicas para esta lista de números: [1, 5, 2, 8, 3, 9, 4, 6, 7, 10]

Por favor:
1. Calcule a média
2. Encontre o valor mínimo e máximo
3. Ordene a lista
4. Salve os resultados em um arquivo chamado 'estatisticas.json'

Use código Python para fazer os cálculos e manipulação de dados.
    """

    print(f"\nInstrução enviada ao agente:\n{instrucao}")

    try:
        # Processar mensagem
        resposta = agent.process_message(instrucao)

        print("\n=== Resposta Final do Agente ===")
        print(resposta)

        # Verificar se arquivo foi criado
        print("\n=== Verificação de Arquivo Criado ===")
        if agent.workspace_manager.file_exists("estatisticas.json"):
            conteudo = agent.workspace_manager.read_file("estatisticas.json")
            print(f"Arquivo 'estatisticas.json' criado com sucesso:")
            print(conteudo)
        else:
            print("❌ Arquivo 'estatisticas.json' não foi criado")

    except Exception as e:
        print(f"❌ Erro durante teste: {e}")
        import traceback
        traceback.print_exc()


def testar_agente_requisicao_http():
    """Testa o agente fazendo uma requisição HTTP simples."""

    print("\n=== Teste 2: Requisição HTTP ===")
    print("Tarefa: Fazer requisição para uma API pública")

    agent = criar_agente_teste()

    instrucao = """
Faça uma requisição para https://jsonplaceholder.typicode.com/posts/1
e mostre o título e o corpo do post retornado.

Use o módulo 'http' do RACI interpreter para fazer a requisição.
Salve os dados em um arquivo chamado 'post.json'.
    """

    print(f"\nInstrução enviada ao agente:\n{instrucao}")

    try:
        resposta = agent.process_message(instrucao)

        print("\n=== Resposta Final do Agente ===")
        print(resposta)

        # Verificar arquivo
        print("\n=== Verificação de Arquivo Criado ===")
        if agent.workspace_manager.file_exists("post.json"):
            conteudo = agent.workspace_manager.read_file("post.json")
            print(f"Arquivo 'post.json' criado:")
            print(conteudo)
        else:
            print("❌ Arquivo 'post.json' não foi criado")

    except Exception as e:
        print(f"❌ Erro durante teste: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    print("🚀 Iniciando testes do Agente RACI")
    print("=" * 60)

    # Teste 1: Código Python básico
    testar_agente_codigo_pythom()

    print("\n" + "=" * 60)

    # Teste 2: Requisição HTTP
    testar_agente_requisicao_http()

    print("\n🏁 Testes concluídos!")
