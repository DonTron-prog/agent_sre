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
    print("DEBUG - Creating plan")
    print(f"DEBUG - Alert: {state['alert'].get('id')} - {state['alert'].get('type')}")
    print(f"DEBUG - Infra context: {state.get('infra_context')}")
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
    try:
        tasks = []
        content = result.content.strip()
        print(f"DEBUG - LLM response: {content[:100]}...")
        
        for line in content.split("\n"):
            # Extract tasks from numbered list
            if line.strip() and line[0].isdigit() and '. ' in line:
                tasks.append(line.split('. ', 1)[1].strip())
        
        print(f"DEBUG - Extracted {len(tasks)} tasks: {tasks}")
        
        # Update the state
        updated_state = {
            **state,
            "plan": tasks,
            "current_task": "Check similar past incidents" if tasks else None
        }
        
        print(f"DEBUG - Plan created successfully")
        print(f"DEBUG - Updated state keys: {updated_state.keys()}")
        
        return updated_state
    except Exception as e:
        print(f"DEBUG - Error creating plan: {str(e)}")
        # Return a minimal valid state update with a default plan
        return {
            **state,
            "plan": ["Check similar past incidents"],
            "current_task": "Check similar past incidents"
        }


def determine_next_task(state: AgentState) -> str:
    """
    Determine which task to execute next or end the workflow.
    
    Args:
        state: Current workflow state
        
    Returns:
        Name of the next node to execute
    """
    print("DEBUG - Determining next task")
    print(f"DEBUG - Completed tasks: {state.get('completed_tasks', [])}")
    print(f"DEBUG - Plan: {state.get('plan', [])}")
    print(f"DEBUG - Current task value: {state.get('current_task')}")
    
    try:
        if not state.get("plan") or len(state.get("completed_tasks", [])) >= len(state.get("plan", [])):
            print("DEBUG - All tasks completed, generating recommendation")
            return "generate_recommendation"
        
        next_task_idx = len(state.get("completed_tasks", []))
        current_task = state["plan"][next_task_idx]
        
        print(f"DEBUG - Next task index: {next_task_idx}")
        print(f"DEBUG - Current task: {current_task}")
        
        if next_task_idx == 0:  # First task is always RAG lookup
            print("DEBUG - First task, routing to RAG lookup")
            # Force the current_task to match the condition in the workflow
            state["current_task"] = "rag_lookup"
            print(f"DEBUG - Set current_task to: {state.get('current_task')}")
            return "rag_lookup"
        
        print("DEBUG - Routing to execute task")
        # Force the current_task to match the condition in the workflow
        state["current_task"] = "execute_task"
        print(f"DEBUG - Set current_task to: {state.get('current_task')}")
        return "execute_task"
    except Exception as e:
        print(f"DEBUG - Error determining next task: {str(e)}")
        # Default to recommendation if there's an error
        return "generate_recommendation"