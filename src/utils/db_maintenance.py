"""
Database maintenance utilities for GEO-Perplex search results
Provides health monitoring, cleanup, optimization, and backup/restore functionality
"""

import sqlite3
import shutil
import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any

logger = logging.getLogger(__name__)

# Database file location
DB_PATH = Path(__file__).parent.parent.parent / 'search_results.db'

# Index definitions matching storage.py
INDEXES = [
    'idx_query',
    'idx_model',
    'idx_timestamp',
    'idx_query_model',
]


def _get_connection() -> sqlite3.Connection:
    """Create a database connection with proper configuration.

    Returns:
        sqlite3.Connection: Database connection object
    """
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    return conn


def _format_bytes(size_bytes: int) -> str:
    """Format byte size into human-readable string.

    Args:
        size_bytes: Size in bytes

    Returns:
        Formatted string (e.g., "1.5 MB", "230 KB")
    """
    for unit in ['B', 'KB', 'MB', 'GB']:
        if size_bytes < 1024:
            return f"{size_bytes:.1f} {unit}"
        size_bytes /= 1024
    return f"{size_bytes:.1f} TB"


def _get_table_size(conn: sqlite3.Connection, table_name: str) -> int:
    """Get approximate size of a table in bytes.

    Args:
        conn: Database connection
        table_name: Name of the table

    Returns:
        Approximate size in bytes
    """
    cursor = conn.cursor()
    cursor.execute(f'SELECT SUM(pgsize) FROM dbstat WHERE name=?', (table_name,))
    result = cursor.fetchone()
    return result[0] if result and result[0] else 0


def _get_index_size(conn: sqlite3.Connection, index_name: str) -> int:
    """Get approximate size of an index in bytes.

    Args:
        conn: Database connection
        index_name: Name of the index

    Returns:
        Approximate size in bytes
    """
    cursor = conn.cursor()
    cursor.execute(f'SELECT SUM(pgsize) FROM dbstat WHERE name=?', (index_name,))
    result = cursor.fetchone()
    return result[0] if result and result[0] else 0


def get_database_info() -> Dict[str, Any]:
    """Get comprehensive database health information.

    Returns:
        Dictionary containing:
        - file_size_bytes: Database file size in bytes
        - file_size_human: Human-readable file size
        - record_count: Total records in search_results table
        - table_sizes: Dict mapping table names to sizes
        - index_sizes: Dict mapping index names to sizes
        - database_version: SQLite version string

    Example:
        >>> info = get_database_info()
        >>> print(f"Database: {info['file_size_human']}")
        >>> print(f"Records: {info['record_count']}")
    """
    try:
        with sqlite3.connect(str(DB_PATH)) as conn:
            cursor = conn.cursor()

            # Get file size
            file_size = DB_PATH.stat().st_size if DB_PATH.exists() else 0

            # Get record count
            cursor.execute('SELECT COUNT(*) FROM search_results')
            record_count = cursor.fetchone()[0]

            # Get table sizes
            table_sizes = {}
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
            for row in cursor.fetchall():
                table_name = row[0]
                table_sizes[table_name] = _get_table_size(conn, table_name)

            # Get index sizes
            index_sizes = {}
            cursor.execute("SELECT name FROM sqlite_master WHERE type='index'")
            for row in cursor.fetchall():
                index_name = row[0]
                index_sizes[index_name] = _get_index_size(conn, index_name)

            # Get SQLite version
            cursor.execute('SELECT sqlite_version()')
            db_version = cursor.fetchone()[0]

        return {
            'file_size_bytes': file_size,
            'file_size_human': _format_bytes(file_size),
            'record_count': record_count,
            'table_sizes': table_sizes,
            'index_sizes': index_sizes,
            'database_version': db_version,
        }
    except Exception as e:
        logger.error(f"Failed to get database info: {e}")
        return {'success': False, 'error': str(e)}


