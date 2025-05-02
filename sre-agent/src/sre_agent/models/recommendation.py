"""
Recommendation model for SRE agent.
"""

from typing import Dict, List, Any, Optional
from pydantic import BaseModel, Field


class RecommendationModel(BaseModel):
    """
    Represents the final output recommendation from the SRE agent.
    
    Attributes:
        alert_id: ID of the alert that was processed
        alert_type: Type of the alert (e.g., "PodCrashLoop")
        recommendation_text: Detailed recommendation text
        similar_incidents: List of similar incidents found during processing
        completed_tasks: List of tasks completed during the investigation
        investigation_summary: Optional summary of the investigation
        priority: Optional priority level for recommendation (e.g., "high", "medium", "low")
        time_to_resolve_estimate: Optional estimate for resolution time
    """
    alert_id: str
    alert_type: str
    recommendation_text: str
    similar_incidents: List[Dict[str, Any]]
    completed_tasks: List[str]
    investigation_summary: Optional[str] = None
    priority: Optional[str] = None
    time_to_resolve_estimate: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert the model to a dictionary."""
        return self.model_dump()