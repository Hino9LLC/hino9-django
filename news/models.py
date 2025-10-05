from typing import TYPE_CHECKING, Any, Dict, cast

from django.contrib.postgres.fields import ArrayField
from django.db import models
from django.utils.text import slugify
from pgvector.django import VectorField

if TYPE_CHECKING:
    from django.db.models import QuerySet


class News(models.Model):
    """
    News model that matches the existing news table in the database.
    This model uses db_table to map to the existing 'news' table.
    """

    # Primary key
    id = models.AutoField(primary_key=True)

    # Article metadata
    article_date = models.DateTimeField(null=True, blank=True)
    title = models.CharField(max_length=512, null=True, blank=True)
    summary = models.TextField(null=True, blank=True)

    # LLM-generated content
    llm_headline = models.TextField(null=True, blank=True)
    llm_summary = models.TextField(null=True, blank=True)
    llm_bullets = ArrayField(
        models.TextField(),
        null=True,
        blank=True,
        help_text="LLM-generated bullet points",
    )
    llm_tags = ArrayField(
        models.TextField(), null=True, blank=True, help_text="LLM-generated tags"
    )

    # Source information
    domain = models.CharField(max_length=255, null=True, blank=True)
    site_name = models.CharField(max_length=255, null=True, blank=True)
    image_url = models.CharField(max_length=2048, null=True, blank=True)
    url = models.CharField(max_length=2048, null=True, blank=True)

    # Foreign key references
    article = models.OneToOneField(
        "Article",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="news",
        db_column="article_id",  # Maintains existing column name in database
    )

    # Status and error handling
    status = models.CharField(
        max_length=20,
        default="pending",
        choices=[
            ("pending", "Pending"),
            ("processed", "Processed"),
            ("failed", "Failed"),
            ("published", "Published"),
            ("ignored", "Ignored"),
        ],
    )
    error_message = models.TextField(null=True, blank=True)

    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(null=True, blank=True)
    processed_at = models.DateTimeField(null=True, blank=True)
    deleted_at = models.DateTimeField(null=True, blank=True)

    # Content and embeddings
    content_text = models.TextField(null=True, blank=True)
    content_embedding = VectorField(dimensions=768, null=True, blank=True)

    class Meta:
        db_table = "news"  # Use existing table
        managed = True  # Let Django manage this table for admin access
        ordering = ["-created_at", "-article_date"]
        verbose_name = "News Article"
        verbose_name_plural = "News Articles"

    def __str__(self) -> str:
        return self.title or f"News Article {self.id}"

    @property
    def display_title(self) -> str:
        """Return LLM headline if available, otherwise original title"""
        return self.llm_headline or self.title or f"Article {self.id}"

    @property
    def display_summary(self) -> str:
        """Return LLM summary if available, otherwise original summary"""
        return self.llm_summary or self.summary or ""

    @property
    def slug(self) -> str:
        """Generate a URL-friendly slug from the headline on-demand"""
        # Use LLM headline if available, otherwise original title
        source_text = self.llm_headline or self.title or f"article-{self.id}"
        return slugify(source_text)

    def get_absolute_url(self) -> str:
        """Return the absolute URL for the news article"""
        from django.urls import reverse

        # Use display_title for generating the slug in the URL
        title = self.display_title
        slug = slugify(title)
        return reverse("news:detail", kwargs={"news_id": self.id, "slug": slug})


class Article(models.Model):
    """
    Full article content storage.

    This table stores the complete original article text and metadata.
    The News table references this via article_id for deep content search.
    Matches production schema from ddl.sql.
    """

    # Article metadata
    article_date = models.DateTimeField(null=True, blank=True)
    title = models.CharField(max_length=512, null=True, blank=True)
    summary = models.TextField(null=True, blank=True)
    domain = models.CharField(max_length=255, null=True, blank=True)
    site_name = models.CharField(max_length=255, null=True, blank=True)
    image_url = models.CharField(max_length=2048, null=True, blank=True)
    url = models.CharField(max_length=2048, null=True, blank=True)

    # References to external tables (not managed by Django)
    url_id = models.IntegerField(null=True, blank=True)
    email_id = models.CharField(max_length=255, null=True, blank=True)

    # Status fields
    status = models.CharField(max_length=20, default="pending")
    error_message = models.TextField(null=True, blank=True)

    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(null=True, blank=True)
    processed_at = models.DateTimeField(null=True, blank=True)
    deleted_at = models.DateTimeField(null=True, blank=True)

    # Content fields (PostgreSQL-specific)
    tags = ArrayField(models.TextField(), null=True, blank=True)
    metadata = models.JSONField(null=True, blank=True)
    content_text = models.TextField(null=True, blank=True)

    # PostgreSQL pgvector field (768 dimensions for nomic-embed-text-v1.5)
    content_embedding = VectorField(dimensions=768, null=True, blank=True)

    # Note: ts_vector_content is a GENERATED column - handled in migration, not model

    class Meta:
        db_table = "articles"
        managed = True  # Django should manage this table
        ordering = ["-created_at"]
        constraints = [
            models.UniqueConstraint(
                fields=["url_id", "article_date"],
                name="articles_url_id_article_date_unique",
            )
        ]

    def __str__(self) -> str:
        return self.title or f"Article {self.id}"


class TagManager(models.Manager):
    """
    Custom manager for Tag model.
    """

    def get_articles_for_tag(self, tag: "Tag") -> "QuerySet[News]":
        """
        Get all news articles that have the given tag in their llm_tags array.
        Only returns published articles.
        """
        # Query news articles that have this tag and are published
        return News.objects.filter(
            llm_tags__contains=[tag.name], status="published", deleted_at__isnull=True
        )

    def get_tag_counts(self) -> Dict["Tag", int]:  # type: ignore
        """
        Get article counts for all tags.
        Returns a dictionary with tag objects as keys and counts as values.
        """
        # Get all tags
        tags = cast("QuerySet[Tag]", self.all())
        tag_counts: Dict["Tag", int] = {}

        for tag in tags:
            count = tag.get_news_count()
            tag_counts[tag] = count

        return tag_counts


class Tag(models.Model):
    """
    Hierarchical tag model for organizing news articles.
    """

    name: models.CharField = models.CharField(
        max_length=100, unique=True, help_text="Tag name (must be unique)"
    )
    slug: models.SlugField = models.SlugField(
        max_length=120, unique=True, help_text="URL-friendly slug for the tag"
    )
    parent = models.ForeignKey(
        "self",
        null=True,
        blank=True,
        on_delete=models.CASCADE,
        related_name="children",
        help_text="Parent tag for hierarchical relationships",
    )

    # Use custom manager
    objects = TagManager()

    class Meta:
        verbose_name = "Tag"
        verbose_name_plural = "Tags"
        ordering = ["name"]

    def __str__(self) -> str:
        return self.name

    def save(self, *args: Any, **kwargs: Any) -> None:
        """Auto-generate slug from name if not provided"""
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)

    @property
    def hierarchy_path(self) -> str:
        """Return the tag name (flat structure)"""
        return self.name

    def get_news_count(self) -> int:
        """Get count of published news articles that have this tag"""
        # Query published news articles that have this tag in their llm_tags array
        return News.objects.filter(
            llm_tags__contains=[self.name], status="published", deleted_at__isnull=True
        ).count()

    @classmethod
    def get_top_level_categories(cls) -> "QuerySet[Tag]":
        """Get all top-level tag categories (tags with no parent)"""
        return cls.objects.filter(parent__isnull=True).order_by("name")
