"""
Statistical analysis module for GEO-Perplex search results.

Provides comprehensive statistics and analytics for search performance,
including execution times, success rates, model comparisons, and data quality metrics.
"""

import sqlite3
import statistics
import json
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple, Any
from pathlib import Path

logger = logging.getLogger(__name__)

# Database file location
DB_PATH = Path(__file__).parent.parent.parent / 'search_results.db'


def _get_connection() -> sqlite3.Connection:
    """Create and return a database connection."""
    return sqlite3.connect(str(DB_PATH))


# ==============================================================================
# Basic Statistics Functions
# ==============================================================================


def get_execution_time_stats(
    model: Optional[str] = None,
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None
) -> Optional[Dict[str, float]]:
    """
    Calculate execution time statistics for search queries.

    Computes mean, median, standard deviation, min/max, and total count
    of execution times in seconds.

    Args:
        model: Filter by specific model (optional)
        start_date: Filter results after this datetime (optional)
        end_date: Filter results before this datetime (optional)

    Returns:
        Dictionary with keys: mean, median, std_dev, min, max, total_queries
        Returns None if no results match the criteria
    """
    with sqlite3.connect(str(DB_PATH)) as conn:
        cursor = conn.cursor()

        query = 'SELECT execution_time_seconds FROM search_results WHERE execution_time_seconds IS NOT NULL'
        params = []

        if model:
            query += ' AND model = ?'
            params.append(model)
        if start_date:
            query += ' AND timestamp >= ?'
            params.append(start_date.isoformat())
        if end_date:
            query += ' AND timestamp <= ?'
            params.append(end_date.isoformat())

        cursor.execute(query, params)
        times = [row[0] for row in cursor.fetchall()]

    if not times:
        return None

    return {
        'mean': statistics.mean(times),
        'median': statistics.median(times),
        'std_dev': statistics.stdev(times) if len(times) > 1 else 0.0,
        'min': min(times),
        'max': max(times),
        'total_queries': len(times),
    }


def get_success_rate_stats(
    model: Optional[str] = None,
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None
) -> Optional[Dict[str, Any]]:
    """
    Calculate success and failure statistics.

    Returns counts and percentages of successful vs failed searches.

    Args:
        model: Filter by specific model (optional)
        start_date: Filter results after this datetime (optional)
        end_date: Filter results before this datetime (optional)

    Returns:
        Dictionary with keys: total, successful, failed, success_rate, failure_rate
        Returns None if no results match the criteria
    """
    with sqlite3.connect(str(DB_PATH)) as conn:
        cursor = conn.cursor()

        query = 'SELECT success FROM search_results'
        params = []
        conditions = []

        if model:
            conditions.append('model = ?')
            params.append(model)
        if start_date:
            conditions.append('timestamp >= ?')
            params.append(start_date.isoformat())
        if end_date:
            conditions.append('timestamp <= ?')
            params.append(end_date.isoformat())

        if conditions:
            query += ' WHERE ' + ' AND '.join(conditions)

        cursor.execute(query, params)
        success_values = [row[0] for row in cursor.fetchall()]

    if not success_values:
        return None

    total = len(success_values)
    successful = sum(1 for s in success_values if s)
    failed = total - successful

    return {
        'total': total,
        'successful': successful,
        'failed': failed,
        'success_rate': successful / total if total > 0 else 0.0,
        'failure_rate': failed / total if total > 0 else 0.0,
    }


