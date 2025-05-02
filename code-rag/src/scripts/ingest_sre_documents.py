"""
Data ingestion script for loading the synthetic SRE incident documents into Chroma.

This script:
1. Loads the synthetic SRE incident documents from the JSON file
2. Processes the data into a format suitable for RAG
3. Generates embeddings for the incident descriptions
4. Loads the embeddings and data into Chroma
"""

import argparse
import json
import os
import sys
import time
from pathlib import Path
from typing import Dict, List, Optional

# Add the parent directory to the path so we can import the code_rag package
sys.path.insert(0, str(Path(__file__).parent.parent))

from code_rag.config import get_settings
from code_rag.core.embeddings import EmbeddingGenerator
from code_rag.data.processor import DataProcessor
from code_rag.db.chroma import ChromaVectorStore
from code_rag.utils.helpers import logger, setup_logger


def parse_args():
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(
        description="Ingest synthetic SRE incident documents into the Chroma vector database"
    )
    parser.add_argument(
        "--input-file",
        type=str,
        default=None,
        help="Path to the input JSON file (default: <raw_data_dir>/sre_incidents.json)",
    )
    parser.add_argument(
        "--batch-size",
        type=int,
        default=16,
        help="Batch size for processing and embedding (default: 16)",
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=None,
        help="Limit the number of documents to process (default: all)",
    )
    parser.add_argument(
        "--log-level",
        type=str,
        default="INFO",
        choices=["DEBUG", "INFO", "WARNING", "ERROR"],
        help="Logging level (default: INFO)",
    )
    parser.add_argument(
        "--chroma-path",
        type=str,
        default=None,
        help="Path to the Chroma database (default: settings.chroma_path)",
    )
    parser.add_argument(
        "--collection-name",
        type=str,
        default="sre_incidents",
        help="Name of the Chroma collection to use (default: sre_incidents)",
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Force reprocessing and reindexing even if previous data exists",
    )
    
    return parser.parse_args()


def load_sre_documents(file_path: Path) -> List[Dict]:
    """
    Load SRE incident documents from a JSON file.
    
    Args:
        file_path: Path to the JSON file
        
    Returns:
        List[Dict]: List of SRE incident documents
    """
    logger.info(f"Loading SRE incident documents from {file_path}")
    
    with open(file_path, 'r') as f:
        documents = json.load(f)
    
    logger.info(f"Loaded {len(documents)} SRE incident documents")
    return documents


def process_sre_documents(documents: List[Dict]) -> List[Dict]:
    """
    Process SRE incident documents into error-solution pairs.
    
    Args:
        documents: List of SRE incident documents
        
    Returns:
        List[Dict]: List of processed error-solution pairs
    """
    logger.info(f"Processing {len(documents)} SRE incident documents")
    
    processed_documents = []
    
    for doc in documents:
        # Each document should have 'error', 'solution', and 'metadata' fields
        if not all(key in doc for key in ['error', 'solution']):
            logger.warning(f"Skipping document missing required fields: {doc}")
            continue
        
        # Ensure metadata exists, create empty dict if missing
        metadata = doc.get('metadata', {})
        
        # Process metadata to ensure all values are simple types (str, int, float, bool)
        processed_metadata = {}
        for key, value in metadata.items():
            if isinstance(value, (str, int, float, bool)):
                processed_metadata[key] = value
            elif isinstance(value, list):
                # Convert lists to comma-separated strings
                processed_metadata[key] = ", ".join(map(str, value))
            else:
                # Convert other types to strings
                processed_metadata[key] = str(value)
        
        # Create a processed document with the required structure
        processed_doc = {
            "error": doc["error"].strip(),
            "solution": doc["solution"].strip(),
            "metadata": processed_metadata
        }
        
        processed_documents.append(processed_doc)
    
    logger.info(f"Processed {len(processed_documents)} documents")
    return processed_documents


