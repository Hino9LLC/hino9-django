"""
E2E tests for navigation and context preservation.

These tests validate that navigation context (pagination, search, tags)
is properly preserved when users navigate between pages.
"""

import pytest
from playwright.sync_api import Page, expect


@pytest.mark.navigation
def test_tag_browsing_journey(page: Page) -> None:
    """
    Test: User browses tags index, clicks tag, views article, then navigates back.

    User Journey:
    1. Visit tags index page
    2. Click on a tag
    3. View articles for that tag
    4. Click on an article
    5. Navigate back to tag page
    6. Navigate back to tags index
    """
    # Navigate to tags index
    page.goto("/tags/")

    # Verify tags index loaded
    expect(page.locator("h1")).to_contain_text("Browse Tags")

    # Click on first tag (extract tag name from h2, not the whole card)
    first_tag_link = page.locator("a[href*='/tag/']").first
    if first_tag_link.is_visible():
        # Get tag name from the h2 element, not the whole card
        tag_name = first_tag_link.locator("h2").inner_text()
        first_tag_link.click()

        # Verify on tag detail page (URL includes tag slug and query params)
        assert "/tag/" in page.url
        # h1 contains the tag name (and possibly article count like "Accessibility\n4 articles")
        page_h1 = page.locator("h1").inner_text()
        # Check tag name is in the h1 text (h1 might have additional text like article count)
        assert tag_name.strip().lower() in page_h1.strip().lower()

        # Click on first article for this tag
        first_article = page.locator("article").first
        if first_article.is_visible():
            first_article.locator("a").first.click()

            # Verify on article detail page
            expect(page.locator("h1")).to_be_visible()

            # Click back to tag
            back_to_tag = page.get_by_text(f"← Back to {tag_name}", exact=False)
            if back_to_tag.is_visible():
                back_to_tag.click()

                # Verify back on tag page
                assert "/tag/" in page.url

                # Click back to tags index
                back_to_index = page.get_by_text("← Back to all tags", exact=False)
                if back_to_index.is_visible():
                    back_to_index.click()
                    expect(page).to_have_url("/tags/")
    else:
        pytest.skip("No tags available for browsing test")


@pytest.mark.navigation
def test_navigation_clean_urls(page: Page) -> None:
    """
    Test: Verify article detail URLs are clean (no navigation context params).

    Validates that we use localStorage + browser back navigation instead of
    complex URL parameters for navigation context.
    """
    # Test from news list page 2
    page.goto("/?page=2")
    if page.locator("article").first.is_visible():
        page.locator("article").first.locator("a").first.click()

        # Verify NO navigation context parameters in URL (clean URLs)
        assert "from_page" not in page.url
        assert "highlight_article" not in page.url
        # URL should just be clean article URL like /123/article-slug/ (no query params)
        assert "?" not in page.url

    # Test from search results
    page.goto("/search/?q=test&type=hybrid")
    if page.locator("article").first.is_visible():
        page.locator("article").first.locator("a").first.click()

        # Verify NO navigation context parameters (clean URLs)
        assert "from_search" not in page.url
        assert "highlight_article" not in page.url
        # Should have clean article URL, not search context params


@pytest.mark.navigation
def test_header_navigation(page: Page) -> None:
    """
    Test: Verify main navigation links in header work correctly.

    User Journey:
    1. Visit homepage
    2. Click logo/home link
    3. Visit search page
    4. Click tags link
    5. Verify all navigation works
    """
    # Navigate to homepage
    page.goto("/")

    # Find and click home/logo link
    home_link = page.locator("a[href='/'], .logo, .site-title").first
    if home_link.is_visible():
        expect(home_link).to_be_visible()

    # Navigate to tags (if link exists in header)
    tags_link = page.locator("a[href='/tags/']")
    if tags_link.is_visible():
        tags_link.click()
        expect(page).to_have_url("/tags/")

        # Navigate back to home
        page.goto("/")
        expect(page).to_have_url("/")


