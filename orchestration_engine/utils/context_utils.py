"""Context management utilities for the orchestration agent."""

from typing import Any, Optional
import json
from datetime import datetime
from atomic_agents.lib.components.system_prompt_generator import SystemPromptContextProviderBase


class ContextAccumulator:
    """Utility for managing accumulated knowledge across planning steps."""
    
    @staticmethod
    def summarize_step_result(step_description: str, tool_output: Any, tool_name: str) -> str:
        """Create concise summary of a step's outcome.
        
        Args:
            step_description: Description of what the step was trying to accomplish
            tool_output: The output from the tool execution
            tool_name: Name of the tool that was executed
            
        Returns:
            Concise summary of the step's outcome
        """
        try:
            # Handle different tool output formats
            if hasattr(tool_output, 'model_dump'):
                output_dict = tool_output.model_dump()
            elif hasattr(tool_output, '__dict__'):
                output_dict = tool_output.__dict__
            else:
                output_dict = str(tool_output)
            
            # Extract key information based on tool type
            if tool_name in ("search", "web-search"):
                if isinstance(output_dict, dict) and 'results' in output_dict:
                    num_results = len(output_dict.get('results', []))
                    summary = f"Web search found {num_results} results"
                    if num_results > 0:
                        first_result = output_dict['results'][0]
                        if 'title' in first_result:
                            summary += f", top result: {first_result['title'][:100]}..."
                else:
                    summary = "Web search completed"
                    
            elif tool_name == "rag":
                if isinstance(output_dict, dict) and 'answer' in output_dict:
                    answer = output_dict['answer'][:200] + "..." if len(output_dict['answer']) > 200 else output_dict['answer']
                    summary = f"RAG search found: {answer}"
                else:
                    summary = "RAG search completed"
                    
            elif tool_name == "deep-research":
                if isinstance(output_dict, dict) and 'answer' in output_dict:
                    answer = output_dict['answer'][:200] + "..." if len(output_dict['answer']) > 200 else output_dict['answer']
                    summary = f"Deep research analysis: {answer}"
                else:
                    summary = "Deep research completed"
                    
            elif tool_name == "calculator":
                if isinstance(output_dict, dict) and 'result' in output_dict:
                    summary = f"Calculation result: {output_dict['result']}"
                else:
                    summary = "Calculation completed"
            else:
                summary = f"Tool '{tool_name}' executed successfully"
                
            return f"Step: {step_description} | Result: {summary}"
            
        except Exception as e:
            return f"Step: {step_description} | Result: Tool execution completed (summary generation failed: {str(e)})"
    
    @staticmethod
    def merge_contexts(existing_context: str, new_information: str, max_length: int = 2000) -> str:
        """Intelligently merge new information with existing context.
        
        Args:
            existing_context: Current accumulated context
            new_information: New information to add
            max_length: Maximum length of the merged context
            
        Returns:
            Merged context, potentially truncated if too long
        """
        if not existing_context:
            return new_information[:max_length] if len(new_information) > max_length else new_information
        
        if not new_information:
            return existing_context
        
        # Simple merge with separator
        merged = f"{existing_context}\n\n{new_information}"
        
        # Truncate if too long, keeping the most recent information
        if len(merged) > max_length:
            # Keep the new information and truncate the existing context
            available_space = max_length - len(new_information) - 10  # 10 chars for separator
            if available_space > 0:
                truncated_existing = existing_context[-available_space:]
                merged = f"...{truncated_existing}\n\n{new_information}"
            else:
                # If new information is too long, just use it
                merged = new_information[:max_length]
        
        return merged
    
    @staticmethod
    def extract_key_findings(accumulated_context: str, max_findings: int = 5) -> list[str]:
        """Extract key findings from accumulated context.
        
        Args:
            accumulated_context: The full accumulated context
            max_findings: Maximum number of key findings to extract
            
        Returns:
            List of key findings extracted from the context
        """
        if not accumulated_context:
            return []
        
        # Simple extraction based on step results
        findings = []
        lines = accumulated_context.split('\n')
        
        for line in lines:
            line = line.strip()
            if line.startswith('Step:') and 'Result:' in line:
                # Extract the result part
                result_part = line.split('Result:', 1)[1].strip()
                if result_part and len(result_part) > 10:  # Only meaningful results
                    findings.append(result_part)
                    if len(findings) >= max_findings:
                        break
        
        return findings
    
    @staticmethod
    def create_focused_context(original_alert: str, original_context: str, 
                             accumulated_knowledge: str, current_step_description: str) -> tuple[str, str]:
        """Create focused alert and context for a specific step.
        
        Args:
            original_alert: The original system alert
            original_context: The original system context
            accumulated_knowledge: Knowledge accumulated from previous steps
            current_step_description: Description of the current step
            
        Returns:
            Tuple of (focused_alert, focused_context) for the current step
        """
        # Create a focused alert that includes the step context
        focused_alert = f"{original_alert} (Current focus: {current_step_description})"
        
        # Create focused context that combines original context with key findings
        key_findings = ContextAccumulator.extract_key_findings(accumulated_knowledge, max_findings=3)
        
        focused_context = original_context
        if key_findings:
            findings_text = " | ".join(key_findings)
            focused_context += f"\n\nPrevious investigation findings: {findings_text}"
        
        return focused_alert, focused_context


class CurrentDateProvider(SystemPromptContextProviderBase):
    """Reusable current date context provider."""
    
    def __init__(self, title: str = "Current Date", date_format: str = "%Y-%m-%d"):
        super().__init__(title)
        self.date_format = date_format
    
    def get_info(self) -> str:
        current_date = datetime.now().strftime(self.date_format)
        return f"Current date in format {self.date_format}: {current_date}"