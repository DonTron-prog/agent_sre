"""
RAG lookup node for the SRE agent workflow.
"""

from typing import Dict, Any

from sre_agent.models.state import AgentState
from sre_agent.services.rag_service import RAGService


def rag_lookup(state: AgentState) -> AgentState:
    """
    Find similar incidents in the RAG system.
    
    This node:
    1. Uses the RAG service to query for similar past incidents
    2. Adds the results to the workflow state
    3. Marks the task as completed
    
    Args:
        state: Current workflow state
        
    Returns:
        Updated workflow state with similar incidents
    """
    # Get the RAG service
    rag_service = RAGService()
    
    # Find similar alerts
    similar_incidents = rag_service.find_similar_alerts(state["alert"])
    
    # Update the state
    new_state = {
        **state,
        "similar_incidents": similar_incidents,
        "completed_tasks": state["completed_tasks"] + ["Check similar past incidents"],
        "current_task": state["plan"][0] if state["plan"] else None,
        "task_results": state.get("task_results", []) + [
            f"Found {len(similar_incidents)} similar past incidents. " +
            f"Top incident: {similar_incidents[0]['error'][:100] + '...' if similar_incidents else 'None'}"
        ]
    }
    
    return new_state