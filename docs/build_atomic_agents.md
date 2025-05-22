Why Another Framework?
Why Not Just the API, or LangChain’s I/O Schemas?

Some folks say: “Can’t I just use the OpenAI API directly? Doesn’t LangChain also have input/output schemas?” Indeed, you can do everything from scratch, and if you already know how to implement techniques like RAG, ReACT, or chain-of-thought manually, that’s great. But as you scale up or build multiple AI pipelines, you often want a consistent, minimal organizational layer — one that helps avoid re-inventing the wheel or burying you in “magic.” That’s where Atomic Agents comes in. It:

    Focuses on transparency and debugging: You can easily set breakpoints and see exactly what’s in your system prompt, input data, or output JSON.
    Doesn’t chase every new prompt-engineering paper for the sake of it. Instead, it’s just enough to keep your code tidy and maintainable, letting you pick the approach you want. So, instead of providing you with bloated, inflexible ways of doing everything, Atomic Agents provides you with the tools you need to easily do things yourself in exactly the way your project requires it.

Atomic Agents: Origins

I personally took a year off between clients to explore every major AI framework — LangChain, CrewAI, AutoGen, Guidance, and others. I kept hitting walls: either unnecessary abstractions, code that was hard to maintain, or breakage between updates. And when I wasn’t dealing with any of that, I was running & re-running my multi-agent AI crew/army because well, let’s face it, 9.5/10 times it will not do what you want in EXACTLY the way you want it and you have a constant back-and-forth or worse yet, infinite loops that burn your money. I realized I liked how Instructor handled structured prompts and retries, but I still needed a minimal “home” for each agent, with well-defined input/output schemas. That’s why I built Atomic Agents. Over time, multiple companies approached me about rewriting LangChain-based solutions in Atomic Agents because it was simply easier to debug, maintain, and understand.
The Problem with LangChain, CrewAI & AutoGen

    LangChain: Introduces layer after layer of abstraction. Simple tasks that should be straightforward start to feel like a labyrinth. Debugging can become a nightmare. Plus, with 15 years of coding experience, I’d argue it’s lacking in standard best practices around architecture.
    CrewAI & AutoGen: Aim for “magic,” promising autonomy and near-AGI capabilities, which often overpromise and underdeliver in real production settings.
    Overpromising: Many popular AI frameworks say “just push a button!” But behind the scenes, they’re not as plug-and-play as they appear — and devs end up with unmaintainable code.

Atomic Agents: Doing Things Differently

    Modularity
    By focusing on single-purpose building blocks (“atoms”), Atomic Agents allows you to fine-tune every part of your system. Swap out a web-scraper for a database query, or a local LLM for an OpenAI model — no extensive rewrites needed.
    Predictability
    Strict input/output schemas let you define precisely what you expect, ensuring consistent results instead of random structure issues or half-baked JSON.
    Lightweight & Developer-Centric
    If you’re a Python dev, it’s just Python. You can step through with a debugger, log everything, or integrate these agents into standard web frameworks (Flask, FastAPI, Django, etc.) without friction.
    Real Control
    No black-box orchestrator deciding which agent calls which tool. You decide the entire flow, hooking up whichever “atoms” make sense for your use case. Although there is nothing stopping you from giving agents a slight bit of autonomy through the use of a Union type as can be seen in this orchestration agent example.

Core Programming Paradigms
Input–Process–Output (IPO) Model

Atomic Agents is built around the IPO principle. Every agent or tool has:

    Input Schema (via Pydantic)
    Processing Function (the actual logic)
    Output Schema (again, enforced by Pydantic)

That means your code is fully structured, testable, and easy to refactor. No more guesswork about the shape of the data in each step.
Atomicity

Each piece should “do one thing and do it well.” For example, you might have:

    A Query Agent that generates search queries from a user’s question.
    A Web Scraper Tool that only knows how to scrape HTML from a URL.
    A Context Provider that dynamically injects the day’s date or search results into the system prompt at runtime.

You can combine these in any order you like, nest them in pipelines, and keep track of everything without losing your sanity.
Installation & Getting Started

pip install atomic-agents

Want to use OpenAI and Groq? Just add those packages:

pip install openai groq

This also installs the atomic CLI tool. If you want to experiment locally with the code:

git clone https://github.com/BrainBlend-AI/atomic-agents.git
cd atomic-agents
poetry install

Example: A Simple Q&A Agent

Let’s see how straightforward it is to build an agent that responds to user queries and suggests follow-up questions.

# input.py
from pydantic import Field
from typing import List
from atomic_agents.agents.base_agent import BaseIOSchema

