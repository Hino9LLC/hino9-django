"""
Test cases for URL routing and patterns.

Tests validate URL resolution, URL generation (reverse), slug handling,
and redirect behavior.
"""

from django.test import TestCase
from django.urls import resolve, reverse

from news.models import News


class NewsUrlResolutionTests(TestCase):
    """Test cases for news URL resolution."""

    def test_news_list_resolves(self) -> None:
        """Test that news:list resolves to /."""
        url = reverse("news:list")
        self.assertEqual(url, "/")

    def test_news_detail_resolves(self) -> None:
        """Test that news:detail resolves to /{id}/{slug}."""
        url = reverse("news:detail", kwargs={"news_id": 1, "slug": "test-slug"})
        self.assertEqual(url, "/1/test-slug")

    def test_news_detail_redirect_resolves(self) -> None:
        """Test that news:detail_redirect resolves to /{id}/."""
        url = reverse("news:detail_redirect", kwargs={"news_id": 1})
        self.assertEqual(url, "/1")

    def test_news_search_resolves(self) -> None:
        """Test that news:search resolves to /search/."""
        url = reverse("news:search")
        self.assertEqual(url, "/search")


class TagUrlResolutionTests(TestCase):
    """Test cases for tag URL resolution."""

    def test_tags_index_resolves(self) -> None:
        """Test that news:tags_index resolves to /tags/."""
        url = reverse("news:tags_index")
        self.assertEqual(url, "/tags")

    def test_tag_detail_resolves(self) -> None:
        """Test that news:tag_detail resolves to /tag/{slug}/."""
        url = reverse("news:tag_detail", kwargs={"tag_slug": "python"})
        self.assertEqual(url, "/tag/python")


class SeoUrlResolutionTests(TestCase):
    """Test cases for SEO URL resolution."""

    def test_sitemap_resolves(self) -> None:
        """Test that sitemap resolves to /sitemap.xml."""
        url = "/sitemap.xml"
        # Verify the URL is accessible
        from django.test import Client

        client = Client()
        response = client.get(url)
        self.assertEqual(response.status_code, 200)

    def test_robots_txt_resolves(self) -> None:
        """Test that robots.txt resolves to /robots.txt."""
        url = "/robots.txt"
        # Verify the URL is accessible
        from django.test import Client

        client = Client()
        response = client.get(url)
        self.assertEqual(response.status_code, 200)


class UrlGenerationTests(TestCase):
    """Test cases for URL generation with reverse()."""

    def test_reverse_news_list(self) -> None:
        """Test reverse() for news list."""
        url = reverse("news:list")
        self.assertEqual(url, "/")

    def test_reverse_news_detail(self) -> None:
        """Test reverse() for news detail with ID and slug."""
        url = reverse("news:detail", args=[123, "test-slug"])
        self.assertEqual(url, "/123/test-slug")

    def test_reverse_tag_detail(self) -> None:
        """Test reverse() for tag detail."""
        url = reverse("news:tag_detail", args=["machine-learning"])
        self.assertEqual(url, "/tag/machine-learning")


class SlugHandlingTests(TestCase):
    """Test cases for slug handling in URLs."""

    def test_slugs_are_lowercase(self) -> None:
        """Test that slugs are lowercase."""
        article = News.objects.create(
            title="TEST ARTICLE",
            status="published",
            deleted_at=None,
        )
        self.assertTrue(article.slug.islower())

    def test_slugs_use_hyphens(self) -> None:
        """Test that slugs use hyphens for spaces."""
        article = News.objects.create(
            title="Test Article Title",
            status="published",
            deleted_at=None,
        )
        self.assertIn("-", article.slug)
        self.assertNotIn(" ", article.slug)

    def test_slugs_are_url_safe(self) -> None:
        """Test that slugs don't contain unsafe characters."""
        article = News.objects.create(
            title="Test @ Article: with (special) [chars]!",
            status="published",
            deleted_at=None,
        )

        # URL-unsafe characters should be removed or converted
        unsafe_chars = ["@", ":", "(", ")", "[", "]", "!"]
        for char in unsafe_chars:
            self.assertNotIn(char, article.slug)

    def test_slugs_handle_unicode(self) -> None:
        """Test that slugs handle unicode characters appropriately."""
        article = News.objects.create(
            title="Test Article café",
            status="published",
            deleted_at=None,
        )

        # Should generate a valid slug
        self.assertIsNotNone(article.slug)
        self.assertTrue(len(article.slug) > 0)

    def test_very_long_slug(self) -> None:
        """Test that very long titles generate valid slugs."""
        long_title = "This is an extremely long article title " * 10
        article = News.objects.create(
            title=long_title,
            status="published",
            deleted_at=None,
        )

        # Should generate a slug (may be truncated)
        self.assertIsNotNone(article.slug)
        self.assertTrue(len(article.slug) > 0)

    def test_slug_with_consecutive_hyphens(self) -> None:
        """Test slug generation with multiple consecutive spaces."""
        article = News.objects.create(
            title="Test    Article    Title",
            status="published",
            deleted_at=None,
        )

        # Should not have consecutive hyphens
        self.assertNotIn("--", article.slug)

    def test_slug_doesnt_start_or_end_with_hyphen(self) -> None:
        """Test that slugs don't start or end with hyphens."""
        article = News.objects.create(
            title="  Test Article  ",
            status="published",
            deleted_at=None,
        )

        self.assertFalse(article.slug.startswith("-"))
        self.assertFalse(article.slug.endswith("-"))


