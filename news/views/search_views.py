"""
Search-related views for news articles.
"""

from django.conf import settings
from django.core.paginator import EmptyPage, PageNotAnInteger, Paginator
from django.db.models import QuerySet
from django.http import HttpRequest, HttpResponse
from django.shortcuts import redirect, render
from django_ratelimit.decorators import ratelimit

from ..models import News
from ..services import SearchService
from .article_views import get_client_ip


@ratelimit(
    key=get_client_ip, rate=settings.SEARCH_RATE_LIMIT, method="GET", block=False
)
def news_search(request: HttpRequest) -> HttpResponse:
    """
    Search news articles using hybrid approach: vector similarity + traditional text search.

    Rate limited based on SEARCH_RATE_LIMIT setting (default: 100 requests/hour per IP).

    Args:
        request: HTTP request object

    Returns:
        Rendered search results template
    """
    # Check if rate limited and block the request (only when RATELIMIT_ENABLE is True)
    if getattr(settings, "RATELIMIT_ENABLE", True) and getattr(
        request, "limited", False
    ):
        context = {
            "rate_limited": True,
            "error_message": "Too many search requests. Please try again later.",
        }
        return render(request, "news/news_search.html", context, status=429)

    query = request.GET.get("q", "").strip()
    search_type = request.GET.get("type", "hybrid")  # hybrid, vector, text

    # Normalize search_type to valid values
    if search_type not in ["vector", "text", "hybrid"]:
        search_type = "hybrid"

    news_articles: QuerySet[News] = News.objects.none()

    if query:
        # Create search service instance
        search_service = SearchService()

        if search_type == "vector":
            # Pure vector similarity search - limit to top 100 results
            news_articles = search_service.vector_search(query, limit=100)
        elif search_type == "text":
            # Traditional text search - limit to 100 results
            news_articles = search_service.text_search(query, limit=100)
        else:
            # Hybrid search (default): combine vector and text search - limit to 100 results
            news_articles = search_service.hybrid_search(query, limit=100)

    # Get total count before pagination
    total_count = news_articles.count()

    # Paginate results
    paginator = Paginator(news_articles, settings.PAGINATION_PAGE_SIZE)
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
        "query": query,
        "search_type": search_type,
        "total_count": total_count,
        "page_obj": paginated_articles,  # For pagination template tags
    }

    return render(request, "news/news_search.html", context)


def news_search_slash_redirect(request: HttpRequest) -> HttpResponse:
    """
    Redirect search URLs with trailing slashes to the version without trailing slash.

    Args:
        request: HTTP request object

    Returns:
        Redirect to search URL without trailing slash
    """
    query_string = request.META.get("QUERY_STRING", "")
    if query_string:
        return redirect(f"/search?{query_string}", permanent=True)
    return redirect("news:search", permanent=True)
