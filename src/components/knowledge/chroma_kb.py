"""
ChromaDB-based Knowledge Base implementation for the Agent Framework.

Provides semantic storage and retrieval using local ChromaDB vector database.
This is a "dumb" CRUD component - just basic operations, no intelligence.

Features:
- Document storage with metadata
- Semantic similarity search
- Collection/namespace management
- Automatic context contribution for agent prompts
"""

import os
import uuid
from pathlib import Path
from typing import Any, Dict, List, Optional

import chromadb
from chromadb.config import Settings

from ...interfaces.base import IKnowledgeBase, IEmbedderProvider
from ...clients.embedder.mock_embedder import MockEmbedderProvider


class CustomEmbeddingFunction:
    """
    Adapter to use IEmbedderProvider with ChromaDB's embedding function interface.
    """

    def __init__(self, embedder_provider: IEmbedderProvider):
        self.embedder = embedder_provider

    def __call__(self, input: List[str]) -> List[List[float]]:
        """
        ChromaDB embedding function interface.

        Args:
            input: List of texts to embed

        Returns:
            List of embedding vectors
        """
        return self.embedder.embed_batch(input)

    def name(self) -> str:
        """Return the name of this embedding function (ChromaDB requirement)."""
        return f"custom_{self.embedder.__class__.__name__.lower()}"


