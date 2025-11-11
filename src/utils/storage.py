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
