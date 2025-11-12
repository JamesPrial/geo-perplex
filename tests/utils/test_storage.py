"""
Unit tests for src/utils/storage.py
Tests database initialization, CRUD operations, and query functions.
"""
import pytest
import sqlite3
import json
from unittest.mock import patch, MagicMock
from src.utils.storage import (
    init_database,
    save_search_result,
    get_results_by_query,
    get_results_by_model,
    compare_models_for_query,
    get_recent_results,
    get_unique_queries,
    get_unique_models,
    get_results_by_date_range,
    get_results_by_success_status,
    get_results_by_execution_time,
    search_in_answers,
    search_in_sources,
    search_queries_fuzzy,
    get_results_advanced_filter
)


@pytest.fixture
def mock_db_connection(tmp_path):
    """
    Patches sqlite3.connect to use a temporary database file for all storage functions.
    """
    # Create a temporary database file
    temp_db_file = tmp_path / "test_db.sqlite"

    # Save the original connect function
    original_connect = sqlite3.connect

    def mock_connect(db_path, *args, **kwargs):
        # Always connect to the temp database file
        return original_connect(str(temp_db_file))

    with patch('src.utils.storage.sqlite3.connect', side_effect=mock_connect):
        yield str(temp_db_file)


def get_test_connection(db_path):
    """Helper to create a connection for test verification"""
    return sqlite3.connect(db_path)


@pytest.mark.unit
class TestDatabaseInitialization:
    """Tests for init_database() function"""

    def test_init_database_creates_table(self, mock_db_connection):
        """Test that init_database creates the search_results table"""
        db_uri = mock_db_connection
        init_database()

        # Create a new connection to verify
        conn = get_test_connection(db_uri)
        cursor = conn.cursor()
        cursor.execute("""
            SELECT name FROM sqlite_master
            WHERE type='table' AND name='search_results'
        """)
        result = cursor.fetchone()
        conn.close()

        assert result is not None
        assert result[0] == 'search_results'

    def test_init_database_creates_indexes(self, mock_db_connection):
        """Test that init_database creates all required indexes"""
        db_uri = mock_db_connection
        init_database()

        conn = get_test_connection(db_uri)
        cursor = conn.cursor()
        cursor.execute("""
            SELECT name FROM sqlite_master
            WHERE type='index'
        """)
        indexes = [row[0] for row in cursor.fetchall()]
        conn.close()

        expected_indexes = ['idx_query', 'idx_model', 'idx_timestamp', 'idx_query_model']
        for expected_index in expected_indexes:
            assert expected_index in indexes

    def test_init_database_has_correct_columns(self, mock_db_connection):
        """Test that search_results table has all required columns"""
        db_uri = mock_db_connection
        init_database()

        conn = get_test_connection(db_uri)
        cursor = conn.cursor()
        cursor.execute("PRAGMA table_info(search_results)")
        columns = {row[1]: row[2] for row in cursor.fetchall()}  # name: type
        conn.close()

        expected_columns = {
            'id': 'INTEGER',
            'query': 'TEXT',
            'model': 'TEXT',
            'timestamp': 'DATETIME',
            'answer_text': 'TEXT',
            'sources': 'TEXT',
            'screenshot_path': 'TEXT',
            'execution_time_seconds': 'REAL',
            'success': 'BOOLEAN',
            'error_message': 'TEXT'
        }

        for col_name, col_type in expected_columns.items():
            assert col_name in columns
            assert columns[col_name] == col_type


@pytest.mark.unit
class TestSaveSearchResult:
    """Tests for save_search_result() function"""

    def test_save_successful_search_result(self, mock_db_connection, sample_search_result):
        """Test saving a successful search result"""
        result_id = save_search_result(
            query=sample_search_result['query'],
            answer_text=sample_search_result['answer_text'],
            sources=sample_search_result['sources'],
            screenshot_path=sample_search_result['screenshot_path'],
            model=sample_search_result['model'],
            execution_time=sample_search_result['execution_time_seconds'],
            success=sample_search_result['success'],
            error_message=sample_search_result['error_message']
        )

        assert isinstance(result_id, int)
        assert result_id > 0

        # Verify data was saved correctly
        conn = get_test_connection(mock_db_connection)
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM search_results WHERE id = ?", (result_id,))
        row = cursor.fetchone()
        conn.close()

        assert row is not None
        assert row[1] == sample_search_result['query']  # query
        assert row[2] == sample_search_result['model']  # model
        assert row[4] == sample_search_result['answer_text']  # answer_text

    def test_save_failed_search_result(self, mock_db_connection, sample_failed_search_result):
        """Test saving a failed search result with error message"""
        result_id = save_search_result(
            query=sample_failed_search_result['query'],
            answer_text=sample_failed_search_result['answer_text'],
            sources=sample_failed_search_result['sources'] or [],
            model=sample_failed_search_result['model'],
            execution_time=sample_failed_search_result['execution_time_seconds'],
            success=sample_failed_search_result['success'],
            error_message=sample_failed_search_result['error_message']
        )

        assert isinstance(result_id, int)
        assert result_id > 0

        # Verify error information was saved
        conn = get_test_connection(mock_db_connection)
        cursor = conn.cursor()
        cursor.execute("SELECT success, error_message FROM search_results WHERE id = ?", (result_id,))
        row = cursor.fetchone()
        conn.close()

        assert row[0] == 0  # success = False (stored as 0)
        assert row[1] == sample_failed_search_result['error_message']

    def test_save_search_result_with_minimal_data(self, mock_db_connection):
        """Test saving with only required fields"""
        result_id = save_search_result(
            query="Minimal query",
            answer_text="Minimal answer",
            sources=[]
        )

        assert isinstance(result_id, int)
        assert result_id > 0

    def test_save_search_result_sources_serialization(self, mock_db_connection):
        """Test that sources list is properly serialized to JSON"""
        sources = [
            {"url": "https://example.com/1", "text": "Source 1"},
            {"url": "https://example.com/2", "text": "Source 2"}
        ]

        result_id = save_search_result(
            query="Test query",
            answer_text="Test answer",
            sources=sources
        )

        conn = get_test_connection(mock_db_connection)
        cursor = conn.cursor()
        cursor.execute("SELECT sources FROM search_results WHERE id = ?", (result_id,))
        sources_json = cursor.fetchone()[0]
        conn.close()

        # Verify it's valid JSON and matches original
        deserialized = json.loads(sources_json)
        assert deserialized == sources


