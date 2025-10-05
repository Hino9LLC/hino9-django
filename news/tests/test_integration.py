"""
Test cases for end-to-end user journeys and integration flows.

Tests validate complete user experiences across multiple pages and actions.
"""

from unittest.mock import MagicMock, patch

from django.test import Client, TestCase
from django.urls import reverse
from django.utils import timezone

from news.models import News, Tag


class ArticleDiscoveryJourneyTests(TestCase):
    """Test cases for article discovery user journey."""

    def setUp(self) -> None:
        """Set up test data."""
        self.client = Client()

        # Create test articles
        self.article1 = News.objects.create(
            title="Breaking: AI Breakthrough in Medical Research",
            llm_headline="AI Achieves Major Medical Research Milestone",
            llm_summary="Researchers announce significant advancement in AI-powered drug discovery, potentially accelerating treatment development.",
            llm_bullets=[
                "AI system discovers new drug compounds",
                "Clinical trials expected next year",
                "Partnership with major pharmaceutical companies",
            ],
            llm_tags=["AI", "Healthcare", "Medical Research"],
            status="published",
            deleted_at=None,
            article_date=timezone.now(),
        )
        self.article2 = News.objects.create(
            title="Tech Giants Announce Climate Initiative",
            llm_headline="Major Tech Companies Unite for Climate Action",
            llm_summary="Leading technology companies pledge carbon neutrality and launch joint environmental initiative.",
            llm_bullets=[
                "$10 billion fund established",
                "Target: Carbon neutral by 2030",
                "Focus on renewable energy",
            ],
            llm_tags=["Climate", "Technology", "Environment"],
            status="published",
            deleted_at=None,
            article_date=timezone.now(),
        )

    def test_homepage_to_article_to_back(self) -> None:
        """Test: User lands on homepage -> clicks article -> clicks back."""
        # Step 1: User lands on homepage
        response = self.client.get(reverse("news:list"))
        self.assertEqual(response.status_code, 200)

        # Verify article list is shown
        self.assertIn("news_articles", response.context)

        # Step 2: User clicks article
        article_url = reverse(
            "news:detail",
            kwargs={"news_id": self.article1.id, "slug": self.article1.slug},
        )
        response = self.client.get(article_url)
        self.assertEqual(response.status_code, 200)

        # Verify article detail is shown
        self.assertEqual(response.context["news_article"], self.article1)

        # Step 3: User clicks back
        back_url = reverse("news:list")
        response = self.client.get(back_url)
        self.assertEqual(response.status_code, 200)

    def test_pagination_preserves_page_on_back(self) -> None:
        """Test: User on page 2 -> clicks article -> clicks back -> returns to page 2."""
        # Create 25 articles to enable pagination
        topics = ["Technology", "Science", "Business", "Health", "Sports"]
        for i in range(25):
            topic = topics[i % len(topics)]
            News.objects.create(
                title=f"{topic} Update: Latest Developments {i}",
                llm_headline=f"{topic} News Headlines",
                llm_summary=f"Recent developments in {topic} sector showing interesting trends.",
                llm_bullets=[
                    f"Key point {i}.1",
                    f"Key point {i}.2",
                    f"Key point {i}.3",
                ],
                llm_tags=[topic, "News", "Latest"],
                status="published",
                deleted_at=None,
            )

        # Step 1: User navigates to page 2
        response = self.client.get(reverse("news:list") + "?page=2")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context["page_obj"].number, 2)

        # Step 2: User clicks article (should include from_page=2)
        article = response.context["news_articles"][0]
        article_url = reverse(
            "news:detail",
            kwargs={"news_id": article.id, "slug": article.slug},
        )
        response = self.client.get(article_url + "?from_page=2")
        self.assertEqual(response.status_code, 200)

        # Verify from_page context is preserved
        self.assertEqual(response.context["from_page"], "2")

        # Step 3: User clicks back (should return to page 2)
        back_url = reverse("news:list") + "?page=2"
        response = self.client.get(back_url)
        self.assertEqual(response.context["page_obj"].number, 2)


