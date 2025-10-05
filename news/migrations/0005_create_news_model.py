# Generated migration for News model
# This creates the news table to match the existing database schema

from typing import Any

import django.contrib.postgres.fields
import pgvector.django
from django.db import connection, migrations, models


# Custom operation to only run CreateExtension on PostgreSQL
class CreateExtensionIfPostgres(migrations.RunPython):
    def __init__(self) -> None:
        def create_extension(apps: Any, schema_editor: Any) -> None:
            if connection.vendor == "postgresql":
                from django.contrib.postgres.operations import CreateExtension

                operation = CreateExtension("vector")
                operation.database_forwards("news", schema_editor, None, None)  # type: ignore[arg-type]

        def reverse_extension(apps: Any, schema_editor: Any) -> None:
            if connection.vendor == "postgresql":
                from django.contrib.postgres.operations import CreateExtension

                operation = CreateExtension("vector")
                operation.database_backwards("news", schema_editor, None, None)  # type: ignore[arg-type]

        super().__init__(create_extension, reverse_extension)


class Migration(migrations.Migration):

    dependencies = [
        ("news", "0004_add_tag_parent_field"),
    ]

    operations = [
        # Enable pgvector extension (PostgreSQL only)
        CreateExtensionIfPostgres(),
        migrations.CreateModel(
            name="News",
            fields=[
                ("id", models.AutoField(primary_key=True, serialize=False)),
                ("article_date", models.DateTimeField(blank=True, null=True)),
                ("title", models.CharField(blank=True, max_length=512, null=True)),
                ("summary", models.TextField(blank=True, null=True)),
                ("llm_headline", models.TextField(blank=True, null=True)),
                ("llm_summary", models.TextField(blank=True, null=True)),
                (
                    "llm_bullets",
                    django.contrib.postgres.fields.ArrayField(
                        base_field=models.TextField(),
                        blank=True,
                        help_text="LLM-generated bullet points",
                        null=True,
                        size=None,
                    ),
                ),
                (
                    "llm_tags",
                    django.contrib.postgres.fields.ArrayField(
                        base_field=models.TextField(),
                        blank=True,
                        help_text="LLM-generated tags",
                        null=True,
                        size=None,
                    ),
                ),
                ("domain", models.CharField(blank=True, max_length=255, null=True)),
                ("site_name", models.CharField(blank=True, max_length=255, null=True)),
                ("image_url", models.CharField(blank=True, max_length=2048, null=True)),
                ("url", models.CharField(blank=True, max_length=2048, null=True)),
                ("article_id", models.IntegerField(blank=True, null=True, unique=True)),
                (
                    "status",
                    models.CharField(
                        choices=[
                            ("pending", "Pending"),
                            ("processed", "Processed"),
                            ("failed", "Failed"),
                            ("published", "Published"),
                            ("ignored", "Ignored"),
                        ],
                        default="pending",
                        max_length=20,
                    ),
                ),
                ("error_message", models.TextField(blank=True, null=True)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(blank=True, null=True)),
                ("processed_at", models.DateTimeField(blank=True, null=True)),
                ("deleted_at", models.DateTimeField(blank=True, null=True)),
                ("content_text", models.TextField(blank=True, null=True)),
                (
                    "content_embedding",
                    pgvector.django.VectorField(blank=True, dimensions=768, null=True),
                ),
            ],
            options={
                "verbose_name": "News Article",
                "verbose_name_plural": "News Articles",
                "db_table": "news",
                "ordering": ["-created_at", "-article_date"],
                "managed": True,
            },
        ),
        # Add generated TSVECTOR column for full-text search (PostgreSQL only)
        migrations.RunPython(
            code=lambda apps, schema_editor: (
                schema_editor.execute(
                    """
                ALTER TABLE news
                ADD COLUMN IF NOT EXISTS ts_vector_content TSVECTOR
                GENERATED ALWAYS AS (to_tsvector('english', coalesce(content_text, ''))) STORED;
                CREATE INDEX IF NOT EXISTS news_ts_vector_idx
                ON news USING GIN(ts_vector_content);
            """
                )
                if connection.vendor == "postgresql"
                else None
            ),
            reverse_code=lambda apps, schema_editor: (
                schema_editor.execute(
                    """
                DROP INDEX IF EXISTS news_ts_vector_idx;
                ALTER TABLE news DROP COLUMN IF EXISTS ts_vector_content;
            """
                )
                if connection.vendor == "postgresql"
                else None
            ),
        ),
    ]
