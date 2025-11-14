"""
Comprehensive unit tests for src/utils/prompts_loader module.

Tests cover all functions and error paths including:
- Loading valid prompts from files and stdin
- Validation of required and optional fields
- Type checking and whitespace handling
- Error messages with context information
- Integration with MODEL_MAPPING from config
"""

import pytest
import json
from io import StringIO
from pathlib import Path
from unittest.mock import patch

from src.utils.prompts_loader import (
    load_prompts_from_file,
    validate_prompt,
    PromptsLoadError,
    PROMPTS_FILE_CONFIG,
)


# ============================================================================
# Fixtures
# ============================================================================

@pytest.fixture
def valid_prompts_data():
    """Sample valid prompts data for testing."""
    return [
        {"query": "What is GEO?"},
        {"query": "Best CRM tools", "model": "gpt-4"},
        {"query": "How does RAG work?", "model": "claude-3", "no_screenshot": True},
    ]


@pytest.fixture
def create_prompts_file(tmp_path):
    """Helper fixture to create temporary prompts JSON file."""
    def _create(data):
        file_path = tmp_path / "prompts.json"
        with open(file_path, 'w') as f:
            json.dump(data, f)
        return str(file_path)
    return _create


# ============================================================================
# TestLoadPromptsFromFile - Happy Path Tests
# ============================================================================

@pytest.mark.unit
class TestLoadPromptsFromFile:
    """Tests for load_prompts_from_file function"""

    def test_load_valid_single_prompt(self, create_prompts_file):
        """Test loading file with single valid prompt"""
        file_path = create_prompts_file([{"query": "What is AI?"}])
        prompts = load_prompts_from_file(file_path)

        assert len(prompts) == 1
        assert prompts[0]['query'] == "What is AI?"
        assert 'model' not in prompts[0]
        assert 'no_screenshot' not in prompts[0]

    def test_load_valid_multiple_prompts(self, create_prompts_file, valid_prompts_data):
        """Test loading file with multiple valid prompts"""
        file_path = create_prompts_file(valid_prompts_data)
        prompts = load_prompts_from_file(file_path)

        assert len(prompts) == 3
        assert prompts[0]['query'] == "What is GEO?"
        assert prompts[1]['query'] == "Best CRM tools"
        assert prompts[2]['query'] == "How does RAG work?"

    def test_load_prompts_with_all_fields(self, create_prompts_file):
        """Test prompts with query, model, and no_screenshot fields"""
        data = [
            {
                "query": "Test query",
                "model": "gpt-4",
                "no_screenshot": True
            }
        ]
        file_path = create_prompts_file(data)
        prompts = load_prompts_from_file(file_path)

        assert len(prompts) == 1
        assert prompts[0]['query'] == "Test query"
        assert prompts[0]['model'] == "gpt-4"
        assert prompts[0]['no_screenshot'] is True

    def test_load_prompts_with_optional_fields_only(self, create_prompts_file):
        """Test prompts with only required query field"""
        data = [
            {"query": "Query 1"},
            {"query": "Query 2"},
        ]
        file_path = create_prompts_file(data)
        prompts = load_prompts_from_file(file_path)

        assert len(prompts) == 2
        assert all('query' in p for p in prompts)
        assert not any('model' in p for p in prompts)
        assert not any('no_screenshot' in p for p in prompts)

    def test_query_whitespace_trimming(self, create_prompts_file):
        """Test query strings are trimmed of leading/trailing whitespace"""
        data = [
            {"query": "  What is AI?  "},
            {"query": "\tHow does ML work?\n"},
            {"query": "  \n  Trim me  \t  "},
        ]
        file_path = create_prompts_file(data)
        prompts = load_prompts_from_file(file_path)

        assert prompts[0]['query'] == "What is AI?"
        assert prompts[1]['query'] == "How does ML work?"
        assert prompts[2]['query'] == "Trim me"

    def test_load_from_stdin(self, monkeypatch):
        """Test loading prompts from stdin when path is '-'"""
        stdin_data = json.dumps([
            {"query": "From stdin query"},
            {"query": "Another stdin query", "model": "claude-3"}
        ])
        monkeypatch.setattr('sys.stdin', StringIO(stdin_data))

        prompts = load_prompts_from_file('-')

        assert len(prompts) == 2
        assert prompts[0]['query'] == "From stdin query"
        assert prompts[1]['model'] == "claude-3"

    def test_all_valid_models_accepted(self, create_prompts_file):
        """Test that all models in MODEL_MAPPING are accepted"""
        models_to_test = ['gpt-4', 'gpt-4-turbo', 'claude', 'claude-3',
                         'claude-opus', 'claude-sonnet', 'sonar', 'sonar-pro',
                         'gemini', 'default']
        data = [{"query": f"Test {model}", "model": model} for model in models_to_test]
        file_path = create_prompts_file(data)

        prompts = load_prompts_from_file(file_path)

        assert len(prompts) == len(models_to_test)
        for i, model in enumerate(models_to_test):
            assert prompts[i]['model'] == model

    def test_no_screenshot_false_preserved(self, create_prompts_file):
        """Test that no_screenshot=False is preserved"""
        data = [{"query": "Test", "no_screenshot": False}]
        file_path = create_prompts_file(data)

        prompts = load_prompts_from_file(file_path)

        assert prompts[0]['no_screenshot'] is False

    def test_load_max_prompts_exactly_1000(self, create_prompts_file):
        """Test loading exactly 1000 prompts (at limit)"""
        data = [{"query": f"Query {i}"} for i in range(1000)]
        file_path = create_prompts_file(data)

        prompts = load_prompts_from_file(file_path)

        assert len(prompts) == 1000


