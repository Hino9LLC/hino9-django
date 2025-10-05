"""
Test cases for SEO features.

Tests validate sitemap.xml, robots.txt, meta tags, structured data (JSON-LD),
and canonical URLs.
"""

import json
from unittest.mock import patch
from xml.etree import ElementTree as ET

from django.test import Client, TestCase
from django.urls import reverse
from django.utils import timezone

from news.models import News, Tag


class SitemapXmlTests(TestCase):
    """Test cases for sitemap.xml generation."""

    def setUp(self) -> None:
        """Set up test data."""
        self.client = Client()
        self.url = "/sitemap.xml"

        # Create test articles
        self.article1 = News.objects.create(
            title="Test Article 1",
            status="published",
            deleted_at=None,
            article_date=timezone.now(),
            llm_bullets=["Key point 1", "Key point 2", "Key point 3"],
            llm_tags=["Test", "SEO"],
        )
        self.article2 = News.objects.create(
            title="Test Article 2",
            status="published",
            deleted_at=None,
            article_date=timezone.now(),
            llm_bullets=["Key point 1", "Key point 2", "Key point 3"],
            llm_tags=["Test", "SEO"],
        )

        # Create test tag
        self.tag1 = Tag.objects.create(name="Python", slug="python")

    def test_returns_200(self) -> None:
        """Test that sitemap.xml returns HTTP 200."""
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)

    def test_content_type_is_xml(self) -> None:
        """Test that sitemap has XML content type."""
        response = self.client.get(self.url)
        content_type = response["Content-Type"]
        self.assertIn("xml", content_type.lower())

    def test_valid_xml_structure(self) -> None:
        """Test that sitemap is valid XML."""
        response = self.client.get(self.url)
        try:
            ET.fromstring(response.content)
        except ET.ParseError:
            self.fail("Sitemap is not valid XML")

    def test_contains_urlset_root_element(self) -> None:
        """Test that sitemap contains <urlset> root element."""
        response = self.client.get(self.url)
        root = ET.fromstring(response.content)
        self.assertTrue(root.tag.endswith("urlset"))

    def test_includes_published_articles(self) -> None:
        """Test that sitemap includes published articles."""
        response = self.client.get(self.url)
        content = response.content.decode("utf-8")

        # Check that article URLs are present
        self.assertIn(f"/{self.article1.id}/", content)
        self.assertIn(f"/{self.article2.id}/", content)

    def test_excludes_unpublished_articles(self) -> None:
        """Test that sitemap excludes unpublished articles."""
        unpublished = News.objects.create(
            title="Unpublished Article",
            status="draft",
            deleted_at=None,
            llm_bullets=["Key point 1", "Key point 2", "Key point 3"],
            llm_tags=["Test", "SEO"],
        )

        response = self.client.get(self.url)
        content = response.content.decode("utf-8")

        self.assertNotIn(f"/{unpublished.id}/", content)

    def test_excludes_deleted_articles(self) -> None:
        """Test that sitemap excludes deleted articles."""
        deleted = News.objects.create(
            title="Deleted Article",
            status="published",
            deleted_at=timezone.now(),
            llm_bullets=["Key point 1", "Key point 2", "Key point 3"],
            llm_tags=["Test", "SEO"],
        )

        response = self.client.get(self.url)
        content = response.content.decode("utf-8")

        self.assertNotIn(f"/{deleted.id}/", content)

    def test_includes_tags(self) -> None:
        """Test that sitemap includes tag pages."""
        response = self.client.get(self.url)
        content = response.content.decode("utf-8")

        # Sitemap URLs don't have trailing slash
        self.assertIn(f"/tag/{self.tag1.slug}", content)

    def test_article_urls_are_absolute(self) -> None:
        """Test that article URLs are absolute (include domain)."""
        response = self.client.get(self.url)
        content = response.content.decode("utf-8")

        # Should contain http:// or https://
        self.assertIn("http://", content)

    def test_article_has_lastmod_date(self) -> None:
        """Test that articles have <lastmod> date."""
        response = self.client.get(self.url)
        root = ET.fromstring(response.content)

        # Find article URL entries
        ns = {"sm": "http://www.sitemaps.org/schemas/sitemap/0.9"}
        urls = root.findall("sm:url", ns)

        # At least one URL should have lastmod
        has_lastmod = False
        for url in urls:
            lastmod = url.find("sm:lastmod", ns)
            if lastmod is not None:
                has_lastmod = True
                break

        self.assertTrue(has_lastmod, "No URLs have <lastmod> element")

    def test_article_has_changefreq(self) -> None:
        """Test that articles have <changefreq> element."""
        response = self.client.get(self.url)
        content = response.content.decode("utf-8")

        self.assertIn("<changefreq>", content)

    def test_article_has_priority(self) -> None:
        """Test that articles have <priority> element."""
        response = self.client.get(self.url)
        content = response.content.decode("utf-8")

        self.assertIn("<priority>", content)


