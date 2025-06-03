"""Execution Orchestrator for running plans using the orchestration engine."""

from typing import List, Dict, Any
from pydantic import Field
from atomic_agents.lib.base.base_io_schema import BaseIOSchema
from orchestration_engine.utils.orchestrator_core import OrchestratorCore
from orchestration_engine.utils.interfaces import ExecutionContext
from orchestration_engine.utils.context_utils import ContextAccumulator
from controllers.planning_agent.planner_schemas import SimplePlanSchema, PlanStepSchema


class ExecutionOrchestratorInputSchema(BaseIOSchema):
    """Input schema for the Execution Orchestrator."""
    
    plan: SimplePlanSchema = Field(..., description="The plan to execute")


class StepExecutionResult(BaseIOSchema):
    """Result of executing a single plan step."""
    
    step_index: int = Field(..., description="Index of the executed step")
    step_description: str = Field(..., description="Description of the step")
    status: str = Field(..., description="Execution status: completed, failed")
    tool_used: str = Field(..., description="Name of the tool that was used")
    result_summary: str = Field(..., description="Summary of the step execution result")
    full_result: Dict[str, Any] = Field(..., description="Complete result data from the step")


class ExecutionOrchestratorOutputSchema(BaseIOSchema):
    """Output schema for the Execution Orchestrator."""
    
    executed_steps: List[StepExecutionResult] = Field(..., description="Results from all executed steps")
    final_summary: str = Field(..., description="Overall execution summary")
    success: bool = Field(..., description="Whether the overall execution was successful")
    accumulated_knowledge: str = Field(..., description="Accumulated knowledge from all steps")


class ExecutionOrchestrator:
    """
    Atomic execution orchestrator that runs plans using the orchestration engine.
    
    This component is responsible for executing plans step-by-step while maintaining
    context and accumulating knowledge across steps.
    """
    
    def __init__(self, orchestrator_core: OrchestratorCore):
        """
        Initialize the Execution Orchestrator.
        
        Args:
            orchestrator_core: The orchestrator core for step execution
        """
        self.orchestrator_core = orchestrator_core
        self.input_schema = ExecutionOrchestratorInputSchema
        self.output_schema = ExecutionOrchestratorOutputSchema
    
    def run(self, params: ExecutionOrchestratorInputSchema) -> ExecutionOrchestratorOutputSchema:
        """
        Execute a plan step by step.
        
        Args:
            params: Input parameters containing the plan to execute
            
        Returns:
            ExecutionOrchestratorOutputSchema: Complete execution results
        """
        plan = params.plan
        executed_steps = []
        success = True
        accumulated_knowledge = plan.accumulated_knowledge
        
        print(f"🚀 Starting execution of plan with {len(plan.steps)} steps")
        
        # Execute each step
        for step_index, step in enumerate(plan.steps):
            print(f"\n🔄 Executing Step {step_index + 1}: {step.description}")
            
            try:
                # Create execution context for this step
                execution_context = ExecutionContext(
                    alert=plan.alert,
                    context=plan.context,
                    accumulated_knowledge=accumulated_knowledge,
                    step_id=f"step_{step_index + 1}",
                    step_description=step.description
                )
                
                # Execute step using orchestrator
                result = self.orchestrator_core.execute_with_context(execution_context)
                
                # Extract orchestrator output and tool response
                orchestrator_output = result.get('orchestrator_output')
                tool_response = result.get('tool_response')
                
                # Get tool name from orchestrator output
                tool_name = orchestrator_output.tool if orchestrator_output else 'unknown'
                
                # Update accumulated knowledge
                step_summary = ContextAccumulator.summarize_step_result(
                    step.description,
                    tool_response,
                    tool_name
                )
                
                accumulated_knowledge = ContextAccumulator.merge_contexts(
                    accumulated_knowledge,
                    step_summary
                )
                
                # Create step execution result
                step_result = StepExecutionResult(
                    step_index=step_index,
                    step_description=step.description,
                    status="completed",
                    tool_used=tool_name,
                    result_summary=step_summary[:200] + "..." if len(step_summary) > 200 else step_summary,
                    full_result=result
                )
                
                executed_steps.append(step_result)
                
                print(f"✅ Step {step_index + 1} completed using {tool_name}")
                print(f"   Summary: {step_summary[:100]}...")
                
                # Check if we got a final answer
                if tool_name == 'final_answer':
                    print("🎯 Final answer reached, stopping execution")
                    break
                    
            except Exception as e:
                print(f"❌ Step {step_index + 1} failed: {e}")
                
                # Create failed step result
                step_result = StepExecutionResult(
                    step_index=step_index,
                    step_description=step.description,
                    status="failed",
                    tool_used="none",
                    result_summary=f"Step failed with error: {str(e)}",
                    full_result={"error": str(e)}
                )
                
                executed_steps.append(step_result)
                success = False
                break
        
        # Generate final summary
        final_summary = self._generate_execution_summary(plan, executed_steps, success)
        
        return ExecutionOrchestratorOutputSchema(
            executed_steps=executed_steps,
            final_summary=final_summary,
            success=success,
            accumulated_knowledge=accumulated_knowledge
        )
    
    def _generate_execution_summary(
        self, 
        plan: SimplePlanSchema, 
        executed_steps: List[StepExecutionResult], 
        success: bool
    ) -> str:
        """Generate a comprehensive execution summary."""
        
        completed_steps = [s for s in executed_steps if s.status == "completed"]
        failed_steps = [s for s in executed_steps if s.status == "failed"]
        
        summary = f"""# Plan Execution Summary

## Original Alert
{plan.alert}

## Context
{plan.context}

## Execution Results
- **Status**: {'✅ Success' if success else '❌ Failed'}
- **Steps Completed**: {len(completed_steps)}/{len(plan.steps)}
- **Steps Failed**: {len(failed_steps)}

## Step Details"""
        
        for step_result in executed_steps:
            status_emoji = "✅" if step_result.status == "completed" else "❌"
            summary += f"\n{step_result.step_index + 1}. {status_emoji} {step_result.step_description}"
            summary += f"\n   → Tool Used: {step_result.tool_used}"
            summary += f"\n   → Result: {step_result.result_summary}"
        
        if plan.accumulated_knowledge:
            summary += f"\n\n## Key Findings\n{plan.accumulated_knowledge}"
        
        return summary


# Example usage
if __name__ == "__main__":
    from rich.console import Console
    from datetime import datetime
    
    console = Console()
    
    # Example plan for testing
    test_plan = SimplePlanSchema(
        alert="Test alert",
        context="Test context",
        steps=[
            PlanStepSchema(description="Investigate system status"),
            PlanStepSchema(description="Check error logs"),
            PlanStepSchema(description="Identify root cause")
        ],
        created_at=datetime.now()
    )
    
    console.print("[bold blue]Example Execution Orchestrator created[/bold blue]")
    console.print("Note: Requires OrchestratorCore instance to run actual execution")