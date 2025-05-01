"""
Data processing for the CodeInsight dataset.
"""

import json
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Union

import pandas as pd
from datasets import Dataset

from code_rag.config import Settings, get_settings
from code_rag.data.loader import DataLoader
from code_rag.utils.helpers import logger


class DataProcessor:
    """
    Processes the CodeInsight dataset for use with the RAG system.
    
    Features:
    - Extracts error messages and solutions
    - Normalizes and cleans the data
    - Prepares data for embedding generation
    - Exports processed data to disk
    """
    
    def __init__(
        self,
        data_loader: Optional[DataLoader] = None,
        output_dir: Optional[Union[str, Path]] = None,
        settings: Optional[Settings] = None,
    ):
        """
        Initialize the data processor.
        
        Args:
            data_loader: DataLoader instance (created if None)
            output_dir: Directory to save processed data (defaults to settings.processed_data_dir)
            settings: Settings instance (optional, will use global if None)
        """
        self.settings = settings or get_settings()
        self.data_loader = data_loader or DataLoader(settings=self.settings)
        self.output_dir = Path(output_dir) if output_dir else self.settings.processed_data_dir
        
        self._ensure_output_dir()
    
    def _ensure_output_dir(self) -> None:
        """Ensure the output directory exists."""
        self.output_dir.mkdir(parents=True, exist_ok=True)
    
    def extract_error_solution_pairs(
        self,
        dataset: Optional[Dataset] = None,
        error_key: str = "code",      # Default key for error/code in the dataset
        solution_key: str = "nl",       # Default key for solution/natural language in the dataset
    ) -> List[Dict]:
        """
        Extract error-solution pairs from the dataset.
        Outputs dictionaries with keys 'error' and 'solution' regardless of input keys.

        Args:
            dataset: Dataset to process (loads from data_loader if None)
            error_key: Key for error/code snippet in the dataset
            solution_key: Key for solution/natural language in the dataset

        Returns:
            List[Dict]: List of dictionaries with 'error' and 'solution' keys
        """
        if dataset is None:
            dataset = self.data_loader.get_train_data()

        # Check if the required columns exist
        if error_key not in dataset.column_names or solution_key not in dataset.column_names:
            available_columns = ", ".join(dataset.column_names)
            raise ValueError(
                f"Required columns '{error_key}' and/or '{solution_key}' not found. "
                f"Available columns are: {available_columns}"
            )

        # Extract error-solution pairs
        pairs = []
        for item in dataset:
            # Use the specified keys to get data from the dataset item
            error_content = item.get(error_key)
            solution_content = item.get(solution_key)

            # Skip rows with missing data
            if not error_content or not solution_content:
                continue

            # Add any additional metadata from the dataset, excluding the main content keys
            metadata = {k: v for k, v in item.items() if k not in [error_key, solution_key]}

            # Store using consistent 'error' and 'solution' keys for downstream use
            pairs.append({
                "error": error_content,
                "solution": solution_content,
                "metadata": metadata
            })

        logger.info(f"Extracted {len(pairs)} error-solution pairs from the dataset using keys '{error_key}' and '{solution_key}'")
        return pairs
    
    def clean_and_normalize(self, pairs: List[Dict]) -> List[Dict]:
        """
        Clean and normalize the error-solution pairs.
        
        Args:
            pairs: List of error-solution pair dictionaries
            
        Returns:
            List[Dict]: Cleaned and normalized error-solution pairs
        """
        cleaned_pairs = []
        
        for pair in pairs:
            # Basic cleaning
            error = pair["error"].strip()
            solution = pair["solution"].strip()
            
            # Skip empty strings
            if not error or not solution:
                continue
            
            # Add the cleaned pair
            cleaned_pairs.append({
                "error": error,
                "solution": solution,
                "metadata": pair.get("metadata", {})
            })
        
        logger.info(f"Cleaned and normalized {len(cleaned_pairs)} error-solution pairs")
        return cleaned_pairs
    
    def prepare_for_embedding(
        self,
        pairs: List[Dict],
    ) -> Tuple[List[str], List[Dict], List[str]]:
        """
        Prepare error-solution pairs for embedding.
        
        Args:
            pairs: List of error-solution pair dictionaries
            
        Returns:
            Tuple[List[str], List[Dict], List[str]]: 
                - List of documents to embed (error messages)
                - List of metadata (containing solutions and other metadata)
                - List of document IDs
        """
        documents = []
        metadatas = []
        ids = []
        
        for i, pair in enumerate(pairs):
            # The document to embed is the error message
            documents.append(pair["error"])
            
            # Metadata includes the solution and any additional metadata
            metadata = {
                "solution": pair["solution"],
                **pair.get("metadata", {})
            }
            metadatas.append(metadata)
            
            # Generate a document ID
            doc_id = f"error_{i}"
            ids.append(doc_id)
        
        logger.info(f"Prepared {len(documents)} documents for embedding")
        return documents, metadatas, ids
    
    def save_processed_data(
        self,
        pairs: List[Dict],
        filename: str = "processed_data.json",
    ) -> Path:
        """
        Save processed data to disk.
        
        Args:
            pairs: List of error-solution pair dictionaries
            filename: Name of the file to save to
            
        Returns:
            Path: Path to the saved file
        """
        output_path = self.output_dir / filename
        
        with open(output_path, 'w') as f:
            json.dump(pairs, f, indent=2)
        
        logger.info(f"Saved {len(pairs)} processed data items to {output_path}")
        return output_path
    
    def load_processed_data(
        self,
        filename: str = "processed_data.json",
    ) -> List[Dict]:
        """
        Load processed data from disk.
        
        Args:
            filename: Name of the file to load from
            
        Returns:
            List[Dict]: Loaded error-solution pairs
        """
        input_path = self.output_dir / filename
        
        with open(input_path, 'r') as f:
            pairs = json.load(f)
        
        logger.info(f"Loaded {len(pairs)} processed data items from {input_path}")
        return pairs
    
    def process_and_save(
        self,
        save_filename: str = "processed_data.json",
    ) -> Path:
        """
        Process the dataset and save to disk.
        
        Args:
            save_filename: Name of the file to save to
            
        Returns:
            Path: Path to the saved file
        """
        # Load raw data
        dataset = self.data_loader.get_train_data()
        
        # Extract error-solution pairs
        pairs = self.extract_error_solution_pairs(dataset)
        
        # Clean and normalize
        cleaned_pairs = self.clean_and_normalize(pairs)
        
        # Save processed data
        output_path = self.save_processed_data(cleaned_pairs, filename=save_filename)
        
        return output_path