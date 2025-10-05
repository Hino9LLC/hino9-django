"""
Management command to flush all Redis cache after database replacement.

This command should be run after replacing the production database to ensure
users see fresh article data. It clears all cached views, queries, and rate
limiting data.

Usage:
    docker exec h9-news uv run python manage.py flush_cache

Cache Strategy:
- Views are cached for CACHE_TTL (7 days)
- Data only changes when database is replaced
- This command clears all cached data immediately
- Between database replacements, cache hits are maximized

Performance Impact:
- First request after flush will be slow (cache miss)
- Subsequent requests will be fast (served from cache)
- This is acceptable since database replacement is infrequent
"""

from typing import Any

from django.conf import settings
from django.core.cache import cache
from django.core.management.base import BaseCommand, CommandParser


class Command(BaseCommand):
    help = "Flush all Redis cache (run after database replacement)"

    def add_arguments(self, parser: CommandParser) -> None:
        parser.add_argument(
            "--stats",
            action="store_true",
            help="Show cache statistics before flushing",
        )

    def handle(self, *args: Any, **options: Any) -> None:
        """Flush all cached data from Redis."""

        # Show current cache configuration
        self.stdout.write(self.style.MIGRATE_HEADING("\n=== Cache Flush ==="))
        self.stdout.write(f"Cache Backend: {settings.CACHES['default']['BACKEND']}")
        self.stdout.write(
            f"Cache TTL: {settings.CACHE_TTL} seconds ({settings.CACHE_TTL // 3600} hours)"
        )

        if hasattr(settings, "REDIS_HOST") and settings.REDIS_HOST:
            location = settings.CACHES["default"]["LOCATION"]
            port = location.split(":")[-1] if isinstance(location, str) else "6379"
            self.stdout.write(f"Redis Host: {settings.REDIS_HOST}:{port}")
        else:
            self.stdout.write(
                self.style.WARNING("Using local memory cache (development mode)")
            )

        # Show stats if requested
        if options["stats"]:
            try:
                # Try to get cache keys (Redis-specific, only works with django-redis)
                if hasattr(cache, "_cache") and hasattr(cache._cache, "get_client"):
                    cache_client = cache._cache.get_client()  # type: ignore[attr-defined]
                    keys = cache_client.keys(
                        f"{settings.CACHES['default']['KEY_PREFIX']}:*"
                    )
                    self.stdout.write(f"\nCached keys: {len(keys)}")
                    if len(keys) > 0:
                        self.stdout.write("Sample keys:")
                        for key in list(keys)[:10]:
                            self.stdout.write(
                                f"  - {key.decode() if isinstance(key, bytes) else key}"
                            )
            except Exception:
                pass  # Stats not available for this cache backend

        # Flush the cache
        self.stdout.write("\nFlushing cache...")

        try:
            cache.clear()
            self.stdout.write(self.style.SUCCESS("\n✅ Cache flushed successfully"))
            self.stdout.write(
                self.style.SUCCESS(
                    "   All cached pages will be regenerated on next request"
                )
            )
            self.stdout.write(
                self.style.SUCCESS("   Rate limiting counters have been reset")
            )

        except Exception as e:
            self.stdout.write(self.style.ERROR(f"\n❌ Error flushing cache: {str(e)}"))
            self.stdout.write(
                self.style.ERROR("   Check Redis connection and try again")
            )
            raise

        self.stdout.write("")  # Empty line for spacing
