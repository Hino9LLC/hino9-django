"""
Test cases for News views.

Tests validate HTTP responses, templates, context data, pagination,
filtering, navigation, and user experience.
"""

from datetime import timedelta
from unittest.mock import MagicMock, patch

from django.test import Client, TestCase, override_settings
from django.urls import reverse
from django.utils import timezone

from news.models import News, Tag


class NewsListViewTests(TestCase):
    """Test cases for news list view."""

    def setUp(self) -> None:
        """Set up test client and data."""
        self.client = Client()
        self.url = reverse("news:list")

    def test_returns_200_for_get_request(self) -> None:
        """Test that news list view returns HTTP 200."""
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)

    def test_uses_correct_template(self) -> None:
        """Test that news list view uses correct template."""
        response = self.client.get(self.url)
        self.assertTemplateUsed(response, "news/news_list.html")

    def test_context_contains_required_data(self) -> None:
        """Test that context contains news_articles and page_obj."""
        response = self.client.get(self.url)
        self.assertIn("news_articles", response.context)
        self.assertIn("page_obj", response.context)
        self.assertIn("total_count", response.context)

    def test_pagination_shows_10_per_page(self) -> None:
        """Test that pagination shows 10 articles per page."""
        # Create 25 published articles
        categories = ["Technology", "Science", "Business", "Health", "Sports"]
        for i in range(25):
            category = categories[i % len(categories)]
            News.objects.create(
                title=f"{category} News: Update {i}",
                llm_headline=f"{category} Headlines",
                llm_summary=f"Latest {category} developments and insights.",
                llm_bullets=[f"Point {i}.1", f"Point {i}.2", f"Point {i}.3"],
                llm_tags=[category, "News", "Updates"],
                status="published",
                deleted_at=None,
                article_date=timezone.now() - timedelta(days=i),
            )

        response = self.client.get(self.url)
        self.assertEqual(len(response.context["news_articles"]), 10)

    def test_pagination_page_2_shows_next_articles(self) -> None:
        """Test that page 2 shows the next set of articles."""
        # Create 25 published articles
        categories = ["Technology", "Science", "Business", "Health", "Sports"]
        for i in range(25):
            category = categories[i % len(categories)]
            News.objects.create(
                title=f"{category} News: Article {i}",
                llm_headline=f"{category} Latest",
                llm_summary=f"Important {category} news and updates.",
                llm_bullets=[f"Detail {i}.1", f"Detail {i}.2", f"Detail {i}.3"],
                llm_tags=[category, "Breaking", "Updates"],
                status="published",
                deleted_at=None,
                article_date=timezone.now() - timedelta(days=i),
            )

        response = self.client.get(self.url + "?page=2")
        self.assertEqual(len(response.context["news_articles"]), 10)

    def test_invalid_page_number_defaults_to_page_1(self) -> None:
        """Test that invalid page numbers default to page 1."""
        News.objects.create(
            title="Pagination Test Article",
            llm_headline="Testing Pagination Handling",
            llm_summary="Article for testing invalid page number handling",
            llm_bullets=[
                "Test pagination",
                "Invalid page handling",
                "Default behavior",
            ],
            llm_tags=["Testing", "Pagination"],
            status="published",
            deleted_at=None,
        )

        response = self.client.get(self.url + "?page=abc")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context["page_obj"].number, 1)

    def test_page_out_of_range_shows_last_page(self) -> None:
        """Test that page numbers beyond range show last page."""
        # Create 25 articles (2 pages)
        topics = ["Technology", "Science", "Business", "Health", "Sports"]
        for i in range(25):
            topic = topics[i % len(topics)]
            News.objects.create(
                title=f"{topic} Article {i}",
                llm_headline=f"{topic} Update",
                llm_summary=f"Latest {topic} news and developments",
                llm_bullets=[f"Point {i}.1", f"Point {i}.2", f"Point {i}.3"],
                llm_tags=[topic, "News"],
                status="published",
                deleted_at=None,
                article_date=timezone.now() - timedelta(days=i),
            )

        response = self.client.get(self.url + "?page=999")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context["page_obj"].number, 3)

    def test_only_shows_published_articles(self) -> None:
        """Test that only published articles are shown."""
        published = News.objects.create(
            title="Published Article",
            llm_headline="Published Content",
            llm_summary="This article is published and visible",
            llm_bullets=["Published status", "Publicly visible", "In production"],
            llm_tags=["Published", "Live"],
            status="published",
            deleted_at=None,
        )
        unpublished = News.objects.create(
            title="Unpublished Draft",
            llm_headline="Draft Content",
            llm_summary="This article is in draft status",
            llm_bullets=["Draft status", "Not visible", "Under review"],
            llm_tags=["Draft"],
            status="draft",
            deleted_at=None,
        )

        response = self.client.get(self.url)
        articles = list(response.context["news_articles"])

        self.assertIn(published, articles)
        self.assertNotIn(unpublished, articles)

    def test_excludes_deleted_articles(self) -> None:
        """Test that deleted articles are excluded."""
        active = News.objects.create(
            title="Active Article",
            llm_headline="Active Content",
            llm_summary="This article is active and available",
            llm_bullets=["Active status", "Available to users", "Not deleted"],
            llm_tags=["Active", "Live"],
            status="published",
            deleted_at=None,
        )
        deleted = News.objects.create(
            title="Deleted Article",
            llm_headline="Deleted Content",
            llm_summary="This article has been deleted",
            llm_bullets=["Deleted status", "Not available", "Removed"],
            llm_tags=["Deleted"],
            status="published",
            deleted_at=timezone.now(),
        )

        response = self.client.get(self.url)
        articles = list(response.context["news_articles"])

        self.assertIn(active, articles)
        self.assertNotIn(deleted, articles)

    def test_articles_ordered_by_date_desc(self) -> None:
        """Test that articles are ordered by article_date DESC."""
        old = News.objects.create(
            title="Older Article from Last Week",
            llm_headline="Old News",
            llm_summary="This is an older article from 10 days ago",
            llm_bullets=["Older content", "Published last week", "Historical"],
            llm_tags=["Archive", "Old"],
            status="published",
            deleted_at=None,
            article_date=timezone.now() - timedelta(days=10),
        )
        new = News.objects.create(
            title="Latest Breaking News",
            llm_headline="Fresh News",
            llm_summary="This is the latest article published today",
            llm_bullets=["Breaking news", "Just published", "Current"],
            llm_tags=["Breaking", "Latest"],
            status="published",
            deleted_at=None,
            article_date=timezone.now(),
        )

        response = self.client.get(self.url)
        articles = list(response.context["news_articles"])

        self.assertEqual(articles[0], new)
        self.assertEqual(articles[1], old)

    def test_empty_state_when_no_articles(self) -> None:
        """Test empty state when no articles in database."""
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.context["news_articles"]), 0)

    def test_exactly_20_articles_shows_pagination(self) -> None:
        """Test that exactly 20 articles shows two pages with 10 per page."""
        for i in range(20):
            News.objects.create(
                title=f"Article {i}",
                status="published",
                deleted_at=None,
            )

        response = self.client.get(self.url)
        self.assertEqual(response.context["page_obj"].paginator.num_pages, 2)

    def test_21_articles_shows_pagination(self) -> None:
        """Test that 21 articles creates 3 pages with 10 per page."""
        for i in range(21):
            News.objects.create(
                title=f"Article {i}",
                status="published",
                deleted_at=None,
            )

        response = self.client.get(self.url)
        self.assertEqual(response.context["page_obj"].paginator.num_pages, 3)


