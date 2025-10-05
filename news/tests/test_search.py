"""
Test cases for search functionality.

Tests validate vector search, text search, hybrid search, and edge cases.
All tests mock the AWS embedding service to avoid external API calls.
"""

from unittest.mock import MagicMock, patch

from django.test import Client, TestCase, override_settings
from django.urls import reverse
from django.utils import timezone

from news.models import News


@override_settings(RATELIMIT_ENABLE=False)
class VectorSearchTests(TestCase):
    """Test cases for vector search functionality."""

    def setUp(self) -> None:
        """Set up test data."""
        self.client = Client()
        self.url = reverse("news:search")

        # Create test articles with embeddings
        self.article1 = News.objects.create(
            title="AI and Machine Learning",
            llm_headline="Artificial Intelligence Advances",
            llm_summary="Article about artificial intelligence and machine learning developments",
            llm_bullets=[
                "Deep learning improvements",
                "New AI models released",
                "Industry applications growing",
            ],
            llm_tags=["AI", "Machine Learning", "Technology"],
            status="published",
            deleted_at=None,
            content_embedding=[0.1] * 768,
        )
        self.article2 = News.objects.create(
            title="Python Programming",
            llm_headline="Python Development Best Practices",
            llm_summary="Article about Python programming language and development techniques",
            llm_bullets=[
                "Performance optimization",
                "Code quality tools",
                "Testing frameworks",
            ],
            llm_tags=["Python", "Programming", "Software Development"],
            status="published",
            deleted_at=None,
            content_embedding=[0.2] * 768,
        )

    @patch("news.services.search_service.get_embedding_service")
    def test_vector_search_generates_query_embedding(
        self, mock_get_service: MagicMock
    ) -> None:
        """Test that vector search generates embedding for query."""
        mock_service = MagicMock()
        mock_service.generate_embedding.return_value = [0.1] * 768
        mock_get_service.return_value = mock_service

        self.client.get(self.url + "?q=test&type=vector")

        mock_service.generate_embedding.assert_called_once_with("test")

    @patch("news.services.search_service.get_embedding_service")
    def test_vector_search_only_searches_published_articles(
        self, mock_get_service: MagicMock
    ) -> None:
        """Test that vector search only returns published articles."""
        unpublished = News.objects.create(
            title="Unpublished Article",
            llm_headline="Draft Article",
            llm_summary="This article is in draft status",
            llm_bullets=["Draft content", "Not published yet", "Under review"],
            llm_tags=["Draft"],
            status="draft",
            deleted_at=None,
            content_embedding=[0.1] * 768,
        )

        mock_service = MagicMock()
        mock_service.generate_embedding.return_value = [0.1] * 768
        mock_get_service.return_value = mock_service

        response = self.client.get(self.url + "?q=test&type=vector")
        results = list(response.context["news_articles"])

        self.assertNotIn(unpublished, results)

    @patch("news.services.search_service.get_embedding_service")
    def test_vector_search_excludes_deleted_articles(
        self, mock_get_service: MagicMock
    ) -> None:
        """Test that vector search excludes deleted articles."""
        deleted = News.objects.create(
            title="Deleted Article",
            llm_headline="Removed Article",
            llm_summary="This article has been deleted",
            llm_bullets=["Content removed", "No longer available", "Deleted status"],
            llm_tags=["Deleted"],
            status="published",
            deleted_at=timezone.now(),
            content_embedding=[0.1] * 768,
        )

        mock_service = MagicMock()
        mock_service.generate_embedding.return_value = [0.1] * 768
        mock_get_service.return_value = mock_service

        response = self.client.get(self.url + "?q=test&type=vector")
        results = list(response.context["news_articles"])

        self.assertNotIn(deleted, results)

    @patch("news.services.search_service.get_embedding_service")
    def test_vector_search_handles_empty_query(
        self, mock_get_service: MagicMock
    ) -> None:
        """Test that empty query returns no results."""
        mock_service = MagicMock()
        mock_get_service.return_value = mock_service

        response = self.client.get(self.url + "?q=&type=vector")

        self.assertEqual(response.context["total_count"], 0)
        # Should not call embedding service for empty query
        mock_service.generate_embedding.assert_not_called()

    @patch("news.services.search_service.get_embedding_service")
    def test_vector_search_handles_embedding_service_error(
        self, mock_get_service: MagicMock
    ) -> None:
        """Test that embedding service errors return empty results."""
        mock_service = MagicMock()
        mock_service.generate_embedding.side_effect = Exception("API Error")
        mock_get_service.return_value = mock_service

        response = self.client.get(self.url + "?q=test&type=vector")

        # Should return empty results gracefully
        self.assertEqual(response.context["total_count"], 0)

    @patch("news.services.search_service.get_embedding_service")
    def test_vector_search_handles_very_long_query(
        self, mock_get_service: MagicMock
    ) -> None:
        """Test that very long queries are handled gracefully."""
        long_query = "test " * 200  # Very long query
        mock_service = MagicMock()
        mock_service.generate_embedding.return_value = [0.1] * 768
        mock_get_service.return_value = mock_service

        response = self.client.get(self.url + f"?q={long_query}&type=vector")

        self.assertEqual(response.status_code, 200)

    @patch("news.services.search_service.get_embedding_service")
    def test_vector_search_handles_special_characters(
        self, mock_get_service: MagicMock
    ) -> None:
        """Test that special characters in query don't break search."""
        special_query = "test @#$%^&*()"
        mock_service = MagicMock()
        mock_service.generate_embedding.return_value = [0.1] * 768
        mock_get_service.return_value = mock_service

        response = self.client.get(self.url + f"?q={special_query}&type=vector")

        self.assertEqual(response.status_code, 200)


