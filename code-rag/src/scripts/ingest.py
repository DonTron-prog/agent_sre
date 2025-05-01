"""
Data ingestion script for loading the CodeInsight dataset into Chroma.

This script:
1. Loads the CodeInsight dataset from HuggingFace
2. Processes the data into a format suitable for RAG
3. Generates embeddings for the error messages
4. Loads the embeddings and data into Chroma
"""

import argparse
import os
import sys
import time
from pathlib import Path
from typing import Optional

# Add the parent directory to the path so we can import the code_rag package
sys.path.insert(0, str(Path(__file__).parent.parent))

from code_rag.config import get_settings
from code_rag.core.embeddings import EmbeddingGenerator
from code_rag.data.loader import DataLoader
from code_rag.data.processor import DataProcessor
from code_rag.db.chroma import ChromaVectorStore
from code_rag.utils.helpers import logger, setup_logger


def parse_args():
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(
        description="Ingest the CodeInsight dataset into the Chroma vector database"
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
        "--processed-data",
        type=str,
        default=None,
        help="Path to previously processed data (skips dataset loading and processing)",
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Force reprocessing and reindexing even if previous data exists",
    )
    
    return parser.parse_args()


def main():
    """Main entry point for the script."""
    args = parse_args()
    
    # Configure logging
    log_level = getattr(logging, args.log_level)
    logger = setup_logger(level=log_level)
    
    # Get settings
    settings = get_settings()
    
    # Override with command-line arguments
    if args.chroma_path:
        settings.chroma_path = args.chroma_path
    
    logger.info("Starting data ingestion process")
    start_time = time.time()
    
    # Create directories if they don't exist
    settings.raw_data_dir.mkdir(parents=True, exist_ok=True)
    settings.processed_data_dir.mkdir(parents=True, exist_ok=True)
    Path(settings.chroma_path).parent.mkdir(parents=True, exist_ok=True)
    
    # Initialize components
    data_loader = DataLoader(settings=settings)
    data_processor = DataProcessor(data_loader=data_loader, settings=settings)
    embedding_generator = EmbeddingGenerator(
        api_key=settings.openai_api_key,
        model=settings.embedding_model,
        settings=settings,
    )
    vector_store = ChromaVectorStore(
        path=settings.chroma_path,
        embedding_generator=embedding_generator,
        settings=settings,
    )
    
    # Step 1: Load and process data
    processed_data_path = Path(args.processed_data) if args.processed_data else settings.processed_data_dir / "processed_data.json"
    
    if not processed_data_path.exists() or args.force:
        logger.info("Processing CodeInsight dataset")
        
        # Load the dataset
        dataset = data_loader.get_train_data()
        
        # Extract error-solution pairs
        pairs = data_processor.extract_error_solution_pairs(dataset)
        
        # Clean and normalize
        cleaned_pairs = data_processor.clean_and_normalize(pairs)
        
        # Apply limit if specified
        if args.limit is not None:
            cleaned_pairs = cleaned_pairs[:args.limit]
            logger.info(f"Limited to {len(cleaned_pairs)} documents")
        
        # Save processed data
        data_processor.save_processed_data(cleaned_pairs)
        
        # Prepare for embedding
        documents, metadatas, ids = data_processor.prepare_for_embedding(cleaned_pairs)
    else:
        logger.info(f"Loading previously processed data from {processed_data_path}")
        
        # Load previously processed data
        pairs = data_processor.load_processed_data()
        
        # Apply limit if specified
        if args.limit is not None:
            pairs = pairs[:args.limit]
            logger.info(f"Limited to {len(pairs)} documents")
        
        # Prepare for embedding
        documents, metadatas, ids = data_processor.prepare_for_embedding(pairs)
    
    # Step 2: Generate embeddings and load into Chroma
    logger.info(f"Generating embeddings and loading into Chroma for {len(documents)} documents")
    
    # Generate embeddings and add to vector store
    vector_store.add_documents(
        documents=documents,
        metadatas=metadatas,
        ids=ids,
        batch_size=args.batch_size,
    )
    
    # Log completion
    end_time = time.time()
    duration = end_time - start_time
    logger.info(f"Data ingestion completed in {duration:.2f} seconds")
    
    # Log stats
    stats = vector_store.get_collection_stats()
    logger.info(f"Collection stats: {stats}")


if __name__ == "__main__":
    import logging
    main()