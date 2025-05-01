"""
Configuration settings for the RAG component.
Uses environment variables with dotenv for configuration.
"""

import os
from pathlib import Path
from typing import Optional

from dotenv import load_dotenv
from pydantic import BaseModel, Field, computed_field, ConfigDict


# Load environment variables from .env file if it exists
load_dotenv()


class Settings(BaseModel):
    """
    Configuration settings for the RAG component.
    Loads from environment variables with sensible defaults.
    """

    model_config = ConfigDict(env_prefix="CODE_RAG_")

    # API Keys
    openai_api_key: str = Field(
        default_factory=lambda: os.environ.get("OPENAI_API_KEY", "")
    )
    openrouter_api_key: str = Field(
        default_factory=lambda: os.environ.get("OPENROUTER_API_KEY", "")
    )

    # Model Configuration
    embedding_model: str = Field(
        default="text-embedding-ada-002",
        description="OpenAI embedding model to use",
    )
    llm_model: str = Field(
        default="openai/gpt-3.5-turbo",
        description="OpenRouter model identifier",
    )
    
    # Data Paths
    base_data_dir: Path = Field(
        default_factory=lambda: Path(os.environ.get("CODE_RAG_DATA_DIR", "./data"))
    )
    chroma_path: Path = Field(
        default_factory=lambda: Path(os.environ.get("CODE_RAG_CHROMA_PATH", "./chroma_db"))
    )

    # Retrieval Configuration
    default_num_results: int = Field(
        default=3,
        description="Default number of results to return from vector search",
    )
    
    # API Configuration
    api_host: str = Field(
        default="0.0.0.0",
        description="Host for the FastAPI server",
    )
    api_port: int = Field(
        default=8000,
        description="Port for the FastAPI server",
    )
    
    @computed_field
    def raw_data_dir(self) -> Path:
        """Path to raw data directory."""
        return self.base_data_dir / "raw"

    @computed_field
    def processed_data_dir(self) -> Path:
        """Path to processed data directory."""
        return self.base_data_dir / "processed"

    def validate_api_keys(self) -> dict:
        """
        Validate that required API keys are present.
        
        Returns:
            dict: Status of each required API key
        """
        return {
            "openai_api_key": bool(self.openai_api_key),
            "openrouter_api_key": bool(self.openrouter_api_key),
        }


# Create a global settings instance
settings = Settings()


def get_settings() -> Settings:
    """
    Get the settings instance.
    
    Returns:
        Settings: The global settings instance
    """
    return settings