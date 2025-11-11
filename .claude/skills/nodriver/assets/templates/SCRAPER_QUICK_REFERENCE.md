# Web Scraper Template - Quick Reference

Quick lookup guide for common scraping tasks.

## Basic Setup

```python
import asyncio
from basic_scraper import BasicScraper, ScraperConfig

async def main():
    scraper = BasicScraper(url="https://example.com")
    try:
        data = await scraper.scrape()
        scraper.export_csv("output.csv")
    finally:
        await scraper.cleanup()

asyncio.run(main())
```

## Configuration Quick Reference

```python
config = ScraperConfig(
    headless=True,              # Run in headless mode
    disable_images=True,        # Disable images for speed
    human_behavior=True,        # Use human-like delays
    enable_cookies=True,        # Save/load cookies
    timeout=30.0,              # Page load timeout
    retry_attempts=3,          # Number of retries
    screenshot_on_error=True,  # Screenshot on error
)
```

## Common Extraction Patterns

### Pattern: CSS Selectors

```python
scraper.set_extractors(
    item_selector="div.product",
    fields={
        "title": "h2.title",
        "price": "span.price",
        "link": "a.product-link",
    }
)
```

### Pattern: Nth-child Selection (Table Columns)

```python
scraper.set_extractors(
    item_selector="tr",
    fields={
        "col1": "td:nth-child(1)",
        "col2": "td:nth-child(2)",
        "col3": "td:nth-child(3)",
    }
)
```

### Pattern: Nested Elements

```python
scraper.set_extractors(
    item_selector="div.item",
    fields={
        "title": "h2",
        "description": "div.content p",
        "metadata": "span.date",
    }
)
```

### Pattern: Attribute Extraction

```python
scraper.set_extractors(
    item_selector="a.item",
    fields={
        "url": "a",  # href attribute
        "text": "span.title",
    }
)
```

## Pagination Patterns

### Basic Pagination

```python
scraper.set_pagination(
    next_button="a.next",
    max_pages=10,
)
```

### Pagination with Button Classes

```python
scraper.set_pagination(
    next_button="button.pagination-next:not([disabled])",
    max_pages=20,
)
```

### Manual Pagination Loop

```python
while scraper.current_page <= scraper.max_pages:
    items = await scraper.extract_page()
    # Process items
    if not await scraper.goto_next_page():
        break
    await asyncio.sleep(2.0)  # Delay between pages
```

## Export Formats

### Export to JSON

```python
scraper.export_json("output.json")
# Creates: {metadata: {...}, items: [...]}
```

### Export to CSV

```python
scraper.export_csv("output.csv")
# Creates: CSV with all fields + metadata columns
```

### Custom Processing

```python
data = await scraper.scrape()

# Filter
clean_data = [
    item for item in data
    if item.data.get("price")
]

# Transform
for item in clean_data:
    item.data["price"] = float(item.data["price"])

# Export
scraper.scraped_items = clean_data
scraper.export_csv("filtered.csv")
```

## Common Selectors

| Task | Selector |
|------|----------|
| All divs | `div` |
| Class | `.classname` |
| ID | `#idname` |
| Attribute | `[attr="value"]` |
| Nth child | `:nth-child(n)` |
| First child | `:first-child` |
| Last child | `:last-child` |
| Not selector | `:not(.disabled)` |
| Contains | Contains (use JavaScript) |

## Debugging Tips

### Enable Verbose Logging

```python
scraper = BasicScraper(url="https://example.com", verbose=True)
```

### Check Extraction Configuration

```python
print(f"Item selector: {scraper.item_selector}")
print(f"Fields: {scraper.field_selectors}")
print(f"Max pages: {scraper.max_pages}")
```

### Validate Selectors

Open browser console on target site:

```javascript
// Test selector
document.querySelectorAll("div.product").length

// Get specific element
document.querySelector("h2.title").textContent
```

### Check Extracted Data

```python
data = await scraper.scrape()
if data:
    print(data[0].data)  # First item
    print(data[0].url)   # Source URL
    print(data[0].page)  # Page number
```

### Screenshot on Error

```python
config = ScraperConfig(screenshot_on_error=True)
scraper = BasicScraper(url="https://example.com", config=config)
# Screenshot saved to screenshots/error_*.png on failure
```

## Error Handling

### Try-Finally Pattern

```python
scraper = BasicScraper(url="https://example.com")
try:
    data = await scraper.scrape()
except RuntimeError as e:
    print(f"Scraping failed: {e}")
finally:
    await scraper.cleanup()
```

### Retry Configuration

```python
config = ScraperConfig(
    retry_attempts=5,    # More retries
    retry_delay=3.0,     # Longer delay
    timeout=45.0,        # Longer timeout
)
```

### Manual Error Handling

```python
try:
    if not await scraper.navigate():
        print("Navigation failed")
        return

    items = await scraper.extract_page()
except Exception as e:
    print(f"Error: {e}")
```

## Performance Tips

| Setting | Benefit |
|---------|---------|
| `disable_images=True` | Faster loading |
| `timeout=15.0` | Quick fail |
| `max_pages=5` | Limited scope |
| `human_behavior=False` | Speed (less detected) |
| `headless=True` | Lower resource usage |

## Human Behavior Configuration

