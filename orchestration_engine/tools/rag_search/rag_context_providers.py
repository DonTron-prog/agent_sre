from typing import List
from dataclasses import dataclass
from atomic_agents.lib.components.system_prompt_generator import SystemPromptContextProviderBase

@dataclass
class ChunkItem:
    content: str
    metadata: dict

class RAGContextProvider(SystemPromptContextProviderBase):
    def __init__(self, title: str):
        super().__init__(title=title)
        self.chunks: List[ChunkItem] = []

    def get_info(self) -> str:
        if not self.chunks:
            return "No context chunks available."
        return "\n\n".join(
            [
                f"Chunk {idx}:\nSource: {item.metadata.get('source', 'N/A')}\nContent:\n{item.content}\n{'-' * 20}"
                for idx, item in enumerate(self.chunks, 1)
            ]
        )