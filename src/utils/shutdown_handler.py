"""
Graceful shutdown handling for browser automation and async operations.

This module provides centralized shutdown coordination to ensure clean resource
cleanup when the application receives termination signals (SIGINT, SIGTERM) or
when cleanup is explicitly requested.

Key Features:
    - Singleton pattern ensures single global handler
    - Thread-safe async operations with asyncio.Lock
    - Signal handler registration (SIGINT, SIGTERM)
    - Priority browser cleanup with timeout protection
    - LIFO cleanup callback execution (last registered, first cleaned)
    - Timeout protection for each cleanup operation
    - Exception isolation (one failure doesn't prevent others)

Example Usage:
    ```python
    # In main CLI
    from src.utils.shutdown_handler import ShutdownHandler

    async def main():
        handler = ShutdownHandler()
        handler.register_signal_handlers()

        # Launch browser and register
        browser = await launch_browser()
        handler.register_browser(browser)

        # Register custom cleanup
        async def cleanup_database():
            await db.close()
        handler.register_cleanup(cleanup_database)

        try:
            # Main loop - check periodically for shutdown requests
            while not handler.is_shutdown_requested():
                # Do work...
                await do_search()
        finally:
            # Ensure cleanup runs even if exception occurs
            await handler.cleanup()
    ```

Thread Safety:
    - Uses asyncio.Lock for all state modifications
    - Signal handlers are synchronous (signal module requirement)
    - Cleanup operations are async with proper lock acquisition
"""

import asyncio
import logging
import signal
from typing import Callable, List, Optional, Any

from src.config import SHUTDOWN_CONFIG

logger = logging.getLogger(__name__)


