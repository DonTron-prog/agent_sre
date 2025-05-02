"""
Reflection node for the SRE agent workflow.
"""

from typing import Dict, Any
from langchain_openai import ChatOpenAI
from langchain.prompts import ChatPromptTemplate

from sre_agent.models.state import AgentState


def reflect(state: AgentState) -> AgentState:
    """
    Reflect on the results of the current task.
    
    This node:
    1. Takes the current task and its result
    2. Analyzes the findings
    3. Generates a reflection on what was learned and next steps
    
    Args:
        state: Current workflow state
        
    Returns:
        Updated workflow state with reflection
    """
    # Get the current task and its result
    current_task = state["current_task"]
    task_result = state["task_results"][-1] if state.get("task_results") else ""
    
    # Define the reflection prompt
    template = """
    You are an expert SRE responsible for critical reflection on alert investigation.
    
    ## ALERT INFORMATION
    Type: {alert_type}
    Summary: {alert_summary}
    Details: {alert_details}
    
    ## CURRENT TASK
    {current_task}
    
    ## TASK RESULT
    {task_result}
    
    ## REFLECTION INSTRUCTIONS
    Analyze the task result and provide a concise reflection on:
    1. What was learned from this task
    2. How this information impacts the investigation
    3. Whether any adjustment is needed to the plan
    4. What insights have been gained about the potential root cause
    
    Make your reflection concise, technical, and actionable.
    """
    
    # Format the prompt with data
    prompt = ChatPromptTemplate.from_template(template)
    llm = ChatOpenAI(temperature=0.2)
    
    # Create the chain
    chain = prompt | llm
    
    # Execute the chain
    result = chain.invoke({
        "alert_type": state["alert"]["type"],
        "alert_summary": state["alert"]["summary"],
        "alert_details": state["alert"]["details"],
        "current_task": current_task,
        "task_result": task_result
    })
    
    reflection = result.content.strip()
    
    # Update the state
    return {
        **state,
        "reflections": state.get("reflections", []) + [reflection],
        "completed_tasks": state["completed_tasks"] + [current_task] 
    }