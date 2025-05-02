"""
FastAPI application for the SRE agent.
"""

import os
from fastapi import FastAPI, Depends, HTTPException
from pydantic import BaseModel
from typing import Dict, List, Any, Optional

from sre_agent.alert_processor import AlertProcessor
from sre_agent.models.alert import AlertModel
from sre_agent.models.recommendation import RecommendationModel

# Define the infrastructure graph
# In a production environment, this would likely be loaded from a database or service
infra_graph = {
    "regions": [
        {
            "name": "us-east-1",
            "projects": [
                {
                    "name": "ProjectA",
                    "vpcs": [
                        {
                            "id": "vpc-001",
                            "subnets": [
                                {
                                    "id": "subnet-101",
                                    "clusters": [
                                        {
                                            "name": "cluster-alpha",
                                            "nodes": [
                                                {
                                                    "name": "node-1",
                                                    "pods": [
                                                        {
                                                            "name": "auth-service-xyz-pod",
                                                            "containers": [
                                                                {
                                                                    "name": "auth-service",
                                                                    "version": "2.3.1",
                                                                    "process": "auth-service-app"
                                                                }
                                                            ]
                                                        },
                                                        {
                                                            "name": "payment-service-abc-pod",
                                                            "containers": [
                                                                {
                                                                    "name": "payment-service",
                                                                    "version": "1.8.0",
                                                                    "process": "payment-service-app"
                                                                }
                                                            ]
                                                        }
                                                    ]
                                                },
                                                {
                                                    "name": "node-2",
                                                    "pods": [
                                                        {
                                                            "name": "auth-service-uvw-pod",
                                                            "containers": [
                                                                {
                                                                    "name": "auth-service",
                                                                    "version": "2.3.1",
                                                                    "process": "auth-service-app"
                                                                }
                                                            ]
                                                        }
                                                    ]
                                                }
                                            ]
                                        }
                                    ]
                                }
                            ]
                        }
                    ]
                }
            ]
        }
    ]
}

# Create the FastAPI application
app = FastAPI(title="SRE Agent API")

# GET AlertProcessor instance
def get_alert_processor():
    return AlertProcessor(infra_graph)

# Define request and response models
class AlertRequest(BaseModel):
    id: str
    type: str
    summary: str
    details: str
    metadata: Optional[Dict[str, Any]] = None

class SimilarIncidentResponse(BaseModel):
    error: str
    solution: str
    similarity_score: float
    metadata: Optional[Dict[str, Any]] = None

class RecommendationResponse(BaseModel):
    alert_id: str
    alert_type: str
    recommendation_text: str
    similar_incidents: List[Dict[str, Any]]
    completed_tasks: List[str]

# API endpoints
@app.post("/api/v1/alerts", response_model=RecommendationResponse)
async def process_alert(alert: AlertRequest):
    """
    Process an alert and return recommendations.
    
    This endpoint:
    1. Takes an alert with ID, type, summary, and details
    2. Processes it through the SRE agent workflow
    3. Returns a recommendation
    """
    try:
        # Instantiate our alert processor
        processor = get_alert_processor()
        
        # Process the alert
        result = await processor.process_alert(alert.model_dump())
        
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing alert: {str(e)}")

@app.get("/health")
def health_check():
    """
    Health check endpoint.
    """
    return {"status": "healthy"}

if __name__ == "__main__":
    import uvicorn
    
    port = int(os.environ.get("PORT", 8000))
    host = os.environ.get("HOST", "0.0.0.0")
    
    uvicorn.run(app, host=host, port=port)