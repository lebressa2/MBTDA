"""
Google Gemini Embedding Provider for Agent Framework.

Uses Google's Generative AI embeddings for text-to-vector conversion.
Supports both single text and batch embedding operations.

Features:
- Uses Google AI Studio API (free tier available)
- Configurable embedding models and dimensions
- Batch processing for efficiency
"""

import os
from typing import List

try:
    import google.generativeai as genai
    from google.genai.types import EmbedContentConfig
    GOOGLE_AVAILABLE = True
except ImportError:
    GOOGLE_AVAILABLE = False

from ...interfaces.knowledge import IEmbedderProvider


class GoogleEmbedderProvider(IEmbedderProvider):
    """
    Google Gemini embedding provider using Generative AI API.

    Uses Google's embedding models for high-quality text embeddings.
    Supports configurable dimensions for performance optimization.

    Args:
        model: Embedding model name (default: "models/text-embedding-004")
        api_key: Google AI API key (reads from GOOGLE_API_KEY env var if not provided)
        output_dimensionality: Target embedding dimension (None = use model default)
    """

    def __init__(
        self,
        model: str = "models/text-embedding-004",
        api_key: str | None = None,
        output_dimensionality: int | None = None
    ):
        if not GOOGLE_AVAILABLE:
            raise ImportError(
                "google-generativeai package not installed. "
                "Install with: pip install google-generativeai"
            )

        # Configure API key
        self.api_key = api_key or os.getenv('GOOGLE_API_KEY')
        if not self.api_key:
            raise ValueError(
                "GOOGLE_API_KEY environment variable not set. "
                "Get your API key from https://aistudio.google.com/app/apikey"
            )

        genai.configure(api_key=self.api_key)

        self.model = model
        self.output_dimensionality = output_dimensionality

        # Test connection and get dimensions
        self._test_connection()
        self._dimensions = self._get_dimensions()

    def _test_connection(self) -> None:
        """Test API connection with a simple embedding request."""
        try:
            result = genai.embed_content(model=self.model, content="test")
            if not result or 'embedding' not in result:
                raise RuntimeError("Failed to get test embedding from Google API")
        except Exception as e:
            raise RuntimeError(f"Google API connection test failed: {e}")

    def _get_dimensions(self) -> int:
        """Get the actual dimensionality of embeddings."""
        # Use test embedding to determine dimensions
        result = genai.embed_content(model=self.model, content="dimension test")
        return len(result['embedding'])

    def embed_text(self, text: str) -> List[float]:
        """
        Generate embedding vector for a single text.

        Args:
            text: Text to embed

        Returns:
            List[float]: Embedding vector
        """
        try:
            result = genai.embed_content(model=self.model, content=text)
            return result['embedding']
        except Exception as e:
            raise RuntimeError(f"Failed to generate embedding: {e}")

    def embed_batch(self, texts: List[str]) -> List[List[float]]:
        """
        Generate embeddings for multiple texts efficiently.

        Args:
            texts: List of texts to embed

        Returns:
            List[List[float]]: List of embedding vectors
        """
        try:
            result = genai.embed_content(model=self.model, content=texts)

            # Handle different response formats
            if 'embeddings' in result:
                # Batch response format
                return [emb['values'] if isinstance(emb, dict) and 'values' in emb else emb
                       for emb in result['embeddings']]
            elif 'embedding' in result:
                # Single response (shouldn't happen for batch, but handle anyway)
                return [result['embedding']]
            else:
                raise RuntimeError("Unexpected response format from Google API")

        except Exception as e:
            raise RuntimeError(f"Failed to generate batch embeddings: {e}")

    @property
    def dimensions(self) -> int:
        """Get the dimensionality of embeddings."""
        return self._dimensions

    @property
    def model_name(self) -> str:
        """Get the model identifier."""
        return f"google/{self.model.replace('models/', '')}"
