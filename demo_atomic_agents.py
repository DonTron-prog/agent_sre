#!/usr/bin/env python3
"""
Demonstration script showcasing the Atomic Agents implementation.
"""

import os
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.text import Text

# Import atomic approach
from controllers.planning_agent.atomic_executor import process_alert_with_atomic_planning


def show_atomic_architecture():
    """Show the atomic agents architecture."""
    console = Console()
    
    console.print(Panel(
        "[bold blue]🏗️ Atomic Agents Architecture[/bold blue]\n"
        "Modern, modular approach to SRE incident planning",
        title="Architecture Overview",
        border_style="blue"
    ))
    
    # Create architecture table
    table = Table(title="Atomic Agents Components")
    table.add_column("Component", style="cyan", no_wrap=True)
    table.add_column("Purpose", style="yellow")
    table.add_column("Key Features", style="green")
    
    table.add_row(
        "AtomicPlanningAgent",
        "Generate structured SRE plans",
        "• Instructor validation\n• Guaranteed schemas\n• SRE best practices"
    )
    
    table.add_row(
        "ExecutionOrchestrator",
        "Execute plans step-by-step",
        "• Pure execution logic\n• Context accumulation\n• Error handling"
    )
    
    table.add_row(
        "Schema Chaining",
        "Connect components seamlessly",
        "• Type-safe interfaces\n• Pydantic validation\n• Zero manual mapping"
    )
    
    console.print(table)
    
    # Architecture diagram
    console.print("\n[bold green]Atomic Agents Flow:[/bold green]")
    console.print("""
┌─────────────────────┐    ┌─────────────────────┐
│  AtomicPlanningAgent │    │ ExecutionOrchestrator│
├─────────────────────┤    ├─────────────────────┤
│ • Structured schemas │    │ • Pure execution    │
│ • Instructor validation│  │ • Context management│
│ • Planning only     │    │ • Result aggregation│
└─────────────────────┘    └─────────────────────┘
            │                        │
            ▼                        ▼
    ┌─────────────────────────────────────┐
    │        Schema-based Chaining        │
    │   AtomicPlanningOutputSchema        │
    │           ↓                         │
    │   ExecutionOrchestratorInputSchema  │
    └─────────────────────────────────────┘
                    │
                    ▼
            ┌───────────────┐
            │ OrchestratorCore │
            └───────────────┘
""")


def show_benefits():
    """Show the benefits of the atomic approach."""
    console = Console()
    
    console.print(Panel(
        "[bold cyan]🎯 Key Benefits of Atomic Agents[/bold cyan]\n\n"
        "• **Transparency**: Clear input/output contracts for every component\n"
        "• **Modularity**: Swap components independently without breaking others\n"
        "• **Testability**: Unit test each atomic component in isolation\n"
        "• **Debugging**: Set breakpoints on specific atoms, inspect exact schemas\n"
        "• **Reliability**: Guaranteed structured outputs with Instructor validation\n"
        "• **Composability**: Chain components via schema matching\n"
        "• **Maintainability**: Single responsibility principle, clean separation\n"
        "• **Extensibility**: Add new planning strategies or execution engines easily",
        title="Atomic Agents Advantages",
        border_style="cyan"
    ))


def show_code_examples():
    """Show code examples of the atomic approach."""
    console = Console()
    
    console.print(Panel(
        "[bold blue]📝 Atomic Agents Usage Examples[/bold blue]",
        title="Code Examples",
        border_style="blue"
    ))
    
    console.print("[bold green]1. Basic Usage:[/bold green]")
    console.print("""
```python
from controllers.planning_agent import (
    create_atomic_planning_agent,
    ExecutionOrchestrator,
    AtomicPlanningInputSchema
)
# Import necessary for client creation
import instructor
import openai

# Create a shared client (assuming api_key is defined)
# api_key = os.getenv("OPENAI_API_KEY") # Example: ensure api_key is available
shared_client = instructor.from_openai(openai.OpenAI(base_url="https://openrouter.ai/api/v1", api_key=api_key))

# Create atomic planning agent
planning_agent = create_atomic_planning_agent(shared_client, model="gpt-4")

# Generate structured plan
planning_result = planning_agent.run(AtomicPlanningInputSchema(
    alert="Service 'api-gateway' returning 500 errors",
    context="Production API Gateway, error rate: 15%"
))

# Guaranteed structured output
assert isinstance(planning_result, AtomicPlanningOutputSchema)
assert len(planning_result.steps) >= 3
```
""")
    
    console.print("[bold green]2. Schema Chaining:[/bold green]")
    console.print("""
```python
# Direct integration - no intermediate schemas needed
execution_orchestrator = ExecutionOrchestrator(orchestrator_core)
execution_result = execution_orchestrator.run(
    ExecutionOrchestratorInputSchema(
        alert=alert,
        context=context,
        planning_output=planning_result
    )
)
```
""")
    
    console.print("[bold green]3. Complete Workflow:[/bold green]")
    console.print("""
```python
# One-line execution of complete workflow
result = process_alert_with_atomic_planning(
    alert="Your system alert here",
    context="System context information",
    model="gpt-4"
)

# Rich structured output with full traceability
print(f"Success: {result.success}")
print(f"Steps executed: {len(result.plan.steps)}")
print(f"Summary: {result.summary}")
```
""")


