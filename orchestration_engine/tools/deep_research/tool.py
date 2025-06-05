from typing import List
from pydantic import Field
from atomic_agents.lib.base.base_tool import BaseTool, BaseToolConfig
from atomic_agents.lib.base.base_io_schema import BaseIOSchema

from orchestration_engine.agents.query_agent import QueryAgentInputSchema, query_agent
from orchestration_engine.agents.qa_agent import (
    QuestionAnsweringAgentInputSchema,
    question_answering_agent,
    QuestionAnsweringAgentOutputSchema,
)
from orchestration_engine.agents.choice_agent import choice_agent, ChoiceAgentInputSchema
from orchestration_engine.tools.searxng_search import SearxNGSearchTool, SearxNGSearchToolConfig, SearxNGSearchToolInputSchema
from orchestration_engine.tools.webpage_scraper import WebpageScraperTool, WebpageScraperToolInputSchema
from orchestration_engine.tools.deep_research.deepresearch_context_providers import ContentItem, CurrentDateContextProvider, ScrapedContentContextProvider


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
    
    def _perform_search_and_scrape(self, queries: List[str], max_results: int) -> tuple[List[ContentItem], bool]:
        """Perform web search and scrape content from results.
        
        Returns:
            tuple: (content_items, hit_token_limit)
        """
        # Perform the search
        search_results = self.searxng_tool.run(SearxNGSearchToolInputSchema(queries=queries))
        
        # Scrape content from search results with token/character limit
        content_items = []
        MAX_TOTAL_CHARS = 380000  # ~95,000 tokens (leaving buffer for system prompt)
        current_char_count = 0
        results_processed = 0
        hit_token_limit = False
        
        for result in search_results.results:
            # Check if we've hit either limit
            if results_processed >= max_results:
                print(f"Stopped at max_results limit: {max_results}")
                break
                
            try:
                scraped_content = self.webpage_scraper_tool.run(
                    WebpageScraperToolInputSchema(url=result.url, include_links=True)
                )
                
                content_length = len(scraped_content.content)
                
                # Check if adding this content would exceed token limit
                if current_char_count + content_length > MAX_TOTAL_CHARS:
                    # Try to fit partial content
                    remaining_chars = MAX_TOTAL_CHARS - current_char_count
                    if remaining_chars > 5000:  # Only if meaningful space left
                        truncated_content = scraped_content.content[:remaining_chars]
                        # Try to end at sentence boundary
                        last_period = truncated_content.rfind('.')
                        if last_period > remaining_chars * 0.8:
                            truncated_content = truncated_content[:last_period + 1]
                        
                        content_items.append(ContentItem(content=truncated_content, url=result.url))
                        print(f"Stopped at token limit: ~{MAX_TOTAL_CHARS//4} tokens (partial content from {result.url})")
                    else:
                        print(f"Stopped at token limit: ~{MAX_TOTAL_CHARS//4} tokens")
                    break
                
                # Add full content
                content_items.append(ContentItem(content=scraped_content.content, url=result.url))
                current_char_count += content_length
                results_processed += 1
                
            except Exception as e:
                # Skip failed scrapes but continue with others
                print(f"Failed to scrape {result.url}: {e}")
                continue
        
        print(f"Processed {results_processed} results, total chars: {current_char_count} (~{current_char_count//4} tokens)")
        return content_items, hit_token_limit
    
    
    def _should_perform_additional_search(self, research_query: str, content_items: List[ContentItem]) -> bool:
        """Determine if additional searches are needed based on initial results quality."""
        if len(content_items) == 0:
            return True  # No results, definitely need more
        
        # Check if results seem comprehensive enough
        choice_agent_output = choice_agent.run(
            ChoiceAgentInputSchema(
                user_message=f"Research Query: {research_query}",
                decision_type=(
                    "Based on the scraped content available in context, should we perform additional searches? "
                    "TRUE if the content seems insufficient, incomplete, or doesn't address the query well. "
                    "FALSE if the content appears comprehensive and relevant for answering the research question."
                ),
            )
        )
        print(f"Choice Agent Decision: {choice_agent_output.decision}")
        return choice_agent_output.decision
    
    def _generate_comprehensive_answer(self, research_query: str) -> QuestionAnsweringAgentOutputSchema:
        """Generate a comprehensive answer based on the research context."""
        return question_answering_agent.run(
            QuestionAnsweringAgentInputSchema(question=research_query)
        )
    
    def run(self, input_data: DeepResearchToolInputSchema) -> DeepResearchToolOutputSchema:
        """
        Execute the deep research process.
        
        Since the orchestrator has already decided to use deep research, we perform
        an initial search and then check if additional searches are needed.
        
        Args:
            input_data: The input schema containing the research query
            
        Returns:
            DeepResearchToolOutputSchema: Comprehensive research results
        """
        research_query = input_data.research_query
        max_results = input_data.max_search_results
        
        # Always perform initial search since orchestrator chose deep research
        # Generate search queries
        search_queries = self._generate_search_queries(research_query)
        
        # Perform search and scrape content
        content_items, hit_token_limit = self._perform_search_and_scrape(search_queries, max_results)
        
        # Check if we need additional searches based on content quality
        # Skip additional search if we already hit the token limit
        # NOTE: Don't update context provider yet to avoid token overflow in choice agent
        if not hit_token_limit and len(content_items) > 0 and self._should_perform_additional_search(research_query, content_items):
            # Generate additional search queries for more comprehensive coverage
            additional_queries = self._generate_search_queries(research_query, num_queries=2)
            additional_content, _ = self._perform_search_and_scrape(additional_queries, max_results // 2)
            
            # Combine content items
            content_items.extend(additional_content)
            search_queries.extend(additional_queries)
        elif hit_token_limit:
            print("Skipping additional search due to token limit reached in initial search")
        
        # Update context provider with final content (after all searches are complete)
        self.scraped_content_context_provider.content_items = content_items
        
        sources = [item.url for item in content_items]
        
        # Generate comprehensive answer
        qa_output = self._generate_comprehensive_answer(research_query)
        
        return DeepResearchToolOutputSchema(
            research_query=research_query,
            answer=qa_output.answer,
            sources=sources,
            follow_up_questions=qa_output.follow_up_questions,
            search_queries_used=search_queries
        )