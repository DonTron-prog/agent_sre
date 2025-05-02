"""
Validation script for SRE Incident RAG system.

This script:
1. Verifies document ingestion status in ChromaDB
2. Validates document properties (count, ID structure, embeddings)
3. Tests the system with diverse SRE incident queries
4. Calculates quality metrics for the RAG system

Usage:
    python validate_sre_rag.py [--log-level=INFO] [--run-ingestion]
"""

import argparse
import json
import os
import sys
import time
from pathlib import Path
from typing import Dict, List, Any, Tuple

# Add the parent directory to the path so we can import the code_rag package
sys.path.insert(0, str(Path(__file__).parent.parent))

from code_rag.config import get_settings
from code_rag.core.embeddings import EmbeddingGenerator
from code_rag.db.chroma import ChromaVectorStore
from code_rag.utils.helpers import logger, setup_logger


# Define test queries for different incident types
TEST_QUERIES = [
    {
        "type": "pod_container_issues",
        "query": "Kubernetes pod keeps crashing with OOMKilled error",
        "description": "Testing retrieval for container memory issues"
    },
    {
        "type": "networking_issues",
        "query": "Intermittent connectivity problems between services in production",
        "description": "Testing retrieval for network connectivity problems"
    },
    {
        "type": "deployment_failures",
        "query": "Failed to deploy new version due to missing ConfigMap",
        "description": "Testing retrieval for deployment configuration issues"
    },
    {
        "type": "resource_constraints",
        "query": "High CPU usage causing throttling across multiple services",
        "description": "Testing retrieval for resource constraint scenarios"
    },
    {
        "type": "database_issues",
        "query": "Database query timeout affecting critical user transactions",
        "description": "Testing retrieval for database performance issues"
    }
]

# Expected document count
EXPECTED_DOC_COUNT = 100


def parse_args():
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(
        description="Validate the SRE incidents RAG system"
    )
    parser.add_argument(
        "--log-level",
        type=str,
        default="INFO",
        choices=["DEBUG", "INFO", "WARNING", "ERROR"],
        help="Logging level (default: INFO)"
    )
    parser.add_argument(
        "--run-ingestion",
        action="store_true",
        help="Run the ingestion process before validation"
    )
    return parser.parse_args()


def setup_environment():
    """Set up the environment for validation."""
    # Get settings
    settings = get_settings()
    
    # Set a dummy API key for testing if not provided
    import os
    if not settings.openai_api_key:
        os.environ['OPENAI_API_KEY'] = 'sk-dummy-api-key-for-validation'
        logger.warning("Using dummy OpenAI API key for testing")
    
    return settings


def run_ingestion_process():
    """Run the document generation and ingestion process."""
    try:
        from subprocess import run
        
        logger.info("Running SRE document generation script...")
        gen_result = run(
            [sys.executable, str(Path(__file__).parent / "generate_sre_documents.py")],
            capture_output=True,
            text=True
        )
        if gen_result.returncode != 0:
            logger.error(f"Document generation failed: {gen_result.stderr}")
            return False
        logger.info("Document generation completed successfully")
        
        logger.info("Running SRE document ingestion script...")
        ingest_result = run(
            [sys.executable, str(Path(__file__).parent / "ingest_sre_documents.py")],
            capture_output=True,
            text=True
        )
        if ingest_result.returncode != 0:
            logger.error(f"Document ingestion failed: {ingest_result.stderr}")
            return False
        logger.info("Document ingestion completed successfully")
        
        return True
    except Exception as e:
        logger.error(f"Error running ingestion process: {e}")
        return False


def validate_document_count(vector_store) -> bool:
    """
    Verify that the expected number of documents are in ChromaDB.
    
    Args:
        vector_store: The ChromaDB vector store instance
        
    Returns:
        bool: Whether the document count matches the expected count
    """
    stats = vector_store.get_collection_stats()
    doc_count = stats["document_count"]
    
    logger.info(f"Found {doc_count} documents in the collection")
    
    if doc_count == EXPECTED_DOC_COUNT:
        logger.info(f"✓ Document count matches expected count of {EXPECTED_DOC_COUNT}")
        return True
    else:
        logger.warning(f"✗ Document count ({doc_count}) does not match expected count ({EXPECTED_DOC_COUNT})")
        return False