class TagBrowsingJourneyTests(TestCase):
    """Test cases for tag browsing user journey."""

    def setUp(self) -> None:
        """Set up test data."""
        self.client = Client()

        # Create test tag
        self.tag = Tag.objects.create(name="Python", slug="python")

        # Create test article with tag
        self.article = News.objects.create(
            title="Python 3.12 Released with Performance Improvements",
            llm_headline="Python 3.12 Brings Speed Boost and New Features",
            llm_summary="The latest Python release includes significant performance improvements and new language features.",
            llm_bullets=[
                "20% faster than Python 3.11",
                "Improved error messages",
                "New type system enhancements",
            ],
            llm_tags=["Python", "Programming", "Software Development"],
            status="published",
            deleted_at=None,
        )

    @patch("news.models.Tag.get_news_count")
    @patch("news.models.Tag.objects.get_articles_for_tag")
    def test_tags_index_to_tag_to_article_to_back(
        self, mock_get_articles: MagicMock, mock_get_news_count: MagicMock
    ) -> None:
        """Test: Tags index -> tag detail -> article -> back to tag."""
        # Mock the methods
        from typing import Any

        from django.db.models import QuerySet

        mock_get_news_count.return_value = 5
        mock_queryset: Any = QuerySet(model=News).filter(id=self.article.id)
        mock_get_articles.return_value = mock_queryset

        # Step 1: User visits tags index
        response = self.client.get(reverse("news:tags_index"))
        self.assertEqual(response.status_code, 200)
        self.assertIn("tags", response.context)

        # Step 2: User clicks tag
        tag_url = reverse("news:tag_detail", kwargs={"tag_slug": self.tag.slug})
        response = self.client.get(tag_url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context["tag"], self.tag)

        # Step 3: User clicks article (with tag context)
        article_url = reverse(
            "news:detail",
            kwargs={"news_id": self.article.id, "slug": self.article.slug},
        )
        response = self.client.get(
            article_url
            + f"?from_tag=1&tag_slug={self.tag.slug}&tag_name={self.tag.name}"
        )
        self.assertEqual(response.status_code, 200)

        # Verify tag context is preserved
        self.assertEqual(response.context["from_tag"], "1")
        self.assertEqual(response.context["tag_slug"], self.tag.slug)

        # Step 4: User clicks back
        back_url = reverse("news:tag_detail", kwargs={"tag_slug": self.tag.slug})
        response = self.client.get(back_url)
        self.assertEqual(response.status_code, 200)


class SearchJourneyTests(TestCase):
    """Test cases for search user journey."""

    def setUp(self) -> None:
        """Set up test data."""
        self.client = Client()

        # Create test articles
        self.article = News.objects.create(
            title="Python Programming Best Practices Guide",
            llm_headline="Essential Python Programming Patterns",
            llm_summary="Comprehensive guide to Python best practices including design patterns, testing, and performance optimization.",
            llm_bullets=[
                "Follow PEP 8 style guide",
                "Use type hints for clarity",
                "Write comprehensive tests",
            ],
            llm_tags=["Python", "Programming", "Best Practices"],
            status="published",
            deleted_at=None,
        )

    def test_search_to_article_to_back_preserves_query(self) -> None:
        """Test: Search -> article -> back preserves search context."""
        # Step 1: User performs search
        search_url = reverse("news:search") + "?q=python&type=text"
        response = self.client.get(search_url)
        self.assertEqual(response.status_code, 200)

        # Step 2: User clicks article (with search context)
        article_url = reverse(
            "news:detail",
            kwargs={"news_id": self.article.id, "slug": self.article.slug},
        )
        response = self.client.get(article_url + "?from_search=1&q=python&type=text")
        self.assertEqual(response.status_code, 200)

        # Verify search context is preserved
        self.assertEqual(response.context["from_search"], "1")
        self.assertEqual(response.context["search_query"], "python")
        self.assertEqual(response.context["search_type"], "text")

        # Step 3: User clicks back
        back_url = reverse("news:search") + "?q=python&type=text"
        response = self.client.get(back_url)
        self.assertEqual(response.status_code, 200)
        self.assertIn("python", response.context["query"])

    @patch("news.services.search_service.get_embedding_service")
    def test_search_type_selection_flow(self, mock_get_service: MagicMock) -> None:
        """Test: User tries different search types."""
        mock_service = MagicMock()
        mock_service.generate_embedding.return_value = [0.1] * 768
        mock_get_service.return_value = mock_service

        # Step 1: Hybrid search (default)
        response = self.client.get(reverse("news:search") + "?q=python")
        self.assertEqual(response.context["search_type"], "hybrid")

        # Step 2: Text search
        response = self.client.get(reverse("news:search") + "?q=python&type=text")
        self.assertEqual(response.context["search_type"], "text")

        # Step 3: Vector search
        response = self.client.get(reverse("news:search") + "?q=python&type=vector")
        self.assertEqual(response.context["search_type"], "vector")


