"""
Main RAG (Retrieval-Augmented Generation) component integrating all functionality.
"""

from typing import Dict, List, Optional, Union

from code_rag.config import Settings, get_settings
from code_rag.core.embeddings import EmbeddingGenerator
from code_rag.core.llm import LLMIntegration
from code_rag.core.retriever import Retriever
from code_rag.db.chroma import ChromaVectorStore
from code_rag.utils.helpers import logger


class CodeRAG:
    """
    Main RAG component for retrieving and generating solutions to code errors.
    
    This class integrates all the components of the RAG system:
    - Vector database (Chroma)
    - Embedding generation (OpenAI)
    - Document retrieval
    - LLM integration (OpenRouter)
    """
    
    def __init__(
        self,
        chroma_path: Optional[str] = None,
        embedding_model: Optional[str] = None,
        llm_model: Optional[str] = None,
        openai_api_key: Optional[str] = None,
        openrouter_api_key: Optional[str] = None,
        settings: Optional[Settings] = None,
    ):
        """
        Initialize the RAG component.
        
        Args:
            chroma_path: Path to the Chroma database (defaults to settings.chroma_path)
            embedding_model: Model to use for embeddings (defaults to settings.embedding_model)
            llm_model: Model to use for generation via OpenRouter (defaults to settings.llm_model)
            openai_api_key: OpenAI API key (defaults to settings.openai_api_key)
            openrouter_api_key: OpenRouter API key (defaults to settings.openrouter_api_key)
            settings: Settings instance (optional, will use global if None)
        """
        # Load settings or use provided settings
        self.settings = settings or get_settings()
        
        # Override settings with provided parameters
        if openai_api_key:
            self.settings.openai_api_key = openai_api_key
        if openrouter_api_key:
            self.settings.openrouter_api_key = openrouter_api_key
        if embedding_model:
            self.settings.embedding_model = embedding_model
        if llm_model:
            self.settings.llm_model = llm_model
        if chroma_path:
            self.settings.chroma_path = chroma_path
        
        # Initialize components
        self._initialize_components()
    
    def _initialize_components(self) -> None:
        """Initialize all required components."""
        # Initialize embedding generator
        self.embedding_generator = EmbeddingGenerator(
            api_key=self.settings.openai_api_key,
            model=self.settings.embedding_model,
            settings=self.settings,
        )
        
        # Initialize vector store
        self.vector_store = ChromaVectorStore(
            path=self.settings.chroma_path,
            embedding_generator=self.embedding_generator,
            settings=self.settings,
        )
        
        # Initialize retriever
        self.retriever = Retriever(
            vector_store=self.vector_store,
            embedding_generator=self.embedding_generator,
            settings=self.settings,
        )
        
        # Initialize LLM integration
        self.llm = LLMIntegration(
            api_key=self.settings.openrouter_api_key,
            model=self.settings.llm_model,
            settings=self.settings,
        )
        
        logger.info("All RAG components initialized successfully")
    
    def health_check(self) -> Dict[str, bool]:
        """
        Check if all components are working correctly.
        
        Returns:
            Dict[str, bool]: Status of each component
        """
        status = {}
        
        # Check API keys
        api_keys = self.settings.validate_api_keys()
        status.update(api_keys)
        
        # Check vector store
        try:
            self.vector_store.get_collection_stats()
            status["vector_store"] = True
        except Exception as e:
            logger.error(f"Vector store check failed: {str(e)}")
            status["vector_store"] = False
        
        # Overall status
        status["healthy"] = all(status.values())
        
        return status
    
    def query(
        self,
        error_message: str,
        num_results: Optional[int] = None,
        temperature: float = 0.7,
        max_tokens: int = 1024,
        system_prompt: Optional[str] = None,
        stream: bool = False,
    ) -> Dict:
        """
        Query the RAG system with an error message.
        
        This method:
        1. Retrieves relevant documents from the vector store
        2. Formats them into context
        3. Sends the context and query to the LLM
        4. Returns the generated solution
        
        Args:
            error_message: The error message to find solutions for
            num_results: Number of relevant results to retrieve (defaults to settings.default_num_results)
            temperature: Temperature for LLM generation (0.0-1.0)
            max_tokens: Maximum tokens for LLM response
            system_prompt: Optional system prompt for the LLM
            stream: Whether to stream the LLM response
            
        Returns:
            Dict: Response containing solution and metadata
        """
        # Log the query
        logger.info(f"Processing query: {error_message[:100]}{'...' if len(error_message) > 100 else ''}")
        
        # Step 1: Retrieve relevant documents
        retrieval_result = self.retriever.retrieve_and_format(
            query=error_message,
            n_results=num_results,
        )
        
        context = retrieval_result["context"]
        retrieved_docs = retrieval_result["retrieved_docs"]
        
        # Step 2: Generate solution using LLM
        llm_response = self.llm.generate_response(
            query=error_message,
            context=context,
            system_prompt=system_prompt,
            temperature=temperature,
            max_tokens=max_tokens,
            stream=stream,
        )
        
        # Handle streaming response
        if stream and "stream" in llm_response:
            generated_text = self.llm.process_streaming_response(llm_response["stream"])
            response = {
                "solution": generated_text,
                "references": retrieved_docs,
                "metadata": {
                    "model_used": self.settings.llm_model,
                    "num_references": len(retrieved_docs),
                }
            }
            return response
        
        # Handle error in LLM call
        if "error" in llm_response:
            logger.error(f"Error generating response: {llm_response['error']}")
            return {
                "solution": "Error generating solution. Please try again.",
                "error": llm_response["error"],
                "references": retrieved_docs,
                "metadata": {
                    "model_used": self.settings.llm_model,
                    "num_references": len(retrieved_docs),
                }
            }
        
        # Format the response
        response = {
            "solution": llm_response.get("solution", "No solution generated."),
            "references": retrieved_docs,
            "metadata": {
                "model_used": llm_response.get("model", self.settings.llm_model),
                "tokens_used": llm_response.get("usage", {}).get("total_tokens", 0),
                "processing_time_ms": llm_response.get("processing_time_ms", 0),
                "num_references": len(retrieved_docs),
            }
        }
        
        return response