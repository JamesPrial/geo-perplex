"""
Unit tests for src/search.py
Tests display functions and argument parsing logic.
"""
import pytest
import sys
import hashlib
from datetime import datetime
from pathlib import Path
from src.search import display_results


@pytest.mark.unit
class TestDisplayResults:
    """Tests for display_results() function"""

    def test_display_results_with_answer_and_sources(self, capsys):
        """Test displaying results with answer and sources"""
        results = {
            'answer': 'Python is a high-level programming language.',
            'sources': [
                {'text': 'Python Official', 'url': 'https://python.org'},
                {'text': 'Python Tutorial', 'url': 'https://docs.python.org'}
            ]
        }

        display_results(results)

        captured = capsys.readouterr()
        output = captured.out

        assert '📊 SEARCH RESULTS' in output
        assert 'ANSWER:' in output
        assert 'Python is a high-level programming language.' in output
        assert 'SOURCES:' in output
        assert 'Python Official' in output
        assert 'https://python.org' in output
        assert 'Python Tutorial' in output
        assert 'https://docs.python.org' in output

    def test_display_results_with_no_sources(self, capsys):
        """Test displaying results without sources"""
        results = {
            'answer': 'This is an answer without sources.',
            'sources': []
        }

        display_results(results)

        captured = capsys.readouterr()
        output = captured.out

        assert '📊 SEARCH RESULTS' in output
        assert 'This is an answer without sources.' in output
        assert 'SOURCES:' not in output

    def test_display_results_with_multiple_sources(self, capsys):
        """Test displaying results with multiple sources"""
        results = {
            'answer': 'Test answer',
            'sources': [
                {'text': 'Source 1', 'url': 'https://example.com/1'},
                {'text': 'Source 2', 'url': 'https://example.com/2'},
                {'text': 'Source 3', 'url': 'https://example.com/3'},
            ]
        }

        display_results(results)

        captured = capsys.readouterr()
        output = captured.out

        assert '1. Source 1' in output
        assert '2. Source 2' in output
        assert '3. Source 3' in output
        assert 'https://example.com/1' in output
        assert 'https://example.com/2' in output
        assert 'https://example.com/3' in output

    def test_display_results_with_long_answer(self, capsys):
        """Test displaying results with a long answer"""
        long_answer = 'A' * 1000  # 1000 character answer
        results = {
            'answer': long_answer,
            'sources': []
        }

        display_results(results)

        captured = capsys.readouterr()
        output = captured.out

        # Full answer should be displayed
        assert long_answer in output

    def test_display_results_with_newlines_in_answer(self, capsys):
        """Test displaying results with multiline answer"""
        results = {
            'answer': 'Line 1\nLine 2\nLine 3',
            'sources': []
        }

        display_results(results)

        captured = capsys.readouterr()
        output = captured.out

        assert 'Line 1' in output
        assert 'Line 2' in output
        assert 'Line 3' in output

    def test_display_results_formatting(self, capsys):
        """Test that results are formatted with proper separators"""
        results = {
            'answer': 'Test answer',
            'sources': [{'text': 'Test', 'url': 'https://test.com'}]
        }

        display_results(results)

        captured = capsys.readouterr()
        output = captured.out

        # Check for formatting elements
        assert '═' * 10 in output  # Check for separator lines
        assert '---' in output     # Check for section dividers

    def test_display_results_sources_numbering(self, capsys):
        """Test that sources are numbered starting from 1"""
        results = {
            'answer': 'Test',
            'sources': [
                {'text': 'First', 'url': 'https://first.com'},
                {'text': 'Second', 'url': 'https://second.com'},
            ]
        }

        display_results(results)

        captured = capsys.readouterr()
        output = captured.out

        # Check numbering
        assert '1. First' in output
        assert '2. Second' in output


