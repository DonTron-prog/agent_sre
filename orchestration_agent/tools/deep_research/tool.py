from typing import List
from pydantic import Field
from atomic_agents.lib.base.base_tool import BaseTool, BaseToolConfig
from atomic_agents.lib.base.base_io_schema import BaseIOSchema

from orchestration_agent.agents.query_agent import QueryAgentInputSchema, query_agent
from orchestration_agent.agents.qa_agent import (
    QuestionAnsweringAgentInputSchema,
    question_answering_agent,
    QuestionAnsweringAgentOutputSchema,
)
from orchestration_agent.agents.choice_agent import choice_agent, ChoiceAgentInputSchema
from orchestration_agent.tools.searxng_search import SearxNGSearchTool, SearxNGSearchToolConfig, SearxNGSearchToolInputSchema
from orchestration_agent.tools.webpage_scraper import WebpageScraperTool, WebpageScraperToolInputSchema
from orchestration_agent.tools.deep_research.deepresearch_context_providers import ContentItem, CurrentDateContextProvider, ScrapedContentContextProvider


class DeepResearchToolInputSchema(BaseIOSchema):
    """Input schema for the Deep Research Tool."""
    
    research_query: str = Field(..., description="The research question or topic to investigate")
    max_search_results: int = Field(default=3, description="Maximum number of search results to scrape and analyze")


class DeepResearchToolOutputSchema(BaseIOSchema):
    """Output schema for the Deep Research Tool."""
    
    research_query: str = Field(..., description="The original research query")
    answer: str = Field(..., description="Comprehensive answer based on research findings")
    sources: List[str] = Field(..., description="List of source URLs used in the research")
    follow_up_questions: List[str] = Field(..., description="Suggested follow-up questions for further research")
    search_queries_used: List[str] = Field(..., description="The search queries that were generated and used")


class DeepResearchToolConfig(BaseToolConfig):
    """Configuration for the Deep Research Tool."""
    
    searxng_base_url: str = Field(default="http://localhost:8080/", description="Base URL for SearxNG search service")
    max_search_results: int = Field(default=3, description="Maximum number of search results to process")


class DeepResearchTool(BaseTool):
    """
    A tool that performs comprehensive research on a given topic by:
    1. Generating relevant search queries
    2. Searching the web using SearxNG
    3. Scraping and analyzing content from found sources
    4. Generating a comprehensive answer with follow-up questions
    """
    
    input_schema = DeepResearchToolInputSchema
    output_schema = DeepResearchToolOutputSchema
    
    def __init__(self, config: DeepResearchToolConfig):
        super().__init__(config)
        self.searxng_tool = SearxNGSearchTool(
            SearxNGSearchToolConfig(
                base_url=config.searxng_base_url,
                max_results=config.max_search_results
            )
        )
        self.webpage_scraper_tool = WebpageScraperTool()
        
        # Initialize context providers
        self.scraped_content_context_provider = ScrapedContentContextProvider("Scraped Content")
        self.current_date_context_provider = CurrentDateContextProvider("Current Date")
        
        # Register context providers with agents
        self._register_context_providers()
    
    def _register_context_providers(self):
        """Register context providers with all relevant agents."""
        agents = [choice_agent, question_answering_agent, query_agent]
        
        for agent in agents:
            agent.register_context_provider("current_date", self.current_date_context_provider)
            agent.register_context_provider("scraped_content", self.scraped_content_context_provider)
    
    def _generate_search_queries(self, research_query: str, num_queries: int = 3) -> List[str]:
        """Generate relevant search queries for the research topic."""
        query_agent_output = query_agent.run(
            QueryAgentInputSchema(instruction=research_query, num_queries=num_queries)
        )
        return query_agent_output.queries
    
    def _perform_search_and_scrape(self, queries: List[str], max_results: int) -> List[ContentItem]:
        """Perform web search and scrape content from results."""
        # Perform the search
        search_results = self.searxng_tool.run(SearxNGSearchToolInputSchema(queries=queries))
        
        # Scrape content from search results
        content_items = []
        for result in search_results.results[:max_results]:
            try:
                scraped_content = self.webpage_scraper_tool.run(
                    WebpageScraperToolInputSchema(url=result.url, include_links=True)
                )
                content_items.append(ContentItem(content=scraped_content.content, url=result.url))
            except Exception as e:
                # Skip failed scrapes but continue with others
                print(f"Failed to scrape {result.url}: {e}")
                continue
        
        return content_items
    
    def _should_perform_new_search(self, research_query: str) -> bool:
        """Determine if a new search is needed based on existing context."""
        choice_agent_output = choice_agent.run(
            ChoiceAgentInputSchema(
                user_message=research_query,
                decision_type=(
                    "Should we perform a new web search? TRUE if we need new or updated information, FALSE if existing "
                    "context is sufficient. Consider: 1) Is the context empty? 2) Is the existing information relevant? "
                    "3) Is the information recent enough?"
                ),
            )
        )
        return choice_agent_output.decision
    
    def _generate_comprehensive_answer(self, research_query: str) -> QuestionAnsweringAgentOutputSchema:
        """Generate a comprehensive answer based on the research context."""
        return question_answering_agent.run(
            QuestionAnsweringAgentInputSchema(question=research_query)
        )
    
    def run(self, input_data: DeepResearchToolInputSchema) -> DeepResearchToolOutputSchema:
        """
        Execute the deep research process.
        
        Args:
            input_data: The input schema containing the research query
            
        Returns:
            DeepResearchToolOutputSchema: Comprehensive research results
        """
        research_query = input_data.research_query
        max_results = input_data.max_search_results
        
        # Check if we need to perform a new search
        should_search = self._should_perform_new_search(research_query)
        search_queries_used = []
        sources = []
        
        if should_search:
            # Generate search queries
            search_queries = self._generate_search_queries(research_query)
            search_queries_used = search_queries
            
            # Perform search and scrape content
            content_items = self._perform_search_and_scrape(search_queries, max_results)
            
            # Update context provider with new content
            self.scraped_content_context_provider.content_items = content_items
            sources = [item.url for item in content_items]
        else:
            # Use existing context
            sources = [item.url for item in self.scraped_content_context_provider.content_items]
        
        # Generate comprehensive answer
        qa_output = self._generate_comprehensive_answer(research_query)
        
        return DeepResearchToolOutputSchema(
            research_query=research_query,
            answer=qa_output.answer,
            sources=sources,
            follow_up_questions=qa_output.follow_up_questions,
            search_queries_used=search_queries_used
        )