# ============================================================================
# TestLoadPromptsFromFile - Error Path Tests
# ============================================================================

    def test_file_not_found_error(self):
        """Test clear error when file doesn't exist"""
        with pytest.raises(PromptsLoadError, match=r"File not found.*nonexistent\.json"):
            load_prompts_from_file("/nonexistent/path/to/nonexistent.json")

    def test_invalid_json_syntax_error(self, create_prompts_file):
        """Test error handling for malformed JSON"""
        malformed_file = Path(create_prompts_file([]))
        malformed_file.write_text("{ invalid json }")

        with pytest.raises(PromptsLoadError, match=r"Invalid JSON syntax"):
            load_prompts_from_file(str(malformed_file))

    def test_not_a_list_error(self, create_prompts_file):
        """Test error when JSON is not an array"""
        malformed_file = Path(create_prompts_file([]))
        malformed_file.write_text('{"query": "This is a dict, not a list"}')

        with pytest.raises(
            PromptsLoadError,
            match=r"Prompts must be a JSON array"
        ):
            load_prompts_from_file(str(malformed_file))

    def test_not_a_list_error_with_dict(self, create_prompts_file):
        """Test error when JSON is a dictionary instead of array"""
        malformed_file = Path(create_prompts_file([]))
        malformed_file.write_text('{"query": "single query"}')

        with pytest.raises(PromptsLoadError, match=r"got dict"):
            load_prompts_from_file(str(malformed_file))

    def test_empty_list_error(self, create_prompts_file):
        """Test error when file contains empty array"""
        file_path = create_prompts_file([])

        with pytest.raises(PromptsLoadError, match=r"Prompts file is empty array"):
            load_prompts_from_file(file_path)

    def test_too_many_prompts_error(self, create_prompts_file):
        """Test max prompts limit enforcement (>1000)"""
        data = [{"query": f"Query {i}"} for i in range(1001)]
        file_path = create_prompts_file(data)

        with pytest.raises(PromptsLoadError, match=r"Too many prompts.*exceeds maximum"):
            load_prompts_from_file(file_path)

    def test_missing_query_field_error(self, create_prompts_file):
        """Test error when prompt missing query field"""
        data = [{"model": "gpt-4"}]
        file_path = create_prompts_file(data)

        with pytest.raises(
            PromptsLoadError,
            match=r"Prompt at index 0.*missing required field: query"
        ):
            load_prompts_from_file(file_path)

    def test_missing_query_field_error_with_index(self, create_prompts_file):
        """Test error message includes correct index for missing query"""
        data = [
            {"query": "Valid"},
            {"model": "gpt-4"},  # Missing query at index 1
        ]
        file_path = create_prompts_file(data)

        with pytest.raises(PromptsLoadError, match=r"index 1.*missing required field"):
            load_prompts_from_file(file_path)

    def test_empty_query_string_error(self, create_prompts_file):
        """Test error when query is empty string"""
        data = [{"query": ""}]
        file_path = create_prompts_file(data)

        with pytest.raises(
            PromptsLoadError,
            match=r"query cannot be empty or whitespace-only"
        ):
            load_prompts_from_file(file_path)

    def test_whitespace_only_query_error(self, create_prompts_file):
        """Test error when query is only whitespace"""
        data = [{"query": "   \n\t   "}]
        file_path = create_prompts_file(data)

        with pytest.raises(PromptsLoadError, match=r"whitespace-only"):
            load_prompts_from_file(file_path)

    def test_invalid_model_name_error(self, create_prompts_file):
        """Test error for model not in MODEL_MAPPING"""
        data = [{"query": "Test", "model": "invalid-model"}]
        file_path = create_prompts_file(data)

        with pytest.raises(
            PromptsLoadError,
            match=r'model "invalid-model" not in MODEL_MAPPING'
        ):
            load_prompts_from_file(file_path)

    def test_invalid_model_name_lists_available_models(self, create_prompts_file):
        """Test error message includes list of available models"""
        data = [{"query": "Test", "model": "bad-model"}]
        file_path = create_prompts_file(data)

        with pytest.raises(PromptsLoadError, match=r"Available models:.*gpt-4"):
            load_prompts_from_file(file_path)

    def test_invalid_no_screenshot_type_error(self, create_prompts_file):
        """Test error when no_screenshot is not boolean"""
        data = [{"query": "Test", "no_screenshot": "true"}]  # String instead of bool
        file_path = create_prompts_file(data)

        with pytest.raises(
            PromptsLoadError,
            match=r"no_screenshot must be a boolean.*got str"
        ):
            load_prompts_from_file(file_path)

    def test_invalid_no_screenshot_with_int(self, create_prompts_file):
        """Test error when no_screenshot is an integer"""
        data = [{"query": "Test", "no_screenshot": 1}]
        file_path = create_prompts_file(data)

        with pytest.raises(PromptsLoadError, match=r"no_screenshot must be a boolean"):
            load_prompts_from_file(file_path)

    def test_query_not_string_error(self, create_prompts_file):
        """Test error when query is not a string"""
        data = [{"query": 123}]  # Integer instead of string
        file_path = create_prompts_file(data)

        with pytest.raises(
            PromptsLoadError,
            match=r"query must be a string"
        ):
            load_prompts_from_file(file_path)

    def test_model_not_string_error(self, create_prompts_file):
        """Test error when model is not a string"""
        data = [{"query": "Test", "model": 123}]
        file_path = create_prompts_file(data)

        with pytest.raises(PromptsLoadError, match=r"model must be a string"):
            load_prompts_from_file(file_path)

    def test_prompt_not_dict_error(self, create_prompts_file):
        """Test error when prompt is not a dictionary"""
        malformed_file = Path(create_prompts_file([]))
        malformed_file.write_text('["not a dict", "also not a dict"]')

        with pytest.raises(
            PromptsLoadError,
            match=r"Prompt at index 0.*must be a dictionary"
        ):
            load_prompts_from_file(str(malformed_file))

    def test_stdin_empty_error(self, monkeypatch):
        """Test error when stdin is empty"""
        monkeypatch.setattr('sys.stdin', StringIO(""))

        with pytest.raises(PromptsLoadError, match=r"stdin is empty"):
            load_prompts_from_file('-')

    def test_stdin_whitespace_only_error(self, monkeypatch):
        """Test error when stdin contains only whitespace"""
        monkeypatch.setattr('sys.stdin', StringIO("   \n\t   "))

        with pytest.raises(PromptsLoadError, match=r"stdin is empty"):
            load_prompts_from_file('-')

    def test_stdin_invalid_json_error(self, monkeypatch):
        """Test error when stdin has invalid JSON"""
        monkeypatch.setattr('sys.stdin', StringIO("{ bad json }"))

        with pytest.raises(PromptsLoadError, match=r"Invalid JSON syntax"):
            load_prompts_from_file('-')


