"""
CLI script for querying the RAG system from the command line.

This script:
1. Takes a query message as input (code error or SRE incident description)
2. Queries the RAG system for a solution
3. Prints the solution and relevant references

Supports two modes:
- Code error queries: For programming errors and exceptions
- SRE incident queries: For infrastructure and operational incidents
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
from code_rag.core.embeddings import EmbeddingGenerator
from code_rag.core.retriever import Retriever
from code_rag.db.chroma import ChromaVectorStore
from code_rag.utils.helpers import logger, setup_logger


def parse_args():
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(
        description="Query the RAG system for solutions to code errors or SRE incidents"
    )
    parser.add_argument(
        "query",
        type=str,
        nargs="?",
        help="The query message (code error or incident description) to search for (if not provided, will prompt for input)",
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
    parser.add_argument(
        "--collection",
        type=str,
        default="code_errors",
        choices=["code_errors", "sre_incidents"],
        help="Collection to query (code_errors or sre_incidents) (default: code_errors)",
    )
    
    return parser.parse_args()


def format_for_console(result: Dict, collection: str = "code_errors") -> str:
    """
    Format the query result for console output.
    
    Args:
        result: The query result
        collection: The collection type ("code_errors" or "sre_incidents")
        
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
            
            if collection == "code_errors":
                output += f"Error: {ref.get('error', '')}\n"
                output += f"Solution: {ref.get('solution', '')}\n"
            elif collection == "sre_incidents":
                output += f"Incident: {ref.get('error', '')}\n"
                output += f"Resolution: {ref.get('solution', '')}\n"
                
                # Add SRE-specific fields if available
                category = ref.get("metadata", {}).get("category")
                severity = ref.get("metadata", {}).get("severity")
                affected_services = ref.get("metadata", {}).get("affected_services")
                
                if category:
                    output += f"Category: {category}\n"
                if severity:
                    output += f"Severity: {severity}\n"
                if affected_services:
                    output += f"Affected Services: {affected_services}\n"
    
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
    
    # Initialize RAG client with the specified collection
    logger.info(f"Initializing RAG client for collection: {args.collection}...")
    rag = CodeRAG(
        chroma_path=str(settings.chroma_path),
        embedding_model=settings.embedding_model,
        llm_model=settings.llm_model,
        openai_api_key=settings.openai_api_key,
        openrouter_api_key=settings.openrouter_api_key,
        settings=settings,
    )
    
    # Update the vector store collection name
    rag.vector_store.collection_name = args.collection
    
    # Reinitialize the vector store with the new collection
    rag.vector_store = ChromaVectorStore(
        path=rag.vector_store.path,
        collection_name=args.collection,
        embedding_generator=rag.embedding_generator,
        settings=settings,
    )
    
    # Reinitialize the retriever with the new vector store
    rag.retriever = Retriever(
        vector_store=rag.vector_store,
        embedding_generator=rag.embedding_generator,
        settings=settings,
    )
    
    # Get query from arguments or prompt
    query = args.query
    if not query:
        if args.collection == "code_errors":
            query = input("Enter your code error: ")
        else:
            query = input("Enter your SRE incident description: ")
    
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
        print(format_for_console(result, args.collection))


if __name__ == "__main__":
    main()