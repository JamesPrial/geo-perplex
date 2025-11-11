# Web Scraper Template Guide

A production-ready web scraper template built with `nodriver` that provides comprehensive functionality for scraping modern web applications.

## Features

### Core Functionality
- **Async Setup**: Complete async/await support with proper initialization
- **Navigation with Retry Logic**: Automatic retry mechanism for failed page loads
- **Data Extraction**: Flexible CSS selector-based or custom extraction functions
- **Pagination**: Built-in pagination handling with max page limits
- **Export Formats**: JSON and CSV export with metadata

### Advanced Features
- **Human-Like Behavior**: Natural delays, scrolling patterns, and interaction timing
- **Session Management**: Cookie persistence across sessions
- **Error Handling**: Screenshot capture on errors, comprehensive logging
- **Graceful Cleanup**: Proper resource cleanup with async context handling
- **Configuration**: Fully customizable via `ScraperConfig` dataclass

## Installation

Ensure `nodriver` is installed:

```bash
pip install nodriver
```

## Quick Start

### Basic Scraping

```python
import asyncio
from basic_scraper import BasicScraper

async def main():
    scraper = BasicScraper(url="https://example.com/products")

    # Configure what to extract
    scraper.set_extractors(
        item_selector="div.product",
        fields={
            "name": "h2.title",
            "price": "span.price",
        }
    )

    # Scrape and export
    data = await scraper.scrape()
    scraper.export_json("products.json")
    scraper.export_csv("products.csv")

asyncio.run(main())
```

### Scraping with Pagination

```python
async def scrape_all_pages():
    scraper = BasicScraper(
        url="https://example.com/products",
        verbose=True
    )

    # Configure extraction
    scraper.set_extractors(
        item_selector="div.product-card",
        fields={
            "title": "h3",
            "price": "span.price",
            "rating": "span.rating",
            "link": "a.product-link",
        }
    )

    # Configure pagination
    scraper.set_pagination(
        next_button="a.next-page",
        max_pages=5,
    )

    # Run scraper
    items = await scraper.scrape()

    # Export results
    scraper.export_csv("all_products.csv")
    stats = scraper.get_statistics()
    print(f"Scraped {stats['total_items']} items across {stats['pages_scraped']} pages")

asyncio.run(scrape_all_pages())
```

## Configuration

### ScraperConfig Options

```python
from basic_scraper import ScraperConfig, BasicScraper

config = ScraperConfig(
    # Browser settings
    headless=True,                      # Run in headless mode
    disable_images=True,                # Disable image loading for speed
    user_agent="Custom UA string",      # Custom user agent

    # Behavior settings
    human_behavior=True,                # Use human-like delays
    enable_cookies=True,                # Save/load cookies

    # Navigation settings
    timeout=30.0,                       # Page load timeout (seconds)
    retry_attempts=3,                   # Number of retry attempts
    retry_delay=2.0,                    # Delay between retries (seconds)

    # Error handling
    screenshot_on_error=True,           # Take screenshot on error
    screenshot_dir="screenshots",       # Directory for screenshots

    # Session settings
    cookies_dir=".cookies",             # Directory for cookie storage

    # Viewport settings
    viewport_width=1920,
    viewport_height=1080,
)

scraper = BasicScraper(url="https://example.com", config=config)
```

## Core Classes and Methods

### BasicScraper

Main scraper class that handles all operations.

#### Initialization

```python
scraper = BasicScraper(
    url: str,                           # URL to scrape
    config: Optional[ScraperConfig],    # Configuration (uses defaults if None)
    verbose: bool = True                # Enable logging
)
```

#### Configuration Methods

##### set_extractors()

Configure how to extract data from the page:

```python
scraper.set_extractors(
    item_selector="div.item",           # CSS selector for each item
    fields={                            # Field name -> CSS selector mapping
        "title": "h2.title",
        "description": "p.desc",
        "link": "a.item-link",
    },
    extractor_func=None                 # Optional custom extraction function
)
```

The `fields` parameter maps field names to CSS selectors within each item element.

##### set_pagination()

Enable pagination support:

```python
scraper.set_pagination(
    next_button="a.next",               # CSS selector for next page button
    max_pages=10,                       # Maximum pages to scrape
    wait_for_load=True                  # Wait for page load after pagination
)
```

#### Scraping Methods

##### navigate()

Navigate to a URL with retry logic:

```python
success = await scraper.navigate(url="https://example.com/page2")
if not success:
    print("Navigation failed after all retries")
```

##### extract_page()

Extract all items from the current page:

```python
items = await scraper.extract_page()
print(f"Extracted {len(items)} items from current page")

for item in items:
    print(item.data)
    print(item.url)
    print(item.page)
```

##### goto_next_page()

Navigate to the next page (if pagination is configured):

```python
has_next = await scraper.goto_next_page()
if has_next:
    print(f"Now on page {scraper.current_page}")
```

