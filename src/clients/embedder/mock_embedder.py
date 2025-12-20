"""
Mock Embedding Provider for Testing.

Provides deterministic, random-like embeddings for testing knowledge bases
without requiring external API calls or model downloads.

Features:
- Deterministic embeddings based on text content (consistent for same input)
- Configurable dimensions
- No external dependencies
- Fast for testing scenarios
"""

import hashlib
import struct
from typing import List

from ...interfaces.knowledge import IEmbedderProvider


class MockEmbedderProvider(IEmbedderProvider):
    """
    Mock embedding provider for testing.

    Generates deterministic "embeddings" based on text content hash.
    Useful for testing knowledge base functionality without API calls.

    The embeddings are pseudo-random but consistent for the same input text,
    making tests reproducible while providing realistic vector behavior.
    """

    def __init__(self, dimensions: int = 384, model_name: str = "mock/embeddings"):
        """
        Initialize mock embedder.

        Args:
            dimensions: Vector dimensionality (default: 384, similar to sentence-transformers)
            model_name: Model identifier for this mock provider
        """
        self._dimensions = dimensions
        self._model_name = model_name

    def embed_text(self, text: str) -> List[float]:
        """
        Generate deterministic "embedding" for a single text.

        Uses SHA256 hash of the text to create a deterministic vector.
        The result is normalized to simulate real embeddings.

        Args:
            text: Text to "embed"

        Returns:
            List[float]: Pseudo-random but deterministic embedding vector
        """
        return self._generate_embedding(text)

    def embed_batch(self, texts: List[str]) -> List[List[float]]:
        """
        Generate embeddings for multiple texts.

        Args:
            texts: List of texts to embed

        Returns:
            List[List[float]]: List of embedding vectors
        """
        return [self._generate_embedding(text) for text in texts]

    def _generate_embedding(self, text: str) -> List[float]:
        """
        Generate deterministic embedding from text.

        Uses text hash to seed deterministic pseudo-random values,
        then normalizes the vector for realistic behavior.

        Args:
            text: Input text

        Returns:
            List[float]: Normalized embedding vector
        """
        # Create hash from text
        hash_obj = hashlib.sha256(text.encode('utf-8'))
        hash_bytes = hash_obj.digest()

        # Generate deterministic floats from hash
        embedding = []
        for i in range(self._dimensions):
            # Use different parts of hash for each dimension
            start_idx = (i * 4) % len(hash_bytes)
            chunk = hash_bytes[start_idx:start_idx + 4]
            if len(chunk) < 4:
                chunk += b'\x00' * (4 - len(chunk))

            # Convert to float between -1 and 1 (similar to real embeddings)
            value = struct.unpack('<f', chunk)[0] % 2.0 - 1.0
            embedding.append(value)

        # Normalize the vector (approximate L2 normalization)
        magnitude = sum(x ** 2 for x in embedding) ** 0.5
        if magnitude > 0:
            embedding = [x / magnitude for x in embedding]

        return embedding

    @property
    def dimensions(self) -> int:
        """Get embedding dimensionality."""
        return self._dimensions

    @property
    def model_name(self) -> str:
        """Get model identifier."""
        return f"{self._model_name}_{self._dimensions}d"