# ============================================================================
# TestValidatePrompt - Happy Path Tests
# ============================================================================

@pytest.mark.unit
class TestValidatePrompt:
    """Tests for validate_prompt function"""

    def test_valid_prompt_with_all_fields(self):
        """Test validation passes for complete prompt"""
        prompt = {
            "query": "Test query",
            "model": "gpt-4",
            "no_screenshot": True
        }

        result = validate_prompt(prompt, 0)

        # validate_prompt modifies prompt in place and returns it
        assert result['query'] == "Test query"
        assert result['model'] == "gpt-4"
        assert result['no_screenshot'] is True
        assert prompt is result  # Same object

    def test_valid_prompt_with_only_query(self):
        """Test validation passes for minimal prompt"""
        prompt = {"query": "Minimal query"}

        result = validate_prompt(prompt, 0)

        assert result['query'] == "Minimal query"
        assert 'model' not in result
        assert 'no_screenshot' not in result

    def test_query_trimming_with_spaces(self):
        """Test query is trimmed of leading/trailing spaces"""
        prompt = {"query": "  Test query  "}

        result = validate_prompt(prompt, 0)

        # Query is trimmed in place
        assert result['query'] == "Test query"
        assert prompt['query'] == "Test query"  # Modified in place

    def test_query_trimming_with_tabs_and_newlines(self):
        """Test query is trimmed of tabs and newlines"""
        prompt = {"query": "\t\nTest query\n\t"}

        result = validate_prompt(prompt, 0)

        assert result['query'] == "Test query"

    def test_internal_whitespace_preserved(self):
        """Test internal whitespace in query is preserved"""
        prompt = {"query": "  Multi word  test  query  "}

        result = validate_prompt(prompt, 0)

        assert result['query'] == "Multi word  test  query"

    def test_no_screenshot_false(self):
        """Test no_screenshot=False is preserved"""
        prompt = {"query": "Test", "no_screenshot": False}

        result = validate_prompt(prompt, 0)

        assert result['no_screenshot'] is False

    def test_model_whitespace_trimmed(self):
        """Test model names are trimmed of whitespace"""
        prompt = {"query": "Test", "model": "  gpt-4  "}

        result = validate_prompt(prompt, 0)

        # Model is trimmed in place
        assert result['model'] == "gpt-4"
        assert prompt['model'] == "gpt-4"  # Modified in place


