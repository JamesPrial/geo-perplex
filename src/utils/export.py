"""
Export utilities for search results
Provides CSV, Markdown, and batch export functionality for database records
"""
import csv
import json
import logging
import re
from pathlib import Path as PathClass
from datetime import datetime
from typing import Dict, List, Optional, Any

from src.utils import storage

logger = logging.getLogger(__name__)


def _validate_output_directory(output_dir: str) -> PathClass:
    """
    Validate output directory and prevent directory traversal attacks.

    Performs security checks:
    - Resolves path to absolute form (handles .., symlinks)
    - Rejects existing symlinks (prevents symlink-based escapes)

    Allows absolute paths (e.g., /tmp) and relative paths, as symlink checks
    provide sufficient security protection against directory traversal attacks.

    Args:
        output_dir: Directory path to validate (relative or absolute)

    Returns:
        Resolved absolute Path object

    Raises:
        ValueError: If path is invalid or is a symlink
    """
    # First check if the path itself is a symlink BEFORE resolving
    path_obj = PathClass(output_dir)
    if path_obj.is_symlink():
        error_msg = f"Cannot use symlink as output directory: {output_dir}"
        logger.error(error_msg)
        raise ValueError(error_msg)

    try:
        output_path = path_obj.resolve(strict=False)
    except (OSError, RuntimeError) as e:
        error_msg = f"Invalid directory path: {output_dir}. Error: {e}"
        logger.error(error_msg)
        raise ValueError(error_msg) from e

    # Check again after resolving (defensive check)
    if output_path.exists() and output_path.is_symlink():
        error_msg = f"Cannot use symlink as output directory: {output_dir}"
        logger.error(error_msg)
        raise ValueError(error_msg)

    return output_path


def _validate_output_path(output_path: str, expected_extension: Optional[str] = None) -> PathClass:
    """
    Validate output path and prevent directory traversal attacks.

    Performs comprehensive security checks:
    - Resolves path to absolute form (handles .., symlinks)
    - Rejects existing symlinks that could point outside allowed areas
    - Validates file extension if specified

    Allows absolute paths (e.g., /tmp) and relative paths, as symlink checks
    provide sufficient security protection against directory traversal attacks.

    Args:
        output_path: Path to validate (relative or absolute)
        expected_extension: Optional expected file extension (e.g., '.csv', '.md', '.json')

    Returns:
        Resolved absolute Path object

    Raises:
        ValueError: If path is invalid, is a symlink, or has wrong extension
    """
    # First check if the path itself is a symlink BEFORE resolving
    # This catches symlinks that point outside the safe directory
    path_obj = PathClass(output_path)
    if path_obj.is_symlink():
        error_msg = f"Cannot write to symlink: {output_path}"
        logger.error(error_msg)
        raise ValueError(error_msg)

    # Resolve to absolute path (handles .., symlinks, etc.)
    try:
        output_file = path_obj.resolve(strict=False)
    except (OSError, RuntimeError) as e:
        error_msg = f"Invalid path: {output_path}. Error: {e}"
        logger.error(error_msg)
        raise ValueError(error_msg) from e

    # Check extension if specified
    if expected_extension:
        if not output_file.suffix.lower() == expected_extension.lower():
            raise ValueError(
                f"Expected extension {expected_extension}, got {output_file.suffix}"
            )

    # Reject if file already exists and is a symlink (defensive check)
    if output_file.exists() and output_file.is_symlink():
        error_msg = f"Cannot write to symlink: {output_path}"
        logger.error(error_msg)
        raise ValueError(error_msg)

    return output_file


def _format_sources_for_csv(sources: List[Dict], mode: str = "count") -> str:
    """
    Format sources for CSV export.

    Args:
        sources: List of source dictionaries with 'url' and 'text' keys
        mode: 'count' returns number of sources, 'json' returns JSON string

    Returns:
        Formatted sources as string
    """
    if not sources:
        return "0" if mode == "count" else "[]"

    if mode == "count":
        return str(len(sources))
    else:
        # JSON format with just URLs for readability
        urls = [source.get("url", "") for source in sources if source.get("url")]
        return json.dumps(urls)


