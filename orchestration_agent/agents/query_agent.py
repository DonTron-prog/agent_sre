import openai
import instructor
from pydantic import Field

from atomic_agents.agents.base_agent import BaseAgent, BaseAgentConfig, BaseIOSchema
from atomic_agents.lib.components.system_prompt_generator import SystemPromptGenerator
from atomic_agents.lib.components.agent_memory import AgentMemory

class RAGQueryAgentInputSchema(BaseIOSchema):
    """Input schema for the RAG query agent, taking the user's raw message."""
    user_message: str = Field(..., description="The user's question or message to generate a semantic search query for")

class RAGQueryAgentOutputSchema(BaseIOSchema):
    """Output schema for the RAG query agent, providing the generated query and reasoning."""
    reasoning: str = Field(..., description="The reasoning process leading up to the final query")
    query: str = Field(..., description="The semantic search query to use for retrieving relevant chunks")

def create_query_agent(client: instructor.Instructor, model_name: str) -> BaseAgent:
    return BaseAgent(
        BaseAgentConfig(
            client=client,
            model=model_name,
            system_prompt_generator=SystemPromptGenerator(
                background=[
                    "You are an expert at formulating semantic search queries for RAG systems.",
                    "Your role is to convert user questions into effective semantic search queries that will retrieve the most relevant text chunks.",
                ],
                steps=[
                    "1. Analyze the user's question to identify key concepts and information needs.",
                    "2. Reformulate the question into a semantic search query that will match relevant content.",
                    "3. Ensure the query captures the core meaning while being general enough to match similar content.",
                ],
                output_instructions=[
                    "Generate a clear, concise semantic search query.",
                    "Focus on key concepts and entities from the user's question.",
                    "Avoid overly specific details that might miss relevant matches.",
                    "Explain your reasoning for the query formulation.",
                ],
            ),
            input_schema=RAGQueryAgentInputSchema,
            output_schema=RAGQueryAgentOutputSchema,
            memory=AgentMemory(max_messages=5)
        )
    )