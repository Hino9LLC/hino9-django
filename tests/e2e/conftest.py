"""
Pytest configuration for E2E tests using Playwright.

This module provides fixtures for running E2E tests against a live Django server.
"""

import os
import subprocess
import time
from typing import Generator

import pytest
from playwright.sync_api import Browser, BrowserContext, Page


@pytest.fixture(scope="session")
def django_server() -> Generator[str, None, None]:
    """
    Start a live Django development server for E2E testing on port 8301.

    Note: Uses port 8301 (not 8300) so it doesn't conflict with 'make run'.
    This allows developers to keep their dev server running while testing.

    Returns:
        str: The base URL of the running server (http://localhost:8301)
    """
    base_url = "http://localhost:8301"

    # Set environment variables for test server
    env = os.environ.copy()
    env["DJANGO_SETTINGS_MODULE"] = "ainews.settings"
    env["DEBUG"] = "False"  # Use production-like settings (shows 404 template)
    env["RATELIMIT_ENABLE"] = "False"  # Disable rate limiting for tests

    # Clear cache before starting test server
    subprocess.run(
        [
            "uv",
            "run",
            "python",
            "manage.py",
            "shell",
            "-c",
            "from django.core.cache import cache; cache.clear()",
        ],
        env=env,
        check=False,  # Don't fail if cache clear fails
    )

    # Start Django server on port 8301 (not 8300, to avoid conflicts with dev server)
    process = subprocess.Popen(
        ["uv", "run", "python", "manage.py", "runserver", "8301", "--noreload"],
        env=env,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )

    # Wait for server to be ready
    max_retries = 30
    for _ in range(max_retries):
        try:
            import requests

            response = requests.get(base_url, timeout=1)
            if response.status_code:
                break
        except (requests.ConnectionError, requests.Timeout):
            time.sleep(0.5)
    else:
        process.kill()
        raise RuntimeError(
            "Django server failed to start. Check if port 8301 is available."
        )

    yield base_url

    # Cleanup: stop the server we started
    process.terminate()
    process.wait(timeout=5)


@pytest.fixture(scope="session")
def browser_context_args(browser_context_args: dict) -> dict:
    """
    Configure browser context arguments.

    Args:
        browser_context_args: Default browser context arguments

    Returns:
        dict: Updated browser context arguments with custom settings
    """
    return {
        **browser_context_args,
        "viewport": {"width": 1920, "height": 1080},
        "locale": "en-US",
        "timezone_id": "America/New_York",
    }


@pytest.fixture
def context(
    browser: Browser, browser_context_args: dict
) -> Generator[BrowserContext, None, None]:
    """
    Create a new browser context for each test.

    Args:
        browser: Playwright browser instance
        browser_context_args: Browser context configuration

    Yields:
        BrowserContext: Fresh browser context for the test
    """
    context = browser.new_context(**browser_context_args)
    yield context
    context.close()


@pytest.fixture(scope="session")
def base_url(django_server: str) -> str:
    """
    Provide base URL for pytest-playwright.

    This fixture is used by pytest-playwright to set the base URL for all page.goto() calls.

    Args:
        django_server: Base URL of the running Django server

    Returns:
        str: Base URL for tests
    """
    return django_server


@pytest.fixture
def page(context: BrowserContext, base_url: str) -> Generator[Page, None, None]:
    """
    Create a new page for each test with the Django server URL.

    Args:
        context: Browser context
        base_url: Base URL of the running Django server

    Yields:
        Page: Fresh page for the test
    """
    page = context.new_page()
    yield page
    page.close()


@pytest.fixture
def mobile_page(browser: Browser, base_url: str) -> Generator[Page, None, None]:
    """
    Create a mobile viewport page for responsive testing.

    Args:
        browser: Playwright browser instance
        base_url: Base URL of the running Django server

    Yields:
        Page: Mobile viewport page for the test
    """
    context = browser.new_context(
        viewport={"width": 375, "height": 812},  # iPhone X dimensions
        user_agent="Mozilla/5.0 (iPhone; CPU iPhone OS 14_0 like Mac OS X) AppleWebKit/605.1.15",
        has_touch=True,
        is_mobile=True,
        base_url=base_url,  # Add base_url to context
    )
    page = context.new_page()
    yield page
    context.close()
