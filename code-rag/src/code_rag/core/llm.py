"""
LLM integration with OpenRouter for response generation.
"""

import json
import time
from typing import Any, Dict, List, Optional, Union

import requests
from tenacity import (
    retry,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential,
)

from code_rag.config import Settings, get_settings
from code_rag.utils.helpers import logger


class LLMIntegration:
    """
    Integrates with OpenRouter for LLM generation capabilities.
    
    Features:
    - Access to various LLMs through OpenRouter
    - Built-in retry mechanism for API calls
    - Customizable prompts and parameters
    - Streaming response support
    """
    
    # OpenRouter API endpoint
    API_URL = "https://openrouter.ai/api/v1/chat/completions"
    
    def __init__(
        self,
        api_key: Optional[str] = None,
        model: Optional[str] = None,
        settings: Optional[Settings] = None,
    ):
        """
        Initialize the LLM integration.
        
        Args:
            api_key: OpenRouter API key (defaults to settings.openrouter_api_key)
            model: Model identifier (defaults to settings.llm_model)
            settings: Settings instance (optional, will use global if None)
        """
        self.settings = settings or get_settings()
        self.api_key = api_key or self.settings.openrouter_api_key
        self.model = model or self.settings.llm_model
        
        # Check API key
        if not self.api_key:
            logger.warning("No OpenRouter API key provided. LLM integration will not work.")
    
    def _build_headers(self) -> Dict[str, str]:
        """
        Build headers for the API request.
        
        Returns:
            Dict[str, str]: Headers for the API request
        """
        return {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_key}",
            "HTTP-Referer": "https://code-rag.example.com",  # Replace with your domain
            "X-Title": "Code RAG",
        }
    
    def _build_messages(
        self,
        query: str,
        context: str,
        system_prompt: Optional[str] = None,
    ) -> List[Dict[str, str]]:
        """
        Build the messages for the API request.
        
        Args:
            query: The user query
            context: The retrieval context
            system_prompt: System prompt (defaults to a predefined prompt)
            
        Returns:
            List[Dict[str, str]]: Messages for the API request
        """
        if system_prompt is None:
            system_prompt = (
                "You are a helpful AI assistant that helps programmers solve coding errors. "
                "Use the provided context of error-solution pairs to craft a detailed and "
                "accurate response to the user's error. Explain why the error occurs and "
                "provide step-by-step solutions. If the context doesn't contain relevant "
                "information, say so and provide general troubleshooting advice."
            )
        
        # Format the user message with the query and context
        user_message = f"Error: {query}\n\nContext:\n{context}\n\nPlease provide a solution to fix this error."
        
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_message},
        ]
        
        return messages
    
    @retry(
        retry=retry_if_exception_type((requests.Timeout, requests.ConnectionError)),
        wait=wait_exponential(multiplier=1, min=1, max=60),
        stop=stop_after_attempt(5),
    )
    def generate_response(
        self,
        query: str,
        context: str,
        system_prompt: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 1024,
        stream: bool = False,
    ) -> Dict[str, Any]:
        """
        Generate a response using the LLM.
        
        Args:
            query: The user query
            context: The retrieval context
            system_prompt: System prompt (defaults to a predefined prompt)
            temperature: Temperature for generation (0.0-1.0)
            max_tokens: Maximum tokens to generate
            stream: Whether to stream the response
            
        Returns:
            Dict[str, Any]: The LLM response
        """
        if not self.api_key:
            error_msg = "OpenRouter API key not provided"
            logger.error(error_msg)
            return {"error": error_msg}
        
        # Build the messages
        messages = self._build_messages(query, context, system_prompt)
        
        # Build the request payload
        payload = {
            "model": self.model,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
            "stream": stream,
        }
        
        # Send the request
        try:
            logger.info(f"Sending request to OpenRouter API with model: {self.model}")
            start_time = time.time()
            
            response = requests.post(
                self.API_URL,
                headers=self._build_headers(),
                json=payload,
                timeout=60,
                stream=stream,
            )
            
            # Handle streaming response
            if stream:
                return {"stream": response}
            
            # Process the response
            if response.status_code == 200:
                response_data = response.json()
                end_time = time.time()
                
                # Extract the generated text
                generated_text = response_data["choices"][0]["message"]["content"]
                
                # Extract usage information
                usage = response_data.get("usage", {})
                prompt_tokens = usage.get("prompt_tokens", 0)
                completion_tokens = usage.get("completion_tokens", 0)
                total_tokens = usage.get("total_tokens", 0)
                
                return {
                    "solution": generated_text,
                    "model": self.model,
                    "processing_time_ms": int((end_time - start_time) * 1000),
                    "usage": {
                        "prompt_tokens": prompt_tokens,
                        "completion_tokens": completion_tokens,
                        "total_tokens": total_tokens,
                    }
                }
            else:
                error_msg = f"OpenRouter API error: {response.status_code}, {response.text}"
                logger.error(error_msg)
                return {"error": error_msg}
        
        except Exception as e:
            error_msg = f"Error calling OpenRouter API: {str(e)}"
            logger.error(error_msg)
            return {"error": error_msg}
    
    def process_streaming_response(self, response: requests.Response) -> str:
        """
        Process a streaming response from the API.
        
        Args:
            response: The streaming response
            
        Returns:
            str: The complete generated text
        """
        if response.status_code != 200:
            error_msg = f"OpenRouter API streaming error: {response.status_code}, {response.text}"
            logger.error(error_msg)
            return f"Error: {error_msg}"
        
        full_text = ""
        
        for line in response.iter_lines():
            if line:
                line = line.decode("utf-8")
                
                # Skip the "data: " prefix and empty lines
                if line.startswith("data: "):
                    line = line[6:]  # Remove "data: " prefix
                
                if line == "[DONE]":
                    break
                
                try:
                    data = json.loads(line)
                    content = data.get("choices", [{}])[0].get("delta", {}).get("content", "")
                    if content:
                        full_text += content
                except json.JSONDecodeError:
                    continue
        
        return full_text