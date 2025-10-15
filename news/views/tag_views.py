"""
Tag browsing and categorization views.
"""

from django.conf import settings
from django.core.paginator import EmptyPage, PageNotAnInteger, Paginator
from django.http import Http404, HttpRequest, HttpResponse
from django.shortcuts import redirect, render
from django.views.decorators.cache import cache_control, cache_page

from ..models import News, Tag


@cache_page(settings.CACHE_TTL)
@cache_control(max_age=300, public=True)
def tag_detail(request: HttpRequest, tag_slug: str) -> HttpResponse:
    """
    Display news articles for a specific tag with pagination.
    Uses the Tag model for hierarchical tag relationships.

    Server-side cached for CACHE_TTL (7 days). Cache is cleared when database is replaced.
    Browser cached for 5 minutes (max_age=300) for performance while ensuring reasonable freshness.

    Args:
        request: HTTP request object
        tag_slug: URL slug for the tag

    Returns:
        Rendered tag detail template
    """
    try:
        # Look up the tag by slug
        tag = Tag.objects.get(slug=tag_slug)
    except Tag.DoesNotExist:
        raise Http404(f"Tag not found: {tag_slug}")

    # Get all articles for this tag and its descendants using the TagManager
    articles = Tag.objects.get_articles_for_tag(tag).order_by(
        "-article_date", "-created_at"
    )

    # Get navigation context for back links
    from_page = request.GET.get("from_page", "")
    highlight_article = request.GET.get("highlight_article", "")
    from_source = request.GET.get("from", "")

    # Paginate results
    paginator = Paginator(articles, settings.PAGINATION_PAGE_SIZE)
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
        "tag": tag,
        "tag_name": tag.name,
        "tag_slug": tag_slug,
        "hierarchy_path": tag.hierarchy_path,
        "hierarchy_parts": tag.hierarchy_path.split(" > "),
        "articles": paginated_articles,
        "total_count": articles.count(),
        "page_obj": paginated_articles,  # For pagination template tags
        "from_page": from_page,
        "highlight_article": highlight_article,
        "from_source": from_source,
    }

    return render(request, "news/tag_detail.html", context)


@cache_page(settings.CACHE_TTL)
@cache_control(max_age=300, public=True)
def tags_index(request: HttpRequest) -> HttpResponse:
    """
    Display all tags with article counts, ordered alphabetically.

    Server-side cached for CACHE_TTL (7 days). Cache is cleared when database is replaced.
    Browser cached for 5 minutes (max_age=300) for performance while ensuring reasonable freshness.

    Args:
        request: HTTP request object

    Returns:
        Rendered tags index template
    """
    # Get all published news articles with their tags in a single query
    published_news = News.objects.filter(
        status="published", deleted_at__isnull=True
    ).values_list("llm_tags", flat=True)

    # Count tag occurrences
    tag_counts: dict[str, int] = {}
    for tags_array in published_news:
        if tags_array:  # Skip None/empty arrays
            for tag_name in tags_array:
                tag_counts[tag_name] = tag_counts.get(tag_name, 0) + 1

    # Get all tags and attach their counts
    tags = Tag.objects.all().order_by("name")
    tags_with_counts = []
    for tag in tags:
        article_count = tag_counts.get(tag.name, 0)
        if article_count > 2:  # Only show tags with more than 2 articles
            tags_with_counts.append(
                {
                    "tag": tag,
                    "article_count": article_count,
                }
            )

    context = {
        "tags": tags_with_counts,
    }

    return render(request, "news/tags_index.html", context)


def category_detail(request: HttpRequest, category_slug: str) -> HttpResponse:
    """
    Display a category and its subcategories/tags.

    Args:
        request: HTTP request object
        category_slug: URL slug for the category

    Returns:
        Rendered category detail template
    """
    try:
        # Look up the category by slug
        category = Tag.objects.get(slug=category_slug, parent=None)
    except Tag.DoesNotExist:
        raise Http404(f"Category not found: {category_slug}")

    # Get all direct children (subcategories and tags)
    subcategories = category.children.all().prefetch_related("children")

    # Separate subcategories from direct tags
    subcategory_data = []
    direct_tags = []

    for child in subcategories:
        if child.children.exists():
            # This is a subcategory with its own children
            subcategory_data.append(
                {
                    "tag": child,
                    "article_count": child.get_news_count(),
                    "child_count": child.children.count(),
                }
            )
        else:
            # This is a direct tag under the category
            direct_tags.append(
                {
                    "tag": child,
                    "article_count": child.get_news_count(),
                }
            )

    context = {
        "category": category,
        "subcategories": subcategory_data,
        "direct_tags": direct_tags,
        "total_article_count": category.get_news_count(),
    }

    return render(request, "news/category_detail.html", context)


def tag_detail_slash_redirect(request: HttpRequest, tag_slug: str) -> HttpResponse:
    """
    Redirect tag detail URLs with trailing slashes to the version without trailing slash.

    Args:
        request: HTTP request object
        tag_slug: URL slug for the tag

    Returns:
        Redirect to URL without trailing slash
    """
    return redirect("news:tag_detail", tag_slug=tag_slug, permanent=True)


def tags_index_slash_redirect(request: HttpRequest) -> HttpResponse:
    """
    Redirect tags index URLs with trailing slashes to the version without trailing slash.

    Args:
        request: HTTP request object

    Returns:
        Redirect to URL without trailing slash
    """
    return redirect("news:tags_index", permanent=True)
