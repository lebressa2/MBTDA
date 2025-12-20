import os
import sys
from pathlib import Path

# Configuração de Path para imports locais
sys.path.append(os.getcwd())

from src.components.context import PromptComposer
from src.components.memory.manager import InMemoryManager
from src.components.workspace.manager import LayeredWorkspaceManager
from src.components.interpreter.manager import SandboxInterpreter
from src.components.tools.manager import ToolManager
from src.clients.llm.google_client import GoogleClient

"""
MANUAL DE USO: ARQUITETURA DE PRIMITIVOS (ATÔMICA)
--------------------------------------------------
Nesta arquitetura, componentes são 'Providers' de dois tipos de fichas:
1. Tool Shards: Ações que o LLM pode executar (via ToolManager).
2. Context Shards: Informações que o LLM deve saber (via PromptComposer).

O Orquestrador (você) decide quais fichas de cada componente quer 'plugar' nos 
consumidores centrais (ToolManager e PromptComposer).
"""

def run_atomic_orchestration():
    print("--- MBTDA Atomic Architecture Demo ---")
    
    # 1. INSTANCIAÇÃO DA INFRAESTRUTURA (Stateless Primitives)
    # Estes componentes cuidam do IO e lógica pesada, mas não sabem nada do System Prompt.
    base = Path("./agent_runtime")
    workspace = LayeredWorkspaceManager(
        project_path=base / "project", 
        office_path=base / "office", 
        interpreter_path=base / "temp"
    )
    memory = InMemoryManager()
    interpreter = SandboxInterpreter(workspace)
    
    # 2. CONSUMIDORES DE PRIMITIVOS
    # Eles são os 'Hubs' que o LLM consulta.
    tool_manager = ToolManager()
    composer = PromptComposer(template="task_agent")
    composer.meta.agent_name = "AtomicAgent"
    
    # 3. COLETA E DISTRIBUIÇÃO DE SHARDS (A Orquestração)
    # Percorremos os componentes coletando o que eles oferecem para o LLM.
    components = [workspace, memory, interpreter]
    
    for comp in components:
        # A) Coleta de Tools (Fichas de Ação)
        # O componente entrega objetos 'Tool' (Nome, Descrição, Schema Pydantic, Função).
        for tool in comp.get_tools():
            tool_manager.register_tool(tool)
            
        # B) Coleta de Context Shards (Fichas de Conhecimento)
        # O componente entrega um Dict com strings úteis (ex: lista de arquivos, histórico).
        # Você decide a chave onde isso será injetado no Composer.
        shard_key = comp.__class__.__name__.lower().replace("manager", "").replace("interpreter", "python")
        composer.add(shard_key, comp.get_context_shard())

    # 4. PREPARAÇÃO PARA O MODELO
    # Agora temos tudo o que é necessário para uma chamada de IA robusta e validada.
    system_prompt = composer.build_system_prompt()
    tool_schemas = tool_manager.get_tool_schemas()
    
    print(f"\n[SISTEMA] Agente '{composer.meta.agent_name}' configurado.")
    print(f"[SISTEMA] {len(tool_schemas)} ferramentas atômicas carregadas.")
    print(f"[SISTEMA] Context Shards ativos: {list(composer.context.keys())}")
    
    print("\n--- MANUAL DE MÉTODOS ---")
    print("1. workspace.read_file(path, layer)  -> Lógica atômica de IO")
    print("2. tool_manager.execute_tool(name, **args) -> Execução com validação Pydantic")
    print("3. composer.build_system_prompt() -> Montagem final do prompt de sistema")
    print("4. memory.add_message(role, content) -> Persistência de histórico")
    
    print("\n[INFO] Componentes prontos para uso manual. Veja o código para o loop de execução.")

if __name__ == "__main__":
    run_atomic_orchestration()