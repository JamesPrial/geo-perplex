# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

> **Status**: ✅ Search functionality is fully working with **advanced bot detection avoidance** as of latest update (2025-01-11). The tool now features human-like typing, browser fingerprint randomization, and multiple extraction fallbacks for maximum reliability.

## Project Overview

GEO-Perplex is a Python-based automation tool for researching Generative Engine Optimization (GEO) using Perplexity.ai. GEO is an emerging field analogous to SEO - where SEO focused on product placement in search engines like Google, GEO is concerned with the likelihood an LLM suggests your product.

The tool automates searches on Perplexity.ai using **Nodriver** (not Playwright or Selenium) for advanced bot detection bypass, and uses cookie-based authentication to avoid CAPTCHA and login rate limits.

### Recent Major Improvements (Latest: 2025-01-13)

**Core Automation:**
- ✅ **Human-like behavior**: Character-by-character typing with variable delays
- ✅ **Browser fingerprint randomization**: Random user agents and viewport sizes
- ✅ **Enhanced reliability**: Retry logic, multiple extraction strategies, cookie verification
- ✅ **Modular architecture**: Refactored monolithic code into clean, focused modules
- ✅ **Multi-query automation**: `--auto-new-chat` flag for continuous querying with automatic navigation

**Data Management:**
- ✅ **Advanced source extraction**: Citation numbers and domain extraction for better source tracking
- ✅ **JSON export**: `--save-json` flag for structured data export
- ✅ **Comprehensive analysis**: Full-text search, advanced filtering, statistical analysis
- ✅ **Multiple export formats**: CSV, JSON, Markdown with batch processing

**Development:**
- ✅ **Protocol-based type safety**: Custom Protocol classes for nodriver types
- ✅ **Comprehensive testing**: pytest suite with 4,341 LOC, 80%+ coverage
- ✅ **Centralized configuration**: All constants moved to `src/config.py`
- ✅ **Structured logging**: Comprehensive DEBUG/INFO/WARNING/ERROR logging
- ✅ **Claude Code integration**: Custom commands, specialized subagents, nodriver skill library

## Core Architecture

### Key Files

- **`src/config.py`**: Centralized configuration file (NEW)
  - All constants, timeouts, and selectors in one place
  - Browser configuration (args, headless mode)
  - Human behavior settings (typing speeds, delays)
  - Element selectors organized by purpose
  - Text extraction markers and patterns
  - User agent and viewport randomization pools
  - Retry and stability detection settings
  - Easy to tune without touching code

- **`src/search_cli.py`**: Main CLI orchestration (209 lines)
  - Command-line argument parsing
  - Orchestrates all modules for search execution
  - Result display and database storage
  - Entry point: `python -m src.search_cli`

### Modular Architecture (Refactored from monolithic 856-line file)

- **`src/types.py`**: Protocol definitions for type safety
  - `NodriverPage` and `NodriverElement` protocols
  - Enables type checking without coupling to nodriver internals
  - Documents critical gotchas (text properties are NOT async)

- **`src/browser/`**: Browser automation modules
  - `manager.py`: Browser lifecycle and fingerprint randomization
  - `interactions.py`: Human-like behavior utilities (`human_delay()`, `type_like_human()`, `find_interactive_element()`, `health_check()`)
  - `auth.py`: Cookie injection with retry logic and authentication verification
  - `navigation.py`: Page navigation helpers (new chat, URL verification)
  - `smart_click.py`: Multi-strategy clicking with 6 fallback methods
  - `element_waiter.py`: Element waiting utilities with custom conditions

- **`src/search/`**: Search execution modules
  - `executor.py`: Search execution with triple fallback submission
  - `extractor.py`: Result extraction with 3-tier strategy and enhanced source parsing
  - `model_selector.py`: AI model selection with smart clicking and verification

- **`src/utils/`**: Utility modules
  - `decorators.py`: Reusable `async_retry()` decorator with exponential backoff
  - `cookies.py`: Cookie loading and validation
  - `storage.py`: SQLite database operations
  - `json_export.py`: JSON export with filtering and metadata
  - `export.py`: Multi-format export (CSV, Markdown)
  - `statistics.py`: Statistical analysis and trends
  - `db_maintenance.py`: Database cleanup and deduplication
  - `process_cleanup.py`: Detection and cleanup of orphaned browser processes