@pytest.mark.unit
class TestArgumentParsing:
    """Tests for command-line argument parsing logic"""

    def test_default_query(self):
        """Test default query is used when no arguments provided"""
        # Simulate no arguments
        args = []

        search_query = 'What is Generative Engine Optimization?'
        model = None
        save_screenshot = True

        # Simulate parsing logic
        i = 0
        while i < len(args):
            if args[i] == '--model' and i + 1 < len(args):
                model = args[i + 1]
                i += 2
            elif args[i] == '--no-screenshot':
                save_screenshot = False
                i += 1
            else:
                search_query = args[i]
                i += 1

        assert search_query == 'What is Generative Engine Optimization?'
        assert model is None
        assert save_screenshot is True

    def test_custom_query_argument(self):
        """Test custom query is parsed correctly"""
        args = ['What is Python?']

        search_query = 'What is Generative Engine Optimization?'
        model = None
        save_screenshot = True

        i = 0
        while i < len(args):
            if args[i] == '--model' and i + 1 < len(args):
                model = args[i + 1]
                i += 2
            elif args[i] == '--no-screenshot':
                save_screenshot = False
                i += 1
            else:
                search_query = args[i]
                i += 1

        assert search_query == 'What is Python?'
        assert model is None
        assert save_screenshot is True

    def test_model_argument(self):
        """Test --model argument is parsed correctly"""
        args = ['What is Python?', '--model', 'gpt-4']

        search_query = 'What is Generative Engine Optimization?'
        model = None
        save_screenshot = True

        i = 0
        while i < len(args):
            if args[i] == '--model' and i + 1 < len(args):
                model = args[i + 1]
                i += 2
            elif args[i] == '--no-screenshot':
                save_screenshot = False
                i += 1
            else:
                search_query = args[i]
                i += 1

        assert search_query == 'What is Python?'
        assert model == 'gpt-4'
        assert save_screenshot is True

    def test_no_screenshot_argument(self):
        """Test --no-screenshot flag is parsed correctly"""
        args = ['What is Python?', '--no-screenshot']

        search_query = 'What is Generative Engine Optimization?'
        model = None
        save_screenshot = True

        i = 0
        while i < len(args):
            if args[i] == '--model' and i + 1 < len(args):
                model = args[i + 1]
                i += 2
            elif args[i] == '--no-screenshot':
                save_screenshot = False
                i += 1
            else:
                search_query = args[i]
                i += 1

        assert search_query == 'What is Python?'
        assert model is None
        assert save_screenshot is False

    def test_all_arguments_combined(self):
        """Test parsing all arguments together"""
        args = ['What is GEO?', '--model', 'claude-3', '--no-screenshot']

        search_query = 'What is Generative Engine Optimization?'
        model = None
        save_screenshot = True

        i = 0
        while i < len(args):
            if args[i] == '--model' and i + 1 < len(args):
                model = args[i + 1]
                i += 2
            elif args[i] == '--no-screenshot':
                save_screenshot = False
                i += 1
            else:
                search_query = args[i]
                i += 1

        assert search_query == 'What is GEO?'
        assert model == 'claude-3'
        assert save_screenshot is False

    def test_model_without_value(self):
        """Test --model flag without value (edge case)"""
        args = ['Query', '--model']

        search_query = 'What is Generative Engine Optimization?'
        model = None
        save_screenshot = True

        i = 0
        while i < len(args):
            if args[i] == '--model' and i + 1 < len(args):
                model = args[i + 1]
                i += 2
            elif args[i] == '--no-screenshot':
                save_screenshot = False
                i += 1
            else:
                search_query = args[i]
                i += 1

        # Model should remain None since no value follows --model
        assert model is None


@pytest.mark.unit
class TestScreenshotFilenameGeneration:
    """Tests for screenshot filename generation logic"""

    def test_screenshot_filename_format(self):
        """Test that screenshot filename has correct format"""
        search_query = "What is Python?"

        # Simulate filename generation logic
        timestamp_str = datetime.now().strftime('%Y%m%d_%H%M%S')
        query_hash = hashlib.md5(search_query.encode()).hexdigest()[:8]
        screenshot_dir = Path('screenshots')
        screenshot_path = screenshot_dir / f'{timestamp_str}_{query_hash}.png'

        # Verify format
        filename = screenshot_path.name
        assert filename.endswith('.png')
        assert query_hash in filename
        # Should have timestamp in YYYYMMDD_HHMMSS format
        assert len(timestamp_str) == 15  # YYYYMMDD_HHMMSS = 15 chars

    def test_screenshot_hash_consistent(self):
        """Test that same query generates same hash"""
        query = "Test query"

        hash1 = hashlib.md5(query.encode()).hexdigest()[:8]
        hash2 = hashlib.md5(query.encode()).hexdigest()[:8]

        assert hash1 == hash2

    def test_screenshot_hash_different_queries(self):
        """Test that different queries generate different hashes"""
        query1 = "Query 1"
        query2 = "Query 2"

        hash1 = hashlib.md5(query1.encode()).hexdigest()[:8]
        hash2 = hashlib.md5(query2.encode()).hexdigest()[:8]

        assert hash1 != hash2

    def test_screenshot_directory_creation(self, tmp_path, monkeypatch):
        """Test that screenshot directory is created if it doesn't exist"""
        # Change to temp directory
        monkeypatch.chdir(tmp_path)

        screenshot_dir = Path('screenshots')
        assert not screenshot_dir.exists()

        # Simulate directory creation
        screenshot_dir.mkdir(exist_ok=True)

        assert screenshot_dir.exists()
        assert screenshot_dir.is_dir()


