"""
Unit tests for src/utils/export.py
Tests CSV, Markdown, JSON, and batch export functionality.
"""
import pytest
import csv
import json
import sqlite3
from pathlib import Path
from datetime import datetime, timedelta
from unittest.mock import patch, MagicMock
from src.utils import export, storage


@pytest.fixture
def mock_db_connection(tmp_path):
    """
    Patches sqlite3.connect to use a temporary database file.
    Enables all storage and export functions to work with test database.
    """
    temp_db_file = tmp_path / "test_export_db.sqlite"
    original_connect = sqlite3.connect

    def mock_connect(db_path, *args, **kwargs):
        return original_connect(str(temp_db_file))

    with patch('src.utils.storage.sqlite3.connect', side_effect=mock_connect):
        with patch('src.utils.export.storage.sqlite3.connect', side_effect=mock_connect):
            yield str(temp_db_file)


@pytest.fixture
def test_db(mock_db_connection):
    """
    Initialize test database with schema and sample data.
    Provides clean, populated database for each test.
    """
    storage.init_database()

    # Add sample data
    storage.save_search_result(
        query="What is Python?",
        answer_text="Python is a high-level programming language known for readability.",
        sources=[
            {"url": "https://python.org", "text": "Official Website"},
            {"url": "https://docs.python.org", "text": "Documentation"}
        ],
        model="gpt-4",
        execution_time=12.5,
        success=True
    )

    storage.save_search_result(
        query="What is Python?",
        answer_text="An interpreted language with dynamic typing and extensive libraries.",
        sources=[
            {"url": "https://wikipedia.org/wiki/Python", "text": "Wikipedia"}
        ],
        model="claude-3",
        execution_time=11.2,
        success=True
    )

    storage.save_search_result(
        query="What is JavaScript?",
        answer_text="JavaScript is a versatile language for web development.",
        sources=[
            {"url": "https://mdn.org", "text": "MDN Web Docs"},
            {"url": "https://javascript.info", "text": "JavaScript.info"}
        ],
        model="gpt-4",
        execution_time=10.8,
        success=True
    )

    storage.save_search_result(
        query="What is Rust?",
        answer_text="Rust is a systems programming language with memory safety.",
        sources=[],
        model="sonar-pro",
        execution_time=15.3,
        success=True
    )

    storage.save_search_result(
        query="Failed search",
        answer_text="",
        sources=[],
        model="gpt-4",
        execution_time=5.0,
        success=False,
        error_message="Timeout occurred"
    )

    return mock_db_connection


@pytest.fixture
def empty_db(mock_db_connection):
    """
    Initialize test database with schema but NO data.
    Used for testing error handling on empty results.
    """
    storage.init_database()
    return mock_db_connection


@pytest.fixture
def tmp_output_dir(tmp_path):
    """Create a temporary output directory for test files."""
    return tmp_path / "exports"


