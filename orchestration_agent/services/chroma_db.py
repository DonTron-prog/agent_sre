import os
import shutil
import uuid
from typing import List, Dict, Optional

import chromadb
from chromadb.utils.embedding_functions import OpenAIEmbeddingFunction

class ChromaDBService:
    """Service for interacting with ChromaDB using OpenAI embeddings."""
    def __init__(
        self,
        collection_name: str,
        embedding_model_name: str,
        openai_api_key: Optional[str],
        persist_directory: str,
        recreate_collection: bool,
    ):
        self.api_key = openai_api_key or os.getenv("OPENAI_API_KEY")
        if not self.api_key:
            raise ValueError("OpenAI API key not found. Please set OPENAI_API_KEY environment variable or pass via config.")
        
        self.embedding_function = OpenAIEmbeddingFunction(api_key=self.api_key, model_name=embedding_model_name)

        if recreate_collection and os.path.exists(persist_directory):
            shutil.rmtree(persist_directory)
        os.makedirs(persist_directory, exist_ok=True)

        self.client = chromadb.PersistentClient(path=persist_directory)
        self.collection = self.client.get_or_create_collection(
            name=collection_name,
            embedding_function=self.embedding_function,
            metadata={"hnsw:space": "cosine"},
        )

    def add_documents(self, documents: List[str], metadatas: List[Dict[str, str]], ids: Optional[List[str]] = None, batch_size: int = 100) -> List[str]:
        if ids is None:
            # If no IDs are provided, generate them for all documents upfront
            # This ensures consistency if batching fails mid-way, though not strictly necessary for this implementation
            # as ChromaDB itself might handle ID generation if not provided per batch.
            # However, explicit ID generation allows us to return all IDs that *would* have been used.
            generated_ids = [str(uuid.uuid4()) for _ in documents]
        else:
            generated_ids = ids

        all_added_ids: List[str] = []
        for i in range(0, len(documents), batch_size):
            batch_documents = documents[i:i + batch_size]
            batch_metadatas = metadatas[i:i + batch_size]
            batch_ids = generated_ids[i:i + batch_size]
            
            # Assuming self.collection.add can handle these lists directly
            self.collection.add(documents=batch_documents, metadatas=batch_metadatas, ids=batch_ids)
            all_added_ids.extend(batch_ids)
            print(f"Added batch {i // batch_size + 1}/{(len(documents) -1) // batch_size + 1} to ChromaDB ({len(batch_documents)} documents)")

        return all_added_ids

    def query(self, query_text: str, n_results: int = 5) -> Dict:
        count = self.collection.count()
        if count == 0:
            return {"documents": [[]], "metadatas": [[]], "distances": [[]], "ids": [[]]} # Chroma returns list of lists
            
        results = self.collection.query(
            query_texts=[query_text],
            n_results=min(n_results, count),
            include=["documents", "metadatas", "distances"],
        )
        # Ensure results are properly unpacked if query_texts was a list of one item
        return {
            "documents": results["documents"][0] if results["documents"] else [],
            "metadatas": results["metadatas"][0] if results["metadatas"] else [],
            "distances": results["distances"][0] if results["distances"] else [],
            "ids": results["ids"][0] if results["ids"] else [],
        }