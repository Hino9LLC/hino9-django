from typing import Any, Optional

from django.contrib.sitemaps import Sitemap
from django.db.models import QuerySet
from django.utils.text import slugify

from .models import News, Tag


class NewsSitemap(Sitemap):
    """
    Sitemap for published news articles.
    """

    changefreq = "weekly"
    priority = 0.8

    def items(self) -> QuerySet[News]:
        """Return all published news articles."""
        return News.objects.filter(
            status="published", deleted_at__isnull=True
        ).order_by("-article_date")

    def lastmod(self, obj: News) -> Optional[Any]:
        """Return the last modification date for the article."""
        # Use article_date if available, otherwise fall back to updated_at or created_at
        if obj.article_date:
            return obj.article_date
        elif obj.updated_at:
            return obj.updated_at
        else:
            return obj.created_at

    def location(self, obj: News) -> str:
        """Return the URL for the news article."""
        # Use the display_title property to get the best available title for slug generation
        title = obj.display_title
        slug = slugify(title)
        return f"/{obj.id}/{slug}"


class TagSitemap(Sitemap):
    """
    Sitemap for tag pages.
    """

    changefreq = "monthly"
    priority = 0.6

    def items(self) -> QuerySet[Tag]:
        """Return all tags."""
        return Tag.objects.all().order_by("name")

    def lastmod(self, obj: Tag) -> Optional[Any]:
        """Return the last modification date for the tag."""
        # Use the most recent article with this tag for lastmod
        latest_article = (
            News.objects.filter(
                llm_tags__contains=[obj.name],
                status="published",
                deleted_at__isnull=True,
            )
            .order_by("-article_date")
            .first()
        )

        if latest_article and latest_article.article_date:
            return latest_article.article_date
        return None

    def location(self, obj: Tag) -> str:
        """Return the URL for the tag page."""
        return f"/tag/{obj.slug}"