def get_model_comparison_stats(
    query: Optional[str] = None,
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None
) -> Optional[Dict[str, Dict[str, Any]]]:
    """
    Compare statistics across different AI models.

    Returns execution time, success rate, and answer length statistics for each model.

    Args:
        query: Filter by specific query (optional)
        start_date: Filter results after this datetime (optional)
        end_date: Filter results before this datetime (optional)

    Returns:
        Dictionary mapping model names to stats dictionaries with keys:
        execution_time_mean, success_rate, answer_length_mean, count
        Returns None if no results match the criteria
    """
    with sqlite3.connect(str(DB_PATH)) as conn:
        cursor = conn.cursor()

        base_query = '''
            SELECT model, execution_time_seconds, success, answer_text
            FROM search_results
            WHERE model IS NOT NULL
        '''
        params = []
        conditions = []

        if query:
            conditions.append('query = ?')
            params.append(query)
        if start_date:
            conditions.append('timestamp >= ?')
            params.append(start_date.isoformat())
        if end_date:
            conditions.append('timestamp <= ?')
            params.append(end_date.isoformat())

        if conditions:
            base_query += ' AND ' + ' AND '.join(conditions)

        cursor.execute(base_query, params)
        rows = cursor.fetchall()

    if not rows:
        return None

    # Group data by model
    model_data: Dict[str, Dict[str, list]] = {}
    for model, exec_time, success, answer_text in rows:
        if model not in model_data:
            model_data[model] = {
                'exec_times': [],
                'successes': [],
                'answer_lengths': [],
            }
        if exec_time is not None:
            model_data[model]['exec_times'].append(exec_time)
        model_data[model]['successes'].append(success)
        if answer_text:
            model_data[model]['answer_lengths'].append(len(answer_text))

    # Calculate stats for each model
    result = {}
    for model, data in model_data.items():
        exec_times = data['exec_times']
        successes = data['successes']
        answer_lengths = data['answer_lengths']

        result[model] = {
            'execution_time_mean': statistics.mean(exec_times) if exec_times else 0.0,
            'success_rate': sum(successes) / len(successes) if successes else 0.0,
            'answer_length_mean': statistics.mean(answer_lengths) if answer_lengths else 0.0,
            'count': len(data['successes']),
        }

    return result if result else None


def get_answer_length_stats(
    model: Optional[str] = None,
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None
) -> Optional[Dict[str, float]]:
    """
    Calculate answer text length statistics.

    Computes mean, median, standard deviation, min/max character counts.

    Args:
        model: Filter by specific model (optional)
        start_date: Filter results after this datetime (optional)
        end_date: Filter results before this datetime (optional)

    Returns:
        Dictionary with keys: mean, median, std_dev, min, max, total_answers
        Returns None if no results match the criteria
    """
    with sqlite3.connect(str(DB_PATH)) as conn:
        cursor = conn.cursor()

        query = 'SELECT LENGTH(answer_text) FROM search_results WHERE answer_text IS NOT NULL'
        params = []

        if model:
            query += ' AND model = ?'
            params.append(model)
        if start_date:
            query += ' AND timestamp >= ?'
            params.append(start_date.isoformat())
        if end_date:
            query += ' AND timestamp <= ?'
            params.append(end_date.isoformat())

        cursor.execute(query, params)
        lengths = [row[0] for row in cursor.fetchall()]

    if not lengths:
        return None

    return {
        'mean': statistics.mean(lengths),
        'median': statistics.median(lengths),
        'std_dev': statistics.stdev(lengths) if len(lengths) > 1 else 0.0,
        'min': min(lengths),
        'max': max(lengths),
        'total_answers': len(lengths),
    }


def get_source_count_stats(
    model: Optional[str] = None,
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None
) -> Optional[Dict[str, float]]:
    """
    Calculate source count statistics across search results.

    Analyzes the number of sources cited in each answer.

    Args:
        model: Filter by specific model (optional)
        start_date: Filter results after this datetime (optional)
        end_date: Filter results before this datetime (optional)

    Returns:
        Dictionary with keys: mean, median, std_dev, min, max, total_results
        Returns None if no results match the criteria
    """
    with sqlite3.connect(str(DB_PATH)) as conn:
        cursor = conn.cursor()

        query = 'SELECT sources FROM search_results WHERE sources IS NOT NULL'
        params = []

        if model:
            query += ' AND model = ?'
            params.append(model)
        if start_date:
            query += ' AND timestamp >= ?'
            params.append(start_date.isoformat())
        if end_date:
            query += ' AND timestamp <= ?'
            params.append(end_date.isoformat())

        cursor.execute(query, params)
        rows = cursor.fetchall()

    source_counts = []
    for (sources_json,) in rows:
        try:
            sources = json.loads(sources_json) if sources_json else []
            source_counts.append(len(sources))
        except json.JSONDecodeError:
            logger.warning(f"Failed to parse sources JSON: {sources_json}")
            source_counts.append(0)

    if not source_counts:
        return None

    return {
        'mean': statistics.mean(source_counts),
        'median': statistics.median(source_counts),
        'std_dev': statistics.stdev(source_counts) if len(source_counts) > 1 else 0.0,
        'min': min(source_counts),
        'max': max(source_counts),
        'total_results': len(source_counts),
    }