- **`src/analyze.py`**: Results analysis and comparison CLI tool (1,434 lines)
  - Query and filter search results with advanced criteria
  - Full-text search in answers, sources, and queries
  - Compare results across different AI models
  - Statistical analysis and trend visualization
  - Multiple export formats (JSON, CSV, Markdown)
  - Database maintenance (deduplication, cleanup)
  - List unique queries and models
  - View recent search history
  - Display results with rich formatting

- **`src/utils/cookies.py`**: Cookie management utilities
  - `load_cookies()`: Loads cookies from `auth.json`
  - `validate_auth_cookies()`: Validates required authentication cookies are present

- **`src/utils/storage.py`**: SQLite database storage utilities
  - `init_database()`: Creates schema with indexes for efficient querying
  - `save_search_result()`: Saves search results with full metadata
  - `get_results_by_query()`: Query results by search text
  - `get_results_by_model()`: Query results by AI model
  - `compare_models_for_query()`: Compare model responses for same query
  - `get_recent_results()`: Get recent searches with limit
  - `get_unique_queries()`: List all unique queries
  - `get_unique_models()`: List all unique models

- **`auth.json`**: Personal authentication cookies (gitignored, never commit)
  - Required cookies: `pplx.session-id`, `__Secure-next-auth.session-token`
  - Must be extracted from logged-in Perplexity.ai session via browser DevTools

- **`search_results.db`**: SQLite database (gitignored, contains personal search data)
  - Stores all search results with full metadata
  - Schema: id, query, model, timestamp, answer_text, sources (JSON), screenshot_path, execution_time_seconds, success, error_message
  - Indexes on: query, model, timestamp, (query, model)

### Key Design Decisions

1. **Nodriver over Playwright/Selenium**: Nodriver is specifically designed to bypass bot detection systems. Perplexity actively blocks standard automation tools.

2. **Headed Mode Required**: Browser must run with visible UI (`headless=False`). Perplexity detects and blocks headless browsers.

3. **Cookie-Based Authentication**: Avoids login rate limits, CAPTCHA challenges, and provides more reliable authentication.

4. **Chrome DevTools Protocol (CDP)**: Uses CDP via `page.send(uc.cdp.network.set_cookie(...))` for native browser control and cookie injection.

5. **Human-Like Behavior**: Character-by-character typing with randomized delays (0.05-0.15s per character) mimics real user interaction and reduces detection risk.

6. **Browser Fingerprint Randomization**: Random selection from 5 user agents and 5 viewport sizes makes each session appear as a different user.

7. **Multiple Fallback Strategies**: Triple fallbacks for search submission and 3-tier text extraction ensures reliability even when Perplexity's UI changes.

8. **Retry Logic with Exponential Backoff**: Critical operations like cookie injection automatically retry with increasing delays, handling transient failures gracefully.

9. **Content Stability Detection**: Hash-based change detection with 0.5s intervals accurately detects when answers finish generating, avoiding premature extraction.

10. **SQLite Database Storage**: All search results are automatically saved to enable:
    - Model comparison and GEO analysis
    - Historical tracking of responses over time
    - Offline querying and analysis
    - Research data persistence

11. **Centralized Configuration**: `src/config.py` contains all tunable parameters, making it easy to adjust behavior without modifying code.

12. **Unique Screenshot Filenames**: Screenshots use timestamp + query hash to prevent overwrites and enable traceability.

13. **Active Model Selection**: The `--model` parameter actively selects AI models in Perplexity's UI (not just tracking). Uses:
    - `SmartClicker` with 6 fallback strategies for reliable clicking
    - `ElementWaiter` for waiting on dynamic UI elements
    - Model name validation against `MODEL_MAPPING` in config
    - Clear error messages with available models if invalid name provided
    - Human-like delays between interactions (button click, menu open, option click)
    - Optional verification to confirm selection succeeded