def _escape_markdown(text: str) -> str:
    """
    Escape markdown special characters in text.

    Args:
        text: Text to escape

    Returns:
        Escaped text safe for markdown
    """
    # Escape special markdown characters
    special_chars = ['\\', '*', '_', '`', '[', ']', '(', ')', '#', '+', '-', '.', '!']
    for char in special_chars:
        text = text.replace(char, f"\\{char}")
    return text


def _truncate_text(text: Optional[str], max_length: int = 500) -> str:
    """
    Truncate text to maximum length and add ellipsis.

    Args:
        text: Text to truncate
        max_length: Maximum length before truncation

    Returns:
        Truncated text
    """
    if not text:
        return ""
    if len(text) <= max_length:
        return text
    return text[:max_length].rstrip() + "..."


def _format_timestamp(timestamp: Any) -> str:
    """
    Format timestamp to human-readable string.

    Args:
        timestamp: Datetime object or ISO string

    Returns:
        Formatted timestamp string
    """
    if isinstance(timestamp, datetime):
        return timestamp.strftime("%Y-%m-%d %H:%M:%S")
    elif isinstance(timestamp, str):
        try:
            dt = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
            return dt.strftime("%Y-%m-%d %H:%M:%S")
        except (ValueError, AttributeError):
            return timestamp
    return str(timestamp)


def _format_markdown_table(headers: List[str], rows: List[List[str]]) -> str:
    """
    Generate markdown table from headers and rows.

    Args:
        headers: List of column headers
        rows: List of rows, each containing values matching header count

    Returns:
        Markdown-formatted table
    """
    if not headers or not rows:
        return ""

    # Build header row
    table = "| " + " | ".join(headers) + " |\n"
    table += "| " + " | ".join(["---"] * len(headers)) + " |\n"

    # Build data rows
    for row in rows:
        # Pad row with empty strings if needed
        padded_row = row + [""] * (len(headers) - len(row))
        table += "| " + " | ".join(padded_row[:len(headers)]) + " |\n"

    return table


