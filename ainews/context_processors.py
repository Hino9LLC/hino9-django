"""
Context processors for ainews project.

Context processors make variables available to all templates automatically.
"""

from django.conf import settings
from django.http import HttpRequest


def google_analytics(request: HttpRequest) -> dict[str, str | bool | None]:
    """
    Add Google Analytics ID and debug mode to template context.

    Makes GOOGLE_ANALYTICS_ID and debug settings available in all templates
    for conditional rendering of analytics scripts.
    """
    return {
        "GOOGLE_ANALYTICS_ID": settings.GOOGLE_ANALYTICS_ID,
        "debug": settings.DEBUG,
    }