class CustomInputSchema(BaseIOSchema):
    chat_message: str = Field(..., description="The user's input message.")
class CustomOutputSchema(BaseIOSchema):
    chat_message: str = Field(..., description="The agent's response message.")
    suggested_questions: List[str] = Field(..., description="Suggested follow-up questions.")

# agent.py
import instructor
import openai

from atomic_agents.agents.base_agent import BaseAgent, BaseAgentConfig
from atomic_agents.lib.components.system_prompt_generator import SystemPromptGenerator
from atomic_agents.lib.components.agent_memory import AgentMemory
from input import CustomInputSchema, CustomOutputSchema
system_prompt_generator = SystemPromptGenerator(
    background=[
        "You are a helpful assistant that provides detailed answers and suggests follow-up questions."
    ],
    steps=[
        "1. Understand the user's query.",
        "2. Provide a clear, concise response.",
        "3. Suggest 3 relevant follow-up questions."
    ],
    output_instructions=[
        "Answer thoroughly and briefly.",
        "End your response with a short list of follow-up questions."
    ]
)
my_client = instructor.from_openai(openai.OpenAI(api_key="YOUR_OPENAI_KEY"))
agent = BaseAgent(
    config=BaseAgentConfig(
        client=my_client,
        model="gpt-4o-mini",
        system_prompt_generator=system_prompt_generator,
        input_schema=CustomInputSchema,
        output_schema=CustomOutputSchema,
        memory=AgentMemory()
    )
)
# Run it
response = agent.run(CustomInputSchema(chat_message="Why should I use Atomic Agents?"))
print("Answer:", response.chat_message)
print("Follow-up questions:", response.suggested_questions)

That’s it. No “chain-of-chains” meltdown, no bizarre overhead. Each part is explicit, typed, and easy to maintain.
Chaining Agents & Tools with Ease

A key feature of Atomic Agents is how easily you can chain agents and tools by matching their schemas. Suppose we have an agent that generates search queries, and we want to pass those queries directly into our SearxNG search tool. All we do is align the output schema of the query agent with the input schema of the search tool.

Below is a snippet that does exactly that. Notice how query_agent is configured to output a schema that SearxNGSearchTool expects, making chaining straightforward:

from deep_research.config import ChatConfig
import instructor
import openai
from pydantic import Field
from atomic_agents.agents.base_agent import BaseIOSchema, BaseAgent, BaseAgentConfig
from atomic_agents.lib.components.system_prompt_generator import SystemPromptGenerator

from deep_research.tools.searxng_search import SearxNGSearchTool
class QueryAgentInputSchema(BaseIOSchema):
    """
    This is the input schema for the QueryAgent.
    """
    instruction: str = Field(..., description="A detailed instruction or request to generate search engine queries for.")
    num_queries: int = Field(..., description="The number of search queries to generate.")

# NOTE: SearxNGSearchTool.input_schema is presumably a schema that expects something like { "queries": [ ... ] },
# but we are telling our query agent to output that exact same format, so the next tool can consume it directly.
query_agent = BaseAgent(
    BaseAgentConfig(
        client=instructor.from_openai(openai.OpenAI(api_key=ChatConfig.api_key)),
        model=ChatConfig.model,
        system_prompt_generator=SystemPromptGenerator(
            background=[
                "You are an expert search engine query generator with a deep understanding of which queries "
                "will maximize the number of relevant results."
            ],
            steps=[
                "Analyze the given instruction to identify key concepts and aspects that need to be researched",
                "For each aspect, craft a search query using appropriate search operators and syntax",
                "Ensure queries cover different angles of the topic (technical, practical, comparative, etc.)",
            ],
            output_instructions=[
                "Return exactly the requested number of queries",
                "Format each query like a search engine query, not a natural language question",
                "Each query should be a concise string of keywords and operators",
            ],
        ),
        input_schema=QueryAgentInputSchema,
        output_schema=SearxNGSearchTool.input_schema,  # Matches the tool's expected input schema
    )
)

Because the output_schema of our query_agent matches SearxNGSearchTool.input_schema, we can pass the agent’s result to the tool with zero extra code:

from deep_research.tools.searxng_search import SearxNGSearchTool, SearxNGSearchToolInputSchema

searx_tool = SearxNGSearchTool()
# 1. Run the query_agent to produce the queries
query_agent_output = query_agent.run(QueryAgentInputSchema(
    instruction="Research the latest breakthroughs in quantum computing",
    num_queries=3
))
# 2. Chain it directly to the search tool
#    Notice we just pass query_agent_output to the tool input schema, no manual remapping needed
search_results = searx_tool.run(SearxNGSearchToolInputSchema(query_agent_output))
print("Search Results:", search_results)

