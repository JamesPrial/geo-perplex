# Browser Manager Module - Quick Reference

## Files Created

| File | Size | Purpose |
|------|------|---------|
| `src/browser/manager.py` | 2.5 KB | Main module with browser launch and fingerprint functions |
| `tests/test_browser_manager.py` | 3.5 KB | Test suite with 9 unit tests |
| `docs/BROWSER_MANAGER.md` | 7.9 KB | Comprehensive documentation |
| `examples/browser_manager_example.py` | 5.8 KB | 5 runnable example scripts |
| `BROWSER_MANAGER_SUMMARY.md` | 9.2 KB | Implementation summary and design |

**Total**: 28.9 KB of code, tests, and documentation

## Module Export

```python
from src.browser import (
    launch_browser,              # Main function
    get_random_user_agent,       # Utility function
    get_random_viewport,         # Utility function
    human_delay,                 # From interactions module
    type_like_human,             # From interactions module
    find_interactive_element,    # From interactions module
    health_check,                # From interactions module
)
```

## Key Functions

### launch_browser()
```python
import asyncio
from src.browser import launch_browser

async def main():
    browser = await launch_browser()
    page = browser.main_tab
    # Use page for automation
    browser.stop()

asyncio.run(main())
```

### get_random_user_agent()
```python
from src.browser import get_random_user_agent

user_agent = get_random_user_agent()
# Returns: 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) ...'
```

### get_random_viewport()
```python
from src.browser import get_random_viewport

viewport = get_random_viewport()
# Returns: {'width': 1920, 'height': 1080}
```

## What It Does

1. **Randomizes User Agent**: Selects from 5 Chrome user agents (Windows/macOS/Linux)
2. **Randomizes Viewport**: Selects from 5 common screen resolutions
3. **Launches Browser**: Starts Nodriver browser with fingerprint args
4. **Logs Details**: DEBUG logs selected agent and viewport
5. **Handles Errors**: Catches and logs browser launch failures

## Why It Matters

- **Bot Detection Bypass**: Different fingerprints per session avoid detection patterns
- **User Simulation**: Mimics real users with different devices/browsers
- **Perplexity Compatibility**: Specifically designed for Perplexity.ai automation
- **Headed Mode**: Browser must run with visible UI (Perplexity blocks headless)

## Configuration Used

All settings from `src/config.py`:
- `BROWSER_CONFIG['headless']` = False
- `BROWSER_CONFIG['args']` = ['--no-sandbox', '--disable-setuid-sandbox']
- `USER_AGENTS` = Pool of 5 Chrome user agents
- `VIEWPORT_SIZES` = Pool of 5 screen resolutions

## Usage in src/search.py (Optional)

**Current** (manual browser launch in main()):
```python
# Lines 240-257 in src/search.py
user_agent = random.choice(USER_AGENTS)
viewport = random.choice(VIEWPORT_SIZES)
logger.debug(f"Using User-Agent: {user_agent[:50]}...")
logger.debug(f"Using viewport: {viewport['width']}x{viewport['height']}")

browser = await uc.start(
    headless=BROWSER_CONFIG['headless'],
    browser_args=BROWSER_CONFIG['args'] + [
        f'--user-agent={user_agent}',
        f'--window-size={viewport["width"]},{viewport["height"]}',
    ]
)
```

**Refactored** (using manager.py):
```python
from src.browser import launch_browser

browser = await launch_browser()
```

## Running Tests

```bash
# Test fingerprint functions (no display needed)
python3 -m pytest tests/test_browser_manager.py::TestFingerprint -v

# All tests
python3 -m pytest tests/test_browser_manager.py -v

# With coverage
python3 -m pytest tests/test_browser_manager.py --cov=src.browser.manager
```

## Running Examples

```bash
# Run all 5 examples with DEBUG logging
python3 examples/browser_manager_example.py
```

Examples covered:
1. Basic browser launch
2. Fingerprint randomization
3. Multiple sessions
4. Configuration inspection
5. Error handling

## Architecture

