"""
Recommendation node for the SRE agent workflow.
"""

from typing import Dict, Any, List
from langchain_openai import ChatOpenAI
from langchain.prompts import ChatPromptTemplate

from sre_agent.models.state import AgentState
from sre_agent.services.rag_service import RAGService


def generate_recommendation(state: AgentState) -> AgentState:
    """
    Generate final recommendations based on all gathered information.
    
    This node:
    1. Takes all accumulated information from the workflow
    2. Synthesizes it into a comprehensive recommendation
    3. Adds the recommendation to the workflow state
    
    Args:
        state: Current workflow state
        
    Returns:
        Updated workflow state with recommendation
    """
    print("\n==== RECOMMENDATION NODE ENTERED ====")
    print(f"DEBUG: State entering recommendation node - reflections: {state.get('reflections', [])}")
    print(f"DEBUG: State entering recommendation node - completed_tasks: {state.get('completed_tasks', [])}")

    # Define the recommendation prompt
    template = """
    You are an expert SRE responsible for providing solution recommendations for alerts.
    
    ## ALERT INFORMATION
    Type: {alert_type}
    Summary: {alert_summary}
    Details: {alert_details}
    
    ## INFRASTRUCTURE CONTEXT
    {infra_context}
    
    ## SIMILAR PAST INCIDENTS
    {similar_incidents}
    
    ## INVESTIGATION FINDINGS
    Completed Tasks:
    {completed_tasks}
    
    Task Results:
    {task_results}
    
    Reflections:
    {reflections}
    
    ## OUTPUT INSTRUCTIONS
    Based on all available information, provide:
    1. A concise summary of the investigation findings
    2. The recommended areas to investigate further
    3. A detailed solution recommendation with specific steps to resolve the issue
    4. Any preventive measures to avoid similar issues in the future
    
    Your response should be highly technical, actionable, and include specific commands, configurations, 
    or code changes where applicable. Format your response as a structured report with clear sections.
    """
    
    # Prepare data for the prompt
    similar_incidents = state.get("similar_incidents", []) or []
    similar_incidents_text = "\n".join([
        f"Incident: {incident.get('error', '')}\n"
        f"Resolution: {incident.get('solution', '')}\n"
        f"Similarity: {incident.get('similarity_score', 0.0):.2f}\n"
        for incident in similar_incidents
    ]) or "No similar incidents found."
    
    completed_tasks = state.get("completed_tasks", []) or []
    completed_tasks_text = "\n".join([
        f"- {task}" for task in completed_tasks
    ]) or "No completed tasks."
    
    task_results = state.get("task_results", []) or []
    plan = state.get("plan", []) or []
    task_results_text = "\n".join([
        f"Task: {plan[i] if i < len(plan) else 'Unknown'}\nResult: {result}\n"
        for i, result in enumerate(task_results)
    ]) or "No task results."
    
    reflections = state.get("reflections", []) or []
    reflections_text = "\n".join([
        f"Reflection {i+1}: {reflection}"
        for i, reflection in enumerate(reflections)
    ]) or "No reflections."
    
    # Format the prompt with all accumulated data
    prompt = ChatPromptTemplate.from_template(template)
    llm = ChatOpenAI(temperature=0.2)
    
    # Create the chain
    chain = prompt | llm
    
    # Execute the chain
    result = chain.invoke({
        "alert_type": state["alert"]["type"],
        "alert_summary": state["alert"]["summary"],
        "alert_details": state["alert"]["details"],
        "infra_context": str(state["infra_context"]),
        "similar_incidents": similar_incidents_text,
        "completed_tasks": completed_tasks_text,
        "task_results": task_results_text,
        "reflections": reflections_text
    })
    
    recommendation = result.content.strip()
    
    # Update the state
    try:
        return {
            **state,
            "recommendation": {
                "alert_id": state["alert"]["id"],
                "alert_type": state["alert"]["type"],
                "recommendation_text": recommendation,
                "similar_incidents": state.get("similar_incidents", []),
                "completed_tasks": state.get("completed_tasks", [])
            }
        }
    except Exception as e:
        # Return state with a basic recommendation to avoid None
        return {
            **state,
            "recommendation": {
                "alert_id": state["alert"].get("id", "unknown"),
                "alert_type": state["alert"].get("type", "unknown"),
                "recommendation_text": "Error generating recommendation: " + str(e),
                "similar_incidents": [],
                "completed_tasks": []
            }
        }