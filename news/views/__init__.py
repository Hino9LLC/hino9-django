"""
News application views.

This module exports all view functions and classes from the modularized view structure.
Maintains backward compatibility with previous imports (e.g., `from news.views import news_list`).
"""

# Article views
from .article_views import (
    get_client_ip,
    news_detail,
    news_detail_redirect,
    news_detail_slash_redirect,
    news_list,
)

# Search views
from .search_views import news_search, news_search_slash_redirect

# Tag views
from .tag_views import (
    category_detail,
    tag_detail,
    tag_detail_slash_redirect,
    tags_index,
    tags_index_slash_redirect,
)

# Utility views
from .utility_views import (
    KeybaseTxtView,
    RobotsTxtView,
    privacy_policy,
    terms_conditions,
)

__all__ = [
    # Article views
    "news_list",
    "news_detail",
    "news_detail_redirect",
    "news_detail_slash_redirect",
    "get_client_ip",
    # Search views
    "news_search",
    "news_search_slash_redirect",
    # Tag views
    "tag_detail",
    "tags_index",
    "category_detail",
    "tag_detail_slash_redirect",
    "tags_index_slash_redirect",
    # Utility views
    "RobotsTxtView",
    "KeybaseTxtView",
    "privacy_policy",
    "terms_conditions",
]
