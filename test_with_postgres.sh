#!/bin/bash

# Test with Temporary PostgreSQL Container
# Spins up PostgreSQL on non-standard port, runs tests, tears down

set -e  # Exit on error

# Configuration
CONTAINER_NAME="ainews-test-postgres"
POSTGRES_PORT="54320"  # Non-standard port to avoid conflicts
POSTGRES_PASSWORD="test_password_123"
POSTGRES_DB="test_ainews"
POSTGRES_USER="testuser"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}============================================${NC}"
echo -e "${BLUE}Django News App - PostgreSQL Test Runner${NC}"
echo -e "${BLUE}============================================${NC}"
echo ""

# Cleanup function
cleanup() {
    echo ""
    echo -e "${YELLOW}🧹 Cleaning up...${NC}"

    # Stop and remove container
    docker stop "$CONTAINER_NAME" 2>/dev/null || true
    docker rm "$CONTAINER_NAME" 2>/dev/null || true
    echo -e "${GREEN}✅ Cleanup complete${NC}"
}

# Set trap to cleanup on exit
trap cleanup EXIT INT TERM

# Check if docker is running
if ! docker info > /dev/null 2>&1; then
    echo -e "${RED}❌ Docker is not running. Please start Docker first.${NC}"
    exit 1
fi

# Check if port is available
if lsof -Pi :$POSTGRES_PORT -sTCP:LISTEN -t >/dev/null 2>&1; then
    echo -e "${RED}❌ Port $POSTGRES_PORT is already in use${NC}"
    echo "   Please stop the service using this port or change POSTGRES_PORT in this script"
    exit 1
fi

# Stop and remove any existing container with same name
echo -e "${YELLOW}🔍 Checking for existing container...${NC}"
if docker ps -a --format '{{.Names}}' | grep -q "^${CONTAINER_NAME}$"; then
    echo -e "${YELLOW}   Removing existing container...${NC}"
    docker stop "$CONTAINER_NAME" 2>/dev/null || true
    docker rm "$CONTAINER_NAME" 2>/dev/null || true
fi

# Start PostgreSQL container with pgvector extension
echo -e "${BLUE}🚀 Starting PostgreSQL container...${NC}"
echo "   Image: pgvector/pgvector:pg16"
echo "   Port: $POSTGRES_PORT"
echo "   Database: $POSTGRES_DB"
echo "   User: $POSTGRES_USER"
echo ""

docker run -d \
    --name "$CONTAINER_NAME" \
    -e POSTGRES_USER="$POSTGRES_USER" \
    -e POSTGRES_PASSWORD="$POSTGRES_PASSWORD" \
    -e POSTGRES_DB="$POSTGRES_DB" \
    -p "$POSTGRES_PORT:5432" \
    pgvector/pgvector:pg16 \
    > /dev/null

echo -e "${GREEN}✅ Container started${NC}"
echo ""

# Wait for PostgreSQL to be ready
echo -e "${YELLOW}⏳ Waiting for PostgreSQL to be ready...${NC}"
MAX_TRIES=30
TRIES=0

while [ $TRIES -lt $MAX_TRIES ]; do
    if docker exec "$CONTAINER_NAME" pg_isready -U "$POSTGRES_USER" > /dev/null 2>&1; then
        echo -e "${GREEN}✅ PostgreSQL is ready${NC}"
        break
    fi
    TRIES=$((TRIES+1))
    echo -n "."
    sleep 1
done

if [ $TRIES -eq $MAX_TRIES ]; then
    echo -e "${RED}❌ PostgreSQL failed to start in time${NC}"
    exit 1
fi

echo ""

# Create test database settings
echo -e "${BLUE}⚙️  Configuring test environment...${NC}"

# Export environment variables for Django
export POSTGRES_HOST="localhost"
export POSTGRES_PORT="$POSTGRES_PORT"
export POSTGRES_USER="$POSTGRES_USER"
export POSTGRES_PASSWORD="$POSTGRES_PASSWORD"
export POSTGRES_DB="$POSTGRES_DB"
export TEST_WITH_POSTGRES="1"

echo -e "${GREEN}✅ Environment configured${NC}"
echo ""

# Run migrations
echo -e "${BLUE}🔄 Running migrations...${NC}"
uv run python manage.py migrate --no-input 2>&1 | grep -E "(Applying|Operations)" || true
echo -e "${GREEN}✅ Migrations complete${NC}"
echo ""

# Run tests with coverage
echo -e "${BLUE}============================================${NC}"
echo -e "${BLUE}🧪 Running Tests with Coverage${NC}"
echo -e "${BLUE}============================================${NC}"
echo ""

uv run coverage run --source='news' manage.py test news.tests --verbosity=2

# Capture exit code
TEST_EXIT_CODE=$?

echo ""
echo -e "${BLUE}============================================${NC}"
echo -e "${BLUE}📊 Test Results${NC}"
echo -e "${BLUE}============================================${NC}"
echo ""

if [ $TEST_EXIT_CODE -eq 0 ]; then
    echo -e "${GREEN}✅ All tests passed!${NC}"
else
    echo -e "${RED}❌ Some tests failed (exit code: $TEST_EXIT_CODE)${NC}"
fi

echo ""
echo -e "${BLUE}============================================${NC}"
echo -e "${BLUE}📈 Code Coverage Report${NC}"
echo -e "${BLUE}============================================${NC}"
echo ""

# Generate coverage report
uv run coverage report

echo ""
echo -e "${YELLOW}💡 Tip: Run 'uv run coverage html' for detailed HTML report${NC}"
echo ""

# Cleanup happens automatically via trap

exit $TEST_EXIT_CODE
