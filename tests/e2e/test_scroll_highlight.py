"""
E2E tests for scroll-and-highlight functionality on back navigation.

These tests validate that when users click "Back" from an article detail page,
the page scrolls to the correct article card and applies a temporary highlight
effect for visual feedback.

Contexts tested:
- News list (homepage) with and without pagination
- Search results with various search types
- Tag detail pages with pagination
"""

import pytest
from playwright.sync_api import Page, expect


@pytest.mark.navigation
def test_news_list_scroll_highlight_page_1_third_article(page: Page) -> None:
    """
    Test: Click 3rd article on page 1, then back - should scroll and highlight.

    User Journey:
    1. Visit homepage (page 1)
    2. Click on 3rd article in the list
    3. Click "Back to News List"
    4. Verify page scrolls to 3rd article
    5. Verify article gets temporary highlight effect
    """
    # Navigate to homepage
    page.goto("/")

    # Get the 3rd article's ID for later verification
    articles = page.locator("article[id^='article-']")
    if articles.count() < 3:
        pytest.skip("Not enough articles for this test")

    third_article = articles.nth(2)
    article_id = third_article.get_attribute("id")

    # Click on the 3rd article's link
    third_article.locator("a").first.click()

    # Verify we're on article detail page
    expect(page.locator("h1")).to_be_visible()

    # Click back link
    back_link = page.locator("a").filter(has_text="Back")
    back_link.first.click()

    # Verify returned to homepage
    assert page.url.endswith("/") or "?page=" in page.url

    # Wait for scroll animation to complete (100ms delay + smooth scroll time)
    page.wait_for_timeout(500)

    # Verify the article is scrolled into view (check if element is in viewport)
    is_in_viewport = third_article.evaluate(
        """(element) => {
        const rect = element.getBoundingClientRect();
        return (
            rect.top >= 0 &&
            rect.bottom <= window.innerHeight
        );
    }"""
    )
    assert is_in_viewport, f"Article {article_id} should be scrolled into viewport"

    # Verify highlight effect is applied (box-shadow should be present)
    box_shadow = third_article.evaluate("(el) => window.getComputedStyle(el).boxShadow")
    # Should have the blue highlight shadow (not 'none')
    assert (
        box_shadow != "none"
    ), f"Article {article_id} should have highlight box-shadow"

    # Wait a bit and verify highlight is removed (after 2 second animation)
    page.wait_for_timeout(2500)
    box_shadow_after = third_article.evaluate(
        "(el) => window.getComputedStyle(el).boxShadow"
    )
    # After animation, should return to default (empty or none)
    assert (
        box_shadow_after == "none" or box_shadow_after == ""
    ), "Highlight should be removed after animation"


@pytest.mark.navigation
def test_news_list_scroll_highlight_page_2_third_article(page: Page) -> None:
    """
    Test: Click 3rd article on page 2, then back - should return to page 2 with scroll/highlight.

    User Journey:
    1. Navigate to page 2
    2. Click 3rd article
    3. Click "Back to News List"
    4. Verify returned to page 2
    5. Verify scrolls to 3rd article with highlight
    """
    # Navigate to homepage page 2
    page.goto("/?page=2")

    # Check if page 2 exists
    if "page=2" not in page.url:
        pytest.skip("Page 2 doesn't exist (not enough articles)")

    # Get the 3rd article
    articles = page.locator("article[id^='article-']")
    if articles.count() < 3:
        pytest.skip("Not enough articles on page 2")

    third_article = articles.nth(2)
    article_id = third_article.get_attribute("id")

    # Click on the 3rd article
    third_article.locator("a").first.click()

    # Click back
    back_link = page.locator("a").filter(has_text="Back")
    back_link.first.click()

    # Verify returned to page 2
    assert "page=2" in page.url, "Should return to page 2"

    # Wait for scroll animation
    page.wait_for_timeout(500)

    # Verify scroll and highlight
    is_in_viewport = third_article.evaluate(
        """(element) => {
        const rect = element.getBoundingClientRect();
        return rect.top >= 0 && rect.bottom <= window.innerHeight;
    }"""
    )
    assert is_in_viewport, f"Article {article_id} should be in viewport on page 2"

    # Check for highlight
    box_shadow = third_article.evaluate("(el) => window.getComputedStyle(el).boxShadow")
    assert box_shadow != "none", "Should have highlight box-shadow"