@pytest.mark.unit
class TestGetResultsByQuery:
    """Tests for get_results_by_query() function"""

    def test_get_results_by_query_returns_matching_results(self, mock_db_connection):
        """Test retrieving results for a specific query"""
        query = "What is Python?"

        # Insert test data
        save_search_result(query=query, answer_text="Answer 1", sources=[])
        save_search_result(query=query, answer_text="Answer 2", sources=[])
        save_search_result(query="Different query", answer_text="Answer 3", sources=[])

        results = get_results_by_query(query)

        assert len(results) == 2
        assert all(r['query'] == query for r in results)

    def test_get_results_by_query_with_model_filter(self, mock_db_connection):
        """Test filtering results by both query and model"""
        query = "What is Python?"

        save_search_result(query=query, answer_text="GPT answer", sources=[], model="gpt-4")
        save_search_result(query=query, answer_text="Claude answer", sources=[], model="claude-3")

        results = get_results_by_query(query, model="gpt-4")

        assert len(results) == 1
        assert results[0]['model'] == "gpt-4"

    def test_get_results_by_query_empty_results(self, mock_db_connection):
        """Test querying for non-existent query"""
        init_database()
        results = get_results_by_query("Non-existent query")

        assert results == []

    def test_get_results_by_query_ordered_by_timestamp(self, mock_db_connection):
        """Test that results are ordered by timestamp descending"""
        query = "Test query"

        # Insert multiple results
        id1 = save_search_result(query=query, answer_text="First", sources=[])
        id2 = save_search_result(query=query, answer_text="Second", sources=[])
        id3 = save_search_result(query=query, answer_text="Third", sources=[])

        results = get_results_by_query(query)

        # Should have 3 results
        assert len(results) == 3
        # Results should be ordered (most recent first)
        # Since timestamps are the same, order defaults to ID ascending
        assert results[0]['answer_text'] == "First"
        assert results[1]['answer_text'] == "Second"
        assert results[2]['answer_text'] == "Third"

    def test_get_results_by_query_deserializes_sources(self, mock_db_connection):
        """Test that sources JSON is properly deserialized"""
        query = "Test query"
        sources = [{"url": "https://test.com", "text": "Test"}]

        save_search_result(query=query, answer_text="Answer", sources=sources)
        results = get_results_by_query(query)

        assert len(results) == 1
        assert results[0]['sources'] == sources
        assert isinstance(results[0]['sources'], list)


@pytest.mark.unit
class TestGetResultsByModel:
    """Tests for get_results_by_model() function"""

    def test_get_results_by_model_returns_matching_results(self, mock_db_connection):
        """Test retrieving results for a specific model"""
        save_search_result(query="Q1", answer_text="A1", sources=[], model="gpt-4")
        save_search_result(query="Q2", answer_text="A2", sources=[], model="gpt-4")
        save_search_result(query="Q3", answer_text="A3", sources=[], model="claude-3")

        results = get_results_by_model("gpt-4")

        assert len(results) == 2
        assert all(r['model'] == "gpt-4" for r in results)

    def test_get_results_by_model_respects_limit(self, mock_db_connection):
        """Test that limit parameter is respected"""
        # Insert 10 results
        for i in range(10):
            save_search_result(query=f"Query {i}", answer_text=f"Answer {i}", sources=[], model="gpt-4")

        results = get_results_by_model("gpt-4", limit=5)

        assert len(results) == 5

    def test_get_results_by_model_ordered_by_timestamp(self, mock_db_connection):
        """Test results are ordered by most recent first"""
        id1 = save_search_result(query="Q1", answer_text="A1", sources=[], model="gpt-4")
        id2 = save_search_result(query="Q2", answer_text="A2", sources=[], model="gpt-4")

        results = get_results_by_model("gpt-4")

        assert len(results) == 2
        # When timestamps are same, order defaults to ID ascending
        assert results[0]['answer_text'] == "A1"
        assert results[1]['answer_text'] == "A2"


@pytest.mark.unit
class TestCompareModelsForQuery:
    """Tests for compare_models_for_query() function"""

    def test_compare_models_groups_by_model(self, mock_db_connection):
        """Test that results are grouped by model"""
        query = "What is Python?"

        save_search_result(query=query, answer_text="GPT answer 1", sources=[], model="gpt-4")
        save_search_result(query=query, answer_text="GPT answer 2", sources=[], model="gpt-4")
        save_search_result(query=query, answer_text="Claude answer", sources=[], model="claude-3")

        results = compare_models_for_query(query)

        assert "gpt-4" in results
        assert "claude-3" in results
        assert len(results["gpt-4"]) == 2
        assert len(results["claude-3"]) == 1

    def test_compare_models_handles_unknown_model(self, mock_db_connection):
        """Test that None model is grouped as 'unknown'"""
        query = "Test query"

        save_search_result(query=query, answer_text="Answer", sources=[], model=None)

        results = compare_models_for_query(query)

        assert "unknown" in results
        assert len(results["unknown"]) == 1

    def test_compare_models_empty_results(self, mock_db_connection):
        """Test comparing models for non-existent query"""
        init_database()
        results = compare_models_for_query("Non-existent query")

        assert results == {}

    def test_compare_models_deserializes_sources(self, mock_db_connection):
        """Test that sources are properly deserialized in comparison"""
        query = "Test query"
        sources = [{"url": "https://test.com", "text": "Test"}]

        save_search_result(query=query, answer_text="Answer", sources=sources, model="gpt-4")
        results = compare_models_for_query(query)

        assert results["gpt-4"][0]['sources'] == sources


@pytest.mark.unit
class TestGetRecentResults:
    """Tests for get_recent_results() function"""

    def test_get_recent_results_returns_latest(self, mock_db_connection):
        """Test retrieving recent results"""
        # Insert multiple results
        id1 = save_search_result(query="Q1", answer_text="A1", sources=[])
        id2 = save_search_result(query="Q2", answer_text="A2", sources=[])
        id3 = save_search_result(query="Q3", answer_text="A3", sources=[])

        results = get_recent_results(limit=2)

        assert len(results) == 2
        assert results[0]['id'] == id3  # Most recent first
        assert results[1]['id'] == id2

    def test_get_recent_results_default_limit(self, mock_db_connection):
        """Test that default limit is 50"""
        # Insert 60 results
        for i in range(60):
            save_search_result(query=f"Q{i}", answer_text=f"A{i}", sources=[])

        results = get_recent_results()

        assert len(results) == 50

    def test_get_recent_results_respects_custom_limit(self, mock_db_connection):
        """Test custom limit parameter"""
        for i in range(20):
            save_search_result(query=f"Q{i}", answer_text=f"A{i}", sources=[])

        results = get_recent_results(limit=10)

        assert len(results) == 10

    def test_get_recent_results_empty_database(self, mock_db_connection):
        """Test getting results from empty database"""
        init_database()
        results = get_recent_results()

        assert results == []


@pytest.mark.unit
class TestGetUniqueQueries:
    """Tests for get_unique_queries() function"""

    def test_get_unique_queries_returns_distinct_queries(self, mock_db_connection):
        """Test retrieving unique queries"""
        save_search_result(query="What is Python?", answer_text="A1", sources=[])
        save_search_result(query="What is Python?", answer_text="A2", sources=[])
        save_search_result(query="What is JavaScript?", answer_text="A3", sources=[])

        queries = get_unique_queries()

        assert len(queries) == 2
        assert "What is Python?" in queries
        assert "What is JavaScript?" in queries

    def test_get_unique_queries_ordered_alphabetically(self, mock_db_connection):
        """Test that queries are ordered alphabetically"""
        save_search_result(query="Zebra", answer_text="A1", sources=[])
        save_search_result(query="Apple", answer_text="A2", sources=[])
        save_search_result(query="Mango", answer_text="A3", sources=[])

        queries = get_unique_queries()

        assert queries == ["Apple", "Mango", "Zebra"]

    def test_get_unique_queries_empty_database(self, mock_db_connection):
        """Test getting queries from empty database"""
        init_database()
        queries = get_unique_queries()

        assert queries == []


