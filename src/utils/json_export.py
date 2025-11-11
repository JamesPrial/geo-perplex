"""
JSON export utilities for search results
Manages exporting database records to JSON files
"""
import json
import logging
from hashlib import md5
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional

from src.utils import storage

logger = logging.getLogger(__name__)


def generate_filename(query: str, timestamp: str, model: Optional[str] = None) -> str:
    """
    Generate a unique filename for individual result exports.

    Args:
        query: The search query
        timestamp: ISO timestamp without special chars (e.g., "20250111_143000")
        model: Optional model name

    Returns:
        Filename in format: result_{timestamp}_{query_hash}_{model}.json
    """
    # Generate 8-char MD5 hash of query for uniqueness
    query_hash = md5(query.encode()).hexdigest()[:8]

    # Sanitize model name (replace special chars with underscore)
    if model:
        sanitized_model = "".join(c if c.isalnum() else "_" for c in model)
        filename = f"result_{timestamp}_{query_hash}_{sanitized_model}.json"
    else:
        filename = f"result_{timestamp}_{query_hash}.json"

    return filename.lower()


def save_result_to_json(
    result_dict: Dict,
    output_dir: str = "exports"
) -> str:
    """
    Save a single search result to a JSON file.

    Args:
        result_dict: Dictionary containing search result (must have id, query, timestamp fields)
        output_dir: Directory to save the file in (created if doesn't exist)

    Returns:
        Full path to the created JSON file

    Raises:
        ValueError: If result_dict missing required fields
        IOError: If unable to write file
    """
    # Validate required fields
    required_fields = {"id", "query", "timestamp"}
    if not required_fields.issubset(result_dict.keys()):
        raise ValueError(
            f"result_dict missing required fields: {required_fields - set(result_dict.keys())}"
        )

    # Create output directory
    output_path = Path(output_dir)
    try:
        output_path.mkdir(parents=True, exist_ok=True)
    except OSError as e:
        logger.error(f"Failed to create output directory {output_dir}: {e}")
        raise IOError(f"Cannot create output directory: {output_dir}") from e

    # Generate filename from timestamp and query
    # Convert datetime string to filename format if needed
    timestamp_str = result_dict["timestamp"]
    if isinstance(timestamp_str, datetime):
        timestamp_str = timestamp_str.strftime("%Y%m%d_%H%M%S")
    elif isinstance(timestamp_str, str):
        # Try to parse as ISO format timestamp for consistency
        try:
            # Handle ISO format timestamps (e.g., "2025-01-11T14:30:00" or "2025-01-11T14:30:00Z")
            dt = datetime.fromisoformat(timestamp_str.replace('Z', '').replace(' ', 'T' if 'T' not in timestamp_str else ' '))
            timestamp_str = dt.strftime("%Y%m%d_%H%M%S")
        except (ValueError, AttributeError):
            # Fallback to string cleaning for non-ISO formats
            timestamp_str = (timestamp_str
                            .replace("-", "")
                            .replace(":", "")
                            .replace(" ", "_")
                            .replace("T", "_")
                            .replace(".", "")
                            .replace("Z", "")[:15])

    filename = generate_filename(
        result_dict["query"],
        timestamp_str,
        result_dict.get("model")
    )

    file_path = output_path / filename

    # Write JSON file
    try:
        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(result_dict, f, indent=2, default=str)
        logger.info(f"Saved result to {file_path}")
        return str(file_path)
    except (IOError, OSError) as e:
        logger.error(f"Failed to write JSON file {file_path}: {e}")
        raise IOError(f"Cannot write to file: {file_path}") from e


def export_database_to_json(
    output_path: str,
    query_filter: Optional[str] = None,
    model_filter: Optional[str] = None,
    limit: Optional[int] = None
) -> Dict:
    """
    Export database records to a JSON file.

    Applies filters in this priority:
    1. If query_filter provided: get results for that query (optionally filtered by model)
    2. If only model_filter: get results for that model (with limit)
    3. If no filters: get recent results (with limit or 999999)

    Args:
        output_path: Path to write JSON export file
        query_filter: Filter by specific query text
        model_filter: Filter by specific model name
        limit: Maximum number of results to export

    Returns:
        Dictionary with export summary:
        {
            "records_exported": int,
            "file_size_bytes": int,
            "output_path": str
        }

    Raises:
        IOError: If unable to write file or create directories
        ValueError: If no results found matching filters or path is outside current directory
    """
    # Validate output path to prevent directory traversal attacks
    output_file = Path(output_path).resolve()
    cwd = Path.cwd().resolve()

    try:
        output_file.relative_to(cwd)
    except ValueError:
        error_msg = (
            f"Output path must be within current directory. "
            f"Attempted: {output_path}, CWD: {cwd}"
        )
        logger.error(error_msg)
        raise ValueError(error_msg)

    # Query database based on filters
    if query_filter:
        logger.info(f"Exporting results for query: {query_filter}")
        results = storage.get_results_by_query(query_filter, model_filter)
    elif model_filter:
        logger.info(f"Exporting results for model: {model_filter}")
        results = storage.get_results_by_model(model_filter, limit or 50)
    else:
        logger.info(f"Exporting recent results (limit: {limit or 999999})")
        results = storage.get_recent_results(limit or 999999)

    if not results:
        logger.warning("No results found matching filters")
        raise ValueError("No results found matching the specified filters")

    # Create parent directories if needed
    output_file = Path(output_path)
    try:
        output_file.parent.mkdir(parents=True, exist_ok=True)
    except OSError as e:
        logger.error(f"Failed to create parent directories for {output_path}: {e}")
        raise IOError(f"Cannot create output directories: {output_file.parent}") from e

    # Convert results to JSON-serializable format
    # Ensure timestamp and sources are properly formatted
    json_results = []
    for result in results:
        json_result = dict(result)
        # Convert datetime objects to ISO format strings
        if isinstance(json_result.get("timestamp"), datetime):
            json_result["timestamp"] = json_result["timestamp"].isoformat()

        # Defensive JSON parsing for sources (storage.py should return parsed list)
        # Handle legacy/corrupted data gracefully
        if isinstance(json_result.get("sources"), str):
            logger.warning(
                f"Unexpected string-type sources for result ID {json_result.get('id')} "
                f"(storage.py should return parsed list)"
            )
            try:
                json_result["sources"] = json.loads(json_result["sources"])
            except json.JSONDecodeError:
                logger.error(f"Failed to parse sources JSON for result {json_result.get('id')}")
                json_result["sources"] = []  # Fallback to empty list

        json_results.append(json_result)

    # Write JSON file
    try:
        with open(output_file, "w", encoding="utf-8") as f:
            json.dump(json_results, f, indent=2, default=str)
        logger.info(f"Exported {len(json_results)} results to {output_path}")
    except (IOError, OSError) as e:
        logger.error(f"Failed to write export file {output_path}: {e}")
        raise IOError(f"Cannot write to file: {output_path}") from e

    # Get file size
    file_size = output_file.stat().st_size

    summary = {
        "records_exported": len(json_results),
        "file_size_bytes": file_size,
        "output_path": str(output_file.resolve())
    }

    logger.info(f"Export summary: {summary}")
    return summary
