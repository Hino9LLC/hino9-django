"""
Base test utilities and fixtures for the news app test suite.

Provides utilities for handling SQLite limitations when testing
PostgreSQL-specific features like ArrayField and VectorField.
"""

from typing import Any

from django.conf import settings
from django.test import TestCase


def is_sqlite() -> bool:
    """Check if tests are running on SQLite."""
    engine_value = settings.DATABASES["default"].get("ENGINE") or ""
    engine = str(engine_value)
    return "sqlite" in engine


def skip_if_sqlite(reason: str = "Test requires PostgreSQL") -> Any:
    """Decorator to skip tests that require PostgreSQL features."""
    import unittest

    return unittest.skipIf(is_sqlite(), reason)


class NewsTestCase(TestCase):
    """
    Base test case for news app tests.

    Provides utilities for handling SQLite compatibility issues.
    """

    is_sqlite: bool

    @classmethod
    def setUpClass(cls) -> None:
        """Set up class-level test data."""
        super().setUpClass()
        cls.is_sqlite = is_sqlite()

    def create_news_article(self, **kwargs: Any) -> Any:
        """
        Create a news article with SQLite-safe defaults.

        Handles ArrayField and VectorField which don't work in SQLite.
        """
        from news.models import News

        defaults: dict[str, Any] = {
            "title": "Test Article",
            "status": "published",
            "deleted_at": None,
        }

        # Handle ArrayField - SQLite doesn't support it
        if self.is_sqlite:
            # Remove array fields or convert to compatible format
            if "llm_tags" not in kwargs:
                defaults["llm_tags"] = None  # SQLite will handle this
            if "llm_bullets" not in kwargs:
                defaults["llm_bullets"] = None
            if "content_embedding" not in kwargs:
                defaults["content_embedding"] = None
        else:
            # PostgreSQL - use actual arrays
            if "llm_tags" not in kwargs:
                defaults["llm_tags"] = []  # type: ignore[assignment]
            if "llm_bullets" not in kwargs:
                defaults["llm_bullets"] = []  # type: ignore[assignment]

        # Merge with provided kwargs
        defaults.update(kwargs)

        return News.objects.create(**defaults)

    def create_tag(self, **kwargs: Any) -> Any:
        """Create a tag with sensible defaults."""
        from news.models import Tag

        defaults = {
            "name": "Test Tag",
        }

        defaults.update(kwargs)

        return Tag.objects.create(**defaults)