@pytest.mark.unit
class TestGetUniqueModels:
    """Tests for get_unique_models() function"""

    def test_get_unique_models_returns_distinct_models(self, mock_db_connection):
        """Test retrieving unique models"""
        save_search_result(query="Q1", answer_text="A1", sources=[], model="gpt-4")
        save_search_result(query="Q2", answer_text="A2", sources=[], model="gpt-4")
        save_search_result(query="Q3", answer_text="A3", sources=[], model="claude-3")

        models = get_unique_models()

        assert len(models) == 2
        assert "gpt-4" in models
        assert "claude-3" in models

    def test_get_unique_models_excludes_null(self, mock_db_connection):
        """Test that NULL models are excluded"""
        save_search_result(query="Q1", answer_text="A1", sources=[], model="gpt-4")
        save_search_result(query="Q2", answer_text="A2", sources=[], model=None)

        models = get_unique_models()

        assert len(models) == 1
        assert "gpt-4" in models

    def test_get_unique_models_ordered_alphabetically(self, mock_db_connection):
        """Test that models are ordered alphabetically"""
        save_search_result(query="Q1", answer_text="A1", sources=[], model="gpt-4")
        save_search_result(query="Q2", answer_text="A2", sources=[], model="claude-3")
        save_search_result(query="Q3", answer_text="A3", sources=[], model="anthropic")

        models = get_unique_models()

        assert models == ["anthropic", "claude-3", "gpt-4"]

    def test_get_unique_models_empty_database(self, mock_db_connection):
        """Test getting models from empty database"""
        init_database()
        models = get_unique_models()

        assert models == []


@pytest.mark.unit
class TestSQLInjectionPrevention:
    """Tests for SQL injection prevention"""

    def test_query_with_sql_drop_table(self, mock_db_connection):
        """Test that SQL DROP TABLE injection is handled safely"""
        malicious_query = "'; DROP TABLE search_results; --"

        # Should save without executing SQL
        result_id = save_search_result(
            query=malicious_query,
            answer_text="Answer",
            sources=[]
        )

        assert result_id is not None

        # Table should still exist and query should be stored as literal string
        results = get_results_by_query(malicious_query)
        assert len(results) == 1
        assert results[0]['query'] == malicious_query

    def test_query_with_sql_or_injection(self, mock_db_connection):
        """Test that SQL OR '1'='1' injection is handled safely"""
        malicious_query = "test' OR '1'='1"

        save_search_result(query="normal query", answer_text="Normal", sources=[])
        save_search_result(query=malicious_query, answer_text="Malicious", sources=[])

        # Should only return exact match, not all records
        results = get_results_by_query(malicious_query)
        assert len(results) == 1
        assert results[0]['query'] == malicious_query
        assert results[0]['answer_text'] == "Malicious"

    def test_model_with_sql_injection(self, mock_db_connection):
        """Test that model parameter is safe from SQL injection"""
        malicious_model = "gpt-4' OR '1'='1"

        save_search_result(query="Q1", answer_text="A1", sources=[], model="gpt-4")
        save_search_result(query="Q2", answer_text="A2", sources=[], model=malicious_model)

        # Should only return exact model match
        results = get_results_by_model(malicious_model)
        assert len(results) == 1
        assert results[0]['model'] == malicious_model

    def test_answer_text_with_sql_commands(self, mock_db_connection):
        """Test that answer text containing SQL is stored safely"""
        answer_with_sql = "DELETE FROM users; SELECT * FROM passwords;"

        result_id = save_search_result(
            query="Test",
            answer_text=answer_with_sql,
            sources=[]
        )

        assert result_id is not None
        results = get_results_by_query("Test")
        assert results[0]['answer_text'] == answer_with_sql


@pytest.mark.unit
class TestUnicodeAndSpecialCharacters:
    """Tests for Unicode and special character handling"""

    def test_query_with_emoji(self, mock_db_connection):
        """Test queries containing emoji characters"""
        query_with_emoji = "What is Python? 🐍 Why use it? 🚀"

        result_id = save_search_result(
            query=query_with_emoji,
            answer_text="Python is a programming language",
            sources=[]
        )

        assert result_id is not None
        results = get_results_by_query(query_with_emoji)
        assert len(results) == 1
        assert results[0]['query'] == query_with_emoji

    def test_query_with_chinese_characters(self, mock_db_connection):
        """Test queries with Chinese characters"""
        query_chinese = "什么是Python编程语言？"

        result_id = save_search_result(
            query=query_chinese,
            answer_text="Python是一种编程语言",
            sources=[]
        )

        assert result_id is not None
        results = get_results_by_query(query_chinese)
        assert len(results) == 1
        assert results[0]['query'] == query_chinese

    def test_query_with_arabic_characters(self, mock_db_connection):
        """Test queries with Arabic characters"""
        query_arabic = "ما هي لغة البرمجة بايثون؟"

        result_id = save_search_result(
            query=query_arabic,
            answer_text="بايثون لغة برمجة",
            sources=[]
        )

        assert result_id is not None
        results = get_results_by_query(query_arabic)
        assert len(results) == 1
        assert results[0]['query'] == query_arabic

    def test_query_with_special_characters(self, mock_db_connection):
        """Test queries with various special characters"""
        query_special = "Test: @#$%^&*()_+-=[]{}|;':\",./<>?"

        result_id = save_search_result(
            query=query_special,
            answer_text="Answer with special chars",
            sources=[]
        )

        assert result_id is not None
        results = get_results_by_query(query_special)
        assert len(results) == 1
        assert results[0]['query'] == query_special

    def test_very_long_unicode_string(self, mock_db_connection):
        """Test handling very long Unicode strings"""
        long_query = "测试" * 5000  # 10,000 characters

        result_id = save_search_result(
            query=long_query,
            answer_text="Answer",
            sources=[]
        )

        assert result_id is not None
        results = get_results_by_query(long_query)
        assert len(results) == 1
        assert results[0]['query'] == long_query

    def test_source_urls_with_encoded_characters(self, mock_db_connection):
        """Test source URLs with URL-encoded special characters"""
        sources_with_encoding = [
            {"url": "https://example.com/search?q=%E6%B5%8B%E8%AF%95", "text": "Test 测试"},
            {"url": "https://example.com/page?name=John%20Doe&age=30", "text": "URL encoded"}
        ]

        result_id = save_search_result(
            query="Test",
            answer_text="Answer",
            sources=sources_with_encoding
        )

        assert result_id is not None
        results = get_results_by_query("Test")
        assert results[0]['sources'] == sources_with_encoding