# ============================================================================
# TestValidatePrompt - Error Path Tests
# ============================================================================

    def test_missing_query_field_raises_error(self):
        """Test ValueError raised when query missing"""
        prompt = {"model": "gpt-4"}

        with pytest.raises(PromptsLoadError, match=r"missing required field: query"):
            validate_prompt(prompt, 0)

    def test_empty_query_raises_error(self):
        """Test ValueError raised when query is empty"""
        prompt = {"query": ""}

        with pytest.raises(PromptsLoadError, match=r"whitespace-only"):
            validate_prompt(prompt, 0)

    def test_whitespace_only_query_raises_error(self):
        """Test error when query is only whitespace"""
        prompt = {"query": "   \t\n   "}

        with pytest.raises(PromptsLoadError, match=r"whitespace-only"):
            validate_prompt(prompt, 5)

    def test_invalid_model_raises_error(self):
        """Test ValueError raised for invalid model"""
        prompt = {"query": "Test", "model": "nonexistent"}

        with pytest.raises(PromptsLoadError, match=r"not in MODEL_MAPPING"):
            validate_prompt(prompt, 0)

    def test_invalid_no_screenshot_type_raises_error(self):
        """Test ValueError raised when no_screenshot not boolean"""
        prompt = {"query": "Test", "no_screenshot": "yes"}

        with pytest.raises(PromptsLoadError, match=r"no_screenshot must be a boolean"):
            validate_prompt(prompt, 0)

    def test_error_message_includes_index(self):
        """Test error messages include prompt index for debugging"""
        prompt = {"query": "Test", "model": "bad"}

        with pytest.raises(PromptsLoadError, match=r"index 7"):
            validate_prompt(prompt, 7)

    def test_error_includes_index_for_missing_query(self):
        """Test index is included in missing query error"""
        prompt = {"model": "gpt-4"}

        with pytest.raises(PromptsLoadError, match=r"index 3"):
            validate_prompt(prompt, 3)

    def test_prompt_not_dict_raises_error(self):
        """Test error when prompt is not a dictionary"""
        with pytest.raises(PromptsLoadError, match=r"must be a dictionary"):
            validate_prompt("not a dict", 0)

    def test_prompt_none_raises_error(self):
        """Test error when prompt is None"""
        with pytest.raises(PromptsLoadError, match=r"NoneType"):
            validate_prompt(None, 0)

    def test_query_not_string_raises_error(self):
        """Test error when query is not a string"""
        prompt = {"query": 123}

        with pytest.raises(PromptsLoadError, match=r"query must be a string"):
            validate_prompt(prompt, 0)

    def test_model_not_string_raises_error(self):
        """Test error when model is not a string"""
        prompt = {"query": "Test", "model": 123}

        with pytest.raises(PromptsLoadError, match=r"model must be a string"):
            validate_prompt(prompt, 0)

    def test_error_lists_available_models(self):
        """Test error for invalid model lists available options"""
        prompt = {"query": "Test", "model": "bad-model"}

        with pytest.raises(PromptsLoadError, match=r"Available models:.*gpt-4"):
            validate_prompt(prompt, 0)