class NewsDetailViewTests(TestCase):
    """Test cases for news detail view."""

    def setUp(self) -> None:
        """Set up test client and data."""
        self.client = Client()
        self.article = News.objects.create(
            title="Test Article",
            status="published",
            deleted_at=None,
            llm_bullets=["Key point 1", "Key point 2", "Key point 3"],
            llm_tags=["Test", "News"],
        )
        self.url = reverse(
            "news:detail",
            kwargs={"news_id": self.article.id, "slug": self.article.slug},
        )

    def test_returns_200_for_valid_article(self) -> None:
        """Test that detail view returns HTTP 200 for valid published article."""
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)

    def test_uses_correct_template(self) -> None:
        """Test that detail view uses correct template."""
        response = self.client.get(self.url)
        self.assertTemplateUsed(response, "news/news_detail.html")

    def test_context_contains_article(self) -> None:
        """Test that context contains news_article."""
        response = self.client.get(self.url)
        self.assertIn("news_article", response.context)
        self.assertEqual(response.context["news_article"], self.article)

    def test_returns_404_for_nonexistent_article(self) -> None:
        """Test that 404 is returned for non-existent article ID."""
        url = reverse("news:detail", kwargs={"news_id": 99999, "slug": "fake-slug"})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 404)

    def test_returns_404_for_unpublished_article(self) -> None:
        """Test that 404 is returned for unpublished article."""
        unpublished = News.objects.create(
            title="Unpublished",
            status="draft",
            deleted_at=None,
            llm_bullets=["Point 1", "Point 2"],
            llm_tags=["Draft"],
        )
        url = reverse(
            "news:detail", kwargs={"news_id": unpublished.id, "slug": unpublished.slug}
        )
        response = self.client.get(url)
        self.assertEqual(response.status_code, 404)

    def test_returns_404_for_deleted_article(self) -> None:
        """Test that 404 is returned for deleted article."""
        deleted = News.objects.create(
            title="Deleted",
            status="published",
            deleted_at=timezone.now(),
            llm_bullets=["Point 1", "Point 2"],
            llm_tags=["Deleted"],
        )
        url = reverse(
            "news:detail", kwargs={"news_id": deleted.id, "slug": deleted.slug}
        )
        response = self.client.get(url)
        self.assertEqual(response.status_code, 404)

    def test_wrong_slug_redirects_to_correct_slug(self) -> None:
        """Test that wrong slug redirects to correct slug."""
        url = reverse(
            "news:detail", kwargs={"news_id": self.article.id, "slug": "wrong-slug"}
        )
        response = self.client.get(url)
        self.assertEqual(response.status_code, 301)  # Permanent redirect
        self.assertTrue(hasattr(response, "url"))  # Type guard

    def test_preserves_from_page_navigation(self) -> None:
        """Test that from_page parameter is preserved in context."""
        response = self.client.get(self.url + "?from_page=2")
        self.assertEqual(response.context["from_page"], "2")

    def test_preserves_search_context(self) -> None:
        """Test that search context is preserved."""
        response = self.client.get(self.url + "?from_search=1&q=test&type=vector")
        self.assertEqual(response.context["from_search"], "1")
        self.assertEqual(response.context["search_query"], "test")
        self.assertEqual(response.context["search_type"], "vector")

    def test_preserves_tag_context(self) -> None:
        """Test that tag context is preserved."""
        response = self.client.get(
            self.url + "?from_tag=1&tag_slug=python&tag_name=Python"
        )
        self.assertEqual(response.context["from_tag"], "1")
        self.assertEqual(response.context["tag_slug"], "python")
        self.assertEqual(response.context["tag_name"], "Python")


