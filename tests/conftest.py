import pytest
import json
from pathlib import Path

@pytest.fixture
def sample_data():
    """Load sample test data."""
    fixtures_path = Path(__file__).parent / "fixtures" / "sample_data.json"
    with open(fixtures_path) as f:
        return json.load(f)

@pytest.fixture
def temp_file(tmp_path):
    """Create a temporary file for testing."""
    file_path = tmp_path / "test_file.txt"
    file_path.write_text("test content")
    return file_path

@pytest.fixture(scope="session")
def database_url():
    """Database URL for integration tests."""
    return "sqlite:///:memory:"
