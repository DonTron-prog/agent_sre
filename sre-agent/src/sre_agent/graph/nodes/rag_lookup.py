"""
RAG lookup node for the SRE agent workflow.
"""

from typing import Dict, Any

from sre_agent.models.state import AgentState
from sre_agent.services.rag_service import RAGService
import traceback


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
    print("DEBUG - RAG lookup function called directly")
    print(f"DEBUG - Alert: {state['alert'].get('id')} - {state['alert'].get('type')}")
    
    # Get the RAG service
    try:
        rag_service = RAGService()
        print("DEBUG - RAG service initialized")
        
        # Find similar alerts
        try:
            similar_incidents = rag_service.find_similar_alerts(state["alert"])
            print(f"DEBUG - Found {len(similar_incidents)} similar incidents")
            print(f"DEBUG - First incident: {similar_incidents[0] if similar_incidents else 'None'}")
        except Exception as e:
            print(f"DEBUG - Error finding similar alerts: {str(e)}")
            print(f"DEBUG - Traceback: {traceback.format_exc()}")
            similar_incidents = []
    except Exception as e:
        print(f"DEBUG - Error initializing RAG service: {str(e)}")
        print(f"DEBUG - Traceback: {traceback.format_exc()}")
        similar_incidents = []
    
    # Update the state
    try:
        new_state = {
            **state,
            "similar_incidents": similar_incidents,
            "completed_tasks": state.get("completed_tasks", []) + ["Check similar past incidents"],
            "current_task": state["plan"][0] if state.get("plan") else None,
            "task_results": state.get("task_results", []) + [
                f"Found {len(similar_incidents)} similar past incidents. " +
                f"Top incident: {similar_incidents[0]['error'][:100] + '...' if similar_incidents else 'None'}"
            ]
        }
        
        print(f"DEBUG - RAG lookup completed successfully")
        print(f"DEBUG - Updated state keys: {new_state.keys()}")
        
        return new_state
    except Exception as e:
        print(f"DEBUG - Error updating state after RAG lookup: {str(e)}")
        # Return a minimal valid state update
        return {
            **state,
            "similar_incidents": similar_incidents,
            "completed_tasks": state.get("completed_tasks", []) + ["Check similar past incidents"],
            "task_results": state.get("task_results", []) + [f"Error in RAG lookup: {str(e)}"]
        }