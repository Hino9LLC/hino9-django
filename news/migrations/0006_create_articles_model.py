# Generated migration for articles table

from typing import Any

from django.contrib.postgres.fields import ArrayField
from django.db import connection, migrations, models
from pgvector.django import VectorField


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
        ("news", "0005_create_news_model"),
    ]

    operations = [
        # Ensure pgvector extension exists (PostgreSQL only, idempotent)
        CreateExtensionIfPostgres(),
        # Create Article model
        migrations.CreateModel(
            name="Article",
            fields=[
                (
                    "id",
                    models.AutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("article_date", models.DateTimeField(blank=True, null=True)),
                ("title", models.CharField(blank=True, max_length=512, null=True)),
                ("summary", models.TextField(blank=True, null=True)),
                ("domain", models.CharField(blank=True, max_length=255, null=True)),
                ("site_name", models.CharField(blank=True, max_length=255, null=True)),
                ("image_url", models.CharField(blank=True, max_length=2048, null=True)),
                ("url", models.CharField(blank=True, max_length=2048, null=True)),
                ("url_id", models.IntegerField(blank=True, null=True)),
                ("email_id", models.CharField(blank=True, max_length=255, null=True)),
                ("status", models.CharField(default="pending", max_length=20)),
                ("error_message", models.TextField(blank=True, null=True)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(blank=True, null=True)),
                ("processed_at", models.DateTimeField(blank=True, null=True)),
                ("deleted_at", models.DateTimeField(blank=True, null=True)),
                (
                    "tags",
                    ArrayField(
                        base_field=models.TextField(),
                        blank=True,
                        null=True,
                        size=None,
                    ),
                ),
                ("metadata", models.JSONField(blank=True, null=True)),
                ("content_text", models.TextField(blank=True, null=True)),
                (
                    "content_embedding",
                    VectorField(blank=True, dimensions=768, null=True),
                ),
            ],
            options={
                "db_table": "articles",
                "ordering": ["-created_at"],
                "managed": True,
            },
        ),
        # Add unique constraint on (url_id, article_date)
        migrations.AddConstraint(
            model_name="article",
            constraint=models.UniqueConstraint(
                fields=["url_id", "article_date"],
                name="articles_url_id_article_date_unique",
            ),
        ),
        # Add generated column and indexes via raw SQL (PostgreSQL only)
        migrations.RunPython(
            code=lambda apps, schema_editor: (
                schema_editor.execute(
                    """
                ALTER TABLE articles
                ADD COLUMN IF NOT EXISTS ts_vector_content TSVECTOR
                GENERATED ALWAYS AS (to_tsvector('english', coalesce(content_text, ''))) STORED;
                CREATE INDEX IF NOT EXISTS articles_ts_vector_idx
                ON articles USING GIN(ts_vector_content);
            """
                )
                if connection.vendor == "postgresql"
                else None
            ),
            reverse_code=lambda apps, schema_editor: (
                schema_editor.execute(
                    """
                DROP INDEX IF EXISTS articles_embedding_idx;
                DROP INDEX IF EXISTS articles_ts_vector_idx;
                ALTER TABLE articles DROP COLUMN IF EXISTS ts_vector_content;
            """
                )
                if connection.vendor == "postgresql"
                else None
            ),
        ),
        # Remove old article_id IntegerField from News
        migrations.RemoveField(
            model_name="news",
            name="article_id",
        ),
        # Add new article ForeignKey to News
        migrations.AddField(
            model_name="news",
            name="article",
            field=models.OneToOneField(
                blank=True,
                db_column="article_id",
                null=True,
                on_delete=models.SET_NULL,
                related_name="news",
                to="news.article",
            ),
        ),
    ]
