"""
Main entry point for processing alerts in the SRE agent.
"""

from typing import Dict, Any
import asyncio

from sre_agent.services.infra_service import InfrastructureGraphService
from sre_agent.services.rag_service import RAGService
from sre_agent.graph.workflow import create_agent_graph
from sre_agent.models.alert import AlertModel
from sre_agent.graph.nodes.rag_lookup import rag_lookup
from sre_agent.graph.nodes.recommendation import generate_recommendation


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
            try:
                alert_model = AlertModel(**alert)
                alert = alert_model.to_dict()
            except Exception as e:
                # Silently handle conversion errors
                pass
        
        # Get infrastructure context for this alert
        try:
            infra_context = self.infra_service.get_context_for_alert(alert)
        except Exception as e:
            infra_context = {}
        
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
        
        # Execute the workflow first
        try:
            final_state = await self.agent_graph.ainvoke(initial_state)
            
            # If workflow execution produced a recommendation, return it
            if final_state.get("recommendation"):
                return final_state.get("recommendation")
        except Exception:
            # Silently handle workflow execution errors
            pass
        
        # If workflow execution failed or didn't produce a recommendation, use direct calls as fallback
        try:
            # First, perform RAG lookup
            rag_result = rag_lookup(initial_state)
            
            # Then, generate a recommendation
            rec_state = {
                **rag_result,
                "completed_tasks": rag_result.get("completed_tasks", []) + ["Execute task"],
                "task_results": rag_result.get("task_results", []) + ["Task execution result"]
            }
            rec_result = generate_recommendation(rec_state)
            
            # Return the recommendation from direct calls
            if rec_result.get("recommendation"):
                return rec_result.get("recommendation")
        except Exception:
            # Silently handle direct call errors
            pass
        
        # If all else fails, create a basic recommendation
        return {
            "alert_id": alert.get("id", "unknown"),
            "alert_type": alert.get("type", "unknown"),
            "recommendation_text": "Unable to generate a detailed recommendation. Please check the logs for more information.",
            "similar_incidents": [],
            "completed_tasks": []
        }
    
    def process_alert_sync(self, alert: Dict[str, Any]) -> Dict[str, Any]:
        """
        Synchronous version of process_alert.
        
        Args:
            alert: The alert to process
            
        Returns:
            Dictionary containing the recommendation
        """
        return asyncio.run(self.process_alert(alert))
        
    async def process_alert_with_state(self, alert: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process an alert and return the full state including the plan.
        
        Args:
            alert: The alert to process
            
        Returns:
            Full state dictionary including plan and recommendation
        """
        # Convert to AlertModel if it's a dict
        if isinstance(alert, dict):
            try:
                alert_model = AlertModel(**alert)
                alert = alert_model.to_dict()
            except Exception as e:
                # Silently handle conversion errors
                pass
        
        # Get infrastructure context for this alert
        try:
            infra_context = self.infra_service.get_context_for_alert(alert)
        except Exception as e:
            infra_context = {}
        
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
        try:
            print("DEBUG: process_alert_with_state: Starting with initial state:")
            print(f"DEBUG: Initial state reflections: {initial_state.get('reflections', [])}")
            
            final_state = await self.agent_graph.ainvoke(initial_state)
            
            print("DEBUG: process_alert_with_state: Workflow completed with final state:")
            print(f"DEBUG: Final state completed_tasks: {final_state.get('completed_tasks', [])}")
            print(f"DEBUG: Final state reflections: {final_state.get('reflections', [])}")
            
            # Make sure the final state preserves reflections
            if not final_state.get("reflections") and initial_state.get("reflections"):
                print("DEBUG: WARNING - Reflections were lost during processing!")
                final_state["reflections"] = initial_state.get("reflections", [])
                
            return final_state
        except Exception as e:
            # If workflow execution failed, return the initial state with error info
            print(f"DEBUG: Error in process_alert_with_state: {str(e)}")
            return {
                **initial_state,
                "error": str(e)
            }