"""Tool management utilities for the orchestration agent."""

from typing import Union, Dict, Any
from orchestration_engine.tools.searxng_search import (
    SearxNGSearchTool,
    SearxNGSearchToolInputSchema,
    SearxNGSearchToolOutputSchema,
)
from orchestration_engine.tools.calculator import (
    CalculatorTool,
    CalculatorToolInputSchema,
    CalculatorToolOutputSchema,
)
from orchestration_engine.tools.rag_search import (
    RAGSearchTool,
    RAGSearchToolInputSchema,
    RAGSearchToolOutputSchema
)
from orchestration_engine.tools.deep_research import (
    DeepResearchTool,
    DeepResearchToolInputSchema,
    DeepResearchToolOutputSchema,
)
from orchestration_engine.schemas.orchestrator_schemas import OrchestratorOutputSchema


class ToolManager:
    """Manages tool execution and provides tool-related utilities."""
    
    def __init__(self, tools_dict: Dict[str, Any]):
        """Initialize with a dictionary of tool instances.
        
        Args:
            tools_dict: Dictionary with keys like 'searxng', 'calculator', 'rag', 'deep_research'
        """
        self.tools = tools_dict
    
    def execute_tool(self, orchestrator_output: OrchestratorOutputSchema) -> Union[
        SearxNGSearchToolOutputSchema, 
        CalculatorToolOutputSchema, 
        RAGSearchToolOutputSchema, 
        DeepResearchToolOutputSchema
    ]:
        """Execute the appropriate tool based on the orchestrator's decision.
        
        Args:
            orchestrator_output: The output from the orchestrator agent
            
        Returns:
            The output from the executed tool
            
        Raises:
            ValueError: If tool name is unknown or parameters are invalid
        """
        if orchestrator_output.tool in ("search", "web-search"):
            if not isinstance(orchestrator_output.tool_parameters, SearxNGSearchToolInputSchema):
                raise ValueError(f"Invalid parameters for search tool: {orchestrator_output.tool_parameters}")
            return self.tools["searxng"].run(orchestrator_output.tool_parameters)
        elif orchestrator_output.tool == "calculator":
            if not isinstance(orchestrator_output.tool_parameters, CalculatorToolInputSchema):
                raise ValueError(f"Invalid parameters for calculator tool: {orchestrator_output.tool_parameters}")
            return self.tools["calculator"].run(orchestrator_output.tool_parameters)
        elif orchestrator_output.tool == "rag":
            if not isinstance(orchestrator_output.tool_parameters, RAGSearchToolInputSchema):
                raise ValueError(f"Invalid parameters for RAG tool: {orchestrator_output.tool_parameters}")
            return self.tools["rag"].run(orchestrator_output.tool_parameters)
        elif orchestrator_output.tool == "deep-research":
            if not isinstance(orchestrator_output.tool_parameters, DeepResearchToolInputSchema):
                raise ValueError(f"Invalid parameters for deep research tool: {orchestrator_output.tool_parameters}")
            return self.tools["deep_research"].run(orchestrator_output.tool_parameters)
        else:
            raise ValueError(f"Unknown tool: {orchestrator_output.tool}")
    
    def get_available_tools(self) -> list[str]:
        """Get list of available tool names.
        
        Returns:
            List of tool names that can be used
        """
        return list(self.tools.keys())
    
    def get_tool_instance(self, tool_name: str) -> Any:
        """Get a specific tool instance by name.
        
        Args:
            tool_name: Name of the tool to retrieve
            
        Returns:
            The tool instance
            
        Raises:
            KeyError: If tool name is not found
        """
        if tool_name not in self.tools:
            raise KeyError(f"Tool '{tool_name}' not found. Available tools: {list(self.tools.keys())}")
        return self.tools[tool_name]