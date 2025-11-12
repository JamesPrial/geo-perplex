"""
Analysis and comparison script for search results
Query and compare Perplexity search results across models and time
"""
import sys
import os
import argparse
import csv
import sqlite3
import logging
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from collections import defaultdict
from src.utils.storage import (
    get_results_by_query,
    get_results_by_model,
    compare_models_for_query,
    get_recent_results,
    get_unique_queries,
    get_unique_models,
    DB_PATH
)
from src.utils.json_export import export_database_to_json

logger = logging.getLogger(__name__)


def format_timestamp(timestamp_str: str) -> str:
    """Format timestamp for display"""
    if timestamp_str is None:
        return "N/A"
    try:
        dt = datetime.fromisoformat(timestamp_str)
        return dt.strftime('%Y-%m-%d %H:%M:%S')
    except:
        return str(timestamp_str) if timestamp_str else "N/A"


def print_result(result: Dict, show_full_answer: bool = False) -> None:
    """Print a single result in formatted way"""
    print(f"\n{'='*80}")
    print(f"ID: {result.get('id', 'N/A')}")
    print(f"Query: {result.get('query', 'N/A')}")
    print(f"Model: {result.get('model') or 'default'}")
    print(f"Timestamp: {format_timestamp(result.get('timestamp'))}")
    exec_time = result.get('execution_time_seconds') or 0
    print(f"Execution Time: {exec_time:.2f}s")
    print(f"Success: {'✓' if result.get('success', True) else '✗'}")

    if not result.get('success', True) and result.get('error_message'):
        print(f"Error: {result['error_message']}")

    if result.get('screenshot_path'):
        print(f"Screenshot: {result['screenshot_path']}")

    answer_text = result.get('answer_text') or ''
    print(f"\nAnswer ({len(answer_text)} chars):")
    print("-" * 80)
    if show_full_answer:
        print(answer_text)
    else:
        # Show first 500 chars
        answer_preview = answer_text[:500]
        if len(answer_text) > 500:
            answer_preview += '...'
        print(answer_preview)

    sources = result.get('sources', [])
    if sources and isinstance(sources, list):
        print(f"\nSources ({len(sources)}):")
        print("-" * 80)
        for i, source in enumerate(sources[:5], 1):
            if isinstance(source, dict):
                print(f"{i}. {source.get('text', 'N/A')}")
                print(f"   {source.get('url', 'N/A')}")


def list_queries(args) -> None:
    """List all unique queries in database"""
    queries = get_unique_queries()
    print(f"\n📋 Found {len(queries)} unique queries:\n")
    for i, query in enumerate(queries, 1):
        print(f"{i}. {query}")


def list_models(args) -> None:
    """List all unique models in database"""
    models = get_unique_models()
    print(f"\n🤖 Found {len(models)} unique models:\n")
    for i, model in enumerate(models, 1):
        print(f"{i}. {model}")


def show_recent(args) -> None:
    """Show recent search results"""
    limit = args.limit or 10
    results = get_recent_results(limit=limit)

    print(f"\n📊 Most recent {len(results)} search results:\n")
    for result in results:
        print_result(result, show_full_answer=args.full)


def show_by_query(args) -> None:
    """Show all results for a specific query"""
    if not args.query:
        print("❌ Error: --query is required")
        return

    results = get_results_by_query(args.query, model=args.model)

    print(f"\n📊 Found {len(results)} results for query: \"{args.query}\"")
    if args.model:
        print(f"   Filtered by model: {args.model}")
    print()

    for result in results:
        print_result(result, show_full_answer=args.full)


def show_by_model(args) -> None:
    """Show all results for a specific model"""
    if not args.model:
        print("❌ Error: --model is required")
        return

    limit = args.limit or 50
    results = get_results_by_model(args.model, limit=limit)

    print(f"\n📊 Found {len(results)} results for model: {args.model}\n")

    for result in results:
        print_result(result, show_full_answer=args.full)


def compare_models(args) -> None:
    """Compare results across models for a specific query"""
    if not args.query:
        print("❌ Error: --query is required")
        return

    results_by_model = compare_models_for_query(args.query)

    if not results_by_model:
        print(f"❌ No results found for query: \"{args.query}\"")
        return

    print(f"\n📊 COMPARISON: \"{args.query}\"")
    print(f"{'='*80}\n")
    print(f"Found results from {len(results_by_model)} model(s):\n")

    for model, results in sorted(results_by_model.items()):
        print(f"\n{'='*80}")
        print(f"MODEL: {model}")
        print(f"{'='*80}")
        print(f"Number of results: {len(results)}\n")

        # Show most recent result for this model
        if results:
            latest = results[0]
            print(f"Latest result:")
            print(f"  Timestamp: {format_timestamp(latest['timestamp'])}")
            latest_exec_time = latest.get('execution_time_seconds') or 0
            print(f"  Execution Time: {latest_exec_time:.2f}s")
            print(f"  Answer Length: {len(latest['answer_text'])} chars")
            print(f"  Sources: {len(latest['sources'])}")

            if args.full:
                print(f"\n  Answer:")
                print(f"  {'-'*76}")
                for line in latest['answer_text'].split('\n'):
                    print(f"  {line}")
            else:
                print(f"\n  Answer Preview (first 300 chars):")
                print(f"  {'-'*76}")
                preview = latest['answer_text'][:300]
                if len(latest['answer_text']) > 300:
                    preview += '...'
                for line in preview.split('\n'):
                    print(f"  {line}")


def export_results(args) -> None:
    """Export search results to JSON file"""
    if not args.output:
        print("❌ Error: --output is required")
        return

    try:
        summary = export_database_to_json(
            output_path=args.output,
            query_filter=args.query,
            model_filter=args.model,
            limit=args.limit
        )
        print(f"\n✅ Export Complete!")
        print(f"Records exported: {summary['records_exported']}")
        print(f"File size: {summary['file_size_bytes']:,} bytes")
        print(f"Output path: {summary['output_path']}")
    except ValueError as e:
        print(f"❌ Error: {e}")
    except IOError as e:
        print(f"❌ File error: {e}")
    except Exception as e:
        print(f"❌ Unexpected error: {e}")


