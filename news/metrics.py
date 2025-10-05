"""
Prometheus custom metrics for HINO9 Django application.

This module defines custom business metrics that are exposed via the /metrics endpoint.
These metrics complement the built-in Django metrics from django-prometheus.
"""

from prometheus_client import Counter, Histogram

# Search Metrics
# Track search queries by type (vector, text, hybrid) and measure latency
SEARCH_QUERIES = Counter(
    "search_queries_total",
    "Total search queries by type",
    ["search_type"],  # labels: vector, text, hybrid
)

SEARCH_DURATION = Histogram(
    "search_duration_seconds",
    "Search query duration in seconds",
    ["search_type"],  # labels: vector, text, hybrid
    buckets=(0.1, 0.25, 0.5, 0.75, 1.0, 2.5, 5.0, 7.5, 10.0),  # Response time buckets
)

# Cache Metrics
# Track cache operations (get/set/delete) and their outcomes (hit/miss/success)
CACHE_OPERATIONS = Counter(
    "cache_operations_total",
    "Cache operations by type and status",
    ["operation", "status"],  # operation: get/set/delete, status: hit/miss/success
)

# Content Metrics
# Track article page views by status
ARTICLE_VIEWS = Counter(
    "article_views_total",
    "Article page views by status",
    ["status"],  # published, 404, etc.
)

# Rate Limiting Metrics
# Track rate limit violations by endpoint
RATE_LIMIT_HITS = Counter(
    "rate_limit_hits_total",
    "Rate limit violations by endpoint",
    ["endpoint"],
)

# Embedding Service Metrics (optional - if we want to track AWS calls)
EMBEDDING_REQUESTS = Counter(
    "embedding_requests_total",
    "Embedding service requests",
    ["status"],  # success, error, timeout
)

EMBEDDING_DURATION = Histogram(
    "embedding_duration_seconds",
    "Embedding service request duration",
    buckets=(0.5, 1.0, 2.0, 5.0, 10.0, 30.0),  # AWS call duration buckets
)