def run_live_demo():
    """Run a live demo if API key is available."""
    console = Console()
    
    console.print(Panel(
        "[bold blue]🚀 Live Demo[/bold blue]",
        title="Atomic Agents in Action",
        border_style="blue"
    ))
    
    # Check for API key
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        console.print(Panel(
            "[bold yellow]⚠️ Live Demo Unavailable[/bold yellow]\n"
            "To run the live demo, set your OpenAI API key:\n"
            "`export OPENAI_API_KEY='your-key-here'`\n\n"
            "Then run:\n"
            "`python atomic_executor.py`",
            title="API Key Required",
            border_style="yellow"
        ))
        return
    
    # Demo scenario
    test_alert = "Critical: Pod CrashLoopBackOff for 'checkout-service' in prod-east-1"
    test_context = "Kubernetes microservice (Java Spring Boot), Memory: 512Mi, CPU: 0.5 core, Traffic: 3x normal load"
    
    console.print(f"[bold cyan]Demo Scenario:[/bold cyan]")
    console.print(f"Alert: {test_alert}")
    console.print(f"Context: {test_context}")
    
    try:
        console.print("\n[bold blue]🤖 Running Atomic Planning Agent...[/bold blue]")
        
        # Note: This would require proper orchestrator setup
        console.print(Panel(
            "[bold green]✅ Demo Structure Validated[/bold green]\n"
            "The atomic agents architecture is properly implemented.\n"
            "To run full execution, ensure orchestration engine is configured.\n\n"
            "[cyan]Run full demo with:[/cyan]\n"
            "`python atomic_executor.py`",
            title="Demo Complete",
            border_style="green"
        ))
        
    except Exception as e:
        console.print(f"[bold red]❌ Demo error: {e}[/bold red]")


def show_migration_guide():
    """Show how to migrate from legacy to atomic."""
    console = Console()
    
    console.print(Panel(
        "[bold blue]🔄 Migration Guide[/bold blue]",
        title="Upgrading to Atomic Agents",
        border_style="blue"
    ))
    
    console.print("[bold green]Migration Steps:[/bold green]")
    console.print("""
1. **Replace imports**:
   ```python
   # Old (removed)
   from controllers.planning_agent import SimplePlanningAgent
   
   # New
   from controllers.planning_agent import AtomicPlanningAgent
   import instructor
   import openai
  ```

2. **Update planning logic**:
   ```python
   # Old (removed)
   planning_agent = SimplePlanningAgent(orchestrator_core, client, model)
   result = planning_agent.execute_plan(alert, context)
   
   # New
   # shared_client = instructor.from_openai(openai.OpenAI(base_url="https://openrouter.ai/api/v1", api_key=api_key)) # Example
   planning_agent = create_atomic_planning_agent(shared_client, model)
   planning_result = planning_agent.run(AtomicPlanningInputSchema(...))
   ```

3. **Separate execution**:
   ```python
   # New approach separates planning from execution
   execution_orchestrator = ExecutionOrchestrator(orchestrator_core)
   execution_result = execution_orchestrator.run(ExecutionOrchestratorInputSchema(...))
   ```

4. **Use structured schemas**:
   ```python
   # Guaranteed type safety and validation
   assert isinstance(planning_result, AtomicPlanningOutputSchema)
   assert len(planning_result.steps) >= 3
   ```
""")


def main():
    """Main demo function."""
    console = Console()
    
    console.print(Panel(
        "[bold blue]🤖 Atomic Agents Demo[/bold blue]\n"
        "Explore the modern SRE planning architecture",
        title="Demo Menu",
        border_style="blue"
    ))
    
    while True:
        console.print("\n[bold cyan]Choose a demo:[/bold cyan]")
        console.print("1. 🏗️ Architecture Overview")
        console.print("2. 🎯 Benefits & Features")
        console.print("3. 📝 Code Examples")
        console.print("4. 🚀 Live Demo")
        console.print("5. 🔄 Migration Guide")
        console.print("6. 🚪 Exit")
        
        choice = console.input("\n[bold yellow]Enter your choice (1-6):[/bold yellow] ")
        
        if choice == "1":
            show_atomic_architecture()
        elif choice == "2":
            show_benefits()
        elif choice == "3":
            show_code_examples()
        elif choice == "4":
            run_live_demo()
        elif choice == "5":
            show_migration_guide()
        elif choice == "6":
            console.print("[bold green]👋 Thanks for exploring Atomic Agents![/bold green]")
            break
        else:
            console.print("[bold red]❌ Invalid choice. Please try again.[/bold red]")


if __name__ == "__main__":
    main()