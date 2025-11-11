# GEO-Perplex: Generative Engine Optimization Research Tool

An automated research tool for analyzing Generative Engine Optimization (GEO) using Perplexity.ai. This tool uses Python and Nodriver to automate searches on Perplexity, helping you understand how LLMs perceive and recommend products or topics.

## What is GEO?

Generative Engine Optimization (GEO) is an emerging field analogous to SEO. Where SEO focused on a product's placement on search engines like Google, GEO is concerned with the likelihood that an LLM suggests your product. Perplexity.ai offers a unified platform for utilizing various LLMs for web searches, making it the perfect platform for gaining insight into your current GEO standing.

## Prerequisites

- Python 3.8 or higher
- Chrome or Chromium browser installed
- Valid Perplexity.ai account with authentication cookies
- Linux, macOS, or Windows operating system

## Setup Instructions

### 1. Clone the Repository

```bash
git clone <repository-url>
cd geo-perplex
```

### 2. Create a Virtual Environment

**Linux/macOS:**
```bash
python3 -m venv venv
source venv/bin/activate
```

**Windows:**
```bash
python -m venv venv
venv\Scripts\activate
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

### 4. Set Up Authentication Cookies

The tool requires valid Perplexity.ai authentication cookies to function.

1. Copy the example authentication file:
   ```bash
   cp auth.json.example auth.json
   ```

2. Update `auth.json` with your own Perplexity.ai cookies. The file should contain an array of cookie objects with the following structure:

   ```json
   [{
     "name": "pplx.session-id",
     "value": "your-session-id-here",
     "domain": "www.perplexity.ai",
     "path": "/",
     "expires": 1762833459,
     "httpOnly": false,
     "secure": false,
     "sameSite": "Lax"
   },
   {
     "name": "__Secure-next-auth.session-token",
     "value": "your-session-token-here",
     "domain": "www.perplexity.ai",
     "path": "/",
     "expires": 1765424168.176595,
     "httpOnly": true,
     "secure": true,
     "sameSite": "Lax"
   }]
   ```

3. **Required cookies:**
   - `pplx.session-id` - Your Perplexity session identifier
   - `__Secure-next-auth.session-token` - Your authentication session token
   - `next-auth.csrf-token` - CSRF protection token (optional but recommended)
   - `next-auth.callback-url` - Callback URL (optional but recommended)

4. **How to extract cookies:**
   - Log into Perplexity.ai in your browser
   - Open Developer Tools (F12)
   - Go to the Application/Storage tab
   - Navigate to Cookies > https://www.perplexity.ai
   - Copy the required cookie values into your `auth.json` file

> **Important:** The `auth.json` file is gitignored for security. Never commit your authentication cookies to version control.

## Usage

### Basic Usage

Run a search with a default query:

```bash
python -m src.search
```

### Custom Search Query

Provide your own search query as a command-line argument:

```bash
python -m src.search "What is GEO?"
```

### Examples

Research how LLMs view a specific product:
```bash
python -m src.search "What are the best project management tools for startups?"
```

Analyze competitor positioning:
```bash
python -m src.search "Compare Slack vs Microsoft Teams for remote teams"
```

Test brand visibility:
```bash
python -m src.search "What are the top CRM solutions for small businesses?"
```

### Expected Output

The tool will display progress as it runs:

```
🔍 Perplexity.ai Search Automation
================================

Query: "What is GEO?"

📋 Loading authentication cookies...
✓ Loaded 4 cookies from /path/to/auth.json
✓ All required authentication cookies present

🚀 Launching browser (headed mode)...
🔐 Setting authentication cookies...
✓ Cookies added to browser
🌐 Navigating to Perplexity.ai...
🔑 Verifying authentication status...
✓ Successfully authenticated!

🔎 Performing search...
✓ Found search input: [contenteditable="true"]
✓ Query entered: "What is GEO?"
✓ Search submitted
⏳ Waiting for search results...

═══════════════════════════════════════════════════════════
📊 SEARCH RESULTS
═══════════════════════════════════════════════════════════

