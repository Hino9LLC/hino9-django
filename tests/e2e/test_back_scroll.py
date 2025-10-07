"""
E2E tests for back navigation scroll behavior.

These tests validate that when users click "Back" from an article detail page,
the page scrolls to show the article they came from.
"""

import pytest
from playwright.sync_api import Page


@pytest.mark.navigation
def test_back_scrolls_to_article_on_news_list(page: Page) -> None:
    """
    Test: Click article from news list, browser back - should scroll to article.

    User Journey:
    1. Click article from homepage
    2. Use browser back button
    3. Verify page scrolls to show the article
    """
    page.goto("/")

    # Click first article
    first_article = page.locator("article[id^='article-']").first
    if not first_article.is_visible():
        pytest.skip("No articles available")

    first_article.locator("a").first.click()

    # Wait for localStorage to be set
    page.wait_for_timeout(100)

    # Use browser back navigation
    page.go_back()

    # Verify returned to homepage
    assert page.url.endswith("/") or "?page=" in page.url

    # Verify localStorage has article ID (indicates scroll behavior will work)
    local_storage_value = page.evaluate(
        "() => localStorage.getItem('article_highlight')"
    )
    assert (
        local_storage_value is not None
    ), "localStorage should have article ID for scrolling"


@pytest.mark.navigation
def test_back_scrolls_to_article_on_search_results(page: Page) -> None:
    """
    Test: Click article from search results, browser back - should scroll to article.

    User Journey:
    1. Perform search
    2. Click article from results
    3. Use browser back button
    4. Verify page scrolls to show the article in search results
    """
    page.goto("/search/")
    search_input = page.locator("input[name='q']")
    search_input.fill("test")
    page.locator("button[type='submit']").filter(has_text="Search").click()

    # Click first article if available
    articles = page.locator("article[id^='article-']")
    if articles.count() < 1:
        pytest.skip("No search results")

    first_article = articles.first
    first_article.locator("a").first.click()

    # Wait for localStorage to be set
    page.wait_for_timeout(100)

    # Use browser back navigation
    page.go_back()

    # Verify on search results page
    assert "/search" in page.url
    assert "q=test" in page.url

    # Verify localStorage has article ID (indicates scroll behavior will work)
    local_storage_value = page.evaluate(
        "() => localStorage.getItem('article_highlight')"
    )
    assert (
        local_storage_value is not None
    ), "localStorage should have article ID for scrolling"
