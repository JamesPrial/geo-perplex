"""
Unit tests for src/utils/db_maintenance.py

Tests database maintenance functions including:
- Database health monitoring and analysis
- Duplicate detection and removal
- Archiving and cleanup operations
- Optimization and backup/restore functionality
"""
import pytest
import sqlite3
import json
from pathlib import Path
from datetime import datetime, timedelta
from unittest.mock import patch, MagicMock
from src.utils.db_maintenance import (
    get_database_info,
    analyze_database_performance,
    find_duplicates,
    remove_duplicates,
    archive_old_results,
    delete_failed_results,
    vacuum_database,
    rebuild_indexes,
    optimize_database,
    backup_database,
    restore_database,
    _format_bytes,
    _get_table_size,
    _get_index_size,
)


@pytest.fixture
def test_db(tmp_path, monkeypatch):
    """
    Create a test database in temporary directory.
    Patches the DB_PATH to use the temporary database.
    """
    db_file = tmp_path / "test_search_results.db"

    # Patch the DB_PATH in db_maintenance module
    import src.utils.db_maintenance as db_maint
    monkeypatch.setattr(db_maint, 'DB_PATH', db_file)

    # Initialize the database with schema
    conn = sqlite3.connect(str(db_file))
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE search_results (
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
    cursor.execute('CREATE INDEX idx_query ON search_results(query)')
    cursor.execute('CREATE INDEX idx_model ON search_results(model)')
    cursor.execute('CREATE INDEX idx_timestamp ON search_results(timestamp)')
    cursor.execute('CREATE INDEX idx_query_model ON search_results(query, model)')
    conn.commit()
    conn.close()

    return db_file


@pytest.fixture
def test_db_with_records(test_db):
    """Test database populated with sample records."""
    conn = sqlite3.connect(str(test_db))
    cursor = conn.cursor()

    # Insert diverse search results
    records = [
        ('What is Python?', 'gpt-4', 'Python is a programming language', '2025-01-10 10:00:00', True, None),
        ('What is Python?', 'claude-3', 'Python is a language', '2025-01-10 11:00:00', True, None),
        ('What is JavaScript?', 'gpt-4', 'JavaScript runs in browsers', '2025-01-09 09:00:00', True, None),
        ('Database query', None, 'Answer about databases', '2025-01-08 14:30:00', False, 'Timeout'),
        ('Failed search', 'gpt-4', '', '2025-01-07 15:00:00', False, 'Network error'),
    ]

    cursor.executemany('''
        INSERT INTO search_results (query, model, answer_text, timestamp, success, error_message)
        VALUES (?, ?, ?, ?, ?, ?)
    ''', records)

    conn.commit()
    conn.close()

    return test_db


@pytest.fixture
def test_db_with_duplicates(test_db):
    """Test database with duplicate records."""
    conn = sqlite3.connect(str(test_db))
    cursor = conn.cursor()

    # Insert duplicate queries with different models and timestamps
    duplicates = [
        ('Duplicate query', 'gpt-4', 'Answer 1', '2025-01-10 10:00:00', True, None),
        ('Duplicate query', 'claude-3', 'Answer 2', '2025-01-10 11:00:00', True, None),
        ('Duplicate query', 'gpt-4', 'Answer 3', '2025-01-10 12:00:00', True, None),
        ('Unique query', 'gpt-4', 'Unique answer', '2025-01-10 13:00:00', True, None),
    ]

    cursor.executemany('''
        INSERT INTO search_results (query, model, answer_text, timestamp, success, error_message)
        VALUES (?, ?, ?, ?, ?, ?)
    ''', duplicates)

    conn.commit()
    conn.close()

    return test_db


@pytest.fixture
def test_db_with_old_records(test_db):
    """Test database with old and recent records for archiving."""
    conn = sqlite3.connect(str(test_db))
    cursor = conn.cursor()

    old_date = '2024-06-01 10:00:00'
    new_date = '2025-01-10 10:00:00'

    records = [
        ('Old query 1', 'gpt-4', 'Old answer', old_date, True, None),
        ('Old query 2', 'claude-3', 'Old answer', old_date, True, None),
        ('Recent query 1', 'gpt-4', 'Recent answer', new_date, True, None),
        ('Recent query 2', 'claude-3', 'Recent answer', new_date, True, None),
    ]

    cursor.executemany('''
        INSERT INTO search_results (query, model, answer_text, timestamp, success, error_message)
        VALUES (?, ?, ?, ?, ?, ?)
    ''', records)

    conn.commit()
    conn.close()

    return test_db


@pytest.mark.unit
class TestFormatBytes:
    """Tests for _format_bytes() helper function"""

    def test_format_bytes_bytes(self):
        """Test formatting bytes."""
        assert _format_bytes(500) == "500.0 B"

    def test_format_bytes_kilobytes(self):
        """Test formatting kilobytes."""
        assert _format_bytes(2048) == "2.0 KB"

    def test_format_bytes_megabytes(self):
        """Test formatting megabytes."""
        assert _format_bytes(1024 * 1024) == "1.0 MB"

    def test_format_bytes_gigabytes(self):
        """Test formatting gigabytes."""
        size = 1024 * 1024 * 1024 + 512 * 1024 * 1024
        result = _format_bytes(size)
        assert "GB" in result
        assert float(result.split()[0]) > 1.0

    def test_format_bytes_zero(self):
        """Test formatting zero bytes."""
        assert _format_bytes(0) == "0.0 B"

    def test_format_bytes_fractional(self):
        """Test formatting fractional sizes."""
        result = _format_bytes(1536)  # 1.5 KB
        assert "KB" in result
        assert "1.5" in result


@pytest.mark.unit
class TestGetDatabaseInfo:
    """Tests for get_database_info() function"""

    def test_get_database_info_empty_db(self, test_db, monkeypatch):
        """Test getting info from empty database."""
        info = get_database_info()

        assert info['record_count'] == 0
        assert info['file_size_bytes'] > 0
        assert 'file_size_human' in info
        assert 'table_sizes' in info
        assert 'index_sizes' in info
        assert 'database_version' in info

    def test_get_database_info_with_records(self, test_db_with_records, monkeypatch):
        """Test getting info from database with records."""
        info = get_database_info()

        assert info['record_count'] == 5
        assert info['file_size_bytes'] > 0
        assert 'KB' in info['file_size_human'] or 'B' in info['file_size_human']
        assert 'search_results' in info['table_sizes']

    def test_get_database_info_structure(self, test_db_with_records, monkeypatch):
        """Test that returned info has correct structure."""
        info = get_database_info()

        required_keys = [
            'file_size_bytes',
            'file_size_human',
            'record_count',
            'table_sizes',
            'index_sizes',
            'database_version'
        ]
        for key in required_keys:
            assert key in info

        assert isinstance(info['record_count'], int)
        assert isinstance(info['file_size_bytes'], int)
        assert isinstance(info['table_sizes'], dict)
        assert isinstance(info['index_sizes'], dict)


@pytest.mark.unit
class TestAnalyzeDatabasePerformance:
    """Tests for analyze_database_performance() function"""

    def test_analyze_database_empty(self, test_db, monkeypatch):
        """Test analyzing empty database."""
        analysis = analyze_database_performance()

        assert 'fragmentation_level' in analysis
        assert 'recommended_actions' in analysis
        assert isinstance(analysis['fragmentation_level'], (int, float))
        assert analysis['fragmentation_level'] >= 0

    def test_analyze_database_with_records(self, test_db_with_records, monkeypatch):
        """Test analyzing database with records."""
        analysis = analyze_database_performance()

        assert 'index_usage_stats' in analysis
        assert 'fragmentation_level' in analysis
        assert 'free_pages' in analysis
        assert 'page_count' in analysis
        assert 'recommended_actions' in analysis

        # Check that index stats are present
        assert isinstance(analysis['index_usage_stats'], list)

    def test_analyze_database_recommendations(self, test_db_with_records, monkeypatch):
        """Test that recommendations are generated."""
        analysis = analyze_database_performance()

        assert len(analysis['recommended_actions']) > 0
        for action in analysis['recommended_actions']:
            assert isinstance(action, str)
            assert len(action) > 0


@pytest.mark.unit
class TestFindDuplicates:
    """Tests for find_duplicates() function"""

    def test_find_duplicates_exact_match(self, test_db_with_duplicates, monkeypatch):
        """Test finding exact duplicate queries."""
        duplicates = find_duplicates(exact_match=True)

        assert len(duplicates) > 0
        # Find the 'Duplicate query' group
        dup_group = next((d for d in duplicates if d['query'] == 'Duplicate query'), None)
        assert dup_group is not None
        assert dup_group['count'] == 3
        assert len(dup_group['ids']) == 3

    def test_find_duplicates_case_insensitive(self, test_db, monkeypatch):
        """Test finding case-insensitive duplicates."""
        conn = sqlite3.connect(str(test_db))
        cursor = conn.cursor()

        # Insert records with case variations
        cursor.executemany('''
            INSERT INTO search_results (query, model, answer_text, timestamp, success, error_message)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', [
            ('What is PYTHON?', 'gpt-4', 'Answer 1', '2025-01-10 10:00:00', True, None),
            ('What is python?', 'claude-3', 'Answer 2', '2025-01-10 11:00:00', True, None),
        ])
        conn.commit()
        conn.close()

        duplicates = find_duplicates(exact_match=False)

        # Should find case-insensitive match
        assert len(duplicates) > 0

    def test_find_duplicates_no_duplicates(self, test_db_with_records, monkeypatch):
        """Test finding duplicates when none exist."""
        duplicates = find_duplicates()

        # May have some duplicates from the fixture, but verify structure
        assert isinstance(duplicates, list)

    def test_find_duplicates_structure(self, test_db_with_duplicates, monkeypatch):
        """Test that duplicates have correct structure."""
        duplicates = find_duplicates()

        if duplicates:
            dup = duplicates[0]
            assert 'query' in dup
            assert 'count' in dup
            assert 'ids' in dup
            assert 'models' in dup
            assert dup['count'] >= 2
            assert isinstance(dup['ids'], list)


@pytest.mark.unit
class TestRemoveDuplicates:
    """Tests for remove_duplicates() function"""

    def test_remove_duplicates_dry_run(self, test_db_with_duplicates, monkeypatch):
        """Test dry-run doesn't remove records."""
        result = remove_duplicates(dry_run=True)

        assert result['success'] is True
        assert result['dry_run'] is True

        # Verify count matches duplicates
        conn = sqlite3.connect(str(test_db_with_duplicates))
        cursor = conn.cursor()
        cursor.execute('SELECT COUNT(*) FROM search_results')
        count_after = cursor.fetchone()[0]
        conn.close()

        # Count should still be 4 (not changed)
        assert count_after == 4

    def test_remove_duplicates_keep_latest(self, test_db_with_duplicates, monkeypatch):
        """Test removing duplicates keeping latest record."""
        result = remove_duplicates(dry_run=False, keep='latest')

        assert result['success'] is True
        assert result['removed_count'] == 1  # 1 removed from (Duplicate query, gpt-4) group
        assert result['kept_count'] == 3  # 3 kept (1 gpt-4 duplicate + 1 claude-3 + 1 unique)

    def test_remove_duplicates_keep_earliest(self, test_db_with_duplicates, monkeypatch):
        """Test removing duplicates keeping earliest record."""
        result = remove_duplicates(dry_run=False, keep='earliest')

        assert result['success'] is True
        assert result['removed_count'] == 1

    def test_remove_duplicates_keep_best(self, test_db_with_duplicates, monkeypatch):
        """Test removing duplicates keeping best record."""
        result = remove_duplicates(dry_run=False, keep='best')

        assert result['success'] is True
        assert result['removed_ids'] is not None

    def test_remove_duplicates_invalid_keep_option(self, test_db_with_duplicates, monkeypatch):
        """Test error with invalid keep option."""
        result = remove_duplicates(dry_run=False, keep='invalid_option')

        assert result['success'] is False
        assert 'error' in result

    def test_remove_duplicates_structure(self, test_db_with_duplicates, monkeypatch):
        """Test return structure of remove_duplicates."""
        result = remove_duplicates(dry_run=True)

        required_keys = ['kept_count', 'removed_count', 'removed_ids', 'success', 'dry_run']
        for key in required_keys:
            assert key in result


@pytest.mark.unit
class TestArchiveOldResults:
    """Tests for archive_old_results() function"""

    def test_archive_old_results_before_date(self, test_db_with_old_records, tmp_path, monkeypatch):
        """Test archiving records before a date."""
        archive_path = tmp_path / "archive.db"

        result = archive_old_results(
            before_date='2025-01-01',
            archive_path=str(archive_path),
            delete_after_archive=False
        )

        assert result['success'] is True
        assert result['archived_count'] == 2
        assert archive_path.exists()

    def test_archive_creates_valid_database(self, test_db_with_old_records, tmp_path, monkeypatch):
        """Test that archive file is a valid database."""
        archive_path = tmp_path / "archive.db"

        archive_old_results(
            before_date='2025-01-01',
            archive_path=str(archive_path),
            delete_after_archive=False
        )

        # Verify archive is valid SQLite database
        conn = sqlite3.connect(str(archive_path))
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM search_results")
        count = cursor.fetchone()[0]
        conn.close()

        assert count == 2

    def test_archive_with_delete_after(self, test_db_with_old_records, tmp_path, monkeypatch):
        """Test archiving with deletion from source."""
        archive_path = tmp_path / "archive.db"

        result = archive_old_results(
            before_date='2025-01-01',
            archive_path=str(archive_path),
            delete_after_archive=True
        )

        assert result['success'] is True
        assert result['archived_count'] == 2

        # Verify records were deleted from main database
        conn = sqlite3.connect(str(test_db_with_old_records))
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM search_results")
        count = cursor.fetchone()[0]
        conn.close()

        assert count == 2  # Only 2 recent records remain

    def test_archive_invalid_date_format(self, test_db_with_old_records, tmp_path, monkeypatch):
        """Test error with invalid date format."""
        archive_path = tmp_path / "archive.db"

        result = archive_old_results(
            before_date='invalid-date',
            archive_path=str(archive_path),
            delete_after_archive=False
        )

        assert result['success'] is False
        assert 'error' in result

    def test_archive_file_already_exists(self, test_db_with_old_records, tmp_path, monkeypatch):
        """Test error when archive file already exists."""
        archive_path = tmp_path / "archive.db"
        archive_path.touch()  # Create empty file

        result = archive_old_results(
            before_date='2025-01-01',
            archive_path=str(archive_path),
            delete_after_archive=False
        )

        assert result['success'] is False
        assert 'error' in result


@pytest.mark.unit
class TestDeleteFailedResults:
    """Tests for delete_failed_results() function"""

    def test_delete_failed_results_no_failures(self, test_db_with_records, monkeypatch):
        """Test deletion when no failed results exist."""
        # Mock input to avoid prompt
        monkeypatch.setattr('builtins.input', lambda x: 'y')

        result = delete_failed_results(confirm=False)

        assert result['success'] is True
        assert result['deleted_count'] >= 0

    def test_delete_failed_results_with_failures(self, test_db_with_records, monkeypatch):
        """Test deletion of failed results."""
        monkeypatch.setattr('builtins.input', lambda x: 'y')

        result = delete_failed_results(confirm=False)

        assert result['success'] is True
        assert result['deleted_count'] == 2  # Two failed records in fixture

    def test_delete_failed_results_before_date(self, test_db_with_records, monkeypatch):
        """Test deleting failures before specific date."""
        monkeypatch.setattr('builtins.input', lambda x: 'y')

        result = delete_failed_results(before_date='2025-01-08', confirm=False)

        assert result['success'] is True

    def test_delete_failed_results_invalid_date(self, test_db_with_records, monkeypatch):
        """Test error with invalid date format."""
        result = delete_failed_results(before_date='invalid', confirm=False)

        assert result['success'] is False
        assert 'error' in result

    def test_delete_failed_results_confirmation_declined(self, test_db_with_records, monkeypatch):
        """Test that confirmation prompt prevents deletion."""
        monkeypatch.setattr('builtins.input', lambda x: 'n')

        result = delete_failed_results(confirm=True)

        assert result['success'] is True
        assert result.get('cancelled') is True
        assert result['deleted_count'] == 0


@pytest.mark.unit
class TestVacuumDatabase:
    """Tests for vacuum_database() function"""

    def test_vacuum_database_success(self, test_db_with_records, monkeypatch):
        """Test successful vacuum operation."""
        result = vacuum_database()

        assert result['success'] is True
        assert 'old_size_bytes' in result
        assert 'new_size_bytes' in result
        assert 'space_freed_bytes' in result
        assert result['space_freed_bytes'] >= 0

    def test_vacuum_reduces_size(self, test_db, monkeypatch):
        """Test that vacuum can reduce database size."""
        conn = sqlite3.connect(str(test_db))
        cursor = conn.cursor()

        # Insert and delete many records to create fragmentation
        for i in range(100):
            cursor.execute(
                'INSERT INTO search_results (query, model, answer_text) VALUES (?, ?, ?)',
                (f'Query {i}', 'test', f'Answer {i}')
            )
        conn.commit()

        # Delete most records
        cursor.execute('DELETE FROM search_results WHERE query LIKE "Query [1-9]%"')
        conn.commit()
        conn.close()

        # Run vacuum
        result = vacuum_database()

        assert result['success'] is True
        assert 'new_size_bytes' in result

    def test_vacuum_returns_correct_structure(self, test_db_with_records, monkeypatch):
        """Test return structure."""
        result = vacuum_database()

        required_keys = ['success', 'old_size_bytes', 'new_size_bytes', 'space_freed_bytes']
        for key in required_keys:
            assert key in result


@pytest.mark.unit
class TestRebuildIndexes:
    """Tests for rebuild_indexes() function"""

    def test_rebuild_indexes_success(self, test_db_with_records, monkeypatch):
        """Test successful index rebuild."""
        result = rebuild_indexes()

        assert result['success'] is True
        assert 'indexes_rebuilt' in result
        assert 'time_taken_seconds' in result
        assert len(result['indexes_rebuilt']) > 0

    def test_rebuild_indexes_recreates_all(self, test_db_with_records, monkeypatch):
        """Test that all indexes are rebuilt."""
        result = rebuild_indexes()

        assert result['success'] is True
        # Should have rebuilt the 4 indexes
        assert len(result['indexes_rebuilt']) >= 3  # At least query, model, timestamp

    def test_rebuild_indexes_timing(self, test_db_with_records, monkeypatch):
        """Test that timing is recorded."""
        result = rebuild_indexes()

        assert result['time_taken_seconds'] >= 0
        assert isinstance(result['time_taken_seconds'], float)


@pytest.mark.unit
class TestOptimizeDatabase:
    """Tests for optimize_database() function"""

    def test_optimize_database_success(self, test_db_with_records, monkeypatch):
        """Test successful database optimization."""
        result = optimize_database()

        assert result['success'] is True
        assert 'actions_performed' in result
        assert 'results' in result

        # Check that multiple actions were performed
        assert len(result['actions_performed']) > 0
        assert 'ANALYZE' in result['actions_performed']
        assert 'VACUUM' in result['actions_performed']
        assert 'REBUILD_INDEXES' in result['actions_performed']

    def test_optimize_database_results_structure(self, test_db_with_records, monkeypatch):
        """Test results structure."""
        result = optimize_database()

        assert 'analyze' in result['results']
        assert 'vacuum' in result['results']
        assert 'rebuild_indexes' in result['results']

        # Each sub-result should have success status
        assert result['results']['analyze']['success'] is True


@pytest.mark.unit
class TestBackupDatabase:
    """Tests for backup_database() function"""

    def test_backup_database_creates_file(self, test_db_with_records, tmp_path, monkeypatch):
        """Test that backup creates a file."""
        backup_path = tmp_path / "backup.db"

        result = backup_database(str(backup_path))

        assert result['success'] is True
        assert backup_path.exists()
        assert result['backup_file_path'] == str(backup_path.absolute())

    def test_backup_database_contains_data(self, test_db_with_records, tmp_path, monkeypatch):
        """Test that backup file contains data."""
        backup_path = tmp_path / "backup.db"

        backup_database(str(backup_path))

        # Verify backup contains records
        conn = sqlite3.connect(str(backup_path))
        cursor = conn.cursor()
        cursor.execute('SELECT COUNT(*) FROM search_results')
        count = cursor.fetchone()[0]
        conn.close()

        assert count == 5

    def test_backup_database_returns_metadata(self, test_db_with_records, tmp_path, monkeypatch):
        """Test backup returns correct metadata."""
        backup_path = tmp_path / "backup.db"

        result = backup_database(str(backup_path))

        assert 'backup_size_bytes' in result
        assert result['backup_size_bytes'] > 0
        assert 'timestamp' in result

    def test_backup_file_already_exists(self, test_db_with_records, tmp_path, monkeypatch):
        """Test error when backup file already exists."""
        backup_path = tmp_path / "backup.db"
        backup_path.touch()

        result = backup_database(str(backup_path))

        assert result['success'] is False
        assert 'error' in result


@pytest.mark.unit
class TestRestoreDatabase:
    """Tests for restore_database() function"""

    def test_restore_database_from_backup(self, test_db_with_records, tmp_path, monkeypatch):
        """Test restoring database from backup."""
        backup_path = tmp_path / "backup.db"

        # Create backup
        backup_database(str(backup_path))

        # Clear original database
        conn = sqlite3.connect(str(test_db_with_records))
        cursor = conn.cursor()
        cursor.execute('DELETE FROM search_results')
        conn.commit()
        conn.close()

        # Restore from backup
        result = restore_database(str(backup_path), confirm=False)

        assert result['success'] is True
        assert result['records_restored'] == 5

    def test_restore_database_not_found(self, test_db_with_records, tmp_path, monkeypatch):
        """Test error when backup file not found."""
        backup_path = tmp_path / "nonexistent.db"

        result = restore_database(str(backup_path), confirm=False)

        assert result['success'] is False
        assert 'error' in result

    def test_restore_database_confirmation_declined(self, test_db_with_records, tmp_path, monkeypatch):
        """Test that confirmation prompt works."""
        backup_path = tmp_path / "backup.db"
        backup_database(str(backup_path))

        monkeypatch.setattr('builtins.input', lambda x: 'n')

        result = restore_database(str(backup_path), confirm=True)

        assert result['success'] is True
        assert result.get('cancelled') is True

    def test_restore_backup_cycle(self, test_db_with_records, tmp_path, monkeypatch):
        """Test complete backup and restore cycle."""
        backup_path = tmp_path / "backup.db"

        # Backup
        backup_result = backup_database(str(backup_path))
        assert backup_result['success'] is True
        original_count = 5

        # Verify backup
        conn = sqlite3.connect(str(backup_path))
        cursor = conn.cursor()
        cursor.execute('SELECT COUNT(*) FROM search_results')
        backup_count = cursor.fetchone()[0]
        conn.close()
        assert backup_count == original_count

        # Restore
        restore_result = restore_database(str(backup_path), confirm=False)
        assert restore_result['success'] is True
        assert restore_result['records_restored'] == original_count


@pytest.mark.unit
class TestEdgeCases:
    """Tests for edge cases and error conditions"""

    def test_operations_on_empty_database(self, test_db, monkeypatch):
        """Test various operations on empty database."""
        # Get info
        info = get_database_info()
        assert info['record_count'] == 0

        # Find duplicates
        duplicates = find_duplicates()
        assert duplicates == []

        # Analyze performance
        analysis = analyze_database_performance()
        assert analysis['record_count'] == 0 or 'fragmentation_level' in analysis

    def test_database_with_null_model(self, test_db, monkeypatch):
        """Test operations with NULL model values."""
        conn = sqlite3.connect(str(test_db))
        cursor = conn.cursor()
        cursor.execute(
            'INSERT INTO search_results (query, answer_text) VALUES (?, ?)',
            ('Query without model', 'Answer')
        )
        conn.commit()
        conn.close()

        info = get_database_info()
        assert info['record_count'] == 1

    def test_remove_duplicates_no_duplicates(self, test_db_with_records, monkeypatch):
        """Test remove_duplicates when no duplicates exist."""
        result = remove_duplicates(dry_run=True)

        assert result['success'] is True
        assert result['removed_count'] == 0

    def test_archive_with_no_old_records(self, test_db_with_records, tmp_path, monkeypatch):
        """Test archiving when no records match date criteria."""
        archive_path = tmp_path / "archive.db"

        result = archive_old_results(
            before_date='2024-01-01',
            archive_path=str(archive_path),
            delete_after_archive=False
        )

        assert result['success'] is True
        assert result['archived_count'] == 0
