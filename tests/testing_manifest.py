# Testing Manifest - Agent Framework
# ==================================
# 
# This manifest defines the 3-level testing strategy for the Agent Framework.
# Each level has specific objectives and requirements.

## Level 1: Atomic Operations (90% of current tests)
## -------------------------------------------------
## Objective: Verify individual component functionality in isolation.
## Focus: Unit-level operations without LLM interaction.
## 
## Tests include:
## - Interface implementation verification
## - Context contribution structure
## - Memory operations (add, retrieve, clear)
## - Tool registration and execution
## - Workspace file operations
## - State machine transitions (without LLM)
## - Template registry operations
## - Deep merge functionality
## 
## Run with: python -m tests.run_tests --level 1
## Expected time: < 5 seconds
## No API keys required


## Level 2: Context Analysis (Advanced)
## ------------------------------------
## Objective: Analyze what context is injected into system prompts.
## Focus: Verify XML structure, custom states, and protocol injection.
## 
## Tests include:
## - Print raw XML system prompt for inspection
## - Custom state definitions and instructions
## - Protocol injection and step tracking
## - Complex nested context structures
## - State transition callbacks
## - Context accumulation across turns
## 
## Run with: python -m tests.run_tests --level 2
## Expected time: 10-30 seconds
## Requires: GROQ_API_KEY or GOOGLE_API_KEY


## Level 3: Real Chatbot Simulation
## --------------------------------
## Objective: Full end-to-end testing with real LLM interaction.
## Focus: Multi-turn conversations, tool usage, thinking chain visibility.
## 
## Tests include:
## - Multi-turn conversation with memory
## - Tool selection and execution
## - Thinking tokens display
## - State transitions during conversation
## - Full ReAct loop visibility
## - Real user interaction simulation
## 
## Run with: python -m tests.run_tests --level 3
## Expected time: 1-3 minutes
## Requires: GROQ_API_KEY or GOOGLE_API_KEY


# Test Configuration
# ------------------
LEVEL_1_TESTS = [
    "test_interface_implementation",
    "test_context_contribution_structure", 
    "test_memory_operations",
    "test_tool_registration",
    "test_workspace_operations",
    "test_state_machine_basic",
    "test_template_registry",
    "test_deep_merge",
    "test_disabled_injection",
]

LEVEL_2_TESTS = [
    "test_system_prompt_xml_structure",
    "test_custom_states_injection",
    "test_protocol_context_injection",
    "test_complex_nested_context",
    "test_state_callbacks",
    "test_context_accumulation",
]

LEVEL_3_TESTS = [
    "test_chatbot_multi_turn",
    "test_tool_usage_chain",
    "test_thinking_chain_visibility",
    "test_full_react_loop",
]
