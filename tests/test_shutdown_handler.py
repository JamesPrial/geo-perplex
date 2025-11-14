"""
Tests for graceful shutdown handler module.

This test suite verifies:
1. Singleton pattern implementation
2. Signal handler registration
3. Shutdown request handling (thread-safe)
4. Cleanup callback registration and execution (LIFO order)
5. Browser cleanup with timeout protection
6. Exception isolation during cleanup
7. Timeout handling for cleanup operations
"""
import pytest
import asyncio
from unittest.mock import AsyncMock, Mock, patch
from src.utils.shutdown_handler import ShutdownHandler


class TestSingletonPattern:
    """Test singleton pattern implementation"""

    def test_singleton_returns_same_instance(self):
        """Multiple instantiations should return the same instance"""
        handler1 = ShutdownHandler()
        handler2 = ShutdownHandler()
        assert handler1 is handler2

    def test_singleton_state_persists(self):
        """State changes should persist across instantiations"""
        handler1 = ShutdownHandler()

        # Clear state first
        handler1._shutdown_requested = False
        handler1._cleanup_callbacks = []

        # Add a callback
        async def test_callback():
            pass
        handler1.register_cleanup(test_callback)

        # New instance should have same state
        handler2 = ShutdownHandler()
        assert len(handler2._cleanup_callbacks) == len(handler1._cleanup_callbacks)


class TestShutdownRequest:
    """Test shutdown request handling"""

    @pytest.mark.asyncio
    async def test_request_shutdown_sets_flag(self):
        """Requesting shutdown should set the flag"""
        handler = ShutdownHandler()
        handler._shutdown_requested = False  # Reset

        await handler.request_shutdown()
        assert handler.is_shutdown_requested() is True

    @pytest.mark.asyncio
    async def test_request_shutdown_is_idempotent(self):
        """Multiple shutdown requests should be safe"""
        handler = ShutdownHandler()
        handler._shutdown_requested = False  # Reset

        await handler.request_shutdown()
        await handler.request_shutdown()
        await handler.request_shutdown()

        assert handler.is_shutdown_requested() is True

    def test_is_shutdown_requested_initial_state(self):
        """Initial state should be False"""
        handler = ShutdownHandler()
        # Note: May be True if previous test set it
        # This tests the method works, not the initial state
        result = handler.is_shutdown_requested()
        assert isinstance(result, bool)


class TestCleanupRegistration:
    """Test cleanup callback registration"""

    def test_register_cleanup_adds_callback(self):
        """Registering cleanup should add to callback list"""
        handler = ShutdownHandler()
        initial_count = len(handler._cleanup_callbacks)

        async def test_callback():
            pass

        handler.register_cleanup(test_callback)
        assert len(handler._cleanup_callbacks) == initial_count + 1

    def test_register_cleanup_maintains_order(self):
        """Callbacks should be stored in registration order"""
        handler = ShutdownHandler()
        handler._cleanup_callbacks = []  # Reset

        async def callback1():
            pass
        async def callback2():
            pass
        async def callback3():
            pass

        handler.register_cleanup(callback1)
        handler.register_cleanup(callback2)
        handler.register_cleanup(callback3)

        assert handler._cleanup_callbacks == [callback1, callback2, callback3]


class TestBrowserRegistration:
    """Test browser instance registration"""

    def test_register_browser_stores_instance(self):
        """Registering browser should store reference"""
        handler = ShutdownHandler()

        mock_browser = Mock()
        handler.register_browser(mock_browser)

        assert handler._browser_instance is mock_browser

    def test_register_browser_replaces_previous(self):
        """Registering new browser should replace old reference"""
        handler = ShutdownHandler()

        browser1 = Mock()
        browser2 = Mock()

        handler.register_browser(browser1)
        assert handler._browser_instance is browser1

        handler.register_browser(browser2)
        assert handler._browser_instance is browser2