class RedirectTests(TestCase):
    """Test cases for URL redirects."""

    def setUp(self) -> None:
        """Set up test data."""
        from django.test import Client

        self.client = Client()
        self.article = News.objects.create(
            title="Test Article",
            status="published",
            deleted_at=None,
        )

    def test_legacy_url_without_slug_redirects(self) -> None:
        """Test that legacy URL without slug redirects to URL with slug."""
        url = reverse("news:detail_redirect", kwargs={"news_id": self.article.id})
        response = self.client.get(url)

        # Should be a permanent redirect
        self.assertEqual(response.status_code, 301)

    def test_redirect_is_permanent(self) -> None:
        """Test that redirects are permanent (HTTP 301)."""
        url = reverse("news:detail_redirect", kwargs={"news_id": self.article.id})
        response = self.client.get(url)

        self.assertEqual(response.status_code, 301)

    def test_redirect_uses_correct_slug(self) -> None:
        """Test that redirect uses the correct slug from article."""
        url = reverse("news:detail_redirect", kwargs={"news_id": self.article.id})
        response = self.client.get(url)

        # Should redirect to URL with correct slug
        expected_url = reverse(
            "news:detail",
            kwargs={"news_id": self.article.id, "slug": self.article.slug},
        )
        self.assertTrue(hasattr(response, "url"))  # Type guard
        self.assertIn(expected_url, response.url)  # type: ignore[attr-defined]

    def test_wrong_slug_redirects_to_correct_slug(self) -> None:
        """Test that wrong slug redirects to correct slug."""
        url = reverse(
            "news:detail", kwargs={"news_id": self.article.id, "slug": "wrong-slug"}
        )
        response = self.client.get(url)

        # Should be a permanent redirect
        self.assertEqual(response.status_code, 301)

        # Should redirect to correct slug
        expected_url = reverse(
            "news:detail",
            kwargs={"news_id": self.article.id, "slug": self.article.slug},
        )
        self.assertTrue(hasattr(response, "url"))  # Type guard
        self.assertIn(expected_url, response.url)  # type: ignore[attr-defined]


class UrlPatternTests(TestCase):
    """Test cases for URL pattern matching."""

    def test_news_detail_url_pattern(self) -> None:
        """Test that news detail URL pattern matches correctly."""
        url = "/123/test-slug"
        match = resolve(url)

        self.assertEqual(match.url_name, "detail")
        self.assertEqual(match.kwargs["news_id"], 123)
        self.assertEqual(match.kwargs["slug"], "test-slug")

    def test_tag_detail_url_pattern(self) -> None:
        """Test that tag detail URL pattern matches correctly."""
        url = "/tag/python"
        match = resolve(url)

        # Note: URL without trailing slash hits the redirect, so check for that
        self.assertIn(match.url_name, ["tag_detail", "tag_detail_slash_redirect"])
        self.assertEqual(match.kwargs["tag_slug"], "python")

    def test_news_list_url_pattern(self) -> None:
        """Test that news list URL pattern matches correctly."""
        url = "/"
        match = resolve(url)

        self.assertEqual(match.url_name, "list")

    def test_search_url_pattern(self) -> None:
        """Test that search URL pattern matches correctly."""
        url = "/search"
        match = resolve(url)

        # Note: URL without trailing slash might hit redirect
        self.assertIn(match.url_name, ["search", "search_slash_redirect"])
