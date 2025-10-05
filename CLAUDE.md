# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is an AI-powered news aggregation platform (`ainews`) built with Django and modern Python tooling. It features a news application with AI-powered content processing and vector-based search capabilities. The project uses PostgreSQL with pgvector extension for vector embeddings and AWS services for embedding generation.

## Development Commands

All common development tasks are managed through the Makefile:

```bash
make setup          # Install dependencies and migrate database (run first time)
make run            # Start development server on port 8300
make migrate        # Apply database migrations
make makemigrations # Create new database migrations

# Testing
make test           # Run Django unit tests (PostgreSQL)
make test-e2e       # Run E2E tests with Playwright (headed mode)
make test-all       # Run all tests (unit + E2E)

# Code Quality
make lint           # Run code linting with ruff
make typecheck      # Run type checking with mypy
make format         # Format code with black and ruff
make shell          # Open Django shell
make superuser      # Create Django admin superuser
make check          # Run Django system checks
make prod-check     # Run all quality checks (check, test, lint, typecheck)
make clean          # Clean temporary files
```

The project uses `uv` as the package manager instead of pip.

## Architecture & Key Components

### Database Configuration
- **Primary Database**: PostgreSQL with pgvector extension for vector similarity search
- **Models**: Uses the existing `news` table with Django ORM mapping via `db_table = "news"`
- **Vector Embeddings**: 768-dimensional embeddings (nomic-embed-text-v1.5) stored in `content_embedding` field

#### News vs Articles Table Architecture

The system uses a dual-table architecture for optimal search performance:

**News Table** (`news`):
- Contains LLM-processed content (headlines, summaries, bullets, tags)
- `content_text`: **Pre-concatenated** text of all LLM fields (`llm_headline` + `llm_summary` + `llm_bullets`). This field is maintained by the application logic, not by the database.
- `content_embedding`: Vector embedding (768-dim) of the `content_text` field
- `ts_vector_content`: PostgreSQL FTS TSVECTOR **GENERATED ALWAYS AS** column from `content_text` (automatically maintained by database)
- `article_id`: Foreign key reference to the full article in the articles table
- Purpose: Optimized for quick searching/browsing with AI-enhanced summaries
- **Important**: Since `content_text` already contains all LLM fields and `ts_vector_content` is auto-generated from it, search queries should use these pre-processed columns directly rather than manually concatenating individual fields

**Articles Table** (`articles`):
- Contains the complete original article text
- `content_text`: Full article text (not concatenated, but the complete original content)
- `content_embedding`: Vector embedding (768-dim) of the full article text
- `ts_vector_content`: PostgreSQL FTS TSVECTOR **GENERATED ALWAYS AS** column from `content_text` (automatically maintained by database)
- Purpose: Deep semantic search across complete article content

**Relationship**: `news.article_id` → `articles.id` (one-to-one)

### News Application (`/news/`)
- **Models**: `News` model with comprehensive fields including LLM-generated content (headlines, summaries, bullets, tags)
- **Views**: Supports list, detail, and advanced search functionality (vector, text, hybrid search)
- **Search Types**:
  - Vector search using pgvector cosine distance
  - Traditional text search across multiple fields
  - Hybrid search combining both approaches
- **URL Patterns**: SEO-friendly URLs with slugs (`/news/{id}/{slug}/`)

#### Sophisticated Search Implementation

The search system (`news/views.py`) implements three search modes:

**1. Vector Search** (`_vector_search`):
- Uses pgvector cosine distance (`<=>` operator) for semantic similarity
- Currently searches only `news.content_embedding` (LLM-generated content)
- Generates query embedding via AWS API Gateway
- Orders by similarity score (lower distance = higher relevance)
- Note: `articles.content_embedding` exists but is not currently used in search

**2. Text Search** (`_text_search`):
- Uses PostgreSQL Full-Text Search (FTS) with field weighting
- Searches both tables via lateral join:
  - `articles.ts_vector_content` (full article text, generated column)
  - `news.ts_vector_content` (LLM content from content_text, generated column)