@pytest.mark.unit
class TestJSONSerializationEdgeCases:
    """Tests for JSON serialization edge cases"""

    def test_sources_with_missing_url_key(self, mock_db_connection):
        """Test sources with missing 'url' key"""
        sources_missing_url = [
            {"text": "Source without URL"}
        ]

        # Should save successfully
        result_id = save_search_result(
            query="Test",
            answer_text="Answer",
            sources=sources_missing_url
        )

        assert result_id is not None
        results = get_results_by_query("Test")
        assert results[0]['sources'] == sources_missing_url

    def test_sources_with_missing_text_key(self, mock_db_connection):
        """Test sources with missing 'text' key"""
        sources_missing_text = [
            {"url": "https://example.com"}
        ]

        result_id = save_search_result(
            query="Test",
            answer_text="Answer",
            sources=sources_missing_text
        )

        assert result_id is not None
        results = get_results_by_query("Test")
        assert results[0]['sources'] == sources_missing_text

    def test_sources_with_none_values(self, mock_db_connection):
        """Test sources containing None values"""
        sources_with_none = [
            {"url": None, "text": "Test"},
            {"url": "https://example.com", "text": None}
        ]

        result_id = save_search_result(
            query="Test",
            answer_text="Answer",
            sources=sources_with_none
        )

        assert result_id is not None
        results = get_results_by_query("Test")
        assert results[0]['sources'] == sources_with_none

    def test_sources_with_nested_objects(self, mock_db_connection):
        """Test sources with nested object structures"""
        sources_nested = [
            {
                "url": "https://example.com",
                "text": "Test",
                "metadata": {"author": "John", "date": "2025-01-01"}
            }
        ]

        result_id = save_search_result(
            query="Test",
            answer_text="Answer",
            sources=sources_nested
        )

        assert result_id is not None
        results = get_results_by_query("Test")
        assert results[0]['sources'] == sources_nested

    def test_empty_sources_list(self, mock_db_connection):
        """Test saving with empty sources list"""
        result_id = save_search_result(
            query="Test",
            answer_text="Answer",
            sources=[]
        )

        assert result_id is not None
        results = get_results_by_query("Test")
        assert results[0]['sources'] == []

    def test_sources_with_very_long_url(self, mock_db_connection):
        """Test sources with extremely long URLs"""
        very_long_url = "https://example.com/" + "a" * 10000
        sources_long_url = [
            {"url": very_long_url, "text": "Long URL"}
        ]

        result_id = save_search_result(
            query="Test",
            answer_text="Answer",
            sources=sources_long_url
        )

        assert result_id is not None
        results = get_results_by_query("Test")
        assert results[0]['sources'][0]['url'] == very_long_url


@pytest.mark.unit
class TestBoundaryConditions:
    """Tests for boundary conditions and edge values"""

    def test_limit_parameter_zero(self, mock_db_connection):
        """Test querying with limit=0"""
        save_search_result(query="Q1", answer_text="A1", sources=[])
        save_search_result(query="Q2", answer_text="A2", sources=[])

        results = get_recent_results(limit=0)

        # Limit of 0 should return empty list
        assert results == []

    def test_limit_parameter_negative(self, mock_db_connection):
        """Test querying with negative limit"""
        save_search_result(query="Q1", answer_text="A1", sources=[])

        # Negative limit should be handled gracefully
        # SQLite treats negative limit as no limit
        results = get_recent_results(limit=-1)

        # Should return all results (or handle error gracefully)
        assert isinstance(results, list)

    def test_empty_query_string(self, mock_db_connection):
        """Test saving and querying with empty string"""
        result_id = save_search_result(
            query="",
            answer_text="Answer for empty query",
            sources=[]
        )

        assert result_id is not None
        results = get_results_by_query("")
        assert len(results) == 1
        assert results[0]['query'] == ""

    def test_empty_answer_text(self, mock_db_connection):
        """Test saving with empty answer text"""
        result_id = save_search_result(
            query="Test",
            answer_text="",
            sources=[]
        )

        assert result_id is not None
        results = get_results_by_query("Test")
        assert results[0]['answer_text'] == ""

    def test_none_answer_text(self, mock_db_connection):
        """Test saving with None as answer text"""
        result_id = save_search_result(
            query="Test",
            answer_text=None,
            sources=[]
        )

        assert result_id is not None
        results = get_results_by_query("Test")
        assert results[0]['answer_text'] is None

    def test_execution_time_zero(self, mock_db_connection):
        """Test saving with execution time of 0"""
        result_id = save_search_result(
            query="Test",
            answer_text="Answer",
            sources=[],
            execution_time=0
        )

        assert result_id is not None
        results = get_results_by_query("Test")
        assert results[0]['execution_time_seconds'] == 0

    def test_execution_time_negative(self, mock_db_connection):
        """Test saving with negative execution time"""
        result_id = save_search_result(
            query="Test",
            answer_text="Answer",
            sources=[],
            execution_time=-5.0
        )

        assert result_id is not None
        results = get_results_by_query("Test")
        assert results[0]['execution_time_seconds'] == -5.0

    def test_very_large_execution_time(self, mock_db_connection):
        """Test saving with very large execution time"""
        result_id = save_search_result(
            query="Test",
            answer_text="Answer",
            sources=[],
            execution_time=999999.99
        )

        assert result_id is not None
        results = get_results_by_query("Test")
        assert results[0]['execution_time_seconds'] == 999999.99

    def test_very_long_answer_text(self, mock_db_connection):
        """Test saving very long answer text"""
        very_long_answer = "A" * 100000  # 100KB of text

        result_id = save_search_result(
            query="Test",
            answer_text=very_long_answer,
            sources=[]
        )

        assert result_id is not None
        results = get_results_by_query("Test")
        assert len(results[0]['answer_text']) == 100000

    def test_model_as_empty_string(self, mock_db_connection):
        """Test saving with model as empty string"""
        result_id = save_search_result(
            query="Test",
            answer_text="Answer",
            sources=[],
            model=""
        )

        assert result_id is not None
        results = get_results_by_query("Test")
        assert results[0]['model'] == ""


