from abc import ABC, abstractmethod
from typing import Any, List, Dict, Optional

class IKnowledgeBase(ABC):
    """
    Interface for knowledge base management.
    """
    @abstractmethod
    def store(
        self,
        content: str,
        metadata: Dict[str, Any] | None = None,
        collection: str | None = None,
        chunk_size: int | None = None,
        chunk_overlap: int | None = None
    ) -> str:
        """Store content in the knowledge base."""
        pass

    @abstractmethod
    def retrieve(
        self,
        query: str,
        top_k: int = 5,
        collection: str | None = None,
        filter_metadata: Dict[str, Any] | None = None,
        min_score: float | None = None
    ) -> List[Dict[str, Any]]:
        """Retrieve relevant information."""
        pass

class IEmbedderProvider(ABC):
    """
    Interface for text embedding providers.
    """
    @abstractmethod
    def embed_text(self, text: str) -> List[float]:
        """Generate embedding vector for a single text."""
        pass

    @abstractmethod
    def embed_batch(self, texts: List[str]) -> List[List[float]]:
        """Generate embeddings for multiple texts."""
        pass

    @property
    @abstractmethod
    def dimensions(self) -> int:
        """Get the dimensionality of embeddings."""
        pass

    @property
    @abstractmethod
    def model_name(self) -> str:
        """Get the name of the embedding model."""
        pass