# Database Query Helpers

def _get_connection():
    """Get database connection"""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def _parse_date(date_str: str) -> Optional[datetime]:
    """Parse date string in YYYY-MM-DD format"""
    try:
        return datetime.strptime(date_str, '%Y-%m-%d')
    except ValueError:
        return None


def _filter_results_advanced(
    model: Optional[str] = None,
    query_pattern: Optional[str] = None,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    success_only: bool = False,
    failed_only: bool = False,
    min_exec_time: Optional[float] = None,
    max_exec_time: Optional[float] = None,
    min_answer_length: Optional[int] = None,
    max_answer_length: Optional[int] = None,
    has_sources: bool = False,
    limit: Optional[int] = None,
    order_by: str = 'timestamp',
    order_desc: bool = True
) -> List[Dict]:
    """Advanced filtering with multiple criteria"""
    # Validate order_by against whitelist
    valid_orders = {'timestamp', 'query', 'model', 'execution_time_seconds', 'id'}
    if order_by not in valid_orders:
        raise ValueError(f"Invalid order_by: {order_by}. Must be one of {sorted(valid_orders)}")

    # Validate limit parameter
    if limit is not None:
        if not isinstance(limit, int) or limit <= 0:
            raise ValueError(f"limit must be a positive integer, got {limit}")

    with sqlite3.connect(DB_PATH) as conn:
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        where_clauses = []
        params = []

        if model:
            where_clauses.append("model = ?")
            params.append(model)

        if query_pattern:
            where_clauses.append("query LIKE ?")
            params.append(f"%{query_pattern}%")

        if start_date:
            dt = _parse_date(start_date)
            if dt:
                where_clauses.append("timestamp >= ?")
                params.append(dt.isoformat())

        if end_date:
            dt = _parse_date(end_date)
            if dt:
                dt = dt.replace(hour=23, minute=59, second=59)
                where_clauses.append("timestamp <= ?")
                params.append(dt.isoformat())

        if success_only:
            where_clauses.append("success = 1")
        elif failed_only:
            where_clauses.append("success = 0")

        if min_exec_time is not None:
            where_clauses.append("execution_time_seconds >= ?")
            params.append(min_exec_time)

        if max_exec_time is not None:
            where_clauses.append("execution_time_seconds <= ?")
            params.append(max_exec_time)

        if min_answer_length is not None:
            where_clauses.append("LENGTH(answer_text) >= ?")
            params.append(min_answer_length)

        if max_answer_length is not None:
            where_clauses.append("LENGTH(answer_text) <= ?")
            params.append(max_answer_length)

        if has_sources:
            where_clauses.append("sources IS NOT NULL AND sources != ''")

        where_clause = " WHERE " + " AND ".join(where_clauses) if where_clauses else ""

        order_direction = "DESC" if order_desc else "ASC"

        # Build query without f-string for LIMIT
        query = f"""
            SELECT * FROM search_results
            {where_clause}
            ORDER BY {order_by} {order_direction}
        """

        # Add LIMIT using parameterized query
        if limit:
            query += " LIMIT ?"
            params.append(limit)

        cursor.execute(query, params)
        rows = cursor.fetchall()

    results = []
    for row in rows:
        result = dict(row)
        try:
            import json
            result['sources'] = json.loads(result['sources']) if result['sources'] else []
        except:
            result['sources'] = []
        results.append(result)

    return results


def _search_results(
    search_term: str,
    search_in: str = 'answers',
    model: Optional[str] = None,
    case_sensitive: bool = False,
    limit: Optional[int] = None
) -> List[Dict]:
    """Full-text search in answers, sources, or queries"""
    # Validate search_in parameter
    valid_search_in = {'answers', 'sources', 'queries', 'all'}
    if search_in not in valid_search_in:
        raise ValueError(f"Invalid search_in: {search_in}. Must be one of {sorted(valid_search_in)}")

    # Validate limit parameter
    if limit is not None:
        if not isinstance(limit, int) or limit <= 0:
            raise ValueError(f"limit must be a positive integer, got {limit}")

    with sqlite3.connect(DB_PATH) as conn:
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        where_clauses = []
        params = []

        if case_sensitive:
            if search_in in ('answers', 'all'):
                where_clauses.append("answer_text LIKE ?")
                params.append(f"%{search_term}%")
            if search_in in ('queries', 'all'):
                where_clauses.append("query LIKE ?")
                params.append(f"%{search_term}%")
            if search_in in ('sources', 'all'):
                where_clauses.append("sources LIKE ?")
                params.append(f"%{search_term}%")
        else:
            search_term_lower = search_term.lower()
            if search_in in ('answers', 'all'):
                where_clauses.append("LOWER(answer_text) LIKE ?")
                params.append(f"%{search_term_lower}%")
            if search_in in ('queries', 'all'):
                where_clauses.append("LOWER(query) LIKE ?")
                params.append(f"%{search_term_lower}%")
            if search_in in ('sources', 'all'):
                where_clauses.append("LOWER(sources) LIKE ?")
                params.append(f"%{search_term_lower}%")

        if model:
            where_clauses.append("model = ?")
            params.append(model)

        # Build WHERE clause: search terms (OR) AND model (if provided)
        search_conditions = where_clauses[:3]  # First 3 are search term clauses
        where_parts = []
        if search_conditions:
            where_parts.append("(" + " OR ".join(search_conditions) + ")")
        if model:
            where_parts.append("model = ?")

        where_clause = " WHERE " + " AND ".join(where_parts) if where_parts else ""

        query = f"""
            SELECT * FROM search_results
            {where_clause}
            ORDER BY timestamp DESC
        """

        # Add LIMIT using parameterized query
        if limit:
            query += " LIMIT ?"
            params.append(limit)

        cursor.execute(query, params)
        rows = cursor.fetchall()

    results = []
    for row in rows:
        result = dict(row)
        try:
            import json
            result['sources'] = json.loads(result['sources']) if result['sources'] else []
        except:
            result['sources'] = []
        results.append(result)

    return results