def validate_document_ids(vector_store) -> bool:
    """
    Verify that document IDs are unique and properly structured.
    
    Args:
        vector_store: The ChromaDB vector store instance
        
    Returns:
        bool: Whether all document IDs are valid
    """
    # Get all document IDs from the collection
    ids = vector_store.collection.get(include=["documents"])["ids"]
    
    # Check for uniqueness
    unique_ids = set(ids)
    if len(unique_ids) != len(ids):
        logger.warning(f"✗ Document IDs are not unique: {len(unique_ids)} unique IDs out of {len(ids)} total")
        return False
    
    # Check ID format/structure
    # For this example, we'll just check that all IDs are non-empty strings
    invalid_ids = [_id for _id in ids if not isinstance(_id, str) or not _id]
    
    if invalid_ids:
        logger.warning(f"✗ Found {len(invalid_ids)} invalid IDs")
        return False
    
    logger.info(f"✓ All {len(ids)} document IDs are unique and valid")
    return True


def validate_embeddings(vector_store, embedding_generator) -> bool:
    """
    Validate that embeddings were created properly by performing a simple similarity search.
    
    Args:
        vector_store: The ChromaDB vector store instance
        embedding_generator: The embedding generator instance
        
    Returns:
        bool: Whether embeddings appear to be working correctly
    """
    # Generate a simple test query
    test_query = "test query for validation"
    
    try:
        # Try to do a similarity search
        results = vector_store.query(
            query_text=test_query,
            n_results=1
        )
        
        # Check that we got results and they have the expected structure
        if (results 
            and "documents" in results 
            and "distances" in results
            and len(results["documents"]) > 0 
            and len(results["distances"]) > 0):
            logger.info(f"✓ Embedding validation successful: similarity search returned results")
            return True
        else:
            logger.warning(f"✗ Embedding validation failed: similarity search returned incomplete results")
            return False
    except Exception as e:
        logger.error(f"✗ Embedding validation failed with error: {e}")
        return False


def run_test_queries(vector_store) -> List[Dict[str, Any]]:
    """
    Run test queries and collect results.
    
    Args:
        vector_store: The ChromaDB vector store instance
        
    Returns:
        List[Dict[str, Any]]: List of query results with performance metrics
    """
    all_results = []
    
    for test_query in TEST_QUERIES:
        query_text = test_query["query"]
        query_type = test_query["type"]
        
        logger.info(f"\n=== Testing {query_type} query ===")
        logger.info(f"Query: \"{query_text}\"")
        
        # Measure query time
        start_time = time.time()
        results = vector_store.query(query_text=query_text, n_results=3)
        query_time = time.time() - start_time
        
        # Process results
        query_results = []
        
        for i, (doc, metadata, distance) in enumerate(zip(
            results['documents'][0], 
            results['metadatas'][0], 
            results['distances'][0]
        )):
            query_results.append({
                "rank": i + 1,
                "document": doc,
                "metadata": metadata,
                "distance": distance,
                "similarity_score": 1 - distance,  # Convert distance to similarity
            })
            
            # Format and display the result
            logger.info(f"\nResult {i+1} (Similarity: {1-distance:.4f})")
            logger.info(f"  Incident: {doc}")
            logger.info(f"  Solution: {metadata.get('solution', 'N/A')}")
            
            # Display additional metadata if available
            if 'category' in metadata:
                logger.info(f"  Category: {metadata['category']}")
            if 'severity' in metadata:
                logger.info(f"  Severity: {metadata['severity']}")
            if 'affected_services' in metadata:
                logger.info(f"  Affected Services: {metadata['affected_services']}")
        
        # Add to overall results
        all_results.append({
            "query_type": query_type,
            "query_text": query_text,
            "query_time_seconds": query_time,
            "results": query_results,
        })
        
        logger.info(f"Query completed in {query_time:.4f} seconds")
    
    return all_results


