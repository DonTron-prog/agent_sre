"""Configuration management utilities for the orchestration agent."""

import os
from typing import Dict, Any

from orchestration_engine.tools.searxng_search import (
    SearxNGSearchTool,
    SearxNGSearchToolConfig,
)
from orchestration_engine.tools.calculator import (
    CalculatorTool,
    CalculatorToolConfig,
)
from orchestration_engine.tools.rag_search import (
    RAGSearchTool,
    RAGSearchToolConfig,
)
from orchestration_engine.tools.deep_research import (
    DeepResearchTool,
    DeepResearchToolConfig,
)


class ConfigManager:
    """Manages configuration loading and tool initialization."""
    
    @staticmethod
    def load_configuration() -> Dict[str, Any]:
        """Load configuration settings from environment variables or config files.
        
        Returns:
            Dictionary containing all configuration settings
        """
        config = {
            "openai_api_key": os.getenv("OPENAI_API_KEY"),
            "openrouter_api_key": os.getenv("OPENROUTER_API_KEY"),
            "model_name": os.getenv("MODEL_NAME", "gpt-4o-mini"),
            "searxng_base_url": os.getenv("SEARXNG_BASE_URL", "http://localhost:8080"),
            "knowledge_base_dir": os.path.join(os.path.dirname(__file__), "..", "..", "knowledge_base_sre"),
            "persist_dir": os.path.join(os.path.dirname(__file__), "..", "..", "sre_chroma_db"),
            "recreate_rag_collection": os.getenv("RECREATE_RAG_COLLECTION", "False").lower() == "true",
            "force_reload_rag_docs": os.getenv("FORCE_RELOAD_RAG_DOCS", "False").lower() == "true",
            "max_search_results": int(os.getenv("MAX_SEARCH_RESULTS", 3))
        }
        return config
    
    @staticmethod
    def initialize_tools(config: Dict[str, Any]) -> Dict[str, Any]:
        """Initialize all required tools with their configurations.
        
        Args:
            config: Configuration dictionary from load_configuration()
            
        Returns:
            Dictionary containing initialized tool instances
        """
        searxng_tool = SearxNGSearchTool(
            SearxNGSearchToolConfig(
                base_url=config["searxng_base_url"],
                max_results=config["max_search_results"]
            )
        )
        
        calculator_tool = CalculatorTool(CalculatorToolConfig())
        
        rag_tool_config = RAGSearchToolConfig(
            docs_dir=config["knowledge_base_dir"],
            persist_dir=config["persist_dir"],
            recreate_collection_on_init=config["recreate_rag_collection"],
            force_reload_documents=config["force_reload_rag_docs"]
        )
        rag_tool = RAGSearchTool(config=rag_tool_config)
        
        deep_research_tool = DeepResearchTool(
            DeepResearchToolConfig(
                searxng_base_url=config["searxng_base_url"],
                max_search_results=config["max_search_results"]
            )
        )
        
        return {
            "searxng": searxng_tool,
            "calculator": calculator_tool,
            "rag": rag_tool,
            "deep_research": deep_research_tool
        }
    
    @staticmethod
    def get_default_config() -> Dict[str, Any]:
        """Get default configuration values.
        
        Returns:
            Dictionary with default configuration values
        """
        return {
            "model_name": "gpt-4o-mini",
            "searxng_base_url": "http://localhost:8080",
            "recreate_rag_collection": False,
            "force_reload_rag_docs": False,
            "max_search_results": 3
        }