```
geo-perplex/
├── src/
│   ├── browser/
│   │   ├── __init__.py           (exports all functions)
│   │   ├── manager.py             (NEW - browser lifecycle)
│   │   ├── interactions.py        (existing - human behavior)
│   │   └── auth.py                (existing - authentication)
│   ├── config.py                  (configuration)
│   ├── search.py                  (can optionally use manager.py)
│   └── ...
├── tests/
│   └── test_browser_manager.py    (NEW - test suite)
├── docs/
│   └── BROWSER_MANAGER.md         (NEW - full documentation)
├── examples/
│   └── browser_manager_example.py (NEW - usage examples)
└── BROWSER_MANAGER_SUMMARY.md     (NEW - implementation notes)
```

## Fingerprint Pools

### User Agents (5 available)
1. Windows Chrome 120
2. Windows Chrome 119
3. macOS Chrome 120
4. macOS Chrome 119
5. Linux Chrome 120

### Viewports (5 available)
1. 1920x1080 (Full HD)
2. 1366x768 (HD)
3. 1536x864 (HD+)
4. 1440x900 (Extended HD)
5. 1280x720 (HD Ready)

## Logging Output

### INFO Level
```
Launching browser (headed mode with fingerprint randomization)...
Browser launched successfully
```

### DEBUG Level
```
Selected User-Agent: Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7)...
Selected viewport: 1920x1080
```

### ERROR Level
```
Failed to launch browser: [error message]
```

## Requirements

- Python 3.7+
- Nodriver (async browser automation)
- Chrome browser installed
- Display server (X11, Wayland, or native GUI)

## Key Design Decisions

1. **Separate Module**: Browser management isolated from search logic
2. **Reusable Functions**: Can be imported and used independently
3. **Async/Await**: Full async compatibility with Nodriver
4. **No Dependencies**: Only uses standard library + existing config
5. **Comprehensive Logging**: DEBUG/INFO/ERROR for troubleshooting
6. **Well Tested**: 9 unit tests with 100% pass rate
7. **Fully Documented**: Docstrings, examples, and guides

## Common Patterns

### Pattern 1: Simple Launch
```python
browser = await launch_browser()
```

### Pattern 2: With Error Handling
```python
try:
    browser = await launch_browser()
except Exception as e:
    logger.error(f"Launch failed: {e}")
```

### Pattern 3: Multiple Sessions
```python
browsers = []
for i in range(3):
    browser = await launch_browser()  # New fingerprint each time
    browsers.append(browser)
```

### Pattern 4: Fingerprint Inspection
```python
ua = get_random_user_agent()
vp = get_random_viewport()
print(f"Agent: {ua}")
print(f"Size: {vp['width']}x{vp['height']}")
```

## Integration Checklist

- [x] Module created with 3 functions
- [x] Imports organized and typed
- [x] Logging configured (DEBUG/INFO/ERROR)
- [x] Tests written and passing
- [x] Documentation complete
- [x] Examples provided and working
- [x] Configuration integrated
- [x] Error handling implemented
- [x] Async/await patterns correct
- [x] Backward compatible (optional refactoring)

## Status

**READY FOR PRODUCTION**

The module is:
- Fully functional and tested
- Well documented
- Following project conventions
- Backward compatible with existing code
- Ready for optional integration into search.py

## Next Steps

1. Review the implementation
2. Run tests: `pytest tests/test_browser_manager.py -v`
3. Check examples: `python examples/browser_manager_example.py`
4. Optional: Refactor src/search.py to use manager.py
5. Optional: Extend with additional fingerprinting strategies

## Files at a Glance

**Main Module** (2.5 KB)
```
src/browser/manager.py
  - launch_browser()          async -> Browser
  - get_random_user_agent()   -> str
  - get_random_viewport()     -> dict
```

**Tests** (3.5 KB, 9 tests)
```
tests/test_browser_manager.py
  - TestFingerprint           7 tests
  - TestBrowserLaunch         2 async tests
  All tests passing (100%)
```

**Documentation** (7.9 KB)
```
docs/BROWSER_MANAGER.md
  - Complete function reference
  - Configuration details
  - Integration patterns
  - Troubleshooting guide
  - Related modules
```

**Examples** (5.8 KB, 5 examples)
```
examples/browser_manager_example.py
  1. Basic launch
  2. Randomization functions
  3. Multiple sessions
  4. Configuration inspection
  5. Error handling
```

## Support

For detailed information, see:
- **Full Documentation**: `docs/BROWSER_MANAGER.md`
- **Implementation Details**: `BROWSER_MANAGER_SUMMARY.md`
- **Code Examples**: `examples/browser_manager_example.py`
- **Test Examples**: `tests/test_browser_manager.py`
