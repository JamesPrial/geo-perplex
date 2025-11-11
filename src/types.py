"""Type definitions for the GEO-Perplex project.

This module defines Protocol classes for nodriver types to enable better
type checking and IDE support without depending on nodriver's internal types.
"""

from typing import Protocol, Any, Optional, List


class NodriverElement(Protocol):
    """Protocol for nodriver Element objects.

    This protocol captures the subset of nodriver.Element methods and properties
    used in this codebase for type checking and IDE autocomplete support.

    Note:
        The `text` and `text_all` properties are synchronous, not async.
        - `text`: Returns direct text content of the element (may be empty for containers)
        - `text_all`: Returns all descendant text concatenated with spaces

    Examples:
        >>> element = await page.select('input[type="text"]')
        >>> await element.send_keys('Hello World')
        >>> await element.click()
        >>> content = element.text_all  # NOT awaited
    """

    text: str
    text_all: str

    async def send_keys(self, text: str) -> None:
        """Send keyboard input to element.

        Args:
            text: Text to type into the element

        Note:
            Use '\\n' or '\\r\\n' to press Enter, NOT 'Enter' (which types literal text)
        """
        ...

    async def click(self) -> None:
        """Click the element."""
        ...

    async def get_attribute(self, name: str) -> Optional[str]:
        """Get element attribute value.

        Args:
            name: Attribute name (e.g., 'href', 'class', 'data-testid')

        Returns:
            Attribute value or None if not present
        """
        ...

    async def clear_input(self) -> None:
        """Clear input field content."""
        ...


class NodriverPage(Protocol):
    """Protocol defining the nodriver Page interface.

    This protocol captures the subset of nodriver.Tab methods and properties
    used in this codebase for type checking and IDE support.

    The nodriver library provides this as the Tab class, which represents
    a browser tab/page. This protocol allows type checking without coupling
    to nodriver's implementation details.

    Examples:
        >>> browser = await uc.start()
        >>> page: NodriverPage = browser.main_tab
        >>> await page.get('https://www.perplexity.ai')
        >>> element = await page.select('input[type="text"]')
        >>> await page.save_screenshot('screenshot.png', full_page=True)
    """

    url: str

    async def select(self, selector: str, timeout: float = 10) -> Optional[Any]:
        """Select first element matching CSS selector.

        Args:
            selector: CSS selector string (e.g., 'input[type="text"]', '#main-content')
            timeout: Maximum wait time in seconds

        Returns:
            Element if found, None otherwise

        Note:
            Automatically waits for element to appear in DOM
        """
        ...

    async def select_all(self, selector: str) -> List[Any]:
        """Select all elements matching CSS selector.

        Args:
            selector: CSS selector string

        Returns:
            List of matching elements (empty list if none found)
        """
        ...

    async def evaluate(self, script: str, *args: Any) -> Any:
        """Evaluate JavaScript in page context.

        Args:
            script: JavaScript code to execute
            *args: Arguments to pass to the script

        Returns:
            Result of JavaScript execution

        Examples:
            >>> result = await page.evaluate('document.title')
            >>> await page.evaluate('window.scrollTo(0, document.body.scrollHeight)')
        """
        ...

    async def save_screenshot(
        self,
        path: Optional[str] = None,
        full_page: bool = False
    ) -> None:
        """Save screenshot to file.

        Args:
            path: File path for screenshot (None for auto-generated name)
            full_page: Capture entire page including below fold

        Examples:
            >>> await page.save_screenshot('results.png')
            >>> await page.save_screenshot('full-page.png', full_page=True)
        """
        ...

    async def send(self, cdp_command: Any) -> None:
        """Send Chrome DevTools Protocol command.

        Args:
            cdp_command: CDP command object (e.g., from uc.cdp.network module)

        Examples:
            >>> import nodriver as uc
            >>> await page.send(uc.cdp.network.set_cookie(
            ...     name='session',
            ...     value='abc123',
            ...     domain='.perplexity.ai'
            ... ))
        """
        ...

    async def get(self, url: str) -> None:
        """Navigate to URL.

        Args:
            url: URL to navigate to

        Examples:
            >>> await page.get('https://www.perplexity.ai')
        """
        ...

    async def wait_for(
        self,
        selector: str,
        timeout: float = 10
    ) -> Optional[Any]:
        """Wait for element to appear in DOM.

        Args:
            selector: CSS selector string
            timeout: Maximum wait time in seconds

        Returns:
            Element if found within timeout, None otherwise
        """
        ...


__all__ = ['NodriverPage', 'NodriverElement']