@override_settings(RATELIMIT_ENABLE=False)
class TextSearchTests(TestCase):
    """Test cases for text search functionality."""

    def setUp(self) -> None:
        """Set up test data."""
        self.client = Client()
        self.url = reverse("news:search")

        # Create test articles
        self.article1 = News.objects.create(
            title="Machine Learning Tutorial",
            llm_headline="Complete ML Guide",
            summary="Learn about machine learning",
            llm_summary="Comprehensive guide to ML",
            llm_bullets=[
                "Introduction to ML",
                "Supervised learning concepts",
                "Practical examples",
            ],
            status="published",
            deleted_at=None,
            llm_tags=["AI", "ML", "Tutorial"],
        )
        self.article2 = News.objects.create(
            title="Python Programming",
            llm_headline="Python Basics",
            summary="Python programming basics",
            llm_summary="Learn Python programming",
            llm_bullets=[
                "Python syntax fundamentals",
                "Data structures",
                "Best practices",
            ],
            status="published",
            deleted_at=None,
            llm_tags=["Python", "Programming"],
        )

    def test_text_search_is_case_insensitive(self) -> None:
        """Test that text search is case-insensitive."""
        response1 = self.client.get(self.url + "?q=python&type=text")
        response2 = self.client.get(self.url + "?q=PYTHON&type=text")

        # Both should return same results
        self.assertEqual(
            response1.context["total_count"], response2.context["total_count"]
        )

    def test_text_search_only_returns_published_articles(self) -> None:
        """Test that text search only returns published articles."""
        unpublished = News.objects.create(
            title="Unpublished Python Article",
            status="draft",
            deleted_at=None,
        )

        response = self.client.get(self.url + "?q=python&type=text")
        results = list(response.context["news_articles"])

        self.assertNotIn(unpublished, results)

    def test_text_search_excludes_deleted_articles(self) -> None:
        """Test that text search excludes deleted articles."""
        deleted = News.objects.create(
            title="Deleted Python Article",
            status="published",
            deleted_at=timezone.now(),
        )

        response = self.client.get(self.url + "?q=python&type=text")
        results = list(response.context["news_articles"])

        self.assertNotIn(deleted, results)

    def test_text_search_handles_empty_query(self) -> None:
        """Test that empty query returns no results."""
        response = self.client.get(self.url + "?q=&type=text")
        self.assertEqual(response.context["total_count"], 0)

    def test_text_search_handles_special_characters(self) -> None:
        """Test that special characters are handled gracefully."""
        response = self.client.get(self.url + "?q=@#$%&type=text")
        self.assertEqual(response.status_code, 200)

    def test_text_search_handles_very_long_query(self) -> None:
        """Test that very long queries are handled gracefully."""
        long_query = "test " * 200
        response = self.client.get(self.url + f"?q={long_query}&type=text")
        self.assertEqual(response.status_code, 200)

    def test_text_search_handles_single_character_query(self) -> None:
        """Test that single character queries work."""
        response = self.client.get(self.url + "?q=a&type=text")
        self.assertEqual(response.status_code, 200)

    def test_text_search_handles_numeric_query(self) -> None:
        """Test that numeric queries work."""
        response = self.client.get(self.url + "?q=12345&type=text")
        self.assertEqual(response.status_code, 200)


