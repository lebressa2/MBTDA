#!/usr/bin/env python3
"""
Demo script for Google Embedder Provider.

Shows how to use the GoogleEmbedderProvider to generate embeddings
using Google's Generative AI API, following the user's example.
"""

import os
import sys
from pathlib import Path

# Add src to PYTHONPATH
src_path = str(Path(__file__).parent.parent / "src")
sys.path.insert(0, src_path)

# Import what we need
try:
    from dotenv import load_dotenv
    from clients.embedder import GoogleEmbedderProvider
    from google.genai.types import EmbedContentConfig
    print("✅ Successfully imported GoogleEmbedderProvider")
except ImportError as e:
    print(f"❌ Import error: {e}")
    sys.exit(1)

def demo_google_embeddings():
    """Demo the Google embeddings following user's example."""

    print("🚀 Testing Google Embedder Provider...")

    # Load .env file
    load_dotenv()

    # Check if API key is available
    api_key = os.getenv('GOOGLE_API_KEY')
    if not api_key:
        print("❌ GOOGLE_API_KEY environment variable not set")
        print("   Get your key from: https://aistudio.google.com/app/apikey")
        return

    try:
        # Defina sua chave gratuita do AI Studio (already set in .env)
        # os.environ['GOOGLE_API_KEY'] = 'sua_chave_aqui'  # Ou usaria genai.configure(api_key='sua_chave')

        # Create the provider with text-embedding-004
        embedder = GoogleEmbedderProvider(
            model="models/text-embedding-004",
            api_key=api_key
            # output_dimensionality removed to test default behavior
        )

        print(f"✅ Embedder initialized: {embedder.model_name}")
        print(f"   Dimensions: {embedder.dimensions}")

        # Test single embedding - like user's example
        print("\n📝 Testing single text embedding...")
        result = embedder.embed_text("O que é a vida?")
        print(f"   Embedding dimensions: {len(result)}")
        print(f"   First 5 values: {result[:5]}")

        # Test batch embeddings - like user's example
        print("\n📚 Testing batch embeddings...")
        texts = ["Inteligência Artificial", "Machine Learning", "Redes Neurais"]

        config = EmbedContentConfig(output_dimensionality=128)  # Reduz dimensão para 128

        # For batch with config, need to create new provider or handle manually
        embeddings = embedder.embed_batch(texts)

        print(f"   Batch processed {len(embeddings)} texts:")
        for i, emb in enumerate(embeddings):
            print(f"   Embedding {i}: {emb[:3]}... (dimensions: {len(emb)})")

        print("\n✅ Demo completed successfully!")

    except Exception as e:
        print(f"❌ Demo failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    demo_google_embeddings()
