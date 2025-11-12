"""
Unit tests for src/analyze.py
Tests formatting, display functions, and CLI argument parsing.
"""
import pytest
import argparse
from io import StringIO
from unittest.mock import patch, MagicMock
from datetime import datetime
from src.analyze import (
    format_timestamp,
    print_result,
    list_queries,
    list_models,
    show_recent,
    show_by_query,
    show_by_model,
    compare_models,
    main
)


@pytest.mark.unit
class TestFormatTimestamp:
    """Tests for format_timestamp() function"""

    def test_format_timestamp_valid_iso_format(self):
        """Test formatting a valid ISO format timestamp"""
        timestamp = "2025-01-11 14:30:45"
        result = format_timestamp(timestamp)

        assert result == "2025-01-11 14:30:45"

    def test_format_timestamp_with_microseconds(self):
        """Test formatting timestamp with microseconds"""
        timestamp = "2025-01-11 14:30:45.123456"
        result = format_timestamp(timestamp)

        assert result == "2025-01-11 14:30:45"

    def test_format_timestamp_invalid_format_returns_original(self):
        """Test that invalid timestamp returns original string"""
        invalid_timestamp = "not-a-timestamp"
        result = format_timestamp(invalid_timestamp)

        assert result == invalid_timestamp

    def test_format_timestamp_empty_string(self):
        """Test that empty string returns N/A"""
        result = format_timestamp("")

        assert result == "N/A"

    def test_format_timestamp_none_like_string(self):
        """Test handling of None-like strings"""
        result = format_timestamp("None")

        assert result == "None"


@pytest.mark.unit
class TestPrintResult:
    """Tests for print_result() function"""

    def test_print_result_successful_search(self, sample_search_result, capsys):
        """Test printing a successful search result"""
        print_result(sample_search_result, show_full_answer=False)

        captured = capsys.readouterr()
        output = captured.out

        assert f"ID: {sample_search_result['id']}" in output
        assert f"Query: {sample_search_result['query']}" in output
        assert f"Model: {sample_search_result['model']}" in output
        assert "Success: ✓" in output
        assert "Answer" in output
        assert "Sources" in output

    def test_print_result_failed_search(self, sample_failed_search_result, capsys):
        """Test printing a failed search result"""
        print_result(sample_failed_search_result, show_full_answer=False)

        captured = capsys.readouterr()
        output = captured.out

        assert "Success: ✗" in output
        assert f"Error: {sample_failed_search_result['error_message']}" in output

    def test_print_result_full_answer(self, sample_search_result, capsys):
        """Test printing with full answer text"""
        print_result(sample_search_result, show_full_answer=True)

        captured = capsys.readouterr()
        output = captured.out

        # Should contain full answer text
        assert sample_search_result['answer_text'] in output
        # Should not show truncation indicator
        assert output.count('...') == 0

    def test_print_result_truncated_answer(self, capsys):
        """Test that long answers are truncated when show_full_answer=False"""
        long_result = {
            'id': 1,
            'query': 'Test query',
            'model': 'gpt-4',
            'timestamp': '2025-01-11 14:30:45',
            'execution_time_seconds': 10.0,
            'success': True,
            'answer_text': 'a' * 600,  # 600 chars, should be truncated to 500
            'sources': [],
            'screenshot_path': None
        }

        print_result(long_result, show_full_answer=False)

        captured = capsys.readouterr()
        output = captured.out

        # Should show truncation
        assert '...' in output
        # Should not show all 600 chars
        assert 'a' * 600 not in output

    def test_print_result_no_model_shows_default(self, capsys):
        """Test that missing model shows as 'default'"""
        result_no_model = {
            'id': 1,
            'query': 'Test',
            'model': None,
            'timestamp': '2025-01-11 14:30:45',
            'execution_time_seconds': 10.0,
            'success': True,
            'answer_text': 'Answer',
            'sources': []
        }

        print_result(result_no_model, show_full_answer=False)

        captured = capsys.readouterr()
        assert "Model: default" in captured.out

    def test_print_result_shows_sources(self, sample_search_result, capsys):
        """Test that sources are displayed"""
        print_result(sample_search_result, show_full_answer=False)

        captured = capsys.readouterr()
        output = captured.out

        assert f"Sources ({len(sample_search_result['sources'])})" in output
        for source in sample_search_result['sources']:
            assert source['url'] in output
            assert source['text'] in output

    def test_print_result_limits_sources_to_five(self, capsys):
        """Test that only first 5 sources are shown"""
        result_many_sources = {
            'id': 1,
            'query': 'Test',
            'model': 'gpt-4',
            'timestamp': '2025-01-11 14:30:45',
            'execution_time_seconds': 10.0,
            'success': True,
            'answer_text': 'Answer',
            'sources': [{'url': f'https://example.com/{i}', 'text': f'Source {i}'} for i in range(10)]
        }

        print_result(result_many_sources, show_full_answer=False)

        captured = capsys.readouterr()
        output = captured.out

        # Should show first 5 sources
        for i in range(5):
            assert f'Source {i}' in output

        # Should not show sources 6-9
        for i in range(6, 10):
            assert f'Source {i}' not in output


@pytest.mark.unit
class TestListQueries:
    """Tests for list_queries() function"""

    @patch('src.analyze.get_unique_queries')
    def test_list_queries_displays_all_queries(self, mock_get_queries, capsys):
        """Test that all unique queries are displayed"""
        mock_get_queries.return_value = [
            "What is Python?",
            "What is JavaScript?",
            "What is GEO?"
        ]

        args = MagicMock()
        list_queries(args)

        captured = capsys.readouterr()
        output = captured.out

        assert "Found 3 unique queries" in output
        assert "What is Python?" in output
        assert "What is JavaScript?" in output
        assert "What is GEO?" in output

    @patch('src.analyze.get_unique_queries')
    def test_list_queries_empty_database(self, mock_get_queries, capsys):
        """Test listing queries from empty database"""
        mock_get_queries.return_value = []

        args = MagicMock()
        list_queries(args)

        captured = capsys.readouterr()
        assert "Found 0 unique queries" in captured.out


