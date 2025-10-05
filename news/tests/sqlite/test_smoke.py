"""
SQLite smoke tests - minimal, fast CI/CD checks.

These tests verify basic functionality without requiring PostgreSQL features:
- URL routing and resolution
- Basic view responses (without database writes)
- SEO endpoints (robots.txt, sitemap.xml)
- Template rendering

Tests that require News object creation are excluded (ArrayField not SQLite-compatible).
"""

from django.test import Client, TestCase
from django.urls import reverse

from news.models import Tag


class UrlResolutionSmokeTests(TestCase):
    """Smoke tests for URL resolution."""

    def test_news_list_resolves(self) -> None:
        """Test that news:list resolves to /."""
        url = reverse("news:list")
        self.assertEqual(url, "/")

    def test_news_search_resolves(self) -> None:
        """Test that news:search resolves to /search."""
        url = reverse("news:search")
        self.assertEqual(url, "/search")

    def test_tags_index_resolves(self) -> None:
        """Test that news:tags_index resolves to /tags."""
        url = reverse("news:tags_index")
        self.assertEqual(url, "/tags")

    def test_tag_detail_resolves(self) -> None:
        """Test that news:tag_detail resolves to /tag/{slug}."""
        url = reverse("news:tag_detail", kwargs={"tag_slug": "python"})
        self.assertEqual(url, "/tag/python")


class BasicViewSmokeTests(TestCase):
    """Smoke tests for basic view responses."""

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

    def test_homepage_uses_correct_template(self) -> None:
        """Test that homepage uses correct template."""
        response = self.client.get(reverse("news:list"))
        self.assertTemplateUsed(response, "news/news_list.html")

    def test_search_uses_correct_template(self) -> None:
        """Test that search uses correct template."""
        response = self.client.get(reverse("news:search"))
        self.assertTemplateUsed(response, "news/news_search.html")

    def test_tags_index_uses_correct_template(self) -> None:
        """Test that tags index uses correct template."""
        response = self.client.get(reverse("news:tags_index"))
        self.assertTemplateUsed(response, "news/tags_index.html")


class SeoEndpointSmokeTests(TestCase):
    """Smoke tests for SEO endpoints."""

    def setUp(self) -> None:
        """Set up test client."""
        self.client = Client()

    def test_robots_txt_returns_200(self) -> None:
        """Test that robots.txt returns 200."""
        response = self.client.get("/robots.txt")
        self.assertEqual(response.status_code, 200)

    def test_robots_txt_content_type(self) -> None:
        """Test that robots.txt has correct content type."""
        response = self.client.get("/robots.txt")
        self.assertEqual(response["Content-Type"], "text/plain")

    def test_robots_txt_contains_user_agent(self) -> None:
        """Test that robots.txt contains User-agent."""
        response = self.client.get("/robots.txt")
        content = response.content.decode("utf-8")
        self.assertIn("User-agent:", content)

    def test_robots_txt_contains_sitemap(self) -> None:
        """Test that robots.txt contains Sitemap reference."""
        response = self.client.get("/robots.txt")
        content = response.content.decode("utf-8")
        self.assertIn("Sitemap:", content)

    def test_sitemap_xml_returns_200(self) -> None:
        """Test that sitemap.xml returns 200."""
        response = self.client.get("/sitemap.xml")
        self.assertEqual(response.status_code, 200)

    def test_sitemap_xml_content_type(self) -> None:
        """Test that sitemap.xml has XML content type."""
        response = self.client.get("/sitemap.xml")
        content_type = response["Content-Type"]
        self.assertIn("xml", content_type.lower())

    def test_sitemap_xml_valid_structure(self) -> None:
        """Test that sitemap.xml is valid XML."""
        from xml.etree import ElementTree as ET

        response = self.client.get("/sitemap.xml")
        try:
            ET.fromstring(response.content)
        except ET.ParseError:
            self.fail("Sitemap is not valid XML")


class TagModelSmokeTests(TestCase):
    """Smoke tests for Tag model (no ArrayField dependency)."""

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


class SearchSmokeTests(TestCase):
    """Smoke tests for search (query handling, no results verification)."""

    def setUp(self) -> None:
        """Set up test client."""
        self.client = Client()
        self.url = reverse("news:search")

    def test_empty_query_returns_no_results(self) -> None:
        """Test that empty query returns no results."""
        response = self.client.get(self.url + "?q=")
        self.assertEqual(response.context["total_count"], 0)

    def test_search_type_preserved_in_context(self) -> None:
        """Test that search type is preserved (no actual search performed)."""
        response = self.client.get(self.url + "?q=test&type=vector")
        self.assertEqual(response.context["search_type"], "vector")