@pytest.mark.navigation
def test_news_list_scroll_highlight_removes_param(page: Page) -> None:
    """
    Test: After highlight animation, verify highlight_article param is removed from URL.

    User Journey:
    1. Click article from news list
    2. Click back (URL has highlight_article param)
    3. Wait for highlight animation
    4. Verify highlight_article param is removed from URL
    """
    page.goto("/")

    # Click first article
    first_article = page.locator("article[id^='article-']").first
    if not first_article.is_visible():
        pytest.skip("No articles available")

    first_article.locator("a").first.click()

    # Click back
    back_link = page.locator("a").filter(has_text="Back")
    back_link.first.click()

    # Wait for highlight to appear (briefly)
    page.wait_for_timeout(200)

    # Wait for highlight animation and cleanup (2+ seconds)
    page.wait_for_timeout(2500)

    # Verify highlight_article param is removed
    final_url = page.url
    assert (
        "highlight_article" not in final_url
    ), "highlight_article param should be removed after animation"


@pytest.mark.navigation
def test_news_list_no_scroll_when_no_highlight_param(page: Page) -> None:
    """
    Test: Direct navigation to news list without highlight param - no scroll/highlight.

    User Journey:
    1. Navigate directly to news list (no highlight_article param)
    2. Verify normal page load
    3. Verify no highlight effect applied
    """
    page.goto("/")

    # Verify no highlight_article in URL
    assert "highlight_article" not in page.url

    # Check that no articles have highlight effect
    articles = page.locator("article[id^='article-']")
    if articles.count() > 0:
        first_article = articles.first
        box_shadow = first_article.evaluate(
            "(el) => window.getComputedStyle(el).boxShadow"
        )
        # Should not have highlight initially
        assert (
            box_shadow == "none" or "rgba(99, 102, 241" not in box_shadow
        ), "Should not have highlight on direct navigation"


@pytest.mark.search
def test_search_scroll_highlight_third_result(page: Page) -> None:
    """
    Test: Search, click 3rd result, back - should scroll and highlight on search results.

    User Journey:
    1. Perform search for "AI"
    2. Click 3rd search result
    3. Click "Back to Search Results"
    4. Verify scroll to 3rd result with highlight
    5. Verify search params preserved (q, type)
    """
    # Navigate to search page and search
    page.goto("/search/")
    search_input = page.locator("input[name='q']")
    search_input.fill("AI")

    # Submit search
    page.locator("button[type='submit']").filter(has_text="Search").click()

    # Wait for results
    page.wait_for_url("**/search?q=AI*")

    # Get 3rd result if available
    articles = page.locator("article[id^='article-']")
    if articles.count() < 3:
        pytest.skip("Not enough search results for this test")

    third_result = articles.nth(2)
    article_id = third_result.get_attribute("id")

    # Click on 3rd result
    third_result.locator("a").first.click()

    # Click back to search results
    back_link = page.locator("a").filter(has_text="Back to Search Results")
    back_link.click()

    # Verify on search results page with query preserved
    assert "/search" in page.url
    assert "q=AI" in page.url

    # Wait for scroll animation
    page.wait_for_timeout(500)

    # Verify scroll and highlight
    is_in_viewport = third_result.evaluate(
        """(element) => {
        const rect = element.getBoundingClientRect();
        return rect.top >= 0 && rect.bottom <= window.innerHeight;
    }"""
    )
    assert is_in_viewport, f"Search result {article_id} should be in viewport"

    # Check for highlight effect
    box_shadow = third_result.evaluate("(el) => window.getComputedStyle(el).boxShadow")
    assert box_shadow != "none", "Search result should have highlight"


