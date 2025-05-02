"""
Configuration settings for the SRE agent.
"""

import os
from pathlib import Path
from typing import Optional
from pydantic import BaseModel, Field
from dotenv import load_dotenv


# Load environment variables from .env file
load_dotenv()


class Settings(BaseModel):
    """
    Configuration settings for the SRE agent.
    
    Attributes:
        openai_api_key: API key for OpenAI (for embeddings)
        openrouter_api_key: API key for OpenRouter (for LLMs)
        chroma_path: Path to the Chroma database
        embedding_model: Model to use for embeddings
        llm_model: Model to use for language generation
        default_num_results: Default number of similar incidents to retrieve
        default_temperature: Default temperature for generation
    """
    # API Keys
    openai_api_key: str = Field(default_factory=lambda: os.environ.get("OPENAI_API_KEY", ""))
    openrouter_api_key: str = Field(default_factory=lambda: os.environ.get("OPENROUTER_API_KEY", ""))
    
    # Paths
    chroma_path: Path = Field(default_factory=lambda: Path(os.environ.get("CHROMA_PATH", "./chroma_db")))
    
    # Model settings
    embedding_model: str = Field(default="text-embedding-ada-002")
    llm_model: str = Field(default="mistralai/mistral-7b-instruct:latest")
    
    # Retrieval settings
    default_num_results: int = Field(default=3)
    default_temperature: float = Field(default=0.2)
    
    def validate_api_keys(self) -> dict:
        """
        Check if API keys are present.
        
        Returns:
            dict: Status of each API key
        """
        return {
            "openai_api_key": bool(self.openai_api_key),
            "openrouter_api_key": bool(self.openrouter_api_key),
        }


# Singleton instance of settings
_settings: Optional[Settings] = None


def get_settings() -> Settings:
    """
    Get the settings instance. Creates one if it doesn't exist.
    
    Returns:
        Settings: The settings instance
    """
    global _settings
    if _settings is None:
        _settings = Settings()
    return _settings