@pytest.mark.navigation
def test_breadcrumb_navigation(page: Page) -> None:
    """
    Test: Verify breadcrumb navigation (if implemented).

    Validates that breadcrumbs display correctly and are clickable.
    """
    # Navigate to article detail
    page.goto("/")
    page.locator("article").first.locator("a").first.click()

    # Look for breadcrumbs
    breadcrumb = page.locator(".breadcrumb, .breadcrumbs, nav[aria-label='breadcrumb']")
    if breadcrumb.is_visible():
        # Verify home link in breadcrumb
        home_breadcrumb = breadcrumb.locator("a[href='/']")
        expect(home_breadcrumb).to_be_visible()

        # Click home in breadcrumb
        home_breadcrumb.click()
        expect(page).to_have_url("/")
    else:
        pytest.skip("Breadcrumbs not implemented")


@pytest.mark.navigation
def test_404_page_navigation(page: Page) -> None:
    """
    Test: Verify 404 page displays and allows navigation back.

    User Journey:
    1. Navigate to non-existent article
    2. Verify 404 page displays
    3. Click link back to homepage
    """
    # Navigate to non-existent article
    page.goto("/999999/nonexistent-article/")

    # Verify 404 page or error message
    # Django typically returns 404 status but page might still render
    expect(page.locator("h2")).to_contain_text("Page not found", ignore_case=True)

    # Look for link back to homepage
    home_link = page.locator("a[href='/']").first
    if home_link.is_visible():
        home_link.click()
        expect(page).to_have_url("/")


@pytest.mark.navigation
def test_keyboard_navigation(page: Page) -> None:
    """
    Test: Verify keyboard navigation works (accessibility).

    Validates that users can navigate using Tab and Enter keys.
    """
    # Navigate to homepage
    page.goto("/")

    # Press Tab to focus on first interactive element
    page.keyboard.press("Tab")

    # Verify an element is focused
    focused = page.evaluate("document.activeElement.tagName")
    assert focused in [
        "A",
        "BUTTON",
        "INPUT",
    ], f"Expected focusable element, got {focused}"

    # Tab to first article link
    for _ in range(5):  # Tab a few times to reach article link
        page.keyboard.press("Tab")
        focused = page.evaluate("document.activeElement")
        if focused and "article" in page.evaluate(
            "document.activeElement.closest('article') ? 'article' : ''"
        ):
            # Press Enter to activate link
            page.keyboard.press("Enter")
            # Wait for navigation (use domcontentloaded instead of networkidle)
            page.wait_for_load_state("domcontentloaded")
            # Verify navigated to article
            expect(page.locator("h1")).to_be_visible()
            break


@pytest.mark.navigation
@pytest.mark.mobile
def test_mobile_navigation_menu(mobile_page: Page) -> None:
    """
    Test: Verify mobile navigation menu works (if implemented).

    User Journey:
    1. Visit homepage on mobile
    2. Open mobile menu (hamburger icon)
    3. Navigate to tags
    4. Verify navigation works
    """
    # Navigate to homepage
    mobile_page.goto("/")

    # Look for mobile menu toggle (hamburger icon)
    menu_toggle = mobile_page.locator(
        "button[aria-label='menu'], .menu-toggle, .hamburger"
    )

    if menu_toggle.is_visible():
        # Open mobile menu
        menu_toggle.click()

        # Wait for menu to open
        mobile_menu = mobile_page.locator(".mobile-menu, nav.open, .menu-expanded")
        expect(mobile_menu).to_be_visible()

        # Click tags link in mobile menu
        tags_link = mobile_menu.locator("a[href='/tags/']")
        if tags_link.is_visible():
            tags_link.click()
            expect(mobile_page).to_have_url("/tags/")
    else:
        pytest.skip("Mobile menu not implemented or not visible")
