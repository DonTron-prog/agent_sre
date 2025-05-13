"""
RAG service adapter for integration with the existing CodeRAG system.
"""

import os
from pathlib import Path
from typing import Dict, List, Any, Optional, Union
from sre_agent.models.state import AgentState
from dotenv import load_dotenv

# Import chromadb for direct collection management
import chromadb
from chromadb.utils import embedding_functions

# Import from code-rag package
from code_rag import CodeRAG
from code_rag.config import get_settings as get_coderag_settings
from code_rag.db.chroma import ChromaVectorStore
from code_rag.core.embeddings import EmbeddingGenerator
from code_rag.utils.helpers import logger

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
        
        # Load API keys from .env file
        env_path = Path("/home/donald/Projects/agent_sre/.env")
        if env_path.exists():
            load_dotenv(dotenv_path=env_path)
            logger.info("Loaded API keys from .env file")
            
            # Set the API keys in the settings
            if os.environ.get('OPENAI_API_KEY'):
                coderag_settings.openai_api_key = os.environ.get('OPENAI_API_KEY')
                os.environ['CHROMA_OPENAI_API_KEY'] = os.environ.get('OPENAI_API_KEY')  # ChromaDB looks for this env var
                logger.info("Using OpenAI API key from .env file")
                
            if os.environ.get('OPENROUTER_API_KEY'):
                coderag_settings.openrouter_api_key = os.environ.get('OPENROUTER_API_KEY')
                logger.info("Using OpenRouter API key from .env file")
        else:
            # Set a dummy API key for testing if not provided
            if not coderag_settings.openai_api_key:
                os.environ['OPENAI_API_KEY'] = 'sk-dummy-api-key-for-testing'
                os.environ['CHROMA_OPENAI_API_KEY'] = 'sk-dummy-api-key-for-testing'  # ChromaDB looks for this env var
                logger.warning("Using dummy OpenAI API key for testing")
            
        # Print the paths to help debug
        logger.info(f"SRE Agent Chroma path: {self.settings.chroma_path}")
        logger.info(f"CodeRAG Chroma path: {coderag_settings.chroma_path}")
        
        # Use the same path for both
        coderag_settings.chroma_path = Path("/home/donald/Projects/agent_sre/chroma_db")
        logger.info(f"Using Chroma path: {coderag_settings.chroma_path}")
        
        # Create a custom embedding generator
        embedding_generator = EmbeddingGenerator(
            api_key=os.environ.get('OPENAI_API_KEY', coderag_settings.openai_api_key),
            model=coderag_settings.embedding_model,
            settings=coderag_settings,
        )
        
        try:
            # Try to create a vector store with the correct collection name
            vector_store = ChromaVectorStore(
                path=coderag_settings.chroma_path,
                collection_name="sre_incidents",  # Set the correct collection name during initialization
                embedding_generator=embedding_generator,
                settings=coderag_settings,
            )
            logger.info("Successfully connected to 'sre_incidents' collection")
        except Exception as e:
            logger.warning(f"Error connecting to collection: {str(e)}")
            logger.warning("Using default 'code_errors' collection instead")
            
            # Use the default collection name
            vector_store = ChromaVectorStore(
                path=coderag_settings.chroma_path,
                collection_name="code_errors",  # Default collection name
                embedding_generator=embedding_generator,
                settings=coderag_settings,
            )
        
        # Initialize with custom vector store that has the correct collection
        self.rag = CodeRAG(
            chroma_path=str(coderag_settings.chroma_path),
            embedding_model=coderag_settings.embedding_model,
            llm_model=coderag_settings.llm_model,
            openai_api_key=os.environ.get('OPENAI_API_KEY', coderag_settings.openai_api_key),
            openrouter_api_key=coderag_settings.openrouter_api_key,
            settings=coderag_settings,
        )
        
        # Replace the default vector store with our custom one
        self.rag.vector_store = vector_store
        
        # Log the collection being used
        logger.info(f"Using collection: {self.rag.vector_store.collection_name}")
    
    def find_similar_alerts(self, alert: Dict[str, Any], state: Optional[Union[Dict[str, Any], AgentState]] = None, num_results: int = None) -> List[Dict[str, Any]]:
        """
        Find similar past incidents for a given alert.
        
        Args:
            alert: The alert to find similar incidents for
            state: Optional workflow state that may contain pre-retrieved similar incidents
            num_results: Number of results to return (uses default if None)
            
        Returns:
            List of similar incidents with their solutions and metadata
        """
        # Check if similar incidents are already in the state
        if state and state.get("similar_incidents"):
            logger.info(f"Using {len(state['similar_incidents'])} similar incidents from state")
            return state["similar_incidents"]
        # Use default number of results if not specified
        if num_results is None:
            num_results = self.settings.default_num_results
        
        # Combine alert details to form a query
        query = f"{alert['type']}: {alert['summary']} - {alert['details']}"

        
        # First check if we can get direct results from the vector store
        logger.info(f"Querying vector store with: {query}")
        direct_results = self.rag.vector_store.query(
            query_text=query,
            n_results=num_results
        )
        
        # Log the direct results
        logger.info(f"Direct query results: {direct_results}")
        
        # If we have direct results, format them
        if direct_results and 'ids' in direct_results and direct_results['ids'] and direct_results['ids'][0]:
            logger.info(f"Found {len(direct_results['ids'][0])} direct results from vector store")
            formatted_results = []
            
            for i, doc_id in enumerate(direct_results['ids'][0]):
                document = direct_results['documents'][0][i] if i < len(direct_results['documents'][0]) else ""
                metadata = direct_results['metadatas'][0][i] if i < len(direct_results['metadatas'][0]) else {}
                distance = direct_results['distances'][0][i] if i < len(direct_results['distances'][0]) else 1.0
                
                # Convert distance to similarity score (smaller distances mean higher similarity)
                similarity_score = round(1.0 - distance, 2)  # Convert to similarity and round
                
                formatted_results.append({
                    "id": doc_id,
                    "error": document,
                    "solution": metadata.get("solution", ""),
                    "similarity_score": similarity_score,  # Add similarity score
                    "metadata": {k: v for k, v in metadata.items() if k != "solution"},
                })
            
            # Return the formatted results directly without a secondary query
            logger.info(f"Returning {len(formatted_results)} formatted results directly")
            return formatted_results
        
        # If no direct results, return an empty list
        logger.warning(f"No direct results found, returning empty list")
        return []
    
    def get_collection_stats(self) -> Dict[str, Any]:
        """
        Get statistics about the SRE incidents collection.
        
        Returns:
            Dictionary with collection statistics
        """
        return self.rag.vector_store.get_collection_stats()