"""
Main entry point for processing alerts in the SRE agent.
"""

from typing import Dict, Any
import asyncio

from sre_agent.services.infra_service import InfrastructureGraphService
from sre_agent.services.rag_service import RAGService
from sre_agent.graph.workflow import create_agent_graph
from sre_agent.models.alert import AlertModel


class AlertProcessor:
    """
    Main entry point for processing alerts.
    
    This class:
    1. Initializes the infrastructure graph service
    2. Initializes the RAG service
    3. Creates the LangGraph agent
    4. Processes alerts through the workflow
    """
    
    def __init__(self, infra_graph: Dict[str, Any]):
        """
        Initialize with the infrastructure graph data.
        
        Args:
            infra_graph: Infrastructure knowledge graph data
        """
        self.infra_service = InfrastructureGraphService(infra_graph)
        self.rag_service = RAGService()
        self.agent_graph = create_agent_graph()
    
    async def process_alert(self, alert: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process an incoming alert through the LangGraph workflow.
        
        Args:
            alert: The alert to process (can be dict or AlertModel)
            
        Returns:
            Dictionary containing the recommendation and related information
        """
        # Convert to AlertModel if it's a dict
        if isinstance(alert, dict):
            alert_model = AlertModel(**alert)
            alert = alert_model.to_dict()
        
        # Get infrastructure context for this alert
        infra_context = self.infra_service.get_context_for_alert(alert)
        
        # Initialize the state
        initial_state = {
            "alert": alert,
            "plan": None,
            "current_task": None,
            "completed_tasks": [],
            "task_results": [],
            "similar_incidents": [],
            "reflections": [],
            "recommendation": None,
            "infra_context": infra_context
        }
        
        # Execute the workflow
        # Use ainvoke instead of arun for newer LangGraph versions
        final_state = await self.agent_graph.ainvoke(initial_state)
        
        return final_state["recommendation"]
    
    def process_alert_sync(self, alert: Dict[str, Any]) -> Dict[str, Any]:
        """
        Synchronous version of process_alert.
        
        Args:
            alert: The alert to process
            
        Returns:
            Dictionary containing the recommendation
        """
        return asyncio.run(self.process_alert(alert))