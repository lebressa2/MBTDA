"""
Base Interfaces (Protocols) for the Agent Framework.

This module defines all abstract interfaces that components must implement.
Using Python's Protocol for structural subtyping (duck typing with type safety).
"""

from abc import ABC, abstractmethod
from enum import Enum
from typing import Any

# ==============================================================================
# ENUMS
# ==============================================================================

class LogLevel(Enum):
    """Log levels for the ILogger interface."""
    DEBUG = "DEBUG"
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"


# ==============================================================================
# CONTEXT PROVIDER INTERFACE (Base for context-injecting components)
# ==============================================================================

# IContextProvider removed in Phase 2

    


# ==============================================================================
# CORE INTERFACES
# ==============================================================================

class ITextClient(ABC):
    """
    Interface for text generation clients (LLM providers).

    Implementations can use langchain-groq, langchain-google, or any other
    LangChain-compatible provider. Works with langchain.BaseMessage.
    """

    @abstractmethod
    def invoke(self, messages: list[Any], **kwargs) -> Any:
        """
        Invoke the LLM with a list of messages.

        Args:
            messages: List of BaseMessage objects
            **kwargs: Additional parameters (temperature, max_tokens, etc.)

        Returns:
            BaseMessage: The LLM response
        """
        pass

    @abstractmethod
    def bind_tools(self, tools: list[Any]) -> "ITextClient":
        """
        Bind tools to the LLM for function calling.

        Args:
            tools: List of LangChain Tool objects

        Returns:
            ITextClient: A new client instance with tools bound
        """
        pass

    @abstractmethod
    def get_model_name(self) -> str:
        """Get the name of the underlying model."""
        pass


class IFormatter(ABC):
    """
    Interface for context formatting.

    Responsible for converting context dictionaries into formatted strings
    suitable for system prompts.
    """

    @abstractmethod
    def format(self, context: dict[str, Any]) -> str:
        """
        Format a context dictionary into a string.

        Args:
            context: Dictionary containing context data

        Returns:
            str: Formatted string representation
        """
        pass


class IMemoryManager(ABC):
    """
    Interface for memory management.

    Handles short-term memory, long-term memory, and retrieval operations.
    """

    @abstractmethod
    def add_message(self, role: str, content: str, metadata: dict | None = None) -> None:
        """Add a message to short-term memory."""
        pass

    @abstractmethod
    def get_recent_messages(self, limit: int = 10) -> list[dict[str, Any]]:
        """Retrieve recent messages from short-term memory."""
        pass

    @abstractmethod
    def store_long_term(self, key: str, value: Any, metadata: dict | None = None) -> None:
        """Store information in long-term memory."""
        pass

    @abstractmethod
    def retrieve(self, query: str, top_k: int = 5) -> list[dict[str, Any]]:
        """Retrieve relevant memories based on a query."""
        pass



class IToolManager(ABC):
    """
    Interface for tool management.

    Handles tool registration, execution, and retrieval.
    Tools are organized by context/category.
    """

    @abstractmethod
    def register_tool(self, context: str, tool: Any) -> None:
        """
        Register a tool under a specific context.

        Args:
            context: Category/context for the tool (e.g., 'retriever_funcs')
            tool: LangChain Tool object
        """
        pass

    @abstractmethod
    def get_tools(self, contexts: list[str] | None = None) -> list[Any]:
        """
        Get tools, optionally filtered by contexts.

        Args:
            contexts: List of contexts to filter by (None = all tools)

        Returns:
            List of Tool objects
        """
        pass

    @abstractmethod
    def get_tool_descriptions(self, contexts: list[str] | None = None) -> str:
        """Get formatted descriptions of available tools."""
        pass



