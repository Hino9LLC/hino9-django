"""
Test cases for News and Tag models.

Tests validate data integrity, business logic, model methods, and edge cases.
"""

from typing import Any
from unittest.mock import MagicMock, patch

from django.test import TestCase
from django.utils import timezone

from news.models import News, Tag


class NewsModelTests(TestCase):
    """Test cases for the News model."""

    def setUp(self) -> None:
        """Set up test data for News model tests."""
        self.article_date = timezone.now()

    # Data Integrity Tests

    def test_published_article_requires_published_status(self) -> None:
        """Test that articles need status='published' to be published."""
        published = News.objects.create(
            title="Published Article",
            status="published",
            deleted_at=None,
            article_date=self.article_date,
            llm_bullets=["Key point 1", "Key point 2", "Key point 3"],
            llm_tags=["Test", "News"],
        )
        unpublished = News.objects.create(
            title="Unpublished Article",
            status="draft",
            deleted_at=None,
            article_date=self.article_date,
            llm_bullets=["Key point 1", "Key point 2", "Key point 3"],
            llm_tags=["Test", "News"],
        )

        # Only published articles should appear in published queries
        published_qs = News.objects.filter(status="published", deleted_at=None)
        self.assertIn(published, published_qs)
        self.assertNotIn(unpublished, published_qs)

    def test_deleted_articles_excluded_from_queries(self) -> None:
        """Test that deleted articles (deleted_at != None) are excluded."""
        active = News.objects.create(
            title="Active Article",
            status="published",
            deleted_at=None,
            article_date=self.article_date,
            llm_bullets=["Key point 1", "Key point 2", "Key point 3"],
            llm_tags=["Test", "News"],
        )
        deleted = News.objects.create(
            title="Deleted Article",
            status="published",
            deleted_at=timezone.now(),
            article_date=self.article_date,
            llm_bullets=["Key point 1", "Key point 2", "Key point 3"],
            llm_tags=["Test", "News"],
        )

        # Only active articles should appear
        published_qs = News.objects.filter(status="published", deleted_at=None)
        self.assertIn(active, published_qs)
        self.assertNotIn(deleted, published_qs)

    def test_article_date_handling(self) -> None:
        """Test article date fields (article_date, updated_at, created_at)."""
        article = News.objects.create(
            title="Test Article",
            status="published",
            deleted_at=None,
            article_date=self.article_date,
            llm_bullets=["Key point 1", "Key point 2", "Key point 3"],
            llm_tags=["Test", "News"],
        )

        self.assertEqual(article.article_date, self.article_date)
        self.assertIsNotNone(article.created_at)
        # updated_at is nullable and not auto-set, so it can be None
        # Only check that the field exists
        self.assertTrue(hasattr(article, "updated_at"))

    # Property Tests

    def test_display_title_uses_llm_headline(self) -> None:
        """Test that display_title prefers llm_headline over title."""
        article = News.objects.create(
            title="Original Title",
            llm_headline="AI-Generated Headline",
            status="published",
            deleted_at=None,
            llm_bullets=["Key point 1", "Key point 2", "Key point 3"],
            llm_tags=["Test", "News"],
        )
        self.assertEqual(article.display_title, "AI-Generated Headline")

    def test_display_title_fallback_to_title(self) -> None:
        """Test that display_title falls back to title when llm_headline is empty."""
        article = News.objects.create(
            title="Original Title",
            llm_headline=None,
            status="published",
            deleted_at=None,
            llm_bullets=["Key point 1", "Key point 2", "Key point 3"],
            llm_tags=["Test", "News"],
        )
        self.assertEqual(article.display_title, "Original Title")

    def test_display_title_fallback_to_article_id(self) -> None:
        """Test that display_title falls back to 'Article {id}' when both are empty."""
        article = News.objects.create(
            title=None,
            llm_headline=None,
            status="published",
            deleted_at=None,
            llm_bullets=["Key point 1", "Key point 2", "Key point 3"],
            llm_tags=["Test", "News"],
        )
        self.assertEqual(article.display_title, f"Article {article.id}")

    def test_display_summary_uses_llm_summary(self) -> None:
        """Test that display_summary prefers llm_summary over summary."""
        article = News.objects.create(
            title="Test",
            summary="Original summary",
            llm_summary="AI-generated summary",
            status="published",
            deleted_at=None,
            llm_bullets=["Key point 1", "Key point 2", "Key point 3"],
            llm_tags=["Test", "News"],
        )
        self.assertEqual(article.display_summary, "AI-generated summary")

    def test_display_summary_fallback_to_summary(self) -> None:
        """Test that display_summary falls back to summary when llm_summary is empty."""
        article = News.objects.create(
            title="Test",
            summary="Original summary",
            llm_summary=None,
            status="published",
            deleted_at=None,
            llm_bullets=["Key point 1", "Key point 2", "Key point 3"],
            llm_tags=["Test", "News"],
        )
        self.assertEqual(article.display_summary, "Original summary")

    def test_display_summary_fallback_to_empty_string(self) -> None:
        """Test that display_summary returns empty string when both are empty."""
        article = News.objects.create(
            title="Test",
            summary=None,
            llm_summary=None,
            status="published",
            deleted_at=None,
            llm_bullets=["Key point 1", "Key point 2", "Key point 3"],
            llm_tags=["Test", "News"],
        )
        self.assertEqual(article.display_summary, "")

    def test_slug_property_generates_url_safe_slug(self) -> None:
        """Test that slug property generates URL-safe slugs from display_title."""
        test_cases = [
            ("Machine Learning in 2025", "machine-learning-in-2025"),
            ("React.js Framework", "reactjs-framework"),
            ("C++ Programming", "c-programming"),
            ("AI/ML Technologies", "aiml-technologies"),
            ("   Spaces   Everywhere   ", "spaces-everywhere"),
        ]

        for title, expected_slug in test_cases:
            article = News.objects.create(
                title=title,
                status="published",
                deleted_at=None,
                llm_bullets=["Key point 1", "Key point 2", "Key point 3"],
                llm_tags=["Test", "News"],
            )
            self.assertEqual(article.slug, expected_slug)
            article.delete()

    def test_slug_handles_special_characters(self) -> None:
        """Test that slug handles special characters properly."""
        article = News.objects.create(
            title="Test @ Article: with (special) [chars]!",
            status="published",
            deleted_at=None,
            llm_bullets=["Key point 1", "Key point 2", "Key point 3"],
            llm_tags=["Test", "News"],
        )
        # Should remove or convert special characters
        self.assertNotIn("@", article.slug)
        self.assertNotIn(":", article.slug)
        self.assertNotIn("(", article.slug)
        self.assertNotIn(")", article.slug)
        self.assertNotIn("[", article.slug)
        self.assertNotIn("]", article.slug)
        self.assertNotIn("!", article.slug)

    def test_slug_handles_long_titles(self) -> None:
        """Test that slug handles very long titles appropriately."""
        long_title = (
            "This is an extremely long article title that goes on and on and on " * 5
        )
        article = News.objects.create(
            title=long_title,
            status="published",
            deleted_at=None,
            llm_bullets=["Key point 1", "Key point 2", "Key point 3"],
            llm_tags=["Test", "News"],
        )
        # Slug should be generated (may be truncated)
        self.assertIsNotNone(article.slug)
        self.assertTrue(len(article.slug) > 0)

    # Method Tests

    def test_get_absolute_url_returns_correct_format(self) -> None:
        """Test that get_absolute_url returns correct URL format."""
        article = News.objects.create(
            title="Test Article",
            status="published",
            deleted_at=None,
            llm_bullets=["Key point 1", "Key point 2", "Key point 3"],
            llm_tags=["Test", "News"],
        )
        url = article.get_absolute_url()
        self.assertTrue(url.startswith("/"))
        self.assertIn(str(article.id), url)
        self.assertIn(article.slug, url)
        self.assertEqual(url, f"/{article.id}/{article.slug}")

    def test_get_absolute_url_uses_display_title_for_slug(self) -> None:
        """Test that get_absolute_url uses display_title for slug generation."""
        article = News.objects.create(
            title="Original Title",
            llm_headline="AI Headline",
            status="published",
            deleted_at=None,
            llm_bullets=["Key point 1", "Key point 2", "Key point 3"],
            llm_tags=["Test", "News"],
        )
        url = article.get_absolute_url()
        # Should use llm_headline (display_title) for slug
        self.assertIn("ai-headline", url)
        self.assertNotIn("original-title", url)

    # Edge Cases

    def test_article_with_no_title_or_headline_does_not_crash(self) -> None:
        """Test that articles with no title or headline don't cause crashes."""
        article = News.objects.create(
            title=None,
            llm_headline=None,
            status="published",
            deleted_at=None,
            llm_bullets=["Key point 1", "Key point 2", "Key point 3"],
            llm_tags=["Test", "News"],
        )
        # Should not raise exceptions
        _ = article.display_title
        _ = article.slug
        _ = article.get_absolute_url()
        self.assertTrue(True)  # If we got here, no crashes occurred

    def test_article_with_empty_llm_tags_array(self) -> None:
        """Test article with empty llm_tags array."""
        article = News.objects.create(
            title="Test Empty Tags",
            llm_tags=[],
            llm_bullets=[],
            status="published",
            deleted_at=None,
        )
        self.assertEqual(article.llm_tags, [])
        self.assertIsInstance(article.llm_tags, list)

    def test_article_with_null_image_url(self) -> None:
        """Test article with null/empty image_url."""
        article = News.objects.create(
            title="Test",
            image_url=None,
            status="published",
            deleted_at=None,
            llm_bullets=["Key point 1", "Key point 2", "Key point 3"],
            llm_tags=["Test", "News"],
        )
        self.assertIsNone(article.image_url)

    def test_article_with_very_long_title(self) -> None:
        """Test article with very long title (>200 chars)."""
        long_title = "A" * 300
        article = News.objects.create(
            title=long_title,
            status="published",
            deleted_at=None,
            llm_bullets=["Key point 1", "Key point 2", "Key point 3"],
            llm_tags=["Test", "News"],
        )
        self.assertIsNotNone(article.title)
        if article.title:
            self.assertEqual(len(article.title), 300)
        # Should still generate slug and URL
        self.assertIsNotNone(article.slug)
        self.assertIsNotNone(article.get_absolute_url())


