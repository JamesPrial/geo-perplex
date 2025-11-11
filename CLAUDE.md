# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

> **Status**: ✅ Search functionality is fully working as of last update. If searches aren't submitting or results aren't extracting, check the **Nodriver-Specific Gotchas** section below first!

## Project Overview

GEO-Perplex is a Python-based automation tool for researching Generative Engine Optimization (GEO) using Perplexity.ai. GEO is an emerging field analogous to SEO - where SEO focused on product placement in search engines like Google, GEO is concerned with the likelihood an LLM suggests your product.

The tool automates searches on Perplexity.ai using **Nodriver** (not Playwright or Selenium) for advanced bot detection bypass, and uses cookie-based authentication to avoid CAPTCHA and login rate limits.

## Core Architecture

### Key Files

- **`src/search.py`**: Main automation script that orchestrates the entire search process
  - Loads cookies via `src/utils/cookies.py`
  - Launches browser with Nodriver in headed mode
  - Authenticates with Perplexity using cookies
  - Performs search and extracts results
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

5. **SQLite Database Storage**: All search results are automatically saved to enable:
   - Model comparison and GEO analysis
   - Historical tracking of responses over time
   - Offline querying and analysis
   - Research data persistence

6. **Unique Screenshot Filenames**: Screenshots use timestamp + query hash to prevent overwrites and enable traceability.

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

### Environment Setup

```bash
# Create virtual environment
python3 -m venv venv
source venv/bin/activate  # Linux/macOS
# or
venv\Scripts\activate  # Windows

# Install dependencies
pip install -r requirements.txt
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
2. Load cookies from `auth.json`
3. Validate required authentication cookies are present
4. Launch browser in headed mode with Nodriver
5. Set cookies BEFORE navigating to site using CDP
6. Navigate to Perplexity.ai
7. Verify authentication by checking for authenticated UI elements

### Search Process

1. Find search input using multiple selectors (fallback approach)
2. Click to focus, type query using `send_keys()`
3. Submit search with triple fallback approach:
   - Send `\n` character (NOT the text "Enter")
   - Send CDP Enter key event as backup
   - Click search button as final fallback
4. Wait for search initiation and content stabilization
5. Extract results using `.text_all` property
6. Take screenshot with unique filename (if not disabled)
7. Save results to SQLite database with metadata
8. Display results to user
9. Clean up and close browser

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

### Cookie Injection

Uses Nodriver's CDP to inject cookies with proper parameters:
- Handles `secure`, `httpOnly`, `sameSite`, `expires` attributes
- Converts cookie format to CDP `network.set_cookie()` format
- Uses `uc.cdp.network.CookieSameSite` and `TimeSinceEpoch` types
- Sets cookies BEFORE navigation to avoid race conditions

### Result Extraction Approach

The tool extracts answer text from Perplexity's dynamic UI:
- Uses `element.text_all` property (NOT `element.text`) to get all descendant text
- **Important**: `.text_all` concatenates text with spaces, not newlines
- Extracts content between markers:
  - Start: After "1 step completed" or "answer images"
  - End: Before "ask a follow-up"
- Sources extracted from `[data-testid*="source"] a` elements
- Failed extractions are saved to database with error details

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

## Limitations and Gotchas

1. **Must run on system with display**: Cannot run on headless servers (cloud instances need X11/VNC)
2. **Cookie expiration**: Cookies typically expire after 30 days - must be refreshed manually
3. **Perplexity UI changes**: Result extraction may break if Perplexity changes HTML structure
4. **Rate limiting**: Excessive automated searches may trigger rate limiting
5. **Detection risk**: Despite Nodriver, automation may still be detected occasionally
6. **Database not cloud-synced**: `search_results.db` is local only - backup manually if needed
7. **Screenshots consume disk**: Default behavior saves screenshots (use `--no-screenshot` to disable)
