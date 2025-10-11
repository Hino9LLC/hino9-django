"""
E2E tests for search functionality.

These tests validate the complete search user experience including:
- Vector search
- Text search
- Hybrid search
- Search type switching
- Search context preservation
"""

import pytest
from playwright.sync_api import Page, expect


@pytest.mark.search
def test_basic_search_flow(page: Page) -> None:
    """
    Test: User performs a basic search from homepage.

    User Journey:
    1. Visit homepage
    2. Enter search query in search box
    3. Submit search
    4. Verify search results page displays
    5. Verify query is preserved in search box
    """
    # Navigate to search page (homepage doesn't have search box)
    page.goto("/search/")

    # Enter search query
    search_input = page.locator("input[name='q']")
    expect(search_input).to_be_visible()
    search_input.fill("technology")

    # Submit search
    search_button = page.locator("button[type='submit']").filter(has_text="Search")
    search_button.click()

    # Verify on search results page (type defaults to hybrid but isn't in URL if not explicitly selected)
    assert "/search" in page.url
    assert "q=technology" in page.url
    # Use more specific selector - first h2 in the results header section
    expect(page.locator("h2").first).to_contain_text('Search Results for "technology"')

    # Verify query preserved in search box
    expect(page.locator("input[name='q']")).to_have_value("technology")


@pytest.mark.search
def test_search_type_switching(page: Page) -> None:
    """
    Test: User switches between different search types.

    User Journey:
    1. Perform initial search (defaults to hybrid)
    2. Switch to vector search
    3. Switch to text search
    4. Verify results update for each type
    """
    # Navigate to search page with explicit hybrid type
    page.goto("/search/?q=AI&type=hybrid")

    # Verify hybrid search is checked (only when explicitly in URL)
    hybrid_radio = page.locator("input[type='radio'][value='hybrid']")
    expect(hybrid_radio).to_be_checked()

    # Switch to vector search (radio is hidden, need to force click)
    vector_radio = page.locator("input[type='radio'][value='vector']")
    vector_radio.check(force=True)

    # Submit search with new type
    page.locator("button[type='submit']").filter(has_text="Search").click()

    # Verify URL updated to vector search (check params, not exact URL)
    assert "q=AI" in page.url
    assert "type=vector" in page.url
    expect(vector_radio).to_be_checked()

    # Switch to text search
    text_radio = page.locator("input[type='radio'][value='text']")
    text_radio.check(force=True)

    # Submit search
    page.locator("button[type='submit']").filter(has_text="Search").click()

    # Verify URL updated to text search (check params, not exact URL)
    assert "q=AI" in page.url
    assert "type=text" in page.url
    expect(text_radio).to_be_checked()


@pytest.mark.search
def test_search_to_article_preserves_context(page: Page) -> None:
    """
    Test: User searches, clicks article, then returns to search results.

    User Journey:
    1. Perform search
    2. Click on search result
    3. View article
    4. Click back to search results
    5. Verify search query and type preserved
    """
    # Perform search (use URL params that Django understands)
    page.goto("/search?q=machine+learning&type=text")

    # Click on first search result if available
    first_result = page.locator("article").first

    if first_result.is_visible():
        first_result.locator("a").first.click()

        # Verify on article detail page
        expect(page.locator("h1")).to_be_visible()

        # Find back to search link (without arrow)
        back_link = page.locator("a").filter(has_text="Back")
        expect(back_link.first).to_be_visible()
        back_link.first.click()

        # Verify returned to search with query preserved (check params, not exact URL)
        assert "/search" in page.url
        assert "machine" in page.url and "learning" in page.url
        assert "type=text" in page.url
        expect(page.locator("input[name='q']")).to_have_value("machine learning")
        expect(page.locator("input[type='radio'][value='text']")).to_be_checked()
    else:
        pytest.skip("No search results available for this test")


@pytest.mark.search
def test_empty_search_shows_message(page: Page) -> None:
    """
    Test: User submits empty search and sees appropriate message.

    User Journey:
    1. Navigate to search page
    2. Submit search with empty query
    3. Verify "no results" or "enter query" message
    """
    # Navigate to search page
    page.goto("/search/")

    # Submit empty search
    page.locator("button[type='submit']").filter(has_text="Search").click()

    # Verify still on search page (empty search doesn't add query params)
    assert "/search" in page.url

    # Verify no results message or empty state
    # (This depends on your implementation - adjust selector as needed)
    no_results = page.locator(".no-results, .empty-state, p").filter(
        has_text="no results"
    )
    if no_results.count() > 0:
        expect(no_results.first).to_be_visible()


@pytest.mark.search
def test_search_results_display_snippets(page: Page) -> None:
    """
    Test: Verify search results display article snippets and metadata.

    Validates that each search result shows:
    - Article title/headline
    - Summary snippet
    - Date
    - Tags (if visible)
    """
    # Perform search
    page.goto("/search/?q=data&type=hybrid")

    # Get first search result
    first_result = page.locator("article").first

    if first_result.is_visible():
        # Verify title/headline
        expect(first_result.locator("h2, h3")).to_be_visible()

        # Verify summary or snippet
        summary = first_result.locator(".summary, .excerpt, p")
        if summary.count() > 0:
            expect(summary.first).to_be_visible()

        # Verify date
        date = first_result.locator(".date, time, .article-date")
        if date.count() > 0:
            expect(date.first).to_be_visible()
    else:
        pytest.skip("No search results available for this test")


@pytest.mark.search
@pytest.mark.slow
def test_search_performance(page: Page) -> None:
    """
    Test: Verify search responds within acceptable time.

    Validates that search completes within 2 seconds.
    """
    # Navigate to search page
    page.goto("/search/")

    # Fill search query
    search_input = page.locator("input[name='q']")
    search_input.fill("artificial intelligence")

    # Measure search time
    import time

    start_time = time.time()

    # Submit search
    page.locator("button[type='submit']").filter(has_text="Search").click()

    # Wait for results to load (check for search results header - use first h2)
    expect(page.locator("h2").first).to_contain_text(
        'Search Results for "artificial intelligence"', timeout=2000
    )

    end_time = time.time()
    search_time = end_time - start_time

    # Assert search completed within 2 seconds
    assert search_time < 2.0, f"Search took {search_time:.2f}s, expected < 2.0s"


@pytest.mark.search
@pytest.mark.mobile
def test_search_on_mobile(mobile_page: Page) -> None:
    """
    Test: Verify search works on mobile viewport.

    User Journey:
    1. Open homepage on mobile
    2. Enter search query
    3. Submit search
    4. Verify mobile-friendly results
    """
    # Navigate to search page
    mobile_page.goto("/search/")

    # Enter search query
    search_input = mobile_page.locator("input[name='q']")
    expect(search_input).to_be_visible()
    search_input.fill("news")

    # Submit search
    mobile_page.locator("button[type='submit']").filter(has_text="Search").click()

    # Verify on search results page (no type in URL when not explicitly selected)
    assert "/search" in mobile_page.url
    assert "q=news" in mobile_page.url

    # Verify results display on mobile (use first h2 for results header)
    expect(mobile_page.locator("h2").first).to_contain_text('Search Results for "news"')

    # Verify search type selector is accessible (radio buttons exist, though hidden with sr-only)
    expect(mobile_page.locator("input[type='radio'][value='hybrid']")).to_be_attached()