14. **UI Discovery Support**: Includes standalone `scripts/inspect_model_selector.py` for manually discovering:
    - Model selector CSS selectors and aria-labels
    - Available model names and their UI text
    - Options container structure (menu vs listbox)
    - Allows non-technical users to update `src/config.py` without code changes

15. **Protocol-Based Type Safety**: Custom `Protocol` classes in `src/types.py` enable type checking without coupling:
    - `NodriverPage` and `NodriverElement` protocols
    - Documents critical gotchas (text properties NOT async)
    - Enables IDE autocomplete and static analysis
    - Maintains flexibility for nodriver version updates

16. **Multi-Query Automation**: `--auto-new-chat` flag enables continuous querying:
    - Automatically clicks new chat button between searches
    - Closes sources overlay before navigation (prevents hangs)
    - URL change verification prevents duplicate searches
    - Retry logic with exponential backoff for reliability

17. **Enhanced Source Extraction**: Advanced source parsing with metadata:
    - Citation numbers preserved from Perplexity UI
    - Domain extraction from URLs for quick reference
    - Structured JSON storage with text, URL, domain, citation number
    - Fallback to index-based numbering when citation missing

18. **Comprehensive Testing**: pytest suite with 4,341 LOC ensuring reliability:
    - 80%+ code coverage with branch coverage enabled
    - Test markers for unit, integration, slow tests
    - In-memory database fixtures for fast testing
    - Async test support via pytest-asyncio

## Common Development Commands

### Running Searches

```bash
# Basic search with default query (uses currently selected model)
python -m src.search_cli

# Custom search query
python -m src.search_cli "What are the best project management tools for startups?"

# Select a specific AI model and perform search
python -m src.search_cli "What is GEO?" --model gpt-4

# Available models: gpt-4, gpt-4-turbo, claude, claude-3, sonar, sonar-pro, default
# (Model names may vary - run with invalid model to see available options)

# Skip screenshot generation
python -m src.search_cli "What is Python?" --no-screenshot

# Combine options: select model, custom query, skip screenshot
python -m src.search_cli "Best CRM tools" --model claude-3 --no-screenshot

# Multi-query automation (requires --auto-new-chat flag)
python -m src.search_cli "What is GEO?" --auto-new-chat --query-count 5

# Save results to JSON
python -m src.search_cli "Best AI tools" --save-json --json-output-dir ./exports

# Combined: multi-query with model selection and JSON export
python -m src.search_cli "query" --model gpt-4 --auto-new-chat --query-count 3 --save-json
```

### Analyzing Stored Results

```bash
# Basic queries
python -m src.analyze recent --limit 10
python -m src.analyze list-queries
python -m src.analyze list-models

# Query by search text or model
python -m src.analyze query --query "What is GEO?" --full
python -m src.analyze model --model gpt-4 --limit 20

# Compare models for same query
python -m src.analyze compare --query "What are the best project management tools?" --full

# Advanced filtering with multiple criteria
python -m src.analyze filter --model gpt-4 --start-date 2025-01-01 --success-only
python -m src.analyze filter --end-date 2025-01-31 --min-execution-time 20 --limit 50

# Full-text search in answers, sources, or queries
python -m src.analyze search "machine learning" --in answers --limit 10
python -m src.analyze search "python" --in all --model gpt-4 --full

# Statistics and trends
python -m src.analyze stats                    # Overall database statistics
python -m src.analyze stats-model --model gpt-4  # Model-specific statistics
python -m src.analyze stats-trends --metric execution_time --period day

# Export in multiple formats
python -m src.analyze export --output results.json
python -m src.analyze export-csv results.csv --model gpt-4 --success-only
python -m src.analyze export-md report.md --full --query "What is GEO?"
python -m src.analyze export-batch ./exports/ --format csv --group-by model

# Database maintenance
python -m src.analyze duplicates --exact        # Find duplicate queries
python -m src.analyze cleanup --dry-run         # Preview cleanup operations
python -m src.analyze cleanup --remove-failed   # Remove failed searches
python -m src.analyze info                      # Show database information
```

