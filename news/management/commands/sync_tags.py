import json
import os
import re
from typing import Any, Dict, List

from django.core.management.base import BaseCommand, CommandError
from django.utils.text import slugify

from ...models import Tag


class Command(BaseCommand):
    """
    Synchronize Tag database with tagCategories.js structure.

    Creates flat tags from all tags found in the hierarchical structure.
    """

    help = "Sync Tag database with tagCategories.js structure (creates flat tags)"

    def add_arguments(self, parser) -> None:  # type: ignore
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Show what would be done without making changes",
        )
        parser.add_argument(
            "--force",
            action="store_true",
            help="Force recreation of all tags (removes existing tags first)",
        )

    def handle(self, *args, **options) -> None:  # type: ignore
        dry_run = options["dry_run"]
        force = options["force"]

        self.stdout.write("Syncing tags from tagCategories.js...")

        # Read and parse the tagCategories.js file
        try:
            categories = self._parse_tag_categories_js()
        except Exception as e:
            raise CommandError(f"Failed to parse tagCategories.js: {e}")

        if dry_run:
            self.stdout.write("DRY RUN - No changes will be made")
            self.stdout.write(f"Found {len(categories)} categories in tagCategories.js")

        # Handle existing tags
        if not dry_run and force:
            current_count = Tag.objects.count()
            self.stdout.write(f"Force mode: Deleting {current_count} existing tags...")
            Tag.objects.all().delete()

        # Collect all unique tags from the hierarchical structure
        all_tags = set()

        for category_name, subcategories in categories.items():
            # Process each subcategory
            for subcategory in subcategories:
                tags = subcategory["tags"]
                # Add all tags from this subcategory
                all_tags.update(tags)

        # Create flat tags for all collected tags
        created_count = 0

        for tag_name in sorted(all_tags):
            if not dry_run:
                self.stdout.write(f"Processing tag: {tag_name}")

            tag, tag_created = Tag.objects.get_or_create(
                name=tag_name, defaults={"slug": slugify(tag_name)}
            )

            if tag_created:
                created_count += 1
                if not dry_run:
                    self.stdout.write(f"  Created tag: {tag_name}")

        if not dry_run:
            self.stdout.write(
                self.style.SUCCESS(
                    f"Sync completed: {created_count} flat tags created from {len(all_tags)} total tags"
                )
            )

    def _parse_tag_categories_js(self) -> Dict[str, List[Dict[str, Any]]]:
        """
        Parse the tagCategories.js file and return the categories structure.
        """
        tag_categories_path = os.path.join(
            os.path.dirname(__file__),  # commands directory
            "..",  # management directory
            "..",  # news directory
            "..",  # project root
            "tagCategories.js",
        )

        with open(tag_categories_path, "r", encoding="utf-8") as f:
            content = f.read()

        # Extract the categories object from the JavaScript
        categories_match = re.search(r"const categories = ({.*?});", content, re.DOTALL)
        if not categories_match:
            raise ValueError("Could not find categories object in tagCategories.js")

        categories_js = categories_match.group(1)

        # Convert JavaScript object to Python dict
        try:
            # Convert JavaScript object syntax to JSON
            categories_js = re.sub(r"(\w+):", r'"\1":', categories_js)
            categories_js = re.sub(r",(\s*[}\]])", r"\1", categories_js)

            categories = json.loads(categories_js)
        except json.JSONDecodeError as e:
            raise ValueError(f"Failed to parse categories from tagCategories.js: {e}")

        return categories
