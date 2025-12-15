#!/usr/bin/env python3
"""
Launcher para testes RACI - configura PYTHONPATH automaticamente.

Este arquivo deve ser executado da raiz do projeto para garantir que os testes
em tests/raci/ funcionem corretamente.
"""

import os
import sys
import subprocess

def run_raci_tests():
    """Executa testes RACI com PYTHONPATH configurado."""

    # Verificar se estamos na raiz do projeto (onde existe src/)
    if not os.path.exists('src'):
        print("Erro: Execute este script da raiz do projeto (onde existe src/)")
        return

    # Caminho para a pasta de testes
    tests_raci_dir = os.path.join('tests', 'raci')
    if not os.path.exists(tests_raci_dir):
        print(f"Erro: Pasta de testes não encontrada: {tests_raci_dir}")
        return

    # Configurar PYTHONPATH - adicionar apenas a RAIZ do projeto
    project_root = os.getcwd()  # Já estamos na raiz
    current_pythonpath = os.environ.get('PYTHONPATH', '')

    # Executar o teste simplificado
    print("Executando teste simplificado do Agente RACI...")
    print(f"Diretorio: {tests_raci_dir}")
    print(f"PYTHONPATH: {project_root}")
    print(f"PYTHONPATH atual: {current_pythonpath}")

    # Garantir que o ambiente virtual seja usado corretamente
    env = os.environ.copy()
    if current_pythonpath:
        env['PYTHONPATH'] = project_root + os.pathsep + current_pythonpath
    else:
        env['PYTHONPATH'] = project_root

    # Garantir que o ambiente virtual Python seja encontrado
    # Procura pelo site-packages do ambiente virtual
    import pathlib
    venv_root = pathlib.Path(sys.executable).parent.parent  # venv/bin ou venv\Scripts
    site_packages = venv_root / "Lib" / "site-packages"
    if site_packages.exists():
        env['PYTHONPATH'] = str(site_packages) + os.pathsep + env['PYTHONPATH']

    print(f"PYTHONPATH final: {env.get('PYTHONPATH', '')}")

    try:
        # Executar teste da pasta src para resolver imports relativos
        result = subprocess.run(
            ['python', '../tests/raci/test_raci_simples.py'],
            cwd='src',
            env=env,
            capture_output=True,
            text=True,
            timeout=30
        )

        print("Saida do teste:")
        print(result.stdout)

        if result.stderr:
            print("Stderr:")
            print(result.stderr)

        if result.returncode == 0:
            print("\nTeste simplificado executado com sucesso!")
            print("Logs salvos em: tests/raci/teste_raci_simples.log")
        else:
            print(f"\nTeste falhou com codigo: {result.returncode}")

    except subprocess.TimeoutExpired:
        print("Teste excedeu timeout de 60 segundos")
    except FileNotFoundError:
        print("Python não encontrado no PATH")
    except Exception as e:
        print(f"Erro ao executar teste: {e}")

if __name__ == "__main__":
    run_raci_tests()