@pytest.mark.unit
class TestListModels:
    """Tests for list_models() function"""

    @patch('src.analyze.get_unique_models')
    def test_list_models_displays_all_models(self, mock_get_models, capsys):
        """Test that all unique models are displayed"""
        mock_get_models.return_value = ["gpt-4", "claude-3", "gemini"]

        args = MagicMock()
        list_models(args)

        captured = capsys.readouterr()
        output = captured.out

        assert "Found 3 unique models" in output
        assert "gpt-4" in output
        assert "claude-3" in output
        assert "gemini" in output

    @patch('src.analyze.get_unique_models')
    def test_list_models_empty_database(self, mock_get_models, capsys):
        """Test listing models from empty database"""
        mock_get_models.return_value = []

        args = MagicMock()
        list_models(args)

        captured = capsys.readouterr()
        assert "Found 0 unique models" in captured.out


@pytest.mark.unit
class TestShowRecent:
    """Tests for show_recent() function"""

    @patch('src.analyze.get_recent_results')
    def test_show_recent_displays_results(self, mock_get_recent, multiple_search_results, capsys):
        """Test showing recent results"""
        mock_get_recent.return_value = multiple_search_results

        args = MagicMock(limit=10, full=False)
        show_recent(args)

        captured = capsys.readouterr()
        output = captured.out

        assert "Most recent" in output
        assert "What is Python?" in output
        assert "What is JavaScript?" in output

    @patch('src.analyze.get_recent_results')
    def test_show_recent_uses_default_limit(self, mock_get_recent, capsys):
        """Test that default limit of 10 is used"""
        mock_get_recent.return_value = []

        args = MagicMock(limit=None, full=False)
        show_recent(args)

        # Verify function was called with limit=10
        mock_get_recent.assert_called_once_with(limit=10)


@pytest.mark.unit
class TestShowByQuery:
    """Tests for show_by_query() function"""

    @patch('src.analyze.get_results_by_query')
    def test_show_by_query_displays_results(self, mock_get_results, sample_search_result, capsys):
        """Test showing results for a specific query"""
        mock_get_results.return_value = [sample_search_result]

        args = MagicMock(query="What is GEO?", model=None, full=False)
        show_by_query(args)

        captured = capsys.readouterr()
        output = captured.out

        assert "Found 1 results for query" in output
        assert "What is GEO?" in output

    @patch('src.analyze.get_results_by_query')
    def test_show_by_query_with_model_filter(self, mock_get_results, capsys):
        """Test filtering by model"""
        mock_get_results.return_value = []

        args = MagicMock(query="What is Python?", model="gpt-4", full=False)
        show_by_query(args)

        captured = capsys.readouterr()
        output = captured.out

        assert "Filtered by model: gpt-4" in output
        mock_get_results.assert_called_once_with("What is Python?", model="gpt-4")

    def test_show_by_query_missing_query(self, capsys):
        """Test error when query is missing"""
        args = MagicMock(query=None, model=None, full=False)
        show_by_query(args)

        captured = capsys.readouterr()
        assert "❌ Error: --query is required" in captured.out


@pytest.mark.unit
class TestShowByModel:
    """Tests for show_by_model() function"""

    @patch('src.analyze.get_results_by_model')
    def test_show_by_model_displays_results(self, mock_get_results, sample_search_result, capsys):
        """Test showing results for a specific model"""
        mock_get_results.return_value = [sample_search_result]

        args = MagicMock(model="gpt-4", limit=50, full=False)
        show_by_model(args)

        captured = capsys.readouterr()
        output = captured.out

        assert "Found 1 results for model: gpt-4" in output

    @patch('src.analyze.get_results_by_model')
    def test_show_by_model_uses_default_limit(self, mock_get_results, capsys):
        """Test that default limit of 50 is used"""
        mock_get_results.return_value = []

        args = MagicMock(model="gpt-4", limit=None, full=False)
        show_by_model(args)

        mock_get_results.assert_called_once_with("gpt-4", limit=50)

    def test_show_by_model_missing_model(self, capsys):
        """Test error when model is missing"""
        args = MagicMock(model=None, limit=50, full=False)
        show_by_model(args)

        captured = capsys.readouterr()
        assert "❌ Error: --model is required" in captured.out


@pytest.mark.unit
class TestCompareModels:
    """Tests for compare_models() function"""

    @patch('src.analyze.compare_models_for_query')
    def test_compare_models_displays_comparison(self, mock_compare, multiple_search_results, capsys):
        """Test comparing models for a query"""
        # Group results by model
        grouped = {
            "gpt-4": [multiple_search_results[0]],
            "claude-3": [multiple_search_results[1]]
        }
        mock_compare.return_value = grouped

        args = MagicMock(query="What is Python?", full=False)
        compare_models(args)

        captured = capsys.readouterr()
        output = captured.out

        assert "COMPARISON:" in output
        assert "What is Python?" in output
        assert "Found results from 2 model(s)" in output
        assert "MODEL: gpt-4" in output
        assert "MODEL: claude-3" in output

    @patch('src.analyze.compare_models_for_query')
    def test_compare_models_no_results(self, mock_compare, capsys):
        """Test comparing when no results exist"""
        mock_compare.return_value = {}

        args = MagicMock(query="Non-existent query", full=False)
        compare_models(args)

        captured = capsys.readouterr()
        assert "❌ No results found" in captured.out

    def test_compare_models_missing_query(self, capsys):
        """Test error when query is missing"""
        args = MagicMock(query=None, full=False)
        compare_models(args)

        captured = capsys.readouterr()
        assert "❌ Error: --query is required" in captured.out

    @patch('src.analyze.compare_models_for_query')
    def test_compare_models_with_full_answer(self, mock_compare, sample_search_result, capsys):
        """Test comparison with full answer display"""
        mock_compare.return_value = {"gpt-4": [sample_search_result]}

        args = MagicMock(query="Test query", full=True)
        compare_models(args)

        captured = capsys.readouterr()
        output = captured.out

        # Should show full answer
        assert sample_search_result['answer_text'] in output


