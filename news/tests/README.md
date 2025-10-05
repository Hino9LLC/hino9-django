# News App Test Suite

Comprehensive test suite for the HINO9 Django news application.

## Overview

This test suite implements the testing strategy outlined in `TESTING_PLAN.md`, providing comprehensive coverage of:

- **Models**: Business logic, data integrity, properties, and edge cases
- **Views**: HTTP responses, templates, context, pagination, and filtering
- **Search**: Vector, text, and hybrid search functionality
- **SEO**: Sitemap, robots.txt, meta tags, structured data, canonical URLs
- **URLs**: Routing, patterns, slugs, and redirects
- **Integration**: End-to-end user journeys and flows

## Test Structure

```
news/tests/
├── __init__.py                 # Package initialization
├── README.md                   # This file
├── test_base.py                # Base utilities and fixtures
├── test_models.py              # Model tests (News, Tag)
├── test_views.py               # View tests (list, detail, search, tags, robots.txt)
├── test_search.py              # Search functionality tests
├── test_seo.py                 # SEO feature tests
├── test_urls.py                # URL routing and pattern tests
├── test_integration.py         # End-to-end integration tests
└── test_tags.py                # Legacy tag tests (kept for compatibility)
```

## Running Tests

### Run All Tests

```bash
make test
# or
uv run python manage.py test news.tests
```

### Run Specific Test Module

```bash
uv run python manage.py test news.tests.test_models
uv run python manage.py test news.tests.test_views
uv run python manage.py test news.tests.test_search
uv run python manage.py test news.tests.test_seo
uv run python manage.py test news.tests.test_urls
uv run python manage.py test news.tests.test_integration
```

### Run Specific Test Class

```bash
uv run python manage.py test news.tests.test_models.NewsModelTests
uv run python manage.py test news.tests.test_views.NewsListViewTests
```

### Run Specific Test Method

```bash
uv run python manage.py test news.tests.test_models.NewsModelTests.test_display_title_uses_llm_headline
```

### Run with Verbose Output

```bash
uv run python manage.py test news.tests --verbosity=2
```

## Test Coverage

### Run Tests with Coverage

```bash
coverage run --source='news' manage.py test news.tests
coverage report
coverage html  # Generates HTML report in htmlcov/
```

### Coverage Goals

- **Overall**: 80%+
- **Critical Code** (views, SEO): 100%
- **Business Logic** (models, search): 90%+

## Important Notes

### SQLite vs PostgreSQL

The test suite is designed to work with SQLite (for speed) but the production app uses PostgreSQL. Some PostgreSQL-specific features are not available in SQLite:

**PostgreSQL-only features:**
- `ArrayField` (llm_tags, llm_bullets)
- `VectorField` (content_embedding for pgvector)
- Generated columns (ts_vector_content)
- Array operators (`__contains`)

**Handling in tests:**
- Tests mock PostgreSQL-specific operations
- `test_base.py` provides utilities for SQLite compatibility
- Some tests are skipped when running on SQLite
- Full test coverage requires PostgreSQL test database

### Running Tests with PostgreSQL

To run tests with full PostgreSQL support:

```bash
# Configure test database in settings.py (remove SQLite override for tests)
# Then run:
uv run python manage.py test news.tests
```

## Test Categories

### 1. Model Tests (`test_models.py`)

**Covers:**
- Data integrity (published vs unpublished, deleted filtering)
- Property methods (display_title, display_summary, slug)
- URL generation (get_absolute_url)
- Tag slug generation and uniqueness
- Edge cases (empty fields, long titles, special characters)

**Key Test Classes:**
- `NewsModelTests`
- `TagModelTests`
- `TagManagerTests`

### 2. View Tests (`test_views.py`)

**Covers:**
- HTTP responses and status codes
- Template usage
- Context data
- Pagination (20 per page)
- Filtering (published only, exclude deleted)
- Navigation context preservation
- Rate limiting (search view)

**Key Test Classes:**
- `NewsListViewTests`
- `NewsDetailViewTests`
- `NewsDetailRedirectViewTests`
- `NewsSearchViewTests`
- `TagViewsTests`
- `RobotsTxtViewTests`

### 3. Search Tests (`test_search.py`)

**Covers:**
- Vector search (with mocked embedding service)
- Text search (PostgreSQL FTS)
- Hybrid search (combining both)
- Published/deleted article filtering
- Error handling (embedding service failures)
- Edge cases (empty queries, special characters, SQL injection)

**Key Test Classes:**
- `VectorSearchTests`
- `TextSearchTests`
- `HybridSearchTests`
- `SearchEdgeCasesTests`

### 4. SEO Tests (`test_seo.py`)

**Covers:**
- Sitemap.xml generation and content
- Robots.txt content
- Meta tags (Open Graph, Twitter Cards)
- JSON-LD structured data
- Canonical URLs
- Absolute URL formatting

**Key Test Classes:**
- `SitemapXmlTests`
- `RobotsTxtTests`
- `MetaTagsTests`
- `StructuredDataTests`
- `CanonicalUrlTests`
- `SEOPagesTests`

### 5. URL Tests (`test_urls.py`)

**Covers:**
- URL resolution (reverse lookup)
- URL pattern matching
- Slug generation and validation
- SEO-friendly URL format
- Redirect behavior (301 permanent redirects)
- Edge cases (long slugs, special characters)