class TagModelTests(TestCase):
    """Test cases for the Tag model."""

    # Slug Generation Tests

    def test_auto_generates_slug_on_save(self) -> None:
        """Test that slug is auto-generated on save if not provided."""
        tag = Tag.objects.create(name="Machine Learning")
        self.assertEqual(tag.slug, "machine-learning")

    def test_slug_is_lowercase_and_hyphenated(self) -> None:
        """Test that generated slug is lowercase with hyphens."""
        tag = Tag.objects.create(name="Natural Language Processing")
        self.assertEqual(tag.slug, "natural-language-processing")
        self.assertTrue(tag.slug.islower())

    def test_slug_handles_special_characters(self) -> None:
        """Test slug generation with special characters."""
        test_cases = [
            ("React.js", "reactjs"),
            ("C++", "c"),
            ("AI/ML", "aiml"),
            ("Node.js & Express", "nodejs-express"),
        ]
        for name, expected_slug in test_cases:
            tag = Tag.objects.create(name=name)
            self.assertEqual(tag.slug, expected_slug)
            tag.delete()

    def test_slug_handles_spaces(self) -> None:
        """Test slug generation replaces spaces with hyphens."""
        tag = Tag.objects.create(name="Machine Learning")
        self.assertEqual(tag.slug, "machine-learning")

    def test_slug_handles_multiple_words(self) -> None:
        """Test slug generation with multiple words."""
        tag = Tag.objects.create(name="Natural Language Processing")
        self.assertEqual(tag.slug, "natural-language-processing")

    def test_preserves_manual_slug_if_provided(self) -> None:
        """Test that manually provided slug is preserved."""
        tag = Tag.objects.create(name="Machine Learning", slug="ml-custom")
        self.assertEqual(tag.slug, "ml-custom")

    # Uniqueness Constraint Tests

    def test_tag_name_must_be_unique(self) -> None:
        """Test that tag name must be unique."""
        Tag.objects.create(name="Python", slug="python")
        # Attempting to create duplicate should raise IntegrityError
        from django.db import IntegrityError

        with self.assertRaises(IntegrityError):
            Tag.objects.create(name="Python", slug="python2")

    def test_tag_slug_must_be_unique(self) -> None:
        """Test that tag slug must be unique."""
        Tag.objects.create(name="Python", slug="python")
        # Attempting to create duplicate slug should raise IntegrityError
        from django.db import IntegrityError

        with self.assertRaises(IntegrityError):
            Tag.objects.create(name="Python Programming", slug="python")

    # Business Logic Tests

    @patch("news.models.News.objects.filter")
    def test_get_news_count_only_counts_published(self, mock_filter: MagicMock) -> None:
        """Test that get_news_count only counts published articles."""
        tag = Tag.objects.create(name="AI", slug="ai")

        # Mock the News QuerySet to return a count
        mock_queryset = type("MockQuerySet", (), {"count": lambda self: 5})()
        mock_filter.return_value = mock_queryset

        _ = tag.get_news_count()

        # Verify filter was called with correct parameters
        mock_filter.assert_called_once()
        call_kwargs = mock_filter.call_args.kwargs
        self.assertEqual(call_kwargs["status"], "published")
        self.assertTrue(call_kwargs["deleted_at__isnull"])

    def test_get_news_count_with_zero_articles(self) -> None:
        """Test get_news_count when tag has no articles."""
        tag = Tag.objects.create(name="Empty Tag", slug="empty-tag")
        # Since we're using SQLite for tests and no actual articles exist
        # This will return 0
        count = tag.get_news_count()
        self.assertEqual(count, 0)