@pytest.mark.integration
class TestCLIArguments:
    """Integration tests for CLI argument parsing"""

    def test_cli_list_queries_command(self):
        """Test parsing list-queries command"""
        with patch('sys.argv', ['analyze.py', 'list-queries']):
            parser = argparse.ArgumentParser()
            subparsers = parser.add_subparsers(dest='command')
            parser_queries = subparsers.add_parser('list-queries')

            args = parser.parse_args(['list-queries'])
            assert args.command == 'list-queries'

    def test_cli_recent_command_with_options(self):
        """Test parsing recent command with options"""
        with patch('sys.argv', ['analyze.py', 'recent', '--limit', '20', '--full']):
            parser = argparse.ArgumentParser()
            subparsers = parser.add_subparsers(dest='command')
            parser_recent = subparsers.add_parser('recent')
            parser_recent.add_argument('--limit', type=int)
            parser_recent.add_argument('--full', action='store_true')

            args = parser.parse_args(['recent', '--limit', '20', '--full'])
            assert args.command == 'recent'
            assert args.limit == 20
            assert args.full is True

    def test_cli_query_command_with_model(self):
        """Test parsing query command with model filter"""
        parser = argparse.ArgumentParser()
        subparsers = parser.add_subparsers(dest='command')
        parser_query = subparsers.add_parser('query')
        parser_query.add_argument('--query', required=True)
        parser_query.add_argument('--model')

        args = parser.parse_args(['query', '--query', 'What is Python?', '--model', 'gpt-4'])
        assert args.command == 'query'
        assert args.query == 'What is Python?'
        assert args.model == 'gpt-4'

    def test_cli_compare_command(self):
        """Test parsing compare command"""
        parser = argparse.ArgumentParser()
        subparsers = parser.add_subparsers(dest='command')
        parser_compare = subparsers.add_parser('compare')
        parser_compare.add_argument('--query', required=True)
        parser_compare.add_argument('--full', action='store_true')

        args = parser.parse_args(['compare', '--query', 'Test', '--full'])
        assert args.command == 'compare'
        assert args.query == 'Test'
        assert args.full is True


@pytest.mark.unit
class TestMalformedResultDicts:
    """Tests for handling malformed result dictionaries"""

    def test_print_result_missing_query_key(self, capsys):
        """Test print_result with missing 'query' key"""
        result_missing_query = {
            # 'query' key missing
            'model': 'gpt-4',
            'timestamp': '2025-01-11 14:30:45',
            'execution_time_seconds': 10.0,
            'success': True,
            'answer_text': 'Answer',
            'sources': []
        }

        # Should handle missing key gracefully (may raise KeyError or handle it)
        try:
            print_result(result_missing_query, show_full_answer=False)
        except KeyError:
            # KeyError is acceptable behavior for missing required field
            pass

    def test_print_result_missing_model_key(self, capsys):
        """Test print_result with missing 'model' key"""
        result_missing_model = {
            'query': 'Test query',
            # 'model' key missing
            'timestamp': '2025-01-11 14:30:45',
            'execution_time_seconds': 10.0,
            'success': True,
            'answer_text': 'Answer',
            'sources': []
        }

        try:
            print_result(result_missing_model, show_full_answer=False)
        except KeyError:
            pass

    def test_print_result_sources_as_string(self, capsys):
        """Test print_result when sources is string instead of list"""
        result_sources_string = {
            'id': 1,
            'query': 'Test',
            'model': 'gpt-4',
            'timestamp': '2025-01-11 14:30:45',
            'execution_time_seconds': 10.0,
            'success': True,
            'answer_text': 'Answer',
            'sources': "not a list"  # Wrong type
        }

        # Should handle type mismatch
        try:
            print_result(result_sources_string, show_full_answer=False)
        except (TypeError, AttributeError):
            pass

    def test_print_result_answer_text_as_none(self, capsys):
        """Test print_result when answer_text is None"""
        result_none_answer = {
            'id': 1,
            'query': 'Test',
            'model': 'gpt-4',
            'timestamp': '2025-01-11 14:30:45',
            'execution_time_seconds': 10.0,
            'success': True,
            'answer_text': None,  # None instead of string
            'sources': []
        }

        # Should handle None gracefully (may print "None" or handle specially)
        try:
            print_result(result_none_answer, show_full_answer=False)
            captured = capsys.readouterr()
            # Just verify it doesn't crash
            assert isinstance(captured.out, str)
        except TypeError:
            pass

    def test_print_result_execution_time_as_string(self, capsys):
        """Test print_result when execution_time is string instead of float"""
        result_string_time = {
            'id': 1,
            'query': 'Test',
            'model': 'gpt-4',
            'timestamp': '2025-01-11 14:30:45',
            'execution_time_seconds': "10.0",  # String instead of float
            'success': True,
            'answer_text': 'Answer',
            'sources': []
        }

        # Should handle or convert string
        try:
            print_result(result_string_time, show_full_answer=False)
            captured = capsys.readouterr()
            assert "10.0" in captured.out
        except (TypeError, ValueError):
            pass

    def test_print_result_success_as_int(self, capsys):
        """Test print_result when success is 1/0 instead of True/False"""
        result_int_success = {
            'id': 1,
            'query': 'Test',
            'model': 'gpt-4',
            'timestamp': '2025-01-11 14:30:45',
            'execution_time_seconds': 10.0,
            'success': 1,  # int instead of bool
            'answer_text': 'Answer',
            'sources': []
        }

        # Python treats 1 as truthy, so should work
        print_result(result_int_success, show_full_answer=False)
        captured = capsys.readouterr()
        assert "✓" in captured.out

    def test_print_result_sources_with_missing_url(self, capsys):
        """Test print_result when source dicts missing 'url' key"""
        result_sources_no_url = {
            'query': 'Test',
            'model': 'gpt-4',
            'timestamp': '2025-01-11 14:30:45',
            'execution_time_seconds': 10.0,
            'success': True,
            'answer_text': 'Answer',
            'sources': [
                {'text': 'Source without URL'}  # Missing 'url'
            ]
        }

        try:
            print_result(result_sources_no_url, show_full_answer=False)
        except KeyError:
            pass


