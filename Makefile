# Django Makefile for ainews project
# Common Django development tasks

.PHONY: help install run migrate makemigrations shell test lint format clean clear-cache superuser build-css watch-css prod-check coverage coverage-html test-e2e test-e2e-headless test-e2e-chromium test-e2e-firefox test-e2e-webkit test-all

# Default target
help:
	@echo "Available commands:"
	@echo ""
	@echo "Development:"
	@echo "  install         - Install dependencies"
	@echo "  setup           - First-time setup (install + migrate)"
	@echo "  run             - Start development server (port 8300)"
	@echo "  migrate         - Apply database migrations"
	@echo "  makemigrations  - Create new migrations"
	@echo "  shell           - Open Django shell"
	@echo "  superuser       - Create Django superuser"
	@echo ""
	@echo "Testing & Quality:"
	@echo "  test              - Run full test suite (PostgreSQL with Docker)"
	@echo "  test-postgres     - Run PostgreSQL test suite (232 tests, ~3s)"
	@echo "  test-sqlite       - Run SQLite smoke tests (22 tests, ~0.2s)"
	@echo "  test-e2e          - Run E2E tests with Playwright (headed mode)"
	@echo "  test-e2e-headless - Run E2E tests headless (CI mode)"
	@echo "  test-e2e-chromium - Run E2E tests in Chromium only"
	@echo "  test-e2e-firefox  - Run E2E tests in Firefox only"
	@echo "  test-e2e-webkit   - Run E2E tests in WebKit only"
	@echo "  test-all          - Run ALL tests (unit + E2E)"
	@echo "  coverage          - Run tests with coverage report"
	@echo "  coverage-html     - Generate detailed HTML coverage report"
	@echo "  lint              - Run linting (ruff)"
	@echo "  typecheck         - Run type checking (mypy)"
	@echo "  format            - Format code (black + ruff --fix)"
	@echo "  check             - Run Django system checks"
	@echo "  prod-check        - Run ALL quality checks (format, lint, typecheck, test)"
	@echo ""
	@echo "Assets:"
	@echo "  build-css       - Build theme CSS (production)"
	@echo "  watch-css       - Watch and rebuild CSS on changes (development)"
	@echo ""
	@echo "Utilities:"
	@echo "  clean           - Clean up temporary files"
	@echo "  clear-cache     - Clear Python, Django, and static file caches"

# Install dependencies
install:
	uv sync

# Start development server
run:
	uv run python manage.py runserver 8300

# Apply database migrations
migrate:
	uv run python manage.py migrate

# Create new migrations
makemigrations:
	uv run python manage.py makemigrations

# Open Django shell
shell:
	uv run python manage.py shell

# Run tests (defaults to PostgreSQL)
test: test-postgres

# Run PostgreSQL test suite (full 232 tests)
test-postgres:
	@./test_with_postgres.sh

# Run SQLite smoke test suite (fast, 22 tests)
test-sqlite:
	@echo "Running SQLite smoke tests..."
	@RATELIMIT_ENABLE=False uv run python manage.py test news.tests.sqlite --verbosity=2

# Run linting
lint:
	uv run ruff check .

# Run type checking
typecheck:
	uv run mypy .

# Format code
format:
	uv run black .
	uv run ruff check --fix .

# Create Django superuser
superuser:
	uv run python manage.py createsuperuser

# Build theme CSS
build-css:
	cd theme/static_src && npm run build

# Watch and rebuild CSS on changes (development)
watch-css:
	cd theme/static_src && npm run dev

# Clean up temporary files
clean:
	find . -type f -name "*.pyc" -delete
	find . -type d -name "__pycache__" -delete
	find . -type d -name "*.egg-info" -exec rm -rf {} +
	rm -rf .pytest_cache
	rm -rf .coverage

# Run Django system checks
check:
	uv run python manage.py check

# Development setup (run this first time)
setup: install migrate
	@echo "Setup complete! Run 'make run' to start the development server on port 8300."