class IWatchdog(ABC):
    """
    Interface for watchdog/timer functionality.

    Controls timeouts and polling intervals for reactive mode.
    """

    @abstractmethod
    def start_timer(self, duration_seconds: float) -> None:
        """Start a timer for the specified duration."""
        pass

    @abstractmethod
    def stop_timer(self) -> None:
        """Stop the current timer."""
        pass

    @abstractmethod
    def is_timed_out(self) -> bool:
        """Check if the timer has expired."""
        pass

    @abstractmethod
    def get_poll_interval(self) -> float:
        """Get the polling interval for reactive mode."""
        pass

    @abstractmethod
    def set_poll_interval(self, interval_seconds: float) -> None:
        """Set the polling interval for reactive mode."""
        pass

    @abstractmethod
    def reset(self) -> None:
        """Reset the watchdog timer."""
        pass


class ILogger(ABC):
    """
    Interface for logging.

    Supports various output destinations (terminal, file, subprocess, etc.)
    Must be able to log thinking tokens and tool calls.
    """

    @abstractmethod
    def debug(self, message: str, **kwargs) -> None:
        """Log a debug message."""
        pass

    @abstractmethod
    def info(self, message: str, **kwargs) -> None:
        """Log an info message."""
        pass

    @abstractmethod
    def warning(self, message: str, **kwargs) -> None:
        """Log a warning message."""
        pass

    @abstractmethod
    def error(self, message: str, **kwargs) -> None:
        """Log an error message."""
        pass

    @abstractmethod
    def critical(self, message: str, **kwargs) -> None:
        """Log a critical message."""
        pass

    @abstractmethod
    def log_thinking(self, thought: str, **kwargs) -> None:
        """Log agent thinking tokens."""
        pass

    @abstractmethod
    def log_tool_call(self, tool_name: str, args: dict, result: Any, **kwargs) -> None:
        """Log a tool call with arguments and result."""
        pass


class ILifeCycle(ABC):
    """
    Interface for lifecycle and resource management.

    Handles token counting, rate limits, resource usage, API errors,
    message limits, and other guardrails for limited resources.
    """

    @abstractmethod
    def count_tokens(self, text: str) -> int:
        """Count tokens in a text string."""
        pass

    @abstractmethod
    def get_token_usage(self) -> dict[str, int]:
        """Get current token usage statistics."""
        pass

    @abstractmethod
    def check_rate_limit(self) -> bool:
        """Check if rate limit allows another request."""
        pass

    @abstractmethod
    def record_request(self, tokens_used: int) -> None:
        """Record a request for rate limiting purposes."""
        pass

    @abstractmethod
    def get_resource_usage(self) -> dict[str, Any]:
        """Get current resource usage (memory, GPU, etc.)."""
        pass

    @abstractmethod
    def set_limits(self, **limits) -> None:
        """
        Set resource limits.

        Args:
            **limits: Limit parameters (max_tokens, requests_per_minute, etc.)
        """
        pass

    @abstractmethod
    def check_guardrails(self) -> dict[str, bool]:
        """Check all guardrails and return their status."""
        pass

    @abstractmethod
    def handle_api_error(self, error: Exception) -> bool:
        """
        Handle an API error.

        Returns:
            bool: True if the error was handled and operation can retry
        """
        pass


class IWorkspaceManager(ABC):
    """
    Interface for workspace management.

    Manages the isolated environment (physical or virtual) where the agent works.
    Provides a controlled sandbox for file operations, version control,
    and computational environments.
    """

    @abstractmethod
    def create_file(self, path: str, content: str) -> bool:
        """Create a file at the specified path with given content."""
        pass

    @abstractmethod
    def read_file(self, path: str) -> str | None:
        """Read the content of a file."""
        pass

    @abstractmethod
    def update_file(self, path: str, content: str) -> bool:
        """Update the content of an existing file."""
        pass

    @abstractmethod
    def delete_file(self, path: str) -> bool:
        """Delete a file."""
        pass

    @abstractmethod
    def create_directory(self, path: str) -> bool:
        """Create a directory."""
        pass

    @abstractmethod
    def delete_directory(self, path: str, recursive: bool = False) -> bool:
        """Delete a directory."""
        pass

    @abstractmethod
    def list_directory(self, path: str) -> list[str]:
        """List contents of a directory."""
        pass

    @abstractmethod
    def file_exists(self, path: str) -> bool:
        """Check if a file exists."""
        pass

    @abstractmethod
    def create_snapshot(self, name: str) -> str:
        """Create a version snapshot of the current workspace state."""
        pass

    @abstractmethod
    def restore_snapshot(self, snapshot_id: str) -> bool:
        """Restore workspace to a previous snapshot."""
        pass

    @abstractmethod
    def get_storage_usage(self) -> dict[str, Any]:
        """Get storage usage statistics."""
        pass

    @abstractmethod
    def set_storage_limit(self, limit_bytes: int) -> None:
        """Set the storage limit for the workspace."""
        pass

    @abstractmethod
    def execute_command(self, command: str, timeout: float | None = None) -> dict[str, Any]:
        """Execute a command in the isolated environment."""
        pass



