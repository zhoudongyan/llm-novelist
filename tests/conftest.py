"""
Pytest configuration file
"""

import pytest
import os
from dotenv import load_dotenv

@pytest.fixture(autouse=True)
def load_test_env():
    """Load test environment variables"""
    # Load .env file if it exists
    env_path = os.path.join(os.path.dirname(__file__), "..", ".env")
    load_dotenv(env_path)

@pytest.fixture
def mock_env_vars(monkeypatch):
    """Set up mock environment variables for testing"""
    test_vars = {
        "STABILITY_API_KEY": "test_stability_key",
        "OPENAI_API_KEY": "test_openai_key",
        "OPENAI_BASE_URL": "https://test.openai.com/v1",
        "LLM_MODEL": "gpt-3.5-turbo",
    }
    
    for key, value in test_vars.items():
        monkeypatch.setenv(key, value) 