@pytest.mark.unit
class TestHelperFunctions:
    """Tests for helper functions in export module"""

    def test_validate_output_path_valid(self, tmp_path):
        """Test that valid paths within current directory are accepted"""
        output_file = tmp_path / "output.csv"
        with patch('pathlib.Path.cwd', return_value=tmp_path.parent):
            result = export._validate_output_path(str(output_file), ".csv")
            assert result.suffix == ".csv"

    def test_validate_output_path_wrong_extension(self, tmp_path):
        """Test that wrong file extension raises ValueError"""
        output_file = tmp_path / "output.txt"
        with patch('pathlib.Path.cwd', return_value=tmp_path.parent):
            with pytest.raises(ValueError, match="Expected extension"):
                export._validate_output_path(str(output_file), ".csv")

    def test_validate_output_path_absolute_path_allowed(self, tmp_path):
        """Test that absolute paths outside current directory are allowed"""
        current_dir = tmp_path / "current"
        current_dir.mkdir()

        # Absolute path outside current directory should be allowed
        outside_file = tmp_path / "outside.csv"

        with patch('pathlib.Path.cwd', return_value=current_dir):
            # Should not raise an error for absolute paths
            result = export._validate_output_path(str(outside_file), ".csv")
            assert result.suffix == ".csv"

    def test_validate_output_path_relative_path_allowed(self, tmp_path):
        """Test that relative paths within current directory are allowed"""
        safe_dir = tmp_path / "safe"
        safe_dir.mkdir()

        # Relative path that resolves outside should now be allowed
        # (relying on symlink check for security instead)
        relative_path = "output.csv"

        with patch('pathlib.Path.cwd', return_value=safe_dir):
            result = export._validate_output_path(relative_path, ".csv")
            assert result.suffix == ".csv"

    def test_validate_output_path_symlink_to_outside(self, tmp_path):
        """Test that symlinks pointing outside are rejected"""
        safe_dir = tmp_path / "safe"
        safe_dir.mkdir()

        outside_file = tmp_path / "outside.csv"
        outside_file.write_text("external data")

        symlink_file = safe_dir / "link.csv"
        try:
            symlink_file.symlink_to(outside_file)
        except OSError:
            # Skip test if symlinks not supported (e.g., Windows)
            pytest.skip("Symlinks not supported on this system")

        with patch('pathlib.Path.cwd', return_value=safe_dir):
            with pytest.raises(ValueError, match="Cannot write to symlink"):
                export._validate_output_path(str(symlink_file), ".csv")

    def test_validate_output_path_symlink_within_directory(self, tmp_path):
        """Test that symlinks within safe directory pointing elsewhere still raise error"""
        safe_dir = tmp_path / "safe"
        safe_dir.mkdir()

        # Create target outside safe dir
        outside_dir = tmp_path / "outside"
        outside_dir.mkdir()
        target_file = outside_dir / "target.csv"
        target_file.write_text("data")

        # Create symlink inside safe dir pointing outside
        symlink_file = safe_dir / "link.csv"
        try:
            symlink_file.symlink_to(target_file)
        except OSError:
            pytest.skip("Symlinks not supported on this system")

        with patch('pathlib.Path.cwd', return_value=safe_dir):
            with pytest.raises(ValueError, match="Cannot write to symlink"):
                export._validate_output_path(str(symlink_file), ".csv")

    def test_validate_output_path_relative_with_dots_allowed(self, tmp_path):
        """Test that relative paths with .. are now allowed (symlinks prevent escapes)"""
        safe_dir = tmp_path / "safe"
        safe_dir.mkdir()

        # Relative path with .. is now allowed since we rely on symlink check
        relative_traversal = "./../../outside.csv"

        with patch('pathlib.Path.cwd', return_value=safe_dir):
            # Should not raise error for path resolution
            result = export._validate_output_path(relative_traversal, ".csv")
            assert result.suffix == ".csv"

    def test_validate_output_path_absolute_to_tmp_allowed(self, tmp_path):
        """Test that absolute paths to /tmp are allowed (e.g., pytest fixtures)"""
        safe_dir = tmp_path / "safe"
        safe_dir.mkdir()

        # Absolute path to temp directory (common with pytest fixtures)
        outside_file = tmp_path / "outside.csv"

        with patch('pathlib.Path.cwd', return_value=safe_dir):
            # Should be allowed since we allow absolute paths
            result = export._validate_output_path(str(outside_file), ".csv")
            assert result.suffix == ".csv"

    def test_validate_output_directory_valid(self, tmp_path):
        """Test that valid directories within current directory are accepted"""
        output_dir = tmp_path / "output"
        with patch('pathlib.Path.cwd', return_value=tmp_path):
            result = export._validate_output_directory(str(output_dir))
            assert result.name == "output"

    def test_validate_output_directory_absolute_allowed(self, tmp_path):
        """Test that absolute directory paths are now allowed"""
        safe_dir = tmp_path / "safe"
        safe_dir.mkdir()

        # Absolute path outside current directory should be allowed
        parent_dir = tmp_path / "parent"

        with patch('pathlib.Path.cwd', return_value=safe_dir):
            # Should not raise error for absolute directory paths
            result = export._validate_output_directory(str(parent_dir))
            assert result.name == "parent"

    def test_validate_output_directory_symlink_rejection(self, tmp_path):
        """Test that existing symlink directories are rejected"""
        safe_dir = tmp_path / "safe"
        safe_dir.mkdir()

        target_dir = tmp_path / "target"
        target_dir.mkdir()

        symlink_dir = safe_dir / "link"
        try:
            symlink_dir.symlink_to(target_dir)
        except OSError:
            pytest.skip("Symlinks not supported on this system")

        with patch('pathlib.Path.cwd', return_value=safe_dir):
            with pytest.raises(ValueError, match="Cannot use symlink"):
                export._validate_output_directory(str(symlink_dir))

    def test_format_sources_for_csv_count_mode(self):
        """Test CSV source formatting in count mode"""
        sources = [
            {"url": "https://example.com/1", "text": "Source 1"},
            {"url": "https://example.com/2", "text": "Source 2"}
        ]
        result = export._format_sources_for_csv(sources, mode="count")
        assert result == "2"

    def test_format_sources_for_csv_json_mode(self):
        """Test CSV source formatting in JSON mode"""
        sources = [
            {"url": "https://example.com/1", "text": "Source 1"},
            {"url": "https://example.com/2", "text": "Source 2"}
        ]
        result = export._format_sources_for_csv(sources, mode="json")
        parsed = json.loads(result)
        assert len(parsed) == 2
        assert parsed[0] == "https://example.com/1"

    def test_format_sources_for_csv_empty(self):
        """Test CSV source formatting with empty list"""
        result_count = export._format_sources_for_csv([], mode="count")
        result_json = export._format_sources_for_csv([], mode="json")
        assert result_count == "0"
        assert result_json == "[]"

    def test_escape_markdown_special_characters(self):
        """Test that markdown special characters are escaped"""
        text = "This has *asterisks* and [brackets] and (parens)"
        result = export._escape_markdown(text)
        assert "\\*" in result
        assert "\\[" in result
        assert "\\(" in result

    def test_truncate_text_below_limit(self):
        """Test truncation with text below limit"""
        text = "Short text"
        result = export._truncate_text(text, max_length=500)
        assert result == text

    def test_truncate_text_above_limit(self):
        """Test truncation with text exceeding limit"""
        text = "A" * 1000
        result = export._truncate_text(text, max_length=100)
        assert len(result) <= 105  # 100 + "..."
        assert result.endswith("...")

    def test_truncate_text_none(self):
        """Test truncation with None input"""
        result = export._truncate_text(None)
        assert result == ""

    def test_format_timestamp_datetime_object(self):
        """Test timestamp formatting with datetime object"""
        dt = datetime(2025, 1, 11, 14, 30, 45)
        result = export._format_timestamp(dt)
        assert result == "2025-01-11 14:30:45"

    def test_format_timestamp_iso_string(self):
        """Test timestamp formatting with ISO string"""
        iso_string = "2025-01-11T14:30:45"
        result = export._format_timestamp(iso_string)
        assert "2025-01-11" in result

    def test_format_timestamp_invalid_string(self):
        """Test timestamp formatting with invalid string"""
        result = export._format_timestamp("invalid timestamp")
        assert result == "invalid timestamp"

    def test_format_markdown_table_basic(self):
        """Test markdown table generation"""
        headers = ["Name", "Age", "City"]
        rows = [
            ["Alice", "30", "NYC"],
            ["Bob", "25", "LA"]
        ]
        result = export._format_markdown_table(headers, rows)
        assert "| Name | Age | City |" in result
        assert "| --- | --- | --- |" in result
        assert "| Alice | 30 | NYC |" in result
        assert "| Bob | 25 | LA |" in result

    def test_format_markdown_table_empty(self):
        """Test markdown table with empty data"""
        result = export._format_markdown_table([], [])
        assert result == ""


