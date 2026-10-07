import sys
import os

TEST_DATABASE_URL = os.getenv("TEST_DATABASE_URL")
if not TEST_DATABASE_URL or "disaster_db" not in TEST_DATABASE_URL:
    print("ERROR: TEST_DATABASE_URL is missing or does not look like a test database.")
    print("Example: postgresql://user:pass@localhost:5432/disaster_db_test")
    sys.exit(1)

if "production" in TEST_DATABASE_URL.lower():
    print("ERROR: Refusing to run tests against production database.")
    sys.exit(1)

print("Starting integration tests against:", TEST_DATABASE_URL)
# Run pytest on the tests directory
import pytest
sys.exit(pytest.main(["src/backend/tests/test_integration.py"]))