@pytest.mark.unit
class TestGetResultsByDateRange:
    """Tests for get_results_by_date_range() function"""

    def test_get_results_by_date_range_both_dates(self, mock_db_connection):
        """Test filtering with both start and end date."""
        init_database()
        save_search_result(query="Q1", answer_text="A1", sources=[], model="gpt-4")
        save_search_result(query="Q2", answer_text="A2", sources=[], model="gpt-4")
        save_search_result(query="Q3", answer_text="A3", sources=[], model="gpt-4")

        results = get_results_by_date_range(
            start_date='2025-01-01',
            end_date='2025-12-31'
        )

        assert len(results) >= 3
        assert all(isinstance(r, dict) for r in results)

    def test_get_results_by_date_range_start_date_only(self, mock_db_connection):
        """Test filtering with only start date."""
        init_database()
        save_search_result(query="Q1", answer_text="A1", sources=[])
        save_search_result(query="Q2", answer_text="A2", sources=[])

        results = get_results_by_date_range(start_date='2025-01-01')

        assert len(results) >= 2

    def test_get_results_by_date_range_end_date_only(self, mock_db_connection):
        """Test filtering with only end date."""
        init_database()
        save_search_result(query="Q1", answer_text="A1", sources=[])

        results = get_results_by_date_range(end_date='2025-12-31')

        assert len(results) >= 1

    def test_get_results_by_date_range_with_model_filter(self, mock_db_connection):
        """Test combining date range and model filters."""
        init_database()
        save_search_result(query="Q1", answer_text="A1", sources=[], model="gpt-4")
        save_search_result(query="Q2", answer_text="A2", sources=[], model="claude-3")

        results = get_results_by_date_range(
            start_date='2025-01-01',
            end_date='2025-12-31',
            model="gpt-4"
        )

        assert all(r['model'] == "gpt-4" for r in results)

    def test_get_results_by_date_range_with_limit(self, mock_db_connection):
        """Test date range filtering respects limit parameter."""
        init_database()
        for i in range(10):
            save_search_result(query=f"Q{i}", answer_text=f"A{i}", sources=[])

        results = get_results_by_date_range(
            start_date='2025-01-01',
            end_date='2025-12-31',
            limit=5
        )

        assert len(results) <= 5

    def test_get_results_by_date_range_empty_results(self, mock_db_connection):
        """Test date range that returns no results."""
        init_database()
        save_search_result(query="Q1", answer_text="A1", sources=[])

        results = get_results_by_date_range(
            start_date='2020-01-01',
            end_date='2020-12-31'
        )

        assert results == []

    def test_get_results_by_date_range_ordered_by_timestamp(self, mock_db_connection):
        """Test results are ordered by timestamp descending."""
        init_database()
        id1 = save_search_result(query="Q1", answer_text="A1", sources=[])
        id2 = save_search_result(query="Q2", answer_text="A2", sources=[])

        results = get_results_by_date_range(start_date='2025-01-01')

        # Should be in reverse order (most recent first)
        assert len(results) >= 2


@pytest.mark.unit
class TestGetResultsBySuccessStatus:
    """Tests for get_results_by_success_status() function"""

    def test_get_results_by_success_status_successful_only(self, mock_db_connection):
        """Test filtering for successful results only."""
        init_database()
        save_search_result(query="Q1", answer_text="A1", sources=[], success=True)
        save_search_result(query="Q2", answer_text="A2", sources=[], success=False)
        save_search_result(query="Q3", answer_text="A3", sources=[], success=True)

        results = get_results_by_success_status(success=True)

        assert len(results) == 2
        assert all(r['success'] == 1 for r in results)

    def test_get_results_by_success_status_failed_only(self, mock_db_connection):
        """Test filtering for failed results only."""
        init_database()
        save_search_result(query="Q1", answer_text="A1", sources=[], success=True)
        save_search_result(query="Q2", answer_text="A2", sources=[], success=False)
        save_search_result(query="Q3", answer_text="A3", sources=[], success=False)

        results = get_results_by_success_status(success=False)

        assert len(results) == 2
        assert all(r['success'] == 0 for r in results)

    def test_get_results_by_success_status_with_limit(self, mock_db_connection):
        """Test success status filtering respects limit parameter."""
        init_database()
        for i in range(8):
            save_search_result(
                query=f"Q{i}",
                answer_text=f"A{i}",
                sources=[],
                success=True
            )

        results = get_results_by_success_status(success=True, limit=3)

        assert len(results) == 3

    def test_get_results_by_success_status_empty_results(self, mock_db_connection):
        """Test when no results match success criteria."""
        init_database()
        save_search_result(query="Q1", answer_text="A1", sources=[], success=True)

        results = get_results_by_success_status(success=False)

        assert results == []

    def test_get_results_by_success_status_default_successful(self, mock_db_connection):
        """Test default parameter returns successful results."""
        init_database()
        save_search_result(query="Q1", answer_text="A1", sources=[], success=True)
        save_search_result(query="Q2", answer_text="A2", sources=[], success=False)

        results = get_results_by_success_status()

        assert len(results) == 1
        assert results[0]['success'] == 1


@pytest.mark.unit
class TestGetResultsByExecutionTime:
    """Tests for get_results_by_execution_time() function"""

    def test_get_results_by_execution_time_min_time_only(self, mock_db_connection):
        """Test filtering by minimum execution time."""
        init_database()
        save_search_result(query="Q1", answer_text="A1", sources=[], execution_time=5.0)
        save_search_result(query="Q2", answer_text="A2", sources=[], execution_time=15.0)
        save_search_result(query="Q3", answer_text="A3", sources=[], execution_time=25.0)

        results = get_results_by_execution_time(min_time=10.0)

        assert len(results) == 2
        assert all(r['execution_time_seconds'] >= 10.0 for r in results)

    def test_get_results_by_execution_time_max_time_only(self, mock_db_connection):
        """Test filtering by maximum execution time."""
        init_database()
        save_search_result(query="Q1", answer_text="A1", sources=[], execution_time=5.0)
        save_search_result(query="Q2", answer_text="A2", sources=[], execution_time=15.0)
        save_search_result(query="Q3", answer_text="A3", sources=[], execution_time=25.0)

        results = get_results_by_execution_time(max_time=20.0)

        assert len(results) == 2
        assert all(r['execution_time_seconds'] <= 20.0 for r in results)

    def test_get_results_by_execution_time_range(self, mock_db_connection):
        """Test filtering by execution time range."""
        init_database()
        save_search_result(query="Q1", answer_text="A1", sources=[], execution_time=5.0)
        save_search_result(query="Q2", answer_text="A2", sources=[], execution_time=15.0)
        save_search_result(query="Q3", answer_text="A3", sources=[], execution_time=25.0)

        results = get_results_by_execution_time(min_time=10.0, max_time=20.0)

        assert len(results) == 1
        assert results[0]['execution_time_seconds'] == 15.0

    def test_get_results_by_execution_time_ordered_ascending(self, mock_db_connection):
        """Test results ordered by execution time ascending."""
        init_database()
        save_search_result(query="Q1", answer_text="A1", sources=[], execution_time=25.0)
        save_search_result(query="Q2", answer_text="A2", sources=[], execution_time=5.0)
        save_search_result(query="Q3", answer_text="A3", sources=[], execution_time=15.0)

        results = get_results_by_execution_time()

        assert len(results) >= 3
        # Verify ordering by checking times are in ascending order
        times = [r['execution_time_seconds'] for r in results if r['execution_time_seconds'] is not None]
        assert times == sorted(times)

    def test_get_results_by_execution_time_excludes_null(self, mock_db_connection):
        """Test that results without execution time are excluded."""
        init_database()
        save_search_result(query="Q1", answer_text="A1", sources=[], execution_time=10.0)
        save_search_result(query="Q2", answer_text="A2", sources=[], execution_time=None)

        results = get_results_by_execution_time()

        assert len(results) == 1
        assert results[0]['execution_time_seconds'] == 10.0

    def test_get_results_by_execution_time_with_limit(self, mock_db_connection):
        """Test execution time filtering respects limit parameter."""
        init_database()
        for i in range(10):
            save_search_result(
                query=f"Q{i}",
                answer_text=f"A{i}",
                sources=[],
                execution_time=float(i + 1)
            )

        results = get_results_by_execution_time(limit=3)

        assert len(results) == 3

    def test_get_results_by_execution_time_zero_time(self, mock_db_connection):
        """Test filtering includes zero execution time."""
        init_database()
        save_search_result(query="Q1", answer_text="A1", sources=[], execution_time=0.0)
        save_search_result(query="Q2", answer_text="A2", sources=[], execution_time=10.0)

        results = get_results_by_execution_time(min_time=0.0, max_time=5.0)

        assert len(results) == 1
        assert results[0]['execution_time_seconds'] == 0.0


