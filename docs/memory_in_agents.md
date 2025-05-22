# atomic agents memory cli

One of **the most useful** features in any AI assistant is undoubtedly the ability to have a **persistent long-term memory**. Whether the goal is to learn more about the user, adjust the AI’s behavior based on user preference or to remember important events, endowing your AI assistant / Agent / … with some form of **long-term, persistent memory storage** is one of the core necessities to achieve this.

**Before we dive in:**

- We will be using [**_Atomic Agents_**](https://github.com/BrainBlend-AI/atomic-agents) to build the actual agents, which is an amazing developer centric framework that **greatly simplifies** and **streamlines** **Agentic AI development**. While this article will completely stand on its own, if you want the introduction to _Atomic Agents_ first, [**_check out this article_**](https://medium.com/p/e34e0b6c8068) **_or_** [**_have a look at some of the examples!_**](https://github.com/BrainBlend-AI/atomic-agents/tree/main/atomic-examples)
- For vector storage, I’ll be using [**_ChromaDB_**](https://www.trychroma.com/) but there is no reason you can’t adapt it to use whatever vector database you want as we don’t really use any special functionality that is only available in _ChromaDB_.
- **Rather than a step-by-step tutorial**, this will be more of a project breakdown in order to be able to focus on what’s important, and not **bog you down** with “Now let’s install package X”, “Now let’s import it”, …

The full project is [available on GitHub right here](https://github.com/KennyVaneetvelde/persistent-memory-agent-example) so **feel free to grab it**, install its dependencies as per the README instructions, **give it a spin** to get a feel for it, and follow along in this guide!

Without further ado, **let’s go!**

# The Goal

This example **by no means** tries to be a **complete implementation** of all the ways you can do **a long-term memory**. In fact, it is **rather simplistic**. But, **as with anything** in the **_Atomic Agents_ framework**, it is made to be **easy to expand upon** and to modify to your own requirements.

Have a look at the sample interaction below, demonstrating **new memory formation**, and how the assistant **was already aware of my name** through previous interaction.

![](https://miro.medium.com/v2/resize:fit:1000/1*qpq_ptuLcx9Oj3dzPVJ0zA.png)

A sample interaction between the AI assistant and the Author

# Installation and Setup

Before we dive into the implementation, **let’s set up the development environment**. This project uses _Poetry_ for dependency management, making it easy to get started.

**Clone the Repository**:

git clone https://github.com/KennyVaneetvelde/persistent-memory-agent-example  
cd persistent-memory-agent-example

**Install Poetry** (if you haven’t already):

pipx install poetry

**Install Dependencies**:

poetry install

This will install all required packages:

[tool.poetry.dependencies]  
python = "^3.10"  
atomic-agents = "^1.0.15"  
rich = "^13.9.4"  
instructor = "^1.6.4"  
openai = "^1.54.4"  
pydantic = "^2.9.2"  
chromadb = "^0.5.18"  
numpy = "^2.1.3"

**Set Up Environment Variables**:  
Create a `.env` file in the project root with your OpenAI API key:

OPENAI_API_KEY=your_api_key_here

And with that out of the way, you should be good to go! You can run the example and get a feel of how it works by running the **_main.py_** inside the **_chat_with_memory_** folder.

Great! So now we can move on to **the breakdown.**

# Overview

This project has a few **key components** that make up everything:

- **Memory models**: Define different types of memories we want to store
- **Memory tools**: Using _ChromaDB_ as our vector database, we have a memory query tool, and a memory storage tool
- **Context providers**: Inject relevant memories into agent conversations
- **Memory Formation agent**: An agent that reasons about and decides what to remember
- **Chat Agent**: The main conversational agent that uses the memories. This is the agent that the user will be conversing with.

# Memory Models

![](https://miro.medium.com/v2/resize:fit:700/1*ghyf3rEpxkSniL55bkks3A.png)

The memory system uses **specialized memory types** for different kinds of information. Here’s the complete implementation:

```python
from typing import Literal  
from pydantic import Field  
from datetime import datetime, timezone  
from atomic_agents.lib.base.base_io_schema import BaseIOSchema  
  
  
class BaseMemory(BaseIOSchema):  
    """Base class for all memory types"""  
    content: str = Field(..., description="Content of the memory")  
    timestamp: str = Field(  
        default_factory=lambda: datetime.now(timezone.utc).isoformat(),  
        description="ISO format timestamp of when the memory was created",  
    )  
  
class CoreBioMemory(BaseMemory):  
    """Core biographical information about the user"""  
    memory_type: Literal["core_bio"] = Field(default="core_bio")  
  
class EventMemory(BaseMemory):  
    """Information about significant events or experiences"""  
    memory_type: Literal["event"] = Field(default="event")  
  
class WorkProjectMemory(BaseMemory):  
    """Information about work projects and tasks"""  
    memory_type: Literal["work_project"] = Field(default="work_project")

Each memory type serves a specific purpose:

- **CoreBioMemory**: Stores fundamental user information (background, preferences, traits)
- **EventMemory**: Records info about significant events and experiences
- **WorkProjectMemory**: Tracks facts about professional projects and accomplishments
```

The keen eye might have noticed already that each of these classes has a memory_type which can only ever be a single value. What’s the use of this? Well, I noticed that, not due to a bug in any framework, but **due to a bug in OpenAI** itself, if this `memory_type`was not specified it would just only ever pick the first one, in this case the **CoreBioMemory.**

But, **none of this is really an issue**, as little things like having that memory type do tend to **steer the LLMs in the right direction**, even if they don’t need it. This is especially useful since **you can use any other LLM provider other than OpenAI**, or even run it locally

_“Why do we even need multiple memory types?”_ you might ask. **This is a personal preference**, really, and y**ou could get by with just a single memory type**. But I find it handy to be able to store different kinds so that we can query them separately if needed and this will provide **a much more solid base for agent personalization**, I think.

That being said, you can customize this completely to your liking, even having 10 different memory types if you really want to, without having to modify any other code!

# Memory Storage and Retrieval

Next, we have where we will actually store our memory. As I mentioned at the start of this guide, **we will use _ChromaDB_ as our vector storage**. I will not show the actual _ChromaDB_ service, since that is not very interesting for the sake of this guide. Instead, let’s go over the two _Atomic Agent Tools_ that will be consuming the _ChromaDB_ service.

Now, remembering how within _Atomic Agents_ each Agent and each Tool adheres to the same structure of **Input -> Processing -> Output** through the use of strict input & output schemas. This allows to easily chain agents or tools together, or even just provide strict development guidelines & structure to adhere to, as how we will mainly use it here.

## Memory Storage Tool

```python
from pydantic import Field  
  
from atomic_agents.lib.base.base_tool import BaseTool, BaseToolConfig  
from atomic_agents.lib.base.base_io_schema import BaseIOSchema  
from chat_with_memory.services.chroma_db import ChromaDBService  
from chat_with_memory.tools.memory_models import (  
    BaseMemory,  
    CoreBioMemory,  
    EventMemory,  
    WorkProjectMemory,  
)  
  
  
class MemoryStoreInputSchema(BaseIOSchema):  
    """Schema for storing memories"""  
  
    memory: BaseMemory = Field(..., description="Memory to store")  
  
  
class MemoryStoreOutputSchema(BaseIOSchema):  
    """Schema for memory storage output"""  
  
    memory: BaseMemory = Field(..., description="Stored memory with generated ID")  
  
  
class MemoryStoreConfig(BaseToolConfig):  
    """Configuration for the MemoryStoreTool"""  
  
    collection_name: str = Field(  
        default="chat_memories", description="Name of the ChromaDB collection to use"  
    )  
    persist_directory: str = Field(  
        default="./chroma_db", description="Directory to persist ChromaDB data"  
    )  
  
  
class MemoryStoreTool(BaseTool):  
    """Tool for storing chat memories using ChromaDB"""  
  
    input_schema = MemoryStoreInputSchema  
    output_schema = MemoryStoreOutputSchema  
  
    def __init__(self, config: MemoryStoreConfig = MemoryStoreConfig()):  
        super().__init__(config)  
        self.db_service = ChromaDBService(  
            collection_name=config.collection_name,  
            persist_directory=config.persist_directory,  
        )  
  
    def run(self, params: MemoryStoreInputSchema) -> MemoryStoreOutputSchema:  
        """Store a new memory in ChromaDB"""  
        memory = params.memory  
  
        # Map memory types to their storage representation  
        memory_type_mapping = {  
            CoreBioMemory: "core_memory",  
            EventMemory: "event_memory",  
            WorkProjectMemory: "work_project_memory",  
        }  
  
        # Get the specific memory type  
        memory_type = memory_type_mapping.get(type(memory), "base_memory")  
  
        # Base metadata with all values as strings  
        metadata = {  
            "timestamp": memory.timestamp,  
            "memory_type": memory_type,  
        }  
  
        self.db_service.add_documents(  
            documents=[memory.content], metadatas=[metadata]  
        )  
  
        return MemoryStoreOutputSchema(memory=memory.model_copy())
```
## Memory Retrieval Tool

```python
from typing import List, Optional, Literal, Union  
from pydantic import Field  
from datetime import datetime  
import json  
  
from atomic_agents.lib.base.base_tool import BaseTool, BaseToolConfig  
from atomic_agents.lib.base.base_io_schema import BaseIOSchema  
from chat_with_memory.services.chroma_db import ChromaDBService, QueryResult  
from chat_with_memory.tools.memory_models import (  
    CoreBioMemory,  
    EventMemory,  
    WorkProjectMemory,  
    BaseMemory,  
)  
  
  
class MemoryQueryInputSchema(BaseIOSchema):  
    """Schema for querying memories"""  
  
    query: str = Field(..., description="Query string to find relevant memories")  
    n_results: Optional[int] = Field(  
        default=2, description="Number of similar memories to retrieve"  
    )  
    memory_type: Optional[str] = Field(  
        default=None, description="Optional memory type to filter memories"  
    )  
  
  
class MemoryQueryOutputSchema(BaseIOSchema):  
    """Schema for memory query output"""  
  
    memories: List[BaseMemory] = Field(  
        default_factory=list, description="Retrieved memories"  
    )  
  
  
class MemoryQueryConfig(BaseToolConfig):  
    """Configuration for the MemoryQueryTool"""  
  
    collection_name: str = Field(  
        default="chat_memories", description="Name of the ChromaDB collection to use"  
    )  
    persist_directory: str = Field(  
        default="./chroma_db", description="Directory to persist ChromaDB data"  
    )  
  
  
class MemoryQueryTool(BaseTool):  
    """Tool for querying chat memories using ChromaDB"""  
  
    input_schema = MemoryQueryInputSchema  
    output_schema = MemoryQueryOutputSchema  
  
    def __init__(self, config: MemoryQueryConfig = MemoryQueryConfig()):  
        super().__init__(config)  
        self.db_service = ChromaDBService(  
            collection_name=config.collection_name,  
            persist_directory=config.persist_directory,  
        )  
  
    def run(self, params: MemoryQueryInputSchema) -> MemoryQueryOutputSchema:  
        """Query for relevant memories using semantic search"""  
        where_filter = None  
        if params.memory_type:  
            # Map query types to stored types  
            type_mapping = {  
                "core": "core_memory",  
                "event": "event_memory",  
                "work_project": "work_project_memory",  
            }  
            memory_type = type_mapping[params.memory_type]  
            where_filter = {"memory_type": memory_type}  
  
        try:  
            results: QueryResult = self.db_service.query(  
                query_text=params.query,  
                n_results=params.n_results,  
                where=where_filter,  
            )  
  
            # Map stored types back to memory classes  
            memory_class_mapping = {  
                "core_memory": CoreBioMemory,  
                "event_memory": EventMemory,  
                "work_project_memory": WorkProjectMemory,  
                "base_memory": BaseMemory,  
            }  
  
            memories = []  
            if results["documents"]:  
                for doc, meta, id_ in zip(  
                    results["documents"], results["metadatas"], results["ids"]  
                ):  
                    memory_type = meta.get("memory_type", "base_memory")  
                    memory_class = memory_class_mapping[memory_type]  
  
                    base_data = {  
                        "id": id_,  
                        "content": doc,  
                        "timestamp": meta["timestamp"],  
                    }  
                    memories.append(memory_class(**base_data))  
  
            return MemoryQueryOutputSchema(memories=memories)  
        except Exception as e:  
            print(f"Query error: {str(e)}")  
            return MemoryQueryOutputSchema(memories=[])
```

These tools work together to provide:

- **Type-Safe Memory Storage**: Each memory is stored with its specific type and metadata
- **Flexible Querying**: Search by content similarity or filter by memory type
- **Automatic Type Conversion**: Results are automatically converted back to the appropriate memory types

As you can see, both of them have an **input schema**, an **output schema**, and the main tool class **always** has a **_run_** method that takes in that input schema, and outputs the output schema.

# Context Providers

So how do we get these memories into the agents? **This is where _Atomic Agents’ Context Providers_ come into play**

Context providers in _Atomic Agents_ are simply an easy and modular way to inject (live) information into the system prompt. Here’s how we implement them:

```python
from atomic_agents.lib.components.system_prompt_generator import SystemPromptContextProviderBase  
  
class MemoryContextProvider(SystemPromptContextProviderBase):  
    """Provides relevant memories as context for the agent"""  
    def __init__(self, memories: List[BaseMemory]):  
        super().__init__(title="Relevant Memories")  
        self.memories = memories  
    def get_info(self) -> str:  
        if not self.memories:  
            return "No relevant memories found."  
          
        memory_strings = []  
        for memory in self.memories:  
            memory_strings.append(f"- {memory.content} ({memory.memory_type})")  
          
        return "Previous memories:\n" + "\n".join(memory_strings)
```

Each context provider has a **get_info()** method that returns a string with the information that should be added to the system prompt. In this case, it will format the memories. The output of this method will look something like this:

Previous memories:  
- User speaks Portuguese, Japanese, and English fluently (core_memory)  
- User has a PhD in Quantum Computing from MIT (event_memory)  
- User has been working in quantum cryptography ever since (work_project_memory)

Ok great so with those basic building blocks out of the way, all that is left to do is creating the actual agents!

# Memory Formation Agent

The most important agent for the purposes of this article, would be the **Memory Formation Agent**, which will look at the current conversation, existing memories, and outputs **which memory can be formed based on this.**

```python
import instructor  
from openai import OpenAI  
import os  
from typing import List, Literal, Optional, Union, Dict, Any  
from pydantic import Field  
from datetime import datetime, timezone  
  
from atomic_agents.agents.base_agent import BaseAgent, BaseAgentConfig, BaseIOSchema  
from atomic_agents.lib.components.system_prompt_generator import SystemPromptGenerator  
from atomic_agents.lib.components.agent_memory import AgentMemory  
from chat_with_memory.tools.memory_models import (  
    BaseMemory,  
    CoreBioMemory,  
    EventMemory,  
    WorkProjectMemory,  
)  
from chat_with_memory.tools.memory_store_tool import (  
    MemoryStoreTool,  
    MemoryStoreInputSchema,  
)  
from chat_with_memory.tools.memory_query_tool import (  
    MemoryQueryTool,  
    MemoryQueryInputSchema,  
)  
  
  
class MemoryFormationInputSchema(BaseIOSchema):  
    """Input schema for the Memory Formation Agent."""  
  
    last_user_msg: str = Field(  
        ...,  
        description="The last message from the user in the conversation",  
    )  
    last_assistant_msg: str = Field(  
        ...,  
        description="The last message from the assistant in the conversation",  
    )  
  
  
class MemoryFormationOutputSchema(BaseIOSchema):  
    """Output schema for the Memory Formation Agent, representing the assistant's memory about the user."""  
  
    reasoning: List[str] = Field(  
        ...,  
        description="Reasoning about which memory type to pick from the list of possible memory types and why",  
        min_length=3,  
        max_length=5,  
    )  
    memories: Optional[List[CoreBioMemory | EventMemory | WorkProjectMemory]] = Field(  
        ...,  
        description="The formed memories of the assistant about the user, if anything relevant was found.",  
    )  
  
  
# Initialize the system prompt generator with more selective criteria  
memory_formation_prompt = SystemPromptGenerator(  
    background=[  
        "You are an AI specialized in identifying and preserving truly significant, long-term relevant information about users.",  
        "You focus on extracting information that will remain relevant and useful over extended periods.",  
        "You carefully filter out temporary states, trivial events, and time-bound information.",  
        "You carefully filter out any memories that are already in the memory store.",  
        "You understand the difference between temporarily relevant details and permanently useful knowledge.",  
    ],  
    steps=[  
        "Analyze both the user's message and the assistant's message for context",  
        "Consider the conversation flow to better understand the information's significance",  
        "Look for information meeting these criteria:",  
        "  - Permanent or long-lasting relevance (e.g., traits, background, significant relationships)",  
        "  - Important biographical details (e.g., health conditions, cultural background)",  
        "  - Major life events that shape the user's context",  
        "  - Information that would be valuable months or years from now",  
        "Filter out information that is:",  
        "  - Temporary or time-bound",  
        "  - Trivial daily events",  
        "  - Current activities or states",  
        "  - Administrative or routine matters",  
        "  - Already in the existing memories",  
        "For each truly significant piece of information:",  
        "  - Formulate it in a way that preserves long-term relevance",  
        "  - Choose the appropriate memory type",  
        "  - Express it clearly and timelessly",  
    ],  
    output_instructions=[  
        "Create memories only for information with lasting significance",  
        "Do not create memories of things that are already in the memory store",  
        "Format memories to be relevant regardless of when they are accessed",  
        "Focus on permanent traits, important relationships, and significant events",  
        "Exclude temporary states and trivial occurrences",  
        "When in doubt, only store information that would be valuable in future conversations",  
    ],  
)  
  
# Create the agent configuration  
memory_formation_config = BaseAgentConfig(  
    client=instructor.from_openai(OpenAI(api_key=os.getenv("OPENAI_API_KEY"))),  
    model="gpt-4o-mini",  
    memory=AgentMemory(max_messages=10),  
    system_prompt_generator=memory_formation_prompt,  
    input_schema=MemoryFormationInputSchema,  
    output_schema=MemoryFormationOutputSchema,  
)  
  
# Create the memory formation agent  
memory_formation_agent = BaseAgent(memory_formation_config)
```

# Chat Agent

![](https://miro.medium.com/v2/resize:fit:688/1*CRESY2QT04Rpiw-E1sPr3w.png)

Now that we have our memory formation agent ready to go, we need an agent that will actually use these memories to have meaningful conversations with users. This is where our Chat Agent comes in.

The Chat Agent is designed to be conversational while leveraging the stored memories to provide personalized and contextually relevant responses. Here’s how it’s implemented:
```python
from atomic_agents.agents.base_agent import BaseAgent, BaseAgentConfig, BaseIOSchema  
from atomic_agents.lib.components.system_prompt_generator import SystemPromptGenerator  
from atomic_agents.lib.components.agent_memory import AgentMemory  
from pydantic import Field  
  
class ChatAgentInputSchema(BaseIOSchema):  
    """Input schema for the Chat Agent."""  
    message: str = Field(..., description="The user's message")  
class ChatAgentOutputSchema(BaseIOSchema):  
    """Output schema for the Chat Agent."""  
    response: str = Field(..., description="The assistant's response to the user")  
# Initialize the system prompt generator for the chat agent  
chat_prompt = SystemPromptGenerator(  
    background=[  
        "You are a friendly and helpful AI assistant with access to long-term memories about the user.",  
        "You use these memories to provide personalized and contextually relevant responses.",  
        "You maintain a natural, conversational tone while being professional and respectful.",  
    ],  
    steps=[  
        "Review any relevant memories about the user",  
        "Consider the current context of the conversation",  
        "Formulate a response that incorporates relevant memories naturally",  
        "Ensure the response is helpful and moves the conversation forward",  
    ],  
    output_instructions=[  
        "Keep responses concise but informative",  
        "Reference memories naturally, as a human friend would",  
        "Maintain a consistent personality across conversations",  
        "Be helpful while respecting boundaries",  
    ],  
)  
# Create the chat agent configuration  
chat_agent_config = BaseAgentConfig(  
    client=instructor.from_openai(OpenAI(api_key=os.getenv("OPENAI_API_KEY"))),  
    model="gpt-4o-mini",  
    memory=AgentMemory(max_messages=10),  
    system_prompt_generator=chat_prompt,  
    input_schema=ChatAgentInputSchema,  
    output_schema=ChatAgentOutputSchema,  
)  
# Create the chat agent  
chat_agent = BaseAgent(chat_agent_config)
```

The Chat Agent is relatively simple compared to the Memory Formation Agent, as its main job is to engage in conversation while naturally incorporating the memories provided by the context providers.

# Putting It All Together

Now that we have all our components ready, let’s see how they work together in the main application. Here’s the core logic that ties everything together:

```python
def main() -> None:  
    console = Console()  
    store_tool = MemoryStoreTool()  
  
    # Initialize tools and context providers  
    memory_context_provider = MemoryContextProvider(  
        title="Existing Memories",  
    )  
    current_date_context_provider = CurrentDateContextProvider(  
        title="Current Date",  
    )  
    # Register context providers with agents  
    chat_agent.register_context_provider("memory", memory_context_provider)  
    chat_agent.register_context_provider("current_date", current_date_context_provider)  
    memory_formation_agent.register_context_provider("memory", memory_context_provider)  
    memory_formation_agent.register_context_provider(  
        "current_date", current_date_context_provider  
    )  
    # Main conversation loop  
    while True:  
        # Get user input  
        user_input = input("User: ")  
        # Query relevant memories  
        memory_query_tool = ==MemoryQueryTool==()  
        retrieved_memories = memory_query_tool.run(  
            MemoryQueryInputSchema(query=user_input, n_results=10)  
        )  
        memory_context_provider.memories = retrieved_memories.memories  
        # Form new memories if needed  
        memory_assessment = memory_formation_agent.run(  
            MemoryFormationInputSchema(  
                last_user_msg=user_input,  
                last_assistant_msg=last_assistant_msg  
            )  
        )  
        # Store any new memories  
        if memory_assessment.memories:  
            for memory in memory_assessment.memories:  
                store_tool.run(MemoryStoreInputSchema(memory=memory))  
        # Generate chat response  
        chat_response = chat_agent.run(ChatAgentInputSchema(message=user_input))  
        last_assistant_msg = chat_response.response  
        print(f"Assistant: {chat_response.response}")
```

The main loop orchestrates the following flow:

1. Get user input
2. Query relevant memories based on the input
3. Update the memory context provider with retrieved memories
4. Run the memory formation agent to identify and store new memories
5. Generate a response using the chat agent
6. Display the response to the user

**This creates a seamless experience** where the assistant can both **remember past interactions and form new memories** while maintaining a natural conversation.

# Conclusion

We’ve built a complete AI assistant system with persistent memory capabilities using _Atomic Agents_. The system demonstrates:

- **Modular Design**: Each component (memory storage, formation, chat) is separate and easily modifiable
- **Type Safety**: All interactions are type-safe through Pydantic models
- **Persistent Storage**: Memories persist between conversations using ChromaDB
- **Natural Interaction**: The chat agent naturally incorporates memories into responses

This implementation provides a solid foundation that you can build upon. Some potential enhancements could include:

- **Adding more memory types** for different kinds of information
- **Implementing memory decay** or relevance scoring
- **Implementing memory verification** or correction mechanisms

Remember, **this is just one way to implement persistent memory in an AI assistant**. The modular nature of _Atomic Agents_ makes it easy to modify and expand upon this implementation to suit your specific needs.