class RobotsTxtTests(TestCase):
    """Test cases for robots.txt."""

    def setUp(self) -> None:
        """Set up test client."""
        self.client = Client()
        self.url = "/robots.txt"

    def test_returns_200(self) -> None:
        """Test that robots.txt returns HTTP 200."""
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)

    def test_content_type_is_text_plain(self) -> None:
        """Test that robots.txt has text/plain content type."""
        response = self.client.get(self.url)
        self.assertEqual(response["Content-Type"], "text/plain")

    def test_contains_user_agent(self) -> None:
        """Test that robots.txt contains User-agent directive."""
        response = self.client.get(self.url)
        content = response.content.decode("utf-8")
        self.assertIn("User-agent:", content)

    def test_contains_allow_directive(self) -> None:
        """Test that robots.txt contains Allow directive."""
        response = self.client.get(self.url)
        content = response.content.decode("utf-8")
        self.assertIn("Allow:", content)

    def test_contains_sitemap_reference(self) -> None:
        """Test that robots.txt contains Sitemap reference."""
        response = self.client.get(self.url)
        content = response.content.decode("utf-8")
        self.assertIn("Sitemap:", content)

    def test_sitemap_url_is_absolute(self) -> None:
        """Test that sitemap URL is absolute (includes domain)."""
        response = self.client.get(self.url)
        content = response.content.decode("utf-8")

        # Should contain full URL (http:// or https://)
        self.assertTrue("http://" in content or "https://" in content)
        self.assertIn("sitemap.xml", content)


class MetaTagsTests(TestCase):
    """Test cases for meta tags (Open Graph, Twitter Cards)."""

    def setUp(self) -> None:
        """Set up test data."""
        self.client = Client()
        self.article = News.objects.create(
            title="Test Article",
            llm_headline="Test Headline",
            summary="Test summary",
            llm_summary="AI-generated summary",
            image_url="http://example.com/image.jpg",
            status="published",
            deleted_at=None,
            llm_bullets=["Key point 1", "Key point 2", "Key point 3"],
            llm_tags=["Test", "SEO"],
        )
        self.url = reverse(
            "news:detail",
            kwargs={"news_id": self.article.id, "slug": self.article.slug},
        )

    def test_article_has_meta_description(self) -> None:
        """Test that article has meta description."""
        response = self.client.get(self.url)
        content = response.content.decode("utf-8")

        self.assertIn('<meta name="description"', content)

    def test_meta_description_uses_article_summary(self) -> None:
        """Test that meta description uses article summary."""
        response = self.client.get(self.url)
        content = response.content.decode("utf-8")

        # Should contain the article summary
        self.assertIn("AI-generated summary", content)

    def test_article_has_open_graph_title(self) -> None:
        """Test that article has Open Graph og:title."""
        response = self.client.get(self.url)
        content = response.content.decode("utf-8")

        self.assertIn('property="og:title"', content)

    def test_article_has_open_graph_description(self) -> None:
        """Test that article has Open Graph og:description."""
        response = self.client.get(self.url)
        content = response.content.decode("utf-8")

        self.assertIn('property="og:description"', content)

    def test_article_has_open_graph_image(self) -> None:
        """Test that article has Open Graph og:image."""
        response = self.client.get(self.url)
        content = response.content.decode("utf-8")

        self.assertIn('property="og:image"', content)

    def test_article_has_open_graph_type(self) -> None:
        """Test that article has Open Graph og:type as article."""
        response = self.client.get(self.url)
        content = response.content.decode("utf-8")

        self.assertIn('property="og:type"', content)
        self.assertIn('content="article"', content)

    def test_article_has_open_graph_url(self) -> None:
        """Test that article has Open Graph og:url."""
        response = self.client.get(self.url)
        content = response.content.decode("utf-8")

        self.assertIn('property="og:url"', content)

    def test_article_has_twitter_card_type(self) -> None:
        """Test that article has Twitter Card type."""
        response = self.client.get(self.url)
        content = response.content.decode("utf-8")

        self.assertIn('name="twitter:card"', content)
        self.assertIn('content="summary_large_image"', content)

    def test_article_has_twitter_card_title(self) -> None:
        """Test that article has Twitter Card title."""
        response = self.client.get(self.url)
        content = response.content.decode("utf-8")

        self.assertIn('name="twitter:title"', content)

    def test_article_has_twitter_card_description(self) -> None:
        """Test that article has Twitter Card description."""
        response = self.client.get(self.url)
        content = response.content.decode("utf-8")

        self.assertIn('name="twitter:description"', content)

    def test_article_has_twitter_card_image(self) -> None:
        """Test that article has Twitter Card image."""
        response = self.client.get(self.url)
        content = response.content.decode("utf-8")

        self.assertIn('name="twitter:image"', content)

    def test_article_without_image_uses_fallback(self) -> None:
        """Test that article without image uses default fallback."""
        article_no_image = News.objects.create(
            title="No Image Article",
            image_url=None,
            status="published",
            deleted_at=None,
            llm_bullets=["Key point 1", "Key point 2", "Key point 3"],
            llm_tags=["Test", "SEO"],
        )

        url = reverse(
            "news:detail",
            kwargs={"news_id": article_no_image.id, "slug": article_no_image.slug},
        )
        response = self.client.get(url)
        content = response.content.decode("utf-8")

        # Should still have image meta tags (with fallback)
        self.assertIn('property="og:image"', content)