# ============================================================================
# Integration Tests
# ============================================================================

@pytest.mark.unit
class TestPromptsLoaderIntegration:
    """Integration tests for the prompts loader module"""

    def test_complex_valid_file(self, create_prompts_file):
        """Test loading a complex valid file with mixed prompts"""
        data = [
            {"query": "Simple query"},
            {"query": "Query with model", "model": "claude-3"},
            {"query": "Query with screenshot disabled", "no_screenshot": True},
            {
                "query": "All fields",
                "model": "sonar-pro",
                "no_screenshot": False
            },
            {"query": "  Whitespace query  ", "model": "  gpt-4  "},
        ]
        file_path = create_prompts_file(data)

        prompts = load_prompts_from_file(file_path)

        assert len(prompts) == 5
        assert prompts[0]['query'] == "Simple query"
        assert prompts[1]['model'] == "claude-3"
        assert prompts[2]['no_screenshot'] is True
        assert prompts[3]['no_screenshot'] is False
        assert prompts[4]['query'] == "Whitespace query"
        assert prompts[4]['model'] == "gpt-4"

    def test_error_stops_at_first_invalid_prompt(self, create_prompts_file):
        """Test that validation stops at first invalid prompt"""
        data = [
            {"query": "Valid"},
            {"query": "Valid"},
            {"query": ""},  # Invalid - first error
            {"model": "no query"},  # Would also error, but we stop earlier
        ]
        file_path = create_prompts_file(data)

        with pytest.raises(PromptsLoadError, match=r"index 2"):
            load_prompts_from_file(file_path)

    def test_large_valid_file_near_limit(self, create_prompts_file):
        """Test loading a file with 999 valid prompts (just under limit)"""
        data = [{"query": f"Query number {i}"} for i in range(999)]
        file_path = create_prompts_file(data)

        prompts = load_prompts_from_file(file_path)

        assert len(prompts) == 999

    def test_unicode_queries_supported(self, create_prompts_file):
        """Test that unicode characters in queries are supported"""
        data = [
            {"query": "What is AI? - Basic question"},
            {"query": "机器学习是什么？"},  # Chinese
            {"query": "Qu'est-ce que l'IA?"},  # French
            {"query": "🤖 Robot"},  # Emoji
        ]
        file_path = create_prompts_file(data)

        prompts = load_prompts_from_file(file_path)

        assert len(prompts) == 4
        assert "AI" in prompts[0]['query']
        assert "学习" in prompts[1]['query']
        assert "IA" in prompts[2]['query']
        assert "🤖" in prompts[3]['query']

    def test_special_characters_in_queries(self, create_prompts_file):
        """Test queries with special characters are preserved"""
        data = [
            {"query": "What is C++ programming?"},
            {"query": "How to use @mentions on Twitter/X"},
            {"query": "Price in USD: $100-$200"},
            {"query": "Email: test@example.com"},
        ]
        file_path = create_prompts_file(data)

        prompts = load_prompts_from_file(file_path)

        assert "++" in prompts[0]['query']
        assert "@mentions" in prompts[1]['query']
        assert "$" in prompts[2]['query']
        assert "@example.com" in prompts[3]['query']
