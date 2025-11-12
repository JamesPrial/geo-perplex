"""
Database storage utilities for search results
Manages SQLite database for storing and querying Perplexity search results
"""
import sqlite3
import json
import logging
from datetime import datetime
from typing import Dict, List, Optional
from pathlib import Path

logger = logging.getLogger(__name__)


# Database file location
DB_PATH = Path(__file__).parent.parent.parent / 'search_results.db'


def init_database() -> None:
    """Initialize the database with required schema"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # Create search_results table
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

    # Create indexes for common queries
    cursor.execute('''
        CREATE INDEX IF NOT EXISTS idx_query ON search_results(query)
    ''')
    cursor.execute('''
        CREATE INDEX IF NOT EXISTS idx_model ON search_results(model)
    ''')
    cursor.execute('''
        CREATE INDEX IF NOT EXISTS idx_timestamp ON search_results(timestamp)
    ''')
    cursor.execute('''
        CREATE INDEX IF NOT EXISTS idx_query_model ON search_results(query, model)
    ''')

    conn.commit()
    conn.close()


def save_search_result(
    query: str,
    answer_text: str,
    sources: List[Dict],
    screenshot_path: Optional[str] = None,
    model: Optional[str] = None,
    execution_time: Optional[float] = None,
    success: bool = True,
    error_message: Optional[str] = None
) -> int:
    """
    Save a search result to the database

    Args:
        query: The search query
        answer_text: The answer text returned by Perplexity
        sources: List of source dicts with 'url' and 'text' keys
        screenshot_path: Path to screenshot file (relative or absolute)
        model: Model used (e.g., 'default', 'gpt-4', 'claude-3')
        execution_time: Time taken to execute search in seconds
        success: Whether the search was successful
        error_message: Error message if search failed

    Returns:
        The ID of the inserted record
    """
    init_database()  # Ensure database exists

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # Convert sources list to JSON string
    sources_json = json.dumps(sources)

    cursor.execute('''
        INSERT INTO search_results (
            query, model, answer_text, sources, screenshot_path,
            execution_time_seconds, success, error_message
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    ''', (
        query,
        model,
        answer_text,
        sources_json,
        screenshot_path,
        execution_time,
        success,
        error_message
    ))

    result_id = cursor.lastrowid
    conn.commit()
    conn.close()

    return result_id


def get_results_by_query(query: str, model: Optional[str] = None) -> List[Dict]:
    """
    Get all results for a specific query, optionally filtered by model

    Args:
        query: The search query to filter by
        model: Optional model to filter by

    Returns:
        List of result dictionaries
    """
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    if model:
        cursor.execute('''
            SELECT * FROM search_results
            WHERE query = ? AND model = ?
            ORDER BY timestamp DESC
        ''', (query, model))
    else:
        cursor.execute('''
            SELECT * FROM search_results
            WHERE query = ?
            ORDER BY timestamp DESC
        ''', (query,))

    rows = cursor.fetchall()
    conn.close()

    # Convert to list of dicts with parsed JSON
    results = []
    for row in rows:
        result = dict(row)
        try:
            result['sources'] = json.loads(result['sources']) if result['sources'] else []
        except json.JSONDecodeError as e:
            logger.warning(f"Failed to parse sources JSON for result ID {result.get('id')}: {e}")
            result['sources'] = []
        results.append(result)

    return results


def get_results_by_model(model: str, limit: int = 50) -> List[Dict]:
    """
    Get recent results for a specific model

    Args:
        model: Model to filter by
        limit: Maximum number of results to return

    Returns:
        List of result dictionaries
    """
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    cursor.execute('''
        SELECT * FROM search_results
        WHERE model = ?
        ORDER BY timestamp DESC
        LIMIT ?
    ''', (model, limit))

    rows = cursor.fetchall()
    conn.close()

    results = []
    for row in rows:
        result = dict(row)
        try:
            result['sources'] = json.loads(result['sources']) if result['sources'] else []
        except json.JSONDecodeError as e:
            logger.warning(f"Failed to parse sources JSON for result ID {result.get('id')}: {e}")
            result['sources'] = []
        results.append(result)

    return results


def compare_models_for_query(query: str) -> Dict[str, List[Dict]]:
    """
    Get all results for a query grouped by model for comparison

    Args:
        query: The search query

    Returns:
        Dictionary mapping model names to lists of results
    """
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    cursor.execute('''
        SELECT * FROM search_results
        WHERE query = ?
        ORDER BY model, timestamp DESC
    ''', (query,))

    rows = cursor.fetchall()
    conn.close()

    # Group by model
    results_by_model = {}
    for row in rows:
        result = dict(row)
        try:
            result['sources'] = json.loads(result['sources']) if result['sources'] else []
        except json.JSONDecodeError as e:
            logger.warning(f"Failed to parse sources JSON for result ID {result.get('id')}: {e}")
            result['sources'] = []

        model = result['model'] or 'unknown'
        if model not in results_by_model:
            results_by_model[model] = []
        results_by_model[model].append(result)

    return results_by_model


def get_recent_results(limit: int = 50) -> List[Dict]:
    """
    Get most recent search results

    Args:
        limit: Maximum number of results to return

    Returns:
        List of result dictionaries
    """
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    cursor.execute('''
        SELECT * FROM search_results
        ORDER BY timestamp DESC
        LIMIT ?
    ''', (limit,))

    rows = cursor.fetchall()
    conn.close()

    results = []
    for row in rows:
        result = dict(row)
        try:
            result['sources'] = json.loads(result['sources']) if result['sources'] else []
        except json.JSONDecodeError as e:
            logger.warning(f"Failed to parse sources JSON for result ID {result.get('id')}: {e}")
            result['sources'] = []
        results.append(result)

    return results


def get_unique_queries() -> List[str]:
    """Get list of all unique queries in the database"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute('''
        SELECT DISTINCT query FROM search_results
        ORDER BY query
    ''')

    queries = [row[0] for row in cursor.fetchall()]
    conn.close()

    return queries


def get_unique_models() -> List[str]:
    """Get list of all unique models in the database"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute('''
        SELECT DISTINCT model FROM search_results
        WHERE model IS NOT NULL
        ORDER BY model
    ''')

    models = [row[0] for row in cursor.fetchall()]
    conn.close()

    return models


def _parse_results(rows: List) -> List[Dict]:
    """
    Helper function to convert database rows to result dictionaries with parsed JSON.

    Args:
        rows: List of sqlite3.Row objects

    Returns:
        List of result dictionaries with parsed sources JSON
    """
    results = []
    for row in rows:
        result = dict(row)
        try:
            result['sources'] = json.loads(result['sources']) if result['sources'] else []
        except json.JSONDecodeError as e:
            logger.warning(f"Failed to parse sources JSON for result ID {result.get('id')}: {e}")
            result['sources'] = []
        results.append(result)
    return results


def get_results_by_date_range(
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    model: Optional[str] = None,
    limit: Optional[int] = None
) -> List[Dict]:
    """
    Get results within a date range, optionally filtered by model.

    Args:
        start_date: Start date (ISO format: YYYY-MM-DD or datetime string)
        end_date: End date (ISO format: YYYY-MM-DD or datetime string)
        model: Optional model to filter by
        limit: Maximum number of results to return

    Returns:
        List of result dictionaries ordered by timestamp descending
    """
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    conditions = []
    params = []

    if start_date:
        conditions.append('timestamp >= ?')
        params.append(start_date)

    if end_date:
        conditions.append('timestamp <= ?')
        params.append(end_date)

    if model:
        conditions.append('model = ?')
        params.append(model)

    where_clause = ' AND '.join(conditions) if conditions else '1=1'

    # Validate limit is a positive integer
    if limit is not None and (not isinstance(limit, int) or limit <= 0):
        raise ValueError("limit must be a positive integer")

    query = '''
        SELECT * FROM search_results
        WHERE {}
        ORDER BY timestamp DESC
    '''.format(where_clause)

    if limit:
        query += ' LIMIT ?'
        params.append(limit)

    cursor.execute(query, params)
    rows = cursor.fetchall()
    conn.close()

    return _parse_results(rows)


def get_results_by_success_status(success: bool = True, limit: Optional[int] = None) -> List[Dict]:
    """
    Get results filtered by success/failure status.

    Args:
        success: True for successful results, False for failed results
        limit: Maximum number of results to return

    Returns:
        List of result dictionaries ordered by timestamp descending
    """
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    # Validate limit is a positive integer
    if limit is not None and (not isinstance(limit, int) or limit <= 0):
        raise ValueError("limit must be a positive integer")

    success_value = 1 if success else 0

    query = '''
        SELECT * FROM search_results
        WHERE success = ?
        ORDER BY timestamp DESC
    '''

    params = [success_value]
    if limit:
        query += ' LIMIT ?'
        params.append(limit)

    cursor.execute(query, params)
    rows = cursor.fetchall()
    conn.close()

    return _parse_results(rows)


def get_results_by_execution_time(
    min_time: Optional[float] = None,
    max_time: Optional[float] = None,
    limit: Optional[int] = None
) -> List[Dict]:
    """
    Get results filtered by execution time.

    Args:
        min_time: Minimum execution time in seconds (inclusive)
        max_time: Maximum execution time in seconds (inclusive)
        limit: Maximum number of results to return

    Returns:
        List of result dictionaries ordered by execution_time_seconds ascending
    """
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    conditions = ['execution_time_seconds IS NOT NULL']
    params = []

    if min_time is not None:
        conditions.append('execution_time_seconds >= ?')
        params.append(min_time)

    if max_time is not None:
        conditions.append('execution_time_seconds <= ?')
        params.append(max_time)

    # Validate limit is a positive integer
    if limit is not None and (not isinstance(limit, int) or limit <= 0):
        raise ValueError("limit must be a positive integer")

    where_clause = ' AND '.join(conditions)

    query = '''
        SELECT * FROM search_results
        WHERE {}
        ORDER BY execution_time_seconds ASC
    '''.format(where_clause)

    if limit:
        query += ' LIMIT ?'
        params.append(limit)

    cursor.execute(query, params)
    rows = cursor.fetchall()
    conn.close()

    return _parse_results(rows)


def search_in_answers(
    search_term: str,
    case_sensitive: bool = False,
    limit: Optional[int] = None
) -> List[Dict]:
    """
    Full-text search within answer_text field.

    Args:
        search_term: Text to search for
        case_sensitive: If False, search is case-insensitive
        limit: Maximum number of results to return

    Returns:
        List of result dictionaries ordered by timestamp descending
    """
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    # Validate limit is a positive integer
    if limit is not None and (not isinstance(limit, int) or limit <= 0):
        raise ValueError("limit must be a positive integer")

    if case_sensitive:
        query = '''
            SELECT * FROM search_results
            WHERE answer_text GLOB ?
            ORDER BY timestamp DESC
        '''
        params = [f'*{search_term}*']
    else:
        # SQLite is case-insensitive by default for ASCII characters
        query = '''
            SELECT * FROM search_results
            WHERE LOWER(answer_text) LIKE LOWER(?)
            ORDER BY timestamp DESC
        '''
        params = [f'%{search_term}%']
    if limit:
        query += ' LIMIT ?'
        params.append(limit)

    cursor.execute(query, params)
    rows = cursor.fetchall()
    conn.close()

    return _parse_results(rows)


def search_in_sources(
    search_term: str,
    case_sensitive: bool = False,
    limit: Optional[int] = None
) -> List[Dict]:
    """
    Full-text search within sources JSON field.

    Args:
        search_term: Text to search for in sources
        case_sensitive: If False, search is case-insensitive
        limit: Maximum number of results to return

    Returns:
        List of result dictionaries with matching sources
    """
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    # Validate limit is a positive integer
    if limit is not None and (not isinstance(limit, int) or limit <= 0):
        raise ValueError("limit must be a positive integer")

    if case_sensitive:
        query = '''
            SELECT * FROM search_results
            WHERE sources GLOB ?
            ORDER BY timestamp DESC
        '''
        params = [f'*{search_term}*']
    else:
        query = '''
            SELECT * FROM search_results
            WHERE LOWER(sources) LIKE LOWER(?)
            ORDER BY timestamp DESC
        '''
        params = [f'%{search_term}%']
    if limit:
        query += ' LIMIT ?'
        params.append(limit)

    cursor.execute(query, params)
    rows = cursor.fetchall()
    conn.close()

    return _parse_results(rows)


def search_queries_fuzzy(pattern: str, limit: Optional[int] = None) -> List[Dict]:
    """
    Fuzzy search for queries using SQL LIKE pattern matching.

    Args:
        pattern: Fuzzy pattern to search for (use % for wildcards)
        limit: Maximum number of results to return

    Returns:
        List of result dictionaries ordered by timestamp descending
    """
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    # Validate limit is a positive integer
    if limit is not None and (not isinstance(limit, int) or limit <= 0):
        raise ValueError("limit must be a positive integer")

    query = '''
        SELECT * FROM search_results
        WHERE query LIKE ?
        ORDER BY timestamp DESC
    '''

    params = [pattern]
    if limit:
        query += ' LIMIT ?'
        params.append(limit)

    cursor.execute(query, params)
    rows = cursor.fetchall()
    conn.close()

    return _parse_results(rows)


def get_results_advanced_filter(
    query_pattern: Optional[str] = None,
    model: Optional[str] = None,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    success: Optional[bool] = None,
    min_exec_time: Optional[float] = None,
    max_exec_time: Optional[float] = None,
    min_answer_length: Optional[int] = None,
    max_answer_length: Optional[int] = None,
    has_sources: Optional[bool] = None,
    limit: Optional[int] = None,
    order_by: str = 'timestamp',
    order_desc: bool = True
) -> List[Dict]:
    """
    Advanced filtering with multiple criteria combined.

    Args:
        query_pattern: Query text pattern (use % for LIKE wildcards)
        model: Specific model to filter by
        start_date: Start date (ISO format: YYYY-MM-DD or datetime string)
        end_date: End date (ISO format: YYYY-MM-DD or datetime string)
        success: None=all, True=successful only, False=failed only
        min_exec_time: Minimum execution time in seconds
        max_exec_time: Maximum execution time in seconds
        min_answer_length: Minimum answer text length in characters
        max_answer_length: Maximum answer text length in characters
        has_sources: None=all, True=has sources, False=no sources
        limit: Maximum number of results to return
        order_by: Sort column ('timestamp', 'execution_time_seconds', 'query', 'model', 'id')
        order_desc: True for descending order, False for ascending

    Returns:
        List of result dictionaries matching all criteria

    Raises:
        ValueError: If order_by is not in whitelist or limit is invalid
    """
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    conditions = []
    params = []

    if query_pattern:
        conditions.append('query LIKE ?')
        params.append(query_pattern)

    if model:
        conditions.append('model = ?')
        params.append(model)

    if start_date:
        conditions.append('timestamp >= ?')
        params.append(start_date)

    if end_date:
        conditions.append('timestamp <= ?')
        params.append(end_date)

    if success is not None:
        conditions.append('success = ?')
        params.append(1 if success else 0)

    if min_exec_time is not None:
        conditions.append('execution_time_seconds >= ?')
        params.append(min_exec_time)

    if max_exec_time is not None:
        conditions.append('execution_time_seconds <= ?')
        params.append(max_exec_time)

    if min_answer_length is not None:
        conditions.append('LENGTH(answer_text) >= ?')
        params.append(min_answer_length)

    if max_answer_length is not None:
        conditions.append('LENGTH(answer_text) <= ?')
        params.append(max_answer_length)

    if has_sources is not None:
        if has_sources:
            conditions.append('sources IS NOT NULL AND sources != ?')
            params.append('[]')
        else:
            conditions.append('(sources IS NULL OR sources = ?)')
            params.append('[]')

    # Validate order_by to prevent SQL injection - whitelist approach
    valid_order_columns = {'timestamp', 'execution_time_seconds', 'query', 'model', 'id'}
    if order_by not in valid_order_columns:
        logger.warning(f"Invalid order_by: {order_by}. Defaulting to 'timestamp'")
        order_by = 'timestamp'

    # Validate limit is a positive integer
    if limit is not None and (not isinstance(limit, int) or limit <= 0):
        raise ValueError("limit must be a positive integer")

    order_direction = 'DESC' if order_desc else 'ASC'

    where_clause = ' AND '.join(conditions) if conditions else '1=1'

    query = '''
        SELECT * FROM search_results
        WHERE {}
        ORDER BY {} {}
    '''.format(where_clause, order_by, order_direction)

    if limit:
        query += ' LIMIT ?'
        params.append(limit)

    cursor.execute(query, params)
    rows = cursor.fetchall()
    conn.close()

    return _parse_results(rows)