def analyze_database_performance() -> Dict[str, Any]:
    """Analyze database performance and fragmentation.

    Returns:
        Dictionary containing:
        - record_count: Total number of records in the database
        - index_usage_stats: Information about index utilization
        - fragmentation_level: Estimated fragmentation percentage
        - free_pages: Number of free pages in database
        - page_count: Total number of pages in database
        - recommended_actions: List of recommended optimizations

    Example:
        >>> analysis = analyze_database_performance()
        >>> print(f"Records: {analysis['record_count']}")
        >>> for action in analysis['recommended_actions']:
        ...     print(f"Recommended: {action}")
    """
    try:
        with sqlite3.connect(str(DB_PATH)) as conn:
            cursor = conn.cursor()

            # Get page statistics
            cursor.execute('PRAGMA page_count')
            page_count = cursor.fetchone()[0]

            cursor.execute('PRAGMA freelist_count')
            free_pages = cursor.fetchone()[0]

            # Calculate fragmentation
            fragmentation = (free_pages / page_count * 100) if page_count > 0 else 0

            # Index usage stats
            cursor.execute('''
                SELECT name, tbl_name
                FROM sqlite_master
                WHERE type='index' AND tbl_name='search_results'
            ''')
            indexes = [{'name': row[0], 'table': row[1]} for row in cursor.fetchall()]

            # Check for unused indexes
            cursor.execute('SELECT COUNT(*) FROM search_results')
            record_count = cursor.fetchone()[0]

            # Generate recommendations
            recommendations = []
            if fragmentation > 20:
                recommendations.append('Run VACUUM to reduce fragmentation')
            if record_count > 10000:
                recommendations.append('Consider archiving old results')
            if not recommendations:
                recommendations.append('Database is well-optimized')

        return {
            'record_count': record_count,
            'index_usage_stats': indexes,
            'fragmentation_level': round(fragmentation, 2),
            'free_pages': free_pages,
            'page_count': page_count,
            'recommended_actions': recommendations,
        }
    except Exception as e:
        logger.error(f"Failed to analyze database performance: {e}")
        return {'success': False, 'error': str(e)}


def find_duplicates(exact_match: bool = True) -> List[Dict[str, Any]]:
    """Find duplicate records in the database.

    Args:
        exact_match: If True, match queries exactly; if False, case-insensitive

    Returns:
        List of duplicate groups, each containing:
        - query: The query text
        - models: List of models used
        - count: Number of duplicates
        - ids: List of record IDs

    Example:
        >>> duplicates = find_duplicates()
        >>> for group in duplicates:
        ...     print(f"Found {group['count']} duplicates of: {group['query']}")
    """
    try:
        with sqlite3.connect(str(DB_PATH)) as conn:
            cursor = conn.cursor()

            if exact_match:
                query_sql = '''
                    SELECT query, COUNT(*) as count, GROUP_CONCAT(id) as ids,
                           GROUP_CONCAT(DISTINCT model) as models
                    FROM search_results
                    GROUP BY query
                    HAVING COUNT(*) > 1
                    ORDER BY count DESC
                '''
            else:
                query_sql = '''
                    SELECT LOWER(query) as query, COUNT(*) as count,
                           GROUP_CONCAT(id) as ids,
                           GROUP_CONCAT(DISTINCT model) as models
                    FROM search_results
                    GROUP BY LOWER(query)
                    HAVING COUNT(*) > 1
                    ORDER BY count DESC
                '''

            cursor.execute(query_sql)
            rows = cursor.fetchall()

        duplicates = []
        for row in rows:
            duplicates.append({
                'query': row[0],
                'count': row[1],
                'ids': [int(id_) for id_ in row[2].split(',')],
                'models': row[3].split(',') if row[3] else [],
            })

        return duplicates
    except Exception as e:
        logger.error(f"Failed to find duplicates: {e}")
        return []


