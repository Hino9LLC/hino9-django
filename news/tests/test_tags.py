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

        # Mock get_news_count to return different counts for different tags
        def mock_get_news_count(self: Tag) -> int:
            count_map = {
                "Machine Learning": 3,  # Should show (> 2)
                "Artificial Intelligence": 2,  # Should be filtered (= 2)
                "Deep Learning": 1,  # Should be filtered (< 2)
                "Python": 0,  # Should be filtered (= 0)
            }
            return count_map.get(self.name, 0)

        # Patch the method on all Tag instances
        with patch.object(Tag, "get_news_count", mock_get_news_count):
            # Make request to tags_index view
            response = self.client.get(reverse("news:tags_index"))

            # Assert response is successful
            self.assertEqual(response.status_code, 200)

            # Assert context has tags
            self.assertIn("tags", response.context)
            tags_in_context = response.context["tags"]

            # Should only have Machine Learning tag (3 articles > 2)
            # AI, Deep Learning, and Python should be filtered out
            self.assertEqual(len(tags_in_context), 1)
            self.assertEqual(tags_in_context[0]["tag"].name, "Machine Learning")
            self.assertEqual(tags_in_context[0]["article_count"], 3)
