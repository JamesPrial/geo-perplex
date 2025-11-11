#!/usr/bin/env python3
"""
Practical examples of using the BasicScraper template.

This file demonstrates real-world scraping scenarios and patterns
that developers can adapt for their specific needs.

Examples include:
1. Simple product listing scraping
2. News article scraping with pagination
3. Table data extraction
4. Dynamic content scraping
5. Multi-page scraping with error recovery
"""

import asyncio
import logging
from pathlib import Path
from datetime import datetime

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


# Example 1: Simple Product Listing
async def example_product_listing():
    """
    Scrape a simple product listing page.

    This example shows how to:
    - Initialize scraper with basic config
    - Configure extractors for product data
    - Export results to JSON
    """
    print("\n" + "=" * 70)
    print("Example 1: Simple Product Listing")
    print("=" * 70)

    try:
        from basic_scraper import BasicScraper, ScraperConfig

        # Create config
        config = ScraperConfig(
            headless=True,
            disable_images=True,
            human_behavior=True,
            timeout=30.0,
        )

        # Initialize scraper
        scraper = BasicScraper(
            url="https://example-ecommerce.com/products",
            config=config,
            verbose=True,
        )

        # Configure extraction
        scraper.set_extractors(
            item_selector="div.product-card",
            fields={
                "title": "h2.product-title",
                "price": "span.price",
                "rating": "span.stars",
                "availability": "span.stock-status",
                "url": "a.product-link",
            }
        )

        # In a real scenario, you would uncomment to run:
        # data = await scraper.scrape()
        # scraper.export_json("products.json")
        # scraper.export_csv("products.csv")
        # stats = scraper.get_statistics()
        # print(f"\nScraped {stats['total_items']} products")

        print("\nConfiguration example:")
        print(f"  URL: {scraper.url}")
        print(f"  Item selector: {scraper.item_selector}")
        print(f"  Fields: {list(scraper.field_selectors.keys())}")
        print("\nTo run this example:")
        print("  1. Update the URL to a real website")
        print("  2. Update selectors based on actual HTML structure")
        print("  3. Uncomment the scrape() call")

    except ImportError as e:
        print(f"Note: {e}")


# Example 2: News Articles with Pagination
async def example_news_scraping():
    """
    Scrape news articles across multiple pages.

    This example shows how to:
    - Handle pagination
    - Extract article metadata
    - Track page numbers
    - Implement delay between pages
    """
    print("\n" + "=" * 70)
    print("Example 2: News Articles with Pagination")
    print("=" * 70)

    try:
        from basic_scraper import BasicScraper, ScraperConfig

        config = ScraperConfig(
            headless=True,
            human_behavior=True,
            enable_cookies=True,
            timeout=30.0,
            retry_attempts=3,
        )

        scraper = BasicScraper(
            url="https://example-news.com/articles",
            config=config,
            verbose=True,
        )

        # Configure article extraction
        scraper.set_extractors(
            item_selector="article.news-item",
            fields={
                "headline": "h2.headline",
                "author": "span.author",
                "date": "time",
                "summary": "p.summary",
                "category": "span.category",
                "link": "a.article-link",
            }
        )

        # Configure pagination
        scraper.set_pagination(
            next_button="a.pagination-next",
            max_pages=5,  # Limit to 5 pages
        )

        print("\nConfiguration example:")
        print(f"  URL: {scraper.url}")
        print(f"  Max pages: {scraper.max_pages}")
        print(f"  Fields: {list(scraper.field_selectors.keys())}")
        print("\nTo run this example:")
        print("  1. Update URL to real news site")
        print("  2. Inspect HTML and update CSS selectors")
        print("  3. Update pagination next button selector")
        print("  4. Call: data = await scraper.scrape()")

    except ImportError as e:
        print(f"Note: {e}")


# Example 3: Table Data Extraction
async def example_table_scraping():
    """
    Extract structured data from HTML tables.

    This example shows how to:
    - Parse table rows
    - Extract cells by column position
    - Handle table headers
    """
    print("\n" + "=" * 70)
    print("Example 3: Table Data Extraction")
    print("=" * 70)

    try:
        from basic_scraper import BasicScraper, ScraperConfig

        config = ScraperConfig(
            headless=True,
            disable_images=True,
            timeout=20.0,
        )

        scraper = BasicScraper(
            url="https://example-data.com/financial-table",
            config=config,
        )

        # Configure for table extraction
        # Each row becomes an item
        scraper.set_extractors(
            item_selector="table.data-table tbody tr",
            fields={
                "company": "td:nth-child(1)",
                "ticker": "td:nth-child(2)",
                "price": "td:nth-child(3)",
                "change": "td:nth-child(4)",
                "volume": "td:nth-child(5)",
            }
        )

        print("\nConfiguration example:")
        print(f"  URL: {scraper.url}")
        print(f"  Item selector (table row): {scraper.item_selector}")
        print(f"  Field selectors:")
        for field, selector in scraper.field_selectors.items():
            print(f"    {field}: {selector}")
        print("\nTo run this example:")
        print("  data = await scraper.scrape()")
        print("  scraper.export_csv('financial_data.csv')")

    except ImportError as e:
        print(f"Note: {e}")