# ==============================================================================
# MONITORING INTERFACES (Inbox & Tasks)
# ==============================================================================

class IInboxClient(ABC):
    """
    Interface for inbox/email operations.

    Used by the inbox_tool to provide email functionality.
    """

    @abstractmethod
    def check_new_emails(self) -> list[Any]:
        """
        Check for new emails.

        Returns:
            List[EmailMessage]: List of new email messages
        """
        pass

    @abstractmethod
    def send_email(
        self,
        to: str,
        subject: str,
        body: str,
        cc: list[str] | None = None,
        bcc: list[str] | None = None
    ) -> bool:
        """
        Send an email.

        Returns:
            bool: True if email was sent successfully
        """
        pass

    @abstractmethod
    def mark_as_read(self, thread_id: str) -> bool:
        """Mark an email thread as read."""
        pass

    @abstractmethod
    def archive(self, thread_id: str) -> bool:
        """Archive an email thread."""
        pass


class ITaskManager(ABC):
    """
    Interface for task management operations.

    Used by the task_tool to provide task functionality.
    """

    @abstractmethod
    def get_pending_tasks(self) -> list[Any]:
        """
        Get all pending tasks.

        Returns:
            List[TaskItem]: List of pending tasks
        """
        pass

    @abstractmethod
    def create_task(
        self,
        title: str,
        due_date: str | None = None,
        priority: int = 1,
        description: str | None = None
    ) -> str:
        """
        Create a new task.

        Returns:
            str: The task ID of the created task
        """
        pass

    @abstractmethod
    def update_task_status(self, task_id: str, status: str) -> bool:
        """
        Update the status of a task.

        Args:
            task_id: The task ID
            status: New status (e.g., 'pending', 'in_progress', 'completed')

        Returns:
            bool: True if update was successful
        """
        pass

    @abstractmethod
    def get_task(self, task_id: str) -> Any | None:
        """Get a specific task by ID."""
        pass

    @abstractmethod
    def delete_task(self, task_id: str) -> bool:
        """Delete a task."""
        pass

    @abstractmethod
    def get_overdue_tasks(self) -> list[Any]:
        """Get all overdue tasks."""
        pass

    # ==============================================================================
#
# ENHANCED KNOWLEDGE BASE FOR AGENT FRAMEWORK
#
#Provides comprehensive knowledge storage, retrieval, and management
#with semantic search capabilities.
# ==============================================================================

from abc import abstractmethod
from typing import Any, List



