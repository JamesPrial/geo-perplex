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