# Example 4: Custom Extraction Function
async def example_custom_extractor():
    """
    Use custom extraction logic for complex parsing.

    This example shows how to:
    - Define custom extraction function
    - Access page context for JavaScript evaluation
    - Handle nested structures
    """
    print("\n" + "=" * 70)
    print("Example 4: Custom Extraction Function")
    print("=" * 70)

    async def custom_product_extractor(element, page):
        """
        Custom extraction logic for complex products.

        Args:
            element: The DOM element to extract from
            page: The page object (for running JS if needed)

        Returns:
            Dictionary with extracted data
        """
        try:
            # Extract basic text
            name_elem = await element.find("h2.name")
            name = await name_elem.text if name_elem else "N/A"

            # Extract from attributes
            link_elem = await element.find("a.link")
            url = await link_elem.get_attribute("href") if link_elem else None

            # Complex price extraction
            price_text = "N/A"
            try:
                price_elem = await element.find("span.price")
                if price_elem:
                    price_text = await price_elem.text
                    # Clean up price (remove currency symbol, etc.)
                    price_text = price_text.replace("$", "").strip()
            except Exception:
                pass

            # Extract ratings (might be in data attributes)
            rating = None
            try:
                rating_elem = await element.find("div.rating")
                if rating_elem:
                    rating = await rating_elem.get_attribute("data-rating")
            except Exception:
                pass

            # Extract tags
            tags = []
            try:
                tag_elems = await element.find_all("span.tag")
                for tag_elem in tag_elems:
                    tag_text = await tag_elem.text
                    if tag_text:
                        tags.append(tag_text.strip())
            except Exception:
                pass

            return {
                "name": name.strip() if isinstance(name, str) else name,
                "price": price_text,
                "rating": rating,
                "tags": ", ".join(tags) if tags else None,
                "url": url,
            }

        except Exception as e:
            logger.error(f"Error in custom extractor: {e}")
            return None

    try:
        from basic_scraper import BasicScraper, ScraperConfig

        config = ScraperConfig(headless=True)

        scraper = BasicScraper(
            url="https://example-ecommerce.com",
            config=config,
        )

        # Use custom extractor
        scraper.set_extractors(
            item_selector="div.product",
            fields={},  # Not used with custom function
            extractor_func=custom_product_extractor,
        )

        print("\nCustom extractor configured:")
        print("  Item selector: div.product")
        print("  Extractor function: custom_product_extractor")
        print("\nExtracted fields:")
        print("  - name: Product name")
        print("  - price: Cleaned price value")
        print("  - rating: Rating from data attribute")
        print("  - tags: Comma-separated tags")
        print("  - url: Product URL")
        print("\nTo run this example:")
        print("  data = await scraper.scrape()")

    except ImportError as e:
        print(f"Note: {e}")


# Example 5: Multi-page Scraping with Error Recovery
async def example_multi_page_with_recovery():
    """
    Scrape multiple pages with error recovery and logging.

    This example shows how to:
    - Handle errors gracefully
    - Log progress
    - Resume from checkpoints
    - Export partial results
    """
    print("\n" + "=" * 70)
    print("Example 5: Multi-page Scraping with Error Recovery")
    print("=" * 70)

    async def resilient_scrape():
        """Perform scraping with error recovery."""
        from basic_scraper import BasicScraper, ScraperConfig

        config = ScraperConfig(
            headless=True,
            human_behavior=True,
            retry_attempts=5,  # More retries
            retry_delay=3.0,   # Longer delays
            timeout=45.0,      # Longer timeout
            screenshot_on_error=True,
        )

        scraper = BasicScraper(
            url="https://example-large-site.com",
            config=config,
            verbose=True,
        )

        scraper.set_extractors(
            item_selector="div.item",
            fields={
                "title": "h3",
                "description": "p",
                "link": "a",
            }
        )

        scraper.set_pagination(
            next_button="a.next",
            max_pages=10,
        )

        # Manual pagination with error recovery
        all_items = []

        try:
            # Navigate to start
            if not await scraper.navigate():
                logger.error("Failed to navigate to initial page")
                return all_items

            # Scrape each page manually for better control
            while scraper.current_page <= scraper.max_pages:
                try:
                    logger.info(f"Scraping page {scraper.current_page}")

                    # Extract items
                    page_items = await scraper.extract_page()
                    all_items.extend(page_items)

                    logger.info(f"Page {scraper.current_page}: {len(page_items)} items")

                    # Save progress every 5 pages
                    if scraper.current_page % 5 == 0:
                        scraper.scraped_items = all_items
                        scraper.export_json(f"progress_page_{scraper.current_page}.json")
                        logger.info("Progress saved")

                    # Try to go to next page
                    if not await scraper.goto_next_page():
                        logger.info("No more pages")
                        break

                    # Delay between pages to avoid rate limiting
                    await asyncio.sleep(2.0)

                except Exception as e:
                    logger.error(f"Error on page {scraper.current_page}: {e}")

                    # Try to continue to next page despite error
                    if not await scraper.goto_next_page():
                        break

            return all_items

        finally:
            await scraper.cleanup()

    print("\nError recovery features:")
    print("  - Multiple retry attempts (5)")
    print("  - Longer timeouts and delays")
    print("  - Screenshot on error")
    print("  - Progress checkpoints every 5 pages")
    print("  - Graceful error handling between pages")
    print("\nUsage:")
    print("  items = await resilient_scrape()")
    print("  print(f'Total items: {len(items)}')")

    try:
        # Show the function but don't run it
        print("\nExample code structure created")
    except ImportError as e:
        print(f"Note: {e}")


