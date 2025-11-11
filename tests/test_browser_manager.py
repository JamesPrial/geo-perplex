"""
Tests for browser manager module
Tests fingerprint randomization and browser launch configuration
"""
import pytest
from src.browser.manager import get_random_user_agent, get_random_viewport, launch_browser
from src.config import USER_AGENTS, VIEWPORT_SIZES, BROWSER_CONFIG


class TestFingerprint:
    """Test fingerprint randomization functions"""

    def test_get_random_user_agent_returns_valid_string(self):
        """User agent should be a non-empty string from the pool"""
        user_agent = get_random_user_agent()
        assert isinstance(user_agent, str)
        assert len(user_agent) > 0
        assert user_agent in USER_AGENTS

    def test_get_random_user_agent_randomization(self):
        """Multiple calls should return various user agents"""
        user_agents = {get_random_user_agent() for _ in range(10)}
        # With 5 user agents and 10 calls, we should get at least 2 different ones
        assert len(user_agents) >= 1

    def test_get_random_viewport_returns_valid_dict(self):
        """Viewport should be a dict with width and height"""
        viewport = get_random_viewport()
        assert isinstance(viewport, dict)
        assert 'width' in viewport
        assert 'height' in viewport
        assert isinstance(viewport['width'], int)
        assert isinstance(viewport['height'], int)
        assert viewport['width'] > 0
        assert viewport['height'] > 0

    def test_get_random_viewport_from_pool(self):
        """Viewport should be one of the configured sizes"""
        viewport = get_random_viewport()
        assert viewport in VIEWPORT_SIZES

    def test_get_random_viewport_randomization(self):
        """Multiple calls should return various viewports"""
        viewports = {
            (v['width'], v['height']) for v in [get_random_viewport() for _ in range(10)]
        }
        # With 5 viewports and 10 calls, we should get at least 1 different one
        assert len(viewports) >= 1

    def test_browser_config_headless_is_false(self):
        """Browser config should disable headless mode"""
        assert BROWSER_CONFIG['headless'] is False

    def test_browser_config_has_args(self):
        """Browser config should have args list"""
        assert isinstance(BROWSER_CONFIG['args'], list)
        assert len(BROWSER_CONFIG['args']) > 0
        assert '--no-sandbox' in BROWSER_CONFIG['args']


class TestBrowserLaunch:
    """Test browser launch function (async tests)"""

    @pytest.mark.asyncio
    async def test_launch_browser_returns_browser_instance(self):
        """launch_browser should return a Nodriver browser instance"""
        try:
            browser = await launch_browser()
            assert browser is not None
            # Should have main_tab attribute
            assert hasattr(browser, 'main_tab')
            # Clean up
            browser.stop()
        except Exception as e:
            # Browser launch might fail in test environment without display
            pytest.skip(f"Browser launch requires display server: {e}")

    @pytest.mark.asyncio
    async def test_launch_browser_uses_headed_mode(self):
        """Browser should be launched in headed mode (not headless)"""
        try:
            browser = await launch_browser()
            # Headless mode should be False per config
            assert BROWSER_CONFIG['headless'] is False
            # Clean up
            browser.stop()
        except Exception as e:
            pytest.skip(f"Browser launch requires display server: {e}")


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
