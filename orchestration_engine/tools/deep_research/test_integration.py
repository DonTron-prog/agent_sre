#!/usr/bin/env python3
"""
Test script for Deep Research Tool integration with the orchestrator.
This script tests the deep research functionality independently.
"""

import sys
import os

# Add the parent directories to the path so we can import the modules
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..', '..'))

from orchestration_engine.tools.deep_research import (
    DeepResearchTool,
    DeepResearchToolConfig,
    DeepResearchToolInputSchema,
    perform_deep_research,
    display_research_results
)

from rich.console import Console

console = Console()


def test_deep_research_tool():
    """Test the Deep Research Tool directly."""
    console.print("\n[bold blue]Testing Deep Research Tool Integration[/bold blue]")
    console.print("=" * 60)
    
    # Test query that would benefit from deep research
    test_query = "ExtPluginReplicationError Code 7749 in experimental-geo-sync-plugin troubleshooting and resolution strategies"
    
    console.print(f"\n[bold yellow]Research Query:[/bold yellow] {test_query}")
    console.print("\n[dim]Initializing Deep Research Tool...[/dim]")
    
    try:
        # Test using the standalone function
        result = perform_deep_research(
            research_query=test_query,
            searxng_base_url="http://localhost:8080/",
            max_results=2  # Limit for testing
        )
        
        console.print("\n[bold green]✅ Deep Research completed successfully![/bold green]")
        
        # Display the results
        display_research_results(result)
        
        return True
        
    except Exception as e:
        console.print(f"\n[bold red]❌ Error during deep research: {e}[/bold red]")
        return False


def test_tool_class_directly():
    """Test the DeepResearchTool class directly."""
    console.print("\n[bold blue]Testing DeepResearchTool Class[/bold blue]")
    console.print("=" * 60)
    
    try:
        # Initialize the tool
        config = DeepResearchToolConfig(
            searxng_base_url="http://localhost:8080/",
            max_search_results=2
        )
        tool = DeepResearchTool(config)
        
        # Create input
        input_data = DeepResearchToolInputSchema(
            research_query="TLS handshake failure patterns and troubleshooting in HAProxy load balancers",
            max_search_results=2
        )
        
        console.print(f"\n[bold yellow]Research Query:[/bold yellow] {input_data.research_query}")
        console.print("\n[dim]Running tool.run()...[/dim]")
        
        # Run the tool
        result = tool.run(input_data)
        
        console.print("\n[bold green]✅ Tool execution completed successfully![/bold green]")
        
        # Display basic result info
        console.print(f"\n[bold cyan]Answer Length:[/bold cyan] {len(result.answer)} characters")
        console.print(f"[bold cyan]Sources Found:[/bold cyan] {len(result.sources)}")
        console.print(f"[bold cyan]Follow-up Questions:[/bold cyan] {len(result.follow_up_questions)}")
        console.print(f"[bold cyan]Search Queries Used:[/bold cyan] {len(result.search_queries_used)}")
        
        return True
        
    except Exception as e:
        console.print(f"\n[bold red]❌ Error during tool execution: {e}[/bold red]")
        return False


if __name__ == "__main__":
    console.print("\n[bold magenta]🧪 Deep Research Tool Integration Tests[/bold magenta]")
    
    # Check if SearxNG is available
    console.print("\n[yellow]Note: These tests require SearxNG to be running at http://localhost:8080/[/yellow]")
    console.print("[yellow]If SearxNG is not available, the tests will fail with connection errors.[/yellow]")
    
    proceed = console.input("\n[bold]Continue with tests? (y/N): [/bold]").strip().lower()
    if proceed not in ['y', 'yes']:
        console.print("\n[dim]Tests cancelled.[/dim]")
        sys.exit(0)
    
    # Run tests
    test1_passed = test_deep_research_tool()
    test2_passed = test_tool_class_directly()
    
    # Summary
    console.print("\n" + "=" * 60)
    console.print("[bold blue]Test Summary[/bold blue]")
    console.print(f"Standalone function test: {'✅ PASSED' if test1_passed else '❌ FAILED'}")
    console.print(f"Tool class test: {'✅ PASSED' if test2_passed else '❌ FAILED'}")
    
    if test1_passed and test2_passed:
        console.print("\n[bold green]🎉 All tests passed! Deep Research Tool is ready for integration.[/bold green]")
    else:
        console.print("\n[bold red]⚠️  Some tests failed. Check the errors above.[/bold red]")