#!/usr/bin/env python3
"""
Example demonstrating graceful shutdown handling in GEO-Perplex.

This example shows:
1. How to set up the shutdown handler
2. How to register browser and cleanup callbacks
3. How to check for shutdown requests in main loop
4. How cleanup happens automatically on Ctrl+C

Run with:
    python examples/shutdown_handler_example.py

Press Ctrl+C to trigger graceful shutdown.
"""

import asyncio
import logging
from src.utils.shutdown_handler import ShutdownHandler

# Configure logging to see shutdown messages
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)


# Simulate database connection
class MockDatabase:
    """Mock database for demonstration"""

    def __init__(self):
        self.connected = False

    async def connect(self):
        """Simulate database connection"""
        await asyncio.sleep(0.5)
        self.connected = True
        logger.info("Database connected")

    async def close(self):
        """Simulate database cleanup"""
        await asyncio.sleep(0.5)
        self.connected = False
        logger.info("Database closed")


# Simulate browser instance
class MockBrowser:
    """Mock browser for demonstration"""

    def __init__(self):
        self.running = False

    async def launch(self):
        """Simulate browser launch"""
        await asyncio.sleep(1.0)
        self.running = True
        logger.info("Browser launched")

    async def close(self):
        """Simulate browser cleanup"""
        await asyncio.sleep(0.5)
        self.running = False
        logger.info("Browser closed")


async def main():
    """Main application demonstrating shutdown handler usage"""

    # Initialize shutdown handler (singleton)
    handler = ShutdownHandler()

    # Register signal handlers for Ctrl+C and SIGTERM
    handler.register_signal_handlers()
    logger.info("Shutdown handler initialized - press Ctrl+C to trigger graceful shutdown")

    # Initialize resources
    db = MockDatabase()
    await db.connect()

    browser = MockBrowser()
    await browser.launch()

    # Register resources for cleanup
    # Browser gets priority cleanup
    handler.register_browser(browser)

    # Database cleanup callback
    async def cleanup_database():
        logger.info("Cleaning up database...")
        await db.close()

    handler.register_cleanup(cleanup_database)

    # Optional: Register additional cleanup callbacks
    async def cleanup_temp_files():
        logger.info("Cleaning up temporary files...")
        await asyncio.sleep(0.2)
        logger.info("Temporary files removed")

    handler.register_cleanup(cleanup_temp_files)

    # Main application loop
    logger.info("Starting main loop (press Ctrl+C to stop)...")

    iteration = 0
    try:
        while not handler.is_shutdown_requested():
            iteration += 1
            logger.info(f"Working... (iteration {iteration})")
            await asyncio.sleep(2.0)

            # Simulate work
            if iteration >= 10:
                logger.info("Reached iteration limit, requesting shutdown...")
                await handler.request_shutdown()
                break

    except Exception as e:
        logger.error(f"Error in main loop: {e}", exc_info=True)

    finally:
        # Cleanup is called in finally block to ensure it runs
        # even if an exception occurs
        logger.info("Initiating cleanup...")
        await handler.cleanup()

    logger.info("Application shutdown complete")


if __name__ == '__main__':
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        # KeyboardInterrupt is caught by signal handler
        # This is a fallback in case signal handler didn't trigger
        logger.info("KeyboardInterrupt caught - cleanup should have already run")
