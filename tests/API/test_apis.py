"""
Test script to verify LLM API connectivity.
"""
import sys
import os
import unittest
from dotenv import load_dotenv

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

load_dotenv()

from tests.clients import GroqTextClient, GoogleTextClient

class TestLLMApis(unittest.TestCase):
    
    def test_groq_api(self):
        print("\nTesting Groq API...")
        try:
            api_key = os.getenv("GROQ_API_KEY")
            if not api_key:
                print("SKIPPING: GROQ_API_KEY not found in env")
                return

            client = GroqTextClient()
            response = client.invoke([{"role": "user", "content": "Say 'Groq is working'"}])
            print(f"Response: {response}")
            self.assertTrue("Groq" in str(response) or "working" in str(response) or len(str(response)) > 0)
            print("✅ Groq API is working")
        except Exception as e:
            print(f"❌ Groq API failed: {e}")
            self.fail(f"Groq API failed: {e}")

    def test_google_api(self):
        print("\nTesting Google API...")
        try:
            api_key = os.getenv("GOOGLE_API_KEY")
            if not api_key:
                print("SKIPPING: GOOGLE_API_KEY not found in env")
                return

            client = GoogleTextClient()
            response = client.invoke([{"role": "user", "content": "Say 'Google is working'"}])
            print(f"Response: {response}")
            self.assertTrue("Google" in str(response) or "working" in str(response) or len(str(response)) > 0)
            print("✅ Google API is working")
        except Exception as e:
            print(f"❌ Google API failed: {e}")
            # Don't fail the test if just google is missing, as long as one works usually, 
            # but here we want to test both if keys exist.
            self.fail(f"Google API failed: {e}")

if __name__ == '__main__':
    unittest.main()
