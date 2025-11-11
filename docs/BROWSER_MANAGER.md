# Browser Manager Module

The `src/browser/manager.py` module handles browser lifecycle management and fingerprint randomization for the GEO-Perplex automation tool.

## Overview

This module provides essential functionality for:
- Launching browser instances with randomized fingerprints
- Randomizing user agents to avoid bot detection
- Randomizing viewport sizes to simulate different devices
- Managing browser initialization with Nodriver

## Module Contents

### `launch_browser()`

Launches a browser with a randomized fingerprint for bot detection avoidance.

```python
async def launch_browser() -> uc.Browser
```

**Returns:**
- `uc.Browser`: Nodriver browser instance ready for automation

**Behavior:**
1. Randomly selects a user agent from the USER_AGENTS pool in config
2. Randomly selects a viewport from the VIEWPORT_SIZES pool in config
3. Launches browser in headed mode with randomized fingerprint args
4. Logs selected fingerprint details for debugging

**Example:**
```python
import asyncio
from src.browser import launch_browser

async def main():
    browser = await launch_browser()
    page = browser.main_tab

    # Use page for automation
    await page.get('https://www.perplexity.ai')

    # Clean up
    browser.stop()

asyncio.run(main())
```

**Raises:**
- `Exception`: If browser launch fails (e.g., no display server available)

**Implementation Details:**
- Uses `BROWSER_CONFIG['headless']` which is hardcoded to `False` (Perplexity blocks headless browsers)
- Appends fingerprint args to `BROWSER_CONFIG['args']` which includes `--no-sandbox` and `--disable-setuid-sandbox`
- Logs success/failure at INFO and ERROR levels respectively

### `get_random_user_agent()`

Returns a randomly selected user agent string.

```python
def get_random_user_agent() -> str
```

**Returns:**
- `str`: Random user agent string from the USER_AGENTS pool

**Example:**
```python
from src.browser import get_random_user_agent

user_agent = get_random_user_agent()
print(f"Using: {user_agent}")
```

**User Agents Available (from config):**
1. Windows Chrome 120 (desktop)
2. Windows Chrome 119 (desktop)
3. macOS Chrome 120 (desktop)
4. macOS Chrome 119 (desktop)
5. Linux Chrome 120 (desktop)

### `get_random_viewport()`

Returns a randomly selected viewport size.

```python
def get_random_viewport() -> dict
```

**Returns:**
- `dict`: Dictionary with 'width' and 'height' keys

**Example:**
```python
from src.browser import get_random_viewport

viewport = get_random_viewport()
print(f"Using viewport: {viewport['width']}x{viewport['height']}")
```

**Viewports Available (from config):**
1. 1920x1080 (Full HD)
2. 1366x768 (HD)
3. 1536x864 (HD+)
4. 1440x900 (Extended HD)
5. 1280x720 (HD Ready)

## Configuration Reference

The module uses configuration values from `src/config.py`:

### BROWSER_CONFIG
```python
BROWSER_CONFIG = {
    'headless': False,  # Must be False - Perplexity blocks headless
    'args': ['--no-sandbox', '--disable-setuid-sandbox'],
}
```

### USER_AGENTS
Pool of 5 realistic Chrome user agent strings for randomization:
```python
USER_AGENTS = [
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    # ... 4 more user agents
]
```

### VIEWPORT_SIZES
Pool of 5 common screen resolutions:
```python
VIEWPORT_SIZES = [
    {'width': 1920, 'height': 1080},
    {'width': 1366, 'height': 768},
    {'width': 1536, 'height': 864},
    {'width': 1440, 'height': 900},
    {'width': 1280, 'height': 720},
]
```

## Why Randomization Matters

### User Agent Randomization
- **Avoids Pattern Detection**: Sites like Perplexity can detect automation by identifying repeated user agents
- **Simulates Real Users**: Different users use different browser/OS combinations
- **Changes Every Launch**: Each browser instance gets a fresh random agent

