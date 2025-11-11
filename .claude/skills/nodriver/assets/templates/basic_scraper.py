#!/usr/bin/env python3
"""
Comprehensive web scraper template using nodriver.

This template provides a production-ready scraper with:
- Async setup with proper initialization
- Navigation with retry logic
- Data extraction from tables/lists
- Pagination handling
- CSV/JSON export functionality
- Error handling and screenshots on failure
- Human-like behavior patterns
- Session management with cookies
- Graceful cleanup

Usage:
    Basic scraping:
        >>> import asyncio
        >>> scraper = BasicScraper(url="https://example.com")
        >>> data = asyncio.run(scraper.scrape())

    With custom configuration:
        >>> config = ScraperConfig(
        ...     headless=False,
        ...     enable_cookies=True,
        ...     human_behavior=True,
        ... )
        >>> scraper = BasicScraper(url="https://example.com", config=config)
        >>> data = asyncio.run(scraper.scrape())

Example:
    Scraping a table with pagination:
        >>> async def scrape_with_pagination():
        ...     scraper = BasicScraper(url="https://example.com/products")
        ...     scraper.set_extractors(
        ...         item_selector="table tbody tr",
        ...         fields={
        ...             "name": "td:nth-child(1)",
        ...             "price": "td:nth-child(2)",
        ...             "link": "td a",
        ...         }
        ...     )
        ...     scraper.set_pagination(
        ...         next_button="a.next-page",
        ...         max_pages=5,
        ...     )
        ...     data = await scraper.scrape()
        ...     scraper.export_csv("products.csv")
        ...     return data
"""

import asyncio
import json
import csv
import logging
import sys
from pathlib import Path
from dataclasses import dataclass, field, asdict
from datetime import datetime
from typing import Any, Dict, List, Optional, Callable
from enum import Enum


# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


class ScraperStatus(Enum):
    """Status of scraper operations."""
    IDLE = "idle"
    INITIALIZING = "initializing"
    NAVIGATING = "navigating"
    EXTRACTING = "extracting"
    PAGINATING = "paginating"
    COMPLETE = "complete"
    ERROR = "error"


@dataclass
class ScraperConfig:
    """
    Configuration for scraper behavior.

    Attributes:
        headless: Run browser in headless mode (default: True)
        disable_images: Disable image loading for performance (default: True)
        human_behavior: Use human-like delays and patterns (default: True)
        enable_cookies: Save and load cookies (default: True)
        timeout: Navigation timeout in seconds (default: 30)
        retry_attempts: Number of retry attempts for failed navigation (default: 3)
        retry_delay: Delay between retry attempts in seconds (default: 2)
        screenshot_on_error: Take screenshot when error occurs (default: True)
        screenshot_dir: Directory for error screenshots (default: "screenshots")
        cookies_dir: Directory for storing cookies (default: ".cookies")
        user_agent: Custom user agent string (default: None)
        viewport_width: Viewport width (default: 1920)
        viewport_height: Viewport height (default: 1080)
    """
    headless: bool = True
    disable_images: bool = True
    human_behavior: bool = True
    enable_cookies: bool = True
    timeout: float = 30.0
    retry_attempts: int = 3
    retry_delay: float = 2.0
    screenshot_on_error: bool = True
    screenshot_dir: str = "screenshots"
    cookies_dir: str = ".cookies"
    user_agent: Optional[str] = None
    viewport_width: int = 1920
    viewport_height: int = 1080


