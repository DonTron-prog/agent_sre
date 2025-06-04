"""Atomic Planning Agent using Atomic Agents framework."""

from typing import List
from pydantic import Field
import instructor
import openai
from atomic_agents.agents.base_agent import BaseAgent, BaseAgentConfig
from atomic_agents.lib.components.system_prompt_generator import SystemPromptGenerator
from atomic_agents.lib.base.base_io_schema import BaseIOSchema
from controllers.planning_agent.planner_schemas import PlanStepSchema


class AtomicPlanningInputSchema(BaseIOSchema):
    """Input schema for the Atomic Planning Agent."""
    
    alert: str = Field(..., description="The system alert to create a plan for")
    context: str = Field(..., description="Contextual information about the system")


class AtomicPlanningOutputSchema(BaseIOSchema):
    """Output schema for the Atomic Planning Agent."""
    
    steps: List[PlanStepSchema] = Field(
        ..., 
        description="Generated plan steps in logical order (3-5 steps)",
        min_items=2,
        max_items=4
    )
    reasoning: str = Field(..., description="Explanation of the planning approach and rationale")


class AtomicPlanningAgent(BaseAgent):
    """
    Atomic Planning Agent that generates structured SRE incident response plans.
    
    This agent follows the Atomic Agents pattern with clear input/output schemas
    and uses instructor for guaranteed structured outputs.
    """
    
    def __init__(self, client, model: str = "gpt-4"):
        """
        Initialize the Atomic Planning Agent.
        
        Args:
            client: Instructor-wrapped OpenAI client
            model: Model name for LLM calls
        """
        system_prompt_generator = SystemPromptGenerator(
            background=[
                "You are an expert SRE (Site Reliability Engineering) planning agent.",
                "You specialize in creating structured, actionable incident response plans.",
                "You analyze system alerts and context to generate logical step-by-step resolution plans.",
                "Your plans follow SRE best practices: investigation → diagnosis → resolution."
            ],
            steps=[
                "1. Analyze the alert and context to understand the problem scope and severity",
                "2. Identify initial investigation steps needed to gather system state information",
                "3. Determine diagnostic steps to identify root causes and contributing factors", 
                "4. Plan resolution steps or escalation procedures based on findings",
                "5. Structure the plan as 3-5 clear, actionable steps in logical sequence"
            ],
            output_instructions=[
                "Generate exactly 3-5 steps in logical order following investigation → diagnosis → resolution flow",
                "Each step description should be specific, actionable, and focused on a single objective",
                "Start with information gathering and system state assessment",
                "Progress through root cause analysis and impact assessment",
                "End with resolution actions or appropriate escalation procedures",
                "Provide clear reasoning for your overall planning approach",
                "Consider the specific technologies and systems mentioned in the context"
            ]
        )
        
        super().__init__(
            config=BaseAgentConfig(
                client=client,
                model=model,
                system_prompt_generator=system_prompt_generator,
                input_schema=AtomicPlanningInputSchema,
                output_schema=AtomicPlanningOutputSchema,
                max_retries=3,
                temperature=0.1  # Low temperature for consistent planning
            )
        )


def create_atomic_planning_agent(client: instructor.Instructor, model: str = "gpt-4") -> BaseAgent:
    """
    Factory function to create an Atomic Planning Agent with a shared client.
    
    Args:
        client: Pre-configured instructor-wrapped OpenAI client
        model: Model name for LLM calls
        
    Returns:
        BaseAgent: Configured planning agent
    """
    return BaseAgent(
        BaseAgentConfig(
            client=client,
            model=model,
            system_prompt_generator=SystemPromptGenerator(
                background=[
                    "You are an expert SRE (Site Reliability Engineering) planning agent.",
                    "You specialize in creating structured, actionable incident response plans.",
                    "You analyze system alerts and context to generate logical step-by-step resolution plans.",
                    "Your plans follow SRE best practices: investigation → diagnosis → resolution."
                ],
                steps=[
                    "1. Analyze the alert and context to understand the problem scope and severity",
                    "2. Identify initial investigation steps needed to gather system state information",
                    "3. Determine diagnostic steps to identify root causes and contributing factors",
                    "4. Plan resolution steps or escalation procedures based on findings",
                    "5. Structure the plan as 3-5 clear, actionable steps in logical sequence"
                ],
                output_instructions=[
                    "Generate exactly 3-5 steps in logical order following investigation → diagnosis → resolution flow",
                    "Each step description should be specific, actionable, and focused on a single objective",
                    "Start with information gathering and system state assessment",
                    "Progress through root cause analysis and impact assessment",
                    "End with resolution actions or appropriate escalation procedures",
                    "Provide clear reasoning for your overall planning approach",
                    "Consider the specific technologies and systems mentioned in the context"
                ]
            ),
            input_schema=AtomicPlanningInputSchema,
            output_schema=AtomicPlanningOutputSchema,
            max_retries=3,
            temperature=0.1  # Low temperature for consistent planning
        )
    )


# Example usage
if __name__ == "__main__":
    import os
    from rich.console import Console
    
    console = Console()
    
    # Create a shared client
    shared_client = instructor.from_openai(openai.OpenAI(base_url="https://openrouter.ai/api/v1", api_key=os.getenv("OPENAI_API_KEY")))

    # Create agent using the factory function
    agent = create_atomic_planning_agent(
        client=shared_client,
        model="gpt-4"
    )
    
    # Example input
    test_input = AtomicPlanningInputSchema(
        alert="Critical failure: 'ExtPluginReplicationError: Code 7749 - Sync Timeout with AlphaNode' in 'experimental-geo-sync-plugin v0.1.2' on db-primary.",
        context="System: Primary PostgreSQL Database (Version 15.3). Plugin: 'experimental-geo-sync-plugin v0.1.2' (third-party, integrated yesterday for PoC). Service: Attempting geo-replicated read-replica setup."
    )
    
    # Run planning
    try:
        result = agent.run(test_input)
        
        console.print("[bold blue]Generated Plan:[/bold blue]")
        for i, step in enumerate(result.steps, 1):
            console.print(f"{i}. {step.description}")
        
        console.print(f"\n[bold green]Reasoning:[/bold green] {result.reasoning}")
        
    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")