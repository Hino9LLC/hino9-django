# E2E Tests

End-to-end tests using Playwright for the ainews news platform.

## Quick Start

```bash
# Run E2E tests (shows browser)
make test-e2e

# Run headless (faster)
make test-e2e-headless

# Run all tests (unit + E2E)
make test-all
```

## Test Files

- **`test_article_journey.py`** - Article navigation and context preservation
- **`test_search_flows.py`** - Search functionality (vector, text, hybrid)
- **`test_navigation.py`** - Navigation, tags, breadcrumbs, accessibility

## Documentation

See [E2E_TESTING.md](../../E2E_TESTING.md) for comprehensive documentation.

## Key Commands

```bash
# Run specific test file
uv run pytest tests/e2e/test_search_flows.py

# Run specific test
uv run pytest tests/e2e/test_search_flows.py::test_basic_search_flow

# Run with specific browser
uv run pytest tests/e2e/ --browser firefox

# Debug mode (slow motion, pause on failure)
uv run pytest tests/e2e/ --headed --slowmo 1000 --pdb
```

## Test Organization

Tests use pytest markers for filtering:

- `@pytest.mark.search` - Search-related tests
- `@pytest.mark.navigation` - Navigation tests
- `@pytest.mark.mobile` - Mobile viewport tests
- `@pytest.mark.visual` - Visual regression tests
- `@pytest.mark.slow` - Slow-running tests

```bash
# Run only search tests
pytest tests/e2e/ -m search

# Skip slow tests
pytest tests/e2e/ -m "not slow"
```
