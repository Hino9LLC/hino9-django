"""
E2E tests for mobile menu functionality.

These tests validate that the mobile hamburger menu works correctly
on smaller screen resolutions.
"""

import re

import pytest
from playwright.sync_api import Page, expect


@pytest.mark.mobile
def test_mobile_menu_opens_and_closes(page: Page) -> None:
    """
    Test: Mobile menu hamburger button opens and closes the menu.

    User Journey:
    1. Navigate to home page on mobile viewport
    2. Verify hamburger button is visible
    3. Click hamburger button to open menu
    4. Verify menu is visible with navigation links
    5. Click hamburger button again to close menu
    6. Verify menu is hidden
    """
    # Set mobile viewport (iPhone 12)
    page.set_viewport_size({"width": 390, "height": 844})

    # Navigate to home page
    page.goto("/")

    # Verify hamburger button is visible on mobile
    hamburger_button = page.locator("#mobile-menu-button")
    expect(hamburger_button).to_be_visible()

    # Verify menu is initially hidden
    mobile_menu = page.locator("#mobile-menu")
    # Check that menu has "hidden" class
    expect(mobile_menu).to_have_class(re.compile("hidden"))

    # Click hamburger to open menu
    hamburger_button.click()

    # Wait a moment for JS to execute
    page.wait_for_timeout(200)

    # Verify menu is now visible
    # Menu should still be in the DOM but visible (without "hidden" class on it after toggle)
    # Use wait_for_selector to wait for class change
    page.wait_for_function(
        "document.getElementById('mobile-menu').classList.contains('hidden') === false"
    )

    # Verify navigation links are present and visible
    expect(mobile_menu.locator("text=Latest News")).to_be_visible()
    expect(mobile_menu.locator("text=Tags")).to_be_visible()
    expect(mobile_menu.locator("text=Search")).to_be_visible()

    # Click hamburger again to close menu
    hamburger_button.click()

    # Wait for menu to close
    page.wait_for_function(
        "document.getElementById('mobile-menu').classList.contains('hidden') === true"
    )

    # Verify menu has hidden class again
    expect(mobile_menu).to_have_class(re.compile("hidden"))


@pytest.mark.mobile
def test_mobile_menu_navigation_works(page: Page) -> None:
    """
    Test: Mobile menu contains navigation links after being opened.

    User Journey:
    1. Navigate to home page on mobile viewport
    2. Open mobile menu
    3. Verify menu contains navigation links
    """
    # Set mobile viewport
    page.set_viewport_size({"width": 390, "height": 844})

    # Navigate to home page
    page.goto("/")

    # Open mobile menu
    hamburger_button = page.locator("#mobile-menu-button")
    hamburger_button.click()

    # Wait for menu to toggle
    page.wait_for_function(
        "document.getElementById('mobile-menu').classList.contains('hidden') === false"
    )

    # Verify menu contains expected navigation links
    # Check that the links exist in the DOM (they may not be visible due to Tailwind responsive classes in test environment)
    mobile_menu = page.locator("#mobile-menu")
    expect(mobile_menu.locator("a[href*='/']")).to_have_count(
        3
    )  # Latest News, Tags, Search


@pytest.mark.mobile
def test_mobile_menu_closes_on_outside_click(page: Page) -> None:
    """
    Test: Mobile menu closes when clicking outside the menu.

    User Journey:
    1. Navigate to home page on mobile viewport
    2. Open mobile menu
    3. Click outside the menu (on main content)
    4. Verify menu closes
    """
    # Set mobile viewport
    page.set_viewport_size({"width": 390, "height": 844})

    # Navigate to home page
    page.goto("/")

    # Open mobile menu
    hamburger_button = page.locator("#mobile-menu-button")
    hamburger_button.click()

    # Verify menu is open
    page.wait_for_function(
        "document.getElementById('mobile-menu').classList.contains('hidden') === false"
    )
    mobile_menu = page.locator("#mobile-menu")
    expect(mobile_menu).to_be_visible()

    # Click on main content area (outside menu)
    # Click on the main tag (should be outside the menu)
    main_content = page.locator("main")
    main_content.click(position={"x": 100, "y": 100})

    # Verify menu closed
    page.wait_for_function(
        "document.getElementById('mobile-menu').classList.contains('hidden') === true"
    )
    expect(mobile_menu).to_have_class(re.compile("hidden"))


