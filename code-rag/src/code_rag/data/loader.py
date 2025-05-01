"""
Data loading functionality for CodeInsight dataset from Hugging Face.
"""

from pathlib import Path
from typing import Dict, List, Optional, Union

from datasets import load_dataset, Dataset, DatasetDict

from code_rag.config import Settings, get_settings
from code_rag.utils.helpers import logger


class DataLoader:
    """
    Handles loading and management of the CodeInsight dataset.
    
    Features:
    - Loads the CodeInsight dataset from Hugging Face
    - Caches dataset locally for performance
    - Provides access to various dataset splits
    """
    
    def __init__(
        self,
        dataset_name: str = "Nbeau/CodeInsight",
        cache_dir: Optional[Union[str, Path]] = None,
        settings: Optional[Settings] = None,
    ):
        """
        Initialize the data loader.
        
        Args:
            dataset_name: Name of the dataset on Hugging Face
            cache_dir: Directory to cache the dataset (defaults to settings.raw_data_dir)
            settings: Settings instance (optional, will use global if None)
        """
        self.settings = settings or get_settings()
        self.dataset_name = dataset_name
        self.cache_dir = Path(cache_dir) if cache_dir else self.settings.raw_data_dir
        
        self.dataset = None
        self._ensure_cache_dir()
    
    def _ensure_cache_dir(self) -> None:
        """Ensure the cache directory exists."""
        self.cache_dir.mkdir(parents=True, exist_ok=True)
    
    def load_dataset(self, force_reload: bool = False) -> Union[Dataset, DatasetDict]:
        """
        Load the CodeInsight dataset from Hugging Face.
        
        Args:
            force_reload: Whether to force a reload of the dataset
            
        Returns:
            Union[Dataset, DatasetDict]: The loaded dataset
        """
        if self.dataset is None or force_reload:
            logger.info(f"Loading dataset '{self.dataset_name}'...")
            try:
                self.dataset = load_dataset(
                    self.dataset_name,
                    cache_dir=str(self.cache_dir),
                )
                logger.info(f"Dataset '{self.dataset_name}' loaded successfully.")
            except Exception as e:
                logger.error(f"Failed to load dataset '{self.dataset_name}': {e}")
                raise
        
        return self.dataset
    
    def get_train_data(self) -> Dataset:
        """
        Get the training split of the dataset.
        
        Returns:
            Dataset: Training dataset
        """
        dataset = self.load_dataset()
        if isinstance(dataset, DatasetDict) and 'train' in dataset:
            return dataset['train']
        return dataset
    
    def get_test_data(self) -> Optional[Dataset]:
        """
        Get the test split of the dataset if available.
        
        Returns:
            Optional[Dataset]: Test dataset or None if not available
        """
        dataset = self.load_dataset()
        if isinstance(dataset, DatasetDict) and 'test' in dataset:
            return dataset['test']
        return None
    
    def get_validation_data(self) -> Optional[Dataset]:
        """
        Get the validation split of the dataset if available.
        
        Returns:
            Optional[Dataset]: Validation dataset or None if not available
        """
        dataset = self.load_dataset()
        if isinstance(dataset, DatasetDict) and 'validation' in dataset:
            return dataset['validation']
        return None
    
    def get_dataset_info(self) -> Dict:
        """
        Get information about the dataset.
        
        Returns:
            Dict: Dataset information
        """
        dataset = self.load_dataset()
        info = {
            "name": self.dataset_name,
            "splits": list(dataset.keys()) if isinstance(dataset, DatasetDict) else ["main"],
        }
        
        # Add split sizes
        if isinstance(dataset, DatasetDict):
            sizes = {}
            for split_name, split_data in dataset.items():
                sizes[split_name] = len(split_data)
            info["sizes"] = sizes
        else:
            info["size"] = len(dataset)
        
        # Add column names
        if isinstance(dataset, DatasetDict):
            first_split = next(iter(dataset.values()))
            info["columns"] = first_split.column_names
        else:
            info["columns"] = dataset.column_names
        
        return info