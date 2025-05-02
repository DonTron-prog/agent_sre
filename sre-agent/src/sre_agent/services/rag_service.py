"""
RAG service adapter for integration with the existing CodeRAG system.
"""

from typing import Dict, List, Any, Optional

# Import from code-rag package
from code_rag import CodeRAG
from code_rag.config import get_settings as get_coderag_settings

from sre_agent.config.settings import get_settings


class RAGService:
    """
    Service to integrate with the existing CodeRAG system.
    
    This adapter bridges between the LangGraph workflow and the CodeRAG system,
    allowing the SRE agent to query the vector store for similar incidents.
    """
    
    def __init__(self, settings=None):
        """
        Initialize with optional custom settings.
        
        Args:
            settings: Optional custom settings
        """
        self.settings = settings or get_settings()
        coderag_settings = get_coderag_settings()
        
        # Initialize with SRE incidents collection
        self.rag = CodeRAG(
            chroma_path=str(coderag_settings.chroma_path),
            embedding_model=coderag_settings.embedding_model,
            llm_model=coderag_settings.llm_model,
            openai_api_key=coderag_settings.openai_api_key,
            openrouter_api_key=coderag_settings.openrouter_api_key,
            settings=coderag_settings,
        )
        
        # Set to use SRE incidents collection
        self.rag.vector_store.collection_name = "sre_incidents"
    
    def find_similar_alerts(self, alert: Dict[str, Any], num_results: int = None) -> List[Dict[str, Any]]:
        """
        Find similar past incidents for a given alert.
        
        Args:
            alert: The alert to find similar incidents for
            num_results: Number of results to return (uses default if None)
            
        Returns:
            List of similar incidents with their solutions and metadata
        """
        # Use default number of results if not specified
        if num_results is None:
            num_results = self.settings.default_num_results
        
        # Combine alert details to form a query
        query = f"{alert['type']}: {alert['summary']} - {alert['details']}"
        
        # Query the RAG system
        result = self.rag.query(
            error_message=query,
            num_results=num_results,
            temperature=self.settings.default_temperature,
        )
        
        return result.get("references", [])
    
    def get_collection_stats(self) -> Dict[str, Any]:
        """
        Get statistics about the SRE incidents collection.
        
        Returns:
            Dictionary with collection statistics
        """
        return self.rag.vector_store.get_collection_stats()