"""
SQLite-compatible tests that don't require PostgreSQL features.

These tests run successfully on SQLite and don't depend on:
- ArrayField (llm_tags, llm_bullets)
- VectorField (content_embedding)
- Generated columns (ts_vector_content)
"""

from django.test import Client, TestCase, override_settings
from django.urls import reverse

from news.models import Tag


@override_settings(RATELIMIT_ENABLE=False)
class BasicUrlTests(TestCase):
    """Basic URL tests that work on SQLite."""

    def setUp(self) -> None:
        """Set up test client."""
        self.client = Client()

    def test_homepage_returns_200(self) -> None:
        """Test that homepage returns 200."""
        response = self.client.get(reverse("news:list"))
        self.assertEqual(response.status_code, 200)

    def test_search_page_returns_200(self) -> None:
        """Test that search page returns 200."""
        response = self.client.get(reverse("news:search"))
        self.assertEqual(response.status_code, 200)

    def test_tags_index_returns_200(self) -> None:
        """Test that tags index returns 200."""
        response = self.client.get(reverse("news:tags_index"))
        self.assertEqual(response.status_code, 200)

    def test_robots_txt_returns_200(self) -> None:
        """Test that robots.txt returns 200."""
        response = self.client.get("/robots.txt")
        self.assertEqual(response.status_code, 200)

    def test_sitemap_xml_returns_200(self) -> None:
        """Test that sitemap.xml returns 200."""
        response = self.client.get("/sitemap.xml")
        self.assertEqual(response.status_code, 200)


class BasicTagTests(TestCase):
    """Basic tag tests that work on SQLite."""

    def test_tag_creation(self) -> None:
        """Test creating a tag."""
        tag = Tag.objects.create(name="Python", slug="python")
        self.assertEqual(tag.name, "Python")
        self.assertEqual(tag.slug, "python")

    def test_tag_slug_auto_generation(self) -> None:
        """Test that tag slug is auto-generated."""
        tag = Tag.objects.create(name="Machine Learning")
        self.assertEqual(tag.slug, "machine-learning")

    def test_tag_slug_handles_special_chars(self) -> None:
        """Test that tag slug handles special characters."""
        test_cases = [
            ("React.js", "reactjs"),
            ("C++", "c"),
            ("Node.js & Express", "nodejs-express"),
        ]

        for name, expected_slug in test_cases:
            tag = Tag.objects.create(name=name)
            self.assertEqual(tag.slug, expected_slug)
            tag.delete()


class RobotsTxtTests(TestCase):
    """Tests for robots.txt that work on SQLite."""

    def setUp(self) -> None:
        """Set up test client."""
        self.client = Client()
        self.url = "/robots.txt"

    def test_returns_200(self) -> None:
        """Test that robots.txt returns 200."""
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)

    def test_content_type_is_text_plain(self) -> None:
        """Test that content type is text/plain."""
        response = self.client.get(self.url)
        self.assertEqual(response["Content-Type"], "text/plain")

    def test_contains_user_agent(self) -> None:
        """Test that robots.txt contains User-agent."""
        response = self.client.get(self.url)
        content = response.content.decode("utf-8")
        self.assertIn("User-agent:", content)

    def test_contains_sitemap_reference(self) -> None:
        """Test that robots.txt contains Sitemap reference."""
        response = self.client.get(self.url)
        content = response.content.decode("utf-8")
        self.assertIn("Sitemap:", content)


class SitemapTests(TestCase):
    """Basic sitemap tests that work on SQLite."""

    def setUp(self) -> None:
        """Set up test client."""
        self.client = Client()
        self.url = "/sitemap.xml"

    def test_returns_200(self) -> None:
        """Test that sitemap returns 200."""
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)

    def test_content_type_is_xml(self) -> None:
        """Test that content type is XML."""
        response = self.client.get(self.url)
        content_type = response["Content-Type"]
        self.assertIn("xml", content_type.lower())

    def test_valid_xml_structure(self) -> None:
        """Test that sitemap is valid XML."""
        from xml.etree import ElementTree as ET

        response = self.client.get(self.url)
        try:
            ET.fromstring(response.content)
        except ET.ParseError:
            self.fail("Sitemap is not valid XML")

    def test_empty_sitemap_is_valid(self) -> None:
        """Test that empty sitemap (no articles/tags) is still valid XML."""
        response = self.client.get(self.url)
        content = response.content.decode("utf-8")

        # Empty sitemap should still be valid XML with urlset element
        self.assertIn("<urlset", content)
        self.assertIn("</urlset>", content)
        # Should not contain any URLs
        self.assertNotIn("<loc>", content)


class UrlResolutionTests(TestCase):
    """URL resolution tests that work on SQLite."""

    def test_news_list_resolves(self) -> None:
        """Test that news:list resolves."""
        url = reverse("news:list")
        self.assertEqual(url, "/")

    def test_news_search_resolves(self) -> None:
        """Test that news:search resolves."""
        url = reverse("news:search")
        self.assertEqual(url, "/search")

    def test_tags_index_resolves(self) -> None:
        """Test that news:tags_index resolves."""
        url = reverse("news:tags_index")
        self.assertEqual(url, "/tags")

    def test_tag_detail_resolves(self) -> None:
        """Test that news:tag_detail resolves."""
        url = reverse("news:tag_detail", kwargs={"tag_slug": "python"})
        self.assertEqual(url, "/tag/python")


@override_settings(RATELIMIT_ENABLE=False)
class TemplateTests(TestCase):
    """Template tests that work on SQLite."""

    def setUp(self) -> None:
        """Set up test client."""
        self.client = Client()

    def test_news_list_template(self) -> None:
        """Test that news list uses correct template."""
        response = self.client.get(reverse("news:list"))
        self.assertTemplateUsed(response, "news/news_list.html")

    def test_search_template(self) -> None:
        """Test that search uses correct template."""
        response = self.client.get(reverse("news:search"))
        self.assertTemplateUsed(response, "news/news_search.html")

    def test_tags_index_template(self) -> None:
        """Test that tags index uses correct template."""
        response = self.client.get(reverse("news:tags_index"))
        self.assertTemplateUsed(response, "news/tags_index.html")


@override_settings(RATELIMIT_ENABLE=False)
class SearchRateLimitTests(TestCase):
    """Test search rate limiting (works on SQLite)."""

    def setUp(self) -> None:
        """Set up test client."""
        self.client = Client()
        self.url = reverse("news:search")

    def test_empty_query_returns_no_results(self) -> None:
        """Test that empty query returns no results."""
        response = self.client.get(self.url + "?q=")
        self.assertEqual(response.context["total_count"], 0)

    def test_search_type_preserved_in_context(self) -> None:
        """Test that search type is preserved."""
        response = self.client.get(self.url + "?q=test&type=vector")
        self.assertEqual(response.context["search_type"], "vector")

    def test_defaults_to_hybrid_search(self) -> None:
        """Test that search defaults to hybrid."""
        response = self.client.get(self.url + "?q=test")
        self.assertEqual(response.context["search_type"], "hybrid")
