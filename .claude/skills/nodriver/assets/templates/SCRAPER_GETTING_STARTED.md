# Web Scraper Template - Getting Started

Welcome! This guide will get you scraping in minutes.

## What You Have

A complete web scraper template with:
- **700 lines** of production-ready Python code
- **7 real-world examples** showing different patterns
- **4 documentation files** covering everything
- **100% type hints** and docstrings
- **Comprehensive error handling** and logging
- **Human-like behavior** patterns built-in
- **Cookie/session management** for authenticated sites

## Files You Need

1. **`basic_scraper.py`** - The main template (copy this to your project)
2. **`README_SCRAPER.md`** - Full documentation (reference while coding)
3. **`SCRAPER_QUICK_REFERENCE.md`** - Quick lookup (for syntax reminders)
4. **`scraper_examples.py`** - 7 working examples (find one matching your use case)

## 5-Minute Quick Start

### Step 1: Install nodriver

```bash
pip install nodriver
```

### Step 2: Copy the Template

Copy `basic_scraper.py` to your project directory.

### Step 3: Write Your First Scraper

Create a file `my_scraper.py`:

```python
import asyncio
from basic_scraper import BasicScraper

async def main():
    # Create scraper
    scraper = BasicScraper(url="https://example.com")

    # Tell it what to extract
    scraper.set_extractors(
        item_selector="div.item",  # CSS selector for each item
        fields={
            "title": "h2",         # Field name -> CSS selector
            "description": "p",
            "link": "a",
        }
    )

    # Scrape and save
    try:
        data = await scraper.scrape()
        scraper.export_csv("results.csv")
        print(f"Scraped {len(data)} items!")
    finally:
        await scraper.cleanup()

# Run it
asyncio.run(main())
```

### Step 4: Run It

```bash
python my_scraper.py
```

That's it! You have a working scraper.

## Common Tasks

### Task: Scrape a Product Listing

```python
scraper = BasicScraper(url="https://shop.example.com/products")

scraper.set_extractors(
    item_selector="div.product-card",
    fields={
        "name": "h2.product-name",
        "price": "span.price",
        "rating": "span.rating",
        "url": "a.product-link",
    }
)

data = await scraper.scrape()
scraper.export_csv("products.csv")
```

### Task: Scrape Multiple Pages

```python
scraper.set_pagination(
    next_button="a.next-page",  # CSS selector for next button
    max_pages=5,                 # Stop after 5 pages
)

data = await scraper.scrape()  # Automatically handles pagination
```

### Task: Scrape a Table

```python
scraper.set_extractors(
    item_selector="table tbody tr",  # Each row is an item
    fields={
        "col1": "td:nth-child(1)",    # Column 1
        "col2": "td:nth-child(2)",    # Column 2
        "col3": "td:nth-child(3)",    # Column 3
    }
)
```

### Task: Complex Extraction (Custom Function)

```python
async def extract_product(element, page):
    name = await element.find("h2")
    name_text = await name.text if name else "N/A"

    price_elem = await element.find("span.price")
    price = await price_elem.text if price_elem else "N/A"

    return {
        "name": name_text.strip(),
        "price": price.strip(),
    }

scraper.set_extractors(
    item_selector="div.product",
    fields={},  # Not used with custom function
    extractor_func=extract_product
)
```

### Task: Faster Scraping

```python
from basic_scraper import ScraperConfig

config = ScraperConfig(
    disable_images=True,        # Skip images
    human_behavior=False,       # No delays
    timeout=15.0,              # Quick timeout
)

scraper = BasicScraper(url="https://example.com", config=config)
```

### Task: Stealth Scraping (Avoid Getting Blocked)

```python
config = ScraperConfig(
    human_behavior=True,        # Natural delays
    enable_cookies=True,        # Session persistence
    disable_images=False,       # Let images load
    user_agent="Mozilla/5.0...", # Custom user agent
)

scraper = BasicScraper(url="https://example.com", config=config)
```

### Task: Save and Load Cookies (Stay Logged In)

```python
# First time (login manually if needed)
config = ScraperConfig(enable_cookies=True)
scraper = BasicScraper(url="https://protected.com", config=config)
data = await scraper.scrape()

# Cookies automatically saved to .cookies/

# Second time (cookies loaded automatically)
scraper2 = BasicScraper(url="https://protected.com", config=config)
data = await scraper2.scrape()  # Uses saved session
```

## Debugging Tips

### Check Your Selectors

Open the website in your browser, then in the console:

```javascript
// Count items
document.querySelectorAll("div.product").length

// Check if field selector works
document.querySelector("div.product h2").textContent
```

### Enable Verbose Logging

```python
scraper = BasicScraper(url="https://example.com", verbose=True)
```

This prints detailed logs showing what's happening.

### Take Screenshots on Error

```python
config = ScraperConfig(screenshot_on_error=True)
scraper = BasicScraper(url="https://example.com", config=config)
```

If scraping fails, check `screenshots/error_*.png`.

### Check Extracted Data

```python
data = await scraper.scrape()

if data:
    print("First item:", data[0].data)
    print("URL:", data[0].url)
    print("Page:", data[0].page)
else:
    print("No items extracted - check selectors!")
```

## Common Issues

### Issue: "Browser failed to initialize"

**Solution**: Ensure Chrome/Chromium is installed
```bash
# Ubuntu/Debian
sudo apt-get install chromium-browser

# macOS
brew install chromium

# Windows
# Download from https://www.chromium.org/
```

### Issue: "No items found"

**Solution**: Check your CSS selectors

1. Open the website in Chrome
2. Press F12 (Developer Tools)
3. Click the element picker (top-left icon)
4. Click an item on the page
5. Copy the selector that appears
6. Update your `item_selector`

### Issue: "Pagination not working"

**Solution**: Verify the next button selector exists

```python
# In browser console:
document.querySelectorAll("a.next-page").length  # Should return > 0
```

### Issue: "Data is incomplete (missing fields)"

**Solution**: Increase timeout or check if page is loading dynamically

```python
config = ScraperConfig(timeout=45.0)  # Longer timeout
scraper = BasicScraper(url="...", config=config)

# Wait longer for JS to load
await asyncio.sleep(3.0)
```

### Issue: "Getting blocked/rate limited"

**Solution**: Enable human behavior and add delays

```python
config = ScraperConfig(
    human_behavior=True,        # Key!
    timeout=30.0,
)

# Add delay between pages
await asyncio.sleep(5.0)
```

## Next Steps

### Want More Details?
- See `README_SCRAPER.md` for complete documentation
- See `SCRAPER_QUICK_REFERENCE.md` for syntax lookup
- See `SCRAPER_TEMPLATE_INDEX.md` for navigation

### Want to See Examples?
- Run `python scraper_examples.py`
- Covers 7 different scenarios
- All fully working examples

### Want Advanced Features?
- Custom extraction functions (see Example 4)
- Error recovery (see Example 5)
- Data validation (see Example 6)
- Cookie management (see Example 7)

## Configuration Cheat Sheet

```python
config = ScraperConfig(
    # Performance
    disable_images=True,        # Faster loading
    timeout=15.0,              # Quick timeout

    # Behavior
    human_behavior=True,        # Natural delays
    enable_cookies=True,        # Session persistence

    # Reliability
    retry_attempts=5,          # More retries
    retry_delay=3.0,          # Longer delays

    # Debugging
    screenshot_on_error=True,   # Save screenshots
    verbose=True,               # Detailed logs
)
```

## Export Formats

### CSV (Good for spreadsheets)
```python
scraper.export_csv("data.csv")
```
Creates: `data.csv` with columns for each field

### JSON (Good for APIs)
```python
scraper.export_json("data.json")
```
Creates: `data.json` with metadata and items

## Code Pattern Template

Use this as a starting point:

```python
import asyncio
from basic_scraper import BasicScraper, ScraperConfig

async def main():
    # 1. Configure
    config = ScraperConfig(
        headless=True,
        disable_images=True,
        human_behavior=True,
    )

    # 2. Initialize
    scraper = BasicScraper(
        url="https://example.com/items",
        config=config,
        verbose=True,
    )

    # 3. Configure extraction
    scraper.set_extractors(
        item_selector="div.item",
        fields={
            "field1": "selector1",
            "field2": "selector2",
        }
    )

    # 4. Optional: Configure pagination
    scraper.set_pagination(
        next_button="a.next",
        max_pages=5,
    )

    # 5. Scrape
    try:
        data = await scraper.scrape()

        # 6. Export
        scraper.export_csv("results.csv")
        scraper.export_json("results.json")

        # 7. Check results
        print(f"Scraped {len(data)} items")

    except Exception as e:
        print(f"Error: {e}")

    finally:
        await scraper.cleanup()

# Run
asyncio.run(main())
```

## Pro Tips

1. **Start Simple**: Get basic scraping working first, then add features
2. **Test Selectors**: Verify CSS selectors in browser console before using
3. **Use Verbose Mode**: While developing, use `verbose=True` to see what's happening
4. **Save Progress**: For long scraping runs, export results every N pages
5. **Check robots.txt**: Verify you're allowed to scrape the site
6. **Be Respectful**: Add delays between pages, respect rate limits
7. **Validate Data**: Check that extracted data is correct
8. **Handle Errors**: Always use try/finally to clean up

## Key Methods

```python
# Setup
scraper.set_extractors(item_selector, fields, extractor_func=None)
scraper.set_pagination(next_button, max_pages=10)

# Main workflow
await scraper.navigate(url)        # Go to page
await scraper.extract_page()       # Get items from current page
await scraper.goto_next_page()     # Go to next page
await scraper.scrape()             # Do complete scraping

# Export
scraper.export_csv(filepath)
scraper.export_json(filepath)
scraper.get_statistics()

# Cleanup
await scraper.cleanup()
```

## File Locations

All scraper files are in:
```
.claude/skills/nodriver/assets/templates/
├── basic_scraper.py                 ← Copy this
├── README_SCRAPER.md               ← Read this
├── SCRAPER_QUICK_REFERENCE.md      ← Reference this
├── scraper_examples.py              ← Learn from this
├── SCRAPER_TEMPLATE_INDEX.md       ← Navigate with this
├── SCRAPER_MANIFEST.md             ← Know what's available
└── SCRAPER_GETTING_STARTED.md      ← You are here
```

## Summary

You now have everything needed to:
- Scrape any website quickly
- Handle pagination automatically
- Export to CSV/JSON
- Manage sessions with cookies
- Avoid getting blocked
- Handle errors gracefully
- Validate data quality

**Next Step**: Copy `basic_scraper.py` and start scraping!

---

**Need Help?**
1. Check your CSS selectors in browser
2. Enable verbose logging: `verbose=True`
3. Read the relevant example in `scraper_examples.py`
4. Check `SCRAPER_QUICK_REFERENCE.md` for syntax
5. See `README_SCRAPER.md` for detailed documentation

**Happy Scraping!**
