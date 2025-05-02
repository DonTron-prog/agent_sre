"""
Task execution node for the SRE agent workflow.
"""

from typing import Dict, Any
from langchain_openai import ChatOpenAI
from langchain.prompts import ChatPromptTemplate

from sre_agent.models.state import AgentState


def execute_task(state: AgentState) -> AgentState:
    """
    Execute the current task in the plan.
    
    This node:
    1. Takes the current task from the plan
    2. Uses the alert information and previous results
    3. Executes the task and adds the result to the state
    
    Args:
        state: Current workflow state
        
    Returns:
        Updated workflow state with task result
    """
    # Get the current task
    current_task_idx = len(state["completed_tasks"])
    current_task = state["plan"][current_task_idx] if state["plan"] and current_task_idx < len(state["plan"]) else None
    
    # If there's no current task, return the state unchanged
    if not current_task:
        return state
    
    # Define the task execution prompt
    template = """
    You are an expert SRE responsible for investigating alerts.
    
    ## ALERT INFORMATION
    Type: {alert_type}
    Summary: {alert_summary}
    Details: {alert_details}
    
    ## INFRASTRUCTURE CONTEXT
    {infra_context}
    
    ## SIMILAR PAST INCIDENTS
    {similar_incidents}
    
    ## CURRENT TASK
    {current_task}
    
    ## COMPLETED TASKS
    {completed_tasks}
    
    ## PREVIOUS TASK RESULTS
    {previous_results}
    
    Execute the current task and provide detailed findings. Be specific about what you discovered
    and the technical steps needed to investigate this issue. Think about:
    
    1. What commands, logs, or metrics would you check?
    2. What patterns or anomalies would you look for?
    3. What specific impact is this issue having?
    4. What is the root cause based on the evidence?
    
    Provide output as if you actually ran these commands and observed real data. Be detailed and technical.
    """
    
    # Format similar incidents for the prompt
    similar_incidents_text = "\n".join([
        f"Incident: {incident.get('error', '')}\n"
        f"Resolution: {incident.get('solution', '')}\n"
        f"Similarity: {incident.get('similarity_score', 0.0):.2f}\n"
        for incident in state["similar_incidents"]
    ])
    
    # Format completed tasks for the prompt
    completed_tasks_text = "\n".join([
        f"- {task}" for task in state["completed_tasks"]
    ])
    
    # Format previous task results
    previous_results_text = "\n".join([
        f"Task {i+1} Result: {result}" 
        for i, result in enumerate(state.get("task_results", []))
    ])
    
    # Format the prompt with data
    prompt = ChatPromptTemplate.from_template(template)
    llm = ChatOpenAI(temperature=0.3)
    
    # Create the chain
    chain = prompt | llm
    
    # Execute the chain
    result = chain.invoke({
        "alert_type": state["alert"]["type"],
        "alert_summary": state["alert"]["summary"],
        "alert_details": state["alert"]["details"],
        "infra_context": str(state["infra_context"]),
        "similar_incidents": similar_incidents_text,
        "current_task": current_task,
        "completed_tasks": completed_tasks_text,
        "previous_results": previous_results_text
    })
    
    # Update the state with the execution result
    task_result = result.content.strip()
    
    return {
        **state, 
        "task_results": state.get("task_results", []) + [task_result],
        "current_task": current_task
    }