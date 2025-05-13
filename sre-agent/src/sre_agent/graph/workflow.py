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
    # Let's create debug versions of functions first
    
    # Debug wrapper for determine_next_task
    def wrapped_determine_next_task(state: AgentState) -> str:
        result = determine_next_task(state)
        print(f"DEBUG: determine_next_task: task={result}")
        return result

    # Debug wrapper for reflect
    def wrapped_reflect(state):
        print(f"DEBUG: reflect ENTER: current_task={state.get('current_task')}")
        print(f"DEBUG: reflect ENTER: reflections={state.get('reflections', [])}")
        result = reflect(state)
        print(f"DEBUG: reflect EXIT: reflections={result.get('reflections', [])}")
        return result
        
    # Initialize the graph with the agent state
    workflow = StateGraph(AgentState)
    
    # Add nodes with wrapped functions where needed
    workflow.add_node("create_plan", create_plan)
    workflow.add_node("execute_task", execute_task)
    workflow.add_node("rag_lookup", rag_lookup)
    workflow.add_node("reflect", wrapped_reflect)  # Use our wrapped version
    workflow.add_node("generate_recommendation", generate_recommendation)
    
    # Modify determine_next_task to return a state update with current_task set
    workflow.add_node("determine_next_task", lambda state: {
        "current_task": wrapped_determine_next_task(state)
    })
    
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
    
    # We don't need the debug wrappers for nodes since we've already added the wrapped versions
    
    # Create a custom router function to force going through the reflect node
    def rag_lookup_router(state):
        print("DEBUG: rag_lookup_router called - forcing path through reflect node")
        return "reflect"
        
    def execute_task_router(state):
        print("DEBUG: execute_task_router called - forcing path through reflect node")
        return "reflect"
    
    # After RAG lookup or executing a task, always reflect (using routers)
    workflow.add_conditional_edges(
        "rag_lookup",
        {
            "reflect": lambda state: True  # Always go to reflect after rag_lookup
        }
    )
    
    workflow.add_conditional_edges(
        "execute_task",
        {
            "reflect": lambda state: True  # Always go to reflect after execute_task
        }
    )
    
    # After reflection, determine the next task again
    workflow.add_edge("reflect", "determine_next_task")
    
    # After generating recommendation, end the workflow
    workflow.add_edge("generate_recommendation", END)
    
    # Compile the graph
    return workflow.compile()