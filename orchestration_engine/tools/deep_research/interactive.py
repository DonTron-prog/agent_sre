from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich import box
from orchestration_engine.tools.deep_research.utils import perform_deep_research, display_research_results


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
    Run an interactive research session.
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