class NewsDetailRedirectViewTests(TestCase):
    """Test cases for news detail redirect views."""

    def setUp(self) -> None:
        """Set up test data."""
        self.client = Client()
        self.article = News.objects.create(
            title="Test Article",
            status="published",
            deleted_at=None,
        )

    def test_redirect_without_slug(self) -> None:
        """Test that URL without slug redirects to URL with slug."""
        url = reverse("news:detail_redirect", kwargs={"news_id": self.article.id})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 301)  # Permanent redirect
        expected_url = reverse(
            "news:detail",
            kwargs={"news_id": self.article.id, "slug": self.article.slug},
        )
        self.assertTrue(hasattr(response, "url"))  # Type guard
        self.assertIn(expected_url, response.url)  # type: ignore[attr-defined]

    def test_redirect_returns_404_for_nonexistent_article(self) -> None:
        """Test that redirect returns 404 if article doesn't exist."""
        url = reverse("news:detail_redirect", kwargs={"news_id": 99999})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 404)


@override_settings(RATELIMIT_ENABLE=False)
class NewsSearchViewTests(TestCase):
    """Test cases for news search view."""

    def setUp(self) -> None:
        """Set up test client and data."""
        self.client = Client()
        self.url = reverse("news:search")

        # Create some test articles
        self.article1 = News.objects.create(
            title="AI and Machine Learning Advances",
            llm_headline="AI Breaking New Ground",
            llm_summary="An article about artificial intelligence and recent machine learning breakthroughs",
            llm_bullets=[
                "New AI models released",
                "Performance improvements",
                "Industry adoption growing",
            ],
            llm_tags=["AI", "Machine Learning", "Technology"],
            status="published",
            deleted_at=None,
        )
        self.article2 = News.objects.create(
            title="Python Programming Best Practices",
            llm_headline="Python Development Guide",
            llm_summary="An article about Python programming techniques and best practices",
            llm_bullets=[
                "Code quality tips",
                "Performance optimization",
                "Testing strategies",
            ],
            llm_tags=["Python", "Programming", "Development"],
            status="published",
            deleted_at=None,
        )

    def test_returns_200_for_get_request(self) -> None:
        """Test that search view returns HTTP 200."""
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)

    def test_uses_correct_template(self) -> None:
        """Test that search view uses correct template."""
        response = self.client.get(self.url)
        self.assertTemplateUsed(response, "news/news_search.html")

    def test_context_contains_search_data(self) -> None:
        """Test that context contains query, search_type, and results."""
        response = self.client.get(self.url + "?q=test&type=text")
        self.assertIn("query", response.context)
        self.assertIn("search_type", response.context)
        self.assertIn("news_articles", response.context)
        self.assertIn("total_count", response.context)

    def test_empty_query_returns_no_results(self) -> None:
        """Test that empty query returns no results."""
        response = self.client.get(self.url + "?q=")
        self.assertEqual(response.context["total_count"], 0)

    def test_whitespace_only_query_returns_no_results(self) -> None:
        """Test that whitespace-only query returns no results."""
        response = self.client.get(self.url + "?q=%20%20%20")
        self.assertEqual(response.context["total_count"], 0)

    def test_query_preserved_in_context(self) -> None:
        """Test that query is preserved in context for display."""
        response = self.client.get(self.url + "?q=test+query")
        self.assertIn("test query", response.context["query"])

    def test_search_type_preserved_in_context(self) -> None:
        """Test that search type is preserved in context."""
        response = self.client.get(self.url + "?q=test&type=vector")
        self.assertEqual(response.context["search_type"], "vector")

    def test_defaults_to_hybrid_search(self) -> None:
        """Test that search defaults to hybrid when type not specified."""
        response = self.client.get(self.url + "?q=test")
        self.assertEqual(response.context["search_type"], "hybrid")

    def test_invalid_search_type_defaults_to_hybrid(self) -> None:
        """Test that invalid search type defaults to hybrid."""
        response = self.client.get(self.url + "?q=test&type=invalid")
        self.assertEqual(response.context["search_type"], "hybrid")

    def test_only_returns_published_articles(self) -> None:
        """Test that search only returns published articles."""
        unpublished = News.objects.create(
            title="Unpublished AI Article",
            status="draft",
            deleted_at=None,
        )

        response = self.client.get(self.url + "?q=AI&type=text")
        results = list(response.context["news_articles"])

        self.assertNotIn(unpublished, results)

    def test_excludes_deleted_articles(self) -> None:
        """Test that search excludes deleted articles."""
        deleted = News.objects.create(
            title="Deleted AI Article",
            status="published",
            deleted_at=timezone.now(),
        )

        response = self.client.get(self.url + "?q=AI&type=text")
        results = list(response.context["news_articles"])

        self.assertNotIn(deleted, results)

    @override_settings(RATELIMIT_ENABLE=True)
    def test_rate_limiting_allows_first_100_searches(self) -> None:
        """Test that first 100 searches within an hour succeed."""
        # Clear cache to ensure clean state
        from django.core.cache import cache

        cache.clear()

        # Make 100 requests
        for i in range(100):
            response = self.client.get(self.url + f"?q=test{i}&type=text")
            self.assertEqual(response.status_code, 200)

    @override_settings(
        RATELIMIT_ENABLE=True,
        CACHES={
            "default": {
                "BACKEND": "django.core.cache.backends.locmem.LocMemCache",
                "LOCATION": "test-ratelimit-cache",
            }
        },
    )
    def test_rate_limiting_blocks_101st_search(self) -> None:
        """Test that 101st search within the same hour is blocked."""
        # Clear cache to ensure clean state
        from django.core.cache import cache

        cache.clear()

        # Make 101 requests
        for i in range(101):
            response = self.client.get(self.url + f"?q=test{i}&type=text")

        # 101st request should be rate limited
        self.assertEqual(response.status_code, 429)

    @override_settings(
        RATELIMIT_ENABLE=True,
        CACHES={
            "default": {
                "BACKEND": "django.core.cache.backends.locmem.LocMemCache",
                "LOCATION": "test-ratelimit-cache",
            }
        },
    )
    def test_rate_limit_response_shows_error(self) -> None:
        """Test that rate limit response shows error message."""
        # Clear cache to ensure clean state
        from django.core.cache import cache

        cache.clear()

        # Make 101 requests to trigger rate limit
        for i in range(101):
            response = self.client.get(self.url + f"?q=test{i}&type=text")

        # Check for rate limit context
        self.assertIn("rate_limited", response.context)
        self.assertTrue(response.context["rate_limited"])