With no extra bridging code, we can swap in or out any tool that uses the same schema. If you later decide to replace SearxNGSearchTool with a “bing_search_tool” or something else with a different schema, you simply adapt either the agent’s output_schema or the new tool’s input_schema. No major refactor required.
Real-World Impact: A LegalTech Example

One of the strongest endorsements of Atomic Agents’ approach comes from a legaltech client. Originally, they were using LangChain to build chat solutions around contract analysis and extraction — things like extracting the parties involved, retrieving metadata about clauses, and identifying due dates in large contracts.
Why It Helped

    Highly Structured System Prompts: By leveraging the background, steps, and output instructions in a clean, explicit way, it became trivial to switch the agent’s persona or strategy.
    Atomic Approach: Instead of one behemoth agent that tries to handle everything, they have separate micro-agents: one for extracting parties, another for due dates, another for metadata. Each one can be debugged independently.
    Context Providers: Contract data is dynamically fed into each relevant agent. If due dates fail to parse, they know exactly which part of the chain to fix — no rummaging around 50 interconnected classes from some “multi-agent” orchestrator.

The client also loved that breakpoints are so easy to set — no hidden “magic” behind the scenes. If an agent is failing to parse a certain date format, they can step right in and see the raw input, the system prompt, the docstrings, and the agent’s outputs, all in standard Python.
Going Deeper: Dynamic Context Providers

Another highlight of Atomic Agents is how easily you can feed live or dynamic data into your system prompts. Context providers attach to your agents and can inject real-time info — such as search results, timestamps, or entire data buffers.

Here’s a snippet from a “deep research” example, showing how we can store scraped web content, then dynamically insert it into the system prompt:

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
        return "\n\n".join([
            f"Source {idx}:\nURL: {item.url}\nContent:\n{item.content}\n{'-' * 80}"
            for idx, item in enumerate(self.content_items, 1)
        ])
class CurrentDateContextProvider(SystemPromptContextProviderBase):
    def __init__(self, title: str, date_format: str = "%A %B %d, %Y"):
        super().__init__(title=title)
        self.date_format = date_format
    def get_info(self) -> str:
        return f"The current date in the format {self.date_format} is {datetime.now().strftime(self.date_format)}."

By registering these providers with one or more agents, you can seamlessly integrate them into your system prompts. Need “up-to-date content from 3 scraped URLs?” Just attach your ScrapedContentContextProvider to your agent before calling .run().
Building Larger Agentic Pipelines: “Deep Research” & Beyond

With Atomic Agents, you can chain multiple micro-agents (or “atoms”) to build powerful multi-step workflows:

    Use a Query Agent to expand the user’s request into multiple relevant search queries.
    Feed that output directly into a web search tool (like SearxNG) or a vector DB tool to retrieve relevant documents.
    Run a “scraper” on each of those results, extracting or summarizing the contents.
    Inject the extracted data into a context provider, so a subsequent agent sees all of it in its prompt.
    Use a Q&A Agent to craft a final answer, referencing the newly added context.

Some developers have even started experimenting with these “atomic” pipelines to control robotics — coordinating specialized agent tasks for computer vision, pathfinding, and more. Atomic Agents doesn’t limit you to chat or text-based tasks; it’s a flexible framework for orchestrating any sequence of actions around a set of well-defined schemas.
Going Multimodal

Atomic Agents also supports multimodal inputs and outputs, letting you build richer AI applications beyond text. Suppose you need to process images, video transcripts, or PDF documents. You define Pydantic models with the appropriate data fields — such as instructor.Image or raw PDF text—and wire them into your agent in the same way you would with text-based prompts.

Example: Suppose you have an agent that extracts data from nutrition labels:

from atomic_agents.lib.base.base_io_schema import BaseIOSchema
from typing import List
from pydantic import Field
import instructor

class NutritionAnalysisInput(BaseIOSchema):
    instruction_text: str = Field(..., description="Instruction for analyzing the nutrition label")
    images: List[instructor.Image] = Field(..., description="Nutrition label images")
class NutritionAnalysisOutput(BaseIOSchema):
    analyzed_labels: List[dict] = Field(..., description="Extracted nutritional data")

You’d then define your system prompt, tie it to a base agent, and let the agent parse the image data. If you want to mix text-based context — like brand info or user preferences — that’s trivial: just add more fields or context providers.
Creating Your Own Tools with Atomic Forge