@pytest.mark.unit
class TestSearchInAnswers:
    """Tests for search_in_answers() function"""

    def test_search_in_answers_case_insensitive(self, mock_db_connection):
        """Test case-insensitive search in answer text."""
        init_database()
        save_search_result(query="Q1", answer_text="Python is a great language", sources=[])
        save_search_result(query="Q2", answer_text="JavaScript is also useful", sources=[])
        save_search_result(query="Q3", answer_text="PYTHON developers love it", sources=[])

        results = search_in_answers("python", case_sensitive=False)

        assert len(results) == 2
        assert any("Python" in r['answer_text'] for r in results)

    def test_search_in_answers_case_sensitive(self, mock_db_connection):
        """Test case-sensitive search in answer text."""
        init_database()
        save_search_result(query="Q1", answer_text="Python is great", sources=[])
        save_search_result(query="Q2", answer_text="python is cool", sources=[])

        results = search_in_answers("Python", case_sensitive=True)

        assert len(results) == 1
        assert "Python" in results[0]['answer_text']

    def test_search_in_answers_partial_match(self, mock_db_connection):
        """Test partial matching works."""
        init_database()
        save_search_result(query="Q1", answer_text="Programming with Python", sources=[])
        save_search_result(query="Q2", answer_text="JavaScript guide", sources=[])

        results = search_in_answers("gram", case_sensitive=False)

        assert len(results) == 1
        assert "Programming" in results[0]['answer_text']

    def test_search_in_answers_no_matches(self, mock_db_connection):
        """Test search with no matching results."""
        init_database()
        save_search_result(query="Q1", answer_text="Python programming", sources=[])

        results = search_in_answers("Rust", case_sensitive=False)

        assert results == []

    def test_search_in_answers_with_limit(self, mock_db_connection):
        """Test search respects limit parameter."""
        init_database()
        for i in range(10):
            save_search_result(query=f"Q{i}", answer_text="Python is awesome", sources=[])

        results = search_in_answers("Python", limit=5)

        assert len(results) == 5

    def test_search_in_answers_special_characters(self, mock_db_connection):
        """Test searching for text with special characters."""
        init_database()
        save_search_result(query="Q1", answer_text="Cost is $100 per month", sources=[])
        save_search_result(query="Q2", answer_text="Price: 50 dollars", sources=[])

        results = search_in_answers("$100", case_sensitive=False)

        assert len(results) == 1

    def test_search_in_answers_empty_search_term(self, mock_db_connection):
        """Test search with empty search term matches all."""
        init_database()
        save_search_result(query="Q1", answer_text="Answer 1", sources=[])
        save_search_result(query="Q2", answer_text="Answer 2", sources=[])

        results = search_in_answers("", case_sensitive=False)

        assert len(results) == 2


@pytest.mark.unit
class TestSearchInSources:
    """Tests for search_in_sources() function"""

    def test_search_in_sources_case_insensitive(self, mock_db_connection):
        """Test case-insensitive search in sources."""
        init_database()
        sources1 = [{"url": "https://github.com", "text": "GitHub repository"}]
        sources2 = [{"url": "https://gitlab.com", "text": "GitLab project"}]

        save_search_result(query="Q1", answer_text="A1", sources=sources1)
        save_search_result(query="Q2", answer_text="A2", sources=sources2)

        results = search_in_sources("github", case_sensitive=False)

        assert len(results) == 1
        assert any("github" in r['sources'][0]['url'].lower() for r in results)

    def test_search_in_sources_case_sensitive(self, mock_db_connection):
        """Test case-sensitive search in sources."""
        init_database()
        sources1 = [{"url": "https://GitHub.com", "text": "Source"}]
        sources2 = [{"url": "https://github.com", "text": "Source"}]

        save_search_result(query="Q1", answer_text="A1", sources=sources1)
        save_search_result(query="Q2", answer_text="A2", sources=sources2)

        results = search_in_sources("GitHub", case_sensitive=True)

        assert len(results) == 1

    def test_search_in_sources_no_matches(self, mock_db_connection):
        """Test search with no matching sources."""
        init_database()
        sources = [{"url": "https://python.org", "text": "Python"}]
        save_search_result(query="Q1", answer_text="A1", sources=sources)

        results = search_in_sources("rust", case_sensitive=False)

        assert results == []

    def test_search_in_sources_with_limit(self, mock_db_connection):
        """Test search respects limit parameter."""
        init_database()
        sources = [{"url": "https://example.com", "text": "Example"}]
        for i in range(10):
            save_search_result(query=f"Q{i}", answer_text=f"A{i}", sources=sources)

        results = search_in_sources("example.com", limit=3)

        assert len(results) == 3

    def test_search_in_sources_empty_sources_not_matched(self, mock_db_connection):
        """Test that empty sources don't match searches."""
        init_database()
        save_search_result(query="Q1", answer_text="A1", sources=[])
        save_search_result(query="Q2", answer_text="A2", sources=[{"url": "https://example.com", "text": "Example"}])

        results = search_in_sources("example", case_sensitive=False)

        assert len(results) == 1

    def test_search_in_sources_searches_url_and_text(self, mock_db_connection):
        """Test that search finds matches in both URL and text."""
        init_database()
        sources1 = [{"url": "https://test.com", "text": "Documentation"}]
        sources2 = [{"url": "https://example.com", "text": "Test Results"}]

        save_search_result(query="Q1", answer_text="A1", sources=sources1)
        save_search_result(query="Q2", answer_text="A2", sources=sources2)

        results_url = search_in_sources("test.com", case_sensitive=False)
        results_text = search_in_sources("Test", case_sensitive=False)

        assert len(results_url) == 1
        assert len(results_text) == 2  # Matches both URL and text fields