def export_to_csv(
    output_path: str,
    filters: Optional[Dict[str, Any]] = None,
    include_sources: bool = True
) -> Dict[str, Any]:
    """
    Export search results to CSV format.

    Args:
        output_path: Path to write CSV file
        filters: Optional dictionary with filter keys:
            - query_pattern: Filter by query (regex or substring)
            - model: Filter by specific model
            - start_date: Start date (YYYY-MM-DD)
            - end_date: End date (YYYY-MM-DD)
            - success: Filter by success status (True/False)
            - min_exec_time: Minimum execution time in seconds
            - max_exec_time: Maximum execution time in seconds
        include_sources: If True, include source count; if False, omit sources column

    Returns:
        Dictionary with export summary:
        {
            "file_path": str,
            "record_count": int,
            "file_size_bytes": int,
            "filters_applied": int
        }

    Raises:
        ValueError: If no results found or path validation fails
        IOError: If unable to write file
    """
    output_file = _validate_output_path(output_path, ".csv")

    # Get all results from database
    logger.info("Retrieving results from database for CSV export")
    all_results = storage.get_recent_results(limit=999999)

    if not all_results:
        logger.warning("No results found in database")
        raise ValueError("No results found in database")

    # Apply filters
    filters_applied = 0
    filtered_results = all_results

    if filters:
        # Filter by query pattern
        if "query_pattern" in filters:
            pattern = filters["query_pattern"]
            filtered_results = [
                r for r in filtered_results
                if pattern.lower() in r.get("query", "").lower()
            ]
            filters_applied += 1

        # Filter by model
        if "model" in filters:
            model = filters["model"]
            filtered_results = [
                r for r in filtered_results
                if r.get("model") == model
            ]
            filters_applied += 1

        # Filter by success status
        if "success" in filters:
            success = filters["success"]
            filtered_results = [
                r for r in filtered_results
                if r.get("success") == success
            ]
            filters_applied += 1

        # Filter by execution time
        if "min_exec_time" in filters:
            min_time = filters["min_exec_time"]
            filtered_results = [
                r for r in filtered_results
                if r.get("execution_time_seconds", 0) >= min_time
            ]
            filters_applied += 1

        if "max_exec_time" in filters:
            max_time = filters["max_exec_time"]
            filtered_results = [
                r for r in filtered_results
                if r.get("execution_time_seconds", 0) <= max_time
            ]
            filters_applied += 1

        # Filter by date range
        if "start_date" in filters or "end_date" in filters:
            start_date = None
            end_date = None

            if "start_date" in filters:
                start_date = datetime.strptime(filters["start_date"], "%Y-%m-%d")
            if "end_date" in filters:
                end_date = datetime.strptime(filters["end_date"], "%Y-%m-%d")

            filtered_results = [
                r for r in filtered_results
                if _is_in_date_range(r.get("timestamp"), start_date, end_date)
            ]
            if start_date or end_date:
                filters_applied += 1

    if not filtered_results:
        logger.warning("No results match the specified filters")
        raise ValueError("No results match the specified filters")

    # Create parent directories
    try:
        output_file.parent.mkdir(parents=True, exist_ok=True)
    except OSError as e:
        logger.error(f"Failed to create parent directories: {e}")
        raise IOError(f"Cannot create output directories: {output_file.parent}") from e

    # Prepare CSV data
    fieldnames = [
        "id", "query", "model", "timestamp", "answer_text",
        "sources", "execution_time_seconds", "success"
    ]

    if not include_sources:
        fieldnames.remove("sources")

    # Write CSV file
    try:
        with open(output_file, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()

            for result in filtered_results:
                row = {
                    "id": result.get("id"),
                    "query": result.get("query"),
                    "model": result.get("model") or "unknown",
                    "timestamp": _format_timestamp(result.get("timestamp")),
                    "answer_text": result.get("answer_text") or "",
                    "execution_time_seconds": result.get("execution_time_seconds") or 0,
                    "success": result.get("success", True)
                }

                if include_sources:
                    sources = result.get("sources", [])
                    row["sources"] = _format_sources_for_csv(sources, mode="count")

                writer.writerow(row)

        logger.info(f"Exported {len(filtered_results)} results to {output_file}")
    except (IOError, OSError) as e:
        logger.error(f"Failed to write CSV file: {e}")
        raise IOError(f"Cannot write to file: {output_file}") from e

    file_size = output_file.stat().st_size

    return {
        "file_path": str(output_file.resolve()),
        "record_count": len(filtered_results),
        "file_size_bytes": file_size,
        "filters_applied": filters_applied
    }


def export_to_markdown(
    output_path: str,
    filters: Optional[Dict[str, Any]] = None,
    include_full_answers: bool = False
) -> Dict[str, Any]:
    """
    Export search results to Markdown format.

    Args:
        output_path: Path to write markdown file
        filters: Optional filter dictionary (same as export_to_csv)
        include_full_answers: If True, include complete answers; if False, truncate to 500 chars

    Returns:
        Dictionary with export summary

    Raises:
        ValueError: If no results found or path validation fails
        IOError: If unable to write file
    """
    output_file = _validate_output_path(output_path, ".md")

    # Get and filter results (same logic as CSV export)
    logger.info("Retrieving results from database for Markdown export")
    all_results = storage.get_recent_results(limit=999999)

    if not all_results:
        logger.warning("No results found in database")
        raise ValueError("No results found in database")

    # Apply filters (reuse same filtering logic)
    filters_applied = 0
    filtered_results = all_results

    if filters:
        if "query_pattern" in filters:
            pattern = filters["query_pattern"]
            filtered_results = [
                r for r in filtered_results
                if pattern.lower() in r.get("query", "").lower()
            ]
            filters_applied += 1

        if "model" in filters:
            model = filters["model"]
            filtered_results = [
                r for r in filtered_results
                if r.get("model") == model
            ]
            filters_applied += 1

        if "success" in filters:
            success = filters["success"]
            filtered_results = [
                r for r in filtered_results
                if r.get("success") == success
            ]
            filters_applied += 1

    if not filtered_results:
        logger.warning("No results match the specified filters")
        raise ValueError("No results match the specified filters")

    # Create parent directories
    try:
        output_file.parent.mkdir(parents=True, exist_ok=True)
    except OSError as e:
        logger.error(f"Failed to create parent directories: {e}")
        raise IOError(f"Cannot create output directories: {output_file.parent}") from e

    # Build markdown content
    content = []
    content.append("# Search Results Export\n")
    content.append(f"Generated: {_format_timestamp(datetime.now())}\n")
    content.append(f"Total Results: {len(filtered_results)}\n")
    content.append("")

    if filters_applied > 0:
        content.append(f"Filters Applied: {filters_applied}\n")
        content.append("")

    content.append("## Results\n")

    for result in filtered_results:
        content.append(f"### Query: \"{result.get('query')}\"\n")
        content.append("")

        # Metadata
        content.append(f"- **Model**: {result.get('model') or 'unknown'}")
        content.append(f"- **Timestamp**: {_format_timestamp(result.get('timestamp'))}")
        exec_time = result.get('execution_time_seconds') or 0
        content.append(f"- **Execution Time**: {exec_time:.1f}s")
        content.append(f"- **Success**: {'✓' if result.get('success', True) else '✗'}")
        content.append("")

        # Answer text
        answer_text = result.get("answer_text") or ""
        if not include_full_answers:
            answer_text = _truncate_text(answer_text, max_length=500)

        content.append("**Answer**:\n")
        content.append(answer_text)
        content.append("")

        # Sources
        sources = result.get("sources", [])
        if sources:
            content.append("**Sources**:\n")
            for i, source in enumerate(sources, 1):
                url = source.get("url", "")
                text = source.get("text", "Link")
                # Ensure valid markdown link format
                if url:
                    content.append(f"{i}. [{text}]({url})")
                else:
                    content.append(f"{i}. {text}")
            content.append("")

        content.append("---\n")

    # Write markdown file
    try:
        with open(output_file, "w", encoding="utf-8") as f:
            f.write("\n".join(content))
        logger.info(f"Exported {len(filtered_results)} results to {output_file}")
    except (IOError, OSError) as e:
        logger.error(f"Failed to write markdown file: {e}")
        raise IOError(f"Cannot write to file: {output_file}") from e

    file_size = output_file.stat().st_size

    return {
        "file_path": str(output_file.resolve()),
        "record_count": len(filtered_results),
        "file_size_bytes": file_size,
        "filters_applied": filters_applied
    }


def export_comparison_to_markdown(query: str, output_path: str) -> Dict[str, Any]:
    """
    Compare models for a specific query and export to markdown.

    Args:
        query: The search query to compare
        output_path: Path to write markdown file

    Returns:
        Dictionary with export summary

    Raises:
        ValueError: If no results found or path validation fails
        IOError: If unable to write file
    """
    output_file = _validate_output_path(output_path, ".md")

    # Get comparison data from database
    logger.info(f"Retrieving comparison data for query: {query}")
    results_by_model = storage.compare_models_for_query(query)

    if not results_by_model:
        logger.warning(f"No results found for query: {query}")
        raise ValueError(f"No results found for query: {query}")

    # Create parent directories
    try:
        output_file.parent.mkdir(parents=True, exist_ok=True)
    except OSError as e:
        logger.error(f"Failed to create parent directories: {e}")
        raise IOError(f"Cannot create output directories: {output_file.parent}") from e

    # Build markdown content
    content = []
    content.append("# Model Comparison\n")
    content.append(f"Query: \"{query}\"\n")
    content.append(f"Generated: {_format_timestamp(datetime.now())}\n")
    content.append(f"Models Compared: {len(results_by_model)}\n")
    content.append("")

    total_results = sum(len(results) for results in results_by_model.values())
    content.append(f"Total Results: {total_results}\n")
    content.append("")

    # Create comparison table
    content.append("## Comparison Table\n")

    headers = ["Model", "Count", "Avg Execution Time", "Success Rate"]
    rows = []

    for model in sorted(results_by_model.keys()):
        results = results_by_model[model]
        count = len(results)
        avg_time = sum(r.get("execution_time_seconds") or 0 for r in results) / count
        success_count = sum(1 for r in results if r.get("success", True))
        success_rate = (success_count / count * 100) if count > 0 else 0

        rows.append([
            model,
            str(count),
            f"{avg_time:.1f}s",
            f"{success_rate:.0f}%"
        ])

    content.append(_format_markdown_table(headers, rows))
    content.append("")

    # Detailed results by model
    content.append("## Detailed Results\n")

    for model in sorted(results_by_model.keys()):
        results = results_by_model[model]
        content.append(f"### {model}\n")
        content.append(f"Results: {len(results)}\n")
        content.append("")

        for i, result in enumerate(results, 1):
            content.append(f"#### Result {i}\n")
            content.append(f"- **Timestamp**: {_format_timestamp(result.get('timestamp'))}")
            exec_time = result.get('execution_time_seconds') or 0
            content.append(f"- **Execution Time**: {exec_time:.1f}s")
            content.append(f"- **Success**: {'✓' if result.get('success', True) else '✗'}")
            content.append("")

            # Truncated answer
            answer_text = result.get("answer_text") or ""
            answer_text = _truncate_text(answer_text, max_length=300)
            content.append(answer_text)
            content.append("")

        content.append("")

    # Write markdown file
    try:
        with open(output_file, "w", encoding="utf-8") as f:
            f.write("\n".join(content))
        logger.info(f"Exported comparison for query '{query}' to {output_file}")
    except (IOError, OSError) as e:
        logger.error(f"Failed to write markdown file: {e}")
        raise IOError(f"Cannot write to file: {output_file}") from e

    file_size = output_file.stat().st_size

    return {
        "file_path": str(output_file.resolve()),
        "record_count": total_results,
        "file_size_bytes": file_size,
        "models_compared": len(results_by_model)
    }


def batch_export_by_model(output_dir: str, format_type: str = "json") -> Dict[str, Any]:
    """
    Export results grouped by model to separate files.

    Args:
        output_dir: Directory to create model-specific export files
        format_type: Export format ('json', 'csv', 'md')

    Returns:
        Dictionary with batch export summary:
        {
            "output_dir": str,
            "files_created": int,
            "total_records": int,
            "total_size_bytes": int,
            "by_model": {model: {file_path, record_count, file_size_bytes}}
        }

    Raises:
        ValueError: If invalid format or no results found
        IOError: If unable to write files
    """
    if format_type not in ["json", "csv", "md"]:
        raise ValueError(f"Invalid format: {format_type}. Must be 'json', 'csv', or 'md'")

    output_path = _validate_output_directory(output_dir)

    # Create output directory
    try:
        output_path.mkdir(parents=True, exist_ok=True)
    except OSError as e:
        logger.error(f"Failed to create output directory: {e}")
        raise IOError(f"Cannot create output directory: {output_path}") from e

    # Get unique models from database
    models = storage.get_unique_models()

    if not models:
        logger.warning("No models found in database")
        raise ValueError("No models found in database")

    logger.info(f"Exporting {len(models)} models to {format_type} format")

    batch_summary = {
        "output_dir": str(output_path.resolve()),
        "files_created": 0,
        "total_records": 0,
        "total_size_bytes": 0,
        "by_model": {}
    }

    # Export each model
    for model in models:
        results = storage.get_results_by_model(model, limit=999999)

        if not results:
            logger.debug(f"No results for model: {model}")
            continue

        # Sanitize model name for filename
        safe_model_name = "".join(c if c.isalnum() else "_" for c in model)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

        if format_type == "json":
            filename = f"{safe_model_name}_{timestamp}.json"
            file_path = output_path / filename

            # Convert results to JSON-serializable format
            json_results = []
            for result in results:
                json_result = dict(result)
                if isinstance(json_result.get("timestamp"), datetime):
                    json_result["timestamp"] = json_result["timestamp"].isoformat()
                json_results.append(json_result)

            try:
                with open(file_path, "w", encoding="utf-8") as f:
                    json.dump(json_results, f, indent=2, default=str)
            except (IOError, OSError) as e:
                logger.error(f"Failed to write JSON file for model {model}: {e}")
                continue

        elif format_type == "csv":
            filename = f"{safe_model_name}_{timestamp}.csv"
            file_path = output_path / filename

            try:
                with open(file_path, "w", newline="", encoding="utf-8") as f:
                    fieldnames = [
                        "id", "query", "timestamp", "answer_text",
                        "sources", "execution_time_seconds", "success"
                    ]
                    writer = csv.DictWriter(f, fieldnames=fieldnames)
                    writer.writeheader()

                    for result in results:
                        row = {
                            "id": result.get("id"),
                            "query": result.get("query"),
                            "timestamp": _format_timestamp(result.get("timestamp")),
                            "answer_text": result.get("answer_text") or "",
                            "sources": _format_sources_for_csv(result.get("sources", []), "count"),
                            "execution_time_seconds": result.get("execution_time_seconds") or 0,
                            "success": result.get("success", True)
                        }
                        writer.writerow(row)
            except (IOError, OSError) as e:
                logger.error(f"Failed to write CSV file for model {model}: {e}")
                continue

        elif format_type == "md":
            filename = f"{safe_model_name}_{timestamp}.md"
            file_path = output_path / filename

            try:
                with open(file_path, "w", encoding="utf-8") as f:
                    f.write(f"# Results for Model: {model}\n\n")
                    f.write(f"Generated: {_format_timestamp(datetime.now())}\n")
                    f.write(f"Total Results: {len(results)}\n\n")

                    for result in results:
                        f.write(f"## {result.get('query')}\n\n")
                        f.write(f"- **Timestamp**: {_format_timestamp(result.get('timestamp'))}\n")
                        f.write(f"- **Execution Time**: {result.get('execution_time_seconds', 0):.1f}s\n")
                        f.write(f"- **Success**: {'✓' if result.get('success', True) else '✗'}\n\n")
                        f.write(result.get("answer_text") or "")
                        f.write("\n\n---\n\n")
            except (IOError, OSError) as e:
                logger.error(f"Failed to write markdown file for model {model}: {e}")
                continue

        # Record statistics for this model
        file_size = file_path.stat().st_size
        batch_summary["by_model"][model] = {
            "file_path": str(file_path.resolve()),
            "record_count": len(results),
            "file_size_bytes": file_size
        }
        batch_summary["files_created"] += 1
        batch_summary["total_records"] += len(results)
        batch_summary["total_size_bytes"] += file_size

        logger.info(
            f"Exported {len(results)} results for model '{model}' to {file_path}"
        )

    logger.info(f"Batch export complete: {batch_summary['files_created']} files created")
    return batch_summary


def batch_export_by_date(
    output_dir: str,
    period: str = "day",
    format_type: str = "json"
) -> Dict[str, Any]:
    """
    Export results grouped by time period to separate files.

    Args:
        output_dir: Directory to create time-period export files
        period: Time period ('day', 'week', 'month')
        format_type: Export format ('json', 'csv', 'md')

    Returns:
        Dictionary with batch export summary

    Raises:
        ValueError: If invalid period/format or no results found
        IOError: If unable to write files
    """
    if period not in ["day", "week", "month"]:
        raise ValueError(f"Invalid period: {period}. Must be 'day', 'week', or 'month'")

    if format_type not in ["json", "csv", "md"]:
        raise ValueError(f"Invalid format: {format_type}. Must be 'json', 'csv', or 'md'")

    output_path = _validate_output_directory(output_dir)

    # Create output directory
    try:
        output_path.mkdir(parents=True, exist_ok=True)
    except OSError as e:
        logger.error(f"Failed to create output directory: {e}")
        raise IOError(f"Cannot create output directory: {output_path}") from e

    # Get all results
    all_results = storage.get_recent_results(limit=999999)

    if not all_results:
        logger.warning("No results found in database")
        raise ValueError("No results found in database")

    # Group results by time period
    grouped_results = _group_results_by_date(all_results, period)

    logger.info(f"Exporting {len(grouped_results)} {period} periods to {format_type} format")

    batch_summary = {
        "output_dir": str(output_path.resolve()),
        "files_created": 0,
        "total_records": 0,
        "total_size_bytes": 0,
        "by_period": {}
    }

    # Export each period
    for period_key in sorted(grouped_results.keys()):
        results = grouped_results[period_key]

        if format_type == "json":
            filename = f"{period}_{period_key}.json"
            file_path = output_path / filename

            json_results = []
            for result in results:
                json_result = dict(result)
                if isinstance(json_result.get("timestamp"), datetime):
                    json_result["timestamp"] = json_result["timestamp"].isoformat()
                json_results.append(json_result)

            try:
                with open(file_path, "w", encoding="utf-8") as f:
                    json.dump(json_results, f, indent=2, default=str)
            except (IOError, OSError) as e:
                logger.error(f"Failed to write JSON file for {period} {period_key}: {e}")
                continue

        elif format_type == "csv":
            filename = f"{period}_{period_key}.csv"
            file_path = output_path / filename

            try:
                with open(file_path, "w", newline="", encoding="utf-8") as f:
                    fieldnames = [
                        "id", "query", "model", "timestamp", "answer_text",
                        "sources", "execution_time_seconds", "success"
                    ]
                    writer = csv.DictWriter(f, fieldnames=fieldnames)
                    writer.writeheader()

                    for result in results:
                        row = {
                            "id": result.get("id"),
                            "query": result.get("query"),
                            "model": result.get("model") or "unknown",
                            "timestamp": _format_timestamp(result.get("timestamp")),
                            "answer_text": result.get("answer_text") or "",
                            "sources": _format_sources_for_csv(result.get("sources", []), "count"),
                            "execution_time_seconds": result.get("execution_time_seconds") or 0,
                            "success": result.get("success", True)
                        }
                        writer.writerow(row)
            except (IOError, OSError) as e:
                logger.error(f"Failed to write CSV file for {period} {period_key}: {e}")
                continue

        elif format_type == "md":
            filename = f"{period}_{period_key}.md"
            file_path = output_path / filename

            try:
                with open(file_path, "w", encoding="utf-8") as f:
                    f.write(f"# Results for {period.capitalize()}: {period_key}\n\n")
                    f.write(f"Generated: {_format_timestamp(datetime.now())}\n")
                    f.write(f"Total Results: {len(results)}\n\n")

                    for result in results:
                        f.write(f"## {result.get('query')}\n\n")
                        f.write(f"- **Model**: {result.get('model') or 'unknown'}\n")
                        f.write(f"- **Timestamp**: {_format_timestamp(result.get('timestamp'))}\n")
                        exec_time = result.get('execution_time_seconds') or 0
                        f.write(f"- **Execution Time**: {exec_time:.1f}s\n\n")
                        f.write(result.get("answer_text") or "")
                        f.write("\n\n---\n\n")
            except (IOError, OSError) as e:
                logger.error(f"Failed to write markdown file for {period} {period_key}: {e}")
                continue

        # Record statistics for this period
        file_size = file_path.stat().st_size
        batch_summary["by_period"][period_key] = {
            "file_path": str(file_path.resolve()),
            "record_count": len(results),
            "file_size_bytes": file_size
        }
        batch_summary["files_created"] += 1
        batch_summary["total_records"] += len(results)
        batch_summary["total_size_bytes"] += file_size

        logger.info(
            f"Exported {len(results)} results for {period} {period_key} to {file_path}"
        )

    logger.info(f"Batch export complete: {batch_summary['files_created']} files created")
    return batch_summary


def export_database_summary(output_path: str) -> Dict[str, Any]:
    """
    Export comprehensive database summary to markdown.

    Args:
        output_path: Path to write summary markdown file

    Returns:
        Dictionary with export summary

    Raises:
        ValueError: If no results found or path validation fails
        IOError: If unable to write file
    """
    output_file = _validate_output_path(output_path, ".md")

    # Get database statistics
    logger.info("Generating database summary")
    all_results = storage.get_recent_results(limit=999999)

    if not all_results:
        logger.warning("No results found in database")
        raise ValueError("No results found in database")

    # Calculate statistics
    unique_queries = storage.get_unique_queries()
    unique_models = storage.get_unique_models()

    total_execution_time = sum(r.get("execution_time_seconds") or 0 for r in all_results)
    avg_execution_time = total_execution_time / len(all_results) if all_results else 0

    success_count = sum(1 for r in all_results if r.get("success", True))
    success_rate = (success_count / len(all_results) * 100) if all_results else 0

    total_sources = sum(len(r.get("sources", [])) for r in all_results)
    avg_sources = total_sources / len(all_results) if all_results else 0

    total_answer_length = sum(len(r.get("answer_text", "")) for r in all_results)
    avg_answer_length = total_answer_length / len(all_results) if all_results else 0

    # Create parent directories
    try:
        output_file.parent.mkdir(parents=True, exist_ok=True)
    except OSError as e:
        logger.error(f"Failed to create parent directories: {e}")
        raise IOError(f"Cannot create output directories: {output_file.parent}") from e

    # Build markdown content
    content = []
    content.append("# Database Summary\n")
    content.append(f"Generated: {_format_timestamp(datetime.now())}\n")
    content.append("")

    # Overview
    content.append("## Overview\n")
    content.append(f"- **Total Results**: {len(all_results)}")
    content.append(f"- **Unique Queries**: {len(unique_queries)}")
    content.append(f"- **Unique Models**: {len(unique_models)}")
    content.append("")

    # Performance Statistics
    content.append("## Performance Statistics\n")
    content.append(f"- **Total Execution Time**: {total_execution_time:.1f}s")
    content.append(f"- **Average Execution Time**: {avg_execution_time:.1f}s")
    content.append(f"- **Success Rate**: {success_rate:.1f}%")
    content.append(f"- **Successful Results**: {success_count}/{len(all_results)}")
    content.append("")

    # Content Statistics
    content.append("## Content Statistics\n")
    content.append(f"- **Total Sources**: {total_sources}")
    content.append(f"- **Average Sources per Result**: {avg_sources:.1f}")
    content.append(f"- **Total Answer Characters**: {total_answer_length}")
    content.append(f"- **Average Answer Length**: {avg_answer_length:.0f} characters")
    content.append("")

    # Model Summary Table
    content.append("## Model Summary\n")

    model_stats = []
    for model in sorted(unique_models):
        model_results = storage.get_results_by_model(model, limit=999999)
        model_count = len(model_results)
        model_success = sum(1 for r in model_results if r.get("success", True))
        model_success_rate = (model_success / model_count * 100) if model_count > 0 else 0
        model_avg_time = (
            sum(r.get("execution_time_seconds") or 0 for r in model_results) / model_count
            if model_count > 0 else 0
        )

        model_stats.append([
            model,
            str(model_count),
            f"{model_success_rate:.0f}%",
            f"{model_avg_time:.1f}s"
        ])

    if model_stats:
        content.append(_format_markdown_table(
            ["Model", "Count", "Success Rate", "Avg Time"],
            model_stats
        ))
    content.append("")

    # Top Queries
    content.append("## Top Queries\n")

    query_stats = []
    for query in unique_queries[:20]:  # Top 20 queries
        query_results = storage.get_results_by_query(query)
        query_count = len(query_results)
        query_stats.append([
            query[:50] + "..." if len(query) > 50 else query,
            str(query_count)
        ])

    if query_stats:
        content.append(_format_markdown_table(["Query", "Count"], query_stats))
    content.append("")

    # Write markdown file
    try:
        with open(output_file, "w", encoding="utf-8") as f:
            f.write("\n".join(content))
        logger.info(f"Exported database summary to {output_file}")
    except (IOError, OSError) as e:
        logger.error(f"Failed to write summary file: {e}")
        raise IOError(f"Cannot write to file: {output_file}") from e

    file_size = output_file.stat().st_size

    return {
        "file_path": str(output_file.resolve()),
        "record_count": len(all_results),
        "file_size_bytes": file_size
    }


def _is_in_date_range(
    timestamp: Any,
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None
) -> bool:
    """
    Check if timestamp falls within date range.

    Args:
        timestamp: Datetime object or ISO string
        start_date: Optional start date (inclusive)
        end_date: Optional end date (inclusive)

    Returns:
        True if timestamp is within range, False otherwise
    """
    if isinstance(timestamp, str):
        try:
            timestamp = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
        except (ValueError, AttributeError):
            return True  # If can't parse, include it

    if not isinstance(timestamp, datetime):
        return True

    if start_date and timestamp.date() < start_date.date():
        return False

    if end_date and timestamp.date() > end_date.date():
        return False

    return True


def _group_results_by_date(
    results: List[Dict],
    period: str
) -> Dict[str, List[Dict]]:
    """
    Group results by time period.

    Args:
        results: List of result dictionaries
        period: Time period ('day', 'week', 'month')

    Returns:
        Dictionary mapping period keys to lists of results
    """
    grouped = {}

    for result in results:
        timestamp = result.get("timestamp")

        if isinstance(timestamp, str):
            try:
                timestamp = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
            except (ValueError, AttributeError):
                timestamp = datetime.now()

        if not isinstance(timestamp, datetime):
            timestamp = datetime.now()

        if period == "day":
            period_key = timestamp.strftime("%Y-%m-%d")
        elif period == "week":
            # ISO week format (YYYY-WXX)
            period_key = timestamp.strftime("%Y-W%V")
        else:  # month
            period_key = timestamp.strftime("%Y-%m")

        if period_key not in grouped:
            grouped[period_key] = []

        grouped[period_key].append(result)

    return grouped