class TagViewsTests(TestCase):
    """Test cases for tag-related views."""

    def setUp(self) -> None:
        """Set up test client and data."""
        self.client = Client()
        self.tag1 = Tag.objects.create(name="Python", slug="python")
        self.tag2 = Tag.objects.create(name="JavaScript", slug="javascript")

    @patch("news.models.Tag.get_news_count")
    def test_tags_index_returns_200(self, mock_get_news_count: MagicMock) -> None:
        """Test that tags index returns HTTP 200."""
        mock_get_news_count.return_value = 3
        response = self.client.get(reverse("news:tags_index"))
        self.assertEqual(response.status_code, 200)

    @patch("news.models.Tag.get_news_count")
    def test_tags_index_uses_correct_template(
        self, mock_get_news_count: MagicMock
    ) -> None:
        """Test that tags index uses correct template."""
        mock_get_news_count.return_value = 3
        response = self.client.get(reverse("news:tags_index"))
        self.assertTemplateUsed(response, "news/tags_index.html")

    @patch("news.models.Tag.get_news_count")
    def test_tags_index_context_contains_tags(
        self, mock_get_news_count: MagicMock
    ) -> None:
        """Test that tags index context contains tags list."""
        mock_get_news_count.return_value = 3
        response = self.client.get(reverse("news:tags_index"))
        self.assertIn("tags", response.context)

    @patch.object(Tag, "get_news_count")
    def test_tags_index_only_shows_tags_with_more_than_2_articles(
        self, mock_get_news_count: MagicMock
    ) -> None:
        """Test that tags index only shows tags with >2 articles."""

        # Use return different values for each tag
        # Tags are ordered alphabetically: JavaScript, then Python
        # JavaScript should return 2, Python should return 3
        mock_get_news_count.side_effect = [2, 3]

        response = self.client.get(reverse("news:tags_index"))
        tags = response.context["tags"]

        self.assertEqual(len(tags), 1)
        self.assertEqual(tags[0]["tag"].name, "Python")

    @patch("news.models.Tag.get_news_count")
    def test_tags_ordered_alphabetically(self, mock_get_news_count: MagicMock) -> None:
        """Test that tags are ordered alphabetically by name."""
        Tag.objects.create(name="Zebra", slug="zebra")
        Tag.objects.create(name="Apple", slug="apple")

        mock_get_news_count.return_value = 3

        response = self.client.get(reverse("news:tags_index"))
        tags = response.context["tags"]

        tag_names = [t["tag"].name for t in tags]
        self.assertEqual(tag_names, sorted(tag_names))

    @patch("news.models.Tag.objects.get_articles_for_tag")
    def test_tag_detail_returns_200_for_valid_slug(
        self, mock_get_articles: MagicMock
    ) -> None:
        """Test that tag detail returns 200 for valid tag slug."""
        from django.db.models import QuerySet

        mock_get_articles.return_value = QuerySet(model=News).none()

        url = reverse("news:tag_detail", kwargs={"tag_slug": "python"})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)

    def test_tag_detail_returns_404_for_invalid_slug(self) -> None:
        """Test that tag detail returns 404 for non-existent tag slug."""
        url = reverse("news:tag_detail", kwargs={"tag_slug": "nonexistent"})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 404)

    @patch("news.models.Tag.objects.get_articles_for_tag")
    def test_tag_detail_uses_correct_template(
        self, mock_get_articles: MagicMock
    ) -> None:
        """Test that tag detail uses correct template."""
        from django.db.models import QuerySet

        mock_get_articles.return_value = QuerySet(model=News).none()

        url = reverse("news:tag_detail", kwargs={"tag_slug": "python"})
        response = self.client.get(url)
        self.assertTemplateUsed(response, "news/tag_detail.html")

    @patch("news.models.Tag.objects.get_articles_for_tag")
    def test_tag_detail_context_contains_tag_and_articles(
        self, mock_get_articles: MagicMock
    ) -> None:
        """Test that tag detail context contains tag and articles."""
        from django.db.models import QuerySet

        mock_get_articles.return_value = QuerySet(model=News).none()

        url = reverse("news:tag_detail", kwargs={"tag_slug": "python"})
        response = self.client.get(url)

        self.assertIn("tag", response.context)
        self.assertIn("articles", response.context)