### Process Cleanup

```bash
# Cleanup orphaned browser processes from crashed runs

# Preview what would be cleaned (safe, recommended first)
python scripts/cleanup_browsers.py --dry-run

# Actually cleanup orphaned browsers
python scripts/cleanup_browsers.py

# List orphaned browsers without cleaning
python scripts/cleanup_browsers.py --list-only

# Verbose output for debugging
python scripts/cleanup_browsers.py --verbose

# Programmatic usage in Python
from src.utils.process_cleanup import cleanup_on_startup

# Safe startup cleanup (automatic detection and termination)
stats = cleanup_on_startup()
if stats['killed'] > 0:
    print(f"Cleaned up {stats['killed']} orphaned browsers")
```

### Cookie Setup

Authentication cookies must be manually extracted from a logged-in Perplexity.ai browser session:

1. Log into Perplexity.ai in Chrome
2. Open DevTools (F12) → Application/Storage → Cookies → https://www.perplexity.ai
3. Copy required cookies to `auth.json`:
   - `pplx.session-id`
   - `__Secure-next-auth.session-token`
   - `next-auth.csrf-token` (optional)
   - `next-auth.callback-url` (optional)

See `auth.json.example` for format.

### Model Selection Setup

The tool supports active AI model selection via the `--model` parameter. To set up models:

1. **Discover available models** (first time only):
   ```bash
   python scripts/inspect_model_selector.py
   ```
   - Browser opens Perplexity.ai automatically
   - Use DevTools (F12) to inspect the model selector UI
   - Note CSS selectors, aria-labels, and available model names
   - Press Ctrl+C when done

2. **Update configuration** in `src/config.py`:
   - Update `MODEL_SELECTOR['selector_patterns']` with discovered selectors
   - Update `MODEL_SELECTOR['options_container']` with menu/listbox selectors
   - Add entries to `MODEL_MAPPING` for each available model
   - Example: `'gpt-4': 'GPT-4'` maps user input to UI text

3. **Test model selection**:
   ```bash
   # Test with a specific model
   python -m src.search_cli "Test query" --model gpt-4

   # If invalid model, error shows available options
   python -m src.search_cli "Test query" --model invalid-model
   ```

**Important Notes**:
- Model names are case-sensitive (e.g., use `gpt-4` not `GPT-4` for `--model` parameter)
- The UI text in MODEL_MAPPING should match exactly what appears in Perplexity's dropdown
- If Perplexity updates their UI, run the discovery script again to get new selectors
- Model selection is optional - omit `--model` to use Perplexity's default selection

### Testing

The project has a comprehensive test suite with 4,341 lines of test code and 80%+ coverage:

```bash
# Run all tests with coverage
pytest

# Run specific test markers
pytest -m unit          # Fast unit tests only (< 1s each)
pytest -m integration   # Integration tests with external dependencies
pytest -m slow          # Long-running tests (browser automation)

# Run specific test file
pytest tests/test_search.py
pytest tests/test_analyze.py

# Run with verbose output
pytest -v

# Generate HTML coverage report
pytest --cov=src --cov-report=html
# View at htmlcov/index.html

# Run tests in parallel (faster, requires pytest-xdist)
pytest -n auto
```

**Test Organization:**
- **16 test modules** covering all major components
- **Markers**: `unit`, `integration`, `slow`, `asyncio`
- **Fixtures**: In-memory database, temp files, sample data
- **Coverage**: Source code (`src/`) with branch coverage enabled

**Test Configuration (`pytest.ini`):**
- Async support via `pytest-asyncio`
- Automatic test discovery in `tests/` directory
- Coverage reports with HTML output
- Warning filters for known third-party issues

## Important Technical Details

### Authentication Flow (`src/search_cli.py` with modular components)

