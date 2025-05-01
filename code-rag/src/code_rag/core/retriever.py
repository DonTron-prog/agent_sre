"""
Document retrieval functionality from the vector store.
"""

from typing import Dict, List, Optional, Union

from code_rag.config import Settings, get_settings
from code_rag.core.embeddings import EmbeddingGenerator
from code_rag.db.chroma import ChromaVectorStore
from code_rag.utils.helpers import logger


class Retriever:
    """
    Retrieves relevant documents from the vector store.
    
    Features:
    - Semantic similarity search using embeddings
    - Metadata filtering options
    - Configurable number of results
    - Result reranking capabilities
    """
    
    def __init__(
        self,
        vector_store: Optional[ChromaVectorStore] = None,
        embedding_generator: Optional[EmbeddingGenerator] = None,
        settings: Optional[Settings] = None,
    ):
        """
        Initialize the retriever.
        
        Args:
            vector_store: ChromaVectorStore instance (created if None)
            embedding_generator: EmbeddingGenerator instance (created if None)
            settings: Settings instance (optional, will use global if None)
        """
        self.settings = settings or get_settings()
        
        # Create embedding generator if not provided
        self.embedding_generator = embedding_generator or EmbeddingGenerator(
            api_key=self.settings.openai_api_key,
            model=self.settings.embedding_model,
            settings=self.settings,
        )
        
        # Create vector store if not provided
        self.vector_store = vector_store or ChromaVectorStore(
            path=self.settings.chroma_path,
            embedding_generator=self.embedding_generator,
            settings=self.settings,
        )
    
    def retrieve(
        self,
        query: str,
        n_results: Optional[int] = None,
        filter_dict: Optional[Dict] = None,
    ) -> List[Dict]:
        """
        Retrieve relevant documents for a query.
        
        Args:
            query: The query string
            n_results: Number of results to return (defaults to settings.default_num_results)
            filter_dict: Optional filter dictionary for metadata filtering
            
        Returns:
            List[Dict]: List of retrieved documents with metadata
        """
        if n_results is None:
            n_results = self.settings.default_num_results
        
        # Query the vector store
        results = self.vector_store.query(
            query_text=query,
            n_results=n_results,
            filter_dict=filter_dict,
        )
        
        # Format the results
        formatted_results = []
        
        # Check if we have any results
        if not results or 'ids' not in results or not results['ids'] or not results['ids'][0]:
            logger.warning(f"No results found for query: {query}")
            return formatted_results
        
        # Process each result
        for i, doc_id in enumerate(results['ids'][0]):
            document = results['documents'][0][i] if 'documents' in results and results['documents'] and i < len(results['documents'][0]) else ""
            metadata = results['metadatas'][0][i] if 'metadatas' in results and results['metadatas'] and i < len(results['metadatas'][0]) else {}
            distance = results['distances'][0][i] if 'distances' in results and results['distances'] and i < len(results['distances'][0]) else 0.0
            
            # Similarity score is 1 - distance for cosine distance
            similarity_score = 1.0 - distance
            
            formatted_results.append({
                "id": doc_id,
                "error": document,
                "solution": metadata.get("solution", ""),
                "similarity_score": similarity_score,
                "metadata": {k: v for k, v in metadata.items() if k != "solution"},
            })
        
        return formatted_results
    
    def format_for_context(self, retrieved_docs: List[Dict]) -> str:
        """
        Format retrieved documents into a context string for the LLM.
        
        Args:
            retrieved_docs: List of retrieved documents
            
        Returns:
            str: Formatted context string
        """
        if not retrieved_docs:
            return "No relevant code error solutions found."
        
        context = "Here are some similar code errors and their solutions:\n\n"
        
        for i, doc in enumerate(retrieved_docs):
            context += f"Example {i+1}:\n"
            context += f"Error: {doc['error']}\n"
            context += f"Solution: {doc['solution']}\n"
            
            # Add a separator between examples
            if i < len(retrieved_docs) - 1:
                context += "\n---\n\n"
        
        return context
    
    def retrieve_and_format(
        self,
        query: str,
        n_results: Optional[int] = None,
        filter_dict: Optional[Dict] = None,
    ) -> Dict:
        """
        Retrieve documents and format them for context.
        
        Args:
            query: The query string
            n_results: Number of results to return (defaults to settings.default_num_results)
            filter_dict: Optional filter dictionary for metadata filtering
            
        Returns:
            Dict: Dictionary containing formatted context and raw retrieval results
        """
        # Retrieve relevant documents
        retrieved_docs = self.retrieve(query, n_results, filter_dict)
        
        # Format for context
        context = self.format_for_context(retrieved_docs)
        
        return {
            "context": context,
            "retrieved_docs": retrieved_docs,
            "query": query,
        }