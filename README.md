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

### Running Searches

#### Basic Usage

Run a search with a default query:

```bash
python -m src.search_cli
```

#### Custom Search Query

Provide your own search query:

```bash
python -m src.search_cli "What is GEO?"
```

#### Track AI Model

Specify which AI model you're using for later comparison:

```bash
python -m src.search_cli "What are the best CRM tools?" --model gpt-4
```

#### Disable Screenshots

Skip screenshot generation to save disk space:

```bash
python -m src.search_cli "What is Python?" --no-screenshot
```

#### Examples

Research how LLMs view a specific product:
```bash
python -m src.search_cli "What are the best project management tools for startups?" --model default
```

Analyze competitor positioning:
```bash
python -m src.search_cli "Compare Slack vs Microsoft Teams for remote teams" --model claude-3
```

Test brand visibility:
```bash
python -m src.search_cli "What are the top CRM solutions for small businesses?" --model gpt-4
```

### Analyzing Search Results

All search results are automatically saved to a SQLite database. Use the analysis tool to query and compare results:

#### View Recent Searches

```bash
# Show 10 most recent searches
python -m src.analyze recent

# Show 20 most recent searches with full answers
python -m src.analyze recent --limit 20 --full
```

#### List All Queries

```bash
python -m src.analyze list-queries
```

#### List All Models

```bash
python -m src.analyze list-models
```

#### Search by Query

View all results for a specific query:

```bash
python -m src.analyze query --query "What is GEO?"

# Filter by model
python -m src.analyze query --query "What is GEO?" --model gpt-4

# Show full answers
python -m src.analyze query --query "What is GEO?" --full
```

#### Search by Model

View all results from a specific model:

```bash
python -m src.analyze model --model gpt-4

# Limit results
python -m src.analyze model --model claude-3 --limit 10
```

#### Compare Models

Compare how different AI models answer the same query:

```bash
python -m src.analyze compare --query "What are the best project management tools?"

# Show full answers for comparison
python -m src.analyze compare --query "What is Python?" --full
```

### Expected Output

#### Search Execution

The tool will display progress as it runs:

```
🔍 Perplexity.ai Search Automation
================================

Query: "What is GEO?"
Model: gpt-4

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

💾 Saving results to database...
✓ Saved as record ID: 42
✓ Execution time: 15.32s

🧹 Cleaning up...
✓ Browser closed
```

Screenshots are automatically saved in the `screenshots/` directory with unique timestamped filenames (unless `--no-screenshot` is used).

#### Analysis Output

When analyzing stored results:

```bash
$ python -m src.analyze recent --limit 2
```

```
📊 Most recent 2 search results:

================================================================================
ID: 42
Query: What is GEO?
Model: gpt-4
Timestamp: 2025-11-11 14:30:45
Execution Time: 15.32s
Success: ✓
Screenshot: screenshots/20251111_143045_a1b2c3d4.png

Answer (297 chars):
--------------------------------------------------------------------------------
Generative Engine Optimization (GEO) is a field focused on optimizing content
for AI-powered search engines and language models...

Sources (2):
--------------------------------------------------------------------------------
1. GEO Guide
   https://example.com/geo-guide
2. AI Search Optimization
   https://example.com/ai-search

================================================================================
ID: 41
Query: What are the best CRM tools?
Model: default
Timestamp: 2025-11-11 14:25:12
Execution Time: 12.84s
Success: ✓
...
```

## How It Works

### Database Storage

All search results are automatically saved to a SQLite database (`search_results.db`) with the following information:
- **Query text**: The search query submitted
- **Answer text**: The full response from Perplexity
- **Sources**: List of cited sources with URLs
- **Model**: The AI model used (if specified)
- **Timestamp**: When the search was performed
- **Execution time**: How long the search took
- **Screenshot path**: Location of the saved screenshot
- **Success status**: Whether the search completed successfully
- **Error messages**: Details of any failures

This allows you to:
- Track how different AI models respond to the same query
- Analyze changes in responses over time
- Build a research database for GEO analysis
- Compare competitor mentions across queries
- Export data for further analysis

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
│   ├── analyze.py               # Results analysis and comparison CLI
│   └── utils/
│       ├── __init__.py          # Utils package initialization
│       ├── cookies.py           # Cookie loading and validation utilities
│       └── storage.py           # SQLite database storage utilities
├── screenshots/                 # Screenshot storage (gitignored)
├── search_results.db            # SQLite database (gitignored)
├── auth.json                    # Your authentication cookies (gitignored)
├── auth.json.example            # Example cookie format
├── requirements.txt             # Python dependencies
├── README.md                    # This file
├── CLAUDE.md                    # Claude AI assistant instructions
└── venv/                        # Virtual environment (gitignored)
```

### Key Files

- **`src/search_cli.py`**: Main CLI orchestration that coordinates modular components
- **`src/browser/`**: Browser automation modules (manager, auth, interactions)
- **`src/search/`**: Search execution and extraction modules
  - Loads cookies and validates authentication
  - Launches browser with Nodriver in headed mode
  - Authenticates with Perplexity using cookies
  - Performs search and extracts results
  - Saves results to database
  - Generates screenshots with unique filenames

- **`src/analyze.py`**: Results analysis and comparison CLI tool
  - Query search results by text, model, or date
  - Compare how different AI models answer the same query
  - List all unique queries and models in database
  - View recent search history
  - Export data for further analysis

- **`src/utils/cookies.py`**: Cookie management utilities
  - Loads cookies from `auth.json`
  - Validates required authentication cookies
  - Provides helpful error messages

- **`src/utils/storage.py`**: SQLite database utilities
  - Initialize database schema with proper indexes
  - Save search results with metadata
  - Query results by query text, model, or timestamp
  - Compare results across different models
  - Retrieve unique queries and models

- **`auth.json`**: Your personal authentication cookies (not tracked by git)

- **`search_results.db`**: SQLite database containing all search results (not tracked by git)

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

### Database Management

**Location**: The database is stored at `search_results.db` in the project root directory.

**Backup**: To backup your research data, simply copy the `search_results.db` file:
```bash
cp search_results.db search_results_backup_$(date +%Y%m%d).db
```

**Reset**: To start fresh, delete the database file (it will be recreated on next search):
```bash
rm search_results.db
```

**Direct Access**: You can query the database directly with any SQLite client:
```bash
sqlite3 search_results.db "SELECT query, model, timestamp FROM search_results ORDER BY timestamp DESC LIMIT 10;"
```

### Future Improvements

Potential enhancements for future development:

- Automated cookie refresh mechanism
- Better result extraction with more robust selectors
- Support for multiple search queries in batch mode
- Export results to JSON/CSV/Excel formats
- Headless mode using advanced evasion techniques
- Integration with proxy services for better reliability
- Retry logic with exponential backoff
- Web dashboard for visualizing GEO trends
- Automated model switching within Perplexity UI
- Statistical analysis of brand/product mentions
- Integration with other AI search engines (ChatGPT, Claude, etc.)

## License

[Specify your license here]

## Contributing

[Specify contribution guidelines if applicable]

## Disclaimer

This tool is for research and educational purposes. Ensure your use complies with Perplexity.ai's Terms of Service. Automated access may violate ToS - use responsibly and at your own risk.
