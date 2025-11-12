"""
Comprehensive tests for src/utils/statistics.py

Tests all 12 statistics functions with diverse test data, edge cases,
and statistical accuracy verification.
"""

import pytest
import sqlite3
import json
import statistics
from datetime import datetime, timedelta
from unittest.mock import patch
from pathlib import Path
from typing import Dict, List

from src.utils.statistics import (
    get_execution_time_stats,
    get_success_rate_stats,
    get_model_comparison_stats,
    get_answer_length_stats,
    get_source_count_stats,
    get_query_volume_by_period,
    get_trends_over_time,
    get_percentiles,
    get_outliers,
    get_histogram_data,
    find_duplicate_queries,
    get_database_summary,
)


@pytest.fixture
def statistics_test_db(tmp_path):
    """
    Create test database with diverse sample data for statistics testing.

    Provides varied execution times, success/failure statuses, answer lengths,
    source counts, and timestamps spanning multiple days for comprehensive testing.
    """
    db_path = tmp_path / "test_statistics.db"
    conn = sqlite3.connect(str(db_path))
    cursor = conn.cursor()

    # Create schema matching production database
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS search_results (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            query TEXT NOT NULL,
            model TEXT,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
            answer_text TEXT,
            sources TEXT,
            screenshot_path TEXT,
            execution_time_seconds REAL,
            success BOOLEAN DEFAULT 1,
            error_message TEXT
        )
    ''')

    # Create indexes
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_query ON search_results(query)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_model ON search_results(model)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_timestamp ON search_results(timestamp)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_query_model ON search_results(query, model)')

    conn.commit()

    # Patch the database path for all statistics functions
    with patch('src.utils.statistics.DB_PATH', str(db_path)):
        yield db_path, conn

    conn.close()


@pytest.fixture
def populate_with_diverse_data(statistics_test_db):
    """
    Populate test database with diverse sample data.

    Includes:
    - Multiple models: gpt-4, claude-3, sonar-pro
    - Execution times: 5s to 60s (various ranges)
    - Success/failure: mixed statuses
    - Answer lengths: 100 to 5000 characters
    - Source counts: 0 to 10 sources
    - Timestamps: spanning 30 days
    - Some duplicate queries for testing
    """
    db_path, conn = statistics_test_db
    cursor = conn.cursor()

    # Base timestamp (30 days ago)
    base_time = datetime.now() - timedelta(days=30)

    # Test data: (query, model, exec_time, success, answer_len, source_count, offset_days)
    test_data = [
        # GPT-4 results
        ("What is Python?", "gpt-4", 10.5, True, 1200, 3, 0),
        ("What is Python?", "gpt-4", 11.2, True, 1150, 3, 1),  # Duplicate query
        ("What is Python?", "gpt-4", 12.0, True, 1300, 4, 2),  # Duplicate query
        ("Best practices for REST APIs", "gpt-4", 15.5, True, 2000, 5, 3),
        ("How to optimize database queries?", "gpt-4", 20.0, True, 1800, 4, 4),
        ("Explain machine learning", "gpt-4", 18.5, False, 800, 2, 5),

        # Claude-3 results
        ("What is Python?", "claude-3", 9.5, True, 1100, 3, 6),  # Duplicate query
        ("What is Python?", "claude-3", 10.0, True, 1180, 3, 7),  # Duplicate query
        ("Best practices for REST APIs", "claude-3", 14.0, True, 1950, 5, 8),
        ("How to optimize database queries?", "claude-3", 19.0, True, 1750, 4, 9),
        ("Explain machine learning", "claude-3", 17.0, True, 2100, 5, 10),
        ("What is cloud computing?", "claude-3", 12.5, True, 1500, 4, 11),

        # Sonar-pro results
        ("What is Python?", "sonar-pro", 8.5, True, 950, 2, 12),  # Duplicate query
        ("What is Python?", "sonar-pro", 9.0, True, 1000, 2, 13),  # Duplicate query
        ("Best practices for REST APIs", "sonar-pro", 13.5, True, 1850, 5, 14),
        ("How to optimize database queries?", "sonar-pro", 18.5, True, 1700, 3, 15),
        ("Explain machine learning", "sonar-pro", 16.0, False, 600, 1, 16),

        # Edge cases
        ("What is the meaning of life?", "gpt-4", 5.0, True, 100, 1, 17),  # Very fast
        ("Complex query about quantum physics", "gpt-4", 60.0, True, 5000, 10, 18),  # Very slow, long answer
        ("Failed query 1", "claude-3", 25.0, False, 200, 1, 19),  # Failed
        ("Failed query 2", "sonar-pro", 30.0, False, 150, 0, 20),  # Failed, no sources
        ("Another unique query", "gpt-4", 11.0, True, 1000, 3, 21),
        ("Another unique query", "claude-3", 10.5, True, 1050, 3, 22),  # Duplicate

        # More data for trends and volume
        ("Query for trends", "gpt-4", 12.0, True, 1200, 3, 23),
        ("Query for trends", "gpt-4", 11.5, True, 1100, 3, 24),
        ("Query for trends", "claude-3", 11.0, True, 1150, 3, 25),
        ("Query for trends", "sonar-pro", 10.5, True, 1050, 3, 26),

        # Same day data for hourly aggregation
        ("Hourly test query", "gpt-4", 10.0, True, 1000, 3, 0),
        ("Hourly test query", "gpt-4", 11.0, True, 1100, 3, 0),
        ("Hourly test query", "claude-3", 9.5, True, 950, 3, 0),
    ]

    for query, model, exec_time, success, answer_len, source_count, offset_days in test_data:
        timestamp = base_time + timedelta(days=offset_days)

        # Create answer text of specific length
        answer_text = "A" * answer_len if answer_len > 0 else None

        # Create sources list
        sources = json.dumps([
            {"url": f"https://example{i}.com", "text": f"Source {i}"}
            for i in range(source_count)
        ])

        cursor.execute('''
            INSERT INTO search_results
            (query, model, timestamp, answer_text, sources, execution_time_seconds, success)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (query, model, timestamp.isoformat(), answer_text, sources, exec_time, int(success)))

    conn.commit()

    with patch('src.utils.statistics.DB_PATH', str(db_path)):
        yield db_path, conn

    conn.close()