Atomic Agents has a concept of a “forge” where you can download or create new tools. Tools live in your codebase — you own them entirely. This approach:

    Gives You Full Control: Don’t like how a tool sorts results? Tweak it locally without affecting other users.
    Manages Dependencies Better: Each tool includes its own minimal set of requirements.
    Keeps It Lean: You only install the tools you actually need.

Building a Tool: Short Overview

    Input Schema & Output Schema: Must inherit from BaseIOSchema.
    Config: Inherits from BaseToolConfig.
    Main Tool Class: Inherits from BaseTool, overrides a run method that accepts your input_schema and returns your output_schema.
    Example Usage: Keep a snippet at the bottom or in a test file so devs can see how to run it directly.

If you want to share the tool with the community, you can open a pull request to add it to the official Atomic Forge folder, accompanied by tests, a README, and any docstrings.

A full guide for building tools can be found here.

As an example, here is a simple calculator tool

from pydantic import Field
from sympy import sympify

from atomic_agents.agents.base_agent import BaseIOSchema
from atomic_agents.lib.base.base_tool import BaseTool, BaseToolConfig


################
# INPUT SCHEMA #
################
class CalculatorToolInputSchema(BaseIOSchema):
    """
    Tool for performing calculations. Supports basic arithmetic operations
    like addition, subtraction, multiplication, and division, as well as more
    complex operations like exponentiation and trigonometric functions.
    Use this tool to evaluate mathematical expressions.
    """

    expression: str = Field(..., description="Mathematical expression to evaluate. For example, '2 + 2'.")


#################
# OUTPUT SCHEMA #
#################
class CalculatorToolOutputSchema(BaseIOSchema):
    """
    Schema for the output of the CalculatorTool.
    """

    result: str = Field(..., description="Result of the calculation.")


#################
# CONFIGURATION #
#################
class CalculatorToolConfig(BaseToolConfig):
    """
    Configuration for the CalculatorTool.
    """

    pass


#####################
# MAIN TOOL & LOGIC #
#####################
class CalculatorTool(BaseTool):
    """
    Tool for performing calculations based on the provided mathematical expression.

    Attributes:
        input_schema (CalculatorToolInputSchema): The schema for the input data.
        output_schema (CalculatorToolOutputSchema): The schema for the output data.
    """

    input_schema = CalculatorToolInputSchema
    output_schema = CalculatorToolOutputSchema

    def __init__(self, config: CalculatorToolConfig = CalculatorToolConfig()):
        """
        Initializes the CalculatorTool.

        Args:
            config (CalculatorToolConfig): Configuration for the tool.
        """
        super().__init__(config)

    def run(self, params: CalculatorToolInputSchema) -> CalculatorToolOutputSchema:
        """
        Executes the CalculatorTool with the given parameters.

        Args:
            params (CalculatorToolInputSchema): The input parameters for the tool.

        Returns:
            CalculatorToolOutputSchema: The result of the calculation.
        """
        # Convert the expression string to a symbolic expression
        parsed_expr = sympify(str(params.expression))

        # Evaluate the expression numerically
        result = parsed_expr.evalf()
        return CalculatorToolOutputSchema(result=str(result))


#################
# EXAMPLE USAGE #
#################
if __name__ == "__main__":
    calculator = CalculatorTool()
    result = calculator.run(CalculatorToolInputSchema(expression="sin(pi/2) + cos(pi/4)"))
    print(result)  # Expected output: {"result":"1.70710678118655"}

About PydanticAI and Instructor

A newly released project called PydanticAI is somewhat similar to Instructor, the library that Atomic Agents currently relies on. People often ask:

    “Will PydanticAI replace Atomic Agents? Will Atomic Agents switch to PydanticAI instead of Instructor?”

The short answer is: They’re complementary in many ways. PydanticAI appears to be evolving toward a role similar to Instructor — focusing on structured prompt generation. It’s still quite new, and while it’s promising, its validation and streaming modes have some rough edges. It also lacks built-in features like retry mechanisms.

At some point, Atomic Agents may consider swapping out Instructor for PydanticAI if it matures to the point that it surpasses Instructor’s functionality. One reason we like Instructor is that it’s available in multiple languages (JS, Rust, Ruby, Python, etc.), meaning Atomic Agents could be more easily ported to new ecosystems in the future. Going all-in on a purely Python library like PydanticAI might complicate that. For now, Instructor does the job reliably, and we’re excited to watch PydanticAI evolve — there’s a possibility we might switch if it becomes compelling enough.
Provider & Model Compatibility

Atomic Agents uses Instructor under the hood, meaning any LLM that Instructor supports — OpenAI, Ollama, Groq, Cohere, Anthropic, Mistral, and more — should work right out of the box. If you decide you need a different provider (or a self-hosted model), just switch it at the agent config level. No rearchitecting needed.
Community & Roadmap: Help Us Build the Future