ANSWER:
-------
[Perplexity's answer will appear here...]

SOURCES:
--------
1. Source Title
   https://example.com/source-url
2. Another Source
   https://example.com/another-source

═══════════════════════════════════════════════════════════

🧹 Cleaning up...
✓ Browser closed
```

A screenshot of the results page is automatically saved as `search-results-screenshot.png` for debugging purposes.

## How It Works

### Cookie-Based Authentication

The tool uses cookie-based authentication rather than username/password login. This approach:
- Avoids triggering Perplexity's login rate limits
- Bypasses CAPTCHA challenges
- Provides faster, more reliable authentication
- Allows for long-term automated access (until cookies expire)

### Nodriver for Bot Detection Bypass

This project uses **Nodriver** instead of Playwright or Selenium because:

1. **Advanced Anti-Detection**: Nodriver is specifically designed to bypass bot detection systems
2. **Stealth Mode**: It patches common detection vectors that sites use to identify automated browsers
3. **Chrome DevTools Protocol**: Uses CDP for more native browser control
4. **Better Success Rate**: Perplexity and similar sites have sophisticated bot detection that blocks standard automation tools

### Why Non-Headless Mode?

The browser runs in **headed mode** (visible window) because:
- Perplexity.ai actively detects and blocks headless browsers
- Running with a visible UI mimics real user behavior
- Many anti-bot systems specifically check for headless mode

### Current Limitations

**Detection**: While Nodriver significantly improves success rates, Perplexity may still occasionally detect automation. If you encounter issues:
- Ensure your cookies are fresh and valid
- Try running the script multiple times with delays between attempts
- Update your cookies if they've expired
- Consider using different search queries to avoid patterns

**Rate Limiting**: Excessive automated searches may trigger rate limiting. Use responsibly.

**Cookie Expiration**: Authentication cookies typically expire after 30 days. You'll need to refresh them periodically.

## Project Structure

```
geo-perplex/
├── src/
│   ├── __init__.py              # Package initialization
│   ├── search.py                # Main search automation script
│   └── utils/
│       ├── __init__.py          # Utils package initialization
│       └── cookies.py           # Cookie loading and validation utilities
├── auth.json                    # Your authentication cookies (gitignored)
├── auth.json.example            # Example cookie format
├── requirements.txt             # Python dependencies
├── README.md                    # This file
├── CLAUDE.md                    # Claude AI assistant instructions
└── venv/                        # Virtual environment (gitignored)
```

### Key Files

- **`src/search.py`**: Main automation script that orchestrates the entire search process
  - Loads cookies
  - Launches browser with Nodriver
  - Authenticates with Perplexity
  - Performs search
  - Extracts and displays results

- **`src/utils/cookies.py`**: Cookie management utilities
  - Loads cookies from `auth.json`
  - Validates required authentication cookies
  - Provides helpful error messages

- **`auth.json`**: Your personal authentication cookies (not tracked by git)

## Troubleshooting

### Common Issues

**Error: Cookie file not found**
- Make sure you've created `auth.json` in the project root
- Check that you're running the command from the project directory

**Error: Authentication failed - cookies may be expired or invalid**
- Your cookies have expired (typically after 30 days)
- Extract fresh cookies from your browser after logging into Perplexity.ai
- Ensure you copied all required cookie values correctly

**Error: Browser fails to launch**
- Ensure Chrome or Chromium is installed on your system
- Try running with sudo (Linux) if you encounter permission issues
- Check that your system meets Nodriver's requirements

**Error: Could not find search input element**
- Perplexity may have changed their UI structure
- Check the `search-results-screenshot.png` file to see what loaded
- The page might not have loaded completely - try increasing wait times in the code

**Browser opens but nothing happens**
- Check your internet connection
- Verify cookies are valid by logging into Perplexity in a regular browser
- Try manually navigating to perplexity.ai in the automated browser window

**Search completes but no results extracted**
- Wait time may be too short for answer generation (Perplexity can take 10-30 seconds)
- Perplexity's HTML structure may have changed
- Check the `search-results-screenshot.png` to see what was captured

### How to Refresh Cookies

When your cookies expire:

1. Open Chrome/Chromium browser
2. Navigate to https://www.perplexity.ai
3. Log in with your credentials
4. Open Developer Tools (F12 or Right-click > Inspect)
5. Go to Application tab (Chrome) or Storage tab (Firefox)
6. Click on Cookies > https://www.perplexity.ai
7. Find and copy the following cookies:
   - `pplx.session-id`
   - `__Secure-next-auth.session-token`
   - `next-auth.csrf-token`
   - `next-auth.callback-url`
8. Update your `auth.json` file with the new values
9. Include all cookie properties: name, value, domain, path, expires, httpOnly, secure, sameSite

## Technical Notes

### Why Non-Headless Mode is Required

Perplexity.ai (like many modern web applications) employs sophisticated bot detection that includes:
- Checking for headless browser indicators
- Monitoring mouse and keyboard patterns
- Analyzing browser fingerprints
- Detecting automation libraries

By running in headed mode with Nodriver's anti-detection features, the tool:
- Appears as a regular Chrome browser to detection systems
- Maintains realistic browser behavior
- Successfully bypasses most automation detection

### Detection Evasion Approach

The tool uses several strategies to avoid detection:

1. **Nodriver Library**: Built specifically for anti-detection
2. **Cookie Authentication**: Avoids triggering login-based detection
3. **Headed Mode**: Runs with visible UI like a real user
4. **Realistic Timing**: Includes appropriate waits between actions
5. **CDP Protocol**: Uses Chrome DevTools Protocol for native browser control

### Known Limitations

1. **Visual Requirement**: Must run on a system with display capabilities (not ideal for headless servers)
2. **Detection Risk**: Despite anti-detection measures, determined detection systems may still identify automation
3. **Maintenance**: Web scraping tools require updates when target sites change their structure
4. **Cookie Management**: Requires manual cookie refresh every 30 days
5. **Rate Limiting**: Excessive use may trigger Perplexity's rate limiting

### Future Improvements

Potential enhancements for future development:

- Automated cookie refresh mechanism
- Better result extraction with more robust selectors
- Support for multiple search queries in batch
- Export results to JSON/CSV format
- Headless mode using advanced evasion techniques
- Integration with proxy services for better reliability
- Retry logic with exponential backoff

## License

[Specify your license here]

## Contributing

[Specify contribution guidelines if applicable]

## Disclaimer

This tool is for research and educational purposes. Ensure your use complies with Perplexity.ai's Terms of Service. Automated access may violate ToS - use responsibly and at your own risk.