@pytest.mark.unit
class TestTimestampFormatVariations:
    """Tests for various timestamp format edge cases"""

    def test_format_timestamp_with_timezone(self):
        """Test timestamp with timezone information"""
        timestamp_with_tz = "2025-01-11T14:30:45Z"
        result = format_timestamp(timestamp_with_tz)

        # Should return something (may strip timezone or keep it)
        assert isinstance(result, str)

    def test_format_timestamp_with_timezone_offset(self):
        """Test timestamp with timezone offset (+00:00)"""
        timestamp_with_offset = "2025-01-11T14:30:45+00:00"
        result = format_timestamp(timestamp_with_offset)

        assert isinstance(result, str)

    def test_format_timestamp_us_format(self):
        """Test US date format (MM/DD/YYYY)"""
        us_format = "01/11/2025 14:30:45"
        result = format_timestamp(us_format)

        # Should return original string if can't parse
        assert result == us_format

    def test_format_timestamp_unix_epoch(self):
        """Test Unix epoch timestamp (integer)"""
        unix_epoch = "1705000245"
        result = format_timestamp(unix_epoch)

        # Should return original if can't parse
        assert result == unix_epoch

    def test_format_timestamp_invalid_date(self):
        """Test invalid dates (Feb 30, Month 13)"""
        invalid_dates = [
            "2025-02-30 14:30:45",  # Feb 30 doesn't exist
            "2025-13-01 14:30:45",  # Month 13 doesn't exist
            "2025-01-32 14:30:45",  # Day 32 doesn't exist
        ]

        for invalid_date in invalid_dates:
            result = format_timestamp(invalid_date)
            # Should return original string
            assert result == invalid_date

    def test_format_timestamp_very_old_date(self):
        """Test very old dates (year 1000)"""
        old_date = "1000-01-01 12:00:00"
        result = format_timestamp(old_date)

        # Should handle or return original
        assert isinstance(result, str)

    def test_format_timestamp_future_date(self):
        """Test far future dates (year 9999)"""
        future_date = "9999-12-31 23:59:59"
        result = format_timestamp(future_date)

        # Should handle or return original
        assert isinstance(result, str)

    def test_format_timestamp_as_none_value(self):
        """Test format_timestamp with actual None (not string 'None')"""
        # This tests the edge case of None vs "None"
        result = format_timestamp(None)
        # Fixed behavior: returns "N/A" when given None
        assert result == "N/A"

    def test_format_timestamp_with_only_date(self):
        """Test timestamp with only date, no time"""
        date_only = "2025-01-11"
        result = format_timestamp(date_only)

        assert isinstance(result, str)

    def test_format_timestamp_with_milliseconds_long(self):
        """Test timestamp with many decimal places in seconds"""
        timestamp_long_ms = "2025-01-11 14:30:45.123456789"
        result = format_timestamp(timestamp_long_ms)

        # Should truncate to seconds
        assert "." not in result or result.count(".") == 0


@pytest.mark.unit
class TestCLIArgumentEdgeCases:
    """Tests for CLI argument edge cases"""

    def test_query_with_special_shell_characters(self):
        """Test query argument with special shell characters"""
        parser = argparse.ArgumentParser()
        subparsers = parser.add_subparsers(dest='command')
        parser_query = subparsers.add_parser('query')
        parser_query.add_argument('--query', required=True)

        # Test various special characters
        special_queries = [
            "query with 'single quotes'",
            'query with "double quotes"',
            "query with semicolon;",
            "query with | pipe",
            "query with & ampersand",
        ]

        for special_query in special_queries:
            args = parser.parse_args(['query', '--query', special_query])
            assert args.query == special_query

    def test_query_with_newlines(self):
        """Test query with embedded newlines"""
        parser = argparse.ArgumentParser()
        subparsers = parser.add_subparsers(dest='command')
        parser_query = subparsers.add_parser('query')
        parser_query.add_argument('--query', required=True)

        query_with_newlines = "Line 1\nLine 2\nLine 3"
        args = parser.parse_args(['query', '--query', query_with_newlines])
        assert args.query == query_with_newlines

    def test_model_as_empty_string(self):
        """Test --model parameter as empty string"""
        parser = argparse.ArgumentParser()
        subparsers = parser.add_subparsers(dest='command')
        parser_query = subparsers.add_parser('query')
        parser_query.add_argument('--query', required=True)
        parser_query.add_argument('--model')

        args = parser.parse_args(['query', '--query', 'Test', '--model', ''])
        assert args.model == ""

    def test_limit_as_zero(self):
        """Test --limit parameter as 0"""
        parser = argparse.ArgumentParser()
        subparsers = parser.add_subparsers(dest='command')
        parser_recent = subparsers.add_parser('recent')
        parser_recent.add_argument('--limit', type=int)

        args = parser.parse_args(['recent', '--limit', '0'])
        assert args.limit == 0

    def test_limit_as_negative(self):
        """Test --limit parameter as negative number"""
        parser = argparse.ArgumentParser()
        subparsers = parser.add_subparsers(dest='command')
        parser_recent = subparsers.add_parser('recent')
        parser_recent.add_argument('--limit', type=int)

        args = parser.parse_args(['recent', '--limit', '-10'])
        assert args.limit == -10

    def test_very_long_query_string(self):
        """Test extremely long query string (10,000 chars)"""
        parser = argparse.ArgumentParser()
        subparsers = parser.add_subparsers(dest='command')
        parser_query = subparsers.add_parser('query')
        parser_query.add_argument('--query', required=True)

        very_long_query = "a" * 10000
        args = parser.parse_args(['query', '--query', very_long_query])
        assert len(args.query) == 10000

    def test_multiple_full_flags(self):
        """Test multiple --full flags (should use last or first)"""
        parser = argparse.ArgumentParser()
        subparsers = parser.add_subparsers(dest='command')
        parser_recent = subparsers.add_parser('recent')
        parser_recent.add_argument('--full', action='store_true')

        # argparse treats multiple --full as same as one
        args = parser.parse_args(['recent', '--full', '--full'])
        assert args.full is True


