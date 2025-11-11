"""
Browser automation modules for Perplexity.ai interaction
"""
from src.browser.manager import (
    launch_browser,
    get_random_user_agent,
    get_random_viewport,
    BrowserConfig,
)
from src.browser.interactions import (
    human_delay,
    type_like_human,
    find_interactive_element,
    health_check,
)
from src.browser.auth import set_cookies, verify_authentication

__all__ = [
    'launch_browser',
    'get_random_user_agent',
    'get_random_viewport',
    'BrowserConfig',
    'human_delay',
    'type_like_human',
    'find_interactive_element',
    'health_check',
    'set_cookies',
    'verify_authentication',
]