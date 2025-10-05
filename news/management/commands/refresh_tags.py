from typing import Any

from django.core.management.base import BaseCommand
from django.db import connection, transaction

from news.models import Tag


class Command(BaseCommand):
    help = "Refresh the tags table from news article llm_tags arrays"

    def add_arguments(self, parser: Any) -> None:
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Show what would be done without making changes",
        )

    def handle(self, *args: Any, **options: Any) -> None:
        dry_run = options["dry_run"]

        if dry_run:
            self.stdout.write("DRY RUN MODE - No changes will be made")
            self.stdout.write("-" * 50)

        # Get tag frequencies from news table
        self.stdout.write("Querying tag frequencies from news table...")

        with connection.cursor() as cursor:
            cursor.execute(
                """
                SELECT tag, COUNT(*) AS frequency
                FROM (
                  SELECT unnest(llm_tags) AS tag
                  FROM news
                  WHERE llm_tags IS NOT NULL
                ) AS tags
                GROUP BY tag
                ORDER BY tag;
            """
            )
            tag_data = cursor.fetchall()

        tag_frequencies = {row[0]: row[1] for row in tag_data}
        self.stdout.write(f"Found {len(tag_frequencies)} unique tags in news articles")

        if dry_run:
            self.stdout.write("\nTags that would be processed:")
            for tag_name, freq in sorted(tag_frequencies.items()):
                self.stdout.write(f"  {tag_name}: {freq} articles")
            return

        # Start transaction for atomic operation
        with transaction.atomic():
            # Get existing tags
            existing_tags = {tag.name: tag for tag in Tag.objects.all()}
            existing_names = set(existing_tags.keys())

            # Determine what to do
            tags_to_create = set(tag_frequencies.keys()) - existing_names
            tags_to_update = set(tag_frequencies.keys()) & existing_names
            tags_to_delete = existing_names - set(tag_frequencies.keys())

            self.stdout.write("\nPlan:")
            self.stdout.write(f"  Create: {len(tags_to_create)} new tags")
            self.stdout.write(f"  Update: {len(tags_to_update)} existing tags")
            self.stdout.write(f"  Delete: {len(tags_to_delete)} unused tags")

            # Delete unused tags
            if tags_to_delete:
                deleted_count = Tag.objects.filter(name__in=tags_to_delete).delete()[0]
                self.stdout.write(f"Deleted {deleted_count} unused tags")

            # Create new tags
            created_tags = []
            for tag_name in sorted(tags_to_create):
                tag = Tag.objects.create(name=tag_name)
                created_tags.append(tag.name)

            if created_tags:
                self.stdout.write(f"Created {len(created_tags)} new tags:")
                for name in created_tags:
                    self.stdout.write(f"  + {name}")

            # Update existing tags (mainly to ensure slugs are correct)
            updated_count = 0
            for tag_name in sorted(tags_to_update):
                tag = existing_tags[tag_name]
                # The save() method will auto-generate slug if needed
                old_slug = tag.slug
                tag.save()  # This will regenerate slug from name if needed
                if tag.slug != old_slug:
                    updated_count += 1

            if updated_count > 0:
                self.stdout.write(f"Updated slugs for {updated_count} tags")

        # Final verification
        final_count = Tag.objects.count()
        self.stdout.write(f"\nFinal result: {final_count} tags in database")

        # Show frequency summary
        self.stdout.write("\nTag frequency summary:")
        sorted_tags = sorted(tag_frequencies.items(), key=lambda x: x[1], reverse=True)
        for tag_name, freq in sorted_tags[:10]:  # Top 10 most frequent
            self.stdout.write(f"  {tag_name}: {freq}")
        if len(sorted_tags) > 10:
            self.stdout.write(f"  ... and {len(sorted_tags) - 10} more")