# Example 6: Data Validation and Filtering
async def example_data_validation():
    """
    Validate and filter scraped data after extraction.

    This example shows how to:
    - Check data quality
    - Filter results
    - Handle missing fields
    - Export cleaned data
    """
    print("\n" + "=" * 70)
    print("Example 6: Data Validation and Filtering")
    print("=" * 70)

    from basic_scraper import ScrapedItem

    # Simulated scraped data
    mock_items = [
        ScrapedItem(
            data={"title": "Product A", "price": "19.99", "rating": "4.5"},
            url="https://example.com/p1",
            page=1,
        ),
        ScrapedItem(
            data={"title": "Product B", "price": None, "rating": "3.0"},
            url="https://example.com/p2",
            page=1,
        ),
        ScrapedItem(
            data={"title": None, "price": "29.99", "rating": "4.8"},
            url="https://example.com/p3",
            page=1,
        ),
    ]

    print("\nOriginal data:")
    print(f"  Total items: {len(mock_items)}")

    # Validation function
    def is_valid_item(item: ScrapedItem) -> bool:
        """Check if item has required fields."""
        required_fields = {"title", "price", "rating"}
        return all(
            item.data.get(field) is not None
            for field in required_fields
        )

    # Filter valid items
    valid_items = [item for item in mock_items if is_valid_item(item)]

    print(f"\nAfter validation:")
    print(f"  Valid items: {len(valid_items)}")
    print(f"  Invalid items: {len(mock_items) - len(valid_items)}")

    # Filter by price range
    cheap_items = [
        item for item in valid_items
        if item.data.get("price") and float(item.data["price"]) < 25
    ]

    print(f"\nFiltered by price < $25:")
    print(f"  Items: {len(cheap_items)}")
    for item in cheap_items:
        print(f"    - {item.data['title']}: ${item.data['price']}")

    # Data quality report
    print("\nData quality report:")
    total = len(mock_items)
    for field in ["title", "price", "rating"]:
        empty = sum(1 for item in mock_items if not item.data.get(field))
        print(f"  {field}: {total - empty}/{total} ({100*(total-empty)/total:.1f}%)")


# Example 7: Cookie Management
async def example_cookie_management():
    """
    Manage cookies for authenticated scraping.

    This example shows how to:
    - Enable cookies
    - Persist sessions across runs
    - Access protected content
    """
    print("\n" + "=" * 70)
    print("Example 7: Cookie Management")
    print("=" * 70)

    try:
        from basic_scraper import BasicScraper, ScraperConfig

        config = ScraperConfig(
            headless=True,
            enable_cookies=True,
            cookies_dir=".scraper_cookies",
        )

        scraper = BasicScraper(
            url="https://example-protected.com/dashboard",
            config=config,
        )

        print("\nCookie configuration:")
        print(f"  Cookies enabled: {config.enable_cookies}")
        print(f"  Storage directory: {config.cookies_dir}")
        print("\nUsage for protected sites:")
        print("  1. First run will prompt for login")
        print("  2. Cookies are automatically saved")
        print("  3. Subsequent runs load saved cookies")
        print("  4. Session is maintained across runs")
        print("\nCookie manager features:")
        print("  - Automatic expiry handling")
        print("  - Domain-specific filtering")
        print("  - JSON export/import")

    except ImportError as e:
        print(f"Note: {e}")


async def main():
    """Run all examples."""
    print("\n")
    print("=" * 70)
    print("BasicScraper Template - Practical Examples")
    print("=" * 70)

    # Run all examples
    await example_product_listing()
    await example_news_scraping()
    await example_table_scraping()
    await example_custom_extractor()
    await example_multi_page_with_recovery()
    await example_data_validation()
    await example_cookie_management()

    print("\n" + "=" * 70)
    print("Summary")
    print("=" * 70)
    print("""
These examples demonstrate:

1. Product Listing: Basic extraction and export
2. News Scraping: Pagination handling
3. Table Extraction: Column-based data
4. Custom Extractors: Complex logic
5. Error Recovery: Resilient scraping
6. Data Validation: Quality checking
7. Cookie Management: Session persistence

For each example:
- Update the URL to your target website
- Adjust CSS selectors based on actual HTML
- Customize fields and extraction logic
- Configure retry/timeout settings as needed

See README_SCRAPER.md for more information.
    """)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n\nInterrupted by user")
    except Exception as e:
        print(f"\nError: {e}")
        import traceback
        traceback.print_exc()