class IKnowledgeBase(ABC):
    """
    Interface for Knowledge Base implementations with RAG capabilities.
    
    A knowledge base stores and retrieves information using semantic search,
    enabling agents to access relevant context beyond their training data.
    
    Key Features:
    - Document storage with metadata
    - Semantic similarity search
    - Collection/namespace management
    - CRUD operations for knowledge entries
    - Context injection for agent prompts
    
    Implementations might use:
    - Vector databases (ChromaDB, Pinecone, Weaviate)
    - Embedding models (OpenAI, sentence-transformers)
    - Chunking strategies for large documents
    """
    
    
    # ==========================================================================
    # CORE STORAGE OPERATIONS
    # ==========================================================================
    
    @abstractmethod
    def store(
        self,
        content: str,
        metadata: dict[str, Any] | None = None,
        collection: str | None = None,
        chunk_size: int | None = None,
        chunk_overlap: int | None = None
    ) -> str:
        """
        Store content in the knowledge base with optional chunking.
        
        Args:
            content: Text content to store
            metadata: Optional metadata (source, timestamp, tags, etc.)
            collection: Collection/namespace to store in (None = default)
            chunk_size: Override default chunk size for this content
            chunk_overlap: Override default chunk overlap
            
        Returns:
            str: Unique document ID
            
        Example:
            doc_id = kb.store(
                content="Long document text...",
                metadata={"source": "manual.pdf", "page": 42, "tags": ["python"]},
                collection="documentation"
            )
        """
        pass
    
    @abstractmethod
    def store_batch(
        self,
        documents: list[dict[str, Any]],
        collection: str | None = None
    ) -> list[str]:
        """
        Store multiple documents efficiently.
        
        Args:
            documents: List of dicts with 'content' and optional 'metadata'
            collection: Collection to store in
            
        Returns:
            list[str]: List of document IDs
            
        Example:
            ids = kb.store_batch([
                {"content": "Doc 1", "metadata": {"source": "file1.txt"}},
                {"content": "Doc 2", "metadata": {"source": "file2.txt"}}
            ])
        """
        pass
    
    @abstractmethod
    def update(
        self,
        doc_id: str,
        content: str | None = None,
        metadata: dict[str, Any] | None = None,
        collection: str | None = None
    ) -> bool:
        """
        Update an existing document.
        
        Args:
            doc_id: Document ID to update
            content: New content (None = keep existing)
            metadata: New metadata (merged with existing)
            collection: Collection containing the document
            
        Returns:
            bool: True if updated successfully
        """
        pass
    
    @abstractmethod
    def delete(
        self,
        doc_id: str,
        collection: str | None = None
    ) -> bool:
        """
        Delete a document from the knowledge base.
        
        Args:
            doc_id: Document ID to delete
            collection: Collection containing the document
            
        Returns:
            bool: True if deleted successfully
        """
        pass
    
    @abstractmethod
    def get(
        self,
        doc_id: str,
        collection: str | None = None
    ) -> dict[str, Any] | None:
        """
        Retrieve a document by ID.
        
        Args:
            doc_id: Document ID
            collection: Collection containing the document
            
        Returns:
            dict | None: Document with content, metadata, and embeddings info
        """
        pass
    
    # ==========================================================================
    # RETRIEVAL & SEARCH OPERATIONS
    # ==========================================================================
    
    @abstractmethod
    def retrieve(
        self,
        query: str,
        top_k: int = 5,
        collection: str | None = None,
        filter_metadata: dict[str, Any] | None = None,
        min_score: float | None = None
    ) -> list[dict[str, Any]]:
        """
        Retrieve relevant chunks using semantic search.
        
        Args:
            query: Search query text
            top_k: Number of results to return
            collection: Collection to search in (None = all collections)
            filter_metadata: Filter by metadata fields (e.g., {"source": "manual.pdf"})
            min_score: Minimum similarity score threshold (0.0-1.0)
            
        Returns:
            list[dict]: List of results with 'content', 'metadata', 'score', 'doc_id'
            
        Example:
            results = kb.retrieve(
                query="How to configure the agent?",
                top_k=3,
                filter_metadata={"tags": "configuration"},
                min_score=0.7
            )
        """
        pass
    
    @abstractmethod
    def search_similar(
        self,
        text: str,
        threshold: float = 0.7,
        collection: str | None = None,
        max_results: int = 10
    ) -> list[dict[str, Any]]:
        """
        Find documents similar to the given text.
        
        Args:
            text: Text to find similar documents for
            threshold: Minimum similarity score (0.0-1.0)
            collection: Collection to search in
            max_results: Maximum number of results
            
        Returns:
            list[dict]: Similar documents with scores
        """
        pass
    
    @abstractmethod
    def search_by_metadata(
        self,
        filters: dict[str, Any],
        collection: str | None = None,
        limit: int = 100
    ) -> list[dict[str, Any]]:
        """
        Search documents by metadata filters.
        
        Args:
            filters: Metadata filters (e.g., {"source": "manual.pdf", "page": 42})
            collection: Collection to search in
            limit: Maximum results
            
        Returns:
            list[dict]: Matching documents
        """
        pass
    
    # ==========================================================================
    # COLLECTION MANAGEMENT
    # ==========================================================================
    
    @abstractmethod
    def create_collection(
        self,
        name: str,
        metadata: dict[str, Any] | None = None
    ) -> bool:
        """
        Create a new collection/namespace.
        
        Args:
            name: Collection name
            metadata: Optional collection-level metadata
            
        Returns:
            bool: True if created successfully
        """
        pass
    
    @abstractmethod
    def delete_collection(self, name: str) -> bool:
        """
        Delete an entire collection.
        
        Args:
            name: Collection name to delete
            
        Returns:
            bool: True if deleted successfully
        """
        pass
    
    @abstractmethod
    def list_collections(self) -> list[str]:
        """
        List all available collections.
        
        Returns:
            list[str]: Collection names
        """
        pass
    
    @abstractmethod
    def get_collection_stats(self, name: str) -> dict[str, Any]:
        """
        Get statistics about a collection.
        
        Args:
            name: Collection name
            
        Returns:
            dict: Stats like document_count, total_chunks, avg_chunk_size, etc.
        """
        pass
    
    
    # ==========================================================================
    # UTILITY & CONFIGURATION
    # ==========================================================================
    
    @abstractmethod
    def clear(self, collection: str | None = None) -> bool:
        """
        Clear all documents from a collection or entire knowledge base.
        
        Args:
            collection: Collection to clear (None = clear all)
            
        Returns:
            bool: True if cleared successfully
        """
        pass
    
    @abstractmethod
    def count_documents(self, collection: str | None = None) -> int:
        """
        Count total documents in collection or entire knowledge base.
        
        Args:
            collection: Collection to count (None = all collections)
            
        Returns:
            int: Number of documents
        """
        pass
    
    @abstractmethod
    def get_embedding_model_info(self) -> dict[str, Any]:
        """
        Get information about the embedding model being used.
        
        Returns:
            dict: Model name, dimensions, provider, etc.
        """
        pass
    
    @abstractmethod
    def reindex(
        self,
        collection: str | None = None,
        batch_size: int = 100
    ) -> bool:
        """
        Reindex documents (useful after changing embedding models).
        
        Args:
            collection: Collection to reindex (None = all)
            batch_size: Batch size for reindexing
            
        Returns:
            bool: True if successful
        """
        pass