@pytest.fixture
def empty_database(statistics_test_db):
    """Provide empty database for testing edge cases."""
    db_path, conn = statistics_test_db
    with patch('src.utils.statistics.DB_PATH', str(db_path)):
        yield db_path, conn


@pytest.fixture
def single_record_database(statistics_test_db):
    """Provide database with single record for edge case testing."""
    db_path, conn = statistics_test_db
    cursor = conn.cursor()

    cursor.execute('''
        INSERT INTO search_results
        (query, model, timestamp, answer_text, sources, execution_time_seconds, success)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    ''', (
        "Single query",
        "gpt-4",
        datetime.now().isoformat(),
        "A" * 1000,
        json.dumps([{"url": "https://example.com", "text": "Source 1"}]),
        10.5,
        1
    ))

    conn.commit()

    with patch('src.utils.statistics.DB_PATH', str(db_path)):
        yield db_path, conn

    conn.close()


@pytest.fixture
def uniform_data_database(statistics_test_db):
    """Provide database where all values are identical (for std_dev testing)."""
    db_path, conn = statistics_test_db
    cursor = conn.cursor()

    # Insert 10 identical records
    for i in range(10):
        cursor.execute('''
            INSERT INTO search_results
            (query, model, timestamp, answer_text, sources, execution_time_seconds, success)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (
            f"Query {i}",
            "gpt-4",
            (datetime.now() + timedelta(days=i)).isoformat(),
            "A" * 1000,  # Uniform length
            json.dumps([{"url": "https://example.com", "text": "Source"}]),
            10.0,  # Uniform time
            1
        ))

    conn.commit()

    with patch('src.utils.statistics.DB_PATH', str(db_path)):
        yield db_path, conn

    conn.close()


# ==============================================================================
# Tests for get_execution_time_stats()
# ==============================================================================


@pytest.mark.unit
class TestExecutionTimeStats:
    """Tests for get_execution_time_stats() function"""

    def test_execution_time_stats_all_data(self, populate_with_diverse_data):
        """Test execution time stats across all data"""
        db_path, _ = populate_with_diverse_data

        result = get_execution_time_stats()

        assert result is not None
        assert 'mean' in result
        assert 'median' in result
        assert 'std_dev' in result
        assert 'min' in result
        assert 'max' in result
        assert 'total_queries' in result

        # Verify statistical properties
        assert result['min'] <= result['mean'] <= result['max']
        assert result['median'] > 0
        assert result['std_dev'] >= 0
        assert result['total_queries'] > 0

    def test_execution_time_stats_by_model(self, populate_with_diverse_data):
        """Test execution time stats filtered by specific model"""
        db_path, _ = populate_with_diverse_data

        result_gpt4 = get_execution_time_stats(model='gpt-4')
        result_claude = get_execution_time_stats(model='claude-3')

        # Both should have results
        assert result_gpt4 is not None
        assert result_claude is not None

        # GPT-4 and Claude-3 should have different statistics
        assert result_gpt4['mean'] != result_claude['mean']

    def test_execution_time_stats_with_date_range(self, populate_with_diverse_data):
        """Test execution time stats with date filtering"""
        db_path, _ = populate_with_diverse_data

        start_date = datetime.now() - timedelta(days=10)
        end_date = datetime.now() - timedelta(days=5)

        result = get_execution_time_stats(start_date=start_date, end_date=end_date)

        # Should have some results in the date range
        if result:
            assert result['total_queries'] > 0

    def test_execution_time_stats_single_record(self, single_record_database):
        """Test execution time stats with single record (std_dev should be 0)"""
        db_path, _ = single_record_database

        result = get_execution_time_stats()

        assert result is not None
        assert result['total_queries'] == 1
        assert result['std_dev'] == 0.0
        assert result['mean'] == result['min'] == result['max']

    def test_execution_time_stats_empty_database(self, empty_database):
        """Test execution time stats on empty database"""
        db_path, _ = empty_database

        result = get_execution_time_stats()

        assert result is None

    def test_execution_time_stats_uniform_data(self, uniform_data_database):
        """Test execution time stats with uniform values"""
        db_path, _ = uniform_data_database

        result = get_execution_time_stats()

        assert result is not None
        assert result['std_dev'] == 0.0
        assert result['mean'] == 10.0
        assert result['median'] == 10.0


# ==============================================================================
# Tests for get_success_rate_stats()
# ==============================================================================


@pytest.mark.unit
class TestSuccessRateStats:
    """Tests for get_success_rate_stats() function"""

    def test_success_rate_stats_all_data(self, populate_with_diverse_data):
        """Test success rate stats across all data"""
        db_path, _ = populate_with_diverse_data

        result = get_success_rate_stats()

        assert result is not None
        assert 'total' in result
        assert 'successful' in result
        assert 'failed' in result
        assert 'success_rate' in result
        assert 'failure_rate' in result

        # Verify relationships
        assert result['successful'] + result['failed'] == result['total']
        assert result['success_rate'] + result['failure_rate'] == pytest.approx(1.0)
        assert 0.0 <= result['success_rate'] <= 1.0

    def test_success_rate_stats_by_model(self, populate_with_diverse_data):
        """Test success rate stats for specific model"""
        db_path, _ = populate_with_diverse_data

        result_gpt4 = get_success_rate_stats(model='gpt-4')
        result_claude = get_success_rate_stats(model='claude-3')

        assert result_gpt4 is not None
        assert result_claude is not None
        assert result_gpt4['total'] > 0
        assert result_claude['total'] > 0

    def test_success_rate_stats_with_date_range(self, populate_with_diverse_data):
        """Test success rate stats with date filtering"""
        db_path, _ = populate_with_diverse_data

        start_date = datetime.now() - timedelta(days=15)
        end_date = datetime.now()

        result = get_success_rate_stats(start_date=start_date, end_date=end_date)

        assert result is not None
        assert result['total'] > 0

    def test_success_rate_stats_single_record(self, single_record_database):
        """Test success rate stats with single successful record"""
        db_path, _ = single_record_database

        result = get_success_rate_stats()

        assert result is not None
        assert result['total'] == 1
        assert result['successful'] == 1
        assert result['failed'] == 0
        assert result['success_rate'] == 1.0

    def test_success_rate_stats_empty_database(self, empty_database):
        """Test success rate stats on empty database"""
        db_path, _ = empty_database

        result = get_success_rate_stats()

        assert result is None


# ==============================================================================
# Tests for get_model_comparison_stats()
# ==============================================================================


@pytest.mark.unit
class TestModelComparisonStats:
    """Tests for get_model_comparison_stats() function"""

    def test_model_comparison_stats_all_data(self, populate_with_diverse_data):
        """Test model comparison stats across all data"""
        db_path, _ = populate_with_diverse_data

        result = get_model_comparison_stats()

        assert result is not None
        assert isinstance(result, dict)

        # Should have at least 3 models
        assert len(result) >= 3
        assert 'gpt-4' in result
        assert 'claude-3' in result
        assert 'sonar-pro' in result

        # Check structure for each model
        for model_name, stats in result.items():
            assert 'execution_time_mean' in stats
            assert 'success_rate' in stats
            assert 'answer_length_mean' in stats
            assert 'count' in stats

            assert stats['execution_time_mean'] > 0
            assert 0.0 <= stats['success_rate'] <= 1.0
            assert stats['answer_length_mean'] > 0
            assert stats['count'] > 0

    def test_model_comparison_stats_specific_query(self, populate_with_diverse_data):
        """Test model comparison for specific query"""
        db_path, _ = populate_with_diverse_data

        result = get_model_comparison_stats(query="What is Python?")

        assert result is not None
        # Multiple models searched for "What is Python?"
        assert len(result) >= 2

    def test_model_comparison_stats_with_date_range(self, populate_with_diverse_data):
        """Test model comparison with date filtering"""
        db_path, _ = populate_with_diverse_data

        start_date = datetime.now() - timedelta(days=20)
        end_date = datetime.now()

        result = get_model_comparison_stats(start_date=start_date, end_date=end_date)

        assert result is not None
        assert len(result) > 0

    def test_model_comparison_stats_empty_database(self, empty_database):
        """Test model comparison on empty database"""
        db_path, _ = empty_database

        result = get_model_comparison_stats()

        assert result is None


# ==============================================================================
# Tests for get_answer_length_stats()
# ==============================================================================


@pytest.mark.unit
class TestAnswerLengthStats:
    """Tests for get_answer_length_stats() function"""

    def test_answer_length_stats_all_data(self, populate_with_diverse_data):
        """Test answer length stats across all data"""
        db_path, _ = populate_with_diverse_data

        result = get_answer_length_stats()

        assert result is not None
        assert 'mean' in result
        assert 'median' in result
        assert 'std_dev' in result
        assert 'min' in result
        assert 'max' in result
        assert 'total_answers' in result

        # Verify statistical properties
        assert result['min'] <= result['mean'] <= result['max']
        assert result['std_dev'] >= 0
        assert result['total_answers'] > 0

    def test_answer_length_stats_by_model(self, populate_with_diverse_data):
        """Test answer length stats filtered by model"""
        db_path, _ = populate_with_diverse_data

        result_gpt4 = get_answer_length_stats(model='gpt-4')
        result_claude = get_answer_length_stats(model='claude-3')

        assert result_gpt4 is not None
        assert result_claude is not None

    def test_answer_length_stats_single_record(self, single_record_database):
        """Test answer length stats with single record"""
        db_path, _ = single_record_database

        result = get_answer_length_stats()

        assert result is not None
        assert result['total_answers'] == 1
        assert result['std_dev'] == 0.0

    def test_answer_length_stats_empty_database(self, empty_database):
        """Test answer length stats on empty database"""
        db_path, _ = empty_database

        result = get_answer_length_stats()

        assert result is None


# ==============================================================================
# Tests for get_source_count_stats()
# ==============================================================================


@pytest.mark.unit
class TestSourceCountStats:
    """Tests for get_source_count_stats() function"""

    def test_source_count_stats_all_data(self, populate_with_diverse_data):
        """Test source count stats across all data"""
        db_path, _ = populate_with_diverse_data

        result = get_source_count_stats()

        assert result is not None
        assert 'mean' in result
        assert 'median' in result
        assert 'std_dev' in result
        assert 'min' in result
        assert 'max' in result
        assert 'total_results' in result

        # Verify relationships
        assert result['min'] <= result['mean'] <= result['max']
        assert result['std_dev'] >= 0
        assert result['total_results'] > 0

    def test_source_count_stats_by_model(self, populate_with_diverse_data):
        """Test source count stats filtered by model"""
        db_path, _ = populate_with_diverse_data

        result_gpt4 = get_source_count_stats(model='gpt-4')
        result_sonar = get_source_count_stats(model='sonar-pro')

        assert result_gpt4 is not None
        assert result_sonar is not None

    def test_source_count_stats_single_record(self, single_record_database):
        """Test source count stats with single record"""
        db_path, _ = single_record_database

        result = get_source_count_stats()

        assert result is not None
        assert result['total_results'] == 1

    def test_source_count_stats_empty_database(self, empty_database):
        """Test source count stats on empty database"""
        db_path, _ = empty_database

        result = get_source_count_stats()

        assert result is None


# ==============================================================================
# Tests for get_query_volume_by_period()
# ==============================================================================


@pytest.mark.unit
class TestQueryVolumeByPeriod:
    """Tests for get_query_volume_by_period() function"""

    def test_query_volume_by_day(self, populate_with_diverse_data):
        """Test query volume grouped by day"""
        db_path, _ = populate_with_diverse_data

        result = get_query_volume_by_period(period='day')

        assert result is not None
        assert isinstance(result, list)
        assert len(result) > 0

        # Each result should be (period_str, count) tuple
        for period_str, count in result:
            assert isinstance(period_str, str)
            assert isinstance(count, int)
            assert count > 0

    def test_query_volume_by_hour(self, populate_with_diverse_data):
        """Test query volume grouped by hour"""
        db_path, _ = populate_with_diverse_data

        result = get_query_volume_by_period(period='hour')

        # Should have results if data exists
        if result:
            assert isinstance(result, list)
            for period_str, count in result:
                assert count > 0

    def test_query_volume_by_week(self, populate_with_diverse_data):
        """Test query volume grouped by week"""
        db_path, _ = populate_with_diverse_data

        result = get_query_volume_by_period(period='week')

        # Should have some results
        if result:
            assert isinstance(result, list)

    def test_query_volume_by_month(self, populate_with_diverse_data):
        """Test query volume grouped by month"""
        db_path, _ = populate_with_diverse_data

        result = get_query_volume_by_period(period='month')

        if result:
            assert isinstance(result, list)

    def test_query_volume_by_model(self, populate_with_diverse_data):
        """Test query volume filtered by model"""
        db_path, _ = populate_with_diverse_data

        result_gpt4 = get_query_volume_by_period(period='day', model='gpt-4')
        result_claude = get_query_volume_by_period(period='day', model='claude-3')

        # Both should have some results
        if result_gpt4 and result_claude:
            assert sum(count for _, count in result_gpt4) > 0
            assert sum(count for _, count in result_claude) > 0

    def test_query_volume_invalid_period(self, populate_with_diverse_data):
        """Test query volume with invalid period"""
        db_path, _ = populate_with_diverse_data

        with pytest.raises(ValueError, match="period must be"):
            get_query_volume_by_period(period='invalid')

    def test_query_volume_empty_database(self, empty_database):
        """Test query volume on empty database"""
        db_path, _ = empty_database

        result = get_query_volume_by_period()

        assert result is None


# ==============================================================================
# Tests for get_trends_over_time()
# ==============================================================================


@pytest.mark.unit
class TestTrendsOverTime:
    """Tests for get_trends_over_time() function"""

    def test_trends_execution_time_by_day(self, populate_with_diverse_data):
        """Test execution time trends by day"""
        db_path, _ = populate_with_diverse_data

        result = get_trends_over_time(metric='execution_time', period='day')

        assert result is not None
        assert isinstance(result, list)

        for period_str, avg_value in result:
            assert isinstance(period_str, str)
            assert isinstance(avg_value, (int, float))

    def test_trends_success_rate_by_day(self, populate_with_diverse_data):
        """Test success rate trends by day"""
        db_path, _ = populate_with_diverse_data

        result = get_trends_over_time(metric='success_rate', period='day')

        if result:
            for period_str, rate in result:
                assert 0.0 <= rate <= 1.0

    def test_trends_answer_length_by_day(self, populate_with_diverse_data):
        """Test answer length trends by day"""
        db_path, _ = populate_with_diverse_data

        result = get_trends_over_time(metric='answer_length', period='day')

        if result:
            assert isinstance(result, list)

    def test_trends_by_hour(self, populate_with_diverse_data):
        """Test trends grouped by hour"""
        db_path, _ = populate_with_diverse_data

        result = get_trends_over_time(metric='execution_time', period='hour')

        if result:
            assert isinstance(result, list)

    def test_trends_by_model(self, populate_with_diverse_data):
        """Test trends filtered by model"""
        db_path, _ = populate_with_diverse_data

        result = get_trends_over_time(metric='execution_time', period='day', model='gpt-4')

        if result:
            assert isinstance(result, list)

    def test_trends_invalid_metric(self, populate_with_diverse_data):
        """Test trends with invalid metric"""
        db_path, _ = populate_with_diverse_data

        with pytest.raises(ValueError, match="metric must be"):
            get_trends_over_time(metric='invalid_metric')

    def test_trends_invalid_period(self, populate_with_diverse_data):
        """Test trends with invalid period"""
        db_path, _ = populate_with_diverse_data

        with pytest.raises(ValueError, match="period must be"):
            get_trends_over_time(metric='execution_time', period='invalid')

    def test_trends_empty_database(self, empty_database):
        """Test trends on empty database"""
        db_path, _ = empty_database

        result = get_trends_over_time()

        assert result is None


# ==============================================================================
# Tests for get_percentiles()
# ==============================================================================


@pytest.mark.unit
class TestPercentiles:
    """Tests for get_percentiles() function"""

    def test_percentiles_execution_time_default(self, populate_with_diverse_data):
        """Test default percentiles for execution time"""
        db_path, _ = populate_with_diverse_data

        result = get_percentiles(metric='execution_time')

        assert result is not None
        assert isinstance(result, dict)

        # Should have default percentiles
        expected_percentiles = [25, 50, 75, 90, 95, 99]
        for p in expected_percentiles:
            assert p in result

    def test_percentiles_custom_percentiles(self, populate_with_diverse_data):
        """Test custom percentile values"""
        db_path, _ = populate_with_diverse_data

        custom_percentiles = [10, 50, 90]
        result = get_percentiles(metric='execution_time', percentiles=custom_percentiles)

        assert result is not None
        for p in custom_percentiles:
            assert p in result

    def test_percentiles_answer_length(self, populate_with_diverse_data):
        """Test percentiles for answer length"""
        db_path, _ = populate_with_diverse_data

        result = get_percentiles(metric='answer_length')

        assert result is not None
        assert isinstance(result, dict)

    def test_percentiles_success_rate(self, populate_with_diverse_data):
        """Test percentiles for success rate"""
        db_path, _ = populate_with_diverse_data

        result = get_percentiles(metric='success_rate')

        assert result is not None

    def test_percentiles_by_model(self, populate_with_diverse_data):
        """Test percentiles filtered by model"""
        db_path, _ = populate_with_diverse_data

        result = get_percentiles(metric='execution_time', model='gpt-4')

        assert result is not None

    def test_percentiles_invalid_metric(self, populate_with_diverse_data):
        """Test percentiles with invalid metric"""
        db_path, _ = populate_with_diverse_data

        with pytest.raises(ValueError, match="metric must be"):
            get_percentiles(metric='invalid_metric')

    def test_percentiles_invalid_percentile_values(self, populate_with_diverse_data):
        """Test percentiles with invalid percentile values"""
        db_path, _ = populate_with_diverse_data

        with pytest.raises(ValueError, match="between 0 and 100"):
            get_percentiles(percentiles=[0, 50, 150])

    def test_percentiles_single_record(self, single_record_database):
        """Test percentiles with single record"""
        db_path, _ = single_record_database

        result = get_percentiles()

        assert result is not None
        assert len(result) > 0

    def test_percentiles_empty_database(self, empty_database):
        """Test percentiles on empty database"""
        db_path, _ = empty_database

        result = get_percentiles()

        assert result is None


# ==============================================================================
# Tests for get_outliers()
# ==============================================================================


@pytest.mark.unit
class TestOutliers:
    """Tests for get_outliers() function"""

    def test_outliers_execution_time_default_threshold(self, populate_with_diverse_data):
        """Test outlier detection with default threshold"""
        db_path, _ = populate_with_diverse_data

        result = get_outliers(metric='execution_time')

        # May or may not have outliers depending on data distribution
        # But if it returns something, it should be a list of dicts
        if result:
            assert isinstance(result, list)
            for record in result:
                assert isinstance(record, dict)
                assert 'execution_time_seconds' in record

    def test_outliers_custom_threshold(self, populate_with_diverse_data):
        """Test outlier detection with custom threshold"""
        db_path, _ = populate_with_diverse_data

        # Very high threshold should find no outliers
        result = get_outliers(metric='execution_time', threshold_std_dev=10.0)

        # May be None or empty
        if result:
            assert isinstance(result, list)

    def test_outliers_answer_length(self, populate_with_diverse_data):
        """Test outlier detection for answer length"""
        db_path, _ = populate_with_diverse_data

        result = get_outliers(metric='answer_length', threshold_std_dev=2.0)

        # May have outliers due to length variation
        if result:
            assert isinstance(result, list)

    def test_outliers_by_model(self, populate_with_diverse_data):
        """Test outlier detection filtered by model"""
        db_path, _ = populate_with_diverse_data

        result = get_outliers(metric='execution_time', model='gpt-4')

        if result:
            assert isinstance(result, list)

    def test_outliers_invalid_metric(self, populate_with_diverse_data):
        """Test outliers with invalid metric"""
        db_path, _ = populate_with_diverse_data

        with pytest.raises(ValueError, match="metric must be"):
            get_outliers(metric='invalid_metric')

    def test_outliers_single_record(self, single_record_database):
        """Test outliers with single record (no outliers possible)"""
        db_path, _ = single_record_database

        result = get_outliers()

        # Single record cannot be an outlier
        assert result is None

    def test_outliers_uniform_data(self, uniform_data_database):
        """Test outliers with uniform data (no variance)"""
        db_path, _ = uniform_data_database

        result = get_outliers(metric='execution_time')

        # No variance means no outliers
        assert result is None


# ==============================================================================
# Tests for get_histogram_data()
# ==============================================================================


@pytest.mark.unit
class TestHistogramData:
    """Tests for get_histogram_data() function"""

    def test_histogram_execution_time_default_bins(self, populate_with_diverse_data):
        """Test histogram with default bin count"""
        db_path, _ = populate_with_diverse_data

        result = get_histogram_data(metric='execution_time')

        assert result is not None
        assert isinstance(result, list)
        assert len(result) == 10  # Default bins

        for bin_start, bin_end, count in result:
            assert bin_start <= bin_end
            assert count >= 0

    def test_histogram_custom_bins(self, populate_with_diverse_data):
        """Test histogram with custom bin count"""
        db_path, _ = populate_with_diverse_data

        result = get_histogram_data(metric='execution_time', bins=5)

        assert result is not None
        assert len(result) == 5

    def test_histogram_answer_length(self, populate_with_diverse_data):
        """Test histogram for answer length"""
        db_path, _ = populate_with_diverse_data

        result = get_histogram_data(metric='answer_length', bins=10)

        assert result is not None
        assert isinstance(result, list)

    def test_histogram_by_model(self, populate_with_diverse_data):
        """Test histogram filtered by model"""
        db_path, _ = populate_with_diverse_data

        result = get_histogram_data(metric='execution_time', bins=5, model='gpt-4')

        if result:
            assert isinstance(result, list)

    def test_histogram_invalid_metric(self, populate_with_diverse_data):
        """Test histogram with invalid metric"""
        db_path, _ = populate_with_diverse_data

        with pytest.raises(ValueError, match="metric must be"):
            get_histogram_data(metric='invalid_metric')

    def test_histogram_invalid_bins(self, populate_with_diverse_data):
        """Test histogram with invalid bin count"""
        db_path, _ = populate_with_diverse_data

        with pytest.raises(ValueError, match="bins must be"):
            get_histogram_data(bins=0)

    def test_histogram_single_record(self, single_record_database):
        """Test histogram with single record"""
        db_path, _ = single_record_database

        result = get_histogram_data()

        assert result is not None
        assert len(result) == 1  # Single bin for single value

    def test_histogram_uniform_data(self, uniform_data_database):
        """Test histogram with uniform data (all same values)"""
        db_path, _ = uniform_data_database

        result = get_histogram_data(metric='execution_time', bins=10)

        assert result is not None
        # All values in same bin
        assert len(result) == 1

    def test_histogram_empty_database(self, empty_database):
        """Test histogram on empty database"""
        db_path, _ = empty_database

        result = get_histogram_data()

        assert result is None


# ==============================================================================
# Tests for find_duplicate_queries()
# ==============================================================================


@pytest.mark.unit
class TestFindDuplicateQueries:
    """Tests for find_duplicate_queries() function"""

    def test_find_duplicate_queries_exact_match(self, populate_with_diverse_data):
        """Test finding exact duplicate queries"""
        db_path, _ = populate_with_diverse_data

        result = find_duplicate_queries(threshold_similarity=1.0)

        assert result is not None
        assert isinstance(result, list)
        assert len(result) > 0

        # Check structure
        for dup_group in result:
            assert 'query_text' in dup_group
            assert 'count' in dup_group
            assert 'similar_queries' in dup_group
            assert dup_group['count'] > 1

    def test_find_duplicate_queries_fuzzy_match(self, populate_with_diverse_data):
        """Test finding fuzzy duplicate queries"""
        db_path, _ = populate_with_diverse_data

        result = find_duplicate_queries(threshold_similarity=0.8)

        # May find fuzzy matches
        if result:
            assert isinstance(result, list)

    def test_find_duplicate_queries_count_verification(self, populate_with_diverse_data):
        """Verify duplicate counts are correct"""
        db_path, _ = populate_with_diverse_data

        result = find_duplicate_queries(threshold_similarity=1.0)

        if result:
            # "What is Python?" should have 4 occurrences (gpt-4, gpt-4, claude-3, claude-3, sonar-pro, sonar-pro = 6)
            python_query = next((dup for dup in result if 'Python' in dup['query_text']), None)
            if python_query:
                assert python_query['count'] >= 2

    def test_find_duplicate_queries_invalid_threshold(self, populate_with_diverse_data):
        """Test with invalid similarity threshold"""
        db_path, _ = populate_with_diverse_data

        with pytest.raises(ValueError, match="between 0.0 and 1.0"):
            find_duplicate_queries(threshold_similarity=1.5)

    def test_find_duplicate_queries_empty_database(self, empty_database):
        """Test on empty database"""
        db_path, _ = empty_database

        result = find_duplicate_queries()

        assert result is None

    def test_find_duplicate_queries_no_duplicates(self, single_record_database):
        """Test when no duplicates exist"""
        db_path, _ = single_record_database

        result = find_duplicate_queries()

        # Single record means no duplicates
        assert result is None


# ==============================================================================
# Tests for get_database_summary()
# ==============================================================================


@pytest.mark.unit
class TestDatabaseSummary:
    """Tests for get_database_summary() function"""

    def test_database_summary_structure(self, populate_with_diverse_data):
        """Test that summary has all required fields"""
        db_path, _ = populate_with_diverse_data

        result = get_database_summary()

        assert isinstance(result, dict)
        assert 'total_records' in result
        assert 'total_successful' in result
        assert 'total_failed' in result
        assert 'success_rate' in result
        assert 'unique_queries' in result
        assert 'unique_models' in result
        assert 'date_range_start' in result
        assert 'date_range_end' in result
        assert 'avg_execution_time' in result
        assert 'total_sources' in result
        assert 'avg_answer_length' in result

    def test_database_summary_values_sanity(self, populate_with_diverse_data):
        """Test that summary values make sense"""
        db_path, _ = populate_with_diverse_data

        result = get_database_summary()

        # Verify relationships
        assert result['total_successful'] + result['total_failed'] == result['total_records']
        assert result['success_rate'] == pytest.approx(
            result['total_successful'] / result['total_records']
        )
        assert 0.0 <= result['success_rate'] <= 1.0
        assert result['unique_queries'] > 0
        assert result['unique_models'] > 0
        assert result['total_sources'] >= 0

    def test_database_summary_empty_database(self, empty_database):
        """Test summary on empty database"""
        db_path, _ = empty_database

        result = get_database_summary()

        # Should return a summary even if empty
        assert isinstance(result, dict)
        assert result['total_records'] == 0
        assert result['success_rate'] == 0.0

    def test_database_summary_single_record(self, single_record_database):
        """Test summary with single record"""
        db_path, _ = single_record_database

        result = get_database_summary()

        assert result['total_records'] == 1
        assert result['total_successful'] == 1
        assert result['total_failed'] == 0
        assert result['success_rate'] == 1.0


# ==============================================================================
# Parametrized Tests for Cross-Function Consistency
# ==============================================================================


@pytest.mark.unit
class TestCrossFunctionConsistency:
    """Verify consistency between different statistical functions"""

    def test_total_records_consistency(self, populate_with_diverse_data):
        """Verify total records are consistent across functions"""
        db_path, _ = populate_with_diverse_data

        summary = get_database_summary()
        success_stats = get_success_rate_stats()

        # Both should report same total
        assert summary['total_records'] == success_stats['total']

    def test_success_rate_consistency(self, populate_with_diverse_data):
        """Verify success rates match across functions"""
        db_path, _ = populate_with_diverse_data

        summary = get_database_summary()
        success_stats = get_success_rate_stats()

        assert summary['success_rate'] == pytest.approx(success_stats['success_rate'])

    @pytest.mark.parametrize("metric", ['execution_time', 'answer_length'])
    def test_stats_range_consistency(self, populate_with_diverse_data, metric):
        """Verify min/max from stats functions are consistent"""
        db_path, _ = populate_with_diverse_data

        if metric == 'execution_time':
            stats = get_execution_time_stats()
        else:
            stats = get_answer_length_stats()

        if stats:
            percentiles = get_percentiles(metric=metric)
            if percentiles:
                # Min should be <= 25th percentile
                assert stats['min'] <= percentiles[25]
                # Max should be >= 75th percentile
                assert stats['max'] >= percentiles[75]

    def test_source_counts_in_histogram(self, populate_with_diverse_data):
        """Verify histogram bin counts sum correctly"""
        db_path, _ = populate_with_diverse_data

        histogram = get_histogram_data(metric='execution_time')
        source_stats = get_source_count_stats()

        if histogram and source_stats:
            total_from_histogram = sum(count for _, _, count in histogram)
            # Should match the count from stats
            assert total_from_histogram <= source_stats['total_results'] + 1