# ==============================================================================
# Time-Series Analysis Functions
# ==============================================================================


def get_query_volume_by_period(
    period: str = 'day',
    model: Optional[str] = None,
    limit: int = 30
) -> Optional[List[Tuple[str, int]]]:
    """
    Get query volume grouped by time period.

    Returns the count of searches for each time period.

    Args:
        period: 'hour', 'day', 'week', or 'month'
        model: Filter by specific model (optional)
        limit: Maximum number of periods to return (sorted by recency)

    Returns:
        List of tuples: (period_start_time, query_count)
        Returns None if no results found

    Raises:
        ValueError: If period is invalid or limit is not a positive integer
    """
    # Validate period - whitelist approach to prevent SQL injection
    valid_periods = {'hour', 'day', 'week', 'month'}
    if period not in valid_periods:
        raise ValueError(f"period must be one of {sorted(valid_periods)}, got '{period}'")

    # Validate limit is a positive integer
    if not isinstance(limit, int) or limit <= 0:
        raise ValueError("limit must be a positive integer")

    # Map period to strftime format
    format_map = {
        'hour': '%Y-%m-%d %H:00:00',
        'day': '%Y-%m-%d 00:00:00',
        'week': '%Y-W%W',
        'month': '%Y-%m-01',
    }
    strftime_format = format_map[period]

    conn = _get_connection()
    cursor = conn.cursor()

    query = '''
        SELECT strftime(?, timestamp) as period,
               COUNT(*) as count
        FROM search_results
    '''
    params = [strftime_format]

    if model:
        query += ' WHERE model = ?'
        params.append(model)

    query += ' GROUP BY period ORDER BY period DESC LIMIT ?'
    params.append(limit)

    cursor.execute(query, params)
    results = cursor.fetchall()
    conn.close()

    if not results:
        return None

    return [(period_str, count) for period_str, count in results]


def get_trends_over_time(
    metric: str = 'execution_time',
    period: str = 'day',
    model: Optional[str] = None,
    limit: int = 30
) -> Optional[List[Tuple[str, float]]]:
    """
    Get metric trends grouped by time period.

    Returns average metric values for each time period.

    Args:
        metric: 'execution_time', 'success_rate', or 'answer_length'
        period: 'hour', 'day', 'week', or 'month'
        model: Filter by specific model (optional)
        limit: Maximum number of periods to return (sorted by recency)

    Returns:
        List of tuples: (period_start_time, metric_average)
        Returns None if no results found

    Raises:
        ValueError: If metric or period is invalid, or limit is not a positive integer
    """
    # Validate inputs - whitelist approach to prevent SQL injection
    valid_metrics = {'execution_time', 'success_rate', 'answer_length'}
    if metric not in valid_metrics:
        raise ValueError(f"metric must be one of {sorted(valid_metrics)}, got '{metric}'")

    valid_periods = {'hour', 'day', 'week', 'month'}
    if period not in valid_periods:
        raise ValueError(f"period must be one of {sorted(valid_periods)}, got '{period}'")

    # Validate limit is a positive integer
    if not isinstance(limit, int) or limit <= 0:
        raise ValueError("limit must be a positive integer")

    format_map = {
        'hour': '%Y-%m-%d %H:00:00',
        'day': '%Y-%m-%d 00:00:00',
        'week': '%Y-W%W',
        'month': '%Y-%m-01',
    }
    strftime_format = format_map[period]

    conn = _get_connection()
    cursor = conn.cursor()

    # Use metric validation to build query safely
    if metric == 'execution_time':
        query = '''
            SELECT strftime(?, timestamp) as period,
                   AVG(execution_time_seconds) as value
            FROM search_results
            WHERE execution_time_seconds IS NOT NULL
        '''
    elif metric == 'success_rate':
        query = '''
            SELECT strftime(?, timestamp) as period,
                   AVG(CAST(success AS FLOAT)) as value
            FROM search_results
        '''
    else:  # answer_length
        query = '''
            SELECT strftime(?, timestamp) as period,
                   AVG(LENGTH(answer_text)) as value
            FROM search_results
            WHERE answer_text IS NOT NULL
        '''

    params = [strftime_format]

    if model:
        query += ' AND model = ?'
        params.append(model)

    query += ' GROUP BY period ORDER BY period DESC LIMIT ?'
    params.append(limit)

    cursor.execute(query, params)
    results = cursor.fetchall()
    conn.close()

    if not results:
        return None

    return [(period_str, value) for period_str, value in results]