1. Parse command-line arguments: query, `--model`, `--no-screenshot` (in `src/search_cli.py`)
2. Load cookies from `auth.json` via `src/utils/cookies.py`
3. Validate required authentication cookies are present
4. **Launch browser with fingerprint**: `src/browser/manager.py` randomizes user agent and viewport
5. **Set cookies with retry logic**: `src/browser/auth.py` with `@async_retry` decorator from `src/utils/decorators.py`
6. Navigate to Perplexity.ai
7. **Health check**: `src/browser/interactions.py` verifies page responsiveness
8. **Verify authentication**: `src/browser/auth.py` checks for authenticated UI elements
9. **Select AI model** (if specified): `src/search/model_selector.py` finds selector, clicks to open options, selects target model
   - Uses `SmartClicker` for reliable multi-strategy clicking
   - Uses `ElementWaiter` for waiting on options container
   - Validates model name against `MODEL_MAPPING` in `src/config.py`
   - Includes human-like delays between interactions
   - Verifies selection success

### Search Process (Enhanced with Human-Like Behavior)

1. **Search execution** (`src/search/executor.py`):
   - Find interactive search input with visibility checks
   - Human delay (0.3-0.7s) before interaction
   - Click to focus input
   - Type query character-by-character with `type_like_human()` from `src/browser/interactions.py`
   - Variable delays (0.05-0.15s per char, 0.1-0.2s for spaces)
   - Submit with triple fallback: `\n` character → CDP Enter key → button click

2. **Result extraction** (`src/search/extractor.py`):
   - Wait for search initiation (URL change, loading indicators)
   - Content stability detection with `wait_for_content_stability()`
   - Hash-based monitoring with 0.5s intervals
   - 3-tier extraction strategy:
     - Strategy 1: Marker-based (between "1 step completed" and "ask a follow-up")
     - Strategy 2: Clean text extraction (filter UI patterns)
     - Strategy 3: Direct container selection (last resort)
   - Extract sources from `[data-testid*="source"] a` elements

3. **Save and display** (`src/search_cli.py`):
   - Take screenshot with unique filename (if not disabled)
   - Save results to SQLite database via `src/utils/storage.py`
   - Display results to user with structured formatting
   - Clean up and close browser

### Model Selection Process (`src/search/model_selector.py`)

When `--model` is specified, the tool performs active model selection:

1. **Validation**: Verifies model name exists in `MODEL_MAPPING` from `src/config.py`
   - Raises `ValueError` with list of available models if invalid
   - User can fix and rerun with correct model name

2. **Finding selector**: Tries multiple CSS selector patterns from `MODEL_SELECTOR['selector_patterns']`
   - Looks for data-testid, aria-label, and class attributes
   - Uses `find_interactive_element()` for visibility checks
   - Raises `RuntimeError` if no selector pattern matches

3. **Opening menu**: Uses `SmartClicker` to click model selector button
   - Tries 6 different click strategies (normal, JavaScript, focus+Enter, etc.)
   - Includes human-like delays (0.3-0.7s before click)
   - Handles elements that require scrolling into view

4. **Waiting for options**: Uses `ElementWaiter` to detect dropdown/menu appearance
   - Tries multiple container selectors: role="menu", role="listbox", etc.
   - Waits up to 5 seconds (configurable timeout)
   - Raises `RuntimeError` if container never appears

5. **Finding option**: Searches for model option by text content
   - Uses JavaScript evaluation to find matching text
   - Tries multiple selector patterns and text matching strategies
   - Lists available options in error message if target not found

6. **Clicking option**: Uses `SmartClicker` again for reliable clicking
   - Includes human-like delays between button click and option click
   - Multiple fallback strategies for maximum reliability

7. **Verification**: Confirms selection took effect
   - Checks if selector UI now shows selected model name
   - Returns True even if verification inconclusive (click succeeded)
   - Logs detailed messages at DEBUG/INFO/ERROR levels

**Error Handling**:
- `ValueError`: Invalid model name - lists available models in error
- `RuntimeError`: Selector not found, menu didn't open, option not found, etc.
- All errors include actionable messages for debugging

### Database Integration

All search results are automatically saved to `search_results.db` with:
- Query text and AI model identifier
- Full answer text and sources (as JSON array)
- Screenshot path (relative to project root)
- Execution time in seconds
- Success/failure status
- Error messages for failed searches
- Auto-generated timestamp

The database uses indexes on query, model, and timestamp for fast querying.