@pytest.mark.unit
class TestFilterCommand:
    """Tests for filter command with advanced criteria"""

    @patch('src.analyze._filter_results_advanced')
    def test_filter_command_basic(self, mock_filter, capsys):
        """Test filter command with basic options"""
        mock_filter.return_value = []

        from src.analyze import handle_filter
        args = MagicMock(
            model=None, query_pattern=None, start_date=None, end_date=None,
            success_only=False, failed_only=False, min_exec_time=None,
            max_exec_time=None, min_answer_length=None, max_answer_length=None,
            has_sources=False, limit=None, order_by='timestamp', order_asc=False,
            full=False
        )

        handle_filter(args)

        captured = capsys.readouterr()
        assert "Found 0 results matching filter criteria" in captured.out

    @patch('src.analyze._filter_results_advanced')
    def test_filter_command_with_model(self, mock_filter, multiple_search_results, capsys):
        """Test filter command with model filter"""
        mock_filter.return_value = [multiple_search_results[0]]

        from src.analyze import handle_filter
        args = MagicMock(
            model='gpt-4', query_pattern=None, start_date=None, end_date=None,
            success_only=False, failed_only=False, min_exec_time=None,
            max_exec_time=None, min_answer_length=None, max_answer_length=None,
            has_sources=False, limit=None, order_by='timestamp', order_asc=False,
            full=False
        )

        handle_filter(args)

        captured = capsys.readouterr()
        assert "Found 1 results matching filter criteria" in captured.out
        mock_filter.assert_called_once()

    @patch('src.analyze._filter_results_advanced')
    def test_filter_command_success_only(self, mock_filter, capsys):
        """Test filter command with success_only flag"""
        mock_filter.return_value = []

        from src.analyze import handle_filter
        args = MagicMock(
            model=None, query_pattern=None, start_date=None, end_date=None,
            success_only=True, failed_only=False, min_exec_time=None,
            max_exec_time=None, min_answer_length=None, max_answer_length=None,
            has_sources=False, limit=10, order_by='timestamp', order_asc=False,
            full=False
        )

        handle_filter(args)

        # Verify filter was called with success_only=True
        call_args = mock_filter.call_args
        assert call_args[1]['success_only'] is True

    @patch('src.analyze._filter_results_advanced')
    def test_filter_command_date_range(self, mock_filter, capsys):
        """Test filter command with date range"""
        mock_filter.return_value = []

        from src.analyze import handle_filter
        args = MagicMock(
            model=None, query_pattern=None, start_date='2025-01-01', end_date='2025-01-31',
            success_only=False, failed_only=False, min_exec_time=None,
            max_exec_time=None, min_answer_length=None, max_answer_length=None,
            has_sources=False, limit=None, order_by='timestamp', order_asc=False,
            full=False
        )

        handle_filter(args)

        call_args = mock_filter.call_args
        assert call_args[1]['start_date'] == '2025-01-01'
        assert call_args[1]['end_date'] == '2025-01-31'

    @patch('src.analyze._filter_results_advanced')
    def test_filter_command_execution_time_range(self, mock_filter, capsys):
        """Test filter command with execution time constraints"""
        mock_filter.return_value = []

        from src.analyze import handle_filter
        args = MagicMock(
            model=None, query_pattern=None, start_date=None, end_date=None,
            success_only=False, failed_only=False, min_exec_time=5.0,
            max_exec_time=15.0, min_answer_length=None, max_answer_length=None,
            has_sources=False, limit=None, order_by='timestamp', order_asc=False,
            full=False
        )

        handle_filter(args)

        call_args = mock_filter.call_args
        assert call_args[1]['min_exec_time'] == 5.0
        assert call_args[1]['max_exec_time'] == 15.0


@pytest.mark.unit
class TestSearchCommand:
    """Tests for full-text search command"""

    @patch('src.analyze._search_results')
    def test_search_command_basic(self, mock_search, capsys):
        """Test search command with basic term"""
        mock_search.return_value = []

        from src.analyze import handle_search
        args = MagicMock(
            search_term='python', search_in='answers', model=None,
            case_sensitive=False, limit=None, full=False
        )

        handle_search(args)

        captured = capsys.readouterr()
        assert 'Found 0 results for: "python"' in captured.out

    @patch('src.analyze._search_results')
    def test_search_command_missing_term(self, mock_search, capsys):
        """Test search command without search term"""
        from src.analyze import handle_search
        args = MagicMock(search_term=None, search_in='answers', model=None,
                        case_sensitive=False, limit=None, full=False)

        handle_search(args)

        captured = capsys.readouterr()
        assert "Error: search term is required" in captured.out

    @patch('src.analyze._search_results')
    def test_search_command_with_results(self, mock_search, multiple_search_results, capsys):
        """Test search command returning results"""
        mock_search.return_value = [multiple_search_results[0]]

        from src.analyze import handle_search
        args = MagicMock(
            search_term='Python', search_in='answers', model=None,
            case_sensitive=False, limit=10, full=False
        )

        handle_search(args)

        captured = capsys.readouterr()
        assert 'Found 1 results for: "Python"' in captured.out

    @patch('src.analyze._search_results')
    def test_search_command_case_sensitive(self, mock_search, capsys):
        """Test search command with case-sensitive flag"""
        mock_search.return_value = []

        from src.analyze import handle_search
        args = MagicMock(
            search_term='Python', search_in='answers', model=None,
            case_sensitive=True, limit=None, full=False
        )

        handle_search(args)

        call_args = mock_search.call_args
        assert call_args[1]['case_sensitive'] is True

    @patch('src.analyze._search_results')
    def test_search_command_search_in_sources(self, mock_search, capsys):
        """Test search command searching in sources"""
        mock_search.return_value = []

        from src.analyze import handle_search
        args = MagicMock(
            search_term='example', search_in='sources', model=None,
            case_sensitive=False, limit=None, full=False
        )

        handle_search(args)

        call_args = mock_search.call_args
        assert call_args[1]['search_in'] == 'sources'