# ==============================================================================
# Advanced Analytics Functions
# ==============================================================================


def get_percentiles(
    metric: str = 'execution_time',
    percentiles: Optional[List[int]] = None,
    model: Optional[str] = None
) -> Optional[Dict[int, float]]:
    """
    Calculate percentiles for a specific metric.

    Computes specified percentiles (25th, 50th, 75th, 90th, 95th, 99th, etc.)

    Args:
        metric: 'execution_time', 'success_rate', or 'answer_length'
        percentiles: List of percentile values (0-100), defaults to [25, 50, 75, 90, 95, 99]
        model: Filter by specific model (optional)

    Returns:
        Dictionary mapping percentile to value
        Returns None if no results found

    Raises:
        ValueError: If metric is invalid or percentiles are out of range
    """
    if percentiles is None:
        percentiles = [25, 50, 75, 90, 95, 99]

    valid_metrics = {'execution_time', 'success_rate', 'answer_length'}
    if metric not in valid_metrics:
        raise ValueError(f"metric must be one of {sorted(valid_metrics)}, got '{metric}'")

    # Validate percentiles
    if not all(0 <= p <= 100 for p in percentiles):
        raise ValueError("All percentiles must be between 0 and 100")

    conn = _get_connection()
    cursor = conn.cursor()

    if metric == 'execution_time':
        query = 'SELECT execution_time_seconds FROM search_results WHERE execution_time_seconds IS NOT NULL'
    elif metric == 'success_rate':
        query = 'SELECT CAST(success AS FLOAT) FROM search_results'
    else:  # answer_length
        query = 'SELECT LENGTH(answer_text) FROM search_results WHERE answer_text IS NOT NULL'

    params = []

    if model:
        query += ' AND model = ?'
        params.append(model)

    cursor.execute(query, params)
    values = [row[0] for row in cursor.fetchall()]
    conn.close()

    if not values:
        return None

    result = {}
    sorted_values = sorted(values)

    for percentile in sorted(percentiles):
        # Calculate percentile using linear interpolation
        index = (percentile / 100.0) * (len(sorted_values) - 1)
        lower_idx = int(index)
        upper_idx = min(lower_idx + 1, len(sorted_values) - 1)
        fraction = index - lower_idx

        value = sorted_values[lower_idx] * (1 - fraction) + sorted_values[upper_idx] * fraction
        result[percentile] = value

    return result


def get_outliers(
    metric: str = 'execution_time',
    threshold_std_dev: float = 3.0,
    model: Optional[str] = None
) -> Optional[List[Dict[str, Any]]]:
    """
    Identify statistical outliers in a metric.

    Uses standard deviation method to find values exceeding threshold.

    Args:
        metric: 'execution_time', 'success_rate', or 'answer_length'
        threshold_std_dev: Number of standard deviations to consider as outlier (default: 3.0)
        model: Filter by specific model (optional)

    Returns:
        List of result dictionaries containing outlier records
        Returns None if no results found

    Raises:
        ValueError: If metric is invalid
    """
    valid_metrics = {'execution_time', 'success_rate', 'answer_length'}
    if metric not in valid_metrics:
        raise ValueError(f"metric must be one of {sorted(valid_metrics)}, got '{metric}'")

    conn = _get_connection()
    cursor = conn.cursor()

    # Get all values with record IDs for filtering
    if metric == 'execution_time':
        query = '''
            SELECT id, execution_time_seconds as value
            FROM search_results
            WHERE execution_time_seconds IS NOT NULL
        '''
    elif metric == 'success_rate':
        query = '''
            SELECT id, CAST(success AS FLOAT) as value
            FROM search_results
        '''
    else:  # answer_length
        query = '''
            SELECT id, LENGTH(answer_text) as value
            FROM search_results
            WHERE answer_text IS NOT NULL
        '''

    params = []

    if model:
        query += ' AND model = ?'
        params.append(model)

    cursor.execute(query, params)
    rows = cursor.fetchall()

    if not rows:
        conn.close()
        return None

    ids = [row[0] for row in rows]
    values = [row[1] for row in rows]

    # Calculate mean and std dev
    mean_val = statistics.mean(values)
    std_dev = statistics.stdev(values) if len(values) > 1 else 0.0

    # Find outliers
    outlier_ids = []
    for val_id, value in zip(ids, values):
        if std_dev > 0 and abs(value - mean_val) > threshold_std_dev * std_dev:
            outlier_ids.append(val_id)

    if not outlier_ids:
        conn.close()
        return None

    # Get full record data for outliers
    placeholders = ','.join('?' * len(outlier_ids))
    query = f'SELECT * FROM search_results WHERE id IN ({placeholders})'

    conn = _get_connection()
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute(query, outlier_ids)
    outlier_rows = cursor.fetchall()
    conn.close()

    results = []
    for row in outlier_rows:
        result = dict(row)
        try:
            result['sources'] = json.loads(result['sources']) if result['sources'] else []
        except json.JSONDecodeError:
            result['sources'] = []
        results.append(result)

    return results if results else None