# Run tests with coverage report
coverage:
	@echo "Running tests with coverage..."
	@uv run coverage run --source='news' manage.py test news.tests
	@echo ""
	@echo "Coverage Report:"
	@uv run coverage report
	@echo ""
	@echo "💡 Run 'make coverage-html' for detailed HTML report"

# Generate HTML coverage report
coverage-html:
	@uv run coverage run --source='news' manage.py test news.tests
	@uv run coverage html
	@echo "✅ HTML coverage report generated in htmlcov/index.html"
	@echo "💡 Open htmlcov/index.html in your browser"

# Clear various caches (Python, Django, static files)
clear-cache:
	@echo "Clearing caches..."
	@find . -name "*.pyc" -delete 2>/dev/null || true
	@find . -name "__pycache__" -type d -exec rm -rf {} + 2>/dev/null || true
	@uv run python manage.py shell -c "from django.core.cache import cache; cache.clear()" 2>/dev/null || echo "Django cache cleared (if available)"
	@uv run python manage.py collectstatic --noinput --clear 2>/dev/null || echo "Static files refreshed"

# Run E2E tests with Playwright (headed mode, shows browser)
test-e2e: clear-cache
	@echo "Running E2E tests with Playwright (headed mode)..."
	@RATELIMIT_ENABLE=False uv run pytest tests/e2e/ --headed --browser chromium --slowmo 100

# Run E2E tests in headless mode (for CI/CD)
test-e2e-headless: clear-cache
	@echo "Running E2E tests with Playwright (headless mode)..."
	@RATELIMIT_ENABLE=False uv run pytest tests/e2e/ --browser chromium

# Run E2E tests in Chromium only
test-e2e-chromium: clear-cache
	@echo "Running E2E tests in Chromium..."
	@RATELIMIT_ENABLE=False uv run pytest tests/e2e/ --browser chromium

# Run E2E tests in Firefox only
test-e2e-firefox: clear-cache
	@echo "Running E2E tests in Firefox..."
	@RATELIMIT_ENABLE=False uv run pytest tests/e2e/ --browser firefox

# Run E2E tests in WebKit only
test-e2e-webkit: clear-cache
	@echo "Running E2E tests in WebKit..."
	@RATELIMIT_ENABLE=False uv run pytest tests/e2e/ --browser webkit

# Run ALL tests (unit + E2E)
test-all:
	@echo "========================================"
	@echo "Running ALL Tests (Unit + E2E)"
	@echo "========================================"
	@echo ""
	@echo "1/2 Running Django Unit Tests..."
	@$(MAKE) test-postgres || (echo "❌ Unit tests failed!" && exit 1)
	@echo ""
	@echo "2/2 Running E2E Tests..."
	@$(MAKE) test-e2e-headless || (echo "❌ E2E tests failed!" && exit 1)
	@echo ""
	@echo "========================================"
	@echo "✅ All Tests Passed!"
	@echo "========================================"

# Production-ready checks (runs all quality checks in order)
prod-check:
	@echo "========================================"
	@echo "Running Production Readiness Checks"
	@echo "========================================"
	@echo ""
	@echo "1/5 Django System Checks..."
	@$(MAKE) check || (echo "❌ Django system checks failed!" && exit 1)
	@echo ""
	@echo "2/5 Code Formatting Check..."
	@uv run black --check . || (echo "❌ Code formatting check failed! Run 'make format' to fix." && exit 1)
	@echo ""
	@echo "3/5 Linting (ruff)..."
	@$(MAKE) lint || (echo "❌ Linting failed! Run 'make format' to auto-fix." && exit 1)
	@echo ""
	@echo "4/5 Type Checking (mypy)..."
	@$(MAKE) typecheck || (echo "❌ Type checking failed!" && exit 1)
	@echo ""
	@echo "5/5 Running Test Suite..."
	@$(MAKE) test || (echo "❌ Tests failed!" && exit 1)
	@echo ""
	@echo "========================================"
	@echo "✅ All Production Checks Passed!"
	@echo "========================================"
