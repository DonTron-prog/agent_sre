"""
Planning node for the SRE agent workflow.
"""

from typing import Dict, List, Any
from langchain_openai import ChatOpenAI
from langchain.prompts import ChatPromptTemplate

from sre_agent.models.state import AgentState


def create_plan(state: AgentState) -> AgentState:
    """
    Create an initial plan based on the alert.
    
    This node:
    1. Takes the alert information
    2. Uses the infrastructure context
    3. Generates a plan with tasks to diagnose and resolve the alert
    
    Args:
        state: Current workflow state
        
    Returns:
        Updated workflow state with plan
    """
    # Define the system prompt for plan creation
    template = """
    You are an expert SRE responsible for creating an investigation plan for alerts.
    
    ## ALERT INFORMATION
    Type: {alert_type}
    Summary: {alert_summary}
    Details: {alert_details}
    
    ## INFRASTRUCTURE CONTEXT
    {infra_context}
    
    Create a sequential investigation plan with 3-5 specific tasks to diagnose and resolve this alert.
    The first task should always be to check similar past incidents.
    Format your response as a numbered list of tasks only.
    """
    
    # Format the prompt with alert data
    prompt = ChatPromptTemplate.from_template(template)
    llm = ChatOpenAI(temperature=0.2)
    
    # Create the chain
    chain = prompt | llm
    
    # Execute the chain
    result = chain.invoke({
        "alert_type": state["alert"]["type"],
        "alert_summary": state["alert"]["summary"],
        "alert_details": state["alert"]["details"],
        "infra_context": str(state["infra_context"])
    })
    
    # Parse the tasks from the result
    tasks = []
    for line in result.content.strip().split("\n"):
        # Extract tasks from numbered list
        if line.strip() and line[0].isdigit() and '. ' in line:
            tasks.append(line.split('. ', 1)[1].strip())
    
    # Update the state
    return {
        **state,
        "plan": tasks,
        "current_task": "Check similar past incidents" if tasks else None
    }


def determine_next_task(state: AgentState) -> str:
    """
    Determine which task to execute next or end the workflow.
    
    Args:
        state: Current workflow state
        
    Returns:
        Name of the next node to execute
    """
    if not state["plan"] or len(state["completed_tasks"]) >= len(state["plan"]):
        return "generate_recommendation"
    
    next_task_idx = len(state["completed_tasks"])
    current_task = state["plan"][next_task_idx]
    
    if next_task_idx == 0:  # First task is always RAG lookup
        return "rag_lookup"
    
    return "execute_task"