class TagManagerTests(TestCase):
    """Test cases for the Tag manager."""

    def setUp(self) -> None:
        """Set up test data."""
        self.tag1 = Tag.objects.create(name="Python", slug="python")
        self.tag2 = Tag.objects.create(name="JavaScript", slug="javascript")

    @patch("news.models.News.objects.filter")
    def test_get_articles_for_tag_returns_published_only(
        self, mock_filter: MagicMock
    ) -> None:
        """Test that get_articles_for_tag returns only published articles."""
        # Mock the QuerySet
        from django.db.models import QuerySet

        mock_queryset: Any = QuerySet(model=News)
        mock_filter.return_value = mock_queryset

        Tag.objects.get_articles_for_tag(self.tag1)

        # Verify filter was called with correct parameters
        mock_filter.assert_called_once()
        call_kwargs = mock_filter.call_args.kwargs
        self.assertEqual(call_kwargs["status"], "published")
        self.assertTrue(call_kwargs["deleted_at__isnull"])

    def test_get_articles_for_tag_returns_queryset(self) -> None:
        """Test that get_articles_for_tag returns a QuerySet."""
        result = Tag.objects.get_articles_for_tag(self.tag1)
        from django.db.models import QuerySet

        self.assertIsInstance(result, QuerySet)

    @patch("news.models.Tag.get_news_count")
    def test_get_tag_counts_returns_dict(self, mock_get_news_count: MagicMock) -> None:
        """Test that get_tag_counts returns dict with tag→count mapping."""
        mock_get_news_count.return_value = 5

        counts = Tag.objects.get_tag_counts()

        self.assertIsInstance(counts, dict)
        self.assertEqual(counts[self.tag1], 5)
        self.assertEqual(counts[self.tag2], 5)
