#!/usr/bin/env python3
"""
Tests for ChromaKnowledgeBase implementation.

Tests the "dumb" CRUD operations of the knowledge base component.
"""

import os
import sys
from pathlib import Path
from typing import Dict, List
import tempfile

import pytest

# Add src to PYTHONPATH
src_path = str(Path(__file__).parent.parent / "src")
os.environ.setdefault('PYTHONPATH', src_path)
sys.path.insert(0, src_path)

from components.knowledge.chroma_kb import ChromaKnowledgeBase, CustomEmbeddingFunction
from clients.embedder import GoogleEmbedderProvider, MockEmbedderProvider


@pytest.fixture
def temp_kb_dir():
    """Create a temporary directory for ChromaDB persistence."""
    with tempfile.TemporaryDirectory() as temp_dir:
        yield temp_dir


@pytest.fixture
def kb(temp_kb_dir):
    """Create a ChromaKnowledgeBase instance for testing."""
    return ChromaKnowledgeBase(
        persist_directory=temp_kb_dir,
        chunk_size=256,  # Smaller for testing
        chunk_overlap=32
    )


class TestChromaKnowledgeBase:
    """Test suite for ChromaKnowledgeBase."""

    def test_initialization(self, temp_kb_dir):
        """Test that ChromaKnowledgeBase initializes correctly."""
        kb = ChromaKnowledgeBase(persist_directory=temp_kb_dir)

        assert kb.persist_directory == Path(temp_kb_dir)
        assert kb.chunk_size == 512  # default
        assert kb.chunk_overlap == 50  # default
        assert kb.inject_context is True

        # Test collections start empty
        assert kb.list_collections() == []

    def test_store_and_get(self, kb):
        """Test basic store and get operations."""
        content = "This is a test document about artificial intelligence and machine learning."
        metadata = {"source": "test", "topic": "AI"}

        # Store document
        doc_id = kb.store(content, metadata, collection="test")

        assert doc_id is not None
        assert isinstance(doc_id, str)

        # Retrieve document
        doc = kb.get(doc_id, collection="test")

        assert doc is not None
        assert doc["doc_id"] == doc_id
        assert content in doc["content"]  # May be reconstructed from chunks
        assert doc["metadata"]["source"] == "test"

    def test_store_batch(self, kb):
        """Test batch document storage."""
        docs = [
            {"content": "Document 1", "metadata": {"id": 1}},
            {"content": "Document 2", "metadata": {"id": 2}},
            {"content": "Document 3", "metadata": {"id": 3}},
        ]

        doc_ids = kb.store_batch(docs, collection="batch_test")

        assert len(doc_ids) == 3
        assert all(isinstance(doc_id, str) for doc_id in doc_ids)

        # Verify all documents are retrievable
        for doc_id in doc_ids:
            doc = kb.get(doc_id, collection="batch_test")
            assert doc is not None

    def test_retrieve_semantic_search(self, kb):
        """Test semantic search/retrieval."""
        # Store some documents with varying content
        docs = [
            {
                "content": "Python is a programming language used for web development.",
                "metadata": {"topic": "programming"}
            },
            {
                "content": "Java is an object-oriented programming language.",
                "metadata": {"topic": "programming"}
            },
            {
                "content": "Machine learning algorithms process data automatically.",
                "metadata": {"topic": "AI"}
            }
        ]

        kb.store_batch(docs)

        # Search for programming languages
        results = kb.retrieve("programming languages", top_k=3)

        assert len(results) > 0
        assert all("score" in result for result in results)
        assert all(result["score"] > 0 for result in results)

        # First result should be about programming
        assert "programming" in results[0]["content"].lower()

    def test_update_document(self, kb):
        """Test document update functionality."""
        # Store initial document
        doc_id = kb.store("Initial content", {"version": 1})

        # Update content and metadata
        success = kb.update(doc_id, content="Updated content", metadata={"version": 2})

        assert success is True

        # Verify update
        doc = kb.get(doc_id)
        assert doc is not None
        assert "Updated content" in doc["content"]
        assert doc["metadata"]["version"] == 2

    def test_delete_document(self, kb):
        """Test document deletion."""
        doc_id = kb.store("Content to delete", {"marked": "for_deletion"})

        # Verify document exists
        assert kb.get(doc_id) is not None

        # Delete document
        deleted = kb.delete(doc_id)
        assert deleted is True

        # Verify document is gone
        assert kb.get(doc_id) is None

    def test_search_by_metadata(self, kb):
        """Test metadata-based search."""
        docs = [
            {"content": "Doc about Python", "metadata": {"language": "python", "type": "tutorial"}},
            {"content": "Doc about Java", "metadata": {"language": "java", "type": "tutorial"}},
            {"content": "Doc about algorithms", "metadata": {"language": "general", "type": "theory"}},
        ]

        kb.store_batch(docs)

        # Search for tutorials
        results = kb.search_by_metadata({"type": "tutorial"})

        assert len(results) == 2
        assert all(result["metadata"]["type"] == "tutorial" for result in results)

    def test_collection_management(self, kb):
        """Test collection operations."""
        # Create collection implicitly by storing
        kb.store("Test", collection="test_col")

        collections = kb.list_collections()
        assert "test_col" in collections

        # Get collection stats
        stats = kb.get_collection_stats("test_col")
        assert stats["exists"] is True
        assert stats["document_count"] > 0

        # Delete collection
        deleted = kb.delete_collection("test_col")
        assert deleted is True

        # Verify collection is gone
        collections_after = kb.list_collections()
        assert "test_col" not in collections_after

    def test_chunking_behavior(self, kb):
        """Test that long documents are properly chunked."""
        # Create a long document that will definitely be chunked
        long_content = " ".join([f"This is sentence {i} in a very long document that should be split into multiple chunks." for i in range(100)])

        doc_id = kb.store(long_content, {"test": "chunking"})

        # Get the full document
        doc = kb.get(doc_id)
        assert doc is not None
        assert doc["total_chunks"] > 1
        assert len(doc["chunks"]) == doc["total_chunks"]

        # Verify content reconstruction
        assert doc["content"] == long_content

    def test_context_provider_integration(self, kb):
        """Test that ChromaKnowledgeBase properly implements IContextProvider."""
        # Store some documents to have data
        kb.store("AI content", {"topic": "AI"})
        kb.store("ML content", {"topic": "ML"})

        # Get context contribution
        context = kb.get_context_contribution()

        assert "knowledge_base" in context
        kb_context = context["knowledge_base"]

        assert kb_context["available"] is True
        assert "default" in kb_context["collections"]
        assert kb_context["total_documents"] > 0
        assert "retrieval_instructions" in kb_context

    def test_disable_context_injection(self, temp_kb_dir):
        """Test disabling context injection."""
        kb = ChromaKnowledgeBase(persist_directory=temp_kb_dir, inject_context=False)

        assert kb.inject_context is False

        context = kb.get_context_contribution()
        # Should still return context structure but marked as unavailable when no data
        assert "knowledge_base" in context

    def test_embedding_model_info(self, kb):
        """Test embedding model information retrieval."""
        info = kb.get_embedding_model_info()

        assert info["model_name"].startswith("mock/embeddings")
        assert info["provider"] == "mock"
        assert info["local"] is True
        assert info["dimensions"] == 384  # Default MockEmbedderProvider dimensions

    @pytest.mark.skipif(os.getenv('GOOGLE_API_KEY') is None, reason="GOOGLE_API_KEY not available")
    def test_google_embedder_integration(self, temp_kb_dir):
        """Test integration with Google embedding provider."""
        # Create KB with Google embedder
        google_embedder = GoogleEmbedderProvider(
            api_key=os.getenv('GOOGLE_API_KEY')
        )

        kb = ChromaKnowledgeBase(
            persist_directory=temp_kb_dir,
            embedder_provider=google_embedder,
            chunk_size=256
        )

        # Test embedding model info
        info = kb.get_embedding_model_info()
        assert info["provider"] == "googleembedderprovider"
        assert "embedding-001" in info["model_name"]
        assert info["dimensions"] > 0

        # Test basic operations work with Google embeddings
        doc_id = kb.store("Test document for Google embeddings")
        assert doc_id is not None

        results = kb.retrieve("test document", top_k=1)
        assert len(results) > 0

    def test_custom_mock_embedder(self, temp_kb_dir):
        """Test KB with custom mock embedder configuration."""
        # Create mock embedder with specific dimensions
        mock_embedder = MockEmbedderProvider(dimensions=128)

        kb = ChromaKnowledgeBase(
            persist_directory=temp_kb_dir,
            embedder_provider=mock_embedder,
            chunk_size=256
        )

        # Verify embedder configuration is used
        info = kb.get_embedding_model_info()
        assert info["dimensions"] == 128
        assert "128" in info["model_name"]

        # Test operations work
        doc_id = kb.store("Test with custom dimensions")
        results = kb.retrieve("test", top_k=1)
        assert len(results) > 0

    def test_error_handling(self, kb):
        """Test error handling for invalid operations."""
        # Try to get non-existent document
        doc = kb.get("non-existent-id")
        assert doc is None

        # Try to delete non-existent document
        deleted = kb.delete("non-existent-id")
        assert deleted is False

        # Try to get stats for non-existent collection
        stats = kb.get_collection_stats("non-existent")
        assert stats["exists"] is False

    def test_empty_database_operations(self, kb):
        """Test operations on empty database."""
        # Search with no documents
        results = kb.retrieve("anything")
        assert results == []

        # Count documents
        count = kb.count_documents()
        assert count == 0

        # List collections (the default collection gets created on first access)
        collections = kb.list_collections()
        # The collection starts empty but gets created when accessed
        assert "default" in collections or collections == []