def remove_duplicates(dry_run: bool = True, keep: str = 'latest') -> Dict[str, Any]:
    """Remove duplicate records, keeping specified version.

    Args:
        dry_run: If True, don't actually delete, just report what would be deleted
        keep: Which record to keep: 'latest', 'earliest', or 'best' (highest success + fastest)

    Returns:
        Dictionary containing:
        - kept_count: Number of records kept
        - removed_count: Number of records removed
        - removed_ids: List of removed record IDs
        - success: Whether operation succeeded

    Example:
        >>> result = remove_duplicates(dry_run=True)
        >>> print(f"Would remove {result['removed_count']} duplicates")
        >>> if result['removed_count'] > 0:
        ...     result = remove_duplicates(dry_run=False)
    """
    try:
        with sqlite3.connect(str(DB_PATH)) as conn:
            cursor = conn.cursor()

            # Find all duplicate groups (same query + model combination)
            cursor.execute('''
                SELECT query, model, GROUP_CONCAT(id) as ids
                FROM search_results
                GROUP BY query, model
                HAVING COUNT(*) > 1
            ''')

            duplicate_groups = cursor.fetchall()
            removed_ids = []

            for group in duplicate_groups:
                query = group[0]
                model = group[1]
                ids = [int(id_) for id_ in group[2].split(',')]

                # Get the record to keep based on criteria
                if keep == 'latest':
                    cursor.execute('''
                        SELECT id FROM search_results
                        WHERE query = ? AND model = ? AND id IN ({})
                        ORDER BY timestamp DESC LIMIT 1
                    '''.format(','.join('?' * len(ids))), [query, model] + ids)
                elif keep == 'earliest':
                    cursor.execute('''
                        SELECT id FROM search_results
                        WHERE query = ? AND model = ? AND id IN ({})
                        ORDER BY timestamp ASC LIMIT 1
                    '''.format(','.join('?' * len(ids))), [query, model] + ids)
                elif keep == 'best':
                    cursor.execute('''
                        SELECT id FROM search_results
                        WHERE query = ? AND model = ? AND id IN ({})
                        ORDER BY success DESC, execution_time_seconds ASC LIMIT 1
                    '''.format(','.join('?' * len(ids))), [query, model] + ids)
                else:
                    raise ValueError(f"Invalid keep value: {keep}")

                keep_id = cursor.fetchone()[0]

                # Mark remaining IDs for deletion
                for id_ in ids:
                    if id_ != keep_id:
                        removed_ids.append(id_)

            kept_count = cursor.execute('SELECT COUNT(*) FROM search_results').fetchone()[0] - len(removed_ids)

            if not dry_run and removed_ids:
                conn.execute('BEGIN TRANSACTION')
                try:
                    placeholders = ','.join('?' * len(removed_ids))
                    cursor.execute(f'DELETE FROM search_results WHERE id IN ({placeholders})', removed_ids)
                    conn.commit()
                    logger.info(f"Removed {len(removed_ids)} duplicate records")
                except Exception as e:
                    conn.rollback()
                    raise e
            elif dry_run:
                logger.info(f"Dry run: Would remove {len(removed_ids)} duplicates")

        return {
            'kept_count': kept_count,
            'removed_count': len(removed_ids),
            'removed_ids': removed_ids,
            'success': True,
            'dry_run': dry_run,
        }
    except Exception as e:
        logger.error(f"Failed to remove duplicates: {e}")
        return {'success': False, 'error': str(e)}