### Cookie Injection (Enhanced with Retry Logic)

Uses Nodriver's CDP to inject cookies with robust error handling:
- **Retry decorator**: `@async_retry(max_attempts=2)` automatically retries on failure
- **Critical cookie tracking**: Validates `pplx.session-id` and `__Secure-next-auth.session-token`
- **Error handling**: Distinguishes between critical (fail fast) and optional cookies
- **Verification**: Confirms all critical cookies were set before proceeding
- Handles `secure`, `httpOnly`, `sameSite`, `expires` attributes properly
- Converts cookie format to CDP `network.set_cookie()` format
- Uses `uc.cdp.network.CookieSameSite` and `TimeSinceEpoch` types
- Sets cookies BEFORE navigation to avoid race conditions
- Logs success/failure for each cookie (DEBUG level)

### Result Extraction Approach (3-Tier Fallback Strategy)

The tool uses multiple strategies to extract answer text from Perplexity's dynamic UI:

**Strategy 1: Marker-Based Extraction** (Most Accurate)
- Searches for answer between configurable start/end markers
- Start markers: "1 step completed", "answer images", "images "
- End markers: "ask a follow-up", "ask follow-up"
- Automatically removes UI elements: "Home Discover", "Spaces Finance", etc.
- Defined in `EXTRACTION_MARKERS` config

**Strategy 2: Clean Text Extraction** (Fallback)
- Gets full main element text and filters out known UI patterns
- Skip patterns: "Home", "Discover", "Spaces", "Finance", "Install", etc.
- Used when markers aren't found or strategy 1 fails

**Strategy 3: Direct Container Selection** (Last Resort)
- Tries multiple answer container selectors: `[data-testid*="answer"]`, `[class*="answer"]`, etc.
- Returns first element with sufficient content (>50 chars)

**Important Technical Notes:**
- Uses `element.text_all` property (NOT `element.text`) to get all descendant text
- `.text_all` concatenates text with spaces, not newlines
- All strategies properly handle async/await (text properties are NOT awaited)
- Sources extracted from `[data-testid*="source"] a` elements
- Failed extractions are logged and saved to database with error details

### Database Schema

The `search_results` table structure:
```sql
CREATE TABLE search_results (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    query TEXT NOT NULL,
    model TEXT,
    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
    answer_text TEXT,
    sources TEXT,  -- JSON array of {url, text} objects
    screenshot_path TEXT,
    execution_time_seconds REAL,
    success BOOLEAN DEFAULT 1,
    error_message TEXT
);
```

Indexes for efficient querying:
- `idx_query` on query
- `idx_model` on model
- `idx_timestamp` on timestamp
- `idx_query_model` on (query, model) for comparisons

### Analysis CLI (`src/analyze.py`)

The analysis tool provides multiple query modes:
- **recent**: View N most recent searches
- **list-queries**: List all unique queries
- **list-models**: List all unique models
- **query**: Filter by specific query text (optionally by model)
- **model**: Filter by specific model (with limit)
- **compare**: Side-by-side comparison of models for same query

All commands support `--full` flag to show complete answers instead of previews.

## Helper Functions (Modularized)

The codebase includes several helper functions organized by module:

### Browser Interactions (`src/browser/interactions.py`)

#### `human_delay(delay_type='short'|'medium'|'long')`
- Adds randomized delays to mimic human behavior
- **short**: 0.3-0.7s, **medium**: 0.5-1.5s, **long**: 1.0-2.5s
- Configurable via `HUMAN_BEHAVIOR['delays']` in `src/config.py`

#### `type_like_human(element, text)`
- Types text character-by-character with variable delays
- 0.05-0.15s per character, 0.1-0.2s for spaces
- Most realistic typing simulation for bot detection avoidance

#### `find_interactive_element(page, selectors, timeout)`
- Finds elements with visibility and interactability checks
- Uses JavaScript to verify element is not hidden
- Tries multiple selectors with fallback

#### `health_check(page)`
- Validates page state after navigation
- Checks: page responsiveness, main content presence, page title
- Returns structured health report dict

