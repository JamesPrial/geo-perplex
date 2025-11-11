# Web Scraper Template - Complete Index

## Overview

This is a comprehensive, production-ready web scraping template built on `nodriver`. It provides everything needed to build robust web scrapers with minimal additional code.

## Files

### 1. `basic_scraper.py` (Main Template)
The core scraper implementation with all features integrated.

**Contents:**
- `ScraperConfig`: Configuration dataclass with 14 customizable options
- `ScraperStatus`: Enum for scraper state management
- `ScrapedItem`: Data class for individual scraped items
- `BasicScraper`: Main scraper class with complete functionality

**Key Features:**
- Async/await throughout
- Navigation with automatic retry logic
- Flexible data extraction (selectors or custom functions)
- Pagination support with max page limits
- CSV and JSON export
- Cookie management and persistence
- Human-like behavior integration
- Error handling with screenshots
- Graceful cleanup

**Usage:**
```python
from basic_scraper import BasicScraper

scraper = BasicScraper(url="https://example.com")
scraper.set_extractors("div.item", {"title": "h2"})
data = await scraper.scrape()
scraper.export_csv("output.csv")
```

**Size:** ~700 lines of well-documented code

---

### 2. `README_SCRAPER.md` (Complete Documentation)
Comprehensive guide covering all aspects of the scraper.

**Sections:**
- Features overview
- Installation instructions
- Quick start examples
- Configuration reference (14 options explained)
- Core classes documentation
- Method reference for all public methods
- Advanced usage patterns
- Error handling strategies
- Best practices
- Common patterns (tables, products, pagination)
- Troubleshooting guide
- Performance optimization tips

**Best For:**
- Learning the full capabilities
- Understanding all configuration options
- Implementing advanced features
- Troubleshooting issues

**Length:** ~600 lines

---

### 3. `scraper_examples.py` (Practical Examples)
Seven real-world scraping examples with complete implementations.

**Examples:**
1. **Simple Product Listing**: Basic extraction and export
2. **News Articles with Pagination**: Multi-page scraping
3. **Table Data Extraction**: Column-based structured data
4. **Custom Extraction Function**: Complex parsing logic
5. **Multi-page with Error Recovery**: Resilient scraping
6. **Data Validation and Filtering**: Quality checks
7. **Cookie Management**: Authenticated scraping

**Best For:**
- Finding a starting point for your use case
- Understanding different extraction patterns
- Learning error handling strategies
- Implementing data validation

**Usage:**
```bash
python scraper_examples.py
```

**Length:** ~500 lines

---

### 4. `SCRAPER_QUICK_REFERENCE.md` (Cheat Sheet)
Quick lookup guide for common tasks and patterns.

**Contents:**
- Basic setup pattern
- Configuration quick reference
- Common CSS selectors
- Extraction patterns
- Pagination patterns
- Export formats
- Debugging tips
- Error handling patterns
- Performance tips
- Common mistakes
- Advanced patterns

**Best For:**
- Quick lookups while coding
- Remembering syntax
- Finding common patterns
- Avoiding mistakes

**Length:** ~350 lines

---

## Getting Started

### Step 1: Installation

Ensure `nodriver` is installed:
```bash
pip install nodriver
```

### Step 2: Copy the Template

The main template is: `basic_scraper.py`

Place it in your project directory.

### Step 3: Write Your First Scraper

```python
import asyncio
from basic_scraper import BasicScraper

async def main():
    # Create scraper
    scraper = BasicScraper(url="https://example.com")

    # Configure extraction
    scraper.set_extractors(
        item_selector="div.product",
        fields={
            "name": "h2.title",
            "price": "span.price",
        }
    )

    # Scrape and export
    try:
        data = await scraper.scrape()
        scraper.export_csv("products.csv")
        print(f"Scraped {len(data)} products")
    finally:
        await scraper.cleanup()

asyncio.run(main())
```

### Step 4: Run It

```bash
python your_scraper.py
```

## Feature Checklist

