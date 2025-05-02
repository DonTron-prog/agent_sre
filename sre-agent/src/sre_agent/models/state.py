"""
State model for SRE agent workflow.
"""

from typing import Dict, List, Optional, Any
from typing_extensions import TypedDict


class AgentState(TypedDict):
    """
    Represents the state of the SRE agent workflow.
    
    Attributes:
        alert: The alert being processed
        plan: The investigation plan (list of tasks)
        current_task: The task currently being executed
        completed_tasks: List of tasks that have been completed
        task_results: Results of completed tasks
        similar_incidents: List of similar incidents from RAG
        reflections: List of reflections after tasks
        recommendation: The final recommendation
        infra_context: Infrastructure context relevant to the alert
    """
    alert: Dict[str, Any]
    plan: Optional[List[str]]
    current_task: Optional[str]
    completed_tasks: List[str]
    task_results: Optional[List[str]]
    similar_incidents: List[Dict[str, Any]]
    reflections: List[str]
    recommendation: Optional[Dict[str, Any]]
    infra_context: Optional[Dict[str, Any]]