class ChromaKnowledgeBase(IKnowledgeBase):
    """
    ChromaDB implementation of IKnowledgeBase.

    Stores documents in vector format for semantic retrieval.
    Uses sentence-transformers for embeddings by default.

    This component is intentionally "dumb" - just CRUD operations.
    Intelligence should come from higher-level components that use this.
    """

    def __init__(
        self,
        persist_directory: str = "./chroma_kb",
        embedder_provider: Optional[IEmbedderProvider] = None,
        chunk_size: int = 512,
        chunk_overlap: int = 50,
        inject_context: bool = True
    ):
        """
        Initialize ChromaDB knowledge base.

        Args:
            persist_directory: Directory to persist ChromaDB data
            embedder_provider: Embedding provider to use (defaults to MockEmbedderProvider)
            chunk_size: Default chunk size for long documents
            chunk_overlap: Overlap between chunks
            inject_context: Whether to auto-inject context in prompts
        """
        self.persist_directory = Path(persist_directory)
        self.persist_directory.mkdir(parents=True, exist_ok=True)

        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        self.inject_context = inject_context

        # Set up embedder provider
        self.embedder = embedder_provider or MockEmbedderProvider()

        # Initialize ChromaDB client
        self.client = chromadb.PersistentClient(
            path=str(self.persist_directory),
            settings=Settings(
                anonymized_telemetry=False,
                allow_reset=True
            )
        )

        # Create custom embedding function that uses our provider
        self.embedding_fn = CustomEmbeddingFunction(self.embedder)

        # Cache for collections to avoid repeated lookups
        self._collections_cache: Dict[str, Any] = {}

    def _get_or_create_collection(self, name: str) -> Any:
        """
        Get or create a ChromaDB collection.

        Args:
            name: Collection name

        Returns:
            ChromaDB collection object
        """
        if name not in self._collections_cache:
            self._collections_cache[name] = self.client.get_or_create_collection(
                name=name,
                embedding_function=self.embedding_fn
            )
        return self._collections_cache[name]

    def _generate_doc_id(self) -> str:
        """Generate a unique document ID."""
        return str(uuid.uuid4())

    def _chunk_text(self, text: str, chunk_size: int, overlap: int) -> List[str]:
        """
        Split text into overlapping chunks.

        Args:
            text: Text to chunk
            chunk_size: Maximum chunk size
            overlap: Overlap between chunks

        Returns:
            List of text chunks
        """
        if len(text) <= chunk_size:
            return [text]

        chunks = []
        start = 0

        while start < len(text):
            end = start + chunk_size

            # Don't break in middle of word if possible
            if end < len(text):
                # Find last space within chunk
                last_space = text.rfind(' ', start, end)
                if last_space > start:
                    end = last_space

            chunk = text[start:end].strip()
            if chunk:  # Don't add empty chunks
                chunks.append(chunk)

            start = max(start + 1, end - overlap)

        return chunks

    # ==========================================================================
    # CORE STORAGE OPERATIONS (BURRO - apenas CRUD básico)
    # ==========================================================================

    def store(
        self,
        content: str,
        metadata: Optional[Dict[str, Any]] = None,
        collection: str = "default",
        chunk_size: Optional[int] = None,
        chunk_overlap: Optional[int] = None
    ) -> str:
        """
        Store content in the knowledge base with automatic chunking.

        Args:
            content: Text content to store
            metadata: Optional metadata (source, timestamp, tags, etc.)
            collection: Collection name (default: "default")
            chunk_size: Override default chunk size
            chunk_overlap: Override default chunk overlap

        Returns:
            str: Unique document ID
        """
        doc_id = self._generate_doc_id()
        coll = self._get_or_create_collection(collection)

        # Use provided or default chunking params
        cs = chunk_size or self.chunk_size
        co = chunk_overlap or self.chunk_overlap

        # Chunk the content
        chunks = self._chunk_text(content, cs, co)

        # Prepare data for ChromaDB
        ids = []
        documents = []
        metadatas = []

        for i, chunk in enumerate(chunks):
            chunk_id = f"{doc_id}_chunk_{i}"
            chunk_metadata = metadata.copy() if metadata else {}
            chunk_metadata.update({
                "doc_id": doc_id,
                "chunk_index": i,
                "total_chunks": len(chunks),
                "original_length": len(content),
                "chunk_length": len(chunk)
            })

            ids.append(chunk_id)
            documents.append(chunk)
            metadatas.append(chunk_metadata)

        # Store in ChromaDB
        coll.add(
            ids=ids,
            documents=documents,
            metadatas=metadatas
        )

        return doc_id

    def store_batch(
        self,
        documents: List[Dict[str, Any]],
        collection: str = "default"
    ) -> List[str]:
        """
        Store multiple documents efficiently.

        Args:
            documents: List of dicts with 'content' and optional 'metadata'
            collection: Collection to store in

        Returns:
            List[str]: List of document IDs
        """
        doc_ids = []
        all_ids = []
        all_documents = []
        all_metadatas = []

        coll = self._get_or_create_collection(collection)

        for doc_data in documents:
            content = doc_data.get("content", "")
            metadata = doc_data.get("metadata", {})

            doc_id = self._generate_doc_id()

            # Chunk the content
            chunks = self._chunk_text(content, self.chunk_size, self.chunk_overlap)

            # Prepare chunks for this document
            for i, chunk in enumerate(chunks):
                chunk_id = f"{doc_id}_chunk_{i}"
                chunk_metadata = metadata.copy()
                chunk_metadata.update({
                    "doc_id": doc_id,
                    "chunk_index": i,
                    "total_chunks": len(chunks),
                    "original_length": len(content),
                    "chunk_length": len(chunk)
                })

                all_ids.append(chunk_id)
                all_documents.append(chunk)
                all_metadatas.append(chunk_metadata)

            doc_ids.append(doc_id)

        # Batch store in ChromaDB
        if all_ids:
            coll.add(
                ids=all_ids,
                documents=all_documents,
                metadatas=all_metadatas
            )

        return doc_ids

    def update(
        self,
        doc_id: str,
        content: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
        collection: str = "default"
    ) -> bool:
        """
        Update an existing document.

        For simplicity, this deletes and re-inserts the document.

        Args:
            doc_id: Document ID to update
            content: New content (None = keep existing)
            metadata: New metadata (merged with existing)
            collection: Collection containing the document

        Returns:
            bool: True if updated successfully
        """
        try:
            coll = self._get_or_create_collection(collection)

            # First get existing chunks
            existing = coll.get(where={"doc_id": doc_id})
            if not existing['ids']:
                return False

            # Delete existing chunks
            coll.delete(ids=existing['ids'])

            # If content provided, re-insert with new content
            if content is not None:
                # Merge metadata if provided
                final_metadata = existing['metadatas'][0].copy() if metadata is None else metadata

                # Re-store the document
                new_doc_id = self.store(content, final_metadata, collection)
                return new_doc_id == doc_id

            # If no content change, just update metadata
            elif metadata is not None:
                # Re-insert chunks with updated metadata
                for i, chunk_id in enumerate(existing['ids']):
                    chunk_metadata = metadata.copy()
                    chunk_metadata.update({
                        "doc_id": doc_id,
                        "chunk_index": i,
                        "total_chunks": len(existing['ids'])
                    })

                    # Keep original content, update metadata
                    coll.upsert(
                        ids=[chunk_id],
                        documents=[existing['documents'][i]],
                        metadatas=[chunk_metadata]
                    )

            return True

        except Exception:
            return False

    def delete(self, doc_id: str, collection: str = "default") -> bool:
        """
        Delete a document and all its chunks.

        Args:
            doc_id: Document ID to delete
            collection: Collection containing the document

        Returns:
            bool: True if deleted successfully
        """
        try:
            coll = self._get_or_create_collection(collection)
            coll.delete(where={"doc_id": doc_id})
            return True
        except Exception:
            return False

    def get(self, doc_id: str, collection: str = "default") -> Optional[Dict[str, Any]]:
        """
        Retrieve a document by ID.

        Returns the first chunk's metadata, plus all chunks.

        Args:
            doc_id: Document ID
            collection: Collection containing the document

        Returns:
            dict | None: Document info with content, metadata, chunks
        """
        try:
            coll = self._get_or_create_collection(collection)
            result = coll.get(where={"doc_id": doc_id})

            if not result['ids']:
                return None

            # Reconstruct document from chunks
            chunks = []
            for i, chunk_id in enumerate(result['ids']):
                chunks.append({
                    "chunk_index": i,
                    "content": result['documents'][i],
                    "metadata": result['metadatas'][i]
                })

            # Sort by chunk_index
            chunks.sort(key=lambda x: x['chunk_index'])

            # Return document info
            return {
                "doc_id": doc_id,
                "content": " ".join(c['content'] for c in chunks),  # Reconstructed
                "metadata": chunks[0]['metadata'],  # First chunk metadata
                "chunks": chunks,
                "total_chunks": len(chunks)
            }

        except Exception:
            return None

    # ==========================================================================
    # RETRIEVAL & SEARCH OPERATIONS
    # ==========================================================================

    def retrieve(
        self,
        query: str,
        top_k: int = 5,
        collection: str = "default",
        filter_metadata: Optional[Dict[str, Any]] = None,
        min_score: Optional[float] = None
    ) -> List[Dict[str, Any]]:
        """
        Retrieve relevant chunks using semantic search.

        Args:
            query: Search query text
            top_k: Number of results to return
            collection: Collection to search in
            filter_metadata: Filter by metadata fields
            min_score: Minimum similarity score threshold

        Returns:
            List of results with content, metadata, score, doc_id
        """
        try:
            coll = self._get_or_create_collection(collection)

            # Build where clause for metadata filtering
            where_clause = None
            if filter_metadata:
                where_clause = filter_metadata

            # Query ChromaDB
            results = coll.query(
                query_texts=[query],
                n_results=top_k,
                where=where_clause,
                include=['documents', 'metadatas', 'distances']
            )

            # Format results
            formatted_results = []
            if results['documents'] and results['metadatas'] and results['distances']:
                documents = results['documents'][0]
                metadatas = results['metadatas'][0]
                distances = results['distances'][0]

                for i, (doc, meta, dist) in enumerate(zip(documents, metadatas, distances)):
                    # Convert distance to similarity score (1 - normalized distance)
                    score = 1.0 - (dist / 2.0) if dist <= 2.0 else 0.0

                    # Filter by min_score if provided
                    if min_score is not None and score < min_score:
                        continue

                    formatted_results.append({
                        "content": doc,
                        "metadata": meta,
                        "score": score,
                        "doc_id": meta.get("doc_id", f"unknown_{i}")
                    })

            return formatted_results

        except Exception:
            return []

    def search_similar(
        self,
        text: str,
        threshold: float = 0.7,
        collection: str = "default",
        max_results: int = 10
    ) -> List[Dict[str, Any]]:
        """
        Find documents similar to the given text.

        Args:
            text: Text to find similar documents for
            threshold: Minimum similarity score
            collection: Collection to search in
            max_results: Maximum number of results

        Returns:
            List of similar documents with scores
        """
        results = self.retrieve(
            query=text,
            top_k=max_results,
            collection=collection,
            min_score=threshold
        )
        return results

    def search_by_metadata(
        self,
        filters: Dict[str, Any],
        collection: str = "default",
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """
        Search documents by metadata filters.

        Args:
            filters: Metadata filters
            collection: Collection to search in
            limit: Maximum results

        Returns:
            List of matching documents
        """
        try:
            coll = self._get_or_create_collection(collection)

            # Get all documents matching the filter
            results = coll.get(where=filters, limit=limit, include=['documents', 'metadatas'])

            # Format results
            formatted_results = []
            if results['documents'] and results['metadatas']:
                for doc, meta in zip(results['documents'], results['metadatas']):
                    formatted_results.append({
                        "content": doc,
                        "metadata": meta,
                        "doc_id": meta.get("doc_id", "unknown")
                    })

            return formatted_results

        except Exception:
            return []

    # ==========================================================================
    # COLLECTION MANAGEMENT
    # ==========================================================================

    def create_collection(self, name: str, metadata: Optional[Dict[str, Any]] = None) -> bool:
        """
        Create a new collection.

        Args:
            name: Collection name
            metadata: Optional collection metadata

        Returns:
            True if created successfully
        """
        try:
            # ChromaDB creates collections on first access
            coll = self._get_or_create_collection(name)
            return True
        except Exception:
            return False

    def delete_collection(self, name: str) -> bool:
        """
        Delete an entire collection.

        Args:
            name: Collection name

        Returns:
            True if deleted successfully
        """
        try:
            self.client.delete_collection(name)
            # Remove from cache
            if name in self._collections_cache:
                del self._collections_cache[name]
            return True
        except Exception:
            return False

    def list_collections(self) -> List[str]:
        """
        List all collections.

        Returns:
            List of collection names
        """
        try:
            collections = self.client.list_collections()
            return [col.name for col in collections]
        except Exception:
            return []

    def get_collection_stats(self, name: str) -> Dict[str, Any]:
        """
        Get statistics about a collection.

        Args:
            name: Collection name

        Returns:
            Stats dictionary
        """
        try:
            if name not in self.list_collections():
                return {"exists": False}

            coll = self._get_or_create_collection(name)
            count = coll.count()

            return {
                "exists": True,
                "document_count": count,
                "name": name
            }
        except Exception:
            return {"exists": False, "error": "Failed to get stats"}

    # ==========================================================================
    # CONTEXT PROVIDER IMPLEMENTATION
    # ==========================================================================

    def get_context_contribution(self) -> Dict[str, Any]:
        """
        Provide knowledge base information for agent context.

        Returns:
            Dictionary with knowledge base information
        """
        collections = self.list_collections()
        total_docs = sum(self.count_documents(col) for col in collections) if collections else 0

        return {
            "knowledge_base": {
                "available": True,
                "collections": collections,
                "total_documents": total_docs,
                "retrieval_instructions": "Use knowledge base methods to store and retrieve information"
            }
        }

    # ==========================================================================
    # UTILITY & CONFIGURATION
    # ==========================================================================

    def clear(self, collection: Optional[str] = None) -> bool:
        """
        Clear all documents from collection(s).

        Args:
            collection: Collection to clear (None = all)

        Returns:
            True if cleared successfully
        """
        try:
            if collection:
                coll = self._get_or_create_collection(collection)
                # Get all document IDs
                results = coll.get(include=[])
                if results['ids']:
                    coll.delete(ids=results['ids'])
            else:
                # Clear all collections
                for col_name in self.list_collections():
                    self.clear(col_name)
            return True
        except Exception:
            return False

    def count_documents(self, collection: Optional[str] = None) -> int:
        """
        Count documents in a collection or all collections.

        Args:
            collection: Collection name (None = all)

        Returns:
            Number of documents
        """
        try:
            if collection:
                if collection not in self.list_collections():
                    return 0
                coll = self._get_or_create_collection(collection)
                return coll.count()
            else:
                return sum(self.count_documents(col) for col in self.list_collections())
        except Exception:
            return 0

    def get_embedding_model_info(self) -> Dict[str, Any]:
        """
        Get information about the embedding model.

        Returns:
            Model information
        """
        try:
            return {
                "model_name": self.embedder.model_name,
                "provider": self.embedder.__class__.__name__.replace('EmbedderProvider', '').lower(),
                "local": True,  # For now assuming all are local (could be extended for cloud services)
                "dimensions": self.embedder.dimensions
            }
        except Exception:
            return {
                "model_name": getattr(self.embedder, 'model_name', 'unknown'),
                "provider": self.embedder.__class__.__name__,
                "local": True,
                "dimensions": getattr(self.embedder, 'dimensions', 'unknown')
            }

    def reindex(self, collection: Optional[str] = None, batch_size: int = 100) -> bool:
        """
        Reindex documents (no-op for ChromaDB since it handles indexing automatically).

        Args:
            collection: Collection to reindex
            batch_size: Ignored for ChromaDB

        Returns:
            True (ChromaDB handles indexing automatically)
        """
        # ChromaDB automatically handles indexing, no manual reindexing needed
        return True