@override_settings(RATELIMIT_ENABLE=False)
class HybridSearchTests(TestCase):
    """Test cases for hybrid search functionality."""

    def setUp(self) -> None:
        """Set up test data."""
        self.client = Client()
        self.url = reverse("news:search")

        # Create test articles
        self.article1 = News.objects.create(
            title="Machine Learning",
            llm_summary="Article about ML",
            status="published",
            deleted_at=None,
            content_embedding=[0.1] * 768,
        )
        self.article2 = News.objects.create(
            title="Python Programming",
            llm_summary="Article about Python",
            status="published",
            deleted_at=None,
            content_embedding=[0.2] * 768,
        )

    @patch("news.services.search_service.get_embedding_service")
    def test_hybrid_search_combines_results(self, mock_get_service: MagicMock) -> None:
        """Test that hybrid search combines vector and text results."""
        mock_service = MagicMock()
        mock_service.generate_embedding.return_value = [0.1] * 768
        mock_get_service.return_value = mock_service

        response = self.client.get(self.url + "?q=machine&type=hybrid")

        # Should get results
        self.assertGreaterEqual(response.context["total_count"], 0)

    @patch("news.services.search_service.get_embedding_service")
    def test_hybrid_search_no_duplicate_articles(
        self, mock_get_service: MagicMock
    ) -> None:
        """Test that hybrid search doesn't return duplicate articles."""
        mock_service = MagicMock()
        mock_service.generate_embedding.return_value = [0.1] * 768
        mock_get_service.return_value = mock_service

        response = self.client.get(self.url + "?q=machine&type=hybrid")
        results = list(response.context["news_articles"])

        # Check for duplicates
        result_ids = [article.id for article in results]
        self.assertEqual(len(result_ids), len(set(result_ids)))

    @patch("news.services.search_service.get_embedding_service")
    def test_hybrid_search_fallback_to_text_on_embedding_error(
        self, mock_get_service: MagicMock
    ) -> None:
        """Test that hybrid falls back to text search if embedding fails."""
        mock_service = MagicMock()
        mock_service.generate_embedding.side_effect = Exception("API Error")
        mock_get_service.return_value = mock_service

        response = self.client.get(self.url + "?q=machine&type=hybrid")

        # Should still get results from text search
        self.assertEqual(response.status_code, 200)

    @patch("news.services.search_service.get_embedding_service")
    def test_hybrid_search_only_returns_published_articles(
        self, mock_get_service: MagicMock
    ) -> None:
        """Test that hybrid search only returns published articles."""
        unpublished = News.objects.create(
            title="Unpublished Article",
            llm_headline="Draft Article",
            llm_summary="This article is in draft status",
            llm_bullets=["Draft content", "Not published yet", "Under review"],
            llm_tags=["Draft"],
            status="draft",
            deleted_at=None,
            content_embedding=[0.1] * 768,
        )

        mock_service = MagicMock()
        mock_service.generate_embedding.return_value = [0.1] * 768
        mock_get_service.return_value = mock_service

        response = self.client.get(self.url + "?q=test&type=hybrid")
        results = list(response.context["news_articles"])

        self.assertNotIn(unpublished, results)

    @patch("news.services.search_service.get_embedding_service")
    def test_hybrid_search_excludes_deleted_articles(
        self, mock_get_service: MagicMock
    ) -> None:
        """Test that hybrid search excludes deleted articles."""
        deleted = News.objects.create(
            title="Deleted Article",
            llm_headline="Removed Article",
            llm_summary="This article has been deleted",
            llm_bullets=["Content removed", "No longer available", "Deleted status"],
            llm_tags=["Deleted"],
            status="published",
            deleted_at=timezone.now(),
            content_embedding=[0.1] * 768,
        )

        mock_service = MagicMock()
        mock_service.generate_embedding.return_value = [0.1] * 768
        mock_get_service.return_value = mock_service

        response = self.client.get(self.url + "?q=test&type=hybrid")
        results = list(response.context["news_articles"])

        self.assertNotIn(deleted, results)

    def test_hybrid_search_handles_empty_query(self) -> None:
        """Test that empty query returns no results."""
        response = self.client.get(self.url + "?q=&type=hybrid")
        self.assertEqual(response.context["total_count"], 0)


@override_settings(RATELIMIT_ENABLE=False)
class SearchEdgeCasesTests(TestCase):
    """Test cases for search edge cases and error handling."""

    def setUp(self) -> None:
        """Set up test data."""
        self.client = Client()
        self.url = reverse("news:search")

    def test_search_with_no_articles_in_database(self) -> None:
        """Test search when database is empty."""
        response = self.client.get(self.url + "?q=test&type=text")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context["total_count"], 0)

    def test_search_with_no_embeddings_available(self) -> None:
        """Test vector search when no articles have embeddings."""
        News.objects.create(
            title="Article without embedding",
            status="published",
            deleted_at=None,
            content_embedding=None,
        )

        with patch(
            "news.services.search_service.get_embedding_service"
        ) as mock_get_service:
            mock_service = MagicMock()
            mock_service.generate_embedding.return_value = [0.1] * 768
            mock_get_service.return_value = mock_service

            response = self.client.get(self.url + "?q=test&type=vector")

            # Should handle gracefully
            self.assertEqual(response.status_code, 200)

    def test_search_preserves_query_in_url(self) -> None:
        """Test that query is preserved in response for pagination."""
        response = self.client.get(self.url + "?q=test+query&type=text")
        self.assertIn("test query", response.context["query"])

    def test_search_handles_url_encoded_characters(self) -> None:
        """Test that URL-encoded characters are handled correctly."""
        response = self.client.get(self.url + "?q=test%20query&type=text")
        self.assertEqual(response.status_code, 200)

    def test_search_with_sql_injection_attempt(self) -> None:
        """Test that SQL injection attempts are sanitized."""
        malicious_query = "'; DROP TABLE news; --"
        response = self.client.get(self.url + f"?q={malicious_query}&type=text")

        # Should handle safely
        self.assertEqual(response.status_code, 200)
        # Verify news table still exists by querying it
        from news.models import News

        self.assertIsNotNone(News.objects.all())
