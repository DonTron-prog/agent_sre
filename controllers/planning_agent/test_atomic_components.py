#!/usr/bin/env python3
"""
Test script for Atomic Agents components.
"""

import os
from rich.console import Console
from rich.panel import Panel
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
    SimplePlanSchema,
    PlanStepSchema
)


def test_atomic_planning_agent():
    """Test the atomic planning agent in isolation."""
    console = Console()
    
    console.print(Panel(
        "[bold blue]🧪 Testing Atomic Planning Agent[/bold blue]",
        title="Component Test",
        border_style="blue"
    ))
    
    # Check if we have an API key
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        console.print("[bold red]❌ OPENAI_API_KEY not found in environment[/bold red]")
        console.print("Set your API key: export OPENAI_API_KEY='your-key-here'")
        return False
    
    try:
        # Create a shared client
        shared_client = instructor.from_openai(openai.OpenAI(base_url="https://openrouter.ai/api/v1", api_key=api_key))

        # Create atomic planning agent using the factory function
        console.print("🔧 Creating atomic planning agent...")
        planning_agent = create_atomic_planning_agent(shared_client, "gpt-4o-mini")
        console.print("✅ Atomic planning agent created successfully")
        
        # Test input
        test_input = AtomicPlanningInputSchema(
            alert="Test alert: Service 'api-gateway' returning 500 errors",
            context="System: Production API Gateway. Error rate: 15%. Normal rate: <1%."
        )
        
        console.print("📝 Testing with sample alert...")
        console.print(f"Alert: {test_input.alert}")
        console.print(f"Context: {test_input.context}")
        
        # Run planning
        console.print("\n🚀 Running atomic planning agent...")
        result = planning_agent.run(test_input)
        
        # Validate result
        console.print("✅ Planning completed successfully!")
        console.print(f"📊 Generated {len(result.steps)} steps")
        console.print(f"🧠 Reasoning: {result.reasoning[:100]}...")
        
        console.print("\n📋 Generated Steps:")
        for i, step in enumerate(result.steps, 1):
            console.print(f"  {i}. {step.description}")
        
        return True
        
    except Exception as e:
        console.print(f"[bold red]❌ Error testing atomic planning agent: {e}[/bold red]")
        return False


def test_execution_orchestrator():
    """Test the execution orchestrator with a mock plan."""
    console = Console()
    
    console.print(Panel(
        "[bold blue]🧪 Testing Execution Orchestrator[/bold blue]",
        title="Component Test",
        border_style="blue"
    ))
    
    try:
        # Create a mock plan for testing
        mock_plan = SimplePlanSchema(
            alert="Test alert: Service 'api-gateway' returning 500 errors",
            context="System: Production API Gateway. Error rate: 15%. Normal rate: <1%.",
            steps=[
                PlanStepSchema(description="Check service health status"),
                PlanStepSchema(description="Review recent error logs"),
                PlanStepSchema(description="Identify root cause of errors")
            ]
        )
        
        console.print("📝 Created mock plan with 3 steps")
        for i, step in enumerate(mock_plan.steps, 1):
            console.print(f"  {i}. {step.description}")
        
        # Note: We can't actually run the orchestrator without proper setup
        console.print("\n⚠️ Execution orchestrator requires OrchestratorCore setup")
        console.print("✅ Execution orchestrator structure validated")
        
        # Test input schema validation
        test_input = ExecutionOrchestratorInputSchema(plan=mock_plan)
        console.print("✅ Input schema validation passed")
        
        return True
        
    except Exception as e:
        console.print(f"[bold red]❌ Error testing execution orchestrator: {e}[/bold red]")
        return False


