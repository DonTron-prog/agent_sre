"""
Test script to query the SRE incidents from ChromaDB
"""

import sys
from pathlib import Path

# Add the parent directory to the path so we can import the code_rag package
sys.path.insert(0, str(Path(__file__).parent.parent))

from code_rag.config import get_settings
from code_rag.core.embeddings import EmbeddingGenerator
from code_rag.db.chroma import ChromaVectorStore
from code_rag.utils.helpers import logger, setup_logger


def main():
    """Main entry point for the query script"""
    # Configure logging
    logger = setup_logger()
    
    # Get settings
    settings = get_settings()
    
    # Set a dummy API key for testing if not provided
    import os
    if not settings.openai_api_key:
        os.environ['OPENAI_API_KEY'] = 'sk-dummy-api-key-for-testing'
        logger.warning("Using dummy OpenAI API key for testing")
    
    # Initialize components
    embedding_generator = EmbeddingGenerator(
        api_key=os.environ.get('OPENAI_API_KEY', settings.openai_api_key),
        model=settings.embedding_model,
        settings=settings,
    )
    
    # Initialize ChromaDB client with the SRE incidents collection
    vector_store = ChromaVectorStore(
        path=settings.chroma_path,
        collection_name="sre_incidents",
        embedding_generator=embedding_generator,
        settings=settings,
    )
    
    # Get collection stats
    stats = vector_store.get_collection_stats()
    print(f"\nCollection stats: {stats}")
    print(f"Total documents: {stats['document_count']}\n")
    
    # Test queries
    test_queries = [
        "Database connection issues",
        "Container crashing with OOM error",
        "Kubernetes pods not starting",
        "Network latency problems",
        "API rate limiting errors"
    ]
    
    for query in test_queries:
        print(f"\n===== Query: '{query}' =====\n")
        
        # Perform the query
        results = vector_store.query(query_text=query, n_results=2)
        
        # Display results
        for i, (doc, metadata, distance) in enumerate(zip(
            results['documents'][0], 
            results['metadatas'][0], 
            results['distances'][0]
        )):
            print(f"Result {i+1} (Distance: {distance:.4f}):")
            print(f"  Error: {doc}")
            print(f"  Solution: {metadata.get('solution', 'N/A')}")
            print(f"  Category: {metadata.get('category', 'N/A')}")
            print(f"  Document Type: {metadata.get('document_type', 'N/A')}")
            print(f"  Affected Services: {metadata.get('affected_services', 'N/A')}")
            print(f"  Severity: {metadata.get('severity', 'N/A')}")
            print()


if __name__ == "__main__":
    main()