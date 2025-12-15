#!/usr/bin/env python3
import os
import sys
import logging

# Configure logging to write to file
logging.basicConfig(
    filename='test_imports.log',
    level=logging.DEBUG,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

# Also log to console
console = logging.StreamHandler()
console.setLevel(logging.DEBUG)
formatter = logging.Formatter('%(levelname)s - %(message)s')
console.setFormatter(formatter)
logging.getLogger('').addHandler(console)

logger = logging.getLogger(__name__)

# Set PYTHONPATH
src_path = os.path.join(os.path.dirname(__file__), 'src')
sys.path.insert(0, src_path)

logger.info("Testing imports...")

try:
    logger.info("Importing Agent...")
    from src.agent import Agent
    logger.info("✓ Agent import successful")

    logger.info("Importing enhanced clients...")
    from src.clients.llm.enhanced_clients import create_fallback_client
    logger.info("✓ Enhanced clients import successful")

    logger.info("Importing RACI manager...")
    from src.components.tools.raci_manager import RACIToolManager
    logger.info("✓ RACI manager import successful")

    logger.info("Importing Sandbox Interpreter...")
    from src.components.interpreter.sandbox import SandboxInterpreter
    logger.info("✓ SandBoxInterpreter import successful")

    logger.info("Importing Layered Workspace Manager...")
    from src.components.workspace.layered import LayeredWorkspaceManager
    logger.info("✓ LayeredWorkspaceManager import successful")

    # Test creating the LLM client
    logger.info("Creating LLM client...")
    client = create_fallback_client(enable_logging=False)  # Disable for now to avoid flood
    logger.info(f"✓ LLM client created: {client.get_current_provider()} - {client.get_model_name()}")

    logger.info("\nAll imports successful! 🎉")

except ImportError as e:
    logger.error(f"❌ Import error: {e}")
    import traceback
    logger.error(traceback.format_exc())

except Exception as e:
    logger.error(f"❌ Other error: {e}")
    import traceback
    logger.error(traceback.format_exc())