class StructuredDataTests(TestCase):
    """Test cases for JSON-LD structured data."""

    def setUp(self) -> None:
        """Set up test data."""
        self.client = Client()
        self.article = News.objects.create(
            title="Structured Data Test Article",
            llm_headline="JSON-LD Testing",
            llm_summary="Article for testing structured data implementation",
            llm_bullets=["Structured data", "Schema.org", "SEO optimization"],
            llm_tags=["SEO", "Structured Data", "Testing"],
            status="published",
            deleted_at=None,
        )
        self.url = reverse(
            "news:detail",
            kwargs={"news_id": self.article.id, "slug": self.article.slug},
        )

    def test_article_has_json_ld_script_tag(self) -> None:
        """Test that article has JSON-LD script tag."""
        response = self.client.get(self.url)
        content = response.content.decode("utf-8")

        self.assertIn('<script type="application/ld+json">', content)

    def test_json_ld_is_valid_json(self) -> None:
        """Test that JSON-LD is valid JSON."""
        response = self.client.get(self.url)
        content = response.content.decode("utf-8")

        # Extract JSON-LD from HTML
        start = content.find('<script type="application/ld+json">')
        if start == -1:
            self.fail("No JSON-LD script tag found")

        start = content.find(">", start) + 1
        end = content.find("</script>", start)
        json_ld = content[start:end].strip()

        try:
            data = json.loads(json_ld)
        except json.JSONDecodeError:
            self.fail("JSON-LD is not valid JSON")

        # Verify basic structure
        self.assertEqual(data["@context"], "https://schema.org")
        self.assertEqual(data["@type"], "NewsArticle")

    def test_json_ld_has_headline(self) -> None:
        """Test that JSON-LD has headline field."""
        response = self.client.get(self.url)
        content = response.content.decode("utf-8")

        self.assertIn('"headline":', content)

    def test_json_ld_has_description(self) -> None:
        """Test that JSON-LD has description field."""
        response = self.client.get(self.url)
        content = response.content.decode("utf-8")

        self.assertIn('"description":', content)

    def test_json_ld_has_image(self) -> None:
        """Test that JSON-LD has image field."""
        response = self.client.get(self.url)
        content = response.content.decode("utf-8")

        self.assertIn('"image":', content)

    def test_json_ld_has_date_published(self) -> None:
        """Test that JSON-LD has datePublished field."""
        response = self.client.get(self.url)
        content = response.content.decode("utf-8")

        self.assertIn('"datePublished":', content)

    def test_json_ld_has_date_modified(self) -> None:
        """Test that JSON-LD has dateModified field."""
        response = self.client.get(self.url)
        content = response.content.decode("utf-8")

        self.assertIn('"dateModified":', content)

    def test_json_ld_has_url(self) -> None:
        """Test that JSON-LD has url field."""
        response = self.client.get(self.url)
        content = response.content.decode("utf-8")

        self.assertIn('"url":', content)

    def test_json_ld_has_publisher(self) -> None:
        """Test that JSON-LD has publisher field."""
        response = self.client.get(self.url)
        content = response.content.decode("utf-8")

        self.assertIn('"publisher":', content)

    def test_json_ld_has_author(self) -> None:
        """Test that JSON-LD has author field."""
        response = self.client.get(self.url)
        content = response.content.decode("utf-8")

        self.assertIn('"author":', content)

    def test_json_ld_has_keywords_from_tags(self) -> None:
        """Test that JSON-LD has keywords from llm_tags."""
        response = self.client.get(self.url)
        content = response.content.decode("utf-8")

        self.assertIn('"keywords":', content)
        # Should contain tags from the article
        self.assertIn("SEO", content)
        self.assertIn("Structured Data", content)
        self.assertIn("Testing", content)

    def test_json_ld_urls_are_absolute(self) -> None:
        """Test that all URLs in JSON-LD are absolute."""
        response = self.client.get(self.url)
        content = response.content.decode("utf-8")

        # Extract JSON-LD
        start = content.find('<script type="application/ld+json">')
        start = content.find(">", start) + 1
        end = content.find("</script>", start)
        json_ld = content[start:end].strip()

        data = json.loads(json_ld)

        # Check that url is absolute
        if "url" in data:
            self.assertTrue(
                data["url"].startswith("http://") or data["url"].startswith("https://")
            )


