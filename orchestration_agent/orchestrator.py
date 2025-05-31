from typing import Union
import openai
from pydantic import Field
from atomic_agents.agents.base_agent import BaseAgent, BaseAgentConfig
from atomic_agents.lib.base.base_io_schema import BaseIOSchema
from atomic_agents.lib.components.agent_memory import AgentMemory
from atomic_agents.lib.components.system_prompt_generator import SystemPromptGenerator, SystemPromptContextProviderBase

# Import schemas from new location
from orchestration_agent.schemas.orchestrator_schemas import (
    OrchestratorInputSchema,
    OrchestratorOutputSchema,
    FinalAnswerSchema
)

# Import new utilities
from orchestration_agent.utils.config_manager import ConfigManager
from orchestration_agent.utils.tool_manager import ToolManager
from orchestration_agent.utils.orchestrator_core import OrchestratorCore

from orchestration_agent.tools.searxng_search import (
    SearxNGSearchToolConfig,
)
from orchestration_agent.tools.calculator import (
    CalculatorToolConfig,
)
from orchestration_agent.tools.rag_search import (
    RAGSearchToolConfig,
)
from orchestration_agent.tools.deep_research import (
    DeepResearchToolConfig,
)

import instructor
from datetime import datetime
from dotenv import load_dotenv
import os

from rich.console import Console
from rich.panel import Panel
from rich.syntax import Syntax

load_dotenv()  # Load environment variables from .env file


#######################
# AGENT CONFIGURATION #
#######################
class OrchestratorAgentConfig(BaseAgentConfig):
    """Configuration for the Orchestrator Agent."""

    searxng_config: SearxNGSearchToolConfig
    calculator_config: CalculatorToolConfig
    rag_config: RAGSearchToolConfig
    deep_research_config: DeepResearchToolConfig


#####################
# CONTEXT PROVIDERS #
#####################
class CurrentDateProvider(SystemPromptContextProviderBase):
    def __init__(self, title):
        super().__init__(title)
        self.date = datetime.now().strftime("%Y-%m-%d")

    def get_info(self) -> str:
        return f"Current date in format YYYY-MM-DD: {self.date}"

################
# TOOL EXECUTION #
################
# Legacy function for backward compatibility - now delegates to ToolManager
def execute_tool(searxng_tool, calculator_tool, rag_tool, deep_research_tool, orchestrator_output):
    """Legacy function for backward compatibility."""
    tools_dict = {
        "searxng": searxng_tool,
        "calculator": calculator_tool,
        "rag": rag_tool,
        "deep_research": deep_research_tool
    }
    tool_manager = ToolManager(tools_dict)
    return tool_manager.execute_tool(orchestrator_output)

###########################
# ORCHESTRATOR FUNCTIONS  #
###########################

# Legacy function for backward compatibility - now delegates to ConfigManager
def load_configuration():
    """Load configuration settings from environment variables or config files."""
    return ConfigManager.load_configuration()

def setup_environment_and_client(config):
    """Set up environment variables and initialize the OpenAI client."""
    client = instructor.from_openai(openai.OpenAI(api_key=config["openai_api_key"]))
    return client

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

# Legacy function for backward compatibility - now delegates to ConfigManager
def initialize_tools(config):
    """Initialize all required tools with their configurations."""
    return ConfigManager.initialize_tools(config)

def prepare_input_schema(alert_data):
    """Convert raw alert data into a properly formatted input schema."""
    return OrchestratorInputSchema(
        system_alert=alert_data["alert"], 
        system_context=alert_data["context"]
    )

def execute_orchestration_pipeline(agent, input_schema):
    """Run the orchestrator agent to determine which tool to use."""
    return agent.run(input_schema)

def handle_tool_execution(orchestrator_output, tools):
    """Execute the appropriate tool based on the orchestrator's decision."""
    return execute_tool(
        tools["searxng"],
        tools["calculator"],
        tools["rag"],
        tools["deep_research"],
        orchestrator_output
    )

def generate_final_answer(agent, input_schema, tool_response):
    """Generate a final answer based on the tool's output."""
    original_schema = agent.output_schema
    agent.output_schema = FinalAnswerSchema
    
    agent.memory.add_message("system", tool_response)

    final_answer_obj = agent.run(input_schema)
    
    agent.output_schema = original_schema
    
    return final_answer_obj

def reset_agent_memory(agent):
    """Reset the agent's memory for the next interaction."""
    agent.memory = AgentMemory()

def process_single_alert(agent, tools, alert_data, console, generate_final_answer_flag=False, reset_memory=True):
    """Process a single alert through the complete orchestration pipeline."""
    # Create tool manager and orchestrator core for enhanced functionality
    tool_manager = ToolManager(tools)
    orchestrator_core = OrchestratorCore(agent, tool_manager, console)
    
    # Use the new orchestrator core method
    return orchestrator_core.process_single_alert(
        alert_data=alert_data,
        generate_final_answer_flag=generate_final_answer_flag,
        reset_memory=reset_memory,
        verbose=True
    )

def run_example_scenarios(agent, tools, example_data, console, generate_final_answer_flag=False, reset_memory=True):
    """Run through a list of example scenarios."""
    console.print(Panel(
        agent.system_prompt_generator.generate_prompt(),
        title="System Prompt",
        expand=False
    ))
    console.print("\n")
    
    for alert_input in example_data:
        process_single_alert(
            agent=agent,
            tools=tools,
            alert_data=alert_input,
            console=console,
            generate_final_answer_flag=generate_final_answer_flag,
            reset_memory=reset_memory
        )

#######################
# MAIN EXECUTION FLOW #
#######################
if __name__ == "__main__":
    config = load_configuration()
    
    openai_client = setup_environment_and_client(config)
    
    agent = create_orchestrator_agent(
        client=openai_client,
        model_name=config["model_name"]
    )
    
    tool_instances = initialize_tools(config)
    
    console_instance = Console()
    
    example_alerts = [
        {
            "alert": "Critical failure: 'ExtPluginReplicationError: Code 7749 - Sync Timeout with AlphaNode' in 'experimental-geo-sync-plugin v0.1.2' on db-primary.",
            "context": "System: Primary PostgreSQL Database (Version 15.3). Plugin: 'experimental-geo-sync-plugin v0.1.2' (third-party, integrated yesterday for PoC). Service: Attempting geo-replicated read-replica setup. Internal Documentation: Confirmed NO internal documentation or runbooks exist for this experimental plugin or its error codes. Vendor documentation for v0.1.2 is sparse."
        },
        {
            "alert": "Pod CrashLoopBackOff for service 'checkout-service' in Kubernetes cluster 'prod-east-1'. Error log snippet: 'java.lang.OutOfMemoryError: Java heap space'.",
            "context": "System: Kubernetes microservice (Java Spring Boot). Service: Checkout processing. Resource limits: Memory 512Mi, CPU 0.5 core. Traffic: Experiencing 3x normal load due to flash sale."
        },
        {
            "alert": "API endpoint /api/v2/orders returning 503 Service Unavailable for 5% of requests over the last 10 minutes. Latency P99 is 2500ms.",
            "context": "System: API Gateway (Kong) and backend OrderService. Service: Order placement. Dependencies: InventoryService, PaymentService. Current error rate threshold: < 1%. Latency SLO: P99 < 800ms."
        },
        {
            "alert": "Unusual network traffic pattern detected: 'TLS handshake failures increased by 400% from external IPs in APAC region' affecting load balancer 'prod-lb-01'.",
            "context": "System: Production Load Balancer (HAProxy 2.4). Service: Frontend traffic distribution. Recent changes: SSL certificate renewal completed 2 hours ago. Geographic pattern: 85% of failures from previously unseen IP ranges in Asia-Pacific. No internal documentation exists for this specific failure pattern or geographic correlation analysis."
        }
        #{
        #    "alert": "High CPU utilization (95%) on server web-prod-01 for 15 minutes.",
        #    "context": "System: Production Web Server Cluster (nginx, Python/Flask). Service: Main customer-facing website. Recent changes: New deployment v2.3.1 two hours ago. Known issues: Occasional spikes during peak load. Monitoring tool: Prometheus."
        #},
    ]
    
    run_example_scenarios(
        agent=agent,
        tools=tool_instances,
        example_data=example_alerts,
        console=console_instance,
        generate_final_answer_flag=True
    )
