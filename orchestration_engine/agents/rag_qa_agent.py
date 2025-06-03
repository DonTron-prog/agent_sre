import openai
import instructor
from pydantic import Field

from atomic_agents.agents.base_agent import BaseAgent, BaseAgentConfig, BaseIOSchema
from atomic_agents.lib.components.system_prompt_generator import SystemPromptGenerator
from atomic_agents.lib.components.agent_memory import AgentMemory
from orchestration_engine.tools.rag_search.rag_context_providers import RAGContextProvider # Adjusted import

class RAGQuestionAnsweringAgentInputSchema(BaseIOSchema):
    """Input schema for the RAG QA agent, taking the user's question."""
    question: str = Field(..., description="The user's question to answer")

class RAGQuestionAnsweringAgentOutputSchema(BaseIOSchema):
    """Output schema for the RAG QA agent, providing the answer and reasoning."""
    reasoning: str = Field(..., description="The reasoning process leading up to the final answer")
    answer: str = Field(..., description="The answer to the user's question based on the retrieved context")

def create_qa_agent(client: instructor.Instructor, model_name: str, rag_context_provider: RAGContextProvider) -> BaseAgent:
    qa_agent = BaseAgent(
        BaseAgentConfig(
            client=client,
            model=model_name,
            system_prompt_generator=SystemPromptGenerator(
                background=[
                    "You are an expert at answering questions using retrieved context chunks from a RAG system.",
                    "Your role is to synthesize information from the chunks to provide accurate, well-supported answers.",
                    "You must explain your reasoning process before providing the answer.",
                ],
                steps=[
                    "1. Analyze the question and available context chunks.",
                    "2. Identify the most relevant information in the chunks.",
                    "3. Explain how you'll use this information to answer the question.",
                    "4. Synthesize information into a coherent answer.",
                ],
                output_instructions=[
                    "First explain your reasoning process clearly.",
                    "Then provide a clear, direct answer based on the context.",
                    "If context is insufficient, state this in your reasoning and answer 'I don't have enough information to answer this question based on the provided documents.'",
                    "Never make up information not present in the chunks.",
                    "Focus on being accurate and concise.",
                ],
            ),
            input_schema=RAGQuestionAnsweringAgentInputSchema,
            output_schema=RAGQuestionAnsweringAgentOutputSchema,
            memory=AgentMemory(max_messages=5)
        )
    )
    qa_agent.register_context_provider("rag_context", rag_context_provider)
    return qa_agent