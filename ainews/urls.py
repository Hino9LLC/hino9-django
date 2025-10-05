"""
URL configuration for ainews project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""

from django.conf import settings
from django.contrib import admin
from django.contrib.sitemaps.views import sitemap
from django.http import HttpRequest, JsonResponse
from django.urls import include, path
from django.views.decorators.cache import cache_page
from django.views.decorators.csrf import csrf_exempt

from news.sitemaps import NewsSitemap, TagSitemap
from news.views import KeybaseTxtView, RobotsTxtView


@csrf_exempt
def health_check(request: HttpRequest) -> JsonResponse:
    """Health check endpoint for Docker and load balancers."""
    return JsonResponse({"status": "healthy"}, status=200)


# Sitemap configuration
sitemaps = {
    "news": NewsSitemap,
    "tags": TagSitemap,
}

urlpatterns = [
    path("", include("django_prometheus.urls")),  # Prometheus metrics at /metrics
    path("health", health_check, name="health"),  # Health check for Docker
    path(
        "admin/", admin.site.urls
    ),  # Keep admin with trailing slash (Django convention)
    path("", include("news.urls")),  # Include news app URLs at root
    path("keybase.txt", KeybaseTxtView.as_view(), name="keybase_txt"),
    path("robots.txt", RobotsTxtView.as_view(), name="robots_txt"),
    path(
        "sitemap.xml",
        cache_page(settings.CACHE_TTL)(sitemap),
        {"sitemaps": sitemaps},
        name="sitemap",
    ),
]

# Development-only URLs
if settings.DEBUG:
    from django.conf.urls.static import static

    # Add browser reload only in DEBUG mode
    urlpatterns.append(path("__reload__/", include("django_browser_reload.urls")))
    # Serve static files in development
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)

# Custom error handlers
# Must be defined at module level in root URLconf
handler404 = "theme.views.handler404"
handler500 = "theme.views.handler500"
