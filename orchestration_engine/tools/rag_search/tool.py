import os
import openai
import instructor
from typing import List, Dict
from pydantic import Field

from atomic_agents.lib.base.base_tool import BaseTool, BaseIOSchema
from atomic_agents.lib.components.agent_memory import AgentMemory # Added for completeness, though not directly used in this snippet

from orchestration_engine.tools.rag_search.config import RAGSearchToolConfig
from orchestration_engine.services.chroma_db import ChromaDBService
import sys
from orchestration_engine.tools.rag_search.rag_context_providers import RAGContextProvider, ChunkItem
from orchestration_engine.agents.rag_query_agent import create_query_agent, RAGQueryAgentInputSchema
from orchestration_engine.agents.rag_qa_agent import create_qa_agent, RAGQuestionAnsweringAgentInputSchema
from orchestration_engine.tools.rag_search.document_processor import DocumentProcessor

# --- Schemas ---
class RAGSearchToolInputSchema(BaseIOSchema):
    """
    Schema for input to a tool for searching through local documents using RAG.
    Takes a query and returns relevant document chunks along with generated answers.
    """
    query: str = Field(..., description="The question or query to search for in the knowledge base.")

class RAGSearchResultItemSchema(BaseIOSchema):
    """This schema represents a single search result item from the RAG system"""
    content: str = Field(..., description="The content chunk from the document")
    source: str = Field(..., description="The source file of this content chunk")
    distance: float = Field(..., description="Similarity score (lower is better)")
    metadata: Dict = Field(..., description="Additional metadata for the chunk")

class RAGSearchToolOutputSchema(BaseIOSchema):
    """This schema represents the output of the RAG search tool."""
    query: str = Field(..., description="The query used for searching")
    results: List[RAGSearchResultItemSchema] = Field(..., description="List of relevant document chunks")
    answer: str = Field(..., description="Generated answer based on the retrieved chunks")
    reasoning: str = Field(..., description="Explanation of how the answer was derived from the chunks")

# --- Main Tool & Logic ---
class RAGSearchTool(BaseTool):
    input_schema = RAGSearchToolInputSchema
    output_schema = RAGSearchToolOutputSchema

    def __init__(self, config: RAGSearchToolConfig = RAGSearchToolConfig()):
        super().__init__(config)
        self.config = config
        
        self.api_key = config.openai_api_key or os.getenv("OPENAI_API_KEY")
        if not self.api_key:
            raise ValueError("OpenAI API key not found. Please set OPENAI_API_KEY environment variable or pass via config.")

        self.chroma_db = ChromaDBService(
            collection_name=config.collection_name,
            embedding_model_name=config.embedding_model_name,
            openai_api_key=self.api_key,
            persist_directory=config.persist_dir,
            recreate_collection=config.recreate_collection_on_init,
        )
        
        self.document_processor = DocumentProcessor(
            chunk_size=config.chunk_size,
            chunk_overlap=config.chunk_overlap
        )
        
        self._load_and_index_documents()

        client = instructor.from_openai(openai.OpenAI(api_key=self.api_key))

        self.query_agent = create_query_agent(client, config.llm_model_name)
        
        self.rag_context_provider = RAGContextProvider("Retrieved Document Chunks")
        self.qa_agent = create_qa_agent(client, config.llm_model_name, self.rag_context_provider)
        

    def _load_and_index_documents(self):
        # Check if collection already has documents or if a reload is forced
        count = self.chroma_db.collection.count()
        
        if count == 0 or self.config.force_reload_documents:
            all_chunks, all_metadatas = self.document_processor.load_and_index_documents(self.config.docs_dir)
            
            if all_chunks:
                self.chroma_db.add_documents(documents=all_chunks, metadatas=all_metadatas)
        # If documents exist and force_reload is false, do nothing and use existing collection.

    def run(self, params: RAGSearchToolInputSchema) -> RAGSearchToolOutputSchema:
        # 1. Generate semantic query
        query_agent_input = RAGQueryAgentInputSchema(user_message=params.query)
        query_output = self.query_agent.run(query_agent_input)
        semantic_query = query_output.query

        # 2. Retrieve relevant chunks
        search_results = self.chroma_db.query(
            query_text=semantic_query,
            n_results=self.config.num_chunks_to_retrieve  # Request significantly more to ensure diversity
        )
        

        
        retrieved_chunks_for_context = []
        output_results = []
        
        # Process results to get unique chunks by content
        added_content = set()
        if search_results["documents"]:
            # Use zip to process all result components together
            for doc, doc_id, dist_val, meta in zip(
                search_results["documents"],
                search_results["ids"],
                search_results["distances"],
                search_results["metadatas"]
            ):
                if doc not in added_content:
                    # Create ChunkItem with all metadata including ID and distance
                    chunk_item = ChunkItem(
                        content=doc,
                        metadata={
                            "chunk_id": doc_id,
                            "distance": dist_val,
                            "source": meta.get("source", "N/A"),
                            "file_name": meta.get("file_name", ""),
                            **meta  # Include all other metadata
                        }
                    )
                    retrieved_chunks_for_context.append(chunk_item)
                    
                    # Create result schema object
                    output_results.append(
                        RAGSearchResultItemSchema(
                            content=doc,
                            source=meta.get("source", "N/A"),
                            distance=dist_val,
                            metadata=meta
                        )
                    )
                    added_content.add(doc)
                
                # Limit to requested number of unique chunks
                if len(output_results) >= self.config.num_chunks_to_retrieve:
                    break
        
        self.rag_context_provider.chunks = retrieved_chunks_for_context # This should ideally also be unique
        
        # Update retrieved_chunks_for_context to only contain unique items for the QA agent
        # This ensures the QA agent also works with the unique set if it relies on self.rag_context_provider.chunks directly
        unique_retrieved_chunks_for_context = []
        seen_context_content = set()
        for chunk_item in retrieved_chunks_for_context:
            if chunk_item.content not in seen_context_content:
                unique_retrieved_chunks_for_context.append(chunk_item)
                seen_context_content.add(chunk_item.content)
        self.rag_context_provider.chunks = unique_retrieved_chunks_for_context

        if not output_results: # Changed from retrieved_chunks_for_context to output_results
            print("No relevant chunks found.")
            return RAGSearchToolOutputSchema(
                query=params.query,
                results=[],
                answer="I could not find any relevant information in the documents to answer your question.",
                reasoning="No relevant document chunks were retrieved from the knowledge base for the generated semantic query."
            )

        # 3. Generate answer using QA agent
        qa_agent_input = RAGQuestionAnsweringAgentInputSchema(question=params.query)
        qa_output = self.qa_agent.run(qa_agent_input)

        return RAGSearchToolOutputSchema(
            query=params.query,
            results=output_results,
            answer=qa_output.answer,
            reasoning=qa_output.reasoning
        )