@pytest.mark.search
def test_search_scroll_highlight_page_2(page: Page) -> None:
    """
    Test: Search with pagination, click article on page 2, verify scroll/highlight.

    User Journey:
    1. Search for common term to get multiple pages
    2. Navigate to page 2 of results
    3. Click article on page 2
    4. Click back
    5. Verify returned to page 2 with scroll/highlight
    """
    # Search for a common term
    page.goto("/search/")
    search_input = page.locator("input[name='q']")
    search_input.fill("technology")
    page.locator("button[type='submit']").filter(has_text="Search").click()

    # Check if there's a page 2
    next_button = page.locator("a").filter(has_text="Next")
    if not next_button.is_visible():
        pytest.skip("Not enough results for pagination")

    # Go to page 2
    next_button.click()
    page.wait_for_timeout(500)

    if "page=2" not in page.url:
        pytest.skip("Page 2 not available")

    # Click first article on page 2
    articles = page.locator("article[id^='article-']")
    if articles.count() < 1:
        pytest.skip("No articles on page 2")

    first_article = articles.first
    first_article.locator("a").first.click()

    # Click back
    back_link = page.locator("a").filter(has_text="Back")
    back_link.first.click()

    # Verify on page 2 of search results
    assert "page=2" in page.url or "from_page=2" in page.url
    assert "q=technology" in page.url

    # Wait for scroll animation
    page.wait_for_timeout(500)

    # Verify highlight
    box_shadow = first_article.evaluate("(el) => window.getComputedStyle(el).boxShadow")
    assert box_shadow != "none", "Article on search page 2 should have highlight"


@pytest.mark.search
def test_search_scroll_highlight_preserves_search_type(page: Page) -> None:
    """
    Test: Search with specific type (vector/text), verify type preserved on back navigation.

    User Journey:
    1. Perform vector search
    2. Click article
    3. Click back
    4. Verify search type preserved in URL
    """
    # Navigate to search and perform vector search
    page.goto("/search/?q=machine+learning&type=vector")

    # Wait for results
    page.wait_for_timeout(500)

    # Click first article if available
    articles = page.locator("article[id^='article-']")
    if articles.count() < 1:
        pytest.skip("No search results for vector search")

    first_article = articles.first
    first_article.locator("a").first.click()

    # Click back
    back_link = page.locator("a").filter(has_text="Back")
    back_link.first.click()

    # Verify search params preserved
    assert "q=machine" in page.url or "q=machine+learning" in page.url
    assert "type=vector" in page.url


