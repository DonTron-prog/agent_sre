This quickstart tutorial demonstrates how to create a very simple multi-agent system using the Atomic Agents library found at https://github.com/KennyVaneetvelde/atomic_agents. The system will include a search agent and a calculator agent, which can be orchestrated to handle different types of user queries.
Prerequisites

Before proceeding with this notebook, it is highly recommended to read up on the basics of the following libraries:

    Pydantic: A data validation and settings management library using Python type annotations. You can find more information and documentation at Pydantic GitHub.
    Instructor: A Python library that simplifies working with structured outputs from large language models (LLMs). It provides a user-friendly API to manage validation, retries, and streaming responses. More details can be found at Instructor GitHub.

Understanding these libraries will help you make the most of this library.
Install Necessary Packages

First, we need to install the required packages. Run the following command to install atomic-agents, openai, and instructor libraries.

pip install atomic-agents openai instructor

Import Libraries

We will import the necessary libraries for creating the multi-agent system.

import os
from typing import Union
import instructor
import openai
from pydantic import create_model
from rich.console import Console
from atomic_agents.agents.base_chat_agent import BaseAgentIO, BaseChatAgent, BaseChatAgentConfig
from atomic_agents.agents.tool_interface_agent import ToolInterfaceAgent, ToolInterfaceAgentConfig
from atomic_agents.lib.tools.search.searx_tool import SearxNGSearchTool, SearxNGSearchToolConfig
from atomic_agents.lib.tools.calculator_tool import CalculatorTool, CalculatorToolConfig

Initialize Components

Initialize the necessary components, including the client, tools, and agents.

It’s important to note that you can use any client supported by the Instructor; simply check their documentation on how to switch OpenAI for, say, Groq or Mistral.

# Initialize the console for output
console = Console()

# Initialize the client
client = instructor.from_openai(openai.OpenAI())

# Initialize the SearxNG search tool
searx_tool = SearxNGSearchTool(SearxNGSearchToolConfig(base_url=os.getenv('SEARXNG_BASE_URL'), max_results=10))

# Initialize the calculator tool
calc_tool = CalculatorTool(CalculatorToolConfig())

Configure and Create Agents

Configure and create the search agent and calculator agent.

We can use the ToolInterfaceAgent for this, which dynamically takes the required input schema of a tool, and instructs the LLM to generate an output of exactly that format.

# Configure the search agent
search_agent_config = ToolInterfaceAgentConfig(client=client, model='gpt-3.5-turbo', tool_instance=searx_tool, return_raw_output=False)

# Configure the calculator agent
calculator_agent_config = ToolInterfaceAgentConfig(client=client, model='gpt-3.5-turbo', tool_instance=calc_tool, return_raw_output=False)

# Create the search agent and calculator agent
searx_agent = ToolInterfaceAgent(config=search_agent_config)
calc_agent = ToolInterfaceAgent(config=calculator_agent_config)

Define Union Response Schema

Create a union response schema that can handle responses from both the search agent and the calculator agent. By doing this we basically tell the orchestrator “Your response can be any of these, pick one.”

# Define a union response schema
UnionResponse = create_model('UnionResponse', __base__=BaseAgentIO, response=(Union[searx_agent.input_schema, calc_agent.input_schema], ...))

Notice how, instead of defining the response schema as a class, we use create_model() to define the schema. This is because we want to use the TOOL.input_schema to dynamically get the input schema of the agent, which is not possible with a class definition. We could even make this more dynamic with a list comprehension, but for verbosity in this tutorial I leave it as is.
Create Orchestration Agent

Create an orchestration agent that can manage the interactions between the user and the individual agents.

# Create the orchestration agent
orchestration_agent = BaseChatAgent(config=BaseChatAgentConfig(client=client, model='gpt-3.5-turbo', output_schema=UnionResponse))

Main Chat Loop

Create a main chat loop to interact with the orchestration agent. The agent will determine whether to use the search tool or the calculator tool based on the user’s input.

while True:
    user_input = input('You: ')
    if user_input.lower() in ['exit', 'quit']:
        print('Exiting chat...')
        break

    response = orchestration_agent.run(orchestration_agent.input_schema(chat_message=user_input))
    console.print(f'Agent: {response.response}')

    if isinstance(response.response, searx_agent.input_schema):
        console.print(f'Using searx agent')
        response = searx_agent.run(response.response)
    elif isinstance(response.response, calc_agent.input_schema):
        console.print(f'Using calc agent')
        response = calc_agent.run(response.response)

    console.print(f'Agent: {response.chat_message}')

Conclusion

We demonstrated how to create a multi-agent system using the Atomic Agents library. The system includes a search agent and a calculator agent, which can be orchestrated to handle different types of user queries. You can further customize the agents and enhance their capabilities based on your requirements.

You can also create your own tools and wrap them into the tool agent. This allows you to extend the functionality of the multi-agent system to suit your specific needs.

Also, as you can see, we did no prompt engineering at all internally in this example, in fact we didn’t even really have a prompt other than the user input, this is because we already have a default system prompt that instructs it to be a simple helpful assistant, but most importantly the Pydantic schemas for the tools, including their descriptions, are formatted and passed into the LLM, for a better look, have a look at the simple calculator tool at https://github.com/KennyVaneetvelde/atomic_agents/blob/main/atomic_agents/lib/tools/calculator_tool.py

So that’s it for this one, decided this should be a short and sweet tutorial, quickstart style, if you want a more in-depth explanation and a look behind the scenes, visit the GitHub repository or have a look at my more in-depth guide.