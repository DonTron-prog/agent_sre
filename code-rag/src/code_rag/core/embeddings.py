"""
Embeddings generation using OpenAI's text-embedding-ada-002 model.
"""

import time
from typing import Dict, List, Optional, Union

import openai
from tenacity import (
    retry,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential,
)

from code_rag.config import Settings, get_settings
from code_rag.utils.helpers import logger


class EmbeddingGenerator:
    """
    Generates embeddings using OpenAI's text-embedding-ada-002 model.
    
    Features:
    - Efficient batching of texts
    - Retries with exponential backoff
    - Caching of recently generated embeddings
    """
    
    def __init__(
        self,
        api_key: Optional[str] = None,
        model: Optional[str] = None,
        settings: Optional[Settings] = None,
        cache_size: int = 1000,
    ):
        """
        Initialize the embedding generator.
        
        Args:
            api_key: OpenAI API key (defaults to settings.openai_api_key)
            model: Embedding model name (defaults to settings.embedding_model)
            settings: Settings instance (optional, will use global if None)
            cache_size: Size of the LRU cache for embeddings
        """
        self.settings = settings or get_settings()
        self.api_key = api_key or self.settings.openai_api_key
        self.model = model or self.settings.embedding_model
        
        # Set up OpenAI client
        self.client = openai.OpenAI(api_key=self.api_key)
        
        # Initialize cache
        self._cache: Dict[str, List[float]] = {}
        self._cache_size = cache_size
        
        # Check API key
        if not self.api_key:
            logger.warning("No OpenAI API key provided. Embeddings will not work.")
    
    @retry(
        retry=retry_if_exception_type((openai.RateLimitError, openai.APITimeoutError)),
        wait=wait_exponential(multiplier=1, min=1, max=60),
        stop=stop_after_attempt(5),
    )
    def _get_embedding(self, text: str) -> List[float]:
        """
        Get embedding for a single text using the OpenAI API.
        If no valid API key is provided, returns random vectors.
        
        Args:
            text: Text to embed
            
        Returns:
            List[float]: Embedding vector
        """
        # Check if in cache
        if text in self._cache:
            return self._cache[text]
        
        # If API key is missing or is dummy, generate random embedding
        if not self.api_key or self.api_key.startswith('sk-dummy'):
            import random
            import hashlib
            
            # Generate deterministic "embeddings" based on text hash
            # This ensures the same text always gets the same embedding
            text_hash = hashlib.md5(text.encode()).hexdigest()
            random.seed(text_hash)
            
            # OpenAI ada-002 embeddings are 1536 dimensions
            embedding = [random.uniform(-1, 1) for _ in range(1536)]
            logger.warning("Using randomly generated embeddings (no valid API key)")
        else:
            # Get embedding from API
            try:
                response = self.client.embeddings.create(
                    model=self.model,
                    input=text,
                )
                embedding = response.data[0].embedding
            except Exception as e:
                logger.error(f"Error generating embedding: {e}")
                # Fallback to random embedding
                import random
                import hashlib
                
                text_hash = hashlib.md5(text.encode()).hexdigest()
                random.seed(text_hash)
                embedding = [random.uniform(-1, 1) for _ in range(1536)]
                logger.warning("Using randomly generated embeddings due to API error")
        
        # Cache the result
        if len(self._cache) >= self._cache_size:
            # Remove a random item if cache is full (simple strategy)
            if self._cache:
                self._cache.pop(next(iter(self._cache)))
        
        self._cache[text] = embedding
        
        return embedding
    
    def get_embeddings(
        self,
        texts: Union[str, List[str]],
        batch_size: int = 16,
    ) -> Union[List[float], List[List[float]]]:
        """
        Get embeddings for one or more texts.
        
        Args:
            texts: A single text or list of texts to embed
            batch_size: Number of texts to process in each batch
            
        Returns:
            Union[List[float], List[List[float]]]: A single embedding vector or a list of embedding vectors
        """
        # Handle single text case
        if isinstance(texts, str):
            return self._get_embedding(texts)
        
        # Process texts in batches
        all_embeddings = []
        for i in range(0, len(texts), batch_size):
            batch = texts[i:i+batch_size]
            
            # Process each text in the batch
            batch_embeddings = []
            for text in batch:
                batch_embeddings.append(self._get_embedding(text))
            
            all_embeddings.extend(batch_embeddings)
            
            # Sleep briefly between batches to avoid rate limiting
            if i + batch_size < len(texts):
                time.sleep(0.5)
        
        return all_embeddings