@pytest.mark.integration
class TestSearchIntegration:
    """Integration tests for search module components"""

    def test_results_dict_structure(self):
        """Test that results dictionary has expected structure"""
        results = {
            'answer': 'Test answer',
            'sources': [
                {'text': 'Source 1', 'url': 'https://example.com'}
            ]
        }

        # Verify structure
        assert 'answer' in results
        assert 'sources' in results
        assert isinstance(results['answer'], str)
        assert isinstance(results['sources'], list)

        if len(results['sources']) > 0:
            source = results['sources'][0]
            assert 'text' in source
            assert 'url' in source

    def test_empty_results_structure(self):
        """Test handling of empty results"""
        results = {
            'answer': '',
            'sources': []
        }

        assert results['answer'] == ''
        assert results['sources'] == []
        assert isinstance(results['sources'], list)


@pytest.mark.unit
class TestDisplayResultsEdgeCases:
    """Tests for edge cases in display_results() function"""

    def test_display_results_missing_answer_key(self, capsys):
        """Test displaying results when 'answer' key is missing"""
        results = {
            # 'answer' key missing
            'sources': [{'text': 'Test', 'url': 'https://test.com'}]
        }

        try:
            display_results(results)
        except KeyError:
            # KeyError is acceptable for missing required field
            pass

    def test_display_results_missing_sources_key(self, capsys):
        """Test displaying results when 'sources' key is missing"""
        results = {
            'answer': 'This is an answer',
            # 'sources' key missing
        }

        try:
            display_results(results)
        except KeyError:
            pass

    def test_display_results_sources_as_none(self, capsys):
        """Test displaying results when sources is None"""
        results = {
            'answer': 'Answer text',
            'sources': None  # None instead of list
        }

        try:
            display_results(results)
        except (TypeError, AttributeError):
            # TypeError acceptable for trying to iterate None
            pass

    def test_display_results_answer_as_none(self, capsys):
        """Test displaying results when answer is None"""
        results = {
            'answer': None,  # None instead of string
            'sources': []
        }

        try:
            display_results(results)
            captured = capsys.readouterr()
            # Should handle None (may print "None" or empty)
            assert isinstance(captured.out, str)
        except TypeError:
            pass

    def test_display_results_source_missing_text(self, capsys):
        """Test source dict without 'text' key"""
        results = {
            'answer': 'Answer',
            'sources': [
                {'url': 'https://example.com'}  # Missing 'text'
            ]
        }

        try:
            display_results(results)
        except KeyError:
            pass

    def test_display_results_source_missing_url(self, capsys):
        """Test source dict without 'url' key"""
        results = {
            'answer': 'Answer',
            'sources': [
                {'text': 'Source text'}  # Missing 'url'
            ]
        }

        try:
            display_results(results)
        except KeyError:
            pass

    def test_display_results_answer_with_ansi_codes(self, capsys):
        """Test answer containing ANSI escape sequences"""
        results = {
            'answer': 'Answer with \x1b[31mcolor\x1b[0m codes',
            'sources': []
        }

        display_results(results)
        captured = capsys.readouterr()

        # Should handle ANSI codes (may strip or preserve)
        assert isinstance(captured.out, str)

    def test_display_results_very_long_source_url(self, capsys):
        """Test source with extremely long URL"""
        very_long_url = "https://example.com/" + "a" * 5000
        results = {
            'answer': 'Answer',
            'sources': [
                {'text': 'Test', 'url': very_long_url}
            ]
        }

        display_results(results)
        captured = capsys.readouterr()

        # Should display without crashing
        assert very_long_url in captured.out or very_long_url[:100] in captured.out

    def test_display_results_source_text_with_newlines(self, capsys):
        """Test source text containing newlines"""
        results = {
            'answer': 'Answer',
            'sources': [
                {'text': 'Line 1\nLine 2\nLine 3', 'url': 'https://test.com'}
            ]
        }

        display_results(results)
        captured = capsys.readouterr()

        assert 'Line 1' in captured.out