- Uses `ts_rank_cd` for relevance scoring with field-specific weights
- Employs `plainto_tsquery` and `to_tsquery` for query parsing
- **Current Implementation Note**: Text search currently manually concatenates individual news fields instead of using the pre-generated `news.ts_vector_content` column (opportunity for optimization)

**3. Hybrid Search** (`_hybrid_search`):
- Combines vector and text search approaches
- Uses RRF (Reciprocal Rank Fusion) for score normalization
- Merges results from both search types
- Provides balanced results leveraging both semantic and keyword matching

**Search Performance Notes**:
- Both tables have IVFFlat indexes on embeddings for fast vector search
- Both tables have GIN indexes on TSVECTOR fields for fast text search
- TSVECTOR fields are GENERATED columns (automatically updated on data changes)

### Embedding Service
- **Integration**: AWS API Gateway with IAM authentication for generating embeddings
- **Service**: Singleton pattern in `news/embedding_service.py`
- **Retry Logic**: Built-in retry mechanism with exponential backoff

### Frontend
- **Templates**: Django templates in `news/templates/news/`
- **Styling**: Tailwind CSS integration via `django-tailwind` and `theme` app
- **Hot Reload**: `django-browser-reload` for development

## Environment Configuration

Required environment variables (stored in `.env`):
- `SECRET_KEY`: Django secret key
- `DEBUG`: Django debug mode
- `POSTGRES_*`: Database connection settings
- `AWS_*`: AWS credentials and API Gateway URL for embeddings

## Code Standards

- **Type Hints**: Strict type checking enabled with mypy
- **Formatting**: Black with 88-character line length
- **Linting**: Ruff with specific rules (E, F, I)
- **Python Version**: 3.11+

## Testing

**Quick Start**:
```bash
./test_with_postgres.sh  # PostgreSQL with pgvector (recommended)
make test                 # SQLite fallback
```

**Test Status**:
- ✅ Django Unit Tests: 232/232 passing (100%)
- ✅ E2E Tests: 21+ Playwright tests

**Documentation**:
- `TESTING.md` - Django unit testing (models, views, search, SEO)
- `E2E_TESTING.md` - Playwright E2E testing (user journeys, navigation)

**Django Unit Test Coverage** (232 tests, ~3s):
- Models (44 tests) - Data integrity, properties, methods
- Views (55 tests) - HTTP responses, templates, context
- Search (27 tests) - Vector, text, hybrid search
- SEO (40 tests) - Sitemap, robots.txt, structured data, meta tags
- URLs (25 tests) - Routing, redirects, slug handling
- Integration (15 tests) - End-to-end user journeys
- SQLite compatibility (22 tests) - Fallback database support

**E2E Test Coverage** (21+ tests, ~30-60s):
- Article journeys (5 tests) - Navigation, pagination context, mobile
- Search flows (8 tests) - Vector/text/hybrid search, type switching
- Navigation (8 tests) - Tag browsing, context preservation, accessibility
- Visual regression - Screenshot comparison for UI changes

## SEO Features

The project includes comprehensive SEO optimizations for production deployment:

### Sitemap Generation
- **Location**: `/sitemap.xml`
- **Implementation**: `news/sitemaps.py` with `NewsSitemap` and `TagSitemap` classes
- **Content**: Automatically generated XML sitemap with all published articles and tags
- **Features**:
  - News articles with last modification dates and weekly change frequency (priority: 0.8)
  - Tag pages with monthly change frequency (priority: 0.6)
  - Proper URL formatting with slugs
  - Filters for published articles only (`status="published"` and `deleted_at__isnull=True`)
- **Configuration**: Added `django.contrib.sitemaps` to `INSTALLED_APPS`

### Robots.txt
- **Location**: `/robots.txt`
- **Implementation**: `news/views.py::RobotsTxtView` class-based view
- **Content**: Standard robots.txt allowing all pages except admin
- **Sitemap Reference**: Dynamically includes sitemap URL using `request.get_host()` for production compatibility
- **Features**: Disallows `/admin/` directory, allows all other paths