# Statistics Helpers

def _get_database_stats() -> Dict:
    """Get overall database statistics"""
    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.cursor()

        cursor.execute("SELECT COUNT(*) FROM search_results")
        total_records = cursor.fetchone()[0]

        cursor.execute("SELECT COUNT(DISTINCT model) FROM search_results WHERE model IS NOT NULL")
        unique_models = cursor.fetchone()[0]

        cursor.execute("SELECT COUNT(DISTINCT query) FROM search_results")
        unique_queries = cursor.fetchone()[0]

        cursor.execute("SELECT MIN(timestamp), MAX(timestamp) FROM search_results")
        date_range = cursor.fetchone()

        cursor.execute("SELECT COUNT(*) FROM search_results WHERE success = 1")
        successful = cursor.fetchone()[0]

        cursor.execute("SELECT AVG(execution_time_seconds) FROM search_results WHERE execution_time_seconds IS NOT NULL")
        avg_exec_time = cursor.fetchone()[0] or 0

        cursor.execute("SELECT AVG(LENGTH(answer_text)) FROM search_results WHERE answer_text IS NOT NULL")
        avg_answer_length = cursor.fetchone()[0] or 0

    success_rate = (successful / total_records * 100) if total_records > 0 else 0

    return {
        'total_records': total_records,
        'unique_models': unique_models,
        'unique_queries': unique_queries,
        'date_range': date_range,
        'successful_records': successful,
        'success_rate': success_rate,
        'avg_execution_time': avg_exec_time,
        'avg_answer_length': avg_answer_length
    }


def _get_model_stats(
    model: Optional[str] = None,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None
) -> Dict:
    """Get per-model statistics"""
    with sqlite3.connect(DB_PATH) as conn:
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        where_clauses = []
        params = []

        if model:
            where_clauses.append("model = ?")
            params.append(model)

        if start_date:
            dt = _parse_date(start_date)
            if dt:
                where_clauses.append("timestamp >= ?")
                params.append(dt.isoformat())

        if end_date:
            dt = _parse_date(end_date)
            if dt:
                dt = dt.replace(hour=23, minute=59, second=59)
                where_clauses.append("timestamp <= ?")
                params.append(dt.isoformat())

        where_clause = " WHERE " + " AND ".join(where_clauses) if where_clauses else ""

        if model:
            query = f"""
                SELECT
                    model,
                    COUNT(*) as record_count,
                    SUM(CASE WHEN success = 1 THEN 1 ELSE 0 END) as successful,
                    AVG(execution_time_seconds) as avg_exec_time,
                    MIN(execution_time_seconds) as min_exec_time,
                    MAX(execution_time_seconds) as max_exec_time,
                    AVG(LENGTH(answer_text)) as avg_answer_length,
                    AVG(JSON_ARRAY_LENGTH(sources)) as avg_sources
                FROM search_results
                {where_clause}
                GROUP BY model
            """
        else:
            query = f"""
                SELECT
                    model,
                    COUNT(*) as record_count,
                    SUM(CASE WHEN success = 1 THEN 1 ELSE 0 END) as successful,
                    AVG(execution_time_seconds) as avg_exec_time,
                    MIN(execution_time_seconds) as min_exec_time,
                    MAX(execution_time_seconds) as max_exec_time,
                    AVG(LENGTH(answer_text)) as avg_answer_length,
                    COUNT(DISTINCT query) as unique_queries
                FROM search_results
                {where_clause}
                GROUP BY model
                ORDER BY record_count DESC
            """

        cursor.execute(query, params)
        rows = cursor.fetchall()

    return [dict(row) for row in rows]


def _get_trend_data(
    metric: str,
    period: str,
    limit: Optional[int] = None,
    model: Optional[str] = None
) -> List[Dict]:
    """Get time-series trend data"""
    # Validate metric parameter
    valid_metrics = {'execution_time', 'success_rate', 'answer_length', 'query_volume'}
    if metric not in valid_metrics:
        raise ValueError(f"Invalid metric: {metric}. Must be one of {sorted(valid_metrics)}")

    # Validate period parameter
    valid_periods = {'hour', 'day', 'week', 'month'}
    if period not in valid_periods:
        raise ValueError(f"Invalid period: {period}. Must be one of {sorted(valid_periods)}")

    # Validate limit parameter
    if limit is not None:
        if not isinstance(limit, int) or limit <= 0:
            raise ValueError(f"limit must be a positive integer, got {limit}")

    with sqlite3.connect(DB_PATH) as conn:
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        # Map period to SQLite strftime format
        period_map = {
            'hour': '%Y-%m-%d %H:00',
            'day': '%Y-%m-%d',
            'week': '%Y-W%W',
            'month': '%Y-%m'
        }

        strftime_format = period_map[period]

        where_clause = ""
        params = [strftime_format]
        if model:
            where_clause = "WHERE model = ?"
            params.append(model)

        if metric == 'execution_time':
            query = """
                SELECT
                    strftime(?, timestamp) as period,
                    AVG(execution_time_seconds) as value,
                    COUNT(*) as count
                FROM search_results
                {where_clause}
                GROUP BY period
                ORDER BY period DESC
            """.format(where_clause=where_clause)
        elif metric == 'success_rate':
            query = """
                SELECT
                    strftime(?, timestamp) as period,
                    CAST(SUM(CASE WHEN success = 1 THEN 1 ELSE 0 END) * 100.0 / COUNT(*) AS REAL) as value,
                    COUNT(*) as count
                FROM search_results
                {where_clause}
                GROUP BY period
                ORDER BY period DESC
            """.format(where_clause=where_clause)
        elif metric == 'answer_length':
            query = """
                SELECT
                    strftime(?, timestamp) as period,
                    AVG(LENGTH(answer_text)) as value,
                    COUNT(*) as count
                FROM search_results
                {where_clause}
                GROUP BY period
                ORDER BY period DESC
            """.format(where_clause=where_clause)
        elif metric == 'query_volume':
            query = """
                SELECT
                    strftime(?, timestamp) as period,
                    COUNT(*) as value,
                    COUNT(DISTINCT query) as count
                FROM search_results
                {where_clause}
                GROUP BY period
                ORDER BY period DESC
            """.format(where_clause=where_clause)
        else:
            return []

        # Add LIMIT using parameterized query
        if limit:
            query += " LIMIT ?"
            params.append(limit)

        cursor.execute(query, params)
        rows = cursor.fetchall()

    return [dict(row) for row in rows]


