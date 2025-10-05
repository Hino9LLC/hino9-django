from django.shortcuts import redirect
from django.urls import path

from . import views

app_name = "news"

urlpatterns = [
    path("", views.news_list, name="list"),
    # Legacy URL redirect (old site used /latest-headlines)
    path("latest-headlines", lambda request: redirect("news:list", permanent=True)),
    path("latest-headlines/", lambda request: redirect("news:list", permanent=True)),
    path("<int:news_id>/<slug:slug>", views.news_detail, name="detail"),
    path(
        "<int:news_id>/<slug:slug>/",
        views.news_detail_slash_redirect,
        name="detail_slash_redirect",
    ),
    path("<int:news_id>", views.news_detail_redirect, name="detail_redirect"),
    path("search", views.news_search, name="search"),
    path("search/", views.news_search_slash_redirect, name="search_slash_redirect"),
    # Tag browsing URLs
    path("tags", views.tags_index, name="tags_index"),
    path("tags/", views.tags_index_slash_redirect, name="tags_index_slash_redirect"),
    path("tag/<slug:tag_slug>", views.tag_detail, name="tag_detail"),
    path(
        "tag/<slug:tag_slug>/",
        views.tag_detail_slash_redirect,
        name="tag_detail_slash_redirect",
    ),
    # Legal pages
    path("privacy", views.privacy_policy, name="privacy_policy"),
    path("privacy/", lambda request: redirect("news:privacy_policy", permanent=True)),
    path("terms", views.terms_conditions, name="terms_conditions"),
    path("terms/", lambda request: redirect("news:terms_conditions", permanent=True)),
]
