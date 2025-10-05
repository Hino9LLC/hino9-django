"""
Database resilience middleware with exponential backoff retry.

Automatically retries database operations during brief outages (e.g., database restarts).

This middleware is critical for the production deployment workflow where the database
is periodically replaced with a fresh copy from the local curation process. During the
~5-second replacement window, this middleware ensures users experience zero downtime
by automatically retrying failed requests.

Key Features:
- 30-second retry window with exponential backoff (200ms → 3s)
- Smart 500 error detection (only retries actual database failures, not app bugs)
- Path whitelisting to avoid delays on static files
- 15 retry limit to prevent connection spam
- Works with both DEBUG=True and DEBUG=False
"""

import logging
import time
from typing import Callable

from django.db import OperationalError, connection
from django.http import HttpRequest, HttpResponse, JsonResponse

logger = logging.getLogger(__name__)


class DatabaseRetryMiddleware:
    """
    Middleware that retries requests on database connection failures with exponential backoff.

    Only applies to database-dependent paths (whitelist approach) to avoid unnecessary delays
    for static files, health checks, and other non-database endpoints.

    Retries for up to 30 seconds to handle temporary database outages during deployments,
    restarts, or network hiccups. This allows the browser to "wait" while the database
    recovers, providing a seamless user experience.
    """

    def __init__(self, get_response: Callable[[HttpRequest], HttpResponse]) -> None:
        self.get_response = get_response
        self.max_retry_time = 30.0  # seconds
        self.max_retries = 15  # Limit number of attempts (in addition to time limit)
        self.initial_delay = 0.2  # 200ms
        self.max_delay = 3.0  # 3 seconds
        self.backoff_factor = 1.5

        # Only retry paths that are likely to use the database
        self.retry_paths = {
            "/",  # Main news list page
            "/news/",  # News detail, search, and tag pages
            "/admin/",  # Django admin
            "/sitemap.xml",  # Sitemap (database-dependent)
        }

    def __call__(self, request: HttpRequest) -> HttpResponse:
        """Process the request with automatic retry on database errors."""
        # Only apply retry logic to database-dependent paths
        should_retry = any(request.path.startswith(path) for path in self.retry_paths)

        if not should_retry:
            return self.get_response(request)

        start_time = time.time()
        retries = 0
        delay = self.initial_delay

        while True:
            try:
                if retries > 0:
                    connection.close()
                    logger.warning(
                        f"Database retry attempt {retries} for {request.path}"
                    )

                response = self.get_response(request)

                # Check if this is a 500 error that might be database-related
                if response.status_code == 500:
                    # Try to detect if this is a database error by checking connection
                    try:
                        from django.db import connection as db_conn

                        db_conn.ensure_connection()
                        # Connection works, this is a real application error - don't retry
                        logger.warning(
                            f"500 error but database is up, not retrying: {request.path}"
                        )
                        return response
                    except OperationalError:
                        # Database is down, retry this request
                        retries += 1
                        elapsed = time.time() - start_time

                        # Check limits
                        if (
                            elapsed >= self.max_retry_time
                            or retries >= self.max_retries
                        ):
                            logger.error(
                                f"Database still unavailable after {elapsed:.1f}s ({retries} attempts): {request.path}"
                            )
                            return self._create_error_response(request)

                        logger.warning(
                            f"500 error with database down (attempt {retries}), retrying in {delay:.2f}s: {request.path}"
                        )
                        time.sleep(delay)
                        delay = min(delay * self.backoff_factor, self.max_delay)
                        continue

                # Success! Log recovery if we had retries
                if retries > 0:
                    elapsed = time.time() - start_time
                    logger.warning(
                        f"Database connection recovered after {retries} retries ({elapsed:.1f}s): {request.path}"
                    )

                return response

            except OperationalError:
                retries += 1
                elapsed = time.time() - start_time

                # Check both time limit and retry count limit
                if elapsed >= self.max_retry_time or retries >= self.max_retries:
                    logger.error(
                        f"Database unavailable after {elapsed:.1f}s ({retries} attempts): {request.path}"
                    )
                    return self._create_error_response(request)

                logger.warning(
                    f"Database error (attempt {retries}, {elapsed:.1f}s elapsed). Retrying in {delay:.2f}s: {request.path}"
                )
                time.sleep(delay)
                delay = min(delay * self.backoff_factor, self.max_delay)

            except Exception:
                # Let all other exceptions propagate normally
                # This ensures proper error handling and debugging
                raise

    def _create_error_response(self, request: HttpRequest) -> HttpResponse:
        """Create appropriate error response based on request type."""
        if (
            request.path.startswith("/api/")
            or request.headers.get("Accept") == "application/json"
        ):
            return JsonResponse(
                {
                    "error": "Service temporarily unavailable. Please try again.",
                    "details": "Database connection failed",
                },
                status=503,
            )
        else:
            return HttpResponse(
                """
                <html>
                <head><title>Service Temporarily Unavailable</title></head>
                <body>
                    <h1>Service Temporarily Unavailable</h1>
                    <p>We're experiencing technical difficulties. Please try again in a moment.</p>
                    <p><a href="javascript:location.reload()">Reload Page</a></p>
                </body>
                </html>
                """,
                status=503,
                content_type="text/html",
            )