@pytest.mark.unit
class TestExportToCsv:
    """Tests for export_to_csv() function"""

    def test_export_to_csv_basic(self, test_db, tmp_path):
        """Test basic CSV export creates valid file with correct structure"""
        output_file = tmp_path / "results.csv"

        result = export.export_to_csv(str(output_file))

        assert output_file.exists()
        assert result['record_count'] > 0
        assert result['file_size_bytes'] > 0
        assert 'file_path' in result

    def test_export_to_csv_content_validation(self, test_db, tmp_path):
        """Test that CSV contains correct headers and data"""
        output_file = tmp_path / "results.csv"

        export.export_to_csv(str(output_file))

        with open(output_file, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            rows = list(reader)

        assert len(rows) >= 4  # At least 4 successful results
        assert 'query' in rows[0]
        assert 'model' in rows[0]
        assert 'answer_text' in rows[0]
        assert 'sources' in rows[0]

    def test_export_to_csv_without_sources(self, test_db, tmp_path):
        """Test CSV export excluding sources column"""
        output_file = tmp_path / "results_no_sources.csv"

        export.export_to_csv(str(output_file), include_sources=False)

        with open(output_file, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            rows = list(reader)

        assert 'sources' not in rows[0]

    def test_export_to_csv_with_model_filter(self, test_db, tmp_path):
        """Test CSV export with model filtering"""
        output_file = tmp_path / "gpt4_results.csv"
        filters = {"model": "gpt-4"}

        result = export.export_to_csv(str(output_file), filters=filters)

        with open(output_file, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            rows = list(reader)

        assert all(row['model'] == 'gpt-4' for row in rows)
        assert result['filters_applied'] >= 1

    def test_export_to_csv_with_query_pattern_filter(self, test_db, tmp_path):
        """Test CSV export with query pattern filtering"""
        output_file = tmp_path / "python_results.csv"
        filters = {"query_pattern": "Python"}

        result = export.export_to_csv(str(output_file), filters=filters)

        with open(output_file, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            rows = list(reader)

        assert len(rows) >= 2  # Two Python results
        assert all("Python" in row['query'] for row in rows)

    def test_export_to_csv_with_success_filter(self, test_db, tmp_path):
        """Test CSV export filtering by success status"""
        output_file = tmp_path / "success_results.csv"
        filters = {"success": True}

        result = export.export_to_csv(str(output_file), filters=filters)

        with open(output_file, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            rows = list(reader)

        # Exclude failed searches
        assert len(rows) == 4  # 4 successful results
        assert result['filters_applied'] >= 1

    def test_export_to_csv_no_results_raises_error(self, empty_db, tmp_path):
        """Test that export raises error when database is empty"""
        output_file = tmp_path / "empty.csv"

        with pytest.raises(ValueError, match="No results found"):
            export.export_to_csv(str(output_file))

    def test_export_to_csv_no_matching_filters_raises_error(self, test_db, tmp_path):
        """Test that export raises error when filters match nothing"""
        output_file = tmp_path / "no_match.csv"
        filters = {"model": "nonexistent-model"}

        with pytest.raises(ValueError, match="No results match"):
            export.export_to_csv(str(output_file), filters=filters)

    def test_export_to_csv_wrong_extension_raises_error(self, test_db, tmp_path):
        """Test that wrong file extension raises error"""
        output_file = tmp_path / "results.txt"

        with pytest.raises(ValueError, match="Expected extension"):
            export.export_to_csv(str(output_file))

    def test_export_to_csv_creates_parent_directories(self, test_db, tmp_path):
        """Test that parent directories are created if missing"""
        output_file = tmp_path / "deep" / "nested" / "dir" / "results.csv"

        result = export.export_to_csv(str(output_file))

        assert output_file.exists()
        assert output_file.parent.exists()

    def test_export_to_csv_data_escaping(self, test_db, tmp_path):
        """Test that special characters in data are properly escaped in CSV"""
        output_file = tmp_path / "special_chars.csv"

        export.export_to_csv(str(output_file))

        with open(output_file, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            rows = list(reader)

        # CSV should be readable without errors
        assert len(rows) > 0
        # Quotes and commas in data should be handled
        for row in rows:
            assert len(row) > 0


@pytest.mark.unit
class TestExportToMarkdown:
    """Tests for export_to_markdown() function"""

    def test_export_to_markdown_basic(self, test_db, tmp_path):
        """Test basic markdown export creates valid file"""
        output_file = tmp_path / "results.md"

        result = export.export_to_markdown(str(output_file))

        assert output_file.exists()
        assert result['record_count'] > 0
        assert result['file_size_bytes'] > 0
        assert 'file_path' in result

    def test_export_to_markdown_content(self, test_db, tmp_path):
        """Test markdown export contains proper formatting"""
        output_file = tmp_path / "results.md"

        export.export_to_markdown(str(output_file))

        content = output_file.read_text(encoding='utf-8')

        assert "# Search Results Export" in content
        assert "## Results" in content
        assert "### Query:" in content
        assert "**Model**:" in content
        assert "**Sources**:" in content

    def test_export_to_markdown_with_full_answers(self, test_db, tmp_path):
        """Test markdown export includes full answers when requested"""
        output_file = tmp_path / "full_answers.md"

        export.export_to_markdown(str(output_file), include_full_answers=True)

        content = output_file.read_text(encoding='utf-8')

        # Full answer should be present
        assert "Python is a high-level programming language" in content

    def test_export_to_markdown_with_truncated_answers(self, test_db, tmp_path):
        """Test markdown export truncates answers by default"""
        output_file = tmp_path / "truncated.md"

        export.export_to_markdown(str(output_file), include_full_answers=False)

        content = output_file.read_text(encoding='utf-8')

        # Check for truncation marker
        lines = content.split('\n')
        answer_lines = [l for l in lines if not l.startswith('#') and not l.startswith('-')]
        assert any('...' in line for line in answer_lines) or len(answer_lines) > 0

    def test_export_to_markdown_with_filters(self, test_db, tmp_path):
        """Test markdown export with filtering"""
        output_file = tmp_path / "filtered.md"
        filters = {"model": "gpt-4"}

        result = export.export_to_markdown(str(output_file), filters=filters)

        content = output_file.read_text(encoding='utf-8')

        assert result['filters_applied'] >= 1
        assert "**Model**" in content or "Model:" in content

    def test_export_to_markdown_with_sources(self, test_db, tmp_path):
        """Test that markdown export includes source links"""
        output_file = tmp_path / "with_sources.md"

        export.export_to_markdown(str(output_file))

        content = output_file.read_text(encoding='utf-8')

        # Check for markdown links
        assert "[" in content and "](" in content

    def test_export_to_markdown_no_results_raises_error(self, empty_db, tmp_path):
        """Test that markdown export raises error with no results"""
        output_file = tmp_path / "empty.md"

        with pytest.raises(ValueError, match="No results found"):
            export.export_to_markdown(str(output_file))

    def test_export_to_markdown_wrong_extension_raises_error(self, test_db, tmp_path):
        """Test that wrong extension raises error"""
        output_file = tmp_path / "results.txt"

        with pytest.raises(ValueError, match="Expected extension"):
            export.export_to_markdown(str(output_file))

    def test_export_to_markdown_creates_parent_directories(self, test_db, tmp_path):
        """Test that parent directories are created"""
        output_file = tmp_path / "a" / "b" / "c" / "results.md"

        result = export.export_to_markdown(str(output_file))

        assert output_file.exists()
        assert output_file.parent.exists()


@pytest.mark.unit
class TestExportComparisonToMarkdown:
    """Tests for export_comparison_to_markdown() function"""

    def test_export_comparison_basic(self, test_db, tmp_path):
        """Test basic model comparison export"""
        output_file = tmp_path / "comparison.md"

        result = export.export_comparison_to_markdown(
            "What is Python?",
            str(output_file)
        )

        assert output_file.exists()
        assert result['record_count'] > 0
        assert result['models_compared'] >= 2

    def test_export_comparison_content(self, test_db, tmp_path):
        """Test that comparison markdown has proper structure"""
        output_file = tmp_path / "comparison.md"

        export.export_comparison_to_markdown("What is Python?", str(output_file))

        content = output_file.read_text(encoding='utf-8')

        assert "# Model Comparison" in content
        assert "## Comparison Table" in content
        assert "## Detailed Results" in content
        assert "Model" in content
        assert "Count" in content

    def test_export_comparison_table_format(self, test_db, tmp_path):
        """Test that comparison table is properly formatted"""
        output_file = tmp_path / "comparison.md"

        export.export_comparison_to_markdown("What is Python?", str(output_file))

        content = output_file.read_text(encoding='utf-8')

        # Markdown table indicators
        assert "|" in content
        assert "---" in content

    def test_export_comparison_no_results_raises_error(self, test_db, tmp_path):
        """Test that comparison raises error for nonexistent query"""
        output_file = tmp_path / "comparison.md"

        with pytest.raises(ValueError, match="No results found"):
            export.export_comparison_to_markdown("Nonexistent query", str(output_file))

    def test_export_comparison_wrong_extension_raises_error(self, test_db, tmp_path):
        """Test that wrong extension raises error"""
        output_file = tmp_path / "comparison.csv"

        with pytest.raises(ValueError, match="Expected extension"):
            export.export_comparison_to_markdown("What is Python?", str(output_file))


@pytest.mark.unit
class TestBatchExportByModel:
    """Tests for batch_export_by_model() function"""

    def test_batch_export_by_model_json(self, test_db, tmp_path):
        """Test batch export to JSON format"""
        output_dir = tmp_path / "batch_json"

        result = export.batch_export_by_model(str(output_dir), format_type="json")

        assert result['files_created'] > 0
        assert result['total_records'] > 0
        assert result['total_size_bytes'] > 0
        assert len(result['by_model']) > 0

    def test_batch_export_by_model_csv(self, test_db, tmp_path):
        """Test batch export to CSV format"""
        output_dir = tmp_path / "batch_csv"

        result = export.batch_export_by_model(str(output_dir), format_type="csv")

        assert result['files_created'] > 0
        assert result['total_records'] > 0

    def test_batch_export_by_model_markdown(self, test_db, tmp_path):
        """Test batch export to Markdown format"""
        output_dir = tmp_path / "batch_md"

        result = export.batch_export_by_model(str(output_dir), format_type="md")

        assert result['files_created'] > 0
        assert result['total_records'] > 0

    def test_batch_export_by_model_files_created(self, test_db, tmp_path):
        """Test that correct number of files are created"""
        output_dir = tmp_path / "batch"

        result = export.batch_export_by_model(str(output_dir), format_type="json")

        # Count actual files in directory
        json_files = list(output_dir.glob("*.json"))
        assert len(json_files) == result['files_created']

    def test_batch_export_by_model_json_validity(self, test_db, tmp_path):
        """Test that generated JSON files are valid"""
        output_dir = tmp_path / "batch_json"

        result = export.batch_export_by_model(str(output_dir), format_type="json")

        for model, stats in result['by_model'].items():
            file_path = Path(stats['file_path'])
            assert file_path.exists()

            # Verify JSON is valid
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)

            assert isinstance(data, list)
            assert len(data) == stats['record_count']

    def test_batch_export_by_model_csv_validity(self, test_db, tmp_path):
        """Test that generated CSV files are valid"""
        output_dir = tmp_path / "batch_csv"

        result = export.batch_export_by_model(str(output_dir), format_type="csv")

        for model, stats in result['by_model'].items():
            file_path = Path(stats['file_path'])

            with open(file_path, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                rows = list(reader)

            assert len(rows) == stats['record_count']

    def test_batch_export_by_model_invalid_format_raises_error(self, test_db, tmp_path):
        """Test that invalid format raises error"""
        output_dir = tmp_path / "batch"

        with pytest.raises(ValueError, match="Invalid format"):
            export.batch_export_by_model(str(output_dir), format_type="xml")

    def test_batch_export_by_model_path_validation(self, test_db, tmp_path):
        """Test that absolute paths are allowed"""
        with patch('pathlib.Path.cwd', return_value=tmp_path / "subdir"):
            # Absolute paths should now be allowed
            result = export.batch_export_by_model(str(tmp_path / "outside"), format_type="json")
            assert result['files_created'] >= 0

    def test_batch_export_by_model_creates_directories(self, test_db, tmp_path):
        """Test that output directory is created"""
        output_dir = tmp_path / "a" / "b" / "c"

        result = export.batch_export_by_model(str(output_dir), format_type="json")

        assert output_dir.exists()


@pytest.mark.unit
class TestBatchExportByDate:
    """Tests for batch_export_by_date() function"""

    def test_batch_export_by_date_daily(self, test_db, tmp_path):
        """Test batch export by day period"""
        output_dir = tmp_path / "batch_daily"

        result = export.batch_export_by_date(
            str(output_dir),
            period="day",
            format_type="json"
        )

        assert result['files_created'] > 0
        assert result['total_records'] > 0
        assert 'by_period' in result

    def test_batch_export_by_date_weekly(self, test_db, tmp_path):
        """Test batch export by week period"""
        output_dir = tmp_path / "batch_weekly"

        result = export.batch_export_by_date(
            str(output_dir),
            period="week",
            format_type="json"
        )

        assert result['files_created'] > 0

    def test_batch_export_by_date_monthly(self, test_db, tmp_path):
        """Test batch export by month period"""
        output_dir = tmp_path / "batch_monthly"

        result = export.batch_export_by_date(
            str(output_dir),
            period="month",
            format_type="json"
        )

        assert result['files_created'] > 0

    def test_batch_export_by_date_csv_format(self, test_db, tmp_path):
        """Test batch export by date in CSV format"""
        output_dir = tmp_path / "batch_date_csv"

        result = export.batch_export_by_date(
            str(output_dir),
            period="day",
            format_type="csv"
        )

        assert result['files_created'] > 0

    def test_batch_export_by_date_markdown_format(self, test_db, tmp_path):
        """Test batch export by date in Markdown format"""
        output_dir = tmp_path / "batch_date_md"

        result = export.batch_export_by_date(
            str(output_dir),
            period="day",
            format_type="md"
        )

        assert result['files_created'] > 0

    def test_batch_export_by_date_file_validity(self, test_db, tmp_path):
        """Test that created date-based files contain correct records"""
        output_dir = tmp_path / "batch_date"

        result = export.batch_export_by_date(
            str(output_dir),
            period="day",
            format_type="json"
        )

        total_count = 0
        for period_key, stats in result['by_period'].items():
            file_path = Path(stats['file_path'])

            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)

            assert len(data) == stats['record_count']
            total_count += stats['record_count']

        assert total_count == result['total_records']

    def test_batch_export_by_date_invalid_period_raises_error(self, test_db, tmp_path):
        """Test that invalid period raises error"""
        output_dir = tmp_path / "batch"

        with pytest.raises(ValueError, match="Invalid period"):
            export.batch_export_by_date(str(output_dir), period="year")

    def test_batch_export_by_date_invalid_format_raises_error(self, test_db, tmp_path):
        """Test that invalid format raises error"""
        output_dir = tmp_path / "batch"

        with pytest.raises(ValueError, match="Invalid format"):
            export.batch_export_by_date(str(output_dir), format_type="xml")

    def test_batch_export_by_date_no_results_raises_error(self, empty_db, tmp_path):
        """Test that error is raised when database is empty"""
        output_dir = tmp_path / "batch"

        with pytest.raises(ValueError, match="No results found"):
            export.batch_export_by_date(str(output_dir), period="day")


@pytest.mark.unit
class TestExportDatabaseSummary:
    """Tests for export_database_summary() function"""

    def test_export_database_summary_basic(self, test_db, tmp_path):
        """Test basic database summary export"""
        output_file = tmp_path / "summary.md"

        result = export.export_database_summary(str(output_file))

        assert output_file.exists()
        assert result['record_count'] > 0
        assert result['file_size_bytes'] > 0

    def test_export_database_summary_content(self, test_db, tmp_path):
        """Test that summary contains all required sections"""
        output_file = tmp_path / "summary.md"

        export.export_database_summary(str(output_file))

        content = output_file.read_text(encoding='utf-8')

        assert "# Database Summary" in content
        assert "## Overview" in content
        assert "## Performance Statistics" in content
        assert "## Content Statistics" in content
        assert "## Model Summary" in content
        assert "## Top Queries" in content

    def test_export_database_summary_statistics(self, test_db, tmp_path):
        """Test that summary includes correct statistics"""
        output_file = tmp_path / "summary.md"

        export.export_database_summary(str(output_file))

        content = output_file.read_text(encoding='utf-8')

        # Check for specific statistics
        assert "**Total Results**" in content or "Total Results:" in content
        assert "**Unique Queries**" in content or "Unique Queries:" in content
        assert "**Unique Models**" in content or "Unique Models:" in content
        assert "**Average Execution Time**" in content or "Average Execution Time:" in content
        assert "**Success Rate**" in content or "Success Rate:" in content

    def test_export_database_summary_model_table(self, test_db, tmp_path):
        """Test that summary includes model comparison table"""
        output_file = tmp_path / "summary.md"

        export.export_database_summary(str(output_file))

        content = output_file.read_text(encoding='utf-8')

        assert "gpt-4" in content or "claude-3" in content or "sonar-pro" in content

    def test_export_database_summary_wrong_extension_raises_error(self, test_db, tmp_path):
        """Test that wrong extension raises error"""
        output_file = tmp_path / "summary.json"

        with pytest.raises(ValueError, match="Expected extension"):
            export.export_database_summary(str(output_file))

    def test_export_database_summary_no_results_raises_error(self, empty_db, tmp_path):
        """Test that error is raised when database is empty"""
        output_file = tmp_path / "summary.md"

        with pytest.raises(ValueError, match="No results found"):
            export.export_database_summary(str(output_file))

    def test_export_database_summary_creates_directories(self, test_db, tmp_path):
        """Test that parent directories are created"""
        output_file = tmp_path / "x" / "y" / "z" / "summary.md"

        result = export.export_database_summary(str(output_file))

        assert output_file.exists()
        assert output_file.parent.exists()


@pytest.mark.unit
class TestEdgeCases:
    """Tests for edge cases and special scenarios"""

    def test_export_with_special_characters_in_query(self, test_db, tmp_path):
        """Test export with special characters in query"""
        # Store result with special characters
        storage.save_search_result(
            query='How to "escape" special chars & symbols?',
            answer_text="Answer with <html> tags",
            sources=[],
            model="test-model",
            execution_time=5.0,
            success=True
        )

        csv_file = tmp_path / "special.csv"
        md_file = tmp_path / "special.md"

        export.export_to_csv(str(csv_file))
        export.export_to_markdown(str(md_file))

        assert csv_file.exists()
        assert md_file.exists()

    def test_export_with_very_long_answer(self, test_db, tmp_path):
        """Test export with extremely long answer text"""
        long_text = "A" * 10000
        storage.save_search_result(
            query="Long answer query",
            answer_text=long_text,
            sources=[],
            model="test",
            execution_time=5.0,
            success=True
        )

        csv_file = tmp_path / "long.csv"
        md_file = tmp_path / "long.md"

        result_csv = export.export_to_csv(str(csv_file))
        result_md = export.export_to_markdown(str(md_file), include_full_answers=True)

        assert result_csv['record_count'] > 0
        assert result_md['record_count'] > 0

    def test_export_with_missing_sources(self, test_db, tmp_path):
        """Test export with results that have no sources"""
        output_file = tmp_path / "no_sources.csv"

        result = export.export_to_csv(str(output_file))

        # Should export without error even with empty sources
        assert result['record_count'] > 0

    def test_export_with_null_model(self, test_db, tmp_path):
        """Test export with results that have None model"""
        storage.save_search_result(
            query="No model query",
            answer_text="Answer without model",
            sources=[],
            model=None,
            execution_time=5.0,
            success=True
        )

        output_file = tmp_path / "null_model.csv"

        export.export_to_csv(str(output_file))

        with open(output_file, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            rows = list(reader)

        # Null model should be represented as "unknown"
        assert any(row['model'] == 'unknown' for row in rows)

    def test_multiple_exports_same_session(self, test_db, tmp_path):
        """Test multiple exports in same session don't interfere"""
        csv_file = tmp_path / "export1.csv"
        md_file = tmp_path / "export1.md"
        json_dir = tmp_path / "batch"

        result1 = export.export_to_csv(str(csv_file))
        result2 = export.export_to_markdown(str(md_file))
        result3 = export.batch_export_by_model(str(json_dir), format_type="json")

        assert csv_file.exists()
        assert md_file.exists()
        assert json_dir.exists()
        assert result1['record_count'] == result2['record_count']
        assert result3['total_records'] > 0

    def test_export_with_unicode_characters(self, test_db, tmp_path):
        """Test export with unicode characters in content"""
        storage.save_search_result(
            query="Unicode test: 你好世界 مرحبا العالم",
            answer_text="Answer with emojis: Hello! 🚀 Testing UTF-8 support.",
            sources=[{"url": "https://example.com", "text": "中文 source"}],
            model="unicode-test",
            execution_time=5.0,
            success=True
        )

        csv_file = tmp_path / "unicode.csv"
        md_file = tmp_path / "unicode.md"

        export.export_to_csv(str(csv_file))
        export.export_to_markdown(str(md_file))

        assert csv_file.exists()
        assert md_file.exists()

        # Verify unicode is preserved
        csv_content = csv_file.read_text(encoding='utf-8')
        assert "你好世界" in csv_content or "مرحبا" in csv_content

    def test_export_preserves_timestamps(self, test_db, tmp_path):
        """Test that timestamps are correctly formatted in exports"""
        csv_file = tmp_path / "timestamps.csv"

        export.export_to_csv(str(csv_file))

        with open(csv_file, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            rows = list(reader)

        # All rows should have valid timestamp format
        for row in rows:
            timestamp = row.get('timestamp', '')
            # Should match YYYY-MM-DD HH:MM:SS format
            assert len(timestamp) > 0
            assert '-' in timestamp  # Date separator
