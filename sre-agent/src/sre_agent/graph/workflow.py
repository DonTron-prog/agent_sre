"""
LangGraph workflow for the SRE agent.
"""

from langgraph.graph import StateGraph, END
from typing import Dict, Any

from sre_agent.models.state import AgentState
from sre_agent.graph.nodes.planning import create_plan, determine_next_task
from sre_agent.graph.nodes.rag_lookup import rag_lookup
from sre_agent.graph.nodes.execution import execute_task
from sre_agent.graph.nodes.reflection import reflect
from sre_agent.graph.nodes.recommendation import generate_recommendation


def create_agent_graph():
    """
    Create the LangGraph workflow for the SRE agent.
    
    This function sets up the nodes and edges for the workflow graph,
    defining how the agent moves through different steps of processing
    an alert.
    
    Returns:
        A compiled StateGraph that can be executed
    """
    # Initialize the graph with the agent state
    workflow = StateGraph(AgentState)
    
    # Add nodes
    workflow.add_node("create_plan", create_plan)
    workflow.add_node("execute_task", execute_task)
    workflow.add_node("rag_lookup", rag_lookup)
    workflow.add_node("reflect", reflect)
    workflow.add_node("generate_recommendation", generate_recommendation)
    workflow.add_node("determine_next_task", lambda state: {"current_task": determine_next_task(state)})
    
    # Define the workflow edges
    
    # Start with creating a plan
    workflow.set_entry_point("create_plan")
    
    # After creating a plan, determine the next task
    workflow.add_edge("create_plan", "determine_next_task")
    
    # Based on the determined task, route to appropriate node
    workflow.add_conditional_edges(
        "determine_next_task",
        {
            "rag_lookup": lambda state: state.get("current_task") == "rag_lookup" or state.get("current_task") == "Check similar past incidents",
            "execute_task": lambda state: state.get("current_task") == "execute_task",
            "generate_recommendation": lambda state: state.get("current_task") == "generate_recommendation",
        }
    )
    
    # After RAG lookup or executing a task, reflect
    workflow.add_edge("rag_lookup", "reflect")
    workflow.add_edge("execute_task", "reflect")
    
    # After reflection, determine the next task again
    workflow.add_edge("reflect", "determine_next_task")
    
    # After generating recommendation, end the workflow
    workflow.add_edge("generate_recommendation", END)
    
    # Compile the graph
    return workflow.compile()