def _find_duplicates(exact: bool = True) -> Dict[str, List[Dict]]:
    """Find duplicate or similar queries"""
    from difflib import SequenceMatcher

    threshold = 1.0 if exact else 0.9

    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.cursor()

        cursor.execute("SELECT DISTINCT query FROM search_results ORDER BY query")
        all_queries = [row[0] for row in cursor.fetchall()]

    duplicates = defaultdict(list)

    for i, query1 in enumerate(all_queries):
        for query2 in all_queries[i+1:]:
            similarity = SequenceMatcher(None, query1, query2).ratio()
            if similarity >= threshold:
                key = min(query1, query2)
                if query1 not in [q[0] for q in duplicates.get(key, [])]:
                    duplicates[key].append((query1, similarity))
                if query2 not in [q[0] for q in duplicates.get(key, [])]:
                    duplicates[key].append((query2, similarity))

    return dict(duplicates)


# Command Handlers

def handle_filter(args) -> None:
    """Handle filter command with advanced criteria"""
    try:
        results = _filter_results_advanced(
            model=args.model,
            query_pattern=args.query_pattern,
            start_date=args.start_date,
            end_date=args.end_date,
            success_only=args.success_only,
            failed_only=args.failed_only,
            min_exec_time=args.min_exec_time,
            max_exec_time=args.max_exec_time,
            min_answer_length=args.min_answer_length,
            max_answer_length=args.max_answer_length,
            has_sources=args.has_sources,
            limit=args.limit,
            order_by=args.order_by,
            order_desc=not args.order_asc
        )

        print(f"\n📊 Found {len(results)} results matching filter criteria\n")

        for result in results:
            print_result(result, show_full_answer=args.full)

    except Exception as e:
        print(f"❌ Error: {e}")


def handle_search(args) -> None:
    """Handle search command for full-text search"""
    try:
        if not args.search_term:
            print("❌ Error: search term is required")
            return

        results = _search_results(
            search_term=args.search_term,
            search_in=args.search_in,
            model=args.model,
            case_sensitive=args.case_sensitive,
            limit=args.limit
        )

        print(f"\n📊 Found {len(results)} results for: \"{args.search_term}\"")
        print(f"   Search in: {args.search_in}")
        if args.model:
            print(f"   Model: {args.model}")
        print()

        for result in results:
            print_result(result, show_full_answer=args.full)

    except Exception as e:
        print(f"❌ Error: {e}")


def handle_stats(args) -> None:
    """Handle stats command for database statistics"""
    try:
        stats = _get_database_stats()

        print("\n📊 DATABASE STATISTICS\n")
        print(f"Total Records: {stats['total_records']:,}")
        print(f"Unique Queries: {stats['unique_queries']:,}")
        print(f"Unique Models: {stats['unique_models']:,}")

        if stats['date_range'][0]:
            print(f"\nDate Range:")
            print(f"  From: {format_timestamp(stats['date_range'][0])}")
            print(f"  To:   {format_timestamp(stats['date_range'][1])}")

        print(f"\nSuccess Metrics:")
        print(f"  Successful: {stats['successful_records']:,} ({stats['success_rate']:.1f}%)")
        print(f"  Failed: {stats['total_records'] - stats['successful_records']:,}")

        print(f"\nPerformance:")
        print(f"  Avg Execution Time: {stats['avg_execution_time']:.2f}s")
        print(f"  Avg Answer Length: {stats['avg_answer_length']:.0f} chars")

    except Exception as e:
        print(f"❌ Error: {e}")


def handle_stats_model(args) -> None:
    """Handle stats-model command for per-model statistics"""
    try:
        model_stats = _get_model_stats(
            model=args.model,
            start_date=args.start_date,
            end_date=args.end_date
        )

        if not model_stats:
            print("❌ No data found matching criteria")
            return

        print("\n📊 MODEL STATISTICS\n")

        if args.model:
            stats = model_stats[0]
            print(f"Model: {stats['model'] or 'default'}")
            print(f"Records: {stats['record_count']}")
            print(f"Successful: {stats['successful']} ({stats['successful']/stats['record_count']*100:.1f}%)")
            print(f"\nExecution Time:")
            print(f"  Average: {stats['avg_exec_time']:.2f}s")
            print(f"  Min: {stats['min_exec_time']:.2f}s")
            print(f"  Max: {stats['max_exec_time']:.2f}s")
            print(f"\nAnswer Statistics:")
            print(f"  Avg Length: {stats['avg_answer_length']:.0f} chars")
            avg_sources = stats.get('avg_sources')
            if avg_sources:
                print(f"  Avg Sources: {avg_sources:.1f}")
        else:
            print("{'='*60}")
            print(f"{'Model':<20} {'Records':<10} {'Success %':<12} {'Avg Time':<12}")
            print(f"{'-'*60}")
            for stats in model_stats:
                model_name = (stats['model'] or 'default')[:20]
                success_pct = stats['successful'] / stats['record_count'] * 100 if stats['record_count'] > 0 else 0
                print(f"{model_name:<20} {stats['record_count']:<10} {success_pct:>10.1f}% {stats['avg_exec_time']:>10.2f}s")

    except Exception as e:
        print(f"❌ Error: {e}")