class ShutdownHandler:
    """Singleton shutdown handler for graceful application termination.

    Coordinates cleanup of browser instances, database connections, and other
    async resources. Ensures cleanup happens in proper order (LIFO) with timeout
    protection to prevent hanging.

    Attributes:
        _instance: Class-level singleton instance
        _shutdown_requested: Boolean flag indicating shutdown in progress
        _cleanup_callbacks: List of async cleanup functions (executed in reverse order)
        _browser_instance: Reference to current nodriver browser for priority cleanup
        _lock: asyncio.Lock for thread-safe state modifications
        _logger: Logger instance for this handler
    """

    _instance: Optional['ShutdownHandler'] = None
    _initialized: bool = False

    def __new__(cls) -> 'ShutdownHandler':
        """Implement singleton pattern.

        Returns:
            The single ShutdownHandler instance
        """
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self) -> None:
        """Initialize shutdown handler state.

        Note:
            Due to singleton pattern, this is only called once even if
            ShutdownHandler() is instantiated multiple times.
        """
        # Only initialize once (singleton pattern requirement)
        if ShutdownHandler._initialized:
            return

        self._shutdown_requested: bool = False
        self._cleanup_callbacks: List[Callable[[], Any]] = []
        self._browser_instance: Optional[Any] = None
        self._lock: asyncio.Lock = asyncio.Lock()
        self._logger = logging.getLogger(f"{__name__}.ShutdownHandler")

        ShutdownHandler._initialized = True
        self._logger.debug("ShutdownHandler initialized (singleton)")

    def register_signal_handlers(self) -> None:
        """Register handlers for SIGINT (Ctrl+C) and SIGTERM signals.

        This allows the application to catch termination signals and perform
        graceful cleanup before exiting.

        Example:
            ```python
            handler = ShutdownHandler()
            handler.register_signal_handlers()
            # Now Ctrl+C will trigger graceful shutdown
            ```
        """
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)
        self._logger.info("Signal handlers registered for SIGINT and SIGTERM")

    def _signal_handler(self, signum: int, frame: Any) -> None:
        """Synchronous signal handler that triggers async shutdown.

        Args:
            signum: Signal number (e.g., signal.SIGINT, signal.SIGTERM)
            frame: Current stack frame (unused)

        Note:
            This must be a synchronous function (signal module requirement).
            It schedules the async shutdown request via asyncio.create_task.
        """
        signal_name = signal.Signals(signum).name
        self._logger.info(f"Received {signal_name} signal, initiating graceful shutdown...")

        # Schedule async shutdown request
        # Note: This requires an event loop to be running
        try:
            loop = asyncio.get_running_loop()
            loop.create_task(self.request_shutdown())
        except RuntimeError:
            # No running event loop - set flag directly as fallback
            self._logger.warning("No running event loop - setting shutdown flag directly")
            self._shutdown_requested = True

    async def request_shutdown(self) -> None:
        """Mark shutdown as requested (thread-safe).

        This method is async and uses a lock to ensure thread-safe flag modification.
        It prevents duplicate shutdown triggers by checking if shutdown is already requested.

        Example:
            ```python
            # Manually request shutdown from async context
            await handler.request_shutdown()
            ```
        """
        async with self._lock:
            if self._shutdown_requested:
                self._logger.debug("Shutdown already requested, ignoring duplicate request")
                return

            self._shutdown_requested = True
            self._logger.info("Shutdown requested - cleanup will begin shortly")

    def is_shutdown_requested(self) -> bool:
        """Check if shutdown is in progress (non-blocking, thread-safe read).

        Returns:
            True if shutdown has been requested, False otherwise

        Example:
            ```python
            while not handler.is_shutdown_requested():
                # Continue working...
                await do_work()
            ```

        Note:
            This is a synchronous read of the boolean flag. While not protected
            by the lock (for performance), boolean reads are atomic in Python.
        """
        return self._shutdown_requested

    def register_cleanup(self, callback: Callable[[], Any]) -> None:
        """Add async cleanup callback to execution list.

        Callbacks are executed in reverse order (LIFO - last registered, first cleaned)
        during shutdown. This ensures dependencies are cleaned up in the correct order.

        Args:
            callback: Async function to call during cleanup (no parameters)

        Example:
            ```python
            async def cleanup_database():
                await db.close()
                logger.info("Database closed")

            handler.register_cleanup(cleanup_database)
            ```

        Note:
            Callbacks must be async functions with no parameters. They should
            handle their own exceptions to prevent blocking other cleanup operations.
        """
        self._cleanup_callbacks.append(callback)
        self._logger.debug(
            f"Registered cleanup callback: {callback.__name__} "
            f"(total: {len(self._cleanup_callbacks)})"
        )

    def register_browser(self, browser: Any) -> None:
        """Store browser instance for priority cleanup.

        The browser gets special priority cleanup before other callbacks to ensure
        browser processes are terminated cleanly.

        Args:
            browser: Nodriver browser instance to cleanup on shutdown

        Example:
            ```python
            browser = await uc.start()
            handler.register_browser(browser)
            ```

        Note:
            Only one browser instance is tracked at a time. Registering a new
            browser will replace the previous reference.
        """
        self._browser_instance = browser
        self._logger.debug(f"Browser instance registered for cleanup: {type(browser).__name__}")

    async def cleanup(self) -> None:
        """Execute all cleanup callbacks with timeout protection.

        This is the main cleanup orchestration method. It:
        1. Cleans up browser first (priority)
        2. Executes registered callbacks in reverse order (LIFO)
        3. Applies 5-second timeout to each cleanup operation
        4. Catches and logs exceptions without stopping other cleanups
        5. Ensures all cleanups are attempted even if some fail

        The method is idempotent - calling multiple times is safe.

        Example:
            ```python
            try:
                # Main application logic
                await run_searches()
            finally:
                # Always cleanup, even if exception occurs
                await handler.cleanup()
            ```

        Note:
            - Each cleanup gets individual 5-second timeout
            - TimeoutError is caught and logged, cleanup continues
            - Exceptions are isolated - one failure doesn't stop others
            - Browser cleanup runs first for process termination
        """
        async with self._lock:
            if not self._shutdown_requested:
                self._logger.debug("Cleanup called without shutdown request - proceeding anyway")

            self._logger.info("Beginning cleanup process...")
            cleanup_count = len(self._cleanup_callbacks)

            # Priority cleanup: browser instance
            if self._browser_instance is not None:
                await self._cleanup_browser()

            # Execute callbacks in reverse order (LIFO)
            # Last registered callback runs first
            for idx, callback in enumerate(reversed(self._cleanup_callbacks)):
                callback_num = cleanup_count - idx
                callback_name = getattr(callback, '__name__', 'unknown')

                try:
                    self._logger.debug(
                        f"Running cleanup {callback_num}/{cleanup_count}: {callback_name}"
                    )

                    # Apply timeout per cleanup operation (from config)
                    timeout = SHUTDOWN_CONFIG['cleanup_timeout']
                    await asyncio.wait_for(callback(), timeout=timeout)

                    self._logger.debug(f"Cleanup {callback_num}/{cleanup_count} completed: {callback_name}")

                except asyncio.TimeoutError:
                    timeout = SHUTDOWN_CONFIG['cleanup_timeout']
                    self._logger.warning(
                        f"Cleanup {callback_num}/{cleanup_count} timed out after {timeout}s: {callback_name}"
                    )
                    # Continue to next cleanup despite timeout

                except Exception as e:
                    self._logger.error(
                        f"Cleanup {callback_num}/{cleanup_count} failed: {callback_name} - {e}",
                        exc_info=True
                    )
                    # Continue to next cleanup despite error

            self._logger.info(
                f"Cleanup process completed ({cleanup_count} callbacks executed)"
            )

    async def _cleanup_browser(self) -> None:
        """Clean up browser instance with timeout protection (private method).

        This is called automatically by cleanup() before other callbacks.
        Applies 5-second timeout to browser cleanup to prevent hanging.

        Note:
            Browser cleanup failures are logged but don't stop the cleanup process.
            The browser reference is cleared even if cleanup fails.
        """
        if self._browser_instance is None:
            return

        browser_type = type(self._browser_instance).__name__
        self._logger.debug(f"Cleaning up browser instance: {browser_type}")

        try:
            # Apply timeout to browser cleanup (from config)
            timeout = SHUTDOWN_CONFIG['browser_cleanup_timeout']
            await asyncio.wait_for(
                self._close_browser(),
                timeout=timeout
            )
            self._logger.info("Browser cleanup completed successfully")

        except asyncio.TimeoutError:
            timeout = SHUTDOWN_CONFIG['browser_cleanup_timeout']
            self._logger.warning(
                f"Browser cleanup timed out after {timeout}s (type: {browser_type})"
            )

        except Exception as e:
            self._logger.error(
                f"Browser cleanup failed (type: {browser_type}): {e}",
                exc_info=True
            )

        finally:
            # Clear reference even if cleanup failed
            self._browser_instance = None

    async def _close_browser(self) -> None:
        """Close browser using available close/quit/stop methods.

        Tries multiple common browser termination methods to ensure compatibility
        with different browser automation libraries.

        Raises:
            AttributeError: If browser has no close/quit/stop methods
        """
        browser = self._browser_instance

        # Try common browser close methods in order of preference
        if hasattr(browser, 'close') and callable(browser.close):
            await browser.close()
        elif hasattr(browser, 'quit') and callable(browser.quit):
            await browser.quit()
        elif hasattr(browser, 'stop') and callable(browser.stop):
            await browser.stop()
        else:
            self._logger.warning(
                f"Browser instance has no close/quit/stop method (type: {type(browser).__name__})"
            )


# Singleton instance - import this for convenience
shutdown_handler = ShutdownHandler()


__all__ = ['ShutdownHandler', 'shutdown_handler']