def calculate_quality_metrics(query_results: List[Dict[str, Any]]) -> Dict[str, float]:
    """
    Calculate quality metrics based on query results.
    
    Args:
        query_results: List of query results
        
    Returns:
        Dict[str, float]: Dictionary of calculated metrics
    """
    # Initialize metrics
    total_queries = len(query_results)
    total_results = sum(len(r["results"]) for r in query_results)
    total_similarity = 0.0
    total_query_time = 0.0
    
    # Calculate metrics
    for query in query_results:
        total_query_time += query["query_time_seconds"]
        
        for result in query["results"]:
            total_similarity += result["similarity_score"]
    
    # Average metrics
    avg_similarity = total_similarity / total_results if total_results > 0 else 0
    avg_query_time = total_query_time / total_queries if total_queries > 0 else 0
    
    # Return metrics
    return {
        "average_similarity_score": avg_similarity,
        "average_query_time_seconds": avg_query_time,
        "total_queries": total_queries,
        "total_results": total_results,
    }


def display_summary(validation_results: Dict[str, bool], quality_metrics: Dict[str, float]):
    """
    Display a summary of validation results and quality metrics.
    
    Args:
        validation_results: Dictionary of validation results
        quality_metrics: Dictionary of quality metrics
    """
    logger.info("\n" + "="*50)
    logger.info("SRE RAG System Validation Summary")
    logger.info("="*50)
    
    # Display validation status
    logger.info("\nValidation Results:")
    for test, status in validation_results.items():
        status_str = "✓ PASS" if status else "✗ FAIL"
        logger.info(f"  {test}: {status_str}")
    
    # Calculate overall validation status
    overall_status = all(validation_results.values())
    status_str = "✓ PASSED" if overall_status else "✗ FAILED"
    logger.info(f"\nOverall Validation: {status_str}")
    
    # Display quality metrics
    logger.info("\nQuality Metrics:")
    logger.info(f"  Average Similarity Score: {quality_metrics['average_similarity_score']:.4f}")
    logger.info(f"  Average Query Time: {quality_metrics['average_query_time_seconds']:.4f} seconds")
    logger.info(f"  Total Queries Executed: {quality_metrics['total_queries']}")
    logger.info(f"  Total Results Retrieved: {quality_metrics['total_results']}")
    
    # System recommendation based on metrics
    sim_threshold = 0.7  # Set a threshold for good similarity
    
    if quality_metrics['average_similarity_score'] >= sim_threshold and overall_status:
        logger.info("\nSystem Status: READY FOR USE")
        logger.info("The RAG system is properly configured and returning relevant results.")
    elif quality_metrics['average_similarity_score'] >= sim_threshold and not overall_status:
        logger.info("\nSystem Status: NEEDS ATTENTION")
        logger.info("The RAG system is returning relevant results but has validation issues to address.")
    elif quality_metrics['average_similarity_score'] < sim_threshold and overall_status:
        logger.info("\nSystem Status: NEEDS TUNING")
        logger.info("The RAG system passed validation but has lower than expected relevance scores.")
    else:
        logger.info("\nSystem Status: REQUIRES FIXES")
        logger.info("The RAG system has validation issues and is not returning sufficiently relevant results.")
    
    logger.info("="*50)


def main():
    """Main entry point for the validation script."""
    # Parse arguments
    args = parse_args()
    
    # Configure logging
    logger = setup_logger(level=args.log_level)
    
    # Set up environment
    settings = setup_environment()
    
    logger.info("Starting SRE RAG system validation")
    
    # Run ingestion if requested
    if args.run_ingestion:
        logger.info("Running document generation and ingestion process...")
        if not run_ingestion_process():
            logger.error("Ingestion process failed, continuing with validation of existing data")
    
    # Initialize components
    embedding_generator = EmbeddingGenerator(
        api_key=os.environ.get('OPENAI_API_KEY', settings.openai_api_key),
        model=settings.embedding_model,
        settings=settings,
    )
    
    vector_store = ChromaVectorStore(
        path=settings.chroma_path,
        collection_name="sre_incidents",
        embedding_generator=embedding_generator,
        settings=settings,
    )
    
    # Run validation tests
    validation_results = {
        "Document Count": validate_document_count(vector_store),
        "Document IDs": validate_document_ids(vector_store),
        "Embeddings": validate_embeddings(vector_store, embedding_generator)
    }
    
    # Run test queries
    logger.info("\nRunning test queries...")
    query_results = run_test_queries(vector_store)
    
    # Calculate quality metrics
    logger.info("\nCalculating quality metrics...")
    quality_metrics = calculate_quality_metrics(query_results)
    
    # Display summary
    display_summary(validation_results, quality_metrics)
    

if __name__ == "__main__":
    main()