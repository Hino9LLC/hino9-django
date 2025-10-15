from unittest.mock import MagicMock, patch

from django.test import Client, TestCase
from django.urls import reverse

from news.models import Tag


class TagViewTests(TestCase):
    """Test cases for tag-related views."""

    def setUp(self) -> None:
        """Set up test data."""
        self.client = Client()

        # Create test tags with various names to test slug generation
        self.tag1 = Tag.objects.create(name="Machine Learning", slug="machine-learning")
        self.tag2 = Tag.objects.create(
            name="Artificial Intelligence", slug="artificial-intelligence"
        )
        self.tag3 = Tag.objects.create(name="Deep Learning", slug="deep-learning")
        self.tag4 = Tag.objects.create(name="Python", slug="python")
        self.tag5 = Tag.objects.create(name="JavaScript", slug="javascript")

    @patch("news.models.Tag.get_news_count")
    def test_tags_index_view_renders(self, mock_get_news_count: MagicMock) -> None:
        """Test that the tags index view renders successfully."""
        # Mock the get_news_count method since it uses PostgreSQL array operations
        mock_get_news_count.return_value = 5

        # Make request to tags_index view
        response = self.client.get(reverse("news:tags_index"))

        # Assert response is successful
        self.assertEqual(response.status_code, 200)

        # Assert template is used
        self.assertTemplateUsed(response, "news/tags_index.html")

        # Assert context has tags
        self.assertIn("tags", response.context)

    def test_tag_model_slug_generation(self) -> None:
        """Test that Tag model generates slugs correctly."""
        # Test various tag names and their expected slugs
        test_cases = [
            ("Web Development", "web-development"),
            ("Mobile Apps", "mobile-apps"),
            ("Cloud Computing", "cloud-computing"),
            ("Data Science", "data-science"),
            ("Blockchain Technology", "blockchain-technology"),
            ("Internet of Things", "internet-of-things"),
            # Edge cases with special characters
            ("Mergers and Acquisitions", "mergers-and-acquisitions"),
            ("React.js", "reactjs"),
            ("mRNA", "mrna"),
            ("Enterprise AI", "enterprise-ai"),
        ]

        for name, expected_slug in test_cases:
            tag = Tag.objects.create(name=name)
            self.assertEqual(
                tag.slug,
                expected_slug,
                f"Slug for '{name}' should be '{expected_slug}', got '{tag.slug}'",
            )
            # Clean up
            tag.delete()

    @patch("news.models.Tag.objects.get_articles_for_tag")
    def test_known_slug_returns_200(self, mock_get_articles: MagicMock) -> None:
        """Test that known tag slugs return a successful response."""
        # Mock the get_articles_for_tag method to return an empty News QuerySet
        from django.db.models import QuerySet

        from news.models import News

        mock_queryset = QuerySet(model=News).none()  # type: ignore  # Empty News queryset
        mock_get_articles.return_value = mock_queryset

        # Test with a known slug from our test data
        response = self.client.get(
            reverse("news:tag_detail", kwargs={"tag_slug": "machine-learning"})
        )

        # Assert response is successful
        self.assertEqual(response.status_code, 200)

        # Verify the tag_detail template is used
        self.assertTemplateUsed(response, "news/tag_detail.html")

        # Verify context contains the expected tag
        self.assertIn("tag", response.context)
        self.assertEqual(response.context["tag"].slug, "machine-learning")

    def test_unknown_slug_returns_404(self) -> None:
        """Test that unknown/rogue tag slugs return a 404 response."""
        # Test with a slug that doesn't exist
        response = self.client.get(
            reverse("news:tag_detail", kwargs={"tag_slug": "non-existent-slug"})
        )

        # Assert response is 404
        self.assertEqual(response.status_code, 404)

    @patch("news.models.Tag.objects.get_articles_for_tag")
    def test_case_sensitive_slug_handling(self, mock_get_articles: MagicMock) -> None:
        """Test that slugs are case-sensitive and handle uppercase properly."""
        # Mock the get_articles_for_tag method to return an empty News QuerySet
        from django.db.models import QuerySet

        from news.models import News

        mock_queryset = QuerySet(model=News).none()  # type: ignore  # Empty News queryset
        mock_get_articles.return_value = mock_queryset

        # Create a tag with mixed case
        tag = Tag.objects.create(name="Test Case", slug="test-case")

        try:
            # Test with correct case
            response = self.client.get(
                reverse("news:tag_detail", kwargs={"tag_slug": "test-case"})
            )
            self.assertEqual(response.status_code, 200)

            # Test with wrong case (should return 404 since slugs are case-sensitive)
            response = self.client.get(
                reverse("news:tag_detail", kwargs={"tag_slug": "Test-Case"})
            )
            self.assertEqual(response.status_code, 404)

        finally:
            # Clean up
            tag.delete()

    def test_tags_index_filters_tags_with_more_than_2_articles(self) -> None:
        """Test that tags index only shows tags with more than 2 articles."""
        from news.models import News

        # Create News articles with different tag combinations
        # Machine Learning: 3 articles (should show)
        News.objects.create(
            title="ML Article 1",
            llm_tags=["Machine Learning"],
            status="published",
        )
        News.objects.create(
            title="ML Article 2",
            llm_tags=["Machine Learning"],
            status="published",
        )
        News.objects.create(
            title="ML Article 3",
            llm_tags=["Machine Learning"],
            status="published",
        )

        # Artificial Intelligence: 2 articles (should be filtered out)
        News.objects.create(
            title="AI Article 1",
            llm_tags=["Artificial Intelligence"],
            status="published",
        )
        News.objects.create(
            title="AI Article 2",
            llm_tags=["Artificial Intelligence"],
            status="published",
        )

        # Deep Learning: 1 article (should be filtered out)
        News.objects.create(
            title="DL Article 1",
            llm_tags=["Deep Learning"],
            status="published",
        )

        # Python: 0 articles (should be filtered out)
        # JavaScript: 0 articles (should be filtered out)

        # Make request to tags_index view
        response = self.client.get(reverse("news:tags_index"))

        # Assert response is successful
        self.assertEqual(response.status_code, 200)

        # Assert context has tags
        self.assertIn("tags", response.context)
        tags_in_context = response.context["tags"]

        # Should only have Machine Learning tag (3 articles > 2)
        # AI, Deep Learning, Python, and JavaScript should be filtered out
        self.assertEqual(len(tags_in_context), 1)
        self.assertEqual(tags_in_context[0]["tag"].name, "Machine Learning")
        self.assertEqual(tags_in_context[0]["article_count"], 3)

    def test_tags_index_boundary_filtering(self) -> None:
        """Test boundary condition: tags with exactly 2 articles should not show, 3+ should show."""
        from news.models import News

        # Create tags for testing boundary conditions
        Tag.objects.create(name="Zero Articles", slug="zero-articles")
        Tag.objects.create(name="One Article", slug="one-article")
        Tag.objects.create(name="Two Articles", slug="two-articles")
        Tag.objects.create(name="Three Articles", slug="three-articles")
        Tag.objects.create(name="Four Articles", slug="four-articles")

        # Create 0 articles for "Zero Articles" tag (should not show)

        # Create 1 article for "One Article" tag (should not show)
        News.objects.create(
            title="Article for One",
            llm_tags=["One Article"],
            status="published",
        )

        # Create 2 articles for "Two Articles" tag (should not show - boundary)
        for i in range(2):
            News.objects.create(
                title=f"Article for Two {i}",
                llm_tags=["Two Articles"],
                status="published",
            )

        # Create 3 articles for "Three Articles" tag (should show - boundary)
        for i in range(3):
            News.objects.create(
                title=f"Article for Three {i}",
                llm_tags=["Three Articles"],
                status="published",
            )

        # Create 4 articles for "Four Articles" tag (should show)
        for i in range(4):
            News.objects.create(
                title=f"Article for Four {i}",
                llm_tags=["Four Articles"],
                status="published",
            )

        # Make request to tags_index view
        response = self.client.get(reverse("news:tags_index"))
        tags_in_context = response.context["tags"]

        # Extract tag names that are shown
        shown_tag_names = [t["tag"].name for t in tags_in_context]

        # Assert that only tags with 3+ articles are shown
        self.assertIn("Three Articles", shown_tag_names)
        self.assertIn("Four Articles", shown_tag_names)

        # Assert that tags with 0, 1, or 2 articles are NOT shown
        self.assertNotIn("Zero Articles", shown_tag_names)
        self.assertNotIn("One Article", shown_tag_names)
        self.assertNotIn("Two Articles", shown_tag_names)

        # Verify exact counts
        self.assertEqual(len(tags_in_context), 2)

        # Verify the article counts are correct
        tag_counts = {t["tag"].name: t["article_count"] for t in tags_in_context}
        self.assertEqual(tag_counts["Three Articles"], 3)
        self.assertEqual(tag_counts["Four Articles"], 4)