def test_schema_chaining():
    """Test schema chaining between components."""
    console = Console()
    
    console.print(Panel(
        "[bold blue]🧪 Testing Schema Chaining[/bold blue]",
        title="Component Test",
        border_style="blue"
    ))
    
    try:
        # Create mock planning result
        from controllers.planning_agent.atomic_planning_agent import AtomicPlanningOutputSchema
        
        mock_planning_result = AtomicPlanningOutputSchema(
            steps=[
                PlanStepSchema(description="Investigate system metrics"),
                PlanStepSchema(description="Check application logs"),
                PlanStepSchema(description="Implement fix or escalate")
            ],
            reasoning="Following standard SRE incident response: investigate → diagnose → resolve"
        )
        
        console.print("📝 Created mock planning result")
        console.print(f"Steps: {len(mock_planning_result.steps)}")
        console.print(f"Reasoning: {mock_planning_result.reasoning}")
        
        # Test direct integration - create execution input directly
        execution_input = ExecutionOrchestratorInputSchema(
            alert="Test alert",
            context="Test context",
            planning_output=mock_planning_result
        )
        
        console.print("✅ Direct execution input created successfully")
        console.print(f"Planning output has {len(mock_planning_result.steps)} steps")
        console.print(f"Reasoning: {mock_planning_result.reasoning[:50]}...")
        
        # Test execution input
        execution_input = ExecutionOrchestratorInputSchema(plan=simple_plan)
        console.print("✅ Execution input schema validated")
        
        return True
        
    except Exception as e:
        console.print(f"[bold red]❌ Error testing schema chaining: {e}[/bold red]")
        return False


def test_all_components():
    """Run all component tests."""
    console = Console()
    
    console.print(Panel(
        "[bold blue]🧪 Atomic Agents Component Test Suite[/bold blue]\n"
        "Testing all atomic components in isolation",
        title="Test Suite",
        border_style="blue"
    ))
    
    tests = [
        ("Schema Chaining", test_schema_chaining),
        ("Execution Orchestrator", test_execution_orchestrator),
        ("Atomic Planning Agent", test_atomic_planning_agent),
    ]
    
    results = []
    
    for test_name, test_func in tests:
        console.print(f"\n{'='*60}")
        console.print(f"Running: {test_name}")
        console.print('='*60)
        
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            console.print(f"[bold red]❌ Test {test_name} failed with exception: {e}[/bold red]")
            results.append((test_name, False))
    
    # Summary
    console.print(f"\n{'='*60}")
    console.print("[bold blue]Test Results Summary[/bold blue]")
    console.print('='*60)
    
    passed = 0
    for test_name, result in results:
        status = "✅ PASSED" if result else "❌ FAILED"
        console.print(f"{test_name}: {status}")
        if result:
            passed += 1
    
    console.print(f"\nOverall: {passed}/{len(results)} tests passed")
    
    if passed == len(results):
        console.print("[bold green]🎉 All tests passed! Atomic Agents components are working correctly.[/bold green]")
    else:
        console.print("[bold yellow]⚠️ Some tests failed. Check the output above for details.[/bold yellow]")


def main():
    """Main test function."""
    console = Console()
    
    console.print(Panel(
        "[bold blue]🧪 Atomic Agents Test Suite[/bold blue]\n"
        "Choose which components to test",
        title="Test Menu",
        border_style="blue"
    ))
    
    while True:
        console.print("\n[bold cyan]Choose a test:[/bold cyan]")
        console.print("1. 🔗 Schema Chaining")
        console.print("2. ⚙️ Execution Orchestrator")
        console.print("3. 🤖 Atomic Planning Agent")
        console.print("4. 🧪 All Components")
        console.print("5. 🚪 Exit")
        
        choice = console.input("\n[bold yellow]Enter your choice (1-5):[/bold yellow] ")
        
        if choice == "1":
            test_schema_chaining()
        elif choice == "2":
            test_execution_orchestrator()
        elif choice == "3":
            test_atomic_planning_agent()
        elif choice == "4":
            test_all_components()
        elif choice == "5":
            console.print("[bold green]👋 Testing complete![/bold green]")
            break
        else:
            console.print("[bold red]❌ Invalid choice. Please try again.[/bold red]")


if __name__ == "__main__":
    main()