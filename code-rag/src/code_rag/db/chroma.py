"""
Chroma vector database integration for storing and retrieving embeddings.
"""

from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Union

import chromadb
from chromadb.utils import embedding_functions

from code_rag.config import Settings, get_settings
from code_rag.core.embeddings import EmbeddingGenerator
from code_rag.utils.helpers import logger


class ChromaVectorStore:
    """
    Interface to Chroma for storing and retrieving vector embeddings.
    
    Features:
    - High-performance similarity search
    - Document metadata storage
    - Flexible filtering capabilities
    """
    
    def __init__(
        self,
        path: Optional[Union[str, Path]] = None,
        collection_name: str = "code_errors",
        embedding_generator: Optional[EmbeddingGenerator] = None,
        settings: Optional[Settings] = None,
    ):
        """
        Initialize the Chroma vector store.
        
        Args:
            path: Path to the Chroma database (defaults to settings.chroma_path)
            collection_name: Name of the collection to use
            embedding_generator: Instance of EmbeddingGenerator (created if None)
            settings: Settings instance (optional, will use global if None)
        """
        self.settings = settings or get_settings()
        self.path = Path(path) if path else self.settings.chroma_path
        self.collection_name = collection_name
        
        # Create embedding generator if not provided
        self.embedding_generator = embedding_generator or EmbeddingGenerator(
            api_key=self.settings.openai_api_key,
            model=self.settings.embedding_model,
            settings=self.settings,
        )
        
        # Initialize Chroma client
        self.client = chromadb.PersistentClient(path=str(self.path))
        
        # Create or get collection
        # The OpenAI embedding function just for schema compatibility - we'll provide our own embeddings
        embedding_function = embedding_functions.OpenAIEmbeddingFunction(
            api_key=self.settings.openai_api_key,
            model_name=self.settings.embedding_model
        )
        
        # Get or create the collection
        self.collection = self.client.get_or_create_collection(
            name=collection_name,
            embedding_function=embedding_function
        )
        logger.info(f"Using collection: {collection_name}")
    
    def add_documents(
        self,
        documents: List[str],
        metadatas: Optional[List[Dict[str, Any]]] = None,
        ids: Optional[List[str]] = None,
        embeddings: Optional[List[List[float]]] = None,
        batch_size: int = 16,
    ) -> None:
        """
        Add documents to the vector store.
        
        Args:
            documents: List of document texts
            metadatas: Optional list of metadata dictionaries for each document
            ids: Optional list of IDs for each document (generated if None)
            embeddings: Optional pre-computed embeddings (generated if None)
            batch_size: Number of documents to process in each batch
        """
        # Generate IDs if not provided
        if ids is None:
            ids = [str(i) for i in range(len(documents))]
            logger.warning("No IDs provided, generating sequential IDs.")
        
        # Generate embeddings if not provided
        if embeddings is None:
            logger.info(f"Generating embeddings for {len(documents)} documents...")
            embeddings = self.embedding_generator.get_embeddings(documents, batch_size=batch_size)
        
        # Create empty metadata if not provided
        if metadatas is None:
            metadatas = [{} for _ in range(len(documents))]
        
        # Add documents in batches
        for i in range(0, len(documents), batch_size):
            end_idx = min(i + batch_size, len(documents))
            batch_documents = documents[i:end_idx]
            batch_metadatas = metadatas[i:end_idx]
            batch_ids = ids[i:end_idx]
            batch_embeddings = embeddings[i:end_idx]
            
            self.collection.add(
                documents=batch_documents,
                metadatas=batch_metadatas,
                ids=batch_ids,
                embeddings=batch_embeddings
            )
            
            logger.debug(f"Added batch {i//batch_size + 1}: {end_idx - i} documents")
        
        logger.info(f"Successfully added {len(documents)} documents to collection {self.collection_name}")
    
    def query(
        self,
        query_text: str,
        n_results: int = 3,
        filter_dict: Optional[Dict[str, Any]] = None,
        include_embeddings: bool = False,
    ) -> Dict[str, Any]:
        """
        Query the vector store for similar documents.
        
        Args:
            query_text: The query text
            n_results: Number of results to return
            filter_dict: Optional filter dictionary
            include_embeddings: Whether to include embeddings in the response
            
        Returns:
            Dict[str, Any]: Query results containing documents, IDs, distances, and metadatas
        """
        # Generate embedding for the query
        query_embedding = self.embedding_generator.get_embeddings(query_text)
        
        # Perform the query
        include_list = ["documents", "distances", "metadatas"]
        if include_embeddings:
            include_list.append("embeddings")
        
        results = self.collection.query(
            query_embeddings=[query_embedding],
            n_results=n_results,
            where=filter_dict,
            include=include_list
        )
        
        return results
    
    def get_document_by_id(self, document_id: str) -> Optional[Dict[str, Any]]:
        """
        Get a specific document by ID.
        
        Args:
            document_id: The ID of the document to retrieve
            
        Returns:
            Optional[Dict[str, Any]]: Document data if found, None otherwise
        """
        try:
            result = self.collection.get(ids=[document_id])
            if result["ids"] and len(result["ids"]) > 0:
                return {
                    "id": result["ids"][0],
                    "document": result["documents"][0],
                    "metadata": result["metadatas"][0] if "metadatas" in result else {},
                }
            return None
        except Exception as e:
            logger.error(f"Error retrieving document {document_id}: {e}")
            return None
    
    def get_collection_stats(self) -> Dict[str, Any]:
        """
        Get statistics about the collection.
        
        Returns:
            Dict[str, Any]: Statistics about the collection
        """
        count = self.collection.count()
        return {
            "collection_name": self.collection_name,
            "document_count": count,
            "path": str(self.path),
        }