### Decorators (`src/utils/decorators.py`)

#### `async_retry(max_attempts, exceptions)`
- Decorator that automatically retries async functions on failure
- Exponential backoff: delay × (2 ** attempt)
- Applied to `set_cookies()` function in `src/browser/auth.py`
- Configurable via `RETRY_CONFIG`

### Search Execution (`src/search/executor.py`)

#### `wait_for_content_stability(page, max_wait)`
- Monitors content changes using MD5 hashing
- Checks every 0.5s for stability
- Requires 3 consecutive stable checks (1.5s total)
- Minimum content threshold: 50 characters
- Prevents premature extraction of incomplete answers

## Protocol-Based Type Safety (`src/types.py`)

The codebase uses Python's `Protocol` classes to enable type safety without tight coupling to nodriver internals:

### Why Protocols?

**Problem**: Nodriver objects don't have type stubs, making IDE autocomplete and static analysis difficult.

**Solution**: Custom `Protocol` definitions that document the interface we actually use:

```python
from typing import Protocol

class NodriverElement(Protocol):
    """Protocol for nodriver Element objects"""
    # CRITICAL: text and text_all are PROPERTIES, not async methods
    @property
    def text(self) -> str: ...

    @property
    def text_all(self) -> str: ...

    async def click(self) -> None: ...
    async def send_keys(self, text: str) -> None: ...
    # ... other methods
```

### Benefits

1. **IDE Support**: Full autocomplete and type hints in VS Code, PyCharm, etc.
2. **Documentation**: Protocol definitions document critical gotchas (like text properties)
3. **Flexibility**: No direct dependency on nodriver internals
4. **Refactoring Safety**: Type checker catches usage errors before runtime

### Critical Gotchas Documented in Protocols

**Text Properties Are NOT Async:**
```python
# ❌ Wrong (but type checker catches this!)
answer_text = await element.text_all

# ✅ Correct
answer_text = element.text_all
```

**send_keys() Types Literal Strings:**
```python
# ❌ Wrong - types literal "Enter" text
await element.send_keys('Enter')

# ✅ Correct - presses Enter key
await element.send_keys('\n')
```

### Usage Throughout Codebase

All functions that accept nodriver objects use these protocols:
```python
async def extract_text(element: NodriverElement) -> str:
    """Type-safe extraction with protocol"""
    return element.text_all  # IDE knows this is a property!
```

This approach makes the critical nodriver gotchas visible in type signatures and documentation.

## Nodriver-Specific Gotchas

### Critical: Keyboard Input Handling
- **`send_keys('Enter')` will type the literal text "Enter"** - it does NOT press the Enter key!
- Use `send_keys('\n')` or `send_keys('\r\n')` to press Enter
- For maximum reliability, also send CDP key events:
  ```python
  await page.send(uc.cdp.input_.dispatch_key_event(
      type_='keyDown', key='Enter', code='Enter',
      windows_virtual_key_code=13, native_virtual_key_code=13
  ))
  ```

### Critical: Text Property Access
- `.text` and `.text_all` are **synchronous properties**, NOT async methods
- ❌ Wrong: `await element.text` or `await element.text_all`
- ✅ Correct: `element.text` or `element.text_all`
- `.text` only returns direct text content (often empty for container elements)
- `.text_all` returns ALL descendant text concatenated with spaces (not newlines!)

### Why These Matter
- Nodriver behaves differently from Selenium/Playwright in these areas
- These issues cause silent failures - no errors, just wrong behavior
- The Enter key issue makes searches appear to work but not actually submit

## Configuration and Logging

### Centralized Configuration (`src/config.py`)

All tunable parameters are in `src/config.py` for easy modification without touching code:
- **BROWSER_CONFIG**: Browser launch arguments and headless mode
- **HUMAN_BEHAVIOR**: Typing speeds and delay ranges
- **TIMEOUTS**: All timeout values (page load, element selection, etc.)
- **STABILITY_CONFIG**: Content detection thresholds
- **SELECTORS**: CSS selectors organized by purpose (search input, auth indicators, etc.)
- **EXTRACTION_MARKERS**: Text extraction start/end markers and UI patterns
- **REQUIRED_COOKIES**: Authentication cookies list
- **RETRY_CONFIG**: Retry attempts and backoff settings
- **USER_AGENTS**: Pool of 5 realistic Chrome user agents
- **VIEWPORT_SIZES**: Pool of 5 common screen resolutions

