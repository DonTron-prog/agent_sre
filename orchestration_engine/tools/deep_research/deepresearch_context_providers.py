from dataclasses import dataclass
from datetime import datetime
from typing import List
from atomic_agents.lib.components.system_prompt_generator import SystemPromptContextProviderBase


@dataclass
class ContentItem:
    content: str
    url: str


class ScrapedContentContextProvider(SystemPromptContextProviderBase):
    def __init__(self, title: str):
        super().__init__(title=title)
        self.content_items: List[ContentItem] = []

    def get_info(self) -> str:
        # Limit context to prevent token overflow
        MAX_CONTEXT_CHARS = 50000  # ~12,500 tokens, leaving room for system prompt and response
        
        if not self.content_items:
            return "No content available."
        
        content_parts = []
        current_chars = 0
        
        for idx, item in enumerate(self.content_items, 1):
            source_content = f"Source {idx}:\nURL: {item.url}\nContent:\n{item.content}\n{'-' * 80}"
            
            # Check if adding this content would exceed the limit
            if current_chars + len(source_content) > MAX_CONTEXT_CHARS:
                # If this is the first item and it's too large, truncate it
                if idx == 1:
                    remaining_chars = MAX_CONTEXT_CHARS - current_chars - 200  # Leave room for truncation message
                    if remaining_chars > 0:
                        truncated_content = item.content[:remaining_chars] + "... [TRUNCATED]"
                        source_content = f"Source {idx}:\nURL: {item.url}\nContent:\n{truncated_content}\n{'-' * 80}"
                        content_parts.append(source_content)
                break
            
            content_parts.append(source_content)
            current_chars += len(source_content)
        
        result = "\n\n".join(content_parts)
        
        # Add truncation notice if we didn't include all items
        if len(content_parts) < len(self.content_items):
            result += f"\n\n[NOTE: Showing {len(content_parts)} of {len(self.content_items)} sources due to context limits]"
        
        return result


class CurrentDateContextProvider(SystemPromptContextProviderBase):
    def __init__(self, title: str, date_format: str = "%A %B %d, %Y"):
        super().__init__(title=title)
        self.date_format = date_format

    def get_info(self) -> str:
        return f"The current date in the format {self.date_format} is {datetime.now().strftime(self.date_format)}."