def get_histogram_data(
    metric: str = 'execution_time',
    bins: int = 10,
    model: Optional[str] = None
) -> Optional[List[Tuple[float, float, int]]]:
    """
    Generate histogram data for a metric.

    Returns data suitable for creating frequency distribution visualizations.

    Args:
        metric: 'execution_time', 'success_rate', or 'answer_length'
        bins: Number of bins for histogram (default: 10)
        model: Filter by specific model (optional)

    Returns:
        List of tuples: (bin_start, bin_end, count)
        Returns None if no results found

    Raises:
        ValueError: If metric is invalid or bins is less than 1
    """
    valid_metrics = {'execution_time', 'success_rate', 'answer_length'}
    if metric not in valid_metrics:
        raise ValueError(f"metric must be one of {sorted(valid_metrics)}, got '{metric}'")

    if bins < 1:
        raise ValueError("bins must be at least 1")

    conn = _get_connection()
    cursor = conn.cursor()

    if metric == 'execution_time':
        query = 'SELECT execution_time_seconds FROM search_results WHERE execution_time_seconds IS NOT NULL'
    elif metric == 'success_rate':
        query = 'SELECT CAST(success AS FLOAT) FROM search_results'
    else:  # answer_length
        query = 'SELECT LENGTH(answer_text) FROM search_results WHERE answer_text IS NOT NULL'

    params = []

    if model:
        query += ' AND model = ?'
        params.append(model)

    cursor.execute(query, params)
    values = [row[0] for row in cursor.fetchall()]
    conn.close()

    if not values:
        return None

    # Calculate bin ranges
    min_val = min(values)
    max_val = max(values)

    # Handle case where all values are the same
    if min_val == max_val:
        return [(min_val, min_val, len(values))]

    bin_width = (max_val - min_val) / bins
    histogram = []

    for i in range(bins):
        bin_start = min_val + (i * bin_width)
        bin_end = bin_start + bin_width
        # Count values in this bin (inclusive on start, exclusive on end, except last bin)
        count = sum(1 for v in values if bin_start <= v < bin_end or (i == bins - 1 and v == bin_end))
        histogram.append((bin_start, bin_end, count))

    return histogram


# ==============================================================================
# Data Quality Functions
# ==============================================================================


