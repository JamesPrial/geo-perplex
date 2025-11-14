"""
Prompts loader and validator for GEO-Perplex.

Handles loading and validating prompts from JSON files or stdin.
Ensures all prompts have required fields and valid structure.
"""

import json
import sys
import logging
from typing import List, Dict, Any

from src.config import MODEL_MAPPING, PROMPTS_FILE_CONFIG

logger = logging.getLogger(__name__)


class PromptsLoadError(ValueError):
    """
    Exception raised when loading or validating prompts fails.

    Provides clear error messages with context information including:
    - File path or source (stdin)
    - Prompt index when applicable
    - Specific field validation failures
    - Available options for invalid choices
    """
    pass


def load_prompts_from_file(file_path: str) -> List[Dict[str, Any]]:
    """
    Load prompts from JSON file or stdin.

    Reads prompts from either a file path or standard input (if file_path is "-"),
    parses the JSON content, validates the structure and individual prompts,
    and returns a list of validated prompt dictionaries.

    Args:
        file_path: Path to the JSON file containing prompts, or "-" to read from stdin.
                   JSON must be an array of prompt objects.

    Returns:
        List of validated prompt dictionaries, each containing at minimum:
        - query (str): The search query (required, non-empty)
        - model (str, optional): AI model name (validated against MODEL_MAPPING)
        - no_screenshot (bool, optional): Whether to skip screenshot generation

    Raises:
        FileNotFoundError: If the file does not exist (when not reading from stdin)
        ValueError: If JSON is invalid, not an array, empty, exceeds max prompts,
                    or contains invalid prompt structures

    Example:
        >>> # Load from file
        >>> prompts = load_prompts_from_file('prompts.json')
        >>> for prompt in prompts:
        ...     print(f"Query: {prompt['query']}")

        >>> # Load from stdin
        >>> prompts = load_prompts_from_file('-')
        >>> # Pipe JSON via: cat prompts.json | python -c ...

        >>> # Typical file format
        >>> # [
        >>> #   {"query": "What is GEO?"},
        >>> #   {"query": "What is SEO?", "model": "gpt-4"},
        >>> #   {"query": "What are LLMs?", "no_screenshot": true}
        >>> # ]
    """
    # Read content from file or stdin
    json_content = _read_json_content(file_path)

    # Parse JSON
    try:
        data = json.loads(json_content)
    except json.JSONDecodeError as e:
        raise PromptsLoadError(
            f"Invalid JSON syntax: {e.msg} at line {e.lineno}, "
            f"column {e.colno}. Please check your JSON formatting."
        )

    # Validate it's an array
    if not isinstance(data, list):
        raise PromptsLoadError(
            f"Prompts must be a JSON array (list), got {type(data).__name__}"
        )

    # Check not empty
    if not data:
        raise PromptsLoadError("Prompts file is empty array")

    # Check max prompts limit
    if len(data) > PROMPTS_FILE_CONFIG['max_prompts']:
        raise PromptsLoadError(
            f"Too many prompts: {len(data)} exceeds maximum of "
            f"{PROMPTS_FILE_CONFIG['max_prompts']}"
        )

    # Validate each prompt
    validated_prompts: List[Dict[str, Any]] = []
    for idx, prompt in enumerate(data):
        if not isinstance(prompt, dict):
            raise PromptsLoadError(
                f"Prompt at index {idx} must be a dictionary, got {type(prompt).__name__}"
            )

        # Validate the prompt structure
        validate_prompt(prompt, idx)
        validated_prompts.append(prompt)

    logger.info(f"Successfully loaded and validated {len(validated_prompts)} prompts")
    return validated_prompts