class SocialSharingScenarioTests(TestCase):
    """Test cases for social sharing scenario."""

    def setUp(self) -> None:
        """Set up test data."""
        self.client = Client()

        self.article = News.objects.create(
            title="Social Media Platforms Update Privacy Policies",
            llm_headline="Major Social Networks Enhance User Privacy Controls",
            llm_summary="Leading social media platforms announce comprehensive updates to privacy policies and user data controls.",
            llm_bullets=[
                "Enhanced privacy settings",
                "Greater transparency",
                "User data download options",
            ],
            llm_tags=["Social Media", "Privacy", "Technology"],
            image_url="http://example.com/social-privacy.jpg",
            status="published",
            deleted_at=None,
        )

    def test_article_has_social_meta_tags(self) -> None:
        """Test that article has all required social meta tags."""
        url = reverse(
            "news:detail",
            kwargs={"news_id": self.article.id, "slug": self.article.slug},
        )
        response = self.client.get(url)
        content = response.content.decode("utf-8")

        # Verify Open Graph tags
        self.assertIn('property="og:title"', content)
        self.assertIn('property="og:description"', content)
        self.assertIn('property="og:image"', content)
        self.assertIn('property="og:type"', content)
        self.assertIn('property="og:url"', content)

        # Verify Twitter Card tags
        self.assertIn('name="twitter:card"', content)
        self.assertIn('name="twitter:title"', content)
        self.assertIn('name="twitter:description"', content)
        self.assertIn('name="twitter:image"', content)


class SeoCrawlerScenarioTests(TestCase):
    """Test cases for SEO crawler scenario."""

    def setUp(self) -> None:
        """Set up test data."""
        self.client = Client()

        self.article = News.objects.create(
            title="SEO Best Practices for Modern Websites",
            llm_headline="Complete Guide to Search Engine Optimization",
            llm_summary="Learn essential SEO techniques including technical optimization, content strategy, and link building.",
            llm_bullets=[
                "Optimize page speed and Core Web Vitals",
                "Create quality content",
                "Build authoritative backlinks",
            ],
            llm_tags=["SEO", "Web Development", "Marketing"],
            status="published",
            deleted_at=None,
        )

    def test_crawler_discovers_site_via_robots_and_sitemap(self) -> None:
        """Test: Crawler fetches robots.txt -> sitemap -> article."""
        # Step 1: Crawler fetches robots.txt
        response = self.client.get("/robots.txt")
        self.assertEqual(response.status_code, 200)
        content = response.content.decode("utf-8")

        # Verify sitemap URL is present
        self.assertIn("Sitemap:", content)

        # Step 2: Crawler fetches sitemap
        response = self.client.get("/sitemap.xml")
        self.assertEqual(response.status_code, 200)

        # Verify article is in sitemap
        content = response.content.decode("utf-8")
        self.assertIn(f"/{self.article.id}/", content)

        # Step 3: Crawler fetches article
        url = reverse(
            "news:detail",
            kwargs={"news_id": self.article.id, "slug": self.article.slug},
        )
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)

        # Verify structured data and canonical URL
        content = response.content.decode("utf-8")
        self.assertIn('<script type="application/ld+json">', content)
        self.assertIn('<link rel="canonical"', content)


