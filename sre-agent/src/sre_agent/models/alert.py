"""
Alert data model for SRE agent.
"""

from typing import Dict, Any, Optional
from pydantic import BaseModel


class AlertModel(BaseModel):
    """
    Represents the standardized alert structure.
    
    Attributes:
        id: Unique identifier for the alert
        type: Type of alert (e.g., "PodCrashLoop", "HighCPU", etc.)
        summary: Brief description of the alert
        details: Detailed description of the alert
        metadata: Additional metadata (optional)
    """
    id: str
    type: str
    summary: str
    details: str
    metadata: Optional[Dict[str, Any]] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert the model to a dictionary."""
        return self.model_dump()