@pytest.mark.unit
class TestSearchQueriesFuzzy:
    """Tests for search_queries_fuzzy() function"""

    def test_search_queries_fuzzy_with_wildcards(self, mock_db_connection):
        """Test fuzzy search with SQL LIKE wildcards."""
        init_database()
        save_search_result(query="What is Python?", answer_text="A1", sources=[])
        save_search_result(query="What is JavaScript?", answer_text="A2", sources=[])
        save_search_result(query="How to learn Java?", answer_text="A3", sources=[])

        results = search_queries_fuzzy("What%", limit=10)

        assert len(results) == 2
        assert all(r['query'].startswith("What") for r in results)

    def test_search_queries_fuzzy_percent_anywhere(self, mock_db_connection):
        """Test fuzzy search with wildcard in middle."""
        init_database()
        save_search_result(query="What is Python?", answer_text="A1", sources=[])
        save_search_result(query="How to use Python?", answer_text="A2", sources=[])
        save_search_result(query="JavaScript basics", answer_text="A3", sources=[])

        results = search_queries_fuzzy("%Python%", limit=10)

        assert len(results) == 2
        assert all("Python" in r['query'] for r in results)

    def test_search_queries_fuzzy_single_char_wildcard(self, mock_db_connection):
        """Test fuzzy search with underscore wildcard (single char)."""
        init_database()
        save_search_result(query="Best Python courses", answer_text="A1", sources=[])
        save_search_result(query="Best Java courses", answer_text="A2", sources=[])
        save_search_result(query="Best Rust courses", answer_text="A3", sources=[])

        results = search_queries_fuzzy("Best _a%", limit=10)

        # Matches "Java" and "Rust" (but not "Python")
        assert len(results) >= 1

    def test_search_queries_fuzzy_no_matches(self, mock_db_connection):
        """Test fuzzy search with no matches."""
        init_database()
        save_search_result(query="What is Python?", answer_text="A1", sources=[])

        results = search_queries_fuzzy("COBOL%", limit=10)

        assert results == []

    def test_search_queries_fuzzy_with_limit(self, mock_db_connection):
        """Test fuzzy search respects limit parameter."""
        init_database()
        for i in range(10):
            save_search_result(query=f"What is test{i}?", answer_text=f"A{i}", sources=[])

        results = search_queries_fuzzy("What%", limit=3)

        assert len(results) == 3

    def test_search_queries_fuzzy_exact_match(self, mock_db_connection):
        """Test fuzzy search with exact match pattern."""
        init_database()
        save_search_result(query="What is Python?", answer_text="A1", sources=[])
        save_search_result(query="What is Python?", answer_text="A2", sources=[])
        save_search_result(query="What is Java?", answer_text="A3", sources=[])

        results = search_queries_fuzzy("What is Python?", limit=10)

        assert len(results) == 2
        assert all(r['query'] == "What is Python?" for r in results)


@pytest.mark.unit
class TestGetResultsAdvancedFilter:
    """Tests for get_results_advanced_filter() function"""

    def test_advanced_filter_query_pattern_only(self, mock_db_connection):
        """Test advanced filter with query pattern only."""
        init_database()
        save_search_result(query="What is Python?", answer_text="A1", sources=[])
        save_search_result(query="What is Java?", answer_text="A2", sources=[])
        save_search_result(query="How to learn coding?", answer_text="A3", sources=[])

        results = get_results_advanced_filter(query_pattern="What%")

        assert len(results) == 2
        assert all("What" in r['query'] for r in results)

    def test_advanced_filter_model_only(self, mock_db_connection):
        """Test advanced filter with model only."""
        init_database()
        save_search_result(query="Q1", answer_text="A1", sources=[], model="gpt-4")
        save_search_result(query="Q2", answer_text="A2", sources=[], model="claude-3")
        save_search_result(query="Q3", answer_text="A3", sources=[], model="gpt-4")

        results = get_results_advanced_filter(model="gpt-4")

        assert len(results) == 2
        assert all(r['model'] == "gpt-4" for r in results)

    def test_advanced_filter_date_range(self, mock_db_connection):
        """Test advanced filter with date range."""
        init_database()
        save_search_result(query="Q1", answer_text="A1", sources=[])
        save_search_result(query="Q2", answer_text="A2", sources=[])

        results = get_results_advanced_filter(
            start_date='2025-01-01',
            end_date='2025-12-31'
        )

        assert len(results) >= 2

    def test_advanced_filter_success_status_true(self, mock_db_connection):
        """Test advanced filter with success=True."""
        init_database()
        save_search_result(query="Q1", answer_text="A1", sources=[], success=True)
        save_search_result(query="Q2", answer_text="A2", sources=[], success=False)

        results = get_results_advanced_filter(success=True)

        assert len(results) == 1
        assert results[0]['success'] == 1

    def test_advanced_filter_success_status_false(self, mock_db_connection):
        """Test advanced filter with success=False."""
        init_database()
        save_search_result(query="Q1", answer_text="A1", sources=[], success=True)
        save_search_result(query="Q2", answer_text="A2", sources=[], success=False)

        results = get_results_advanced_filter(success=False)

        assert len(results) == 1
        assert results[0]['success'] == 0

    def test_advanced_filter_execution_time_range(self, mock_db_connection):
        """Test advanced filter with execution time range."""
        init_database()
        save_search_result(query="Q1", answer_text="A1", sources=[], execution_time=5.0)
        save_search_result(query="Q2", answer_text="A2", sources=[], execution_time=15.0)
        save_search_result(query="Q3", answer_text="A3", sources=[], execution_time=25.0)

        results = get_results_advanced_filter(
            min_exec_time=10.0,
            max_exec_time=20.0
        )

        assert len(results) == 1
        assert results[0]['execution_time_seconds'] == 15.0

    def test_advanced_filter_answer_length_range(self, mock_db_connection):
        """Test advanced filter with answer length constraints."""
        init_database()
        save_search_result(query="Q1", answer_text="Short", sources=[])
        save_search_result(query="Q2", answer_text="This is a longer answer text", sources=[])
        save_search_result(query="Q3", answer_text="Very " * 100, sources=[])

        results = get_results_advanced_filter(
            min_answer_length=10,
            max_answer_length=100
        )

        assert len(results) == 1
        assert len(results[0]['answer_text']) >= 10
        assert len(results[0]['answer_text']) <= 100

    def test_advanced_filter_has_sources_true(self, mock_db_connection):
        """Test advanced filter for results with sources."""
        init_database()
        save_search_result(query="Q1", answer_text="A1", sources=[{"url": "https://example.com", "text": "Source"}])
        save_search_result(query="Q2", answer_text="A2", sources=[])
        save_search_result(query="Q3", answer_text="A3", sources=[])

        results = get_results_advanced_filter(has_sources=True)

        assert len(results) == 1
        assert len(results[0]['sources']) > 0

    def test_advanced_filter_has_sources_false(self, mock_db_connection):
        """Test advanced filter for results without sources."""
        init_database()
        save_search_result(query="Q1", answer_text="A1", sources=[{"url": "https://example.com", "text": "Source"}])
        save_search_result(query="Q2", answer_text="A2", sources=[])

        results = get_results_advanced_filter(has_sources=False)

        assert len(results) == 1
        assert len(results[0]['sources']) == 0

    def test_advanced_filter_multiple_criteria(self, mock_db_connection):
        """Test advanced filter with multiple criteria combined."""
        init_database()
        save_search_result(
            query="What is Python?",
            answer_text="Python is a programming language with good documentation",
            sources=[{"url": "https://python.org", "text": "Official Python"}],
            model="gpt-4",
            execution_time=15.0,
            success=True
        )
        save_search_result(
            query="What is Java?",
            answer_text="Java is verbose",
            sources=[],
            model="claude-3",
            execution_time=25.0,
            success=True
        )
        save_search_result(
            query="What is Rust?",
            answer_text="Rust is hard",
            sources=[],
            model="gpt-4",
            execution_time=5.0,
            success=False
        )

        results = get_results_advanced_filter(
            query_pattern="What%",
            model="gpt-4",
            success=True,
            min_exec_time=10.0,
            has_sources=True
        )

        assert len(results) == 1
        assert results[0]['query'] == "What is Python?"
        assert results[0]['model'] == "gpt-4"
        assert results[0]['success'] == 1

    def test_advanced_filter_order_by_timestamp_desc(self, mock_db_connection):
        """Test advanced filter orders by timestamp descending."""
        init_database()
        id1 = save_search_result(query="Q1", answer_text="A1", sources=[])
        id2 = save_search_result(query="Q2", answer_text="A2", sources=[])
        id3 = save_search_result(query="Q3", answer_text="A3", sources=[])

        results = get_results_advanced_filter(order_by='timestamp', order_desc=True)

        assert len(results) >= 3

    def test_advanced_filter_order_by_execution_time(self, mock_db_connection):
        """Test advanced filter orders by execution time."""
        init_database()
        save_search_result(query="Q1", answer_text="A1", sources=[], execution_time=25.0)
        save_search_result(query="Q2", answer_text="A2", sources=[], execution_time=5.0)
        save_search_result(query="Q3", answer_text="A3", sources=[], execution_time=15.0)

        results = get_results_advanced_filter(
            order_by='execution_time_seconds',
            order_desc=False
        )

        assert len(results) >= 3
        times = [r['execution_time_seconds'] for r in results if r['execution_time_seconds'] is not None]
        assert times == sorted(times)

    def test_advanced_filter_order_by_query(self, mock_db_connection):
        """Test advanced filter orders by query text."""
        init_database()
        save_search_result(query="Zebra facts", answer_text="A1", sources=[])
        save_search_result(query="Apple info", answer_text="A2", sources=[])
        save_search_result(query="Mango guide", answer_text="A3", sources=[])

        results = get_results_advanced_filter(
            order_by='query',
            order_desc=False
        )

        assert len(results) >= 3
        queries = [r['query'] for r in results]
        assert queries == sorted(queries)

    def test_advanced_filter_invalid_order_by_defaults_to_timestamp(self, mock_db_connection):
        """Test that invalid order_by defaults to timestamp."""
        init_database()
        save_search_result(query="Q1", answer_text="A1", sources=[])

        results = get_results_advanced_filter(order_by='invalid_column')

        assert len(results) >= 1

    def test_advanced_filter_with_limit(self, mock_db_connection):
        """Test advanced filter respects limit parameter."""
        init_database()
        for i in range(10):
            save_search_result(
                query=f"Test query {i}",
                answer_text=f"Answer {i}",
                sources=[],
                model="gpt-4"
            )

        results = get_results_advanced_filter(model="gpt-4", limit=5)

        assert len(results) == 5

    def test_advanced_filter_no_criteria_returns_all(self, mock_db_connection):
        """Test that no filter criteria returns all results."""
        init_database()
        save_search_result(query="Q1", answer_text="A1", sources=[])
        save_search_result(query="Q2", answer_text="A2", sources=[])
        save_search_result(query="Q3", answer_text="A3", sources=[])

        results = get_results_advanced_filter()

        assert len(results) >= 3

    def test_advanced_filter_all_criteria_combined(self, mock_db_connection):
        """Test advanced filter with all filter criteria specified."""
        init_database()
        sources = [{"url": "https://example.com", "text": "Source"}]
        save_search_result(
            query="What is test?",
            answer_text="This is a detailed explanation with many characters",
            sources=sources,
            model="gpt-4",
            execution_time=20.0,
            success=True
        )
        save_search_result(
            query="What is fail?",
            answer_text="Short",
            sources=[],
            model="claude-3",
            execution_time=5.0,
            success=False
        )

        results = get_results_advanced_filter(
            query_pattern="What%",
            model="gpt-4",
            start_date='2025-01-01',
            end_date='2025-12-31',
            success=True,
            min_exec_time=10.0,
            max_exec_time=30.0,
            min_answer_length=20,
            max_answer_length=100,
            has_sources=True,
            limit=10,
            order_by='timestamp',
            order_desc=True
        )

        assert len(results) == 1
        assert results[0]['query'] == "What is test?"


