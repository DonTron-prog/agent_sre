#!/usr/bin/env python3
"""
Atomic Planning Agent Executor - Entry point using Atomic Agents framework.
"""

import openai
import instructor
from rich.console import Console
from rich.panel import Panel
from orchestration_engine import ConfigManager, ToolManager, OrchestratorCore, create_orchestrator_agent
from controllers.planning_agent.atomic_planning_agent import (
    AtomicPlanningAgent,
    AtomicPlanningInputSchema,
    create_atomic_planning_agent
)
from controllers.planning_agent.execution_orchestrator import (
    ExecutionOrchestrator,
    ExecutionOrchestratorInputSchema
)
from controllers.planning_agent.planner_schemas import (
    PlanningAgentOutputSchema,
    SimplePlanSchema
)


def process_alert_with_atomic_planning(alert: str, context: str = "", model: str = "mistral/ministral-8b") -> PlanningAgentOutputSchema:
    """
    Process an alert using the atomic planning agent architecture.
    
    This function demonstrates the atomic agents pattern:
    1. AtomicPlanningAgent generates structured plans
    2. ExecutionOrchestrator executes the plans
    3. Clean separation of concerns with schema-based chaining
    
    Args:
        alert: The system alert to process
        context: Contextual information about the system
        model: Model name for LLM calls
        
    Returns:
        PlanningAgentOutputSchema: Complete planning execution results
    """
    console = Console()
    
    # Initialize components
    config = ConfigManager.load_configuration()
    tools = ConfigManager.initialize_tools(config)
    
    # Create instructor client for orchestrator agent
    client = openai.OpenAI(
        base_url="https://openrouter.ai/api/v1",
        api_key=config.get("openrouter_api_key")
    )
    instructor_client = instructor.from_openai(client, mode=instructor.Mode.JSON)
    
    # Create orchestrator core
    orchestrator_agent = create_orchestrator_agent(instructor_client, model)
    tool_manager = ToolManager(tools)
    orchestrator_core = OrchestratorCore(orchestrator_agent, tool_manager)
    
    console.print(Panel(
        "[bold blue]🤖 Atomic Planning Agent[/bold blue]\n"
        "Using Atomic Agents framework for structured planning...",
        title="Planning Phase",
        border_style="blue"
    ))
    
    # Step 1: Create atomic planning agent using the factory function
    planning_agent = create_atomic_planning_agent(
        client=instructor_client,
        model=model
    )
    
    # Step 2: Generate plan using atomic planning agent
    planning_input = AtomicPlanningInputSchema(
        alert=alert,
        context=context
    )
    
    try:
        planning_result = planning_agent.run(planning_input)
        
        console.print(Panel(
            f"[green]✅ Plan Generated[/green]\n"
            f"[yellow]Steps:[/yellow] {len(planning_result.steps)}\n"
            f"[yellow]Reasoning:[/yellow] {planning_result.reasoning[:100]}...",
            title="Planning Complete",
            border_style="green"
        ))
        
        # Display the generated plan
        console.print("\n[bold cyan]📋 Generated Plan:[/bold cyan]")
        for i, step in enumerate(planning_result.steps, 1):
            console.print(f"  {i}. {step.description}")
        
        console.print(Panel(
            "[bold blue]🚀 Execution Phase[/bold blue]\n"
            "Executing plan using orchestration engine...",
            title="Execution Phase",
            border_style="blue"
        ))
        
        # Step 3: Execute plan using execution orchestrator with direct integration
        execution_orchestrator = ExecutionOrchestrator(orchestrator_core)
        execution_input = ExecutionOrchestratorInputSchema(
            alert=alert,
            context=context,
            planning_output=planning_result
        )
        
        execution_result = execution_orchestrator.run(execution_input)
        
        # Step 4: Generate final summary
        final_summary = f"""# Atomic Planning Agent Execution Summary

## Planning Phase
**Reasoning:** {planning_result.reasoning}

## Execution Phase
{execution_result.final_summary}

## Overall Result
- **Success:** {'✅ Yes' if execution_result.success else '❌ No'}
- **Steps Executed:** {len(execution_result.executed_steps)}
- **Tools Used:** {', '.join(set(step.tool_used for step in execution_result.executed_steps))}

## Key Insights
{execution_result.accumulated_knowledge}
"""
        
        # Create a simple plan for the final result with execution results
        simple_plan = SimplePlanSchema(
            alert=alert,
            context=context,
            steps=planning_result.steps,
            accumulated_knowledge=execution_result.accumulated_knowledge
        )
        
        # Update the simple plan with execution results
        for i, step_result in enumerate(execution_result.executed_steps):
            if i < len(simple_plan.steps):
                simple_plan.steps[i].status = step_result.status
                simple_plan.steps[i].result = step_result.full_result
        
        return PlanningAgentOutputSchema(
            plan=simple_plan,
            summary=final_summary,
            success=execution_result.success
        )
        
    except Exception as e:
        console.print(Panel(
            f"[red]❌ Error in atomic planning: {e}[/red]",
            title="Planning Error",
            border_style="red"
        ))
        
        # Return error result
        error_plan = SimplePlanSchema(
            alert=alert,
            context=context,
            steps=[],
            accumulated_knowledge=f"Error occurred: {str(e)}"
        )
        
        return PlanningAgentOutputSchema(
            plan=error_plan,
            summary=f"Planning failed with error: {str(e)}",
            success=False
        )


def run_atomic_planning_scenarios(example_data, model: str = "mistral/ministral-8b"):
    """
    Run example scenarios using the atomic planning agent.
    
    Args:
        example_data: List of alert scenarios
        model: Model name for LLM calls
    """
    console = Console()
    
    for i, scenario in enumerate(example_data, 1):
        console.print(Panel(
            f"[bold blue]Atomic Planning Scenario {i}[/bold blue]\n"
            f"[yellow]Alert:[/yellow] {scenario['alert']}\n"
            f"[yellow]Context:[/yellow] {scenario['context']}",
            title="🤖 Atomic SRE Planning Agent",
            border_style="blue"
        ))
        
        try:
            result = process_alert_with_atomic_planning(
                scenario["alert"],
                scenario["context"],
                model
            )
            
            # Display the summary
            console.print(Panel(
                result.summary,
                title="📋 Atomic Planning Execution Summary",
                border_style="green" if result.success else "red"
            ))
            
        except Exception as e:
            console.print(Panel(
                f"[red]Error processing scenario: {e}[/red]",
                title="❌ Atomic Planning Error",
                border_style="red"
            ))
        
        console.print("\n" + "="*80 + "\n")


def main():
    """Main entry point for the atomic planning agent."""
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
        }
    ]
    
    console = Console()
    console.print(Panel(
        "[bold blue]🤖 Atomic SRE Planning Agent[/bold blue]\n"
        "Running example scenarios with atomic agents architecture...\n"
        "[green]✨ Features:[/green]\n"
        "• Structured planning with guaranteed schemas\n"
        "• Separation of planning and execution concerns\n"
        "• Schema-based component chaining\n"
        "• Full transparency and debuggability",
        title="Atomic Planning Agent Executor",
        border_style="blue"
    ))
    
    run_atomic_planning_scenarios(example_alerts)


if __name__ == "__main__":
    main()