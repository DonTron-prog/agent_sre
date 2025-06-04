"""Core orchestrator functionality for reusable components."""

from typing import Dict, Any, Tuple, Optional
from rich.console import Console
from rich.panel import Panel
from rich.syntax import Syntax
from pydantic import Field

from atomic_agents.agents.base_agent import BaseAgent, BaseAgentConfig
from atomic_agents.lib.components.agent_memory import AgentMemory
from atomic_agents.lib.components.system_prompt_generator import SystemPromptGenerator
from orchestration_engine.schemas.orchestrator_schemas import (
    OrchestratorInputSchema,
    OrchestratorOutputSchema,
    FinalAnswerSchema
)
from orchestration_engine.utils.tool_manager import ToolManager
from orchestration_engine.utils.interfaces import ExecutionContext, PlanningCapableOrchestrator
from orchestration_engine.utils.context_utils import CurrentDateProvider

from orchestration_engine.tools.searxng_search import SearxNGSearchToolConfig
from orchestration_engine.tools.calculator import CalculatorToolConfig
from orchestration_engine.tools.rag_search import RAGSearchToolConfig
from orchestration_engine.tools.deep_research import DeepResearchToolConfig


#######################
# AGENT CONFIGURATION #
#######################
class OrchestratorAgentConfig(BaseAgentConfig):
    """Configuration for the Orchestrator Agent."""

    searxng_config: SearxNGSearchToolConfig
    calculator_config: CalculatorToolConfig
    rag_config: RAGSearchToolConfig
    deep_research_config: DeepResearchToolConfig


###########################
# ORCHESTRATOR FUNCTIONS  #
###########################

def create_orchestrator_agent(client, model_name):
    """Create and configure the orchestrator agent instance."""
    system_prompt_generator = SystemPromptGenerator(
        background=[
            "You are an SRE Orchestrator Agent. Your primary role is to analyze a system alert and its associated context. Based on this analysis, you must decide which tool (RAG, web-search, deep-research, or calculator) will provide the most valuable additional information or context for a subsequent reflection agent to understand and act upon the alert.",
            "Use the RAG (Retrieval Augmented Generation) tool for querying internal SRE knowledge bases. This includes runbooks, incident histories, post-mortems, architectural diagrams, service dependencies, and internal documentation related to the alerted system or similar past issues.",
            "Use the web-search tool for finding external information. This includes searching for specific error codes, CVEs (Common Vulnerabilities and Exposures), documentation for third-party software or services, status pages of external dependencies, or general troubleshooting guides from the broader internet.",
            "Use the deep-research tool when you need comprehensive, multi-source research on complex topics. This tool automatically generates multiple search queries, scrapes content from multiple sources, and synthesizes comprehensive answers. Use this for complex troubleshooting scenarios, emerging technologies, or when you need detailed analysis of unfamiliar systems or error patterns.",
            "Use the calculator tool if the alert involves specific metrics, thresholds, or requires calculations to determine severity, impact (e.g., error budget consumption), or trends.",
        ],
        output_instructions=[
            "Carefully analyze the provided 'system_alert' and 'system_context'.",
            "Determine if the most valuable next step is to: query internal knowledge (RAG), search for external information (web-search), perform comprehensive research (deep-research), or perform a calculation (calculator).",
            "If RAG is chosen: use the 'rag' tool. Formulate a specific question for the RAG system based on the alert and context to retrieve relevant internal documentation (e.g., 'Find runbooks for high CPU on web servers', 'Retrieve incident history for ORA-12514 on payment_db').",
            "If web-search is chosen: use the 'search' tool. Provide 1-3 concise and relevant search queries based on the alert and context (e.g., 'ORA-12514 TNS listener error Oracle', 'Kubernetes Pod CrashLoopBackOff OOMKilled troubleshooting').",
            "If deep-research is chosen: use the 'deep-research' tool. Provide a comprehensive research question that requires analysis of multiple sources and synthesis of information (e.g., 'Research ExtPluginReplicationError Code 7749 in experimental-geo-sync-plugin v0.1.2 and provide troubleshooting guidance', 'Analyze Java OutOfMemoryError patterns in Kubernetes microservices and provide resolution strategies').",
            "If calculator is chosen: use the 'calculator' tool. Provide the mathematical expression needed (e.g., if latency increased from 50ms to 500ms, an expression could be '500 / 50' to find the factor of increase).",
            "Format your output strictly according to the OrchestratorOutputSchema.",
        ],
    )
    
    agent = BaseAgent(
        BaseAgentConfig(
            client=client,
            model=model_name,
            system_prompt_generator=system_prompt_generator,
            input_schema=OrchestratorInputSchema,
            output_schema=OrchestratorOutputSchema,
        )
    )
    
    agent.register_context_provider("current_date", CurrentDateProvider("Current Date"))
    
    return agent


