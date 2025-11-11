# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

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
2. Click to focus, type query, submit with Enter (line 207-216)
3. Wait for answer generation (~20 seconds, line 230)
4. Extract results from main content area (line 240-296)
5. Take screenshot for debugging (line 235)

### Cookie Injection (lines 80-121)

Uses Nodriver's CDP to inject cookies with proper parameters:
- Handles `secure`, `httpOnly`, `sameSite`, `expires` attributes
- Converts cookie format to CDP `network.set_cookie()` format
- Uses `uc.cdp.network.CookieSameSite` and `TimeSinceEpoch` types

### Result Extraction Challenges

Perplexity's UI structure changes frequently. The tool uses multiple fallback methods:
- Method 1: Extract from `main` content area, clean navigation text (line 242)
- Method 2: Try `[data-testid*="answer"]` containers (line 263)
- Sources extracted from `[data-testid*="source"] a` elements (line 278)

## Limitations and Gotchas

1. **Must run on system with display**: Cannot run on headless servers (cloud instances need X11/VNC)
2. **Cookie expiration**: Cookies typically expire after 30 days - must be refreshed manually
3. **Perplexity UI changes**: Result extraction may break if Perplexity changes HTML structure
4. **Rate limiting**: Excessive automated searches may trigger rate limiting
5. **Detection risk**: Despite Nodriver, automation may still be detected occasionally