### Core Functionality
- [x] Async setup with proper initialization
- [x] Navigation with retry logic (configurable)
- [x] Data extraction from tables/lists
- [x] Pagination handling with max pages
- [x] CSV/JSON export functionality
- [x] Error handling and screenshots on failure
- [x] Human-like behavior patterns
- [x] Session management with cookies
- [x] Graceful cleanup

### Additional Features
- [x] Logging with configurable verbosity
- [x] Custom extraction functions
- [x] Data validation and filtering
- [x] Statistics and progress tracking
- [x] Comprehensive error messages
- [x] Configuration dataclass
- [x] Type hints throughout
- [x] Multiple export formats
- [x] Retry with exponential backoff
- [x] Human behavior delay patterns

## Quick Reference

### Common Selectors
```
Class:    .classname
ID:       #idname
Tag:      tag
Multiple: selector, selector
Child:    parent > child
Descendant: parent descendant
Nth child: :nth-child(n)
```

### Configuration Examples

**Fast Scraping:**
```python
config = ScraperConfig(
    headless=True,
    disable_images=True,
    human_behavior=False,
    timeout=15.0,
)
```

**Stealth Scraping:**
```python
config = ScraperConfig(
    human_behavior=True,
    enable_cookies=True,
    disable_images=False,  # Let images load
    timeout=30.0,
)
```

**Reliable Scraping:**
```python
config = ScraperConfig(
    retry_attempts=5,
    retry_delay=3.0,
    timeout=45.0,
    screenshot_on_error=True,
)
```

## Architecture

```
BasicScraper (main class)
├── Browser Management
│   ├── _init_browser()
│   ├── navigate()
│   └── cleanup()
├── Data Extraction
│   ├── set_extractors()
│   ├── extract_page()
│   └── _extract_item()
├── Pagination
│   ├── set_pagination()
│   └── goto_next_page()
├── Export
│   ├── export_json()
│   ├── export_csv()
│   └── get_statistics()
├── Behavior
│   ├── _init_behavior()
│   └── _human_delay()
└── Error Handling
    ├── _handle_error()
    └── _log()
```

## Configuration Options (14 Total)

```python
ScraperConfig(
    # Browser settings (4)
    headless=True,
    disable_images=True,
    user_agent=None,

    # Behavior settings (2)
    human_behavior=True,
    enable_cookies=True,

    # Navigation settings (3)
    timeout=30.0,
    retry_attempts=3,
    retry_delay=2.0,

    # Error handling (2)
    screenshot_on_error=True,
    screenshot_dir="screenshots",

    # Session settings (1)
    cookies_dir=".cookies",

    # Viewport settings (2)
    viewport_width=1920,
    viewport_height=1080,
)
```

## Usage Patterns

### Pattern 1: Simple Extraction
```python
scraper = BasicScraper(url="https://example.com")
scraper.set_extractors("div.item", {"field": "selector"})
data = await scraper.scrape()
```

### Pattern 2: With Pagination
```python
scraper.set_pagination(next_button="a.next", max_pages=5)
data = await scraper.scrape()
```

### Pattern 3: Custom Function
```python
async def extractor(element, page):
    return {"data": await element.find("h2").text}

scraper.set_extractors("div.item", {}, extractor_func=extractor)
```

### Pattern 4: Error Recovery
```python
try:
    data = await scraper.scrape()
except RuntimeError as e:
    print(f"Failed: {e}")
finally:
    await scraper.cleanup()
```

## Performance Tips

1. **Disable Images**: Speeds up loading by 50%+
   ```python
   config = ScraperConfig(disable_images=True)
   ```

2. **Reduce Timeout**: For fast sites
   ```python
   config = ScraperConfig(timeout=15.0)
   ```

3. **Limit Pages**: Don't scrape unnecessary pages
   ```python
   scraper.set_pagination(max_pages=5)
   ```

4. **Headless Mode**: Uses less resources
   ```python
   config = ScraperConfig(headless=True)
   ```

## Common Issues & Solutions

| Issue | Solution |
|-------|----------|
| Browser won't start | Ensure Chrome/Chromium installed |
| Elements not found | Check CSS selectors in browser |
| Getting blocked | Enable human_behavior, add delays |
| Slow performance | Disable images, reduce timeout |
| Data incomplete | Increase timeout, disable human_behavior |
| Screenshots fail | Check screenshot_dir exists |