def test_mock_embedder_provider():
    """Test MockEmbedderProvider independently."""
    embedder = MockEmbedderProvider(dimensions=128)

    # Test properties
    assert embedder.dimensions == 128
    assert embedder.model_name == "mock/embeddings_128d"

    # Test single embedding
    embedding = embedder.embed_text("test text")
    assert len(embedding) == 128
    assert all(isinstance(x, float) for x in embedding)

    # Test batch embeddings
    texts = ["text 1", "text 2", "text 3"]
    embeddings = embedder.embed_batch(texts)
    assert len(embeddings) == 3
    assert all(len(emb) == 128 for emb in embeddings)

    # Test consistency (same text should give same embedding)
    emb1 = embedder.embed_text("consistent text")
    emb2 = embedder.embed_text("consistent text")
    assert emb1 == emb2


def test_custom_embedding_function():
    """Test the CustomEmbeddingFunction adapter."""
    embedder = MockEmbedderProvider(dimensions=64)
    custom_fn = CustomEmbeddingFunction(embedder)

    # Test ChromaDB interface
    texts = ["hello world", "goodbye world"]
    embeddings = custom_fn(texts)

    assert len(embeddings) == 2
    assert len(embeddings[0]) == 64
    assert len(embeddings[1]) == 64

    # Test name method
    assert custom_fn.name() == "custom_mockembedderprovider"


if __name__ == "__main__":
    pytest.main([__file__])
