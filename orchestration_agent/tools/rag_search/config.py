from typing import Optional
from pydantic import Field
from atomic_agents.lib.base.base_tool import BaseToolConfig

# --- Configuration ---
class RAGSearchToolConfig(BaseToolConfig):
    """Configuration for the RAG Search Tool."""
    docs_dir: str = Field("./knowledge_base_sre", description="Directory containing documents to index")
    chunk_size: int = Field(1000, description="Size of each text chunk.")
    chunk_overlap: int = Field(200, description="Overlap between text chunks.")
    num_chunks_to_retrieve: int = Field(5, description="Number of chunks to retrieve for RAG.")
    persist_dir: str = Field("./sre_chroma_db", description="Directory to persist ChromaDB data.")
    collection_name: str = Field("rag_documents", description="ChromaDB collection name.")
    embedding_model_name: str = Field("text-embedding-3-small", description="OpenAI embedding model name.")
    llm_model_name: str = Field("gpt-4o-mini", description="LLM model name for agents.")
    recreate_collection_on_init: bool = Field(True, description="Recreate ChromaDB collection on tool initialization.")
    force_reload_documents: bool = Field(True, description="Force reloading and reindexing of documents even if collection already has content.")
    openai_api_key: Optional[str] = Field(None, description="OpenAI API key. If None, attempts to use OPENAI_API_KEY env var.")