### Viewport Randomization
- **Device Diversity**: Different users have different screen sizes
- **Responsive Design Variations**: Different viewports may have different rendering
- **Fingerprint Complexity**: Harder to correlate sessions by screen resolution

## Integration with Search Workflow

The `launch_browser()` function is typically used at the beginning of the search automation:

```python
from src.browser import launch_browser
from src.utils.cookies import load_cookies, validate_auth_cookies

async def main():
    # 1. Load and validate cookies
    cookies = load_cookies()
    validate_auth_cookies(cookies)

    # 2. Launch browser with random fingerprint
    browser = await launch_browser()  # <- Uses this module
    page = browser.main_tab

    # 3. Set cookies before navigation
    await set_cookies(page, cookies)

    # 4. Navigate and search
    await page.get('https://www.perplexity.ai')
    # ... continue with search automation
```

## Logging Output

The module provides detailed logging at multiple levels:

**INFO Level:**
```
INFO - Launching browser (headed mode with fingerprint randomization)...
INFO - Browser launched successfully
```

**DEBUG Level:**
```
DEBUG - Selected User-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36...
DEBUG - Selected viewport: 1920x1080
```

**ERROR Level:**
```
ERROR - Failed to launch browser: [error details]
```

## Testing

Unit tests are provided in `tests/test_browser_manager.py`:

```bash
# Run all tests
python3 -m pytest tests/test_browser_manager.py -v

# Run only fingerprint tests
python3 -m pytest tests/test_browser_manager.py::TestFingerprint -v

# Run with coverage
python3 -m pytest tests/test_browser_manager.py --cov=src.browser.manager
```

**Test Coverage:**
- User agent randomization and validity
- Viewport randomization and validity
- Browser configuration validation
- Browser launch functionality (requires display server)

## Nodriver Specifics

This module uses **Nodriver**, an async-first browser automation library with advanced bot detection bypass:

- **Async/Await**: All operations are async for non-blocking execution
- **Chrome DevTools Protocol (CDP)**: Low-level browser control without hitting web APIs
- **No Headless Detection**: Must run in headed mode (with visible UI)
- **Undetected**: Mimics real Chrome browser behavior

## Future Enhancements

Potential improvements for consideration:

1. **Mobile User Agents**: Add mobile browser user agents to the pool
2. **Proxy Support**: Add randomized proxy rotation capabilities
3. **Browser Version Rotation**: Use different Chrome versions
4. **Geolocation Spoofing**: Add location randomization
5. **WebGL Canvas Randomization**: Randomize canvas fingerprinting
6. **Timezone Randomization**: Use different timezones per session

## Troubleshooting

### "Browser launch requires display server"

**Error**: `No display server available` when running on headless server

**Solution**:
- Use X11 forwarding: `ssh -X user@server`
- Or set up VNC server for remote display
- Or run on a system with a graphics display

### "Headless mode not supported"

**Error**: Browser launches but Perplexity detects headless mode

**Solution**:
- Ensure `BROWSER_CONFIG['headless']` is `False` in config.py
- The module enforces this setting

### Inconsistent fingerprints between requests

**Note**: This is intentional behavior. Each `launch_browser()` call creates a new fingerprint to:
- Avoid being tracked across multiple searches
- Simulate different users/sessions
- Reduce detection risk

If you need a consistent fingerprint, either:
1. Use the same browser instance (don't stop/restart)
2. Manually set user agent before calling launch_browser()

## Related Modules

- **`src.browser.interactions`**: Human-like behavior (typing, delays, etc.)
- **`src.browser.auth`**: Authentication and cookie handling
- **`src.config`**: Centralized configuration for all constants
- **`src.search`**: Main search automation that uses this module

## Dependencies

- **nodriver**: Browser automation library (async-first, undetected)
- **random**: Standard library for random selection
- **logging**: Standard library for structured logging
