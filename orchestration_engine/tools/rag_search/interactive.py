from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.markdown import Markdown
from rich import box
from rich.text import Text

from orchestration_engine.tools.rag_search.tool import RAGSearchTool, RAGSearchToolInputSchema, RAGSearchToolConfig

from dotenv import load_dotenv
load_dotenv()  # Load environment variables from .env file

console = Console()

WELCOME_MESSAGE = (
    "Welcome to RAG Search - your SRE knowledge assistant! I can help you find information "
    "from your indexed SRE documents and provide detailed answers with sources."
)

SRE_STARTER_QUESTIONS = [
    "How do I troubleshoot high CPU usage on a server?",
    "What are the steps for incident response?",
    "How do I configure monitoring alerts for disk space?",
    "What should I do when memory usage alerts are triggered?",
    "How do I handle database connection pool exhaustion alerts?",
    "What are the best practices for setting up alerting thresholds?",
    "How do I respond to load balancer health check failures?",
    "What steps should I take when receiving SSL certificate expiration alerts?",
    "How do I troubleshoot application response time alerts?",
    "What are the procedures for handling security breach alerts?",
]


def display_welcome() -> None:
    """Display welcome message and starter questions."""
    welcome_panel = Panel(
        WELCOME_MESSAGE,
        title="[bold blue]RAG Search - SRE Knowledge Assistant[/bold blue]",
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
        title="[bold]Example SRE Questions to Get Started[/bold]"
    )
    table.add_column("№", style="dim", width=4)
    table.add_column("Question", style="green")

    for i, question in enumerate(SRE_STARTER_QUESTIONS, 1):
        table.add_row(str(i), question)

    console.print("\n")
    console.print(table)
    console.print("\n" + "─" * 80 + "\n")


def display_rag_results(result) -> None:
    """Display RAG search results in a formatted way."""
    
    # Display the main answer
    answer_panel = Panel(
        Markdown(result.answer),
        title="[bold blue]Answer[/bold blue]",
        border_style="blue",
        padding=(1, 2)
    )
    console.print("\n")
    console.print(answer_panel)
    
    # Display reasoning
    if result.reasoning:
        reasoning_panel = Panel(
            Text(result.reasoning, style="italic"),
            title="[bold yellow]Reasoning[/bold yellow]",
            border_style="yellow",
            padding=(1, 2)
        )
        console.print("\n")
        console.print(reasoning_panel)
    
    # Display retrieved document chunks
    if result.results:
        chunks_table = Table(
            show_header=True,
            header_style="bold cyan",
            box=box.ROUNDED,
            title="[bold]Retrieved Document Chunks[/bold]"
        )
        chunks_table.add_column("№", style="dim", width=4)
        chunks_table.add_column("Source", style="green", width=25)
        chunks_table.add_column("Distance", style="yellow", width=10)
        chunks_table.add_column("Content Preview", style="white")
        
        for i, chunk in enumerate(result.results, 1):
            # Truncate content for preview
            content_preview = chunk.content[:100] + "..." if len(chunk.content) > 100 else chunk.content
            distance_str = f"{chunk.distance:.4f}"
            
            chunks_table.add_row(
                str(i), 
                chunk.source, 
                distance_str,
                content_preview
            )
        
        console.print("\n")
        console.print(chunks_table)
        
        # Show full content of chunks if user wants to see them
        console.print("\n[dim]Tip: Full chunk contents are used for generating the answer above.[/dim]")


def interactive_rag_session() -> None:
    """
    Run an interactive RAG search session.
    This function provides a way to test the RAG search functionality interactively.
    """
    console.print("\n[bold magenta]🚀 Starting Interactive RAG Search Session...[/bold magenta]")
    display_welcome()

    # Initialize the RAG search tool
    try:
        console.print("[dim]Initializing RAG Search Tool and loading documents...[/dim]")
        config = RAGSearchToolConfig()
        rag_tool = RAGSearchTool(config)
        console.print("[bold green]✅ RAG Search Tool initialized successfully![/bold green]")
    except Exception as e:
        console.print(f"[bold red]❌ Error initializing RAG Search Tool: {e}[/bold red]")
        console.print("[yellow]Please check your configuration and ensure the knowledge base directory exists.[/yellow]")
        return

    while True:
        user_query = console.input("\n[bold blue]Your SRE question:[/bold blue] ").strip()

        if user_query.lower() in ["exit", "quit", "/exit", "/quit"]:
            console.print("\n[bold]👋 Goodbye! Thanks for using RAG Search.[/bold]")
            break

        if not user_query:
            console.print("[yellow]Please enter a question.[/yellow]")
            continue

        console.print("\n[bold yellow]🔍 Searching knowledge base...[/bold yellow]")
        
        try:
            # Perform the RAG search
            input_data = RAGSearchToolInputSchema(query=user_query)
            result = rag_tool.run(input_data)
            
            # Display the results
            display_rag_results(result)
            
        except Exception as e:
            console.print(f"\n[bold red]Error during search: {e}[/bold red]")
            console.print("[yellow]Please try rephrasing your question or check the system logs.[/yellow]")


if __name__ == "__main__":
    interactive_rag_session()