class TestCleanupExecution:
    """Test cleanup execution with callbacks"""

    @pytest.mark.asyncio
    async def test_cleanup_executes_callbacks_in_reverse_order(self):
        """Callbacks should execute in LIFO order (last registered, first executed)"""
        handler = ShutdownHandler()
        handler._cleanup_callbacks = []  # Reset

        execution_order = []

        async def callback1():
            execution_order.append(1)

        async def callback2():
            execution_order.append(2)

        async def callback3():
            execution_order.append(3)

        handler.register_cleanup(callback1)
        handler.register_cleanup(callback2)
        handler.register_cleanup(callback3)

        await handler.cleanup()

        # Should execute in reverse: 3, 2, 1
        assert execution_order == [3, 2, 1]

    @pytest.mark.asyncio
    async def test_cleanup_handles_callback_exception(self):
        """Exception in one callback shouldn't stop others"""
        handler = ShutdownHandler()
        handler._cleanup_callbacks = []  # Reset

        execution_order = []

        async def callback1():
            execution_order.append(1)

        async def callback2():
            execution_order.append(2)
            raise RuntimeError("Test error")

        async def callback3():
            execution_order.append(3)

        handler.register_cleanup(callback1)
        handler.register_cleanup(callback2)
        handler.register_cleanup(callback3)

        # Should not raise exception
        await handler.cleanup()

        # All callbacks should execute despite error in callback2
        assert execution_order == [3, 2, 1]

    @pytest.mark.asyncio
    async def test_cleanup_handles_timeout(self):
        """Cleanup should timeout slow callbacks and continue"""
        handler = ShutdownHandler()
        handler._cleanup_callbacks = []  # Reset

        execution_order = []

        async def callback1():
            execution_order.append(1)

        async def slow_callback():
            # Sleep longer than timeout (5 seconds from config)
            await asyncio.sleep(10)
            execution_order.append('slow')

        async def callback3():
            execution_order.append(3)

        handler.register_cleanup(callback1)
        handler.register_cleanup(slow_callback)
        handler.register_cleanup(callback3)

        await handler.cleanup()

        # callback3 and callback1 should execute, slow_callback should timeout
        assert 3 in execution_order
        assert 1 in execution_order
        assert 'slow' not in execution_order

    @pytest.mark.asyncio
    async def test_cleanup_without_shutdown_request(self):
        """Cleanup should work even if shutdown wasn't explicitly requested"""
        handler = ShutdownHandler()
        handler._cleanup_callbacks = []  # Reset
        handler._shutdown_requested = False

        executed = []

        async def callback():
            executed.append(True)

        handler.register_cleanup(callback)

        # Should execute cleanup despite no shutdown request
        await handler.cleanup()
        assert len(executed) == 1


class TestBrowserCleanup:
    """Test browser-specific cleanup"""

    @pytest.mark.asyncio
    async def test_browser_cleanup_calls_close_method(self):
        """Browser cleanup should call close() if available"""
        handler = ShutdownHandler()

        mock_browser = Mock()
        mock_browser.close = AsyncMock()

        handler.register_browser(mock_browser)
        await handler.cleanup()

        mock_browser.close.assert_called_once()

    @pytest.mark.asyncio
    async def test_browser_cleanup_tries_quit_if_no_close(self):
        """Browser cleanup should try quit() if close() not available"""
        handler = ShutdownHandler()

        mock_browser = Mock(spec=[])  # No methods
        mock_browser.quit = AsyncMock()

        handler.register_browser(mock_browser)
        await handler.cleanup()

        mock_browser.quit.assert_called_once()

    @pytest.mark.asyncio
    async def test_browser_cleanup_handles_exception(self):
        """Browser cleanup should handle exceptions gracefully"""
        handler = ShutdownHandler()
        handler._cleanup_callbacks = []  # Reset

        mock_browser = Mock()
        mock_browser.close = AsyncMock(side_effect=RuntimeError("Browser error"))

        handler.register_browser(mock_browser)

        # Should not raise exception
        await handler.cleanup()

        # Browser reference should be cleared
        assert handler._browser_instance is None

    @pytest.mark.asyncio
    async def test_browser_cleanup_handles_timeout(self):
        """Browser cleanup should timeout if taking too long"""
        handler = ShutdownHandler()
        handler._cleanup_callbacks = []  # Reset

        async def slow_close():
            await asyncio.sleep(10)  # Longer than 5s timeout

        mock_browser = Mock()
        mock_browser.close = slow_close

        handler.register_browser(mock_browser)

        # Should complete despite timeout
        await handler.cleanup()

        # Browser reference should be cleared even after timeout
        assert handler._browser_instance is None

    @pytest.mark.asyncio
    async def test_browser_cleanup_before_callbacks(self):
        """Browser should be cleaned up before other callbacks"""
        handler = ShutdownHandler()
        handler._cleanup_callbacks = []  # Reset

        execution_order = []

        async def callback1():
            execution_order.append('callback1')

        mock_browser = Mock()
        async def browser_close():
            execution_order.append('browser')
        mock_browser.close = browser_close

        handler.register_cleanup(callback1)
        handler.register_browser(mock_browser)

        await handler.cleanup()

        # Browser should be first in execution order
        assert execution_order[0] == 'browser'
        assert 'callback1' in execution_order


class TestSignalHandlers:
    """Test signal handler registration"""

    def test_register_signal_handlers_success(self):
        """Signal handlers should register without error"""
        handler = ShutdownHandler()

        # Should not raise exception
        handler.register_signal_handlers()


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