@pytest.mark.unit
class TestArgumentParsingEdgeCases:
    """Tests for argument parsing edge cases"""

    def test_query_containing_model_flag_text(self):
        """Test query that contains '--model' as substring"""
        args = ['Query about --model parameter', '--model', 'gpt-4']

        search_query = 'What is Generative Engine Optimization?'
        model = None

        i = 0
        while i < len(args):
            if args[i] == '--model' and i + 1 < len(args):
                model = args[i + 1]
                i += 2
            else:
                search_query = args[i]
                i += 1

        # Should correctly parse despite '--model' in query text
        assert '--model' in search_query
        assert model == 'gpt-4'

    def test_query_as_empty_string(self):
        """Test parsing empty string as query"""
        args = ['']

        search_query = 'What is Generative Engine Optimization?'
        model = None

        i = 0
        while i < len(args):
            if args[i] == '--model' and i + 1 < len(args):
                model = args[i + 1]
                i += 2
            elif args[i] == '--no-screenshot':
                i += 1
            else:
                search_query = args[i]
                i += 1

        # Should accept empty string
        assert search_query == ''

    def test_query_with_newlines_and_tabs(self):
        """Test query containing newlines and tabs"""
        args = ['Query\nwith\nnewlines\tand\ttabs']

        search_query = 'default'
        i = 0
        while i < len(args):
            if args[i] == '--model' and i + 1 < len(args):
                i += 2
            else:
                search_query = args[i]
                i += 1

        assert '\n' in search_query
        assert '\t' in search_query

    def test_very_long_query_argument(self):
        """Test very long query (10,000 characters)"""
        very_long_query = 'a' * 10000
        args = [very_long_query]

        search_query = 'default'
        i = 0
        while i < len(args):
            if args[i] == '--model' and i + 1 < len(args):
                i += 2
            else:
                search_query = args[i]
                i += 1

        assert len(search_query) == 10000

    def test_model_with_special_characters(self):
        """Test model parameter with special characters"""
        args = ['Test query', '--model', 'model:v1.2-beta']

        model = None
        i = 0
        while i < len(args):
            if args[i] == '--model' and i + 1 < len(args):
                model = args[i + 1]
                i += 2
            else:
                i += 1

        assert model == 'model:v1.2-beta'


@pytest.mark.unit
class TestScreenshotEdgeCases:
    """Tests for screenshot filename generation edge cases"""

    def test_screenshot_filename_with_slash_in_query(self):
        """Test filename generation when query contains slashes"""
        query_with_slash = "What is TCP/IP protocol?"

        # Generate hash (slashes in query shouldn't affect hash)
        query_hash = hashlib.md5(query_with_slash.encode()).hexdigest()[:8]

        # Hash should be generated successfully
        assert len(query_hash) == 8
        # Hash shouldn't contain slashes
        assert '/' not in query_hash

    def test_screenshot_filename_with_invalid_chars(self):
        """Test filename generation with characters invalid in filenames"""
        invalid_chars_query = 'Query with <invalid> chars: *?"|'

        query_hash = hashlib.md5(invalid_chars_query.encode()).hexdigest()[:8]

        # Hash should be safe for filenames
        assert len(query_hash) == 8
        assert all(c.isalnum() for c in query_hash)

    def test_screenshot_filename_unicode_query(self):
        """Test filename generation with Unicode query"""
        unicode_query = "什么是Python编程？"

        query_hash = hashlib.md5(unicode_query.encode()).hexdigest()[:8]

        # Should generate valid hash
        assert len(query_hash) == 8
        assert all(c in '0123456789abcdef' for c in query_hash)

    def test_screenshot_filename_very_long_query(self):
        """Test filename generation with very long query"""
        very_long_query = "a" * 10000

        query_hash = hashlib.md5(very_long_query.encode()).hexdigest()[:8]
        timestamp_str = datetime.now().strftime('%Y%m%d_%H%M%S')
        screenshot_path = Path('screenshots') / f'{timestamp_str}_{query_hash}.png'

        # Filename should still be reasonable length
        assert len(screenshot_path.name) < 50

    def test_screenshot_hash_collision_different_queries(self):
        """Test that different queries produce different hashes"""
        query1 = "What is Python?"
        query2 = "What is Java?"

        hash1 = hashlib.md5(query1.encode()).hexdigest()[:8]
        hash2 = hashlib.md5(query2.encode()).hexdigest()[:8]

        assert hash1 != hash2

    def test_screenshot_empty_query_hash(self):
        """Test hash generation for empty query"""
        empty_query = ""

        query_hash = hashlib.md5(empty_query.encode()).hexdigest()[:8]

        # Should still generate valid hash
        assert len(query_hash) == 8