def handle_stats_trends(args) -> None:
    """Handle stats-trends command for trend analysis"""
    try:
        trend_data = _get_trend_data(
            metric=args.metric,
            period=args.period,
            limit=args.limit,
            model=args.model
        )

        if not trend_data:
            print("❌ No trend data found")
            return

        metric_labels = {
            'execution_time': 'Execution Time (s)',
            'success_rate': 'Success Rate (%)',
            'answer_length': 'Avg Answer Length',
            'query_volume': 'Query Count'
        }

        print(f"\n📊 TREND ANALYSIS - {metric_labels.get(args.metric, args.metric).upper()}")
        print(f"Period: {args.period.upper()}")
        if args.model:
            print(f"Model: {args.model}")
        print()

        print(f"{'Period':<20} {'Value':<15} {'Count':<10}")
        print(f"{'-'*45}")

        for row in trend_data:
            value = row.get('value', 0)
            if args.metric == 'execution_time':
                value_str = f"{value:.2f}s"
            elif args.metric == 'success_rate':
                value_str = f"{value:.1f}%"
            else:
                value_str = f"{value:.1f}"

            print(f"{row['period']:<20} {value_str:<15} {row['count']:<10}")

    except Exception as e:
        print(f"❌ Error: {e}")


def handle_stats_performance(args) -> None:
    """Handle stats-performance command for cross-model comparison"""
    try:
        results = _filter_results_advanced(
            query_pattern=args.query,
            start_date=args.start_date,
            end_date=args.end_date
        )

        if not results:
            print("❌ No results found matching criteria")
            return

        # Group by model
        by_model = defaultdict(list)
        for result in results:
            model = result['model'] or 'default'
            by_model[model].append(result)

        print("\n📊 PERFORMANCE COMPARISON")
        if args.query:
            print(f"Query: {args.query}")
        print()

        print(f"{'Model':<20} {'Count':<8} {'Success %':<12} {'Avg Time':<12} {'Avg Len':<12}")
        print(f"{'-'*64}")

        for model in sorted(by_model.keys()):
            data = by_model[model]
            success_count = sum(1 for r in data if r['success'])
            success_pct = success_count / len(data) * 100 if data else 0
            avg_time = sum(r.get('execution_time_seconds', 0) for r in data) / len(data) if data else 0
            avg_len = sum(len(r.get('answer_text', '')) for r in data) / len(data) if data else 0

            print(f"{model[:20]:<20} {len(data):<8} {success_pct:>10.1f}% {avg_time:>10.2f}s {avg_len:>10.0f}")

    except Exception as e:
        print(f"❌ Error: {e}")


def handle_export_csv(args) -> None:
    """Handle export-csv command"""
    try:
        if not args.output:
            print("❌ Error: output path is required")
            return

        results = _filter_results_advanced(
            model=args.model,
            query_pattern=args.query_pattern,
            start_date=args.start_date,
            end_date=args.end_date,
            success_only=args.success_only,
            failed_only=args.failed_only,
            min_exec_time=args.min_exec_time,
            max_exec_time=args.max_exec_time,
            min_answer_length=args.min_answer_length,
            max_answer_length=args.max_answer_length,
            has_sources=args.has_sources,
            limit=args.limit
        )

        if not results:
            print("❌ No results found matching criteria")
            return

        output_path = Path(args.output)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        with open(output_path, 'w', newline='', encoding='utf-8') as f:
            fieldnames = ['id', 'query', 'model', 'timestamp', 'success', 'execution_time_seconds']
            if args.include_sources:
                fieldnames.extend(['answer_length', 'source_count'])
            else:
                fieldnames.append('answer_length')

            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()

            for result in results:
                row = {
                    'id': result['id'],
                    'query': result['query'],
                    'model': result['model'] or 'default',
                    'timestamp': result['timestamp'],
                    'success': result['success'],
                    'execution_time_seconds': result['execution_time_seconds'],
                    'answer_length': len(result.get('answer_text', ''))
                }
                if args.include_sources:
                    sources = result.get('sources', [])
                    row['source_count'] = len(sources) if isinstance(sources, list) else 0

                writer.writerow(row)

        file_size = output_path.stat().st_size
        print(f"\n✅ CSV Export Complete!")
        print(f"Records exported: {len(results)}")
        print(f"File size: {file_size:,} bytes")
        print(f"Output path: {output_path.resolve()}")

    except Exception as e:
        print(f"❌ Error: {e}")