### Structured Logging

The tool uses Python's `logging` module with 4 levels:
- **DEBUG**: Technical details (selectors used, extraction strategies, timings)
- **INFO**: User-facing progress messages (authentication, search steps)
- **WARNING**: Non-fatal issues (auth concerns, timeouts, fallback usage)
- **ERROR**: Failures with full stack traces

Configure logging level in `LOGGING_CONFIG['level']` (default: 'INFO')

View debug logs: Change to `'DEBUG'` in `src/config.py` and rerun

## Claude Code Integration

This project includes comprehensive Claude Code integration for AI-assisted development:

### Custom Slash Commands (`.claude/commands/`)

**`/implement`** - Coordinated subagent workflow for feature implementation:
- Automatically launches specialized agents in sequence
- Code planning → writing → reviewing → testing → committing
- Zero-tolerance quality gates at each stage
- Usage: `/implement <feature description>`

### Specialized Subagents (`.claude/agents/`)

**`python-code-writer`** - Clean, Pythonic code implementation:
- Prioritizes readability and maintainability
- Follows PEP 8 and project conventions
- Creates focused, well-documented code

**`python-code-reviewer`** - Expert code review with actionable feedback:
- Checks code quality and best practices
- Identifies potential bugs and improvements
- Suggests optimizations and refactoring

**`python-test-runner`** - Automated test execution with concise summaries:
- Runs pytest suite with coverage
- Provides clear pass/fail status
- Highlights failing tests with context

**`nodriver-debugger`** - Nodriver-specific debugging specialist:
- Investigates browser automation issues
- Creates diagnostic scripts
- Provides solutions for common nodriver gotchas

### Nodriver Skill Library (`.claude/skills/nodriver/`)

Comprehensive nodriver development assistance:
- **Scripts**: Quick start, Docker setup, profile manager, smart click, safe typing, element waiting
- **Templates**: Basic scraper, login automation, data extractor
- **References**: Common patterns, known issues, migration guide
- **Docker Support**: Production-ready Dockerfile and compose configuration

**Using the Nodriver Skill:**
```
# Activate in Claude Code
/skill nodriver

# Access battle-tested patterns and solutions
# Get help with anti-detection, CDP integration, and more
```

### Development Workflow

**Typical feature development with `/implement`:**
1. User requests feature: `/implement <description>`
2. **Plan agent** analyzes requirements and creates implementation plan
3. **Code writer** implements the feature following project conventions
4. **Code reviewer** checks quality and suggests improvements
5. **Test runner** verifies all tests pass
6. **Git operations** creates commit with proper formatting

**Benefits:**
- Consistent code quality across all contributions
- Automatic testing before commits
- Nodriver expertise always available
- Reduced debugging time with specialized agents

## Limitations and Gotchas

1. **Must run on system with display**: Cannot run on headless servers (cloud instances need X11/VNC)
2. **Longer execution times**: Human-like behavior adds 5-10 seconds per search (character-by-character typing, random delays). This is intentional for bot detection avoidance. Typical execution time: 30-40 seconds.
3. **Cookie expiration**: Cookies typically expire after 30 days - must be refreshed manually
4. **Perplexity UI changes**: Result extraction may break if Perplexity changes HTML structure (3-tier fallback minimizes this risk)
5. **Rate limiting**: Excessive automated searches may trigger rate limiting (human-like behavior reduces risk)
6. **Detection risk**: Despite advanced stealth measures (fingerprinting, human typing, delays), automation may still be detected occasionally
7. **Database not cloud-synced**: `search_results.db` is local only - backup manually if needed
8. **Screenshots consume disk**: Default behavior saves screenshots (use `--no-screenshot` to disable)
9. **Configuration changes require restart**: Changes to `src/config.py` only take effect on next run