class ErrorHandlingJourneyTests(TestCase):
    """Test cases for error handling in user journeys."""

    def setUp(self) -> None:
        """Set up test data."""
        self.client = Client()

    def test_404_for_nonexistent_article(self) -> None:
        """Test that nonexistent article returns 404."""
        url = reverse("news:detail", kwargs={"news_id": 99999, "slug": "fake-slug"})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 404)

    def test_404_for_nonexistent_tag(self) -> None:
        """Test that nonexistent tag returns 404."""
        url = reverse("news:tag_detail", kwargs={"tag_slug": "nonexistent"})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 404)

    def test_unpublished_article_returns_404(self) -> None:
        """Test that unpublished article returns 404."""
        article = News.objects.create(
            title="Unpublished Draft Article",
            llm_headline="Draft: Work in Progress",
            llm_summary="This article is still being written and reviewed.",
            llm_bullets=["Not yet published", "Under review", "Coming soon"],
            llm_tags=["Draft"],
            status="draft",
            deleted_at=None,
        )

        url = reverse(
            "news:detail", kwargs={"news_id": article.id, "slug": article.slug}
        )
        response = self.client.get(url)
        self.assertEqual(response.status_code, 404)

    def test_deleted_article_returns_404(self) -> None:
        """Test that deleted article returns 404."""
        article = News.objects.create(
            title="Deleted Article No Longer Available",
            llm_headline="Article Removed",
            llm_summary="This article has been removed from the site.",
            llm_bullets=[
                "Content removed",
                "No longer available",
                "See other articles",
            ],
            llm_tags=["Deleted"],
            status="published",
            deleted_at=timezone.now(),
        )

        url = reverse(
            "news:detail", kwargs={"news_id": article.id, "slug": article.slug}
        )
        response = self.client.get(url)
        self.assertEqual(response.status_code, 404)


class NavigationContextTests(TestCase):
    """Test cases for navigation context preservation across pages."""

    def setUp(self) -> None:
        """Set up test data."""
        self.client = Client()

        self.article = News.objects.create(
            title="Navigation Context Testing Article",
            llm_headline="Testing User Navigation Patterns",
            llm_summary="Article used for testing navigation context preservation across different page views.",
            llm_bullets=[
                "Test navigation flow",
                "Verify context preservation",
                "Check back button behavior",
            ],
            llm_tags=["Testing", "Navigation", "UX"],
            status="published",
            deleted_at=None,
        )

    def test_from_page_context_preserved(self) -> None:
        """Test that from_page parameter is preserved in article detail."""
        url = reverse(
            "news:detail",
            kwargs={"news_id": self.article.id, "slug": self.article.slug},
        )
        response = self.client.get(url + "?from_page=3")

        self.assertEqual(response.context["from_page"], "3")

    def test_search_context_preserved(self) -> None:
        """Test that search context is preserved in article detail."""
        url = reverse(
            "news:detail",
            kwargs={"news_id": self.article.id, "slug": self.article.slug},
        )
        response = self.client.get(url + "?from_search=1&q=test&type=hybrid")

        self.assertEqual(response.context["from_search"], "1")
        self.assertEqual(response.context["search_query"], "test")
        self.assertEqual(response.context["search_type"], "hybrid")

    def test_tag_context_preserved(self) -> None:
        """Test that tag context is preserved in article detail."""
        url = reverse(
            "news:detail",
            kwargs={"news_id": self.article.id, "slug": self.article.slug},
        )
        response = self.client.get(url + "?from_tag=1&tag_slug=python&tag_name=Python")

        self.assertEqual(response.context["from_tag"], "1")
        self.assertEqual(response.context["tag_slug"], "python")
        self.assertEqual(response.context["tag_name"], "Python")

    def test_empty_navigation_context_uses_defaults(self) -> None:
        """Test that article detail works without navigation context."""
        url = reverse(
            "news:detail",
            kwargs={"news_id": self.article.id, "slug": self.article.slug},
        )
        response = self.client.get(url)

        # Should use defaults
        self.assertEqual(response.context["from_page"], "1")
        self.assertEqual(response.context["from_search"], "")
        self.assertEqual(response.context["from_tag"], "")