class OrchestratorCore(PlanningCapableOrchestrator):
    """Core orchestrator functionality that can be used by planning agents."""
    
    def __init__(self, agent, tool_manager: ToolManager, console: Optional[Console] = None):
        """Initialize the orchestrator core.
        
        Args:
            agent: The orchestrator agent instance
            tool_manager: Tool manager for executing tools
            console: Rich console for output (optional)
        """
        self.agent = agent
        self.tool_manager = tool_manager
        self.console = console or Console()
    
    def execute_orchestration_step(self, input_schema: OrchestratorInputSchema, 
                                 reset_memory: bool = True) -> Tuple[OrchestratorOutputSchema, Any]:
        """Execute a single orchestration step.
        
        Args:
            input_schema: Input schema with alert and context
            reset_memory: Whether to reset agent memory after execution
            
        Returns:
            Tuple of (orchestrator_output, tool_response)
        """
        # Execute orchestrator to get tool selection
        orchestrator_output = self.agent.run(input_schema)
        
        # Execute the selected tool
        tool_response = self.tool_manager.execute_tool(orchestrator_output)
        
        # Reset memory if requested
        if reset_memory:
            self.reset_agent_memory()
            
        return orchestrator_output, tool_response
    
    def execute_with_context(self, execution_context: ExecutionContext) -> Dict[str, Any]:
        """Execute orchestration with planning context.
        
        Args:
            execution_context: Context containing alert, system context, and accumulated knowledge
            
        Returns:
            Dict containing orchestrator_output and tool_response
        """
        # Create input schema from execution context
        input_schema = OrchestratorInputSchema(
            system_alert=execution_context.alert,
            system_context=execution_context.context
        )
        
        # Execute the orchestration step without resetting memory (planning agent manages this)
        orchestrator_output, tool_response = self.execute_orchestration_step(
            input_schema, reset_memory=False
        )
        
        return {
            "orchestrator_output": orchestrator_output,
            "tool_response": tool_response,
            "step_id": execution_context.step_id,
            "step_description": execution_context.step_description
        }
    
    def get_available_tools(self) -> list[str]:
        """Get list of available tool names."""
        return self.tool_manager.get_available_tools()
    
    def generate_final_answer(self, input_schema: OrchestratorInputSchema, tool_response: Any) -> FinalAnswerSchema:
        """Generate a final answer based on the tool's output.
        
        Args:
            input_schema: Original input schema
            tool_response: Response from tool execution
            
        Returns:
            Final answer schema
        """
        # Store original output schema
        original_schema = self.agent.output_schema
        
        try:
            # Temporarily change output schema to FinalAnswerSchema
            self.agent.output_schema = FinalAnswerSchema
            
            # Add tool response to memory
            self.agent.memory.add_message("system", tool_response)
            
            # Generate final answer
            final_answer_obj = self.agent.run(input_schema)
            
            return final_answer_obj
            
        finally:
            # Restore original output schema
            self.agent.output_schema = original_schema
    
    def reset_agent_memory(self):
        """Reset the agent's memory for the next interaction."""
        self.agent.memory = AgentMemory()
    
    def process_single_alert(self, alert_data: Dict[str, str], 
                           generate_final_answer_flag: bool = False,
                           reset_memory: bool = True,
                           verbose: bool = True) -> Dict[str, Any]:
        """Process a single alert through the complete orchestration pipeline.
        
        Args:
            alert_data: Dictionary with 'alert' and 'context' keys
            generate_final_answer_flag: Whether to generate a final answer
            reset_memory: Whether to reset memory after processing
            verbose: Whether to print detailed output
            
        Returns:
            Dictionary containing all results from the processing
        """
        if verbose:
            self.console.print(Panel(
                f"[bold cyan]System Alert:[/bold cyan] {alert_data['alert']}\n"
                f"[bold cyan]System Context:[/bold cyan] {alert_data['context']}",
                expand=False
            ))
        
        # Prepare input schema
        input_schema = OrchestratorInputSchema(
            system_alert=alert_data["alert"], 
            system_context=alert_data["context"]
        )
        
        # Execute orchestration step
        orchestrator_output, tool_response = self.execute_orchestration_step(
            input_schema, reset_memory=False
        )
        
        if verbose:
            self.console.print("\n[bold magenta]Orchestrator Output:[/bold magenta]")
            orchestrator_syntax = Syntax(
                str(orchestrator_output.model_dump_json(indent=2)),
                "json",
                theme="monokai",
                line_numbers=True
            )
            self.console.print(orchestrator_syntax)
            
            self.console.print("\n[bold green]Tool Output:[/bold green]")
            output_syntax = Syntax(
                str(tool_response.model_dump_json(indent=2)),
                "json",
                theme="monokai",
                line_numbers=True
            )
            self.console.print(output_syntax)
            
            self.console.print("\n" + "-" * 80 + "\n")
        
        results = {
            "orchestrator_output": orchestrator_output,
            "tool_response": tool_response,
            "final_answer": None
        }
        
        # Handle final answer generation based on tool type
        if generate_final_answer_flag:
            if orchestrator_output.tool == "deep-research":
                # Deep research already provides comprehensive answer, no need to re-analyze
                if verbose:
                    self.console.print(f"\n[bold blue]Research Answer:[/bold blue] {tool_response.answer}")
                results["final_answer"] = tool_response.answer
            else:
                # Other tools return raw data that needs final answer generation
                final_answer_obj = self.generate_final_answer(input_schema, tool_response)
                if verbose:
                    self.console.print(f"\n[bold blue]Final Answer:[/bold blue] {final_answer_obj.final_answer}")
                results["final_answer"] = final_answer_obj.final_answer
        
        # Reset memory if requested
        if reset_memory:
            self.reset_agent_memory()
        
        return results