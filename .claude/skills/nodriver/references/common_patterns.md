# Common Nodriver Patterns

This guide contains frequently used patterns for browser automation with nodriver.

## Table of Contents
1. [Basic Browser Operations](#basic-browser-operations)
2. [Element Selection & Interaction](#element-selection--interaction)
3. [Wait Strategies](#wait-strategies)
4. [Network Operations](#network-operations)
5. [Session Management](#session-management)
6. [Error Handling](#error-handling)
7. [Anti-Detection Patterns](#anti-detection-patterns)

## Basic Browser Operations

### Standard Browser Initialization
```python
import nodriver as uc

async def create_browser():
    browser = await uc.start(
        headless=False,  # Visible mode is less detectable
        user_data_dir="./profiles/default"  # Persist profile
    )
    return browser
```

### Docker/Linux Setup
```python
# For containerized environments
browser = await uc.start(
    no_sandbox=True,  # Required for Docker
    headless=False,
    browser_args=['--disable-gpu', '--disable-dev-shm-usage']
)
```

### Multi-Tab Management
```python
# Open multiple tabs
tab1 = await browser.get("https://example.com")
tab2 = await browser.get("https://google.com", new_tab=True)
tab3 = await browser.get("https://github.com", new_window=True)

# Switch between tabs
for tab in [tab1, tab2, tab3]:
    await tab.bring_to_front()
    await tab.reload()
```

## Element Selection & Interaction

### Selector Strategies
```python
# CSS selector (fastest, most reliable)
element = await tab.select("#submit-button")

# Text-based selection (best for dynamic content)
element = await tab.find("Submit", best_match=True)

# XPath (when CSS won't work)
element = await tab.xpath("//button[@type='submit']")

# Multiple elements
elements = await tab.select_all(".item")
```

### Smart Clicking Pattern
```python
async def safe_click(tab, selector):
    """Click with fallback strategies"""
    try:
        element = await tab.select(selector, timeout=10)
        await element.scroll_into_view()
        await tab.sleep(0.5)  # Small delay
        await element.click()
    except Exception:
        # Fallback: JavaScript click
        await tab.evaluate(f'''
            document.querySelector("{selector}").click();
        ''')
```

### Reliable Text Input
```python
async def type_safely(tab, selector, text):
    """Type text with verification"""
    element = await tab.select(selector)

    # Clear field first
    await element.clear_input()

    # Type character by character to avoid truncation
    for char in text:
        await element.send_keys(char)
        await tab.sleep(0.05)  # Small delay between chars

    # Verify input
    value = await element.get_value()
    if value != text:
        # Fallback: JavaScript injection
        await tab.evaluate(f'''
            document.querySelector("{selector}").value = "{text}";
        ''')
```

## Wait Strategies

### Wait for Page Load
```python
# Wait for body element as load indicator
await tab.select("body")
```

### Wait for Element
```python
# Built-in wait (10 seconds default)
element = await tab.select("#dynamic-content", timeout=15)

# Custom wait condition
async def wait_for_text(tab, selector, text, timeout=10):
    start = time.time()
    while time.time() - start < timeout:
        try:
            element = await tab.select(selector, timeout=1)
            content = await element.text_content
            if text in content:
                return element
        except:
            pass
        await tab.sleep(0.5)
    raise TimeoutError(f"Text '{text}' not found in {selector}")
```

### Wait for Network Idle
```python
async def wait_network_idle(tab, idle_time=2):
    """Wait for no network activity"""
    await tab.sleep(idle_time)
    # Additional CDP-based network monitoring can be added
```

## Network Operations

### Cookie Management
```python
# Save cookies
cookies = await tab.get_cookies()
with open("cookies.json", "w") as f:
    json.dump(cookies, f)

# Load cookies
with open("cookies.json", "r") as f:
    cookies = json.load(f)
    await tab.set_cookies(cookies)

# Reload page to apply cookies
await tab.reload()
```

### Download Handling
```python
import pathlib
from nodriver import cdp

# Configure download path
download_path = pathlib.Path("./downloads").resolve()
await tab.send(cdp.browser.set_download_behavior(
    "allow",
    str(download_path),
    events_enabled=True
))
```

### Request Interception (CDP)
```python
import nodriver.cdp as cdp

# Monitor network requests
def handle_request(event):
    print(f"Request: {event.request.url}")

tab.add_handler(cdp.network.RequestWillBeSent, handle_request)
```

## Session Management

### Profile Persistence
```python
# Use consistent profile directory
browser = await uc.start(
    user_data_dir="./profiles/user1"
)

# Profile will persist cookies, localStorage, etc.
```

### Session Recovery Pattern
```python
async def get_authenticated_browser(profile_dir):
    """Get browser with existing session or login"""
    browser = await uc.start(user_data_dir=profile_dir)
    tab = await browser.get("https://example.com/dashboard")

    # Check if logged in
    try:
        await tab.select(".user-menu", timeout=3)
        print("Session restored")
    except:
        # Need to login
        await login(tab)
        print("New login performed")

    return browser, tab
```

## Error Handling

### Retry Pattern
```python
async def retry_operation(func, max_attempts=3):
    """Retry with exponential backoff"""
    for attempt in range(max_attempts):
        try:
            return await func()
        except Exception as e:
            if attempt == max_attempts - 1:
                raise
            wait_time = 2 ** attempt
            print(f"Attempt {attempt + 1} failed, retrying in {wait_time}s")
            await asyncio.sleep(wait_time)
```

### Screenshot on Error
```python
async def safe_operation(tab, operation):
    """Execute with error capture"""
    try:
        return await operation()
    except Exception as e:
        # Take screenshot for debugging
        await tab.save_screenshot(f"error_{time.time()}.png")

        # Log page state
        url = await tab.get_url()
        title = await tab.get_title()
        print(f"Error at {url} ({title}): {e}")
        raise
```

### Graceful Cleanup
```python
async def main():
    browser = None
    try:
        browser = await uc.start()
        # ... do work ...
    finally:
        if browser:
            await browser.stop()
```

## Anti-Detection Patterns

### Human-like Delays
```python
import random

async def human_delay(min_s=0.5, max_s=2.0):
    """Random delay with exponential distribution"""
    delay = random.expovariate(1 / ((min_s + max_s) / 2))
    delay = max(min_s, min(delay, max_s))
    await asyncio.sleep(delay)
```

### Natural Scrolling
```python
async def scroll_naturally(tab):
    """Scroll page like a human"""
    # Get page height
    height = await tab.evaluate("document.body.scrollHeight")

    # Scroll in chunks with pauses
    current = 0
    while current < height:
        # Random scroll amount
        scroll_amount = random.randint(100, 500)
        current += scroll_amount

        await tab.scroll_to(0, min(current, height))
        await human_delay(0.5, 2.0)

        # Sometimes scroll back up a bit
        if random.random() < 0.2:
            await tab.scroll_by(0, -random.randint(50, 150))
            await human_delay(0.3, 1.0)
```

### Mouse Movement
```python
async def move_mouse_naturally(tab, to_element):
    """Move mouse with curve instead of straight line"""
    # Get element position
    box = await to_element.get_box_model()
    x = box['content'][0] + random.randint(5, box['width'] - 5)
    y = box['content'][1] + random.randint(5, box['height'] - 5)

    # Move with small random movements
    await tab.mouse_move(x + random.randint(-10, 10), y + random.randint(-10, 10))
    await human_delay(0.1, 0.3)
    await tab.mouse_move(x, y)
```

### Typing Rhythm
```python
async def type_like_human(element, text):
    """Type with natural rhythm variations"""
    for char in text:
        await element.send_keys(char)

        # Vary delay based on character
        if char in ".,!?":
            delay = random.uniform(0.1, 0.3)
        elif char == " ":
            delay = random.uniform(0.05, 0.15)
        else:
            delay = random.uniform(0.03, 0.1)

        await asyncio.sleep(delay)
```

## Complete Example: Form Automation

```python
import nodriver as uc
import asyncio
import random

async def fill_form_naturally():
    """Complete form with human-like behavior"""

    # Initialize browser
    browser = await uc.start(
        user_data_dir="./profiles/form_filler"
    )

    try:
        # Navigate to form
        tab = await browser.get("https://example.com/form")
        await tab.select("body")  # Wait for load

        # Random initial delay (reading the page)
        await asyncio.sleep(random.uniform(2, 4))

        # Fill first name
        first_name = await tab.select("#firstName")
        await first_name.scroll_into_view()
        await asyncio.sleep(random.uniform(0.5, 1))
        await type_like_human(first_name, "John")

        # Tab to next field (more natural than clicking)
        await tab.send_keys("\t")
        await asyncio.sleep(random.uniform(0.3, 0.8))

        # Fill last name
        last_name = await tab.select("#lastName")
        await type_like_human(last_name, "Doe")

        # Random pause (thinking)
        await asyncio.sleep(random.uniform(1, 3))

        # Fill email
        email = await tab.select("#email")
        await email.scroll_into_view()
        await email.click()
        await asyncio.sleep(0.5)
        await type_like_human(email, "john.doe@example.com")

        # Scroll down to see submit button
        await scroll_naturally(tab)

        # Submit form
        submit = await tab.select("#submit")
        await move_mouse_naturally(tab, submit)
        await asyncio.sleep(random.uniform(0.5, 1.5))
        await submit.click()

        # Wait for success
        await tab.select(".success-message", timeout=15)

    finally:
        await browser.stop()

# Run
asyncio.run(fill_form_naturally())
```

## Best Practices

1. **Always use try/finally** for browser cleanup
2. **Prefer visible mode** over headless (better anti-detection)
3. **Use profiles** for session persistence
4. **Add human-like delays** between actions
5. **Take screenshots** on errors for debugging
6. **Verify actions** (don't assume they succeeded)
7. **Use text-based selectors** when elements are dynamic
8. **Implement retry logic** for flaky operations
9. **Monitor network** when dealing with dynamic content
10. **Test locally first** before deploying to production

## Common Pitfalls to Avoid

- Don't use uniform delays (use exponential distribution)
- Don't move mouse in straight lines
- Don't type too fast or too uniformly
- Don't skip reading/thinking pauses
- Don't ignore viewport (scroll elements into view)
- Don't use headless mode against protected sites
- Don't forget to handle iframes separately
- Don't assume elements are immediately clickable