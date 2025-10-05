"""
Utility views for robots.txt, keybase.txt, and legal pages.
"""

from django.conf import settings
from django.http import HttpRequest, HttpResponse
from django.shortcuts import render
from django.views import View
from django.views.decorators.cache import cache_control, cache_page


class RobotsTxtView(View):
    """
    Serve robots.txt for search engine crawlers.
    """

    def get(self, request: HttpRequest) -> HttpResponse:
        """
        Generate robots.txt content.

        Args:
            request: HTTP request object

        Returns:
            Plain text robots.txt response
        """
        lines = [
            "User-agent: *",
            "Allow: /",
            "",
            "Sitemap: https://{}{}".format(request.get_host(), "/sitemap.xml"),
        ]
        return HttpResponse("\n".join(lines), content_type="text/plain")


class KeybaseTxtView(View):
    """
    Serve keybase.txt for Keybase identity verification.
    """

    def get(self, request: HttpRequest) -> HttpResponse:
        """
        Serve keybase.txt file content.

        Args:
            request: HTTP request object

        Returns:
            Plain text keybase.txt response or 404 if not found
        """
        try:
            with open(settings.BASE_DIR / "keybase.txt", "r") as f:
                content = f.read()
            return HttpResponse(content, content_type="text/plain")
        except FileNotFoundError:
            return HttpResponse(
                "keybase.txt not found", status=404, content_type="text/plain"
            )


@cache_page(settings.CACHE_TTL)
@cache_control(max_age=300, public=True)
def privacy_policy(request: HttpRequest) -> HttpResponse:
    """
    Display the privacy policy page.

    Server-side cached for CACHE_TTL (7 days). Cache is cleared when database is replaced.
    Browser cached for 5 minutes (max_age=300) for performance while ensuring reasonable freshness.

    Args:
        request: HTTP request object

    Returns:
        Rendered privacy policy template
    """
    return render(request, "news/privacy_policy.html")


@cache_page(settings.CACHE_TTL)
@cache_control(max_age=300, public=True)
def terms_conditions(request: HttpRequest) -> HttpResponse:
    """
    Display the terms & conditions page.

    Server-side cached for CACHE_TTL (7 days). Cache is cleared when database is replaced.
    Browser cached for 5 minutes (max_age=300) for performance while ensuring reasonable freshness.

    Args:
        request: HTTP request object

    Returns:
        Rendered terms & conditions template
    """
    return render(request, "news/terms_conditions.html")