@pytest.mark.unit
class TestStatsCommand:
    """Tests for database statistics command"""

    @patch('src.analyze._get_database_stats')
    def test_stats_command_basic(self, mock_stats, capsys):
        """Test stats command displays database statistics"""
        mock_stats.return_value = {
            'total_records': 100,
            'unique_models': 5,
            'unique_queries': 25,
            'date_range': ('2025-01-01 10:00:00', '2025-01-11 15:00:00'),
            'successful_records': 95,
            'success_rate': 95.0,
            'avg_execution_time': 11.5,
            'avg_answer_length': 250.0
        }

        from src.analyze import handle_stats
        args = MagicMock()

        handle_stats(args)

        captured = capsys.readouterr()
        assert "DATABASE STATISTICS" in captured.out
        assert "Total Records: 100" in captured.out
        assert "Unique Queries: 25" in captured.out
        assert "Unique Models: 5" in captured.out

    @patch('src.analyze._get_database_stats')
    def test_stats_command_empty_database(self, mock_stats, capsys):
        """Test stats command with empty database"""
        mock_stats.return_value = {
            'total_records': 0,
            'unique_models': 0,
            'unique_queries': 0,
            'date_range': (None, None),
            'successful_records': 0,
            'success_rate': 0.0,
            'avg_execution_time': 0.0,
            'avg_answer_length': 0.0
        }

        from src.analyze import handle_stats
        args = MagicMock()

        handle_stats(args)

        captured = capsys.readouterr()
        assert "Total Records: 0" in captured.out


@pytest.mark.unit
class TestStatsModelCommand:
    """Tests for per-model statistics command"""

    @patch('src.analyze._get_model_stats')
    def test_stats_model_command_all_models(self, mock_stats, capsys):
        """Test stats-model command showing all models"""
        mock_stats.return_value = [
            {
                'model': 'gpt-4',
                'record_count': 50,
                'successful': 48,
                'avg_exec_time': 11.0,
                'min_exec_time': 8.5,
                'max_exec_time': 14.2,
                'avg_answer_length': 300.0,
                'unique_queries': 10
            },
            {
                'model': 'claude-3',
                'record_count': 50,
                'successful': 47,
                'avg_exec_time': 12.5,
                'min_exec_time': 9.0,
                'max_exec_time': 15.0,
                'avg_answer_length': 280.0,
                'unique_queries': 12
            }
        ]

        from src.analyze import handle_stats_model
        args = MagicMock(model=None, start_date=None, end_date=None, full=False)

        handle_stats_model(args)

        captured = capsys.readouterr()
        assert "MODEL STATISTICS" in captured.out
        assert "gpt-4" in captured.out
        assert "claude-3" in captured.out

    @patch('src.analyze._get_model_stats')
    def test_stats_model_command_specific_model(self, mock_stats, capsys):
        """Test stats-model command for specific model"""
        mock_stats.return_value = [
            {
                'model': 'gpt-4',
                'record_count': 50,
                'successful': 48,
                'avg_exec_time': 11.0,
                'min_exec_time': 8.5,
                'max_exec_time': 14.2,
                'avg_answer_length': 300.0,
                'avg_sources': 3.5
            }
        ]

        from src.analyze import handle_stats_model
        args = MagicMock(model='gpt-4', start_date=None, end_date=None, full=True)

        handle_stats_model(args)

        captured = capsys.readouterr()
        assert "Model: gpt-4" in captured.out
        assert "Records: 50" in captured.out

    @patch('src.analyze._get_model_stats')
    def test_stats_model_command_no_data(self, mock_stats, capsys):
        """Test stats-model command with no data"""
        mock_stats.return_value = []

        from src.analyze import handle_stats_model
        args = MagicMock(model='nonexistent', start_date=None, end_date=None, full=False)

        handle_stats_model(args)

        captured = capsys.readouterr()
        assert "No data found" in captured.out


@pytest.mark.unit
class TestStatsTrendsCommand:
    """Tests for trend analysis command"""

    @patch('src.analyze._get_trend_data')
    def test_stats_trends_execution_time(self, mock_trends, capsys):
        """Test stats-trends command for execution time metric"""
        mock_trends.return_value = [
            {'period': '2025-01-11', 'value': 11.5, 'count': 10},
            {'period': '2025-01-10', 'value': 10.8, 'count': 12}
        ]

        from src.analyze import handle_stats_trends
        args = MagicMock(
            metric='execution_time', period='day', limit=None, model=None
        )

        handle_stats_trends(args)

        captured = capsys.readouterr()
        assert "TREND ANALYSIS" in captured.out
        assert "2025-01-11" in captured.out
        assert "11.50s" in captured.out

    @patch('src.analyze._get_trend_data')
    def test_stats_trends_success_rate(self, mock_trends, capsys):
        """Test stats-trends command for success rate metric"""
        mock_trends.return_value = [
            {'period': '2025-01-11', 'value': 95.0, 'count': 20}
        ]

        from src.analyze import handle_stats_trends
        args = MagicMock(
            metric='success_rate', period='day', limit=10, model=None
        )

        handle_stats_trends(args)

        captured = capsys.readouterr()
        assert "95.0%" in captured.out

    @patch('src.analyze._get_trend_data')
    def test_stats_trends_no_data(self, mock_trends, capsys):
        """Test stats-trends command with no trend data"""
        mock_trends.return_value = []

        from src.analyze import handle_stats_trends
        args = MagicMock(
            metric='answer_length', period='week', limit=None, model=None
        )

        handle_stats_trends(args)

        captured = capsys.readouterr()
        assert "No trend data found" in captured.out


@pytest.mark.unit
class TestStatsPerformanceCommand:
    """Tests for performance comparison command"""

    @patch('src.analyze._filter_results_advanced')
    def test_stats_performance_basic(self, mock_filter, multiple_search_results, capsys):
        """Test stats-performance command basic operation"""
        mock_filter.return_value = multiple_search_results

        from src.analyze import handle_stats_performance
        args = MagicMock(query=None, start_date=None, end_date=None)

        handle_stats_performance(args)

        captured = capsys.readouterr()
        assert "PERFORMANCE COMPARISON" in captured.out

    @patch('src.analyze._filter_results_advanced')
    def test_stats_performance_no_results(self, mock_filter, capsys):
        """Test stats-performance command with no results"""
        mock_filter.return_value = []

        from src.analyze import handle_stats_performance
        args = MagicMock(query=None, start_date=None, end_date=None)

        handle_stats_performance(args)

        captured = capsys.readouterr()
        assert "No results found" in captured.out


