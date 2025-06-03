#!/usr/bin/env python3
"""
Planning Agent Executor - Entry point for running the planning agent pipeline.
"""

import openai
from rich.console import Console
from rich.panel import Panel
from orchestration_engine import ConfigManager, ToolManager, OrchestratorCore
from orchestration_engine.orchestrator import create_orchestrator_agent
from controllers.planning_agent.planner_schemas import PlanningAgentOutputSchema
from controllers.planning_agent.simple_agent import SimplePlanningAgent


def process_alert_with_planning(alert: str, context: str = "", model: str = "gpt-4") -> PlanningAgentOutputSchema:
    """
    Process an alert using the planning agent.
    
    Args:
        alert: The system alert to process
        context: Contextual information about the system
        model: Model name for LLM calls
        
    Returns:
        PlanningAgentOutputSchema: Complete planning execution results
    """
    # Initialize components
    config = ConfigManager.load_configuration()
    tools = ConfigManager.initialize_tools(config)
    
    # Create instructor client (required by orchestrator agent)
    import instructor
    client = instructor.from_openai(openai.OpenAI(api_key=config.get("openai_api_key")))
    
    # Create orchestrator core
    orchestrator_agent = create_orchestrator_agent(client, model)
    tool_manager = ToolManager(tools)
    orchestrator_core = OrchestratorCore(orchestrator_agent, tool_manager)
    
    # Create and run planning agent
    # Use regular OpenAI client for planning agent LLM calls
    openai_client = openai.OpenAI(api_key=config.get("openai_api_key"))
    planning_agent = SimplePlanningAgent(orchestrator_core, openai_client, model)
    
    return planning_agent.execute_plan(alert, context)


def run_planning_scenarios(example_data, model: str = "gpt-4"):
    """
    Run example scenarios using the planning agent.
    
    Args:
        example_data: List of alert scenarios
        model: Model name for LLM calls
    """
    console = Console()
    
    for i, scenario in enumerate(example_data, 1):
        console.print(Panel(
            f"[bold blue]Planning Scenario {i}[/bold blue]\n"
            f"[yellow]Alert:[/yellow] {scenario['alert']}\n"
            f"[yellow]Context:[/yellow] {scenario['context']}",
            title="🤖 SRE Planning Agent",
            border_style="blue"
        ))
        
        try:
            result = process_alert_with_planning(
                scenario["alert"],
                scenario["context"],
                model
            )
            
            # Display the summary
            console.print(Panel(
                result.summary,
                title="📋 Planning Execution Summary",
                border_style="green" if result.success else "red"
            ))
            
        except Exception as e:
            console.print(Panel(
                f"[red]Error processing scenario: {e}[/red]",
                title="❌ Planning Error",
                border_style="red"
            ))
        
        console.print("\n" + "="*80 + "\n")


def main():
    """Main entry point for the planning agent."""
    import sys
    
    # Define example scenarios
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
    ]
    
    console = Console()
    console.print(Panel(
        "[bold blue]🤖 SRE Planning Agent[/bold blue]\n"
        "Running example scenarios with multi-step planning...",
        title="Planning Agent Executor",
        border_style="blue"
    ))
    
    run_planning_scenarios(example_alerts)


if __name__ == "__main__":
    main()