## File Sizes & Complexity

| File | Size | Complexity | Purpose |
|------|------|-----------|---------|
| basic_scraper.py | ~700 lines | High | Implementation |
| README_SCRAPER.md | ~600 lines | Medium | Documentation |
| scraper_examples.py | ~500 lines | Medium | Examples |
| SCRAPER_QUICK_REFERENCE.md | ~350 lines | Low | Reference |

## When to Use This Template

### Perfect For:
- Scraping public websites
- Extracting product data
- Gathering news/articles
- Collecting public information
- Learning web scraping
- Building production scrapers

### Not For:
- Scraping against Terms of Service
- Private/protected content (without permission)
- Bypassing access controls
- Rate-limiting attacks

## Integration with Other nodriver Skills

The template integrates with:
- `human_behavior.py`: Natural interaction patterns
- `cookie_manager.py`: Session persistence
- `quick_start.py`: Browser initialization
- `element_waiter.py`: Element waiting (future enhancement)
- `network_monitor.py`: Request monitoring (future enhancement)

## Extending the Template

### Add Custom Validation
```python
def validate_item(item: ScrapedItem) -> bool:
    return all(item.data.values())

valid_data = [item for item in data if validate_item(item)]
```

### Add Progress Tracking
```python
for page in range(scraper.max_pages):
    items = await scraper.extract_page()
    print(f"Page {scraper.current_page}: {len(items)} items")
    await scraper.goto_next_page()
```

### Add Custom Processing
```python
async def process_items():
    data = await scraper.scrape()

    # Transform
    for item in data:
        item.data['price'] = float(item.data['price'])

    # Filter
    expensive = [item for item in data if item.data['price'] > 100]

    return expensive
```

## Documentation Structure

```
basic_scraper.py                    ← Implementation
├── README_SCRAPER.md              ← Full documentation
│   ├── Features
│   ├── Installation
│   ├── Quick Start
│   ├── Configuration
│   ├── Methods Reference
│   ├── Advanced Usage
│   └── Troubleshooting
├── SCRAPER_QUICK_REFERENCE.md     ← Cheat sheet
│   ├── Basic Setup
│   ├── Common Patterns
│   ├── Quick Reference
│   └── Common Mistakes
└── scraper_examples.py             ← 7 Working Examples
    ├── Product Listing
    ├── News with Pagination
    ├── Table Extraction
    ├── Custom Extractors
    ├── Error Recovery
    ├── Data Validation
    └── Cookie Management
```

## Support & Resources

### File References
- **Main Code**: `basic_scraper.py`
- **Full Docs**: `README_SCRAPER.md`
- **Examples**: `scraper_examples.py`
- **Quick Lookup**: `SCRAPER_QUICK_REFERENCE.md`

### External Resources
- nodriver: https://github.com/ultrafunkamsterdam/nodriver
- CSS Selectors: https://www.w3schools.com/cssref/selectors_intro.asp
- Async Python: https://docs.python.org/3/library/asyncio.html

### Related nodriver Skills
- Browser initialization patterns
- Human behavior simulation
- Cookie management
- Element waiting strategies
- Network monitoring

## Version Information

- **Template Version**: 1.0
- **Python Version**: 3.8+
- **nodriver Version**: Latest
- **Created**: 2024
- **Status**: Production-ready

## Summary

This template provides a complete, production-ready solution for web scraping. It includes:

- **Main Implementation**: Fully-featured scraper class (700 lines)
- **Documentation**: Comprehensive guide (600 lines)
- **Examples**: 7 real-world patterns (500 lines)
- **Quick Reference**: Cheat sheet (350 lines)

All code includes:
- Type hints
- Docstrings
- Error handling
- Logging
- Configuration options
- Best practices

Perfect for developers who want to build reliable web scrapers without starting from scratch.

---

**Next Steps:**
1. Read `README_SCRAPER.md` for complete documentation
2. Review `scraper_examples.py` for patterns matching your use case
3. Copy `basic_scraper.py` to your project
4. Adapt for your target website
5. Use `SCRAPER_QUICK_REFERENCE.md` while developing