We’d love to grow and improve Atomic Agents — and, as with any open-source project, your feedback and contributions are invaluable. Here are a few ways you can help:

    Documentation: We have examples and an API reference, but it’s currently split across multiple directories. If you’re skilled at auto-generating docs or bundling them into a single site, your help is welcome!
    Try It & Report Issues: Simply playing around with Atomic Agents, posting pain points, or showing off a cool pipeline is hugely beneficial.
    Code Contributions & Discussions: There’s still a ton to do. Everything from tool expansions to improved streaming support. Open a PR or start a discussion on GitHub!
    Financial Support: We’d love to eventually sponsor bug bounties or small tasks for new contributors if the project sees enough donations. If you want to tip us, see the PayPal link or GitHub Sponsors.

In the longer term, we may port Atomic Agents to other languages, especially since we can rely on Instructor’s JS, Rust, Ruby, or Python variants. We’re also encouraging an approach where you log all input & output for potential fine-tuning — like DPO (Direct Preference Optimization) or other advanced methods — to keep improving your AI’s capabilities. Some devs are already using Atomic Agents for next-level stuff like controlling robotics pipelines — the possibilities are wide open.
Scaling, Team Adoption & Traditional Solutions
Performance & Scaling

Because Atomic Agents is just Python code — no giant meta-layer on top — you can scale it the same way you’d scale any traditional backend. Whether that means spinning up more pods in Kubernetes, parallelizing calls, or caching results — all those standard approaches apply. You retain the power to optimize or orchestrate on the infrastructure side without fighting an opaque black box.
Easy Onboarding for Teams

It’s real easy for dev teams to learn and adopt because the entire approach is simply Input → Processing → Output with Pydantic enforcing type safety. New hires can quickly read the docstrings, system prompt definitions, and input/output schemas — and they’ll know exactly what the agent does and how to tweak it. It’s “AI agent development made to look (and feel) like normal development.”
A Final Word on Control & Ownership

Unlike other frameworks that wrestle control away from you with “clever” multi-agent orchestration or fancy wrappers, Atomic Agents gives you everything you need to keep your code tight and well-organized:

    Human-Readable: Each agent or tool has an input schema, a process, and an output schema. That’s it.
    Testable: Because each step is a “microservice” in design, you can easily isolate and test.
    Interchangeable: Swap or chain these microservices (a.k.a. “atoms”) in any order you need.
    Adaptable: Use standard dev knowledge — breakpoints, logs, deployment patterns — no special hoops to jump through.

No black boxes. No illusions. Just pure, developer-centric control.
Get Started & Get Involved

If you’ve grown weary of frameworks that promise the moon but deliver code obfuscation and bloat, it’s time to give Atomic Agents a try. Jump in and build:

    A deep research agent that combines web-search, scraping, and summarization.
    A multimodal pipeline that processes images, transcripts, or specialized data.
    A chatbot with dynamic memory, fetching real-time info or historical data from a vector DB.
    Or even a personal knowledge base that queries different AI tools and merges their results into consolidated insights.

Installation Recap

    Install: pip install atomic-agents openai
    Check out our examples directory for quickstarts and more advanced demos.
    Try the Atomic Assembler CLI: atomic
    Join our new subreddit: if you build anything amazing using this, feel free to drop by the newly created Atomic Agents subreddit and show off what you did, or ask questions if you are stuck!
    Support the project (if you like!) via PayPal or GitHub Sponsors.

Conclusion

Atomic Agents aims to strip away the overhyped layers of “magic” that other frameworks pile on. By returning to small, modular components governed by a clear input-output model, we believe you’ll rediscover the joy of building AI applications. Whether you’re orchestrating multiple specialized agents in a deep research pipeline, analyzing images, or creating a next-generation chat assistant with robust context, Atomic Agents has your back without dictating your design choices.

If you’re tired of code you can’t fully control — or if you simply want to accelerate your AI development with a truly developer-friendly approach — give Atomic Agents a try. We’d love to hear your feedback, see your projects, and help you tackle your next big AI idea.

    GitHub Repo: BrainBlend-AI/atomic-agents
    API Docs: https://brainblend-ai.github.io/atomic-agents/
    Examples: Atomic Examples
    Subreddit: reddit.com/r/AtomicAgents

And if you’d like to support further development — or just say thanks for making your dev life easier — I’d be honored if you’d consider a donation via PayPal or a sponsorship on GitHub Sponsors. Your contributions help keep this project growing, documented, and improved for everyone.

Happy coding — and welcome to a more streamlined way to build AI!