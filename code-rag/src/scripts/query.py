"""
CLI script for querying the RAG system from the command line.

This script:
1. Takes a code error message as input
2. Queries the RAG system for a solution
3. Prints the solution and relevant references
"""

import argparse
import json
import os
import sys
from pathlib import Path
from typing import Dict, Optional

# Add the parent directory to the path so we can import the code_rag package
sys.path.insert(0, str(Path(__file__).parent.parent))

from code_rag import CodeRAG
from code_rag.config import get_settings
from code_rag.utils.helpers import logger, setup_logger


def parse_args():
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(
        description="Query the RAG system for solutions to code errors"
    )
    parser.add_argument(
        "query",
        type=str,
        nargs="?",
        help="The error message to query (if not provided, will prompt for input)",
    )
    parser.add_argument(
        "--num-results",
        type=int,
        default=3,
        help="Number of results to retrieve (default: 3)",
    )
    parser.add_argument(
        "--temperature",
        type=float,
        default=0.7,
        help="Temperature for LLM generation (default: 0.7)",
    )
    parser.add_argument(
        "--max-tokens",
        type=int,
        default=1024,
        help="Maximum tokens for LLM response (default: 1024)",
    )
    parser.add_argument(
        "--chroma-path",
        type=str,
        default=None,
        help="Path to the Chroma database (default: settings.chroma_path)",
    )
    parser.add_argument(
        "--log-level",
        type=str,
        default="INFO",
        choices=["DEBUG", "INFO", "WARNING", "ERROR"],
        help="Logging level (default: INFO)",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Output results in JSON format",
    )
    
    return parser.parse_args()


def format_for_console(result: Dict) -> str:
    """
    Format the query result for console output.
    
    Args:
        result: The query result
        
    Returns:
        str: Formatted output
    """
    solution = result.get("solution", "No solution generated")
    references = result.get("references", [])
    metadata = result.get("metadata", {})
    
    # Format the solution
    output = f"\n{'='*80}\n"
    output += f"SOLUTION:\n{'-'*80}\n{solution}\n"
    
    # Format references
    if references:
        output += f"\n{'='*80}\n"
        output += f"REFERENCES ({len(references)}):\n"
        
        for i, ref in enumerate(references, 1):
            output += f"{'-'*80}\n"
            output += f"Reference {i} (Score: {ref.get('similarity_score', 0.0):.2f}):\n"
            output += f"Error: {ref.get('error', '')}\n"
            output += f"Solution: {ref.get('solution', '')}\n"
    
    # Format metadata
    if metadata:
        output += f"\n{'='*80}\n"
        output += f"METADATA:\n{'-'*80}\n"
        output += f"Model: {metadata.get('model_used', 'unknown')}\n"
        output += f"Tokens: {metadata.get('tokens_used', 0)}\n"
        output += f"Processing time: {metadata.get('processing_time_ms', 0)} ms\n"
    
    output += f"{'='*80}\n"
    return output


def main():
    """Main entry point for the script."""
    args = parse_args()
    
    # Configure logging
    log_level = getattr(__import__("logging"), args.log_level)
    logger = setup_logger(level=log_level)
    
    # Get settings
    settings = get_settings()
    
    # Override with command-line arguments
    if args.chroma_path:
        settings.chroma_path = args.chroma_path
    
    # Initialize RAG client
    logger.info("Initializing RAG client...")
    rag = CodeRAG(
        chroma_path=str(settings.chroma_path),
        embedding_model=settings.embedding_model,
        llm_model=settings.llm_model,
        openai_api_key=settings.openai_api_key,
        openrouter_api_key=settings.openrouter_api_key,
        settings=settings,
    )
    
    # Get query from arguments or prompt
    query = args.query
    if not query:
        query = input("Enter your code error: ")
    
    if not query:
        logger.error("No query provided")
        sys.exit(1)
    
    # Query the RAG system
    logger.info(f"Querying RAG system: {query[:50]}{'...' if len(query) > 50 else ''}")
    result = rag.query(
        error_message=query,
        num_results=args.num_results,
        temperature=args.temperature,
        max_tokens=args.max_tokens,
    )
    
    # Output the result
    if args.json:
        # Output as JSON
        print(json.dumps(result, indent=2))
    else:
        # Output formatted for console
        print(format_for_console(result))


if __name__ == "__main__":
    main()