def main():
    """Main entry point for the script."""
    # Parse arguments
    args = parse_args()
    
    # Configure logging
    import logging
    log_level = getattr(logging, args.log_level)
    logger = setup_logger(level=log_level)
    
    # Get settings
    settings = get_settings()
    
    # Override with command-line arguments
    if args.chroma_path:
        settings.chroma_path = args.chroma_path
    
    logger.info("Starting SRE document ingestion process")
    start_time = time.time()
    
    # Create directories if they don't exist
    settings.raw_data_dir.mkdir(parents=True, exist_ok=True)
    settings.processed_data_dir.mkdir(parents=True, exist_ok=True)
    Path(settings.chroma_path).parent.mkdir(parents=True, exist_ok=True)
    
    # Determine input file path
    if args.input_file:
        input_file_path = Path(args.input_file)
    else:
        input_file_path = Path(os.path.abspath(os.path.join(os.path.dirname(__file__), "../../data/raw/sre_incidents.json")))
    
    if not input_file_path.exists():
        logger.error(f"Input file not found: {input_file_path}")
        sys.exit(1)
    
    # Determine output file for processed data
    processed_data_path = Path(os.path.abspath(os.path.join(os.path.dirname(__file__), "../../data/processed/processed_sre_documents.json")))
    
    # Initialize components
    data_processor = DataProcessor(settings=settings)
    
    # Set a dummy API key for testing if not provided
    if not settings.openai_api_key:
        os.environ['OPENAI_API_KEY'] = 'sk-dummy-api-key-for-testing'
        logger.warning("Using dummy OpenAI API key for testing")
    
    embedding_generator = EmbeddingGenerator(
        api_key=os.environ.get('OPENAI_API_KEY', settings.openai_api_key),
        model=settings.embedding_model,
        settings=settings,
    )
    vector_store = ChromaVectorStore(
        path=settings.chroma_path,
        collection_name=args.collection_name,
        embedding_generator=embedding_generator,
        settings=settings,
    )
    
    # Step 1: Load and process data
    if not processed_data_path.exists() or args.force:
        logger.info("Loading and processing SRE incident documents")
        
        # Load documents
        documents = load_sre_documents(input_file_path)
        
        # Process documents
        processed_documents = process_sre_documents(documents)
        
        # Apply limit if specified
        if args.limit is not None:
            processed_documents = processed_documents[:args.limit]
            logger.info(f"Limited to {len(processed_documents)} documents")
        
        # Save processed data
        with open(processed_data_path, 'w') as f:
            json.dump(processed_documents, f, indent=2)
        logger.info(f"Saved processed documents to {processed_data_path}")
        
        # Prepare for embedding
        documents_to_embed, metadatas, ids = data_processor.prepare_for_embedding(processed_documents)
    else:
        logger.info(f"Loading previously processed data from {processed_data_path}")
        
        # Load previously processed data
        with open(processed_data_path, 'r') as f:
            processed_documents = json.load(f)
        
        # Apply limit if specified
        if args.limit is not None:
            processed_documents = processed_documents[:args.limit]
            logger.info(f"Limited to {len(processed_documents)} documents")
        
        # Prepare for embedding
        documents_to_embed, metadatas, ids = data_processor.prepare_for_embedding(processed_documents)
    
    # Step 2: Generate embeddings and load into Chroma
    logger.info(f"Generating embeddings and loading into Chroma for {len(documents_to_embed)} documents")
    
    # Generate embeddings and add to vector store
    vector_store.add_documents(
        documents=documents_to_embed,
        metadatas=metadatas,
        ids=ids,
        batch_size=args.batch_size,
    )
    
    # Log completion
    end_time = time.time()
    duration = end_time - start_time
    logger.info(f"SRE document ingestion completed in {duration:.2f} seconds")
    
    # Log stats
    stats = vector_store.get_collection_stats()
    logger.info(f"Collection stats: {stats}")


if __name__ == "__main__":
    main()