"""
Article-related views for listing and displaying news articles.
"""

from django.conf import settings
from django.core.paginator import EmptyPage, PageNotAnInteger, Paginator
from django.http import Http404, HttpRequest, HttpResponse
from django.shortcuts import redirect, render
from django.views.decorators.cache import cache_control, cache_page

from ..models import News


def get_client_ip(group: str, request: HttpRequest) -> str:
    """
    Get the real client IP from X-Forwarded-For header (set by nginx proxy).
    Falls back to REMOTE_ADDR if header is not present.

    Args:
        group: Rate limiting group (unused, required by django-ratelimit)
        request: HTTP request object

    Returns:
        Client IP address string
    """
    x_forwarded_for = request.META.get("HTTP_X_FORWARDED_FOR")
    if x_forwarded_for:
        # X-Forwarded-For can contain multiple IPs: "client, proxy1, proxy2"
        # The first IP is the original client
        ip = x_forwarded_for.split(",")[0].strip()
        return ip
    # Fallback to REMOTE_ADDR (used in local dev without proxy)
    ip = request.META.get("REMOTE_ADDR")
    return ip if ip else ""


@cache_page(settings.CACHE_TTL)
@cache_control(max_age=300, public=True)
def news_list(request: HttpRequest) -> HttpResponse:
    """
    Display the latest news articles with pagination.

    Server-side cached for CACHE_TTL (7 days). Cache is cleared when database is replaced.
    Browser cached for 5 minutes (max_age=300) for performance while ensuring reasonable freshness.

    Args:
        request: HTTP request object

    Returns:
        Rendered news list template
    """
    # Get the latest news articles, only published ones
    news_queryset = News.objects.filter(
        deleted_at__isnull=True, status="published"
    ).order_by("-article_date", "-article_id")

    # Paginate results
    paginator = Paginator(news_queryset, settings.PAGINATION_PAGE_SIZE)
    page = request.GET.get("page", 1)

    try:
        paginated_articles = paginator.page(page)
    except PageNotAnInteger:
        # If page is not an integer, deliver first page
        paginated_articles = paginator.page(1)
    except EmptyPage:
        # If page is out of range, deliver last page
        paginated_articles = paginator.page(paginator.num_pages)

    context = {
        "news_articles": paginated_articles,
        "total_count": news_queryset.count(),
        "page_obj": paginated_articles,  # For pagination template tags
    }

    return render(request, "news/news_list.html", context)


@cache_page(settings.CACHE_TTL)
@cache_control(max_age=300, public=True)
def news_detail(request: HttpRequest, news_id: int, slug: str) -> HttpResponse:
    """
    Display a single news article detail.
    The slug parameter is validated - redirects if it doesn't match.

    Server-side cached for CACHE_TTL (7 days). Cache is cleared when database is replaced.
    Browser cached for 5 minutes (max_age=300) for performance while ensuring reasonable freshness.

    Args:
        request: HTTP request object
        news_id: News article ID
        slug: URL slug for the article

    Returns:
        Rendered news detail template or redirect if slug doesn't match
    """
    try:
        news_article = News.objects.get(
            id=news_id, deleted_at__isnull=True, status="published"
        )
    except News.DoesNotExist:
        raise Http404("News article not found")

    # Verify slug matches (redirect if mismatch for SEO)
    if news_article.slug != slug:
        return redirect(
            "news:detail", news_id=news_id, slug=news_article.slug, permanent=True
        )

    # Get navigation context for back links
    from_search = request.GET.get("from_search", "")
    from_tag = request.GET.get("from_tag", "")
    from_page = request.GET.get("from_page", "1")
    tag_slug = request.GET.get("tag_slug", "")
    tag_name = request.GET.get("tag_name", "")
    search_query = request.GET.get("q", "")
    search_type = request.GET.get("type", "hybrid")

    context = {
        "news_article": news_article,
        "article_id": news_article.id,
        "from_search": from_search,
        "from_tag": from_tag,
        "from_page": from_page,
        "tag_slug": tag_slug,
        "tag_name": tag_name,
        "search_query": search_query,
        "search_type": search_type,
    }

    return render(request, "news/news_detail.html", context)


def news_detail_redirect(request: HttpRequest, news_id: int) -> HttpResponse:
    """
    Redirect URLs without slugs to the proper URL with slug for SEO.

    Args:
        request: HTTP request object
        news_id: News article ID

    Returns:
        Redirect to URL with slug
    """
    try:
        news_article = News.objects.get(
            id=news_id, deleted_at__isnull=True, status="published"
        )
        # Redirect to the URL with the slug
        return redirect(
            "news:detail", news_id=news_id, slug=news_article.slug, permanent=True
        )
    except News.DoesNotExist:
        raise Http404("News article not found")


def news_detail_slash_redirect(
    request: HttpRequest, news_id: int, slug: str
) -> HttpResponse:
    """
    Redirect URLs with trailing slashes to the version without trailing slash.

    Args:
        request: HTTP request object
        news_id: News article ID
        slug: URL slug

    Returns:
        Redirect to URL without trailing slash
    """
    return redirect("news:detail", news_id=news_id, slug=slug, permanent=True)