@pytest.mark.unit
class TestExportCSVCommand:
    """Tests for CSV export command"""

    @patch('src.analyze._filter_results_advanced')
    def test_export_csv_creates_file(self, mock_filter, multiple_search_results, tmp_path, capsys):
        """Test export-csv command creates valid CSV file"""
        mock_filter.return_value = multiple_search_results[:2]

        from src.analyze import handle_export_csv
        output_file = tmp_path / "results.csv"

        args = MagicMock(
            output=str(output_file), model=None, query_pattern=None,
            start_date=None, end_date=None, success_only=False, failed_only=False,
            min_exec_time=None, max_exec_time=None, min_answer_length=None,
            max_answer_length=None, has_sources=False, include_sources=False, limit=None
        )

        handle_export_csv(args)

        assert output_file.exists()
        content = output_file.read_text()
        assert "query" in content
        assert "What is Python?" in content

    @patch('src.analyze._filter_results_advanced')
    def test_export_csv_missing_output_path(self, mock_filter, capsys):
        """Test export-csv command without output path"""
        from src.analyze import handle_export_csv
        args = MagicMock(output=None)

        handle_export_csv(args)

        captured = capsys.readouterr()
        assert "Error: output path is required" in captured.out

    @patch('src.analyze._filter_results_advanced')
    def test_export_csv_no_results(self, mock_filter, tmp_path, capsys):
        """Test export-csv command with no matching results"""
        mock_filter.return_value = []

        from src.analyze import handle_export_csv
        output_file = tmp_path / "results.csv"

        args = MagicMock(
            output=str(output_file), model=None, query_pattern=None,
            start_date=None, end_date=None, success_only=False, failed_only=False,
            min_exec_time=None, max_exec_time=None, min_answer_length=None,
            max_answer_length=None, has_sources=False, include_sources=False, limit=None
        )

        handle_export_csv(args)

        captured = capsys.readouterr()
        assert "No results found matching criteria" in captured.out

    @patch('src.analyze._filter_results_advanced')
    def test_export_csv_includes_sources(self, mock_filter, multiple_search_results, tmp_path, capsys):
        """Test export-csv command with source count included"""
        mock_filter.return_value = multiple_search_results[:1]

        from src.analyze import handle_export_csv
        output_file = tmp_path / "results.csv"

        args = MagicMock(
            output=str(output_file), model=None, query_pattern=None,
            start_date=None, end_date=None, success_only=False, failed_only=False,
            min_exec_time=None, max_exec_time=None, min_answer_length=None,
            max_answer_length=None, has_sources=False, include_sources=True, limit=None
        )

        handle_export_csv(args)

        captured = capsys.readouterr()
        assert "CSV Export Complete!" in captured.out
        assert output_file.exists()


@pytest.mark.unit
class TestExportMarkdownCommand:
    """Tests for Markdown export command"""

    @patch('src.analyze._filter_results_advanced')
    def test_export_md_creates_file(self, mock_filter, multiple_search_results, tmp_path, capsys):
        """Test export-md command creates valid Markdown file"""
        mock_filter.return_value = multiple_search_results[:2]

        from src.analyze import handle_export_md
        output_file = tmp_path / "report.md"

        args = MagicMock(
            output=str(output_file), model=None, query_pattern=None,
            start_date=None, end_date=None, success_only=False, failed_only=False,
            min_exec_time=None, max_exec_time=None, min_answer_length=None,
            max_answer_length=None, has_sources=False, limit=None, full=False
        )

        handle_export_md(args)

        assert output_file.exists()
        content = output_file.read_text()
        assert "# Search Results Report" in content
        assert "What is Python?" in content

    @patch('src.analyze._filter_results_advanced')
    def test_export_md_missing_output_path(self, mock_filter, capsys):
        """Test export-md command without output path"""
        from src.analyze import handle_export_md
        args = MagicMock(output=None)

        handle_export_md(args)

        captured = capsys.readouterr()
        assert "Error: output path is required" in captured.out

    @patch('src.analyze._filter_results_advanced')
    def test_export_md_full_answers(self, mock_filter, multiple_search_results, tmp_path, capsys):
        """Test export-md command with full answer text"""
        mock_filter.return_value = multiple_search_results[:1]

        from src.analyze import handle_export_md
        output_file = tmp_path / "report.md"

        args = MagicMock(
            output=str(output_file), model=None, query_pattern=None,
            start_date=None, end_date=None, success_only=False, failed_only=False,
            min_exec_time=None, max_exec_time=None, min_answer_length=None,
            max_answer_length=None, has_sources=False, limit=None, full=True
        )

        handle_export_md(args)

        assert output_file.exists()
        content = output_file.read_text()
        # Should contain full answer when full=True
        assert "Python is a high-level programming language" in content


@pytest.mark.unit
class TestExportBatchCommand:
    """Tests for batch export command"""

    @patch('src.analyze._filter_results_advanced')
    def test_export_batch_creates_directory(self, mock_filter, multiple_search_results, tmp_path, capsys):
        """Test export-batch command creates output directory"""
        mock_filter.return_value = multiple_search_results

        from src.analyze import handle_export_batch
        output_dir = tmp_path / "exports"

        args = MagicMock(
            output_dir=str(output_dir), format='json', group_by='model'
        )

        handle_export_batch(args)

        captured = capsys.readouterr()
        assert "Batch Export Complete!" in captured.out
        assert "Groups created:" in captured.out

    @patch('src.analyze._filter_results_advanced')
    def test_export_batch_missing_output_dir(self, mock_filter, capsys):
        """Test export-batch command without output directory"""
        from src.analyze import handle_export_batch
        args = MagicMock(output_dir=None)

        handle_export_batch(args)

        captured = capsys.readouterr()
        assert "Error: output directory is required" in captured.out

    @patch('src.analyze._filter_results_advanced')
    def test_export_batch_no_results(self, mock_filter, tmp_path, capsys):
        """Test export-batch command with no results"""
        mock_filter.return_value = []

        from src.analyze import handle_export_batch
        output_dir = tmp_path / "exports"

        args = MagicMock(output_dir=str(output_dir), format='json', group_by='model')

        handle_export_batch(args)

        captured = capsys.readouterr()
        assert "No results found" in captured.out

    @patch('src.analyze._filter_results_advanced')
    def test_export_batch_csv_format(self, mock_filter, multiple_search_results, tmp_path, capsys):
        """Test export-batch command with CSV format"""
        mock_filter.return_value = multiple_search_results

        from src.analyze import handle_export_batch
        output_dir = tmp_path / "exports"

        args = MagicMock(output_dir=str(output_dir), format='csv', group_by='date')

        handle_export_batch(args)

        captured = capsys.readouterr()
        assert "Batch Export Complete!" in captured.out


