from typing import Dict, Any
from .tool import (
    DeepResearchTool,
    DeepResearchToolConfig,
    DeepResearchToolInputSchema,
    DeepResearchToolOutputSchema
)

from rich.console import Console
from rich.panel import Panel
from rich.markdown import Markdown
from rich.table import Table
from rich import box


console = Console()


def perform_deep_research(research_query: str, searxng_base_url: str = "http://localhost:8080/", max_results: int = 3) -> DeepResearchToolOutputSchema:
    """
    Perform deep research on a given query without looping.
    
    Args:
        research_query: The research question or topic to investigate
        searxng_base_url: Base URL for SearxNG search service
        max_results: Maximum number of search results to process
        
    Returns:
        DeepResearchToolOutputSchema: Comprehensive research results
    """
    # Initialize the deep research tool
    config = DeepResearchToolConfig(
        searxng_base_url=searxng_base_url,
        max_search_results=max_results
    )
    deep_research_tool = DeepResearchTool(config)
    
    # Create input schema
    input_data = DeepResearchToolInputSchema(
        research_query=research_query,
        max_search_results=max_results
    )
    
    # Perform the research
    return deep_research_tool.run(input_data)


def display_research_results(result: DeepResearchToolOutputSchema) -> None:
    """Display research results in a formatted way."""
    
    # Display the main answer
    answer_panel = Panel(
        Markdown(result.answer),
        title="[bold blue]Research Results[/bold blue]",
        border_style="blue",
        padding=(1, 2)
    )
    console.print("\n")
    console.print(answer_panel)
    
    # Display sources if available
    if result.sources:
        sources_table = Table(
            show_header=True,
            header_style="bold cyan",
            box=box.ROUNDED,
            title="[bold]Sources Used[/bold]"
        )
        sources_table.add_column("№", style="dim", width=4)
        sources_table.add_column("URL", style="green")
        
        for i, source in enumerate(result.sources, 1):
            sources_table.add_row(str(i), source)
        
        console.print("\n")
        console.print(sources_table)
    
    # Display search queries used
    if result.search_queries_used:
        queries_table = Table(
            show_header=True,
            header_style="bold cyan",
            box=box.ROUNDED,
            title="[bold]Search Queries Used[/bold]"
        )
        queries_table.add_column("№", style="dim", width=4)
        queries_table.add_column("Query", style="yellow")
        
        for i, query in enumerate(result.search_queries_used, 1):
            queries_table.add_row(str(i), query)
        
        console.print("\n")
        console.print(queries_table)
    
    # Display follow-up questions if available
    if result.follow_up_questions:
        questions_table = Table(
            show_header=True,
            header_style="bold cyan",
            box=box.ROUNDED,
            title="[bold]Follow-up Questions[/bold]"
        )
        questions_table.add_column("№", style="dim", width=4)
        questions_table.add_column("Question", style="green")
        
        for i, question in enumerate(result.follow_up_questions, 1):
            questions_table.add_row(str(i), question)
        
        console.print("\n")
        console.print(questions_table)