### Structured Data (JSON-LD)
- **Location**: All article detail pages (`/news/{id}/{slug}/`)
- **Implementation**: `news/templates/news/news_detail.html` structured_data block
- **Format**: NewsArticle schema.org structured data
- **Content**: Article metadata including:
  - headline, description, image array
  - datePublished, dateModified
  - url, mainEntityOfPage
  - publisher and author (Organization type)
  - keywords from llm_tags
  - articleSection from first tag
  - isAccessibleForFree: true
- **Validation**: Compatible with Google's Rich Results Test and Schema.org Validator
- **URL Format**: All URLs use absolute format with `request.scheme` and `request.get_host()`

### Canonical URLs
- **Implementation**:
  - Model method: `News.get_absolute_url()` in `news/models.py`
  - Template block: `canonical_url` in `news/templates/news/news_detail.html`
  - Base template: Block placeholder in `theme/templates/base.html`
- **SEO Benefits**: Prevents duplicate content issues and consolidates link signals
- **URL Format**: Absolute URLs with proper domain and path structure (`/news/{id}/{slug}/`)
- **Features**: Query parameters (pagination, search context) do not affect canonical URL

### Meta Tags
- **Open Graph**: Complete social media optimization (title, description, image, type)
- **Twitter Cards**: Enhanced Twitter sharing with large image cards (`summary_large_image`)
- **Meta Descriptions**: SEO-optimized descriptions for all pages
- **Implementation**: Template blocks in `theme/templates/base.html` with overrides in child templates
- **Image Handling**: Falls back to default site image if article image not available

### Files Modified for SEO Features
- `ainews/settings.py` - Added `django.contrib.sitemaps` to INSTALLED_APPS
- `ainews/urls.py` - Added sitemap and robots.txt URL patterns
- `news/sitemaps.py` - **New file** with NewsSitemap and TagSitemap classes
- `news/models.py` - Added `get_absolute_url()` method to News model
- `news/views.py` - Added RobotsTxtView class
- `news/templates/news/news_detail.html` - Added JSON-LD structured data and canonical URL blocks
- `theme/templates/base.html` - Added canonical_url and structured_data block placeholders

## Testing URLs

Key URLs for testing SEO and functionality:

### SEO Testing
- **Sitemap**: `http://localhost:8300/sitemap.xml`
- **Robots.txt**: `http://localhost:8300/robots.txt`
- **Article with JSON-LD**: `http://localhost:8300/news/{id}/{slug}/` (e.g., `http://localhost:8300/news/2765/trump-shares-ai-generated-video-promoting-qanon-medbed-conspiracy-theory-before-deleting-post/`)

### Functionality Testing
- **Home Page**: `http://localhost:8300/` (news list with pagination)
- **Search**: `http://localhost:8300/news/search/` (vector, text, and hybrid search)
- **Tags Index**: `http://localhost:8300/news/tags/` (browse by tags)
- **Tag Detail**: `http://localhost:8300/news/tag/{slug}/` (articles by specific tag)

### Social Media Testing
- **Facebook Debugger**: https://developers.facebook.com/tools/debug/
- **Twitter Card Validator**: https://cards-dev.twitter.com/validator
- **Google Rich Results**: https://search.google.com/test/rich-results

## Production Deployment Checklist

Before deploying to production, ensure:

1. ✅ All SEO features implemented and tested
2. ✅ Production CSS built (`make build-css`)
3. ✅ All tests passing (`make prod-check`)
4. ✅ Sitemap URLs use production domain (not localhost)
5. ✅ Robots.txt sitemap URL uses production domain
6. ✅ Canonical URLs use production domain
7. ✅ Social media meta tags use production domain for images

## Key Development Notes

- The server runs on port 8300 (not the Django default 8000)
- The `News` model maps to an existing database table, so be careful with migrations
- Vector search requires valid embeddings in the database
- The embedding service uses AWS SigV4 authentication
- URLs include both ID and slug for SEO, with automatic redirects for legacy URLs