def handle_export_md(args) -> None:
    """Handle export-md command"""
    try:
        if not args.output:
            print("❌ Error: output path is required")
            return

        results = _filter_results_advanced(
            model=args.model,
            query_pattern=args.query_pattern,
            start_date=args.start_date,
            end_date=args.end_date,
            success_only=args.success_only,
            failed_only=args.failed_only,
            min_exec_time=args.min_exec_time,
            max_exec_time=args.max_exec_time,
            min_answer_length=args.min_answer_length,
            max_answer_length=args.max_answer_length,
            has_sources=args.has_sources,
            limit=args.limit
        )

        if not results:
            print("❌ No results found matching criteria")
            return

        output_path = Path(args.output)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        with open(output_path, 'w', encoding='utf-8') as f:
            f.write("# Search Results Report\n\n")
            f.write(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
            f.write(f"**Total Results:** {len(results)}\n\n")

            for i, result in enumerate(results, 1):
                f.write(f"## Result {i}\n\n")
                f.write(f"**Query:** {result['query']}\n\n")
                f.write(f"**Model:** {result['model'] or 'default'}\n\n")
                f.write(f"**Timestamp:** {format_timestamp(result['timestamp'])}\n\n")
                f.write(f"**Status:** {'Success' if result['success'] else 'Failed'}\n\n")
                f.write(f"**Execution Time:** {result.get('execution_time_seconds', 0):.2f}s\n\n")

                if result.get('answer_text'):
                    f.write("### Answer\n\n")
                    if args.full:
                        f.write(result['answer_text'] + "\n\n")
                    else:
                        preview = result['answer_text'][:500]
                        if len(result['answer_text']) > 500:
                            preview += "..."
                        f.write(preview + "\n\n")

                sources = result.get('sources', [])
                if sources and isinstance(sources, list):
                    f.write("### Sources\n\n")
                    for source in sources:
                        if isinstance(source, dict):
                            f.write(f"- [{source.get('text', 'Source')}]({source.get('url', '#')})\n")
                    f.write("\n")

                f.write("---\n\n")

        file_size = output_path.stat().st_size
        print(f"\n✅ Markdown Export Complete!")
        print(f"Records exported: {len(results)}")
        print(f"File size: {file_size:,} bytes")
        print(f"Output path: {output_path.resolve()}")

    except Exception as e:
        print(f"❌ Error: {e}")


def handle_export_batch(args) -> None:
    """Handle export-batch command"""
    try:
        if not args.output_dir:
            print("❌ Error: output directory is required")
            return

        output_dir = Path(args.output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)

        results = _filter_results_advanced(limit=None)

        if not results:
            print("❌ No results found")
            return

        # Group results
        if args.group_by == 'model':
            grouped = defaultdict(list)
            for result in results:
                model = result['model'] or 'default'
                grouped[model].append(result)
            group_name = "model"
        else:  # date
            grouped = defaultdict(list)
            for result in results:
                date_key = result['timestamp'][:10] if result['timestamp'] else 'unknown'
                grouped[date_key].append(result)
            group_name = "date"

        total_exported = 0
        for group_key, group_results in grouped.items():
            if args.format == 'json':
                filename = f"{group_name}_{group_key}.json"
                filepath = output_dir / filename
                import json
                with open(filepath, 'w', encoding='utf-8') as f:
                    json.dump(group_results, f, indent=2, default=str)
            elif args.format == 'csv':
                filename = f"{group_name}_{group_key}.csv"
                filepath = output_dir / filename
                with open(filepath, 'w', newline='', encoding='utf-8') as f:
                    fieldnames = ['id', 'query', 'model', 'timestamp', 'success', 'execution_time_seconds']
                    writer = csv.DictWriter(f, fieldnames=fieldnames)
                    writer.writeheader()
                    for result in group_results:
                        writer.writerow({
                            'id': result['id'],
                            'query': result['query'],
                            'model': result['model'] or 'default',
                            'timestamp': result['timestamp'],
                            'success': result['success'],
                            'execution_time_seconds': result['execution_time_seconds']
                        })

            total_exported += len(group_results)

        print(f"\n✅ Batch Export Complete!")
        print(f"Records exported: {total_exported}")
        print(f"Groups created: {len(grouped)}")
        print(f"Output directory: {output_dir.resolve()}")

    except Exception as e:
        print(f"❌ Error: {e}")


def handle_duplicates(args) -> None:
    """Handle duplicates command"""
    try:
        duplicates = _find_duplicates(exact=args.exact)

        if not duplicates:
            print("✅ No duplicates found")
            return

        print(f"\n⚠️  Found {len(duplicates)} groups of similar queries\n")

        for group_key, similar_queries in duplicates.items():
            if len(similar_queries) > 1:
                print(f"Group: {group_key[:60]}...")
                for query, similarity in similar_queries:
                    print(f"  - {query[:60]}... (similarity: {similarity:.0%})")
                print()

    except Exception as e:
        print(f"❌ Error: {e}")


def handle_cleanup(args) -> None:
    """Handle cleanup command for database maintenance"""
    try:
        if not args.dry_run and not args.confirm:
            print("⚠️  Use --confirm to perform actual cleanup (or --dry-run for preview)")
            return

        with sqlite3.connect(DB_PATH) as conn:
            cursor = conn.cursor()

            removed_count = 0
            archived_count = 0

            # Remove duplicates
            if args.remove_duplicates:
                cursor.execute("""
                    DELETE FROM search_results WHERE id NOT IN (
                        SELECT MIN(id) FROM search_results GROUP BY query, model, timestamp
                    )
                """)
                removed_count = cursor.rowcount
                if not args.dry_run:
                    conn.commit()
                    print(f"Removed {removed_count} duplicate records")
                else:
                    print(f"[DRY-RUN] Would remove {removed_count} duplicate records")

            # Archive old failed records
            if args.archive_before:
                dt = _parse_date(args.archive_before)
                if dt:
                    cursor.execute("""
                        DELETE FROM search_results
                        WHERE success = 0 AND timestamp < ?
                    """, (dt.isoformat(),))
                    archived_count = cursor.rowcount
                    if not args.dry_run:
                        conn.commit()
                        print(f"Archived {archived_count} failed records before {args.archive_before}")
                    else:
                        print(f"[DRY-RUN] Would archive {archived_count} failed records before {args.archive_before}")

        if args.dry_run:
            print(f"\n[DRY-RUN] Total would affect: {removed_count + archived_count} records")

    except Exception as e:
        print(f"❌ Error: {e}")


def handle_info(args) -> None:
    """Handle info command for database health"""
    try:
        if not DB_PATH.exists():
            print("❌ Database not found")
            return

        file_size = DB_PATH.stat().st_size

        with sqlite3.connect(DB_PATH) as conn:
            cursor = conn.cursor()

            cursor.execute("SELECT COUNT(*) FROM search_results")
            record_count = cursor.fetchone()[0]

            cursor.execute("SELECT page_count * page_size FROM pragma_page_count(), pragma_page_size()")
            db_size = cursor.fetchone()[0]

        print("\n📊 DATABASE HEALTH INFORMATION\n")
        print(f"File Size: {file_size:,} bytes ({file_size / (1024*1024):.2f} MB)")
        print(f"Database Size: {db_size:,} bytes")
        print(f"Record Count: {record_count:,}")
        print(f"Avg Record Size: {(file_size / record_count) if record_count > 0 else 0:.0f} bytes")
        print(f"Database Path: {DB_PATH.resolve()}")

    except Exception as e:
        print(f"❌ Error: {e}")


def main():
    """Main CLI entry point"""
    parser = argparse.ArgumentParser(
        description='Analyze and compare Perplexity search results',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # List all queries
  python -m src.analyze list-queries

  # List all models
  python -m src.analyze list-models

  # Show recent results
  python -m src.analyze recent --limit 20

  # Show all results for a specific query
  python -m src.analyze query --query "What is Python?"

  # Show results for a specific query and model
  python -m src.analyze query --query "What is Python?" --model gpt-4

  # Show all results for a specific model
  python -m src.analyze model --model claude-3

  # Compare models for a specific query
  python -m src.analyze compare --query "What is Python?" --full

  # Advanced filtering
  python -m src.analyze filter --model gpt-4 --start-date 2025-01-01 --success-only --limit 20

  # Full-text search
  python -m src.analyze search "machine learning" --in answers --limit 10

  # Database statistics
  python -m src.analyze stats
  python -m src.analyze stats-model --model gpt-4
  python -m src.analyze stats-trends --metric execution_time --period day --limit 30
  python -m src.analyze stats-performance --query "What is GEO?"

  # Export formats
  python -m src.analyze export --output results.json
  python -m src.analyze export-csv results.csv --model gpt-4
  python -m src.analyze export-md report.md --full
  python -m src.analyze export-batch exports/ --format csv --group-by model

  # Database maintenance
  python -m src.analyze duplicates --exact
  python -m src.analyze cleanup --dry-run
  python -m src.analyze info
        """
    )

    subparsers = parser.add_subparsers(dest='command', help='Command to execute')

    # list-queries command
    parser_queries = subparsers.add_parser('list-queries', help='List all unique queries')
    parser_queries.set_defaults(func=list_queries)

    # list-models command
    parser_models = subparsers.add_parser('list-models', help='List all unique models')
    parser_models.set_defaults(func=list_models)

    # recent command
    parser_recent = subparsers.add_parser('recent', help='Show recent search results')
    parser_recent.add_argument('--limit', type=int, help='Number of results to show (default: 10)')
    parser_recent.add_argument('--full', action='store_true', help='Show full answer text')
    parser_recent.set_defaults(func=show_recent)

    # query command
    parser_query = subparsers.add_parser('query', help='Show results for a specific query')
    parser_query.add_argument('--query', required=True, help='Query to search for')
    parser_query.add_argument('--model', help='Filter by model')
    parser_query.add_argument('--full', action='store_true', help='Show full answer text')
    parser_query.set_defaults(func=show_by_query)

    # model command
    parser_model = subparsers.add_parser('model', help='Show results for a specific model')
    parser_model.add_argument('--model', required=True, help='Model to filter by')
    parser_model.add_argument('--limit', type=int, help='Number of results to show (default: 50)')
    parser_model.add_argument('--full', action='store_true', help='Show full answer text')
    parser_model.set_defaults(func=show_by_model)

    # compare command
    parser_compare = subparsers.add_parser('compare', help='Compare models for a specific query')
    parser_compare.add_argument('--query', required=True, help='Query to compare')
    parser_compare.add_argument('--full', action='store_true', help='Show full answer text')
    parser_compare.set_defaults(func=compare_models)

    # export command (JSON)
    parser_export = subparsers.add_parser('export', help='Export search results to JSON')
    parser_export.add_argument('--output', '-o', required=True,
                               help='Output JSON file path')
    parser_export.add_argument('--query', help='Filter by query text')
    parser_export.add_argument('--model', help='Filter by model name')
    parser_export.add_argument('--limit', type=int, help='Limit number of results')
    parser_export.set_defaults(func=export_results)

    # filter command
    parser_filter = subparsers.add_parser('filter', help='Advanced filtering with multiple criteria')
    parser_filter.add_argument('--model', help='Filter by model')
    parser_filter.add_argument('--query-pattern', help='Filter by query pattern (substring match)')
    parser_filter.add_argument('--start-date', help='Start date (YYYY-MM-DD)')
    parser_filter.add_argument('--end-date', help='End date (YYYY-MM-DD)')
    parser_filter.add_argument('--success-only', action='store_true', help='Only successful results')
    parser_filter.add_argument('--failed-only', action='store_true', help='Only failed results')
    parser_filter.add_argument('--min-exec-time', type=float, help='Minimum execution time (seconds)')
    parser_filter.add_argument('--max-exec-time', type=float, help='Maximum execution time (seconds)')
    parser_filter.add_argument('--min-answer-length', type=int, help='Minimum answer length (chars)')
    parser_filter.add_argument('--max-answer-length', type=int, help='Maximum answer length (chars)')
    parser_filter.add_argument('--has-sources', action='store_true', help='Only results with sources')
    parser_filter.add_argument('--limit', type=int, help='Limit number of results')
    parser_filter.add_argument('--order-by', default='timestamp',
                              choices=['timestamp', 'query', 'model', 'execution_time_seconds', 'id'],
                              help='Order by field (default: timestamp)')
    parser_filter.add_argument('--order-asc', action='store_true', help='Sort ascending (default: descending)')
    parser_filter.add_argument('--full', action='store_true', help='Show full answer text')
    parser_filter.set_defaults(func=handle_filter)

    # search command
    parser_search = subparsers.add_parser('search', help='Full-text search in results')
    parser_search.add_argument('search_term', help='Search term')
    parser_search.add_argument('--in', dest='search_in', default='answers',
                              choices=['answers', 'sources', 'queries', 'all'],
                              help='Search in (default: answers)')
    parser_search.add_argument('--model', help='Filter by model')
    parser_search.add_argument('--case-sensitive', action='store_true', help='Case-sensitive search')
    parser_search.add_argument('--limit', type=int, help='Limit number of results')
    parser_search.add_argument('--full', action='store_true', help='Show full answer text')
    parser_search.set_defaults(func=handle_search)

    # stats command
    parser_stats = subparsers.add_parser('stats', help='Show database statistics')
    parser_stats.set_defaults(func=handle_stats)

    # stats-model command
    parser_stats_model = subparsers.add_parser('stats-model', help='Show per-model statistics')
    parser_stats_model.add_argument('--model', help='Filter by specific model (show all if omitted)')
    parser_stats_model.add_argument('--start-date', help='Start date (YYYY-MM-DD)')
    parser_stats_model.add_argument('--end-date', help='End date (YYYY-MM-DD)')
    parser_stats_model.add_argument('--full', action='store_true', help='Show detailed statistics')
    parser_stats_model.set_defaults(func=handle_stats_model)

    # stats-trends command
    parser_stats_trends = subparsers.add_parser('stats-trends', help='Show trend analysis over time')
    parser_stats_trends.add_argument('--metric', default='execution_time',
                                    choices=['execution_time', 'success_rate', 'answer_length', 'query_volume'],
                                    help='Metric to analyze (default: execution_time)')
    parser_stats_trends.add_argument('--period', default='day',
                                    choices=['hour', 'day', 'week', 'month'],
                                    help='Time period (default: day)')
    parser_stats_trends.add_argument('--limit', type=int, help='Limit number of periods')
    parser_stats_trends.add_argument('--model', help='Filter by model')
    parser_stats_trends.set_defaults(func=handle_stats_trends)

    # stats-performance command
    parser_stats_perf = subparsers.add_parser('stats-performance', help='Compare performance across models')
    parser_stats_perf.add_argument('--query', help='Filter by query pattern')
    parser_stats_perf.add_argument('--start-date', help='Start date (YYYY-MM-DD)')
    parser_stats_perf.add_argument('--end-date', help='End date (YYYY-MM-DD)')
    parser_stats_perf.set_defaults(func=handle_stats_performance)

    # export-csv command
    parser_export_csv = subparsers.add_parser('export-csv', help='Export results to CSV')
    parser_export_csv.add_argument('output', help='Output CSV file path')
    parser_export_csv.add_argument('--model', help='Filter by model')
    parser_export_csv.add_argument('--query-pattern', help='Filter by query pattern')
    parser_export_csv.add_argument('--start-date', help='Start date (YYYY-MM-DD)')
    parser_export_csv.add_argument('--end-date', help='End date (YYYY-MM-DD)')
    parser_export_csv.add_argument('--success-only', action='store_true', help='Only successful results')
    parser_export_csv.add_argument('--failed-only', action='store_true', help='Only failed results')
    parser_export_csv.add_argument('--min-exec-time', type=float, help='Minimum execution time (seconds)')
    parser_export_csv.add_argument('--max-exec-time', type=float, help='Maximum execution time (seconds)')
    parser_export_csv.add_argument('--min-answer-length', type=int, help='Minimum answer length (chars)')
    parser_export_csv.add_argument('--max-answer-length', type=int, help='Maximum answer length (chars)')
    parser_export_csv.add_argument('--has-sources', action='store_true', help='Only results with sources')
    parser_export_csv.add_argument('--include-sources', action='store_true', help='Include source count in export')
    parser_export_csv.add_argument('--limit', type=int, help='Limit number of results')
    parser_export_csv.set_defaults(func=handle_export_csv)

    # export-md command
    parser_export_md = subparsers.add_parser('export-md', help='Export results to Markdown')
    parser_export_md.add_argument('output', help='Output Markdown file path')
    parser_export_md.add_argument('--model', help='Filter by model')
    parser_export_md.add_argument('--query-pattern', help='Filter by query pattern')
    parser_export_md.add_argument('--start-date', help='Start date (YYYY-MM-DD)')
    parser_export_md.add_argument('--end-date', help='End date (YYYY-MM-DD)')
    parser_export_md.add_argument('--success-only', action='store_true', help='Only successful results')
    parser_export_md.add_argument('--failed-only', action='store_true', help='Only failed results')
    parser_export_md.add_argument('--min-exec-time', type=float, help='Minimum execution time (seconds)')
    parser_export_md.add_argument('--max-exec-time', type=float, help='Maximum execution time (seconds)')
    parser_export_md.add_argument('--min-answer-length', type=int, help='Minimum answer length (chars)')
    parser_export_md.add_argument('--max-answer-length', type=int, help='Maximum answer length (chars)')
    parser_export_md.add_argument('--has-sources', action='store_true', help='Only results with sources')
    parser_export_md.add_argument('--limit', type=int, help='Limit number of results')
    parser_export_md.add_argument('--full', action='store_true', help='Include full answer text')
    parser_export_md.set_defaults(func=handle_export_md)

    # export-batch command
    parser_export_batch = subparsers.add_parser('export-batch', help='Batch export all results')
    parser_export_batch.add_argument('output_dir', help='Output directory path')
    parser_export_batch.add_argument('--format', default='json',
                                    choices=['json', 'csv', 'md'],
                                    help='Export format (default: json)')
    parser_export_batch.add_argument('--group-by', default='model',
                                    choices=['model', 'date'],
                                    help='Group results by (default: model)')
    parser_export_batch.set_defaults(func=handle_export_batch)

    # duplicates command
    parser_duplicates = subparsers.add_parser('duplicates', help='Find duplicate or similar queries')
    parser_duplicates.add_argument('--exact', action='store_true', help='Find exact duplicates only')
    parser_duplicates.set_defaults(func=handle_duplicates)

    # cleanup command
    parser_cleanup = subparsers.add_parser('cleanup', help='Database maintenance and cleanup')
    parser_cleanup.add_argument('--remove-duplicates', action='store_true', help='Remove duplicate records')
    parser_cleanup.add_argument('--archive-before', help='Archive failed records before date (YYYY-MM-DD)')
    parser_cleanup.add_argument('--dry-run', action='store_true', help='Preview changes without applying')
    parser_cleanup.add_argument('--confirm', action='store_true', help='Confirm actual cleanup (required if not --dry-run)')
    parser_cleanup.set_defaults(func=handle_cleanup)

    # info command
    parser_info = subparsers.add_parser('info', help='Show database health information')
    parser_info.set_defaults(func=handle_info)

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        return

    # Execute the command
    args.func(args)


if __name__ == '__main__':
    main()
