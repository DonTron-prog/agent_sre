"""
RAG lookup node for the SRE agent workflow.
"""

from typing import Dict, Any
import logging

from sre_agent.models.state import AgentState
from sre_agent.services.rag_service import RAGService

# Set up logging
logger = logging.getLogger(__name__)


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
    try:
        logger.info("Initializing RAG service")
        rag_service = RAGService()
        
        # Find similar alerts
        try:
            logger.info(f"Finding similar alerts for: {state['alert']['type']}: {state['alert']['summary']}")
            similar_incidents = rag_service.find_similar_alerts(state["alert"], state)
            logger.info(f"Found {len(similar_incidents)} similar incidents")
            if similar_incidents:
                logger.info(f"First incident: {similar_incidents[0]}")
        except Exception as e:
            logger.error(f"Error finding similar alerts: {str(e)}")
            similar_incidents = []
    except Exception as e:
        logger.error(f"Error initializing RAG service: {str(e)}")
        similar_incidents = []
    
    # Update the state
    try:
        print("DEBUG: RAG lookup completed, returning state with similar incidents")
        updated_state = {
            **state,
            "similar_incidents": similar_incidents,
            "completed_tasks": state.get("completed_tasks", []) + ["Check similar past incidents"],
            # Don't set current_task here, let determine_next_task handle it
            "task_results": state.get("task_results", []) + [
                f"Found {len(similar_incidents)} similar past incidents. " +
                f"Top incident: {similar_incidents[0]['error'][:100] + '...' if similar_incidents else 'None'}"
            ]
        }
        print(f"DEBUG: RAG lookup updated state - completed_tasks: {updated_state.get('completed_tasks', [])}")
        return updated_state
    except Exception as e:
        print(f"DEBUG: Error in RAG lookup: {str(e)}")
        # Return a minimal valid state update
        return {
            **state,
            "similar_incidents": similar_incidents,
            "completed_tasks": state.get("completed_tasks", []) + ["Check similar past incidents"],
            "task_results": state.get("task_results", []) + ["Error in RAG lookup"]
        }