**Key Test Classes:**
- `NewsUrlResolutionTests`
- `TagUrlResolutionTests`
- `SeoUrlResolutionTests`
- `UrlGenerationTests`
- `SlugHandlingTests`
- `RedirectTests`
- `UrlPatternTests`

### 6. Integration Tests (`test_integration.py`)

**Covers:**
- Complete user journeys (homepage → article → back)
- Pagination flow preservation
- Tag browsing (tags index → tag → article → back)
- Search flow (search → article → back with context)
- Social sharing (meta tags)
- SEO crawler scenario (robots.txt → sitemap → article)
- Error handling (404s for missing/deleted content)
- Navigation context preservation

**Key Test Classes:**
- `ArticleDiscoveryJourneyTests`
- `TagBrowsingJourneyTests`
- `SearchJourneyTests`
- `SocialSharingScenarioTests`
- `SeoCrawlerScenarioTests`
- `ErrorHandlingJourneyTests`
- `NavigationContextTests`

## Mocking Strategy

### External Services Mocked

**AWS Embedding Service:**
```python
@patch('news.views.get_embedding_service')
def test_vector_search(mock_get_service):
    mock_service = MagicMock()
    mock_service.generate_embedding.return_value = [0.1] * 768
    mock_get_service.return_value = mock_service
    # Test continues...
```

**PostgreSQL-Specific Queries:**
- Array contains operations (`llm_tags__contains`)
- Full-text search (`SearchVector`, `SearchQuery`)
- Vector similarity (`CosineDistance`)

### Database Mocking

Tests use Django's in-memory SQLite database for speed. PostgreSQL-specific features are mocked or skipped.

## Common Test Patterns

### 1. Testing View Responses

```python
def test_news_list_returns_200(self):
    response = self.client.get(reverse('news:list'))
    self.assertEqual(response.status_code, 200)
    self.assertTemplateUsed(response, 'news/news_list.html')
```

### 2. Testing Context Data

```python
def test_news_list_context(self):
    response = self.client.get(reverse('news:list'))
    self.assertIn('news_articles', response.context)
    self.assertIn('page_obj', response.context)
```

### 3. Testing with Mocks

```python
@patch('news.views.get_embedding_service')
def test_vector_search_with_mock(self, mock_service):
    mock_service.return_value.generate_embedding.return_value = [0.1] * 768
    response = self.client.get(reverse('news:search'), {'q': 'AI', 'type': 'vector'})
    self.assertEqual(response.status_code, 200)
```

### 4. Testing Edge Cases

```python
def test_article_with_no_title(self):
    article = News.objects.create(
        title=None,
        llm_headline=None,
        status="published",
        deleted_at=None
    )
    self.assertEqual(article.display_title, f"Article {article.id}")
```

## Test Performance

**Target Times:**
- Individual test: <1 second
- Test module: <5 seconds
- Full test suite: <30 seconds

**Optimization Techniques:**
- Use `setUpTestData()` for shared test data
- Mock external services (AWS, embeddings)
- Use in-memory SQLite for tests
- Minimize database queries

## Known Issues / Limitations

### SQLite Limitations

1. **ArrayField errors**: SQLite doesn't support PostgreSQL array types
   - **Workaround**: Tests set arrays to None or mock array operations

2. **VectorField errors**: SQLite doesn't support pgvector extension
   - **Workaround**: Tests mock embedding-related queries

3. **Generated columns**: SQLite doesn't support `GENERATED ALWAYS AS`
   - **Workaround**: Tests avoid relying on ts_vector_content

4. **Array operators**: `llm_tags__contains` doesn't work in SQLite
   - **Workaround**: Tests mock these queries or use alternatives

### Current Test Results

When running on SQLite (default), some tests will error due to PostgreSQL feature incompatibility. This is expected and documented. The tests are designed to work fully when run against a PostgreSQL test database.

**To get full test coverage:**
1. Configure a PostgreSQL test database in settings.py
2. Remove the SQLite test database override
3. Run tests against PostgreSQL

## Maintenance

### When to Update Tests

- **New features**: Always write tests first (TDD approach)
- **Bug fixes**: Write failing test, then fix bug
- **Refactoring**: Tests ensure behavior unchanged
- **Changing requirements**: Update tests to match new requirements

### Test Review Checklist

Before merging test code:
- [ ] All tests pass
- [ ] New tests cover new functionality
- [ ] Tests have clear, descriptive names
- [ ] No flaky tests (consistent results)
- [ ] Coverage maintained or improved
- [ ] Tests run quickly (<30s total)

## Contributing

When adding new tests:

1. Follow existing test structure and naming conventions
2. Use descriptive test names that explain what's being tested
3. Include docstrings explaining the test purpose
4. Mock external dependencies
5. Handle SQLite limitations appropriately
6. Update this README if adding new test categories

## Resources

- **Testing Plan**: `/TESTING_PLAN.md`
- **Django Testing Docs**: https://docs.djangoproject.com/en/5.2/topics/testing/
- **Project Docs**: `/CLAUDE.md`

---

**Last Updated**: 2025-09-30
**Test Count**: 200+ tests across 6 test modules
**Maintainer**: Development Team
