"""
Search service for news articles.

Provides three search modes:
1. Vector search - Semantic similarity using pgvector embeddings
2. Text search - PostgreSQL full-text search with relevance ranking
3. Hybrid search - Combines vector and text search for best results
"""

import re
import time
from typing import Optional

from django.db import connection
from django.db.models import Q, QuerySet

from ..embedding_service import get_embedding_service
from ..metrics import SEARCH_DURATION, SEARCH_QUERIES
from ..models import News


class SearchService:
    """Service for searching news articles using various search strategies."""

    def vector_search(self, query: str, limit: Optional[int] = 50) -> QuerySet[News]:
        """
        Perform vector similarity search using embeddings from both news and articles tables.

        Searches both:
        - news.content_embedding (LLM-generated summary content) - weight 1.2
        - articles.content_embedding (full article text) - weight 1.0

        Uses weighted average of cosine distances for final ranking.
        Includes recency boost: newer articles get subtle ranking improvement.

        Args:
            query: Search query string
            limit: Maximum number of results (None for unlimited)

        Returns:
            QuerySet of News objects ordered by relevance
        """
        start_time = time.time()
        try:
            # Generate embedding for the search query
            embedding_service = get_embedding_service()
            query_embedding = embedding_service.generate_embedding(query)

            if not query_embedding:
                return News.objects.none()

            # Convert embedding list to PostgreSQL vector format
            embedding_str = "[" + ",".join(str(x) for x in query_embedding) + "]"

            # Use raw SQL to search both news and articles embeddings with weighted combination
            # Add recency boost to penalize distance for older articles (lower distance = better match)
            if limit is None:
                raw_sql = """
                    SELECT n.id,
                           (((COALESCE(nd.news_distance, 1.0) * 1.2) + (COALESCE(ad.article_distance, 1.0) * 1.0)) / 2.2) /
                           (1.0 + (0.05 / (1.0 + EXTRACT(EPOCH FROM (NOW() - COALESCE(n.article_date, n.created_at))) / 86400.0))) as combined_distance
                    FROM news n
                    LEFT JOIN articles a ON n.article_id = a.id
                    LEFT JOIN LATERAL (
                        SELECT n.content_embedding <=> %s::vector as news_distance
                    ) nd ON true
                    LEFT JOIN LATERAL (
                        SELECT a.content_embedding <=> %s::vector as article_distance
                    ) ad ON true
                    WHERE n.deleted_at IS NULL
                      AND n.status = 'published'
                      AND (n.content_embedding IS NOT NULL OR a.content_embedding IS NOT NULL)
                    ORDER BY combined_distance ASC
                """
                sql_params = [embedding_str, embedding_str]
            else:
                raw_sql = """
                    SELECT n.id,
                           (((COALESCE(nd.news_distance, 1.0) * 1.2) + (COALESCE(ad.article_distance, 1.0) * 1.0)) / 2.2) /
                           (1.0 + (0.05 / (1.0 + EXTRACT(EPOCH FROM (NOW() - COALESCE(n.article_date, n.created_at))) / 86400.0))) as combined_distance
                    FROM news n
                    LEFT JOIN articles a ON n.article_id = a.id
                    LEFT JOIN LATERAL (
                        SELECT n.content_embedding <=> %s::vector as news_distance
                    ) nd ON true
                    LEFT JOIN LATERAL (
                        SELECT a.content_embedding <=> %s::vector as article_distance
                    ) ad ON true
                    WHERE n.deleted_at IS NULL
                      AND n.status = 'published'
                      AND (n.content_embedding IS NOT NULL OR a.content_embedding IS NOT NULL)
                    ORDER BY combined_distance ASC
                    LIMIT %s
                """
                sql_params = [embedding_str, embedding_str, str(limit)]

            with connection.cursor() as cursor:
                cursor.execute(raw_sql, sql_params)
                results = cursor.fetchall()

            if not results:
                return News.objects.none()

            # Extract news IDs in ranked order
            news_ids = [row[0] for row in results]

            # Return News objects preserving the ranked order
            if news_ids:
                order_case = (
                    "CASE "
                    + " ".join(
                        [
                            f"WHEN id = {news_id} THEN {i}"
                            for i, news_id in enumerate(news_ids)
                        ]
                    )
                    + " END"
                )

                return News.objects.filter(id__in=news_ids).extra(
                    select={"ordering": order_case}, order_by=["ordering"]
                )

            return News.objects.none()

        except Exception:
            # Fallback to empty queryset if vector search fails
            return News.objects.none()
        finally:
            # Record metrics
            duration = time.time() - start_time
            SEARCH_QUERIES.labels(search_type="vector").inc()
            SEARCH_DURATION.labels(search_type="vector").observe(duration)

    def text_search(self, query: str, limit: Optional[int] = 50) -> QuerySet[News]:
        """
        Perform sophisticated full-text search using PostgreSQL FTS.

        Features:
        - Uses pre-generated ts_vector_content columns for both news and articles
        - Weights: article content (1.0) > news content (0.8)
        - news.ts_vector_content includes: headline, summary, bullets, tags
        - articles.ts_vector_content includes: full article text
        - Relevance ranking with ts_rank_cd
        - Recency boost: newer articles get subtle ranking boost
        - Handles phrases (in quotes), boolean operators, and complex queries
        - Fallback to simple search if advanced FTS fails

        Args:
            query: Search query string
            limit: Maximum number of results (None for unlimited)

        Returns:
            QuerySet of News objects ordered by relevance
        """
        start_time = time.time()
        # Parse and enhance the query
        parsed_query = self.parse_query(query)
        if not parsed_query:
            return News.objects.none()

        try:
            # Use raw SQL to leverage full PostgreSQL FTS capabilities with articles table
            # Use pre-generated ts_vector_content columns for both news and articles
            # Add recency boost: more recent articles get subtle ranking improvement
            if limit is None:
                raw_sql = """
                    SELECT DISTINCT n.id,
                           (COALESCE(news_content_rank, 0) * 0.8 + COALESCE(article_content_rank, 0) * 1.0) *
                           (1.0 + (0.05 / (1.0 + EXTRACT(EPOCH FROM (NOW() - COALESCE(n.article_date, n.created_at))) / 86400.0))) as combined_rank,
                           n.article_date,
                           n.created_at
                    FROM news n
                    LEFT JOIN articles a ON n.article_id = a.id
                    LEFT JOIN LATERAL (
                        SELECT CASE
                            WHEN n.ts_vector_content IS NOT NULL
                            THEN ts_rank_cd(n.ts_vector_content, plainto_tsquery('english', %s))
                            ELSE 0
                        END as news_content_rank
                    ) news_content ON true
                    LEFT JOIN LATERAL (
                        SELECT CASE
                            WHEN a.ts_vector_content IS NOT NULL
                            THEN ts_rank_cd(a.ts_vector_content, plainto_tsquery('english', %s))
                            ELSE 0
                        END as article_content_rank
                    ) article_content ON true
                    WHERE n.deleted_at IS NULL
                      AND n.status = 'published'
                      AND (news_content_rank > 0 OR article_content_rank > 0)
                    ORDER BY combined_rank DESC, n.article_date DESC, n.created_at DESC
                """
                sql_params = [query, query]
            else:
                raw_sql = """
                    SELECT DISTINCT n.id,
                           (COALESCE(news_content_rank, 0) * 0.8 + COALESCE(article_content_rank, 0) * 1.0) *
                           (1.0 + (0.05 / (1.0 + EXTRACT(EPOCH FROM (NOW() - COALESCE(n.article_date, n.created_at))) / 86400.0))) as combined_rank,
                           n.article_date,
                           n.created_at
                    FROM news n
                    LEFT JOIN articles a ON n.article_id = a.id
                    LEFT JOIN LATERAL (
                        SELECT CASE
                            WHEN n.ts_vector_content IS NOT NULL
                            THEN ts_rank_cd(n.ts_vector_content, plainto_tsquery('english', %s))
                            ELSE 0
                        END as news_content_rank
                    ) news_content ON true
                    LEFT JOIN LATERAL (
                        SELECT CASE
                            WHEN a.ts_vector_content IS NOT NULL
                            THEN ts_rank_cd(a.ts_vector_content, plainto_tsquery('english', %s))
                            ELSE 0
                        END as article_content_rank
                    ) article_content ON true
                    WHERE n.deleted_at IS NULL
                      AND n.status = 'published'
                      AND (news_content_rank > 0 OR article_content_rank > 0)
                    ORDER BY combined_rank DESC, n.article_date DESC, n.created_at DESC
                    LIMIT %s
                """
                sql_params = [query, query, str(limit)]

            with connection.cursor() as cursor:
                cursor.execute(raw_sql, sql_params)
                results = cursor.fetchall()

            if not results:
                # Try fallback with plainto_tsquery if to_tsquery fails
                return self.fallback_text_search(query, limit)

            # Extract news IDs in ranked order
            news_ids = [row[0] for row in results]

            # Return News objects preserving the ranked order
            if news_ids:
                order_case = (
                    "CASE "
                    + " ".join(
                        [
                            f"WHEN id = {news_id} THEN {i}"
                            for i, news_id in enumerate(news_ids)
                        ]
                    )
                    + " END"
                )

                return News.objects.filter(id__in=news_ids).extra(
                    select={"ordering": order_case}, order_by=["ordering"]
                )
        except Exception:
            # Fallback to simple text search if FTS fails
            return self.fallback_text_search(query, limit)
        finally:
            # Record metrics
            duration = time.time() - start_time
            SEARCH_QUERIES.labels(search_type="text").inc()
            SEARCH_DURATION.labels(search_type="text").observe(duration)

        return News.objects.none()

    def hybrid_search(self, query: str, limit: int = 50) -> QuerySet[News]:
        """
        Combine vector similarity search with traditional text search.
        Returns vector results first, then fills with text search results.

        Args:
            query: Search query string
            limit: Maximum number of results

        Returns:
            QuerySet of News objects ordered by combined relevance
        """
        start_time = time.time()
        try:
            # Get vector search results first (always include these)
            vector_results = self.vector_search(query, limit=min(30, limit))
            vector_ids = list(vector_results.values_list("id", flat=True))

            # If we already have enough results from vector search, return them
            if len(vector_ids) >= limit:
                return vector_results[:limit]

            # Get text search results to fill remaining slots
            # Use the advanced text search instead of simple icontains
            text_results = self.text_search(
                query, limit=limit * 2
            )  # Get more to filter
            text_ids = list(text_results.values_list("id", flat=True))

            # Exclude vector results from text results and get remaining slots
            remaining_text_ids = [id for id in text_ids if id not in vector_ids]
            remaining_slots = limit - len(vector_ids)
            final_text_ids = remaining_text_ids[:remaining_slots]

            # Combine results: vector first, then text
            combined_ids = vector_ids + final_text_ids

            # Return combined queryset maintaining order
            if combined_ids:
                # Apply limit if specified
                final_ids = combined_ids if limit is None else combined_ids[:limit]

                ordering = (
                    "CASE "
                    + " ".join(
                        [f"WHEN id = {id} THEN {i}" for i, id in enumerate(final_ids)]
                    )
                    + " END"
                )
                return News.objects.filter(id__in=final_ids).extra(
                    select={"ordering": ordering}, order_by=["ordering"]
                )
            else:
                return News.objects.none()

        except Exception:
            # Fallback to vector search if hybrid fails, then text search
            vector_fallback = self.vector_search(query, limit)
            if vector_fallback.exists():
                return vector_fallback
            return self.text_search(query, limit)
        finally:
            # Record metrics
            duration = time.time() - start_time
            SEARCH_QUERIES.labels(search_type="hybrid").inc()
            SEARCH_DURATION.labels(search_type="hybrid").observe(duration)

    def parse_query(self, query: str) -> str:
        """
        Parse and enhance search queries to leverage PostgreSQL FTS capabilities.

        Supports:
        - Quoted phrases: "exact phrase"
        - Boolean operators: AND, OR, NOT, &, |, !
        - Wildcard searches
        - Field-specific searches (future enhancement)

        Args:
            query: Raw search query string

        Returns:
            Parsed query string ready for PostgreSQL FTS
        """
        if not query or not query.strip():
            return ""

        query = query.strip()

        # Handle quoted phrases by preserving them
        # PostgreSQL FTS will handle quoted phrases in tsquery

        # Convert common boolean operators to PostgreSQL syntax
        # Note: plainto_tsquery handles most of this, but we can enhance it

        # For now, let PostgreSQL handle it with plainto_tsquery
        # which automatically handles phrases in quotes
        return query

    def convert_to_tsquery(self, query: str) -> str:
        """
        Convert user query to PostgreSQL tsquery format.
        Handles phrases, operators, and normalizes the query.

        Args:
            query: User search query

        Returns:
            PostgreSQL tsquery formatted string
        """
        # Remove extra whitespace
        query = re.sub(r"\s+", " ", query.strip())

        # Handle quoted phrases - convert to PostgreSQL phrase syntax
        # "exact phrase" becomes 'exact <-> phrase'
        def replace_quoted_phrases(match: re.Match[str]) -> str:
            phrase = match.group(1)
            words = phrase.split()
            if len(words) > 1:
                return " <-> ".join(words)
            return phrase

        # Replace quoted phrases with proximity operators
        query = re.sub(r'"([^"]+)"', replace_quoted_phrases, query)

        # For now, let PostgreSQL handle the rest with plainto_tsquery
        # which automatically handles phrases and operators
        return query

    def fallback_text_search(
        self, query: str, limit: Optional[int] = 50
    ) -> QuerySet[News]:
        """
        Fallback simple text search when advanced FTS fails.

        Args:
            query: Search query string
            limit: Maximum number of results (None for unlimited)

        Returns:
            QuerySet of News objects
        """
        queryset = News.objects.filter(
            Q(title__icontains=query)
            | Q(summary__icontains=query)
            | Q(llm_headline__icontains=query)
            | Q(llm_summary__icontains=query)
            | Q(llm_tags__contains=[query])
            | Q(content_text__icontains=query),
            deleted_at__isnull=True,
            status="published",
        ).order_by("-article_date", "-created_at")
        if limit is not None:
            return queryset[:limit]
        return queryset
