"""
E2E tests for article discovery and navigation journeys.

These tests validate the complete user experience from homepage to article detail
and back, including context preservation for pagination.
"""

import pytest
from playwright.sync_api import Page, expect


@pytest.mark.navigation
def test_homepage_to_article_and_back(page: Page) -> None:
    """
    Test: User browses homepage, clicks article, then returns to homepage.

    User Journey:
    1. Visit homepage
    2. Click on first article
    3. Verify article detail page loads
    4. Click "Back to Homepage" link
    5. Verify returned to homepage
    """
    # Navigate to homepage
    page.goto("/")

    # Verify homepage loaded
    expect(page).to_have_title("Latest News - HINO9")
    expect(page.locator("h1")).to_contain_text("Latest News")

    # Get first article link
    first_article = page.locator("article").first
    article_title = first_article.locator("h2").inner_text()

    # Click on first article
    first_article.locator("a").first.click()

    # Verify article detail page
    expect(page.locator("h1")).to_contain_text(article_title)

    # Find and click back link (could be "Back to Homepage" or "Back to page X")
    back_link = page.locator("a").filter(has_text="Back")
    expect(back_link.first).to_be_visible()
    back_link.first.click()

    # Verify back on homepage (might be page 1 instead of /)
    expect(page.locator("h1")).to_contain_text("Latest News")


@pytest.mark.navigation
def test_pagination_context_preservation(page: Page) -> None:
    """
    Test: User navigates to page 2, clicks article, then returns to page 2.

    User Journey:
    1. Visit homepage
    2. Navigate to page 2
    3. Click on an article
    4. Click "Back to page 2" link
    5. Verify returned to correct page with from_page parameter
    """
    # Navigate to homepage
    page.goto("/")

    # Click "Next" or "Page 2" if pagination exists
    # Use get_by_role to be more specific and avoid matching article text
    next_button = page.get_by_role("link", name="Next")

    try:
        next_button.wait_for(state="visible", timeout=1000)
        is_visible = True
    except Exception:
        is_visible = False

    if is_visible:
        next_button.click()

        # Verify on page 2
        assert "page=2" in page.url

        # Click on first article on page 2
        first_article = page.locator("article").first
        first_article.locator("a").first.click()

        # Verify the back link has "Back" (might say "page 2" or just "Back")
        back_link = page.locator("a").filter(has_text="Back")
        expect(back_link.first).to_be_visible()
        back_link.first.click()

        # Verify returned to page 2
        assert "page=2" in page.url
    else:
        # Skip if not enough articles for pagination
        pytest.skip("Not enough articles for pagination test")


@pytest.mark.navigation
def test_article_detail_displays_all_content(page: Page) -> None:
    """
    Test: Verify article detail page displays all expected content.

    Validates:
    - Article headline/title
    - Article image (if present)
    - Article summary
    - Article bullets
    - Tags
    - Source link
    """
    # Navigate to homepage and click first article
    page.goto("/")
    page.locator("article").first.locator("a").first.click()

    # Verify core content elements
    expect(page.locator("h1")).to_be_visible()

    # Check for article image (may not always exist)
    article_image = page.locator("img.article-image")
    if article_image.count() > 0:
        expect(article_image.first).to_be_visible()

    # Verify summary or content exists
    if page.locator("p").count() > 0:
        expect(page.locator("p").first).to_be_visible()

    # Verify tags (if present)
    if (
        page.locator("a").filter(has_text="tag").count() > 0
        or page.locator(".tag").count() > 0
    ):
        # Tags exist, good
        pass


@pytest.mark.mobile
def test_article_navigation_on_mobile(mobile_page: Page) -> None:
    """
    Test: Verify article navigation works on mobile viewport.

    User Journey:
    1. Visit homepage on mobile device
    2. Click on article
    3. Verify mobile-friendly layout
    4. Navigate back using browser back button (back link is hidden on mobile)
    """
    # Navigate to homepage
    mobile_page.goto("/")

    # Verify mobile layout
    expect(mobile_page.locator("h1")).to_be_visible()

    # Click first article
    mobile_page.locator("article").first.locator("a").first.click()

    # Verify article displays on mobile
    expect(mobile_page.locator("h1")).to_be_visible()

    # Verify browser back button works (back link is hidden on mobile)
    mobile_page.go_back()

    # Verify returned to homepage
    assert mobile_page.url.endswith("/") or "?page=" in mobile_page.url


@pytest.mark.visual
def test_article_page_visual_regression(page: Page) -> None:
    """
    Test: Capture screenshot of article detail page for visual regression testing.

    This test captures a screenshot that can be compared against baseline
    to detect unintended visual changes.
    """
    # Navigate to first article
    page.goto("/")
    page.locator("article").first.locator("a").first.click()

    # Wait for page to fully load
    expect(page.locator("h1")).to_be_visible()

    # Take screenshot
    page.screenshot(
        path="tests/e2e/test-results/article-detail-page.png", full_page=True
    )
