from typing import Any, Dict, Optional

from django.contrib import admin, messages
from django.core.management import call_command
from django.db.models import QuerySet
from django.http import HttpRequest, HttpResponse, HttpResponseRedirect
from django.urls import path
from django.utils.html import format_html

from .models import News, Tag


@admin.register(News)
class NewsAdmin(admin.ModelAdmin):
    """
    Django admin configuration for News model.
    """

    list_display = [
        "id",
        "display_title",
        "domain",
        "site_name",
        "status",
        "article_date",
        "created_at",
    ]

    list_filter = [
        "status",
        "domain",
        "site_name",
        "created_at",
        "article_date",
    ]

    search_fields = [
        "title",
        "llm_headline",
        "summary",
        "llm_summary",
        "domain",
        "site_name",
        "url",
    ]

    readonly_fields = [
        "id",
        "created_at",
        "updated_at",
        "processed_at",
        "deleted_at",
        "image_preview",
    ]

    fieldsets = (
        (
            "Basic Information",
            {
                "fields": (
                    "id",
                    "title",
                    "summary",
                    "article_date",
                    "url",
                )
            },
        ),
        (
            "LLM Generated Content",
            {
                "fields": (
                    "llm_headline",
                    "llm_summary",
                    "llm_bullets",
                    "llm_tags",
                ),
                "classes": ("collapse",),
            },
        ),
        (
            "Source Information",
            {
                "fields": (
                    "domain",
                    "site_name",
                    "image_url",
                    "image_preview",
                    "article",
                )
            },
        ),
        (
            "Status & Processing",
            {
                "fields": (
                    "status",
                    "error_message",
                    "created_at",
                    "updated_at",
                    "processed_at",
                    "deleted_at",
                )
            },
        ),
        (
            "Content",
            {
                "fields": ("content_text",),
                "classes": ("collapse",),
            },
        ),
    )

    def display_title(self, obj: News) -> str:
        """Display the preferred title in admin list"""
        return obj.display_title

    display_title.short_description = "Title"  # type: ignore
    display_title.admin_order_field = "title"  # type: ignore

    def image_preview(self, obj: News) -> str:
        """Display image preview in admin interface"""
        if obj.image_url:
            return format_html(
                '<img src="{}" alt="Article image" style="max-width: 300px; max-height: 200px; border-radius: 4px; border: 1px solid #ddd;" />',
                obj.image_url,
            )
        return "No image"

    image_preview.short_description = "Image Preview"  # type: ignore

    def get_queryset(self, request: HttpRequest) -> QuerySet[News]:
        """Optimize queryset for admin list view"""
        return super().get_queryset(request)


@admin.register(Tag)
class TagAdmin(admin.ModelAdmin):
    """
    Django admin configuration for Tag model.
    """

    actions = ["refresh_tags_from_news"]

    list_display = [
        "name",
        "slug",
        "article_count",
        "hierarchy_path",
    ]

    search_fields = [
        "name",
        "slug",
    ]

    readonly_fields = [
        "article_count",
        "hierarchy_path",
    ]

    fieldsets = (
        (
            "Basic Information",
            {
                "fields": (
                    "name",
                    "slug",
                )
            },
        ),
        (
            "Statistics",
            {
                "fields": (
                    "article_count",
                    "hierarchy_path",
                ),
                "classes": ("collapse",),
            },
        ),
    )

    def article_count(self, obj: Tag) -> int:
        """Display article count for this tag"""
        return obj.get_news_count()

    article_count.short_description = "Article Count"  # type: ignore

    def hierarchy_path(self, obj: Tag) -> str:
        """Display the tag name (flat structure)"""
        return obj.hierarchy_path

    hierarchy_path.short_description = "Tag Name"  # type: ignore

    def get_queryset(self, request: HttpRequest) -> QuerySet[Tag]:
        """Optimize queryset for admin list view"""
        return super().get_queryset(request)

    def changelist_view(
        self, request: HttpRequest, extra_context: Optional[Dict[str, Any]] = None
    ) -> HttpResponse:
        """Override changelist view to handle actions without selected items"""
        # Handle the refresh action even when no items are selected
        if request.method == "POST" and "action" in request.POST:
            action = request.POST.get("action")
            if action == "refresh_tags_from_news":
                # Call the action directly
                self.refresh_tags_from_news(request, Tag.objects.all())
                # Redirect to avoid re-posting
                return HttpResponseRedirect(request.get_full_path())

        return super().changelist_view(request, extra_context)

    def get_urls(self) -> list:
        """Add custom URLs for tag admin"""
        urls = super().get_urls()
        custom_urls = [
            path(
                "refresh/",
                self.admin_site.admin_view(self.refresh_tags_view),
                name="refresh_tags",
            ),
        ]
        return custom_urls + urls

    def refresh_tags_view(self, request: HttpRequest) -> HttpResponse:
        """Custom view to refresh tags from news articles"""
        try:
            # Run the management command
            call_command("refresh_tags")

            # Count the results
            total_tags = Tag.objects.count()

            self.message_user(
                request,
                f"Successfully refreshed tags table. {total_tags} tags now in database.",
                messages.SUCCESS,
            )
        except Exception as e:
            self.message_user(
                request,
                f"Error refreshing tags: {str(e)}",
                messages.ERROR,
            )

        # Redirect back to the changelist
        return HttpResponseRedirect("../")

    @admin.action(description="Refresh tags from news articles")
    def refresh_tags_from_news(
        self, request: HttpRequest, queryset: QuerySet[Tag]
    ) -> None:
        """Refresh the tags table from news article llm_tags arrays"""
        # This action works even when no items are selected
        try:
            # Run the management command
            call_command("refresh_tags")

            # Count the results
            total_tags = Tag.objects.count()

            self.message_user(
                request,
                f"Successfully refreshed tags table. {total_tags} tags now in database.",
                messages.SUCCESS,
            )
        except Exception as e:
            self.message_user(
                request,
                f"Error refreshing tags: {str(e)}",
                messages.ERROR,
            )