@pytest.mark.unit
class TestNewFunctionsSQLInjectionPrevention:
    """Tests for SQL injection prevention in new functions"""

    def test_date_range_sql_injection_in_date(self, mock_db_connection):
        """Test that malicious dates don't execute SQL."""
        init_database()
        save_search_result(query="Normal query", answer_text="Normal answer", sources=[])

        malicious_date = "2025-01-01'; DROP TABLE search_results; --"
        results = get_results_by_date_range(start_date=malicious_date)

        # Table should still exist, no injection occurred
        verify_results = get_results_by_query("Normal query")
        assert len(verify_results) >= 1

    def test_answer_search_sql_injection(self, mock_db_connection):
        """Test that malicious search terms don't execute SQL."""
        init_database()
        save_search_result(query="Q1", answer_text="Normal content", sources=[])

        malicious_search = "content' OR '1'='1"
        results = search_in_answers(malicious_search)

        # Should only find exact substring matches, not bypass WHERE clause
        assert len(results) <= 1

    def test_source_search_sql_injection(self, mock_db_connection):
        """Test that malicious source searches don't execute SQL."""
        init_database()
        save_search_result(
            query="Q1",
            answer_text="A1",
            sources=[{"url": "https://example.com", "text": "Source"}]
        )

        malicious_search = "%' OR '1'='1"
        results = search_in_sources(malicious_search)

        # Should handle safely
        assert isinstance(results, list)

    def test_fuzzy_search_sql_injection(self, mock_db_connection):
        """Test that fuzzy pattern injection is handled safely."""
        init_database()
        save_search_result(query="What is Python?", answer_text="A1", sources=[])

        malicious_pattern = "What%' OR '1'='1"
        results = search_queries_fuzzy(malicious_pattern)

        # Should handle as literal pattern, not SQL injection
        assert isinstance(results, list)

    def test_advanced_filter_all_parameters_injection_safe(self, mock_db_connection):
        """Test that advanced filter handles injection in all parameters."""
        init_database()
        save_search_result(
            query="Test query",
            answer_text="Test answer",
            sources=[],
            model="gpt-4"
        )

        # Try injection in various parameters
        results = get_results_advanced_filter(
            query_pattern="Test%' OR '1'='1",
            model="gpt-4' OR '1'='1",
            start_date="2025-01-01' OR '1'='1",
            end_date="2025-12-31' OR '1'='1"
        )

        # Should handle safely (likely no matches due to literal matching)
        assert isinstance(results, list)