class RobotsTxtViewTests(TestCase):
    """Test cases for robots.txt view."""

    def setUp(self) -> None:
        """Set up test client."""
        self.client = Client()
        self.url = "/robots.txt"

    def test_returns_200(self) -> None:
        """Test that robots.txt returns HTTP 200."""
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)

    def test_content_type_is_text_plain(self) -> None:
        """Test that robots.txt has correct content type."""
        response = self.client.get(self.url)
        self.assertEqual(response["Content-Type"], "text/plain")

    def test_contains_user_agent(self) -> None:
        """Test that robots.txt contains User-agent directive."""
        response = self.client.get(self.url)
        self.assertIn(b"User-agent:", response.content)

    def test_contains_allow_directive(self) -> None:
        """Test that robots.txt contains Allow directive."""
        response = self.client.get(self.url)
        self.assertIn(b"Allow:", response.content)

    def test_contains_sitemap_reference(self) -> None:
        """Test that robots.txt contains Sitemap reference."""
        response = self.client.get(self.url)
        self.assertIn(b"Sitemap:", response.content)


class KeybaseTxtViewTests(TestCase):
    """Test cases for keybase.txt view."""

    def setUp(self) -> None:
        """Set up test client."""
        self.client = Client()
        self.url = "/keybase.txt"

    def test_returns_404_when_file_not_found(self) -> None:
        """Test that keybase.txt returns HTTP 404 when file doesn't exist."""
        from django.conf import settings

        keybase_path = settings.BASE_DIR / "keybase.txt"
        temp_file_path = None

        try:
            # Backup existing file if it exists
            if keybase_path.exists():
                temp_file_path = keybase_path.with_suffix(".bak")
                keybase_path.rename(temp_file_path)

            # Test the response when file doesn't exist
            response = self.client.get(self.url)
            self.assertEqual(response.status_code, 404)
            self.assertIn(b"keybase.txt not found", response.content)

        finally:
            # Restore original file if it existed
            if temp_file_path and temp_file_path.exists():
                temp_file_path.rename(keybase_path)

    def test_content_type_is_text_plain(self) -> None:
        """Test that keybase.txt has correct content type when file exists."""
        from django.conf import settings

        test_content = "test keybase content"
        keybase_path = settings.BASE_DIR / "keybase.txt"
        temp_file_path = None

        try:
            # Backup existing file if it exists
            if keybase_path.exists():
                temp_file_path = keybase_path.with_suffix(".bak")
                keybase_path.rename(temp_file_path)

            # Write test content to keybase.txt
            with open(keybase_path, "w") as f:
                f.write(test_content)

            # Test the response
            response = self.client.get(self.url)
            self.assertEqual(response.status_code, 200)
            self.assertEqual(response["Content-Type"], "text/plain")
            self.assertEqual(response.content.decode(), test_content)

        finally:
            # Clean up the test file
            if keybase_path.exists():
                keybase_path.unlink()
            # Restore original file if it existed
            if temp_file_path and temp_file_path.exists():
                temp_file_path.rename(keybase_path)
