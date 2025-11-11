# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

> **Status**: ✅ Search functionality is fully working with **advanced bot detection avoidance** as of latest update (2025-01-11). The tool now features human-like typing, browser fingerprint randomization, and multiple extraction fallbacks for maximum reliability.

## Project Overview

GEO-Perplex is a Python-based automation tool for researching Generative Engine Optimization (GEO) using Perplexity.ai. GEO is an emerging field analogous to SEO - where SEO focused on product placement in search engines like Google, GEO is concerned with the likelihood an LLM suggests your product.

The tool automates searches on Perplexity.ai using **Nodriver** (not Playwright or Selenium) for advanced bot detection bypass, and uses cookie-based authentication to avoid CAPTCHA and login rate limits.

### Recent Major Improvements (2025-01-11)

- ✅ **Human-like behavior**: Character-by-character typing with variable delays
- ✅ **Browser fingerprint randomization**: Random user agents and viewport sizes
- ✅ **Enhanced reliability**: Retry logic, multiple extraction strategies, cookie verification
- ✅ **Structured logging**: Comprehensive DEBUG/INFO/WARNING/ERROR logging
- ✅ **Centralized configuration**: All constants moved to `src/config.py`
- ✅ **Bug fixes**: Corrected all async/await issues with Nodriver properties

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

- **`src/search.py`**: Main automation script (645 lines, heavily enhanced)
  - **Helper functions**: `human_delay()`, `type_like_human()`, `find_interactive_element()`, `health_check()`, `async_retry()`
  - **Browser fingerprinting**: Random user agents and viewport sizes
  - **Human-like typing**: Character-by-character with variable delays (0.05-0.15s per char)
  - **Cookie injection**: Enhanced with retry logic and verification
  - **Content stability**: Hash-based detection with 0.5s intervals
  - **Text extraction**: 3-tier fallback strategy (marker-based → clean text → direct container)
  - **Structured logging**: DEBUG/INFO/WARNING/ERROR levels throughout
  - Loads cookies via `src/utils/cookies.py`
  - Saves results to database via `src/utils/storage.py`
  - Generates screenshots with unique timestamped filenames (unless `--no-screenshot`)

- **`src/analyze.py`**: Results analysis and comparison CLI tool
  - Query and filter search results from database
  - Compare results across different AI models
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

## Common Development Commands

### Running Searches

```bash
# Basic search with default query
python -m src.search

# Custom search query
python -m src.search "What are the best project management tools for startups?"

# Track which AI model is being used
python -m src.search "What is GEO?" --model gpt-4

# Skip screenshot generation
python -m src.search "What is Python?" --no-screenshot

# Combine options
python -m src.search "Best CRM tools" --model claude-3 --no-screenshot
```

### Analyzing Stored Results

```bash
# View recent searches
python -m src.analyze recent --limit 10

# List all unique queries
python -m src.analyze list-queries

# List all unique models
python -m src.analyze list-models

# Query by search text
python -m src.analyze query --query "What is GEO?" --full

# Query by model
python -m src.analyze model --model gpt-4 --limit 20

# Compare models for same query
python -m src.analyze compare --query "What are the best project management tools?" --full
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

## Important Technical Details

### Authentication Flow (`src/search.py`)

1. Parse command-line arguments: query, `--model`, `--no-screenshot`
2. Load cookies from `auth.json` via `src/utils/cookies.py`
3. Validate required authentication cookies are present
4. **Randomize browser fingerprint**: Select random user agent and viewport size from pools
5. Launch browser in headed mode with Nodriver + randomized fingerprint
6. **Set cookies with retry logic**: `@async_retry` decorator automatically retries on failure
7. Navigate to Perplexity.ai
8. **Health check**: Verify page responsiveness and content availability
9. **Verify authentication**: Check for authenticated UI elements (sidebar, account menu)

### Search Process (Enhanced with Human-Like Behavior)

1. **Find interactive search input**: Use `find_interactive_element()` with visibility checks
2. **Human delay**: Short random pause (0.3-0.7s) before interaction
3. Click to focus input with mouse hover simulation
4. **Type query character-by-character**: Variable delays (0.05-0.15s per char, 0.1-0.2s for spaces)
5. **Reading pause**: Short delay (0.3-0.7s) before submission (mimics human reading)
6. Submit search with triple fallback approach:
   - Send `\n` character (NOT the text "Enter")
   - Send CDP Enter key event as backup
   - Click search button as final fallback
7. **Wait for search initiation**: Check URL change and loading indicators
8. **Content stability detection**: Hash-based monitoring with 0.5s intervals until content stabilizes
9. **Extract results with 3-tier strategy**:
   - Strategy 1: Marker-based extraction (between "1 step completed" and "ask a follow-up")
   - Strategy 2: Clean text extraction (filter UI patterns)
   - Strategy 3: Direct container selection (last resort)
10. Extract sources from `[data-testid*="source"] a` elements
11. Take screenshot with unique filename (if not disabled)
12. Save results to SQLite database with full metadata
13. Display results to user with structured logging
14. Clean up and close browser

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

## Helper Functions (`src/search.py`)

The codebase includes several helper functions for improved reliability and maintainability:

### `human_delay(delay_type='short'|'medium'|'long')`
- Adds randomized delays to mimic human behavior
- **short**: 0.3-0.7s, **medium**: 0.5-1.5s, **long**: 1.0-2.5s
- Configurable via `HUMAN_BEHAVIOR['delays']` in `src/config.py`
- Used throughout to avoid detection patterns

### `type_like_human(element, text)`
- Types text character-by-character with variable delays
- 0.05-0.15s per character, 0.1-0.2s for spaces
- Most realistic typing simulation for bot detection avoidance
- Configurable via `HUMAN_BEHAVIOR['typing_speed']`

### `find_interactive_element(page, selectors, timeout)`
- Finds elements with visibility and interactability checks
- Uses JavaScript to verify element is not hidden (`display: none`, `visibility: hidden`)
- Tries multiple selectors with fallback
- Returns only visible, interactive elements

### `async_retry(max_attempts, exceptions)` (Decorator)
- Automatically retries async functions on failure
- Exponential backoff: delay × (2 ** attempt)
- Applied to `set_cookies()` function
- Configurable via `RETRY_CONFIG`

### `health_check(page)`
- Validates page state after navigation
- Checks: page responsiveness, main content presence, page title
- Returns structured health report dict
- Used for debugging navigation issues

### `wait_for_content_stability(page, max_wait)`
- Monitors content changes using MD5 hashing
- Checks every 0.5s for stability
- Requires 3 consecutive stable checks (1.5s total)
- Minimum content threshold: 50 characters
- Prevents premature extraction of incomplete answers

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
