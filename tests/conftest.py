"""
Shared pytest fixtures for GEO-Perplex tests.
"""
import pytest
import sqlite3
import tempfile
import json
from pathlib import Path
from typing import Generator


@pytest.fixture
def in_memory_db() -> Generator[sqlite3.Connection, None, None]:
    """
    Provides an in-memory SQLite database connection for testing.
    Database is automatically cleaned up after test completes.
    """
    conn = sqlite3.connect(':memory:')
    yield conn
    conn.close()


@pytest.fixture
def temp_auth_file(tmp_path: Path) -> Path:
    """
    Creates a temporary auth.json file with valid test cookies.
    """
    auth_file = tmp_path / "auth.json"
    test_cookies = {
        "pplx.session-id": "test-session-id-123",
        "__Secure-next-auth.session-token": "test-token-456",
        "next-auth.csrf-token": "test-csrf-789",
        "next-auth.callback-url": "https://www.perplexity.ai"
    }
    auth_file.write_text(json.dumps(test_cookies, indent=2))
    return auth_file


@pytest.fixture
def invalid_auth_file(tmp_path: Path) -> Path:
    """
    Creates a temporary auth.json file with missing required cookies.
    """
    auth_file = tmp_path / "auth_invalid.json"
    invalid_cookies = {
        "some-other-cookie": "value"
    }
    auth_file.write_text(json.dumps(invalid_cookies, indent=2))
    return auth_file


@pytest.fixture
def malformed_json_file(tmp_path: Path) -> Path:
    """
    Creates a temporary file with malformed JSON.
    """
    malformed_file = tmp_path / "malformed.json"
    malformed_file.write_text("{ invalid json }")
    return malformed_file


@pytest.fixture
def sample_search_result() -> dict:
    """
    Provides a sample search result for testing.
    """
    return {
        "id": 1,
        "query": "What is GEO?",
        "model": "gpt-4",
        "timestamp": "2025-01-11 14:30:45",
        "answer_text": "GEO stands for Generative Engine Optimization, a technique for optimizing content visibility in generative AI systems.",
        "sources": [
            {"url": "https://example.com/1", "text": "Source 1"},
            {"url": "https://example.com/2", "text": "Source 2"}
        ],
        "screenshot_path": "screenshots/test_20250111_120000_abc123.png",
        "execution_time_seconds": 12.5,
        "success": True,
        "error_message": None
    }


@pytest.fixture
def sample_failed_search_result() -> dict:
    """
    Provides a sample failed search result for testing.
    """
    return {
        "id": 2,
        "query": "Failed query",
        "model": "claude-3",
        "timestamp": "2025-01-11 15:00:00",
        "answer_text": "",  # Empty string instead of None
        "sources": [],      # Empty list instead of None
        "screenshot_path": None,
        "execution_time_seconds": 5.2,
        "success": False,
        "error_message": "Element not found"
    }


@pytest.fixture
def multiple_search_results() -> list:
    """
    Provides multiple search results for testing queries and comparisons.
    """
    return [
        {
            "id": 1,
            "query": "What is Python?",
            "model": "gpt-4",
            "timestamp": "2025-01-11 10:00:00",
            "answer_text": "Python is a high-level programming language...",
            "sources": [{"url": "https://python.org", "text": "Official docs"}],
            "screenshot_path": "screenshots/test1.png",
            "execution_time_seconds": 10.0,
            "success": True,
            "error_message": None
        },
        {
            "id": 2,
            "query": "What is Python?",
            "model": "claude-3",
            "timestamp": "2025-01-11 11:00:00",
            "answer_text": "Python is an interpreted, high-level language...",
            "sources": [{"url": "https://example.com", "text": "Tutorial"}],
            "screenshot_path": "screenshots/test2.png",
            "execution_time_seconds": 11.5,
            "success": True,
            "error_message": None
        },
        {
            "id": 3,
            "query": "What is JavaScript?",
            "model": "gpt-4",
            "timestamp": "2025-01-11 12:00:00",
            "answer_text": "JavaScript is a scripting language...",
            "sources": [{"url": "https://mdn.org", "text": "MDN Web Docs"}],
            "screenshot_path": "screenshots/test3.png",
            "execution_time_seconds": 9.5,
            "success": True,
            "error_message": None
        }
    ]
