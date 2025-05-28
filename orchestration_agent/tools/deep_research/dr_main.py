from typing import Dict, Any
from orchestration_agent.tools.deep_research.tool import (
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
from rich.progress import Progress, SpinnerColumn, TextColumn


console = Console()

WELCOME_MESSAGE = (
    "Welcome to Deep Research - your AI-powered research assistant! I can help you explore and "
    "understand any topic through detailed research and interactive discussion."
)

STARTER_QUESTIONS = [
    "Can you help me research the latest AI news?",
    "Who won the Nobel Prize in Physics this year?",
    "Where can I learn more about quantum computing?",
]


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


def display_welcome() -> None:
    """Display welcome message and starter questions."""
    welcome_panel = Panel(
        WELCOME_MESSAGE,
        title="[bold blue]Deep Research Tool[/bold blue]",
        border_style="blue",
        padding=(1, 2)
    )
    console.print("\n")
    console.print(welcome_panel)

    # Create a table for starter questions
    table = Table(
        show_header=True,
        header_style="bold cyan",
        box=box.ROUNDED,
        title="[bold]Example Questions to Get Started[/bold]"
    )
    table.add_column("№", style="dim", width=4)
    table.add_column("Question", style="green")

    for i, question in enumerate(STARTER_QUESTIONS, 1):
        table.add_row(str(i), question)

    console.print("\n")
    console.print(table)
    console.print("\n" + "─" * 80 + "\n")


def interactive_research_session() -> None:
    """
    Run an interactive research session (replaces the old chat_loop).
    This function provides a way to test the deep research functionality interactively.
    """
    console.print("\n[bold magenta]🚀 Starting Interactive Deep Research Session...[/bold magenta]")
    display_welcome()

    while True:
        user_message = console.input("\n[bold blue]Your research question:[/bold blue] ").strip()

        if user_message.lower() in ["exit", "quit", "/exit", "/quit"]:
            console.print("\n[bold]👋 Goodbye! Thanks for using Deep Research.[/bold]")
            break

        if not user_message:
            console.print("[yellow]Please enter a research question.[/yellow]")
            continue

        console.print("\n[bold yellow]🤖 Performing deep research...[/bold yellow]")
        
        try:
            # Perform the research
            result = perform_deep_research(user_message)
            
            # Display the results
            display_research_results(result)
            
        except Exception as e:
            console.print(f"\n[bold red]Error during research: {e}[/bold red]")


if __name__ == "__main__":
    interactive_research_session()