class IKnowledgeBaseAsync(ABC):
    """
    Async version of IKnowledgeBase for non-blocking operations.
    
    Use this for agents that need to perform knowledge operations
    without blocking the event loop (e.g., in FastAPI, Discord bots).
    """
    

    # ==========================================================================
    # CORE STORAGE OPERATIONS
    # ==========================================================================

    @abstractmethod
    async def store(
        self,
        content: str,
        metadata: dict[str, Any] | None = None,
        collection: str | None = None,
        chunk_size: int | None = None,
        chunk_overlap: int | None = None
    ) -> str:
        """Async version of store."""
        pass

    @abstractmethod
    async def store_batch(
        self,
        documents: list[dict[str, Any]],
        collection: str | None = None
    ) -> list[str]:
        """Async version of store_batch."""
        pass

    @abstractmethod
    async def update(
        self,
        doc_id: str,
        content: str | None = None,
        metadata: dict[str, Any] | None = None,
        collection: str | None = None
    ) -> bool:
        """Async version of update."""
        pass

    @abstractmethod
    async def delete(
        self,
        doc_id: str,
        collection: str | None = None
    ) -> bool:
        """Async version of delete."""
        pass

    @abstractmethod
    async def get(
        self,
        doc_id: str,
        collection: str | None = None
    ) -> dict[str, Any] | None:
        """Async version of get."""
        pass

    # ==========================================================================
    # RETRIEVAL & SEARCH OPERATIONS
    # ==========================================================================

    @abstractmethod
    async def retrieve(
        self,
        query: str,
        top_k: int = 5,
        collection: str | None = None,
        filter_metadata: dict[str, Any] | None = None,
        min_score: float | None = None
    ) -> list[dict[str, Any]]:
        """Async version of retrieve."""
        pass

    @abstractmethod
    async def search_similar(
        self,
        text: str,
        threshold: float = 0.7,
        collection: str | None = None,
        max_results: int = 10
    ) -> list[dict[str, Any]]:
        """Async version of search_similar."""
        pass

    @abstractmethod
    async def search_by_metadata(
        self,
        filters: dict[str, Any],
        collection: str | None = None,
        limit: int = 100
    ) -> list[dict[str, Any]]:
        """Async version of search_by_metadata."""
        pass

    # ==========================================================================
    # COLLECTION MANAGEMENT
    # ==========================================================================

    @abstractmethod
    async def create_collection(
        self,
        name: str,
        metadata: dict[str, Any] | None = None
    ) -> bool:
        """Async version of create_collection."""
        pass

    @abstractmethod
    async def delete_collection(self, name: str) -> bool:
        """Async version of delete_collection."""
        pass

    @abstractmethod
    async def list_collections(self) -> list[str]:
        """Async version of list_collections."""
        pass

    async def clear(self, collection: str | None = None) -> bool:
        """Async version of clear."""
        pass

    @abstractmethod
    async def count_documents(self, collection: str | None = None) -> int:
        """Async version of count_documents."""
        pass

    @abstractmethod
    async def get_embedding_model_info(self) -> dict[str, Any]:
        """Async version of get_embedding_model_info."""
        pass

    @abstractmethod
    async def reindex(
        self,
        collection: str | None = None,
        batch_size: int = 100
    ) -> bool:
        """Async version of reindex."""
        pass


# ==============================================================================
# EMBEDDING PROVIDER INTERFACE
# ==============================================================================

# ==============================================================================
# RUNNER INTERFACE
# ==============================================================================

from abc import ABC, abstractmethod
from typing import Any

class IRunner(ABC):
    @abstractmethod
    def set_agent_reference(self, agent):
        """Define a referência do agente para o runner"""
        pass

    @abstractmethod
    def start(self) -> None:
        """Inicia a execução do agente (blocking)"""

    @abstractmethod
    def stop(self) -> None:
        """Para a execução de forma segura"""


# ==============================================================================
# EMBEDDING PROVIDER INTERFACE
# ==============================================================================

class IEmbedderProvider(ABC):
    """
    Interface for text embedding providers.

    Provides text-to-vector conversion for semantic search capabilities.
    Implementations can use different embedding models (SentenceTransformers,
    OpenAI, Ollama, etc.) or mock implementations for testing.

    This abstraction allows knowledge bases to use different embedding
    backends without tight coupling to specific providers.
    """

    @abstractmethod
    def embed_text(self, text: str) -> List[float]:
        """
        Generate embedding vector for a single text.

        Args:
            text: Text to embed

        Returns:
            List[float]: Embedding vector
        """
        pass

    @abstractmethod
    def embed_batch(self, texts: List[str]) -> List[List[float]]:
        """
        Generate embeddings for multiple texts efficiently.

        Args:
            texts: List of texts to embed

        Returns:
            List[List[float]]: List of embedding vectors
        """
        pass

    @property
    @abstractmethod
    def dimensions(self) -> int:
        """
        Get the dimensionality of embeddings.

        Returns:
            int: Vector dimension size
        """
        pass

    @property
    @abstractmethod
    def model_name(self) -> str:
        """
        Get the name/identifier of the embedding model.

        Returns:
            str: Model identifier
        """
        pass