class CanonicalUrlTests(TestCase):
    """Test cases for canonical URLs."""

    def setUp(self) -> None:
        """Set up test data."""
        self.client = Client()
        self.article = News.objects.create(
            title="Test Article",
            status="published",
            deleted_at=None,
            llm_bullets=["Key point 1", "Key point 2", "Key point 3"],
            llm_tags=["Test", "SEO"],
        )
        self.url = reverse(
            "news:detail",
            kwargs={"news_id": self.article.id, "slug": self.article.slug},
        )

    def test_article_has_canonical_link(self) -> None:
        """Test that article has <link rel="canonical">."""
        response = self.client.get(self.url)
        content = response.content.decode("utf-8")

        self.assertIn('<link rel="canonical"', content)

    def test_canonical_url_is_absolute(self) -> None:
        """Test that canonical URL is absolute."""
        response = self.client.get(self.url)
        content = response.content.decode("utf-8")

        # Should contain http:// or https://
        start = content.find('<link rel="canonical"')
        end = content.find(">", start)
        canonical_tag = content[start:end]

        self.assertIn("http://", canonical_tag)

    def test_canonical_url_matches_get_absolute_url(self) -> None:
        """Test that canonical URL matches get_absolute_url()."""
        response = self.client.get(self.url)
        content = response.content.decode("utf-8")

        # Extract canonical URL
        start = content.find('<link rel="canonical"')
        end = content.find(">", start)
        canonical_tag = content[start:end]

        # Should contain the article's absolute URL path
        expected_path = self.article.get_absolute_url()
        self.assertIn(expected_path, canonical_tag)

    def test_query_parameters_dont_affect_canonical(self) -> None:
        """Test that query parameters don't affect canonical URL."""
        response1 = self.client.get(self.url)
        response2 = self.client.get(self.url + "?from_page=2")

        content1 = response1.content.decode("utf-8")
        content2 = response2.content.decode("utf-8")

        # Extract canonical URLs
        def extract_canonical(content: str) -> str:
            start = content.find('<link rel="canonical"')
            end = content.find(">", start)
            return content[start:end]

        canonical1 = extract_canonical(content1)
        canonical2 = extract_canonical(content2)

        # Should be identical
        self.assertEqual(canonical1, canonical2)


class SEOPagesTests(TestCase):
    """Test cases for SEO on other pages (homepage, search, tags)."""

    def setUp(self) -> None:
        """Set up test client."""
        self.client = Client()

    def test_homepage_has_meta_description(self) -> None:
        """Test that homepage has meta description."""
        response = self.client.get(reverse("news:list"))
        content = response.content.decode("utf-8")

        self.assertIn('<meta name="description"', content)

    def test_search_page_has_meta_description(self) -> None:
        """Test that search page has meta description."""
        response = self.client.get(reverse("news:search"))
        content = response.content.decode("utf-8")

        self.assertIn('<meta name="description"', content)

    def test_tags_index_has_meta_description(self) -> None:
        """Test that tags index has meta description."""
        response = self.client.get(reverse("news:tags_index"))
        content = response.content.decode("utf-8")

        self.assertIn('<meta name="description"', content)

    def test_tag_detail_has_meta_description(self) -> None:
        """Test that tag detail has meta description."""
        Tag.objects.create(name="Python", slug="python")

        with patch("news.models.Tag.objects.get_articles_for_tag"):
            response = self.client.get(
                reverse("news:tag_detail", kwargs={"tag_slug": "python"})
            )
            content = response.content.decode("utf-8")

            self.assertIn('<meta name="description"', content)