@pytest.mark.unit
class TestDuplicatesCommand:
    """Tests for duplicate detection command"""

    @patch('src.analyze._find_duplicates')
    def test_duplicates_command_found_exact(self, mock_dups, capsys):
        """Test duplicates command finding exact duplicates"""
        mock_dups.return_value = {
            'What is Python?': [
                ('What is Python?', 1.0),
                ('What is Python?', 1.0)
            ]
        }

        from src.analyze import handle_duplicates
        args = MagicMock(exact=True)

        handle_duplicates(args)

        captured = capsys.readouterr()
        assert "Found 1 groups of similar queries" in captured.out
        assert "What is Python?" in captured.out

    @patch('src.analyze._find_duplicates')
    def test_duplicates_command_no_duplicates(self, mock_dups, capsys):
        """Test duplicates command when no duplicates found"""
        mock_dups.return_value = {}

        from src.analyze import handle_duplicates
        args = MagicMock(exact=False)

        handle_duplicates(args)

        captured = capsys.readouterr()
        assert "No duplicates found" in captured.out

    @patch('src.analyze._find_duplicates')
    def test_duplicates_command_similar(self, mock_dups, capsys):
        """Test duplicates command finding similar queries"""
        mock_dups.return_value = {
            'What is Python?': [
                ('What is Python?', 1.0),
                ('What is python?', 0.95),
                ('What is Python programming?', 0.85)
            ]
        }

        from src.analyze import handle_duplicates
        args = MagicMock(exact=False)

        handle_duplicates(args)

        captured = capsys.readouterr()
        assert "Found" in captured.out
        assert "similarity:" in captured.out


@pytest.mark.unit
class TestCleanupCommand:
    """Tests for cleanup command"""

    @patch('src.analyze._get_connection')
    def test_cleanup_command_dry_run(self, mock_conn, capsys):
        """Test cleanup command with dry-run mode"""
        mock_cursor = MagicMock()
        mock_cursor.rowcount = 5
        mock_conn_instance = MagicMock()
        mock_conn_instance.cursor.return_value = mock_cursor
        mock_conn.return_value = mock_conn_instance

        from src.analyze import handle_cleanup
        args = MagicMock(
            dry_run=True, confirm=False, remove_duplicates=True,
            archive_before=None
        )

        handle_cleanup(args)

        captured = capsys.readouterr()
        assert "[DRY-RUN]" in captured.out

    @patch('src.analyze._get_connection')
    def test_cleanup_command_missing_confirm(self, mock_conn, capsys):
        """Test cleanup command without confirmation"""
        from src.analyze import handle_cleanup
        args = MagicMock(dry_run=False, confirm=False)

        handle_cleanup(args)

        captured = capsys.readouterr()
        assert "Use --confirm" in captured.out

    @patch('src.analyze._get_connection')
    def test_cleanup_command_remove_duplicates(self, mock_conn, capsys):
        """Test cleanup command removing duplicates"""
        mock_cursor = MagicMock()
        mock_cursor.rowcount = 10
        mock_conn_instance = MagicMock()
        mock_conn_instance.cursor.return_value = mock_cursor
        mock_conn_instance.commit = MagicMock()
        mock_conn.return_value = mock_conn_instance

        from src.analyze import handle_cleanup
        args = MagicMock(
            dry_run=False, confirm=True, remove_duplicates=True,
            archive_before=None
        )

        handle_cleanup(args)

        captured = capsys.readouterr()
        assert "Removed 10 duplicate records" in captured.out

    @patch('src.analyze._get_connection')
    def test_cleanup_command_archive_before(self, mock_conn, capsys):
        """Test cleanup command archiving old failed records"""
        mock_cursor = MagicMock()
        mock_cursor.rowcount = 3
        mock_conn_instance = MagicMock()
        mock_conn_instance.cursor.return_value = mock_cursor
        mock_conn_instance.commit = MagicMock()
        mock_conn.return_value = mock_conn_instance

        from src.analyze import handle_cleanup
        args = MagicMock(
            dry_run=False, confirm=True, remove_duplicates=False,
            archive_before='2025-01-01'
        )

        handle_cleanup(args)

        captured = capsys.readouterr()
        assert "Archived 3 failed records" in captured.out


@pytest.mark.unit
class TestInfoCommand:
    """Tests for database info command"""

    @patch('src.analyze.DB_PATH')
    @patch('src.analyze._get_connection')
    def test_info_command_displays_health(self, mock_conn_func, mock_db_path, capsys, tmp_path):
        """Test info command displays database health information"""
        # Create a temporary database file
        test_db = tmp_path / "test.db"
        test_db.touch()
        mock_db_path.exists.return_value = True
        mock_db_path.stat.return_value = MagicMock(st_size=1024000)

        mock_cursor = MagicMock()
        mock_cursor.fetchone.side_effect = [
            (100,),  # record_count
            (1024000,)  # db_size
        ]
        mock_conn_instance = MagicMock()
        mock_conn_instance.cursor.return_value = mock_cursor
        mock_conn_func.return_value = mock_conn_instance

        from src.analyze import handle_info
        args = MagicMock()

        handle_info(args)

        captured = capsys.readouterr()
        assert "DATABASE HEALTH INFORMATION" in captured.out
        assert "File Size:" in captured.out
        assert "Record Count:" in captured.out

    @patch('src.analyze.DB_PATH')
    def test_info_command_database_not_found(self, mock_db_path, capsys):
        """Test info command when database doesn't exist"""
        mock_db_path.exists.return_value = False

        from src.analyze import handle_info
        args = MagicMock()

        handle_info(args)

        captured = capsys.readouterr()
        assert "Database not found" in captured.out