@pytest.mark.search
def test_search_highlight_removes_param_keeps_search(page: Page) -> None:
    """
    Test: After highlight animation, verify highlight_article removed but search params remain.

    User Journey:
    1. Search and click article
    2. Click back (highlight_article param present)
    3. Wait for animation
    4. Verify highlight_article removed but q and type remain
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

    # Click back
    back_link = page.locator("a").filter(has_text="Back")
    back_link.first.click()

    # Wait for highlight cleanup
    page.wait_for_timeout(2500)

    # Verify search params still present
    final_url = page.url
    assert "q=test" in final_url, "Search query should be preserved"

    # Verify highlight_article removed
    assert (
        "highlight_article" not in final_url
    ), "highlight_article should be removed after animation"


@pytest.mark.navigation
def test_tag_scroll_highlight_third_article(page: Page) -> None:
    """
    Test: Navigate to tag page, click 3rd article, back - should scroll and highlight.

    User Journey:
    1. Navigate to a tag detail page
    2. Click 3rd article
    3. Click "Back to [Tag] Articles"
    4. Verify scroll to 3rd article with highlight
    """
    # Navigate to tags index
    page.goto("/tags/")

    # Click first tag
    first_tag_link = page.locator("a[href*='/tag/']").first
    if not first_tag_link.is_visible():
        pytest.skip("No tags available")

    first_tag_link.click()

    # Verify on tag detail page
    assert "/tag/" in page.url

    # Get 3rd article if available
    articles = page.locator("article[id^='article-']")
    if articles.count() < 3:
        pytest.skip("Not enough articles for this tag")

    third_article = articles.nth(2)
    article_id = third_article.get_attribute("id")

    # Click 3rd article
    third_article.locator("a").first.click()

    # Click back
    back_link = page.locator("a").filter(has_text="Back")
    back_link.first.click()

    # Verify on tag page
    assert "/tag/" in page.url

    # Wait for scroll animation
    page.wait_for_timeout(500)

    # Verify scroll and highlight
    is_in_viewport = third_article.evaluate(
        """(element) => {
        const rect = element.getBoundingClientRect();
        return rect.top >= 0 && rect.bottom <= window.innerHeight;
    }"""
    )
    assert is_in_viewport, f"Tag article {article_id} should be in viewport"

    # Check highlight
    box_shadow = third_article.evaluate("(el) => window.getComputedStyle(el).boxShadow")
    assert box_shadow != "none", "Tag article should have highlight"


@pytest.mark.navigation
def test_tag_scroll_highlight_page_2(page: Page) -> None:
    """
    Test: Tag page with pagination, click article on page 2, verify scroll/highlight.

    User Journey:
    1. Navigate to tag with multiple pages
    2. Go to page 2
    3. Click article
    4. Click back
    5. Verify returned to page 2 with scroll/highlight
    """
    # Navigate to tags and find a tag
    page.goto("/tags/")

    first_tag_link = page.locator("a[href*='/tag/']").first
    if not first_tag_link.is_visible():
        pytest.skip("No tags available")

    first_tag_link.click()

    # Check if page 2 exists
    next_button = page.locator("a").filter(has_text="Next")
    if not next_button.is_visible():
        pytest.skip("Tag doesn't have page 2")

    # Go to page 2
    next_button.click()
    page.wait_for_timeout(500)

    if "page=2" not in page.url:
        pytest.skip("Page 2 not available for this tag")

    # Click first article on page 2
    articles = page.locator("article[id^='article-']")
    if articles.count() < 1:
        pytest.skip("No articles on page 2")

    first_article = articles.first
    first_article.locator("a").first.click()

    # Click back
    back_link = page.locator("a").filter(has_text="Back")
    back_link.first.click()

    # Verify on page 2
    assert "page=2" in page.url or "from_page=2" in page.url

    # Verify highlight
    box_shadow = first_article.evaluate("(el) => window.getComputedStyle(el).boxShadow")
    assert box_shadow != "none", "Tag article on page 2 should have highlight"


@pytest.mark.navigation
def test_tag_from_news_list_preserves_context(page: Page) -> None:
    """
    Test: Click tag from news list page 2, then click article - verify context preservation.

    User Journey:
    1. Navigate to news list page 2
    2. Click a tag from an article
    3. Click an article on tag page
    4. Verify back navigation context is preserved
    """
    # Navigate to page 2
    page.goto("/?page=2")

    if "page=2" not in page.url:
        pytest.skip("Page 2 doesn't exist")

    # Find and click a tag from an article
    tag_link = page.locator("a[href*='/tag/']").first
    if not tag_link.is_visible():
        pytest.skip("No tags on page 2")

    tag_link.click()

    # Now on tag page - click an article
    articles = page.locator("article[id^='article-']")
    if articles.count() < 1:
        pytest.skip("No articles for this tag")

    first_article = articles.first
    first_article.locator("a").first.click()

    # Verify article detail page has proper context
    # The back link should exist
    back_link = page.locator("a").filter(has_text="Back")
    expect(back_link.first).to_be_visible()


@pytest.mark.navigation
def test_tag_highlight_visual_effect(page: Page) -> None:
    """
    Test: Verify the visual highlight effect timing and appearance.

    User Journey:
    1. Navigate to tag page
    2. Click article and back
    3. Verify highlight appears immediately
    4. Verify highlight duration is ~2 seconds
    """
    # Navigate to a tag
    page.goto("/tags/")

    first_tag_link = page.locator("a[href*='/tag/']").first
    if not first_tag_link.is_visible():
        pytest.skip("No tags available")

    first_tag_link.click()

    # Click first article
    articles = page.locator("article[id^='article-']")
    if articles.count() < 1:
        pytest.skip("No articles for this tag")

    first_article = articles.first
    first_article.locator("a").first.click()

    # Click back
    back_link = page.locator("a").filter(has_text="Back")
    back_link.first.click()

    # Immediately check for highlight (should appear within 200ms)
    page.wait_for_timeout(200)
    box_shadow_initial = first_article.evaluate(
        "(el) => window.getComputedStyle(el).boxShadow"
    )
    assert box_shadow_initial != "none", "Highlight should appear immediately"
    assert (
        "rgba(99, 102, 241" in box_shadow_initial
        or "rgb(99, 102, 241" in box_shadow_initial
    ), "Should have blue highlight color"

    # Wait for animation duration (2 seconds) plus buffer
    page.wait_for_timeout(2500)

    # Verify highlight is removed
    box_shadow_final = first_article.evaluate(
        "(el) => window.getComputedStyle(el).boxShadow"
    )
    assert (
        box_shadow_final == "none" or box_shadow_final == ""
    ), "Highlight should be removed after 2 seconds"