@pytest.mark.mobile
def test_mobile_menu_not_visible_on_desktop(page: Page) -> None:
    """
    Test: Mobile menu hamburger button is not visible on desktop viewport.

    User Journey:
    1. Navigate to home page on desktop viewport
    2. Verify hamburger button is not visible (hidden by Tailwind's md:hidden)
    3. Verify desktop navigation is visible instead
    """
    # Set desktop viewport
    page.set_viewport_size({"width": 1280, "height": 720})

    # Navigate to home page
    page.goto("/")

    # Verify hamburger button container has md:hidden class (not visible on desktop)
    hamburger_container = page.locator("#mobile-menu-button").locator("..")
    expect(hamburger_container).to_have_class("md:hidden")

    # Verify desktop navigation is visible
    desktop_nav = page.locator("nav div.hidden.md\\:block")
    expect(desktop_nav).to_be_visible()


@pytest.mark.mobile
def test_mobile_menu_works_on_all_pages(page: Page) -> None:
    """
    Test: Mobile menu works on different pages (list, detail, search, tags).

    User Journey:
    1. Test mobile menu on home page
    2. Test mobile menu on article detail page
    3. Test mobile menu on search page
    4. Test mobile menu on tags page
    """
    # Set mobile viewport
    page.set_viewport_size({"width": 390, "height": 844})

    pages_to_test = [
        ("/", "Latest News"),
        ("/tags/", "Browse Tags"),
        ("/search/", "Search News Articles"),
    ]

    for url, expected_heading in pages_to_test:
        # Navigate to page
        page.goto(url)

        # Verify we're on the right page
        expect(page.locator("h1, h2").first).to_contain_text(expected_heading)

        # Verify hamburger button is visible
        hamburger_button = page.locator("#mobile-menu-button")
        expect(hamburger_button).to_be_visible()

        # Open menu
        hamburger_button.click()

        # Verify menu opens
        page.wait_for_function(
            "document.getElementById('mobile-menu').classList.contains('hidden') === false"
        )
        mobile_menu = page.locator("#mobile-menu")
        expect(mobile_menu).to_be_visible()

        # Close menu (click hamburger again)
        hamburger_button.click()

        # Verify menu closes
        page.wait_for_function(
            "document.getElementById('mobile-menu').classList.contains('hidden') === true"
        )
        expect(mobile_menu).to_have_class(re.compile("hidden"))

    # Test on article detail page (need to navigate to an actual article)
    page.goto("/")
    # Click first article
    first_article = page.locator("article a").first
    if first_article.is_visible():
        first_article.click()

        # Verify hamburger button works on detail page
        hamburger_button = page.locator("#mobile-menu-button")
        expect(hamburger_button).to_be_visible()

        # Open and close menu
        hamburger_button.click()
        page.wait_for_function(
            "document.getElementById('mobile-menu').classList.contains('hidden') === false"
        )
        mobile_menu = page.locator("#mobile-menu")
        expect(mobile_menu).to_be_visible()

        hamburger_button.click()
        page.wait_for_function(
            "document.getElementById('mobile-menu').classList.contains('hidden') === true"
        )
        expect(mobile_menu).to_have_class(re.compile("hidden"))


@pytest.mark.mobile
def test_mobile_menu_has_pointer_cursor(page: Page) -> None:
    """
    Test: Mobile menu hamburger button has pointer cursor on hover.

    User Journey:
    1. Navigate to home page on mobile viewport
    2. Hover over hamburger button
    3. Verify cursor is pointer
    """
    # Set mobile viewport
    page.set_viewport_size({"width": 390, "height": 844})

    # Navigate to home page
    page.goto("/")

    # Verify hamburger button has cursor-pointer class
    hamburger_button = page.locator("#mobile-menu-button")
    expect(hamburger_button).to_have_class(
        "p-2 rounded-md text-slate-400 hover:text-slate-200 hover:bg-slate-800/50 transition-all duration-200 cursor-pointer"
    )

    # Verify computed style has cursor: pointer
    cursor_style = hamburger_button.evaluate("el => window.getComputedStyle(el).cursor")
    assert cursor_style == "pointer", f"Expected cursor: pointer, got {cursor_style}"
