
import sys
import os

# Add src to path
sys.path.append(os.path.join(os.getcwd(), 'src'))

from src.components.context_manager import ContextManager
from src.components.state_machine import StateMachine
from src.agent import Agent
from src.interfaces.base import ITextClient, IContextProvider

class MockLLM(ITextClient):
    def invoke(self, messages, **kwargs):
        return "Mock response"
    def bind_tools(self, tools):
        return self
    def get_model_name(self):
        return "mock-model"

class MockComponent(IContextProvider):
    def get_context_contribution(self):
        return {"mock_component": "active"}

def test_context_centralization():
    print("Testing Context Centralization...")
    
    # Setup
    llm = MockLLM()
    context_manager = ContextManager()
    state_machine = StateMachine()
    
    # Initialize Agent
    agent = Agent(
        text_provider=llm,
        context=context_manager,
        state_machine=state_machine
    )
    
    # 1. Verify StateMachine is registered
    if state_machine in context_manager._providers:
        print("✅ StateMachine is registered as provider")
    else:
        print("❌ StateMachine NOT registered")
        
    # 2. Add another component and verify registration logic
    mock_comp = MockComponent()
    agent.mock_comp = mock_comp
    # Manually trigger registration again (usually happens in init)
    agent._register_context_providers()
    
    if mock_comp in context_manager._providers:
        print("✅ Auto-discovery of components works")
    else:
        print("❌ Auto-discovery failed")
        
    # 3. Verify Context Population
    # Set a state
    state_machine.current_state = "THINKING"
    
    system_message = context_manager.populate_system_message()
    print("\nGenerated System Message:")
    print(system_message)
    
    if "<current_state>THINKING</current_state>" in system_message:
        print("✅ current_state present in system message")
    else:
        print("❌ current_state missing")
        
    if "<mock_component>active</mock_component>" in system_message:
        print("✅ mock_component present in system message")
    else:
        print("❌ mock_component missing")

if __name__ == "__main__":
    test_context_centralization()