def validate_prompt(prompt: Dict[str, Any], index: int) -> Dict[str, Any]:
    """
    Validate a single prompt dictionary.

    Checks that:
    - Prompt is a dictionary
    - Required field 'query' exists and is a non-empty string (after strip)
    - Optional field 'model', if present, is a valid model name (trimmed)
    - Optional field 'no_screenshot', if present, is a boolean

    Args:
        prompt: The prompt dictionary to validate
        index: The 0-based index of this prompt in the list (for error messages)

    Returns:
        The validated prompt dictionary with normalized values (trimmed strings)

    Raises:
        PromptsLoadError: If validation fails with a descriptive error message
                          including the prompt index

    Example:
        >>> # Valid prompt
        >>> result = validate_prompt({"query": "What is GEO?"}, 0)
        >>> result['query']
        'What is GEO?'

        >>> # Invalid - missing query
        >>> validate_prompt({"model": "gpt-4"}, 0)
        PromptsLoadError: Prompt at index 0 missing required field: query

        >>> # Invalid - invalid model
        >>> validate_prompt({"query": "test", "model": "invalid-model"}, 0)
        PromptsLoadError: Prompt at index 0 model "invalid-model" not in MODEL_MAPPING
    """
    # Check prompt is a dictionary
    if not isinstance(prompt, dict):
        raise PromptsLoadError(
            f"Prompt at index {index} must be a dictionary, got {type(prompt).__name__}"
        )

    # Check query field exists
    if 'query' not in prompt:
        raise PromptsLoadError(
            f"Prompt at index {index} missing required field: query"
        )

    query = prompt['query']

    # Check query is a string
    if not isinstance(query, str):
        raise PromptsLoadError(
            f"Prompt at index {index} query must be a string, got {type(query).__name__}"
        )

    # Check query is non-empty after strip and trim it
    trimmed_query = query.strip()
    if not trimmed_query:
        raise PromptsLoadError(
            f"Prompt at index {index} query cannot be empty or whitespace-only"
        )
    prompt['query'] = trimmed_query

    # Validate and trim model if specified
    if 'model' in prompt:
        model = prompt['model']

        if not isinstance(model, str):
            raise PromptsLoadError(
                f"Prompt at index {index} model must be a string, got {type(model).__name__}"
            )

        # Trim model name
        trimmed_model = model.strip()

        if trimmed_model not in MODEL_MAPPING:
            available = ', '.join(sorted(MODEL_MAPPING.keys()))
            raise PromptsLoadError(
                f"Prompt at index {index} model \"{trimmed_model}\" not in MODEL_MAPPING. "
                f"Available models: {available}"
            )

        prompt['model'] = trimmed_model

    # Validate no_screenshot if specified
    if 'no_screenshot' in prompt:
        no_screenshot = prompt['no_screenshot']

        if not isinstance(no_screenshot, bool):
            raise PromptsLoadError(
                f"Prompt at index {index} no_screenshot must be a boolean, "
                f"got {type(no_screenshot).__name__}"
            )

    return prompt


def _read_json_content(file_path: str) -> str:
    """
    Read JSON content from file or stdin.

    Args:
        file_path: Path to file, or "-" for stdin

    Returns:
        String content of JSON file

    Raises:
        PromptsLoadError: If file doesn't exist, is not readable, is invalid encoding,
                          or if stdin is empty
    """
    if file_path == "-":
        logger.info("Reading prompts from stdin...")
        content = sys.stdin.read()
        if not content.strip():
            raise PromptsLoadError("stdin is empty")
        return content

    # File path case
    try:
        logger.info(f"Reading prompts from file: {file_path}")
        with open(file_path, 'r', encoding='utf-8') as f:
            return f.read()

    except UnicodeDecodeError as e:
        raise PromptsLoadError(
            f"Invalid file encoding in {file_path}. "
            f"File must be UTF-8 encoded JSON. Error: {e}"
        )

    except FileNotFoundError:
        raise PromptsLoadError(
            f"File not found: {file_path}. "
            f"Please check the path is correct and the file exists."
        )

    except OSError as e:
        raise PromptsLoadError(
            f"Cannot read prompts file {file_path}: {e}"
        )