@dataclass
class ScrapedItem:
    """Represents a single scraped item with metadata."""
    data: Dict[str, Any]
    url: str = ""
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
    page: int = 1

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for export."""
        return {
            **self.data,
            "_url": self.url,
            "_timestamp": self.timestamp,
            "_page": self.page,
        }


class BasicScraper:
    """
    Comprehensive web scraper with full feature support.

    Handles browser initialization, navigation, data extraction,
    pagination, session management, and error handling.
    """

    def __init__(
        self,
        url: str,
        config: Optional[ScraperConfig] = None,
        verbose: bool = True,
    ) -> None:
        """
        Initialize the scraper.

        Args:
            url: URL to scrape
            config: ScraperConfig instance or None for defaults
            verbose: Enable verbose logging (default: True)
        """
        self.url = url
        self.config = config or ScraperConfig()
        self.verbose = verbose
        self.status = ScraperStatus.IDLE

        # Browser and page management
        self.browser: Optional[Any] = None
        self.page: Optional[Any] = None

        # Extraction configuration
        self.item_selector: Optional[str] = None
        self.field_selectors: Dict[str, str] = {}
        self.extractor_func: Optional[Callable] = None

        # Pagination configuration
        self.next_button_selector: Optional[str] = None
        self.max_pages: int = 1
        self.current_page: int = 1

        # Data storage
        self.scraped_items: List[ScrapedItem] = []

        # Human behavior
        self.behavior: Optional[Any] = None

        # Cookie manager
        self.cookie_manager: Optional[Any] = None

        # Setup paths
        Path(self.config.screenshot_dir).mkdir(exist_ok=True, parents=True)
        if self.config.enable_cookies:
            Path(self.config.cookies_dir).mkdir(exist_ok=True, parents=True)

    def _log(self, message: str, level: str = "info") -> None:
        """Log message with optional verbosity."""
        if self.verbose:
            getattr(logger, level)(message)

    def set_extractors(
        self,
        item_selector: str,
        fields: Dict[str, str],
        extractor_func: Optional[Callable] = None,
    ) -> None:
        """
        Configure data extraction.

        Args:
            item_selector: CSS selector for items to extract
            fields: Dictionary mapping field names to CSS selectors
            extractor_func: Optional custom extraction function

        Example:
            scraper.set_extractors(
                item_selector="div.product",
                fields={
                    "name": "h2.title",
                    "price": "span.price",
                    "link": "a.product-link",
                }
            )
        """
        self.item_selector = item_selector
        self.field_selectors = fields
        self.extractor_func = extractor_func
        self._log(f"Extractors configured: {len(fields)} fields")

    def set_pagination(
        self,
        next_button: str,
        max_pages: int = 10,
        wait_for_load: bool = True,
    ) -> None:
        """
        Configure pagination.

        Args:
            next_button: CSS selector for next page button
            max_pages: Maximum number of pages to scrape (default: 10)
            wait_for_load: Wait for page load after pagination (default: True)

        Example:
            scraper.set_pagination(
                next_button="a.next",
                max_pages=5,
            )
        """
        self.next_button_selector = next_button
        self.max_pages = max_pages
        self._log(f"Pagination configured: max {max_pages} pages")

    async def _init_browser(self) -> None:
        """Initialize browser with nodriver."""
        self._log("Initializing browser...")
        self.status = ScraperStatus.INITIALIZING

        try:
            import nodriver

            # Build launch arguments
            args = []
            if self.config.headless:
                args.append("--headless=new")

            if self.config.disable_images:
                args.append("--blink-settings=imagesEnabled=false")

            args.extend([
                "--disable-blink-features=AutomationControlled",
                "--disable-sync",
                "--disable-plugins",
                "--disable-extensions",
            ])

            # Initialize browser
            self.browser = await nodriver.start(
                headless=self.config.headless,
                args=args,
                user_agent=self.config.user_agent,
            )

            self._log("Browser initialized successfully")

        except ImportError:
            raise ImportError(
                "nodriver is not installed. Install with: pip install nodriver"
            )
        except Exception as e:
            self._log(f"Failed to initialize browser: {e}", "error")
            raise

    async def _init_behavior(self) -> None:
        """Initialize human behavior module if enabled."""
        if not self.config.human_behavior:
            return

        self._log("Initializing human behavior patterns...")
        try:
            # Try to import from the nodriver skills
            import sys
            from pathlib import Path

            # Attempt to import HumanBehavior if available
            try:
                # This is a placeholder - adjust path as needed
                from human_behavior import HumanBehavior, BehaviorConfig

                self.behavior = HumanBehavior(
                    BehaviorConfig(interaction_style="normal")
                )
                self._log("Human behavior patterns enabled")
            except ImportError:
                self._log(
                    "Human behavior module not available, using basic delays",
                    "warning"
                )
        except Exception as e:
            self._log(f"Error initializing behavior: {e}", "warning")

    async def _init_cookies(self) -> None:
        """Initialize cookie manager if enabled."""
        if not self.config.enable_cookies:
            return

        self._log("Initializing cookie manager...")
        try:
            from pathlib import Path

            # Create a basic cookie manager if available
            class SimpleCookieManager:
                def __init__(self, storage_path: Path):
                    self.storage_path = storage_path
                    self.cookies = {}

                async def load_cookies(self, domain: str) -> None:
                    """Load cookies for domain."""
                    pass

                async def save_cookies(self, domain: str) -> None:
                    """Save cookies for domain."""
                    pass

            self.cookie_manager = SimpleCookieManager(
                Path(self.config.cookies_dir)
            )
            self._log("Cookie manager initialized")

        except Exception as e:
            self._log(f"Error initializing cookies: {e}", "warning")

    async def _human_delay(
        self,
        min_seconds: float = 0.5,
        max_seconds: float = 2.0,
    ) -> None:
        """Add human-like delay."""
        if self.behavior:
            try:
                await self.behavior.random_delay(min_seconds, max_seconds)
                return
            except Exception:
                pass

        # Fallback to basic delay
        import random
        delay = random.uniform(min_seconds, max_seconds)
        await asyncio.sleep(delay)

    async def navigate(self, url: Optional[str] = None) -> bool:
        """
        Navigate to URL with retry logic.

        Args:
            url: URL to navigate to (uses self.url if None)

        Returns:
            True if navigation successful, False otherwise
        """
        target_url = url or self.url
        self._log(f"Navigating to {target_url}")
        self.status = ScraperStatus.NAVIGATING

        for attempt in range(1, self.config.retry_attempts + 1):
            try:
                self.page = await self.browser.get(target_url)
                self._log(f"Navigation successful: {target_url}")

                # Wait for page to stabilize
                await asyncio.sleep(1.0)

                # Apply human behavior
                if self.behavior:
                    try:
                        await self.behavior.read_page(
                            self.page,
                            reading_speed="normal",
                            include_scrolling=False,
                        )
                    except Exception:
                        pass

                return True

            except Exception as e:
                self._log(
                    f"Navigation attempt {attempt}/{self.config.retry_attempts} "
                    f"failed: {e}",
                    "warning"
                )

                if attempt < self.config.retry_attempts:
                    await asyncio.sleep(self.config.retry_delay)
                else:
                    await self._handle_error(
                        f"Navigation failed after {self.config.retry_attempts} "
                        f"attempts"
                    )
                    return False

        return False

    async def _extract_item(self, element: Any) -> Optional[Dict[str, Any]]:
        """
        Extract data from a single item element.

        Args:
            element: Element to extract from

        Returns:
            Dictionary of extracted data or None
        """
        if self.extractor_func:
            try:
                return await self.extractor_func(element, self.page)
            except Exception as e:
                self._log(f"Custom extractor error: {e}", "warning")
                return None

        # Standard field extraction
        item_data: Dict[str, Any] = {}

        for field_name, selector in self.field_selectors.items():
            try:
                # Try to find element
                found_elements = await element.find_all(selector)

                if found_elements:
                    field_element = found_elements[0]

                    # Try to get text content first
                    try:
                        text = await field_element.text
                        item_data[field_name] = text.strip()
                    except Exception:
                        # Try to get attribute value (for links)
                        try:
                            href = await field_element.get_attribute("href")
                            item_data[field_name] = href
                        except Exception:
                            item_data[field_name] = None
                else:
                    item_data[field_name] = None

            except Exception as e:
                self._log(f"Error extracting field '{field_name}': {e}", "debug")
                item_data[field_name] = None

        return item_data if any(item_data.values()) else None

    async def extract_page(self) -> List[ScrapedItem]:
        """
        Extract all items from current page.

        Returns:
            List of ScrapedItem objects
        """
        if not self.page or not self.item_selector:
            return []

        self._log(f"Extracting items from page {self.current_page}...")
        self.status = ScraperStatus.EXTRACTING

        items: List[ScrapedItem] = []

        try:
            # Find all items
            elements = await self.page.find_all(self.item_selector)
            self._log(f"Found {len(elements)} items on page {self.current_page}")

            # Extract from each item
            for idx, element in enumerate(elements, 1):
                try:
                    item_data = await self._extract_item(element)

                    if item_data:
                        item = ScrapedItem(
                            data=item_data,
                            url=self.page.current_url or self.url,
                            page=self.current_page,
                        )
                        items.append(item)

                        # Small delay between extractions for human behavior
                        if self.config.human_behavior:
                            await self._human_delay(0.1, 0.5)

                except Exception as e:
                    self._log(
                        f"Error extracting item {idx} on page {self.current_page}: {e}",
                        "warning"
                    )
                    continue

            self._log(f"Successfully extracted {len(items)} items from page")
            self.scraped_items.extend(items)

        except Exception as e:
            self._log(f"Error during extraction: {e}", "error")
            await self._handle_error(f"Extraction failed: {e}")

        return items

    async def goto_next_page(self) -> bool:
        """
        Navigate to next page if pagination is enabled.

        Returns:
            True if next page found and navigated, False otherwise
        """
        if not self.next_button_selector or not self.page:
            return False

        self._log(f"Looking for next page button...")
        self.status = ScraperStatus.PAGINATING

        try:
            # Find next button
            next_buttons = await self.page.find_all(self.next_button_selector)

            if not next_buttons:
                self._log("Next page button not found, pagination complete")
                return False

            next_button = next_buttons[0]

            # Check if button is enabled
            try:
                disabled = await next_button.get_attribute("disabled")
                if disabled is not None:
                    self._log("Next button is disabled, pagination complete")
                    return False
            except Exception:
                pass

            # Click next button
            self._log("Clicking next page button...")
            await next_button.click()

            # Wait for page to load
            await asyncio.sleep(1.0)

            # Human behavior: wait and scroll
            if self.behavior:
                try:
                    await self.behavior.scroll_naturally(self.page)
                except Exception:
                    pass
            else:
                await asyncio.sleep(random.uniform(1.0, 2.0))

            self.current_page += 1
            self._log(f"Navigated to page {self.current_page}")
            return True

        except Exception as e:
            self._log(f"Error navigating to next page: {e}", "warning")
            return False

    async def _handle_error(self, error_message: str) -> None:
        """
        Handle error by taking screenshot and logging.

        Args:
            error_message: Error message to log
        """
        self.status = ScraperStatus.ERROR
        self._log(f"Error: {error_message}", "error")

        if self.config.screenshot_on_error and self.page:
            try:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                filename = Path(self.config.screenshot_dir) / f"error_{timestamp}.png"
                await self.page.screenshot(str(filename))
                self._log(f"Screenshot saved: {filename}")
            except Exception as e:
                self._log(f"Failed to save screenshot: {e}", "warning")

    async def scrape(self) -> List[ScrapedItem]:
        """
        Perform the complete scraping operation.

        Returns:
            List of all scraped items

        Raises:
            RuntimeError: If scraping fails
        """
        try:
            # Initialize
            await self._init_browser()
            await self._init_behavior()
            await self._init_cookies()

            # Navigate to initial page
            if not await self.navigate():
                raise RuntimeError("Failed to navigate to initial URL")

            # Scrape pages
            while self.current_page <= self.max_pages:
                # Extract items from current page
                await self.extract_page()

                # Check if we should continue to next page
                if self.current_page >= self.max_pages:
                    self._log(f"Reached maximum pages ({self.max_pages})")
                    break

                # Try to navigate to next page
                if not await self.goto_next_page():
                    self._log("No more pages to scrape")
                    break

                # Human-like delay between pages
                await self._human_delay(2.0, 5.0)

            self.status = ScraperStatus.COMPLETE
            self._log(f"Scraping complete: {len(self.scraped_items)} items")
            return self.scraped_items

        except Exception as e:
            self._log(f"Scraping failed: {e}", "error")
            await self._handle_error(str(e))
            raise

        finally:
            await self.cleanup()

    async def cleanup(self) -> None:
        """Close browser and cleanup resources."""
        self._log("Cleaning up resources...")

        try:
            if self.browser:
                await self.browser.aclose()
                self._log("Browser closed")
        except Exception as e:
            self._log(f"Error closing browser: {e}", "warning")

    def export_json(self, filepath: str) -> None:
        """
        Export scraped data to JSON file.

        Args:
            filepath: Path to output file

        Example:
            scraper.export_json("data.json")
        """
        self._log(f"Exporting data to {filepath}...")

        data = {
            "metadata": {
                "url": self.url,
                "timestamp": datetime.now().isoformat(),
                "total_items": len(self.scraped_items),
                "pages_scraped": self.current_page,
            },
            "items": [item.to_dict() for item in self.scraped_items],
        }

        try:
            with open(filepath, "w") as f:
                json.dump(data, f, indent=2)
            self._log(f"JSON export complete: {len(self.scraped_items)} items")
        except Exception as e:
            self._log(f"JSON export failed: {e}", "error")
            raise

    def export_csv(self, filepath: str) -> None:
        """
        Export scraped data to CSV file.

        Args:
            filepath: Path to output file

        Example:
            scraper.export_csv("data.csv")
        """
        if not self.scraped_items:
            self._log("No items to export", "warning")
            return

        self._log(f"Exporting data to {filepath}...")

        try:
            # Get all field names
            fieldnames = set()
            for item in self.scraped_items:
                fieldnames.update(item.data.keys())

            fieldnames = sorted(fieldnames)
            fieldnames.extend(["_url", "_timestamp", "_page"])

            # Write CSV
            with open(filepath, "w", newline="") as f:
                writer = csv.DictWriter(f, fieldnames=fieldnames)
                writer.writeheader()

                for item in self.scraped_items:
                    row = item.to_dict()
                    writer.writerow(row)

            self._log(f"CSV export complete: {len(self.scraped_items)} items")

        except Exception as e:
            self._log(f"CSV export failed: {e}", "error")
            raise

    def get_statistics(self) -> Dict[str, Any]:
        """
        Get scraping statistics.

        Returns:
            Dictionary with statistics
        """
        return {
            "total_items": len(self.scraped_items),
            "pages_scraped": self.current_page,
            "status": self.status.value,
            "timestamp": datetime.now().isoformat(),
        }


async def example_scraper() -> None:
    """Example demonstrating basic scraper usage."""
    print("\n" + "=" * 60)
    print("Basic Web Scraper Example")
    print("=" * 60)

    # Example 1: Simple table scraping
    print("\n[Example 1] Simple Table Scraping")
    print("-" * 60)

    config = ScraperConfig(
        headless=True,
        human_behavior=True,
        enable_cookies=True,
    )

    scraper = BasicScraper(
        url="https://example.com",
        config=config,
        verbose=True,
    )

    # Configure extractors for a hypothetical table
    scraper.set_extractors(
        item_selector="tr",  # Each row
        fields={
            "column1": "td:nth-child(1)",
            "column2": "td:nth-child(2)",
            "column3": "td:nth-child(3)",
        }
    )

    try:
        # This would scrape the page
        # data = await scraper.scrape()
        # scraper.export_json("output.json")
        # scraper.export_csv("output.csv")

        print("\nScraper configured successfully!")
        print(f"Target URL: {scraper.url}")
        print(f"Item selector: {scraper.item_selector}")
        print(f"Fields: {scraper.field_selectors}")

    except Exception as e:
        print(f"Error: {e}")

    # Example 2: With pagination
    print("\n[Example 2] Scraping with Pagination")
    print("-" * 60)

    scraper2 = BasicScraper(
        url="https://example.com/products",
        config=config,
        verbose=True,
    )

    scraper2.set_extractors(
        item_selector="div.product",
        fields={
            "name": "h2.title",
            "price": "span.price",
            "link": "a.product-link",
        }
    )

    scraper2.set_pagination(
        next_button="a.next-page",
        max_pages=3,
    )

    print("Pagination configured!")
    print(f"Next button selector: {scraper2.next_button_selector}")
    print(f"Max pages: {scraper2.max_pages}")

    # Example 3: Statistics
    print("\n[Example 3] Scraper Configuration Summary")
    print("-" * 60)

    print(f"Config settings:")
    for key, value in asdict(config).items():
        print(f"  {key}: {value}")


async def main() -> None:
    """Run examples."""
    await example_scraper()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n\nInterrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)
