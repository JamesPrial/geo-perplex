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

- **`src/utils/cookies.py`**: Cookie management utilities
  - `load_cookies()`: Loads cookies from `auth.json`
  - `validate_auth_cookies()`: Validates required authentication cookies are present

- **`auth.json`**: Personal authentication cookies (gitignored, never commit)
  - Required cookies: `pplx.session-id`, `__Secure-next-auth.session-token`
  - Must be extracted from logged-in Perplexity.ai session via browser DevTools

### Key Design Decisions

1. **Nodriver over Playwright/Selenium**: Nodriver is specifically designed to bypass bot detection systems. Perplexity actively blocks standard automation tools.

2. **Headed Mode Required**: Browser must run with visible UI (`headless=False`). Perplexity detects and blocks headless browsers.

3. **Cookie-Based Authentication**: Avoids login rate limits, CAPTCHA challenges, and provides more reliable authentication.

4. **Chrome DevTools Protocol (CDP)**: Uses CDP via `page.send(uc.cdp.network.set_cookie(...))` for native browser control and cookie injection.

## Common Development Commands

### Running Searches

```bash
# Basic search with default query
python -m src.search

# Custom search query
python -m src.search "What are the best project management tools for startups?"
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

1. Load cookies from `auth.json` (line 25)
2. Launch browser in headed mode (line 31)
3. Set cookies BEFORE navigating to site (line 40-42)
4. Navigate to Perplexity.ai (line 46)
5. Verify authentication by checking for authenticated UI elements (line 51)

### Search Process

1. Find search input using multiple selectors (line 181-200)
2. Click to focus, type query (line 207-213)
3. Submit search with triple fallback approach (line 215-251):
   - Send `\n` character (NOT the text "Enter")
   - Send CDP Enter key event as backup
   - Click search button as final fallback
4. Wait for search initiation and content stabilization (line 260-336)
5. Extract results using `.text_all` property (line 363-460)
6. Take screenshot for debugging (line 361)

### Cookie Injection (lines 80-121)

Uses Nodriver's CDP to inject cookies with proper parameters:
- Handles `secure`, `httpOnly`, `sameSite`, `expires` attributes
- Converts cookie format to CDP `network.set_cookie()` format
- Uses `uc.cdp.network.CookieSameSite` and `TimeSinceEpoch` types

### Result Extraction Approach

The tool extracts answer text from Perplexity's dynamic UI:
- Uses `element.text_all` property (NOT `element.text`) to get all descendant text
- **Important**: `.text_all` concatenates text with spaces, not newlines
- Extracts content between markers:
  - Start: After "1 step completed" or "answer images"
  - End: Before "ask a follow-up"
- Sources extracted from `[data-testid*="source"] a` elements

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