def find_duplicate_queries(threshold_similarity: float = 1.0) -> Optional[List[Dict[str, Any]]]:
    """
    Find duplicate or similar queries in the database.

    Uses exact string matching or similarity threshold for fuzzy matching.

    Args:
        threshold_similarity: Similarity threshold (1.0 = exact match only)
                            Values between 0-1 for fuzzy matching (0.8 = 80% similar)

    Returns:
        List of duplicate groups, each containing:
        - query_text: The query string
        - count: Number of occurrences
        - similar_queries: List of other similar query strings
        Returns None if no duplicates found

    Raises:
        ValueError: If threshold_similarity is not between 0.0 and 1.0
    """
    if not 0.0 <= threshold_similarity <= 1.0:
        raise ValueError("threshold_similarity must be between 0.0 and 1.0")

    conn = _get_connection()
    cursor = conn.cursor()

    if threshold_similarity == 1.0:
        # Exact match only
        query = '''
            SELECT query, COUNT(*) as count
            FROM search_results
            GROUP BY query
            HAVING COUNT(*) > 1
            ORDER BY count DESC
        '''
        cursor.execute(query)
        rows = cursor.fetchall()
        conn.close()

        if not rows:
            return None

        results = []
        for query_text, count in rows:
            results.append({
                'query_text': query_text,
                'count': count,
                'similar_queries': [],
            })

        return results
    else:
        # Fuzzy matching using simple character-level similarity
        query = 'SELECT DISTINCT query FROM search_results'
        cursor.execute(query)
        all_queries = [row[0] for row in cursor.fetchall()]
        conn.close()

        if not all_queries:
            return None

        # Simple Levenshtein-like similarity (for basic matching)
        def string_similarity(s1: str, s2: str) -> float:
            """Calculate simple string similarity (0-1)."""
            if len(s1) == 0 and len(s2) == 0:
                return 1.0
            if len(s1) == 0 or len(s2) == 0:
                return 0.0

            matches = sum(1 for c1, c2 in zip(s1, s2) if c1 == c2)
            return matches / max(len(s1), len(s2))

        # Find similar query groups
        seen = set()
        groups = []

        for i, query1 in enumerate(all_queries):
            if query1 in seen:
                continue

            similar = [query1]
            for j, query2 in enumerate(all_queries):
                if i != j and query2 not in seen:
                    similarity = string_similarity(query1.lower(), query2.lower())
                    if similarity >= threshold_similarity:
                        similar.append(query2)
                        seen.add(query2)

            if len(similar) > 1:
                seen.add(query1)
                groups.append({
                    'query_text': query1,
                    'count': len(similar),
                    'similar_queries': similar[1:],
                })

        return groups if groups else None


def get_database_summary() -> Dict[str, Any]:
    """
    Get comprehensive summary statistics of the entire database.

    Returns overall metrics including total records, date range, and health indicators.

    Returns:
        Dictionary with keys:
        - total_records: Total number of search results
        - total_successful: Count of successful searches
        - total_failed: Count of failed searches
        - success_rate: Overall success percentage
        - unique_queries: Number of distinct queries
        - unique_models: Number of distinct models
        - date_range_start: Oldest record timestamp
        - date_range_end: Most recent record timestamp
        - avg_execution_time: Mean execution time across all searches
        - total_sources: Total number of sources cited
        - avg_answer_length: Mean answer text length
    """
    conn = _get_connection()
    cursor = conn.cursor()

    # Total records and success/failure counts
    cursor.execute('''
        SELECT COUNT(*) as total,
               SUM(CASE WHEN success THEN 1 ELSE 0 END) as successful
        FROM search_results
    ''')
    total, successful = cursor.fetchone()
    total = total or 0
    successful = successful or 0
    failed = total - successful

    # Unique queries and models
    cursor.execute('SELECT COUNT(DISTINCT query) FROM search_results')
    unique_queries = cursor.fetchone()[0] or 0

    cursor.execute('SELECT COUNT(DISTINCT model) FROM search_results WHERE model IS NOT NULL')
    unique_models = cursor.fetchone()[0] or 0

    # Date range
    cursor.execute('SELECT MIN(timestamp), MAX(timestamp) FROM search_results')
    date_start, date_end = cursor.fetchone()

    # Average metrics
    cursor.execute('SELECT AVG(execution_time_seconds) FROM search_results WHERE execution_time_seconds IS NOT NULL')
    avg_exec_time = cursor.fetchone()[0] or 0.0

    cursor.execute('SELECT AVG(LENGTH(answer_text)) FROM search_results WHERE answer_text IS NOT NULL')
    avg_answer_length = cursor.fetchone()[0] or 0.0

    # Total sources (need to parse JSON)
    cursor.execute('SELECT sources FROM search_results WHERE sources IS NOT NULL')
    total_sources = 0
    for (sources_json,) in cursor.fetchall():
        try:
            sources = json.loads(sources_json) if sources_json else []
            total_sources += len(sources)
        except json.JSONDecodeError:
            pass

    conn.close()

    return {
        'total_records': total,
        'total_successful': successful,
        'total_failed': failed,
        'success_rate': successful / total if total > 0 else 0.0,
        'unique_queries': unique_queries,
        'unique_models': unique_models,
        'date_range_start': date_start,
        'date_range_end': date_end,
        'avg_execution_time': avg_exec_time,
        'total_sources': total_sources,
        'avg_answer_length': avg_answer_length,
    }