```python
from basic_scraper import BehaviorConfig, InteractionStyle

# Available styles:
# - MINIMAL: Very little interaction
# - CAUTIOUS: Limited, careful
# - NORMAL: Natural patterns (default)
# - ENGAGED: Frequent interaction

config = ScraperConfig(human_behavior=True)
```

## Cookie Management

```python
# Enable cookies
config = ScraperConfig(enable_cookies=True)

# Cookies auto-saved to .cookies/
# Loaded automatically on next run
scraper = BasicScraper(url="https://example.com", config=config)
```

## Navigation

### Navigate to URL

```python
success = await scraper.navigate(url="https://example.com/page")
if success:
    print("Navigation successful")
```

### Navigate Current Page

```python
await scraper.navigate()  # Uses self.url
```

## Data Structures

### ScrapedItem

```python
item = ScrapedItem(
    data={"field1": "value1", "field2": "value2"},
    url="https://source-url.com",
    timestamp="2024-01-01T12:00:00",
    page=1,
)

# Convert to dict
item_dict = item.to_dict()
# Includes metadata: _url, _timestamp, _page
```

## Statistics

```python
stats = scraper.get_statistics()
print(f"Items: {stats['total_items']}")
print(f"Pages: {stats['pages_scraped']}")
print(f"Status: {stats['status']}")
print(f"Time: {stats['timestamp']}")
```

## Common Mistakes

### Mistake 1: Not Cleaning Up

**Wrong:**
```python
scraper = BasicScraper(url="https://example.com")
data = await scraper.scrape()
# Browser left open!
```

**Right:**
```python
scraper = BasicScraper(url="https://example.com")
try:
    data = await scraper.scrape()
finally:
    await scraper.cleanup()
```

### Mistake 2: Hardcoding Selectors

**Wrong:**
```python
# Breaks if site changes HTML
fields = {
    "title": "div > div > h2",
}
```

**Right:**
```python
# More resilient to changes
fields = {
    "title": "h2.product-title",
}
```

### Mistake 3: Not Validating Data

**Wrong:**
```python
data = await scraper.scrape()
scraper.export_csv("output.csv")  # May include invalid items
```

**Right:**
```python
data = await scraper.scrape()
valid = [item for item in data if item.data.get("price")]
scraper.scraped_items = valid
scraper.export_csv("output.csv")
```

### Mistake 4: Ignoring Rate Limits

**Wrong:**
```python
config = ScraperConfig(human_behavior=False)  # Too fast
scraper = BasicScraper(url="https://example.com", config=config)
```

**Right:**
```python
config = ScraperConfig(human_behavior=True)  # Natural delays
scraper = BasicScraper(url="https://example.com", config=config)
```

## Selector Testing

### In Browser Console

```javascript
// Check if selector works
console.log(document.querySelectorAll("div.product").length);

// Get first element
const el = document.querySelector("h2.title");
console.log(el.textContent);

// Get attribute
const link = document.querySelector("a.product-link");
console.log(link.href);
```

## Advanced: Custom Extractor

```python
async def custom_extractor(element, page):
    # Extract text
    title = await element.find("h2")
    title_text = await title.text if title else None

    # Extract attribute
    link = await element.find("a")
    href = await link.get_attribute("href") if link else None

    # Run JavaScript
    content = await page.evaluate(
        "arguments[0].querySelector('.content').textContent",
        element
    )

    return {
        "title": title_text,
        "link": href,
        "content": content,
    }

scraper.set_extractors(
    item_selector="div.item",
    fields={},
    extractor_func=custom_extractor
)
```

## Async Patterns

### Sequential Scraping

```python
data1 = await scraper1.scrape()
data2 = await scraper2.scrape()
```

### Parallel Scraping (Careful!)

```python
results = await asyncio.gather(
    scraper1.scrape(),
    scraper2.scrape(),
    scraper3.scrape(),
)
```

### Timeout Protection

```python
try:
    data = await asyncio.wait_for(
        scraper.scrape(),
        timeout=120.0  # 2 minutes max
    )
except asyncio.TimeoutError:
    print("Scraping took too long")
```

## Status Tracking

```python
from basic_scraper import ScraperStatus

while scraper.status != ScraperStatus.COMPLETE:
    print(f"Status: {scraper.status.value}")
    await asyncio.sleep(1)
```

## File Operations

### Create Output Directory

```python
from pathlib import Path

output_dir = Path("scraper_output")
output_dir.mkdir(exist_ok=True)

scraper.export_json(str(output_dir / "data.json"))
scraper.export_csv(str(output_dir / "data.csv"))
```

### Timestamped Output

```python
from datetime import datetime

timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
scraper.export_json(f"output_{timestamp}.json")
```

## Quick Checklist

Before scraping:
- [ ] Test selectors in browser
- [ ] Check robots.txt and terms of service
- [ ] Set appropriate delays
- [ ] Configure retry/timeout
- [ ] Enable error screenshots
- [ ] Plan data validation

During scraping:
- [ ] Monitor progress
- [ ] Check for errors
- [ ] Validate data quality
- [ ] Save progress checkpoints

After scraping:
- [ ] Verify data completeness
- [ ] Filter/clean results
- [ ] Export to desired format
- [ ] Clean up resources

## Resources

- Main template: `basic_scraper.py`
- Full documentation: `README_SCRAPER.md`
- Examples: `scraper_examples.py`
- nodriver docs: https://github.com/ultrafunkamsterdam/nodriver