def archive_old_results(
    before_date: str,
    archive_path: str,
    delete_after_archive: bool = False
) -> Dict[str, Any]:
    """Archive search results older than specified date to a new database.

    Args:
        before_date: ISO format date string (YYYY-MM-DD) - records before this date are archived
        archive_path: Path where archive database will be created
        delete_after_archive: If True, delete archived records from main database

    Returns:
        Dictionary containing:
        - archived_count: Number of records archived
        - archive_file_path: Path to created archive file
        - success: Whether operation succeeded

    Example:
        >>> result = archive_old_results(
        ...     before_date='2024-01-01',
        ...     archive_path='/backups/archive_2024.db',
        ...     delete_after_archive=False
        ... )
        >>> print(f"Archived {result['archived_count']} records")
    """
    try:
        # Validate path
        archive_path_obj = Path(archive_path)
        archive_path_obj.parent.mkdir(parents=True, exist_ok=True)

        if archive_path_obj.exists():
            raise ValueError(f"Archive file already exists: {archive_path}")

        # Validate date format
        try:
            datetime.fromisoformat(before_date)
        except ValueError:
            raise ValueError(f"Invalid date format: {before_date} (use YYYY-MM-DD)")

        # Open connections with proper context managers
        with sqlite3.connect(str(DB_PATH)) as source_conn:
            source_cursor = source_conn.cursor()

            # Create archive database with same schema
            with sqlite3.connect(str(archive_path_obj)) as archive_conn:
                archive_cursor = archive_conn.cursor()

                # Create schema in archive
                archive_cursor.execute('''
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

                # Copy records older than specified date
                source_cursor.execute('''
                    SELECT * FROM search_results
                    WHERE timestamp < ?
                    ORDER BY timestamp
                ''', (before_date,))

                records = source_cursor.fetchall()
                archived_count = 0

                if records:
                    archive_cursor.executemany('''
                        INSERT INTO search_results (
                            id, query, model, timestamp, answer_text, sources,
                            screenshot_path, execution_time_seconds, success, error_message
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    ''', records)
                    archived_count = len(records)

                archive_conn.commit()

            # Delete from main database if requested
            if delete_after_archive and archived_count > 0:
                source_conn.execute('BEGIN TRANSACTION')
                try:
                    source_cursor.execute(
                        'DELETE FROM search_results WHERE timestamp < ?',
                        (before_date,)
                    )
                    source_conn.commit()
                    logger.info(f"Deleted {archived_count} archived records from main database")
                except Exception as e:
                    source_conn.rollback()
                    raise e

        logger.info(f"Archived {archived_count} records to {archive_path}")

        return {
            'archived_count': archived_count,
            'archive_file_path': str(archive_path_obj.absolute()),
            'success': True,
        }
    except Exception as e:
        logger.error(f"Failed to archive results: {e}")
        return {'success': False, 'error': str(e)}


def delete_failed_results(before_date: Optional[str] = None, confirm: bool = True) -> Dict[str, Any]:
    """Delete failed search results, optionally filtered by date.

    Args:
        before_date: Optional ISO format date string - only delete failures before this date
        confirm: If False, skip confirmation prompt (use carefully!)

    Returns:
        Dictionary containing:
        - deleted_count: Number of records deleted
        - success: Whether operation succeeded

    Example:
        >>> result = delete_failed_results(before_date='2024-06-01')
        >>> print(f"Deleted {result['deleted_count']} failed records")
    """
    try:
        with sqlite3.connect(str(DB_PATH)) as conn:
            cursor = conn.cursor()

            # Build query
            if before_date:
                try:
                    datetime.fromisoformat(before_date)
                except ValueError:
                    raise ValueError(f"Invalid date format: {before_date} (use YYYY-MM-DD)")

                cursor.execute('''
                    SELECT COUNT(*) FROM search_results
                    WHERE success = 0 AND timestamp < ?
                ''', (before_date,))
            else:
                cursor.execute('SELECT COUNT(*) FROM search_results WHERE success = 0')

            count = cursor.fetchone()[0]

            if count == 0:
                logger.info("No failed results to delete")
                return {'deleted_count': 0, 'success': True}

            # Show confirmation
            date_info = f" before {before_date}" if before_date else ""
            message = f"Delete {count} failed search results{date_info}? (y/n): "

            if confirm and input(message).lower() != 'y':
                logger.info("Deletion cancelled")
                return {'deleted_count': 0, 'success': True, 'cancelled': True}

            # Delete records
            conn.execute('BEGIN TRANSACTION')
            try:
                if before_date:
                    cursor.execute('''
                        DELETE FROM search_results
                        WHERE success = 0 AND timestamp < ?
                    ''', (before_date,))
                else:
                    cursor.execute('DELETE FROM search_results WHERE success = 0')

                conn.commit()
                logger.info(f"Deleted {count} failed records")
                return {'deleted_count': count, 'success': True}
            except Exception as e:
                conn.rollback()
                raise e
    except Exception as e:
        logger.error(f"Failed to delete failed results: {e}")
        return {'success': False, 'error': str(e)}


def vacuum_database() -> Dict[str, Any]:
    """Optimize database by reclaiming unused space.

    Returns:
        Dictionary containing:
        - success: Whether operation succeeded
        - old_size_bytes: Database size before vacuum
        - new_size_bytes: Database size after vacuum
        - space_freed_bytes: Space reclaimed

    Example:
        >>> result = vacuum_database()
        >>> print(f"Freed {_format_bytes(result['space_freed_bytes'])}")
    """
    try:
        # Get size before
        old_size = DB_PATH.stat().st_size if DB_PATH.exists() else 0

        with sqlite3.connect(str(DB_PATH)) as conn:
            conn.execute('VACUUM')

        # Get size after
        new_size = DB_PATH.stat().st_size if DB_PATH.exists() else 0
        space_freed = max(0, old_size - new_size)

        logger.info(f"Vacuum freed {_format_bytes(space_freed)}")

        return {
            'success': True,
            'old_size_bytes': old_size,
            'new_size_bytes': new_size,
            'space_freed_bytes': space_freed,
        }
    except Exception as e:
        logger.error(f"Failed to vacuum database: {e}")
        return {'success': False, 'error': str(e)}


def rebuild_indexes() -> Dict[str, Any]:
    """Rebuild all database indexes for optimal performance.

    Returns:
        Dictionary containing:
        - success: Whether operation succeeded
        - indexes_rebuilt: List of index names rebuilt
        - time_taken_seconds: Time taken to rebuild

    Example:
        >>> result = rebuild_indexes()
        >>> print(f"Rebuilt {len(result['indexes_rebuilt'])} indexes")
    """
    try:
        import time
        start_time = time.time()

        with sqlite3.connect(str(DB_PATH)) as conn:
            cursor = conn.cursor()

            indexes_rebuilt = []

            # Drop all indexes
            for index in INDEXES:
                try:
                    cursor.execute(f'DROP INDEX IF EXISTS {index}')
                    logger.debug(f"Dropped index: {index}")
                except Exception as e:
                    logger.warning(f"Failed to drop index {index}: {e}")

            # Recreate indexes
            index_definitions = [
                ('idx_query', 'CREATE INDEX idx_query ON search_results(query)'),
                ('idx_model', 'CREATE INDEX idx_model ON search_results(model)'),
                ('idx_timestamp', 'CREATE INDEX idx_timestamp ON search_results(timestamp)'),
                ('idx_query_model', 'CREATE INDEX idx_query_model ON search_results(query, model)'),
            ]

            for index_name, create_sql in index_definitions:
                try:
                    cursor.execute(create_sql)
                    indexes_rebuilt.append(index_name)
                    logger.debug(f"Rebuilt index: {index_name}")
                except Exception as e:
                    logger.error(f"Failed to rebuild index {index_name}: {e}")

            conn.commit()

        time_taken = time.time() - start_time
        logger.info(f"Rebuilt {len(indexes_rebuilt)} indexes in {time_taken:.2f}s")

        return {
            'success': True,
            'indexes_rebuilt': indexes_rebuilt,
            'time_taken_seconds': round(time_taken, 2),
        }
    except Exception as e:
        logger.error(f"Failed to rebuild indexes: {e}")
        return {'success': False, 'error': str(e)}


def optimize_database() -> Dict[str, Any]:
    """Run all optimization operations on the database.

    Performs: ANALYZE, VACUUM, and index rebuild.

    Returns:
        Dictionary containing:
        - actions_performed: List of actions completed
        - results: Dict with results from each operation
        - success: Whether all operations succeeded

    Example:
        >>> result = optimize_database()
        >>> for action in result['actions_performed']:
        ...     print(f"Completed: {action}")
    """
    try:
        actions = []
        results = {}

        # Run ANALYZE
        logger.info("Running ANALYZE...")
        with sqlite3.connect(str(DB_PATH)) as conn:
            conn.execute('ANALYZE')
        actions.append('ANALYZE')
        results['analyze'] = {'success': True}

        # Run VACUUM
        logger.info("Running VACUUM...")
        vacuum_result = vacuum_database()
        actions.append('VACUUM')
        results['vacuum'] = vacuum_result

        # Rebuild indexes
        logger.info("Rebuilding indexes...")
        index_result = rebuild_indexes()
        actions.append('REBUILD_INDEXES')
        results['rebuild_indexes'] = index_result

        logger.info("Database optimization completed successfully")

        return {
            'actions_performed': actions,
            'results': results,
            'success': True,
        }
    except Exception as e:
        logger.error(f"Failed to optimize database: {e}")
        return {'success': False, 'error': str(e)}


def backup_database(backup_path: str) -> Dict[str, Any]:
    """Create a backup of the database.

    Args:
        backup_path: Path where backup will be created

    Returns:
        Dictionary containing:
        - success: Whether backup succeeded
        - backup_file_path: Absolute path to backup file
        - backup_size_bytes: Size of backup file
        - timestamp: When backup was created

    Example:
        >>> result = backup_database('/backups/search_results_backup.db')
        >>> print(f"Backup created: {result['backup_file_path']}")
    """
    try:
        backup_path_obj = Path(backup_path)
        backup_path_obj.parent.mkdir(parents=True, exist_ok=True)

        if backup_path_obj.exists():
            raise ValueError(f"Backup file already exists: {backup_path}")

        # Use SQLite backup API via file copy
        if DB_PATH.exists():
            shutil.copy2(str(DB_PATH), str(backup_path_obj))

            backup_size = backup_path_obj.stat().st_size
            timestamp = datetime.now().isoformat()

            logger.info(f"Database backed up to {backup_path} ({_format_bytes(backup_size)})")

            return {
                'success': True,
                'backup_file_path': str(backup_path_obj.absolute()),
                'backup_size_bytes': backup_size,
                'timestamp': timestamp,
            }
        else:
            raise ValueError(f"Database file not found: {DB_PATH}")
    except Exception as e:
        logger.error(f"Failed to backup database: {e}")
        return {'success': False, 'error': str(e)}


def restore_database(backup_path: str, confirm: bool = True) -> Dict[str, Any]:
    """Restore database from a backup file.

    Args:
        backup_path: Path to backup file
        confirm: If False, skip confirmation prompt (use carefully!)

    Returns:
        Dictionary containing:
        - success: Whether restore succeeded
        - records_restored: Number of records in restored database
        - timestamp: When restore was performed

    Example:
        >>> result = restore_database('/backups/search_results_backup.db')
        >>> print(f"Restored {result['records_restored']} records")
    """
    try:
        backup_path_obj = Path(backup_path)

        if not backup_path_obj.exists():
            raise ValueError(f"Backup file not found: {backup_path}")

        # Show confirmation
        if confirm and input("Restore database from backup? (y/n): ").lower() != 'y':
            logger.info("Restore cancelled")
            return {'success': True, 'cancelled': True}

        # Restore from backup
        shutil.copy2(str(backup_path_obj), str(DB_PATH))

        # Verify restore
        with sqlite3.connect(str(DB_PATH)) as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT COUNT(*) FROM search_results')
            records_restored = cursor.fetchone()[0]

        timestamp = datetime.now().isoformat()
        logger.info(f"Database restored with {records_restored} records")

        return {
            'success': True,
            'records_restored': records_restored,
            'timestamp': timestamp,
        }
    except Exception as e:
        logger.error(f"Failed to restore database: {e}")
        return {'success': False, 'error': str(e)}
