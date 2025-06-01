"""Simple Planning Agent for SRE Orchestration."""

from typing import List, Dict, Any, Optional
from openai import OpenAI
from orchestration_agent.utils.orchestrator_core import OrchestratorCore
from orchestration_agent.utils.interfaces import ExecutionContext
from orchestration_agent.utils.context_utils import ContextAccumulator
from orchestration_agent.schemas.orchestrator_schemas import (
    SimplePlanSchema,
    PlanStepSchema,
    PlanningAgentOutputSchema
)


class SimplePlanningAgent:
    """
    A simple planning agent that creates multi-step plans and executes them
    using the existing orchestrator infrastructure.
    """
    
    def __init__(self, orchestrator_core: OrchestratorCore, client: OpenAI, model: str = "gpt-4"):
        """
        Initialize the planning agent.
        
        Args:
            orchestrator_core: The orchestrator core for step execution
            client: OpenAI client for LLM calls
            model: Model name for LLM calls
        """
        self.orchestrator_core = orchestrator_core
        self.client = client
        self.model = model
        self.current_plan: Optional[SimplePlanSchema] = None
    
    def create_plan(self, alert: str, context: str) -> SimplePlanSchema:
        """
        Generate a simple 3-5 step plan using LLM.
        
        Args:
            alert: The system alert to plan for
            context: Contextual information about the system
            
        Returns:
            SimplePlanSchema: The created plan
        """
        
        prompt = f"""
You are an SRE planning agent. Given this alert and context, create a logical 3-5 step plan to diagnose and resolve the issue.

Alert: {alert}
Context: {context}

Return ONLY a numbered list of steps, each step should be a clear, actionable description:
1. [First step description]
2. [Second step description]
...

Focus on: investigation → diagnosis → resolution

Guidelines:
- Start with gathering information and understanding the current state
- Progress to identifying root causes
- End with implementing solutions or escalation
- Each step should be specific and actionable
- Keep steps focused and not too broad
"""
        
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.1
            )
            
            # Parse the response into steps
            steps_text = response.choices[0].message.content.strip()
            step_descriptions = []
            
            for line in steps_text.split('\n'):
                line = line.strip()
                if line and (line[0].isdigit() or line.startswith('-')):
                    # Remove numbering and clean up
                    if '.' in line:
                        step_desc = line.split('.', 1)[-1].strip()
                    elif line.startswith('-'):
                        step_desc = line[1:].strip()
                    else:
                        step_desc = line.strip()
                    
                    if step_desc:
                        step_descriptions.append(step_desc)
            
            # Ensure we have at least one step
            if not step_descriptions:
                step_descriptions = [
                    "Investigate the alert and gather system information",
                    "Analyze findings to identify potential root causes",
                    "Implement appropriate resolution or escalation"
                ]
            
            # Create plan with steps
            steps = [PlanStepSchema(description=desc) for desc in step_descriptions]
            
            self.current_plan = SimplePlanSchema(
                alert=alert,
                context=context,
                steps=steps
            )
            
            return self.current_plan
            
        except Exception as e:
            print(f"❌ Error creating plan: {e}")
            # Fallback to default plan
            default_steps = [
                PlanStepSchema(description="Investigate the alert and gather system information"),
                PlanStepSchema(description="Analyze findings to identify potential root causes"),
                PlanStepSchema(description="Implement appropriate resolution or escalation")
            ]
            
            self.current_plan = SimplePlanSchema(
                alert=alert,
                context=context,
                steps=default_steps
            )
            
            return self.current_plan
    
    def execute_plan(self, alert: str, context: str) -> PlanningAgentOutputSchema:
        """
        Execute the complete planning workflow.
        
        Args:
            alert: The system alert to plan for
            context: Contextual information about the system
            
        Returns:
            PlanningAgentOutputSchema: Complete execution results
        """
        
        # Create the plan
        plan = self.create_plan(alert, context)
        print(f"📋 Created plan with {len(plan.steps)} steps:")
        for i, step in enumerate(plan.steps, 1):
            print(f"  {i}. {step.description}")
        print()
        
        success = True
        
        # Execute each step
        for step_index, step in enumerate(plan.steps):
            print(f"🔄 Executing Step {step_index + 1}: {step.description}")
            
            # Create execution context for this step
            execution_context = ExecutionContext(
                alert=plan.alert,
                context=plan.context,
                accumulated_knowledge=plan.accumulated_knowledge,
                step_id=f"step_{step_index + 1}",
                step_description=step.description
            )
            
            try:
                # Execute step using orchestrator (without memory reset)
                result = self.orchestrator_core.execute_with_context(execution_context)
                
                # Extract orchestrator output and tool response
                orchestrator_output = result.get('orchestrator_output')
                tool_response = result.get('tool_response')
                
                # Update step status
                step.status = "completed"
                step.result = result
                
                # Get tool name from orchestrator output
                tool_name = orchestrator_output.tool if orchestrator_output else 'unknown'
                
                # Update accumulated knowledge
                step_summary = ContextAccumulator.summarize_step_result(
                    step.description,
                    tool_response,
                    tool_name
                )
                
                plan.accumulated_knowledge = ContextAccumulator.merge_contexts(
                    plan.accumulated_knowledge,
                    step_summary
                )
                
                print(f"✅ Step {step_index + 1} completed")
                print(f"   Tool used: {tool_name}")
                print(f"   Summary: {step_summary[:100]}...")
                print()
                
                # Check if we got a final answer
                if tool_name == 'final_answer':
                    print("🎯 Final answer reached, stopping execution")
                    break
                    
            except Exception as e:
                step.status = "failed"
                step.result = {"error": str(e)}
                print(f"❌ Step {step_index + 1} failed: {e}")
                success = False
                break
        
        # Generate final summary
        summary = self.generate_summary()
        
        return PlanningAgentOutputSchema(
            plan=plan,
            summary=summary,
            success=success
        )
    
    def generate_summary(self) -> str:
        """Generate a summary of the planning execution."""
        if not self.current_plan:
            return "No plan was executed"
        
        plan = self.current_plan
        completed_steps = [s for s in plan.steps if s.status == "completed"]
        failed_steps = [s for s in plan.steps if s.status == "failed"]
        
        summary = f"""# Planning Agent Execution Summary

## Original Alert
{plan.alert}

## Context
{plan.context}

## Steps Executed"""
        
        for i, step in enumerate(plan.steps, 1):
            status_emoji = "✅" if step.status == "completed" else "❌" if step.status == "failed" else "⏸️"
            summary += f"\n{i}. {status_emoji} {step.description}"
            
            if step.result and step.status == "completed":
                tool_name = step.result.get('tool_name', 'unknown')
                summary += f"\n   → Used: {tool_name}"
        
        summary += f"""

## Results
- Completed: {len(completed_steps)}/{len(plan.steps)} steps
- Failed: {len(failed_steps)} steps

## Key Findings
{plan.accumulated_knowledge if plan.accumulated_knowledge else "No significant findings accumulated."}
"""
        
        return summary