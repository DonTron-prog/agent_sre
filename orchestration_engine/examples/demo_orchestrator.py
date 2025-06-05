#!/usr/bin/env python3
"""
Demo script for testing the orchestrator with example scenarios.
This file contains the example scenarios that were previously in orchestrator.py.
"""

import sys
from rich.console import Console
from rich.panel import Panel

from orchestration_engine import ConfigManager, create_orchestrator_agent, OrchestratorCore, ToolManager


def setup_environment_and_client(config):
    """Set up environment variables and initialize the OpenAI client."""
    import openai
    import instructor
    client = instructor.from_openai(openai.OpenAI(api_key=config["openai_api_key"]))
    return client


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


def main():
    """Main execution flow for demo scenarios."""
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
    
    # Standard orchestration mode
    config = ConfigManager.load_configuration()
    
    openai_client = setup_environment_and_client(config)
    
    agent = create_orchestrator_agent(
        client=openai_client,
        model_name=config["model_name"]
    )
    
    tool_instances = ConfigManager.initialize_tools(config)
    
    console_instance = Console()
    
    run_example_scenarios(
        agent=agent,
        tools=tool_instances,
        example_data=example_alerts,
        console=console_instance,
        generate_final_answer_flag=True
    )


if __name__ == "__main__":
    main()