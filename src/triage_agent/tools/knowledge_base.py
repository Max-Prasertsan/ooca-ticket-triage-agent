"""
Knowledge Base Search Tool
===========================

Tool for searching the knowledge base to find relevant articles
for customer support issues.

This implementation uses a mock knowledge base for demonstration.
In production, this would integrate with a real search backend
(Elasticsearch, Algolia, etc.).
"""

import logging
from typing import Type

from src.triage_agent.knowledge_base_data import KNOWLEDGE_BASE_ARTICLES
from src.triage_agent.models.tools import (
    KnowledgeBaseArticle,
    KnowledgeBaseInput,
    KnowledgeBaseOutput,
)
from src.triage_agent.tools.base import BaseTool

logger = logging.getLogger(__name__)


class KnowledgeBaseTool(BaseTool[KnowledgeBaseInput, KnowledgeBaseOutput]):
    """
    Tool for searching the knowledge base.
    
    Searches through knowledge base articles to find relevant
    documentation for customer issues. Returns ranked results
    based on keyword matching and category filtering.
    
    Attributes:
        name: "knowledge_base_search"
        description: Description for the AI agent
        input_model: KnowledgeBaseInput
        output_model: KnowledgeBaseOutput
    
    Example:
        >>> tool = KnowledgeBaseTool()
        >>> input_data = KnowledgeBaseInput(query="password reset")
        >>> result = tool.execute(input_data)
        >>> print(result.results[0].title)
        'How to Reset Your Password'
    """
    
    name: str = "knowledge_base_search"
    description: str = (
        "Search the knowledge base for relevant help articles and documentation. "
        "Use this tool to find solutions, guides, and troubleshooting steps that "
        "may help resolve the customer's issue. Returns ranked articles with "
        "relevance scores."
    )
    input_model: Type[KnowledgeBaseInput] = KnowledgeBaseInput
    output_model: Type[KnowledgeBaseOutput] = KnowledgeBaseOutput
    
    def _execute(self, input_data: KnowledgeBaseInput) -> KnowledgeBaseOutput:
        """
        Execute knowledge base search.
        
        Args:
            input_data: Search parameters including query and filters.
        
        Returns:
            KnowledgeBaseOutput: Search results with relevance scores.
        """
        query = input_data.query.lower()
        query_terms = set(query.split())
        
        logger.debug(f"Searching KB for: '{query}' (terms: {query_terms})")
        
        scored_results: list[tuple[float, dict]] = []
        
        for article in KNOWLEDGE_BASE_ARTICLES:
            # Apply category filter if specified
            if input_data.category_filter:
                if article["category"].lower() != input_data.category_filter.lower():
                    continue
            
            # Calculate relevance score based on keyword matching
            score = self._calculate_relevance(query_terms, article)
            
            if score > 0.1:  # Minimum relevance threshold
                scored_results.append((score, article))
        
        # Sort by relevance score descending
        scored_results.sort(key=lambda x: x[0], reverse=True)
        
        # Limit to max_results
        top_results = scored_results[:input_data.max_results]
        
        # Convert to output format
        results = [
            KnowledgeBaseArticle(
                id=article["id"],
                title=article["title"],
                url=article["url"],
                category=article["category"],
                content_snippet=article["content"][:200] + "...",
                relevance_score=round(score, 2)
            )
            for score, article in top_results
        ]
        
        logger.info(f"KB search found {len(results)} relevant articles")
        
        return KnowledgeBaseOutput(
            results=results,
            total_matches=len(scored_results),
            query_processed=query
        )
    
    def _calculate_relevance(
        self,
        query_terms: set[str],
        article: dict
    ) -> float:
        """
        Calculate relevance score for an article.
        
        Uses a simple TF-based scoring with boosts for title matches.
        
        Args:
            query_terms: Set of query terms.
            article: Article dictionary.
        
        Returns:
            float: Relevance score between 0 and 1.
        """
        title_lower = article["title"].lower()
        content_lower = article["content"].lower()
        keywords_lower = [k.lower() for k in article.get("keywords", [])]
        
        score = 0.0
        
        for term in query_terms:
            # Title match (highest weight)
            if term in title_lower:
                score += 0.4
            
            # Keyword match (high weight)
            if any(term in kw for kw in keywords_lower):
                score += 0.3
            
            # Content match (lower weight)
            if term in content_lower:
                score += 0.15
        
        # Normalize to 0-1 range
        max_possible = len(query_terms) * 0.85
        if max_possible > 0:
            score = min(score / max_possible, 1.0)
        
        return score