##### scrape()

Perform complete scraping operation (main method):

```python
try:
    data = await scraper.scrape()
    print(f"Successfully scraped {len(data)} items")
except RuntimeError as e:
    print(f"Scraping failed: {e}")
```

#### Export Methods

##### export_json()

Export data to JSON format:

```python
scraper.export_json("output.json")
# Creates: {
#   "metadata": {
#     "url": "...",
#     "timestamp": "...",
#     "total_items": 42,
#     "pages_scraped": 2
#   },
#   "items": [...]
# }
```

##### export_csv()

Export data to CSV format:

```python
scraper.export_csv("output.csv")
# Creates CSV with columns for each field plus metadata columns:
# - _url: Source URL
# - _timestamp: Extraction timestamp
# - _page: Page number
```

##### get_statistics()

Get scraping statistics:

```python
stats = scraper.get_statistics()
print(stats)
# Output: {
#   "total_items": 100,
#   "pages_scraped": 5,
#   "status": "complete",
#   "timestamp": "2024-..."
# }
```

### ScrapedItem

Represents a single scraped item:

```python
item = ScrapedItem(
    data={"name": "Product X", "price": "$19.99"},
    url="https://example.com/page1",
    timestamp="2024-01-01T12:00:00",
    page=1
)

# Access data
print(item.data["name"])
print(item.url)
print(item.page)

# Convert to dictionary (for export)
dict_data = item.to_dict()
```

## Advanced Usage

### Custom Extraction Function

Use a custom function for complex extraction logic:

```python
async def custom_extractor(element, page):
    """Custom extraction logic."""
    # Extract text
    title_elem = await element.find("h2")
    title = await title_elem.text if title_elem else "N/A"

    # Extract attribute
    link_elem = await element.find("a")
    link = await link_elem.get_attribute("href") if link_elem else None

    # Run JavaScript for dynamic content
    price = await page.evaluate(
        "document.querySelector('.price').textContent"
    )

    return {
        "title": title.strip(),
        "link": link,
        "price": price,
    }

scraper.set_extractors(
    item_selector="div.product",
    fields={},  # Not used with custom function
    extractor_func=custom_extractor
)
```

### Handling JavaScript-Heavy Sites

For sites with dynamic content:

```python
config = ScraperConfig(
    headless=False,  # Disable headless for debugging
    human_behavior=True,
    timeout=45.0,  # Longer timeout for complex sites
)

scraper = BasicScraper(url="https://complex-spa.com", config=config)

# Optionally wait for specific elements
async def scrape_spa():
    await scraper.navigate()

    # Wait for dynamic content to load
    await asyncio.sleep(3.0)

    # Extract when ready
    items = await scraper.extract_page()
    return items
```

### Filtering Results

Filter extracted items after scraping:

```python
data = await scraper.scrape()

# Filter by price
expensive_items = [
    item for item in data
    if float(item.data.get("price", 0)) > 100
]

# Filter by content
items_with_rating = [
    item for item in data
    if item.data.get("rating") is not None
]
```

### Dealing with Anti-Bot Protection

For sites with anti-bot measures:

```python
config = ScraperConfig(
    headless=True,
    human_behavior=True,  # Critical for avoiding detection
    disable_images=True,  # Faster, less detectable
    user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) ...",
    timeout=40.0,
    retry_attempts=5,
)

scraper = BasicScraper(url="https://strict-site.com", config=config)
```

## Error Handling

### Automatic Error Handling

Errors are logged and screenshots are taken:

```python
try:
    data = await scraper.scrape()
except RuntimeError as e:
    print(f"Scraping failed: {e}")
    # Screenshot saved to screenshots/error_YYYYMMDD_HHMMSS.png
```

### Manual Error Handling

Handle errors within extraction:

```python
async def safe_scrape():
    try:
        await scraper.navigate()
        items = await scraper.extract_page()

        # Validate items
        valid_items = []
        for item in items:
            if item.data.get("name") and item.data.get("price"):
                valid_items.append(item)

        print(f"Valid items: {len(valid_items)}/{len(items)}")

    except Exception as e:
        print(f"Error: {e}")
        # Continue gracefully
    finally:
        await scraper.cleanup()
```

## Best Practices

### 1. Always Use Async Context

Always use async/await and proper cleanup:

```python
async def safe_scraper():
    scraper = BasicScraper(url="https://example.com")
    try:
        data = await scraper.scrape()
        return data
    finally:
        await scraper.cleanup()

data = asyncio.run(safe_scraper())
```

### 2. Start Simple

Begin with simple extraction, then add complexity:

```python
# Step 1: Basic extraction
scraper.set_extractors(
    item_selector="div.item",
    fields={"title": "h2"}
)

# Step 2: Add more fields
scraper.set_extractors(
    item_selector="div.item",
    fields={
        "title": "h2",
        "price": "span.price",
        "link": "a"
    }
)

# Step 3: Add pagination
scraper.set_pagination(next_button="a.next", max_pages=5)
```

### 3. Respect Rate Limits

Human-like behavior helps avoid rate limiting:

```python
config = ScraperConfig(
    human_behavior=True,  # Natural delays
)

# Additional courtesy delay between pages
async def respectful_scrape():
    scraper = BasicScraper(url="https://example.com", config=config)
    await scraper.navigate()
    await scraper.extract_page()

    # Extra delay between pages
    await asyncio.sleep(5.0)

    if await scraper.goto_next_page():
        await scraper.extract_page()
```

### 4. Monitor and Debug

Use verbose mode and logging:

```python
import logging

# Enable detailed logging
logging.basicConfig(level=logging.DEBUG)

scraper = BasicScraper(
    url="https://example.com",
    verbose=True  # Print detailed logs
)

data = asyncio.run(scraper.scrape())
```

### 5. Validate Extracted Data

Always validate data quality:

```python
data = await scraper.scrape()

# Check for empty results
if not data:
    print("Warning: No data extracted")

# Check data quality
incomplete_items = [
    item for item in data
    if None in item.data.values()
]

if incomplete_items:
    print(f"Warning: {len(incomplete_items)} items have missing fields")
```

## Common Patterns

### Pattern 1: Table Scraping

```python
scraper = BasicScraper(url="https://example.com/table")

scraper.set_extractors(
    item_selector="table tbody tr",
    fields={
        "col1": "td:nth-child(1)",
        "col2": "td:nth-child(2)",
        "col3": "td:nth-child(3)",
    }
)

data = await scraper.scrape()
scraper.export_csv("table_data.csv")
```

### Pattern 2: Product Listing

```python
scraper = BasicScraper(url="https://shop.example.com/products")

scraper.set_extractors(
    item_selector="div.product-card",
    fields={
        "name": "h3.product-name",
        "price": "span.price",
        "rating": "div.rating",
        "url": "a.product-link",
    }
)

scraper.set_pagination(
    next_button="a.pagination-next",
    max_pages=10
)

data = await scraper.scrape()
scraper.export_json("products.json")
```

### Pattern 3: Dynamic Content

```python
async def scrape_spa():
    config = ScraperConfig(timeout=45.0)
    scraper = BasicScraper(url="https://spa.example.com", config=config)

    await scraper.navigate()

    # Wait for JavaScript to load content
    await asyncio.sleep(3.0)

    # Scroll to trigger lazy loading
    if scraper.behavior:
        await scraper.behavior.scroll_naturally(scraper.page)

    # Extract when ready
    scraper.set_extractors(
        item_selector="div.dynamic-item",
        fields={"content": "p"}
    )

    return await scraper.extract_page()
```

## Troubleshooting

### Issue: "nodriver is not installed"

**Solution**: Install nodriver package

```bash
pip install nodriver
```

### Issue: Browser fails to initialize

**Solution**: Ensure Chrome/Chromium is installed and accessible

```bash
# Ubuntu/Debian
sudo apt-get install chromium-browser

# macOS
brew install chromium

# Or use existing Chrome installation
```

### Issue: Elements not found

**Solution**: Verify CSS selectors

```python
# Test selector in browser console first
# Debug with screenshots
config = ScraperConfig(screenshot_on_error=True)
```

### Issue: Pagination doesn't work

**Solution**: Check pagination selector and button state

```python
# Verify next button exists
scraper.set_pagination(
    next_button="a.next",  # Check this selector
    max_pages=2,
)

# Add debugging
items = await scraper.extract_page()
print(f"Extracted {len(items)} items")
```

### Issue: Data quality issues

**Solution**: Validate and filter results

```python
data = await scraper.scrape()

# Validate
valid = [item for item in data if all(item.data.values())]
print(f"Valid items: {len(valid)}/{len(data)}")
```

## Performance Tips

1. **Disable Images**: Speeds up page loading
   ```python
   config = ScraperConfig(disable_images=True)
   ```

2. **Reduce Timeouts**: After testing, lower timeout for fast sites
   ```python
   config = ScraperConfig(timeout=15.0)
   ```

3. **Batch Operations**: Scrape multiple pages in parallel (with caution)
   ```python
   tasks = [scraper.scrape() for _ in range(3)]
   results = await asyncio.gather(*tasks)
   ```

4. **Limit Max Pages**: Don't scrape unnecessary pages
   ```python
   scraper.set_pagination(next_button="a.next", max_pages=5)
   ```

## Summary

This template provides everything needed for professional web scraping:

- Clean, async-first architecture
- Comprehensive error handling
- Human-like behavior patterns
- Flexible data extraction
- Multiple export formats
- Production-ready code

Adapt and extend it for your specific scraping needs!
