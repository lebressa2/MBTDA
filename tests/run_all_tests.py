"""
Run All Agent Tests - Real API Tests

Execute the complete test suite using real LLM APIs:
- Groq (qwen/qwen3-32b) - Primary
- Google Gemini (gemini-2.5-flash) - Fallback

This runs the framework tests in tests/test_agent_framework.py
"""

import sys
import os

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from tests.test_agent_framework import run_all_tests


def main():
    """Run all API tests."""
    print("\n" + "🧪"*30)
    print("\n   AGENT FRAMEWORK - REAL API TEST SUITE")
    print("\n" + "🧪"*30)
    
    success = run_all_tests()
    
    return 0 if success else 1


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
