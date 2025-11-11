# Migration Guide: Selenium/Playwright to Nodriver

This guide helps you migrate from Selenium or Playwright to nodriver.

## Table of Contents
1. [Why Migrate?](#why-migrate)
2. [Key Differences](#key-differences)
3. [Selenium to Nodriver](#selenium-to-nodriver)
4. [Playwright to Nodriver](#playwright-to-nodriver)
5. [Feature Comparison](#feature-comparison)
6. [Migration Strategies](#migration-strategies)

## Why Migrate?

### When to Choose Nodriver
✅ **Use nodriver when:**
- Websites detect and block Selenium/Playwright
- You need stealth web scraping
- Bypassing Cloudflare protection (partial success)
- Working with anti-bot protected sites
- Direct CDP control is needed

### When NOT to Choose Nodriver
❌ **Avoid nodriver when:**
- You need multi-browser support (Firefox, Safari)
- Robust headless mode is critical
- You need extensive documentation
- Complex proxy setups required
- Standard testing/automation (not scraping)

## Key Differences

### Architecture
| Feature | Selenium | Playwright | Nodriver |
|---------|----------|------------|----------|
| Protocol | WebDriver | CDP + others | CDP only |
| Browsers | Chrome, Firefox, Safari, Edge | Chrome, Firefox, Safari | Chrome only |
| Detection | Easily detected | Somewhat detectable | Harder to detect |
| Async | Optional | Built-in | Required |
| Headless | Reliable | Reliable | Unreliable |
| Documentation | Extensive | Extensive | Limited |

### Syntax Differences
| Operation | Selenium | Playwright | Nodriver |
|-----------|----------|------------|----------|
| Import | `from selenium import webdriver` | `from playwright.async_api import async_playwright` | `import nodriver as uc` |
| Launch | `driver = webdriver.Chrome()` | `browser = await playwright.chromium.launch()` | `browser = await uc.start()` |
| Navigate | `driver.get(url)` | `await page.goto(url)` | `tab = await browser.get(url)` |
| Find Element | `driver.find_element(By.ID, "id")` | `page.locator("#id")` | `await tab.select("#id")` |
| Click | `element.click()` | `await element.click()` | `await element.click()` |
| Type | `element.send_keys("text")` | `await element.fill("text")` | `await element.send_keys("text")` |
| Wait | `WebDriverWait(driver, 10)` | `page.wait_for_selector()` | Built-in (10s default) |

## Selenium to Nodriver

### Basic Setup

**Selenium:**
```python
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

driver = webdriver.Chrome()
driver.get("https://example.com")
```

**Nodriver:**
```python
import nodriver as uc
import asyncio

async def main():
    browser = await uc.start()
    tab = await browser.get("https://example.com")

asyncio.run(main())
```

### Element Selection

**Selenium:**
```python
# By ID
element = driver.find_element(By.ID, "submit")

# By class
element = driver.find_element(By.CLASS_NAME, "button")

# By CSS selector
element = driver.find_element(By.CSS_SELECTOR, "#form > button")

# By XPath
element = driver.find_element(By.XPATH, "//button[@type='submit']")

# Multiple elements
elements = driver.find_elements(By.CLASS_NAME, "item")
```

**Nodriver:**
```python
# CSS selector (preferred)
element = await tab.select("#submit")

# Class selector
element = await tab.select(".button")

# Complex CSS
element = await tab.select("#form > button")

# XPath (slower)
element = await tab.xpath("//button[@type='submit']")

# Multiple elements
elements = await tab.select_all(".item")

# Text-based (unique to nodriver)
element = await tab.find("Submit Button", best_match=True)
```

### Waiting Strategies

**Selenium:**
```python
# Explicit wait
wait = WebDriverWait(driver, 10)
element = wait.until(EC.presence_of_element_located((By.ID, "myId")))

# Wait for clickable
element = wait.until(EC.element_to_be_clickable((By.ID, "button")))

# Custom condition
wait.until(lambda driver: driver.find_element(By.ID, "result").text == "Done")
```

**Nodriver:**
```python
# Built-in wait (auto-retry for 10 seconds)
element = await tab.select("#myId")

# Custom timeout
element = await tab.select("#myId", timeout=20)

# Wait for text
async def wait_for_text(tab, selector, expected_text, timeout=10):
    start = time.time()
    while time.time() - start < timeout:
        try:
            element = await tab.select(selector)
            text = await element.text_content
            if expected_text in text:
                return element
        except:
            pass
        await asyncio.sleep(0.5)
    raise TimeoutError()

# Custom JavaScript condition
await tab.evaluate("return document.readyState") == "complete"
```

### Actions

**Selenium:**
```python
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.keys import Keys

# Click
element.click()

# Type
element.send_keys("Hello World")

# Clear and type
element.clear()
element.send_keys("New Text")

# Keyboard actions
element.send_keys(Keys.ENTER)

# Mouse hover
ActionChains(driver).move_to_element(element).perform()

# Drag and drop
ActionChains(driver).drag_and_drop(source, target).perform()
```

**Nodriver:**
```python
# Click
await element.click()

# Type (character by character to avoid bugs)
for char in "Hello World":
    await element.send_keys(char)
    await tab.sleep(0.05)

# Clear and type
await element.clear_input()
await element.send_keys("New Text")

# Keyboard actions
await element.send_keys("\n")  # Enter

# Mouse operations (via CDP)
box = await element.get_box_model()
await tab.mouse_move(box['content'][0], box['content'][1])
await tab.mouse_click()

# JavaScript alternative for complex actions
await tab.evaluate('''
    const source = document.querySelector("#source");
    const target = document.querySelector("#target");
    // Implement drag-drop via JS
''')
```

### JavaScript Execution

**Selenium:**
```python
# Execute script
result = driver.execute_script("return document.title")

# Execute with arguments
driver.execute_script("arguments[0].click();", element)

# Async script
driver.execute_async_script("""
    var callback = arguments[arguments.length - 1];
    setTimeout(function() { callback('done'); }, 1000);
""")
```

**Nodriver:**
```python
# Execute script
result = await tab.evaluate("document.title")

# Click via JavaScript
await tab.evaluate(f'''
    document.querySelector("{selector}").click();
''')

# Async operations
result = await tab.evaluate('''
    await new Promise(resolve => setTimeout(resolve, 1000));
    return "done";
''')
```

### Screenshots

**Selenium:**
```python
# Full page
driver.save_screenshot("screenshot.png")

# Specific element
element.screenshot("element.png")
```

**Nodriver:**
```python
# Save screenshot
await tab.save_screenshot("screenshot.png")

# Element screenshot (use CDP)
# Note: Element screenshots require additional CDP implementation
```

### Cookies

**Selenium:**
```python
# Get all cookies
cookies = driver.get_cookies()

# Add cookie
driver.add_cookie({"name": "key", "value": "value"})

# Delete cookie
driver.delete_cookie("key")

# Delete all
driver.delete_all_cookies()
```

**Nodriver:**
```python
# Get all cookies
cookies = await tab.get_cookies()

# Set cookies
await tab.set_cookies(cookies)

# Save to file
await browser.cookies.save("cookies.dat")

# Load from file
await browser.cookies.load("cookies.dat")

# Note: Individual cookie operations may require CDP
```

## Playwright to Nodriver

### Basic Setup

**Playwright:**
```python
from playwright.async_api import async_playwright

async def main():
    async with async_playwright() as p:
        browser = await p.chromium.launch()
        page = await browser.new_page()
        await page.goto("https://example.com")
```

**Nodriver:**
```python
import nodriver as uc

async def main():
    browser = await uc.start()
    tab = await browser.get("https://example.com")
```

### Element Selection

**Playwright:**
```python
# Locators
element = page.locator("#id")
element = page.locator(".class")
element = page.locator("text=Submit")
element = page.locator("button:has-text('Submit')")

# Get multiple
elements = page.locator(".item").all()
```

**Nodriver:**
```python
# CSS selectors
element = await tab.select("#id")
element = await tab.select(".class")

# Text selection (unique feature)
element = await tab.find("Submit", best_match=True)

# Get multiple
elements = await tab.select_all(".item")
```

### Waiting

**Playwright:**
```python
# Auto-waiting built-in
await page.click("#button")  # Waits automatically

# Explicit wait
await page.wait_for_selector("#element")

# Wait for state
await page.wait_for_load_state("networkidle")

# Custom wait
await page.wait_for_function("() => document.querySelector('#result').innerText === 'Done'")
```

**Nodriver:**
```python
# Auto-waiting built-in (10s default)
element = await tab.select("#button")
await element.click()

# Custom timeout
element = await tab.select("#element", timeout=20)

# Wait for network (basic)
await tab.sleep(2)  # Simple approach

# Custom wait
while True:
    result = await tab.evaluate("document.querySelector('#result')?.innerText")
    if result == "Done":
        break
    await asyncio.sleep(0.5)
```

### Network Interception

**Playwright:**
```python
# Route requests
await page.route("**/api/*", lambda route: route.fulfill(
    status=200,
    body='{"data": "mocked"}'
))

# Monitor requests
page.on("request", lambda request: print(request.url))
page.on("response", lambda response: print(response.status))
```

**Nodriver:**
```python
import nodriver.cdp as cdp

# Monitor requests (CDP)
def on_request(event):
    print(event.request.url)

def on_response(event):
    print(event.response.status)

tab.add_handler(cdp.network.RequestWillBeSent, on_request)
tab.add_handler(cdp.network.ResponseReceived, on_response)

# Note: Request interception requires CDP implementation
```

## Feature Comparison

| Feature | Selenium | Playwright | Nodriver |
|---------|----------|------------|----------|
| **Browser Support** | ✅ All major | ✅ All major | ❌ Chrome only |
| **Headless Mode** | ✅ Reliable | ✅ Reliable | ⚠️ Unreliable |
| **Auto-waiting** | ❌ Manual | ✅ Built-in | ✅ Built-in |
| **Network Control** | ❌ Limited | ✅ Full | ⚠️ Via CDP |
| **Mobile Emulation** | ✅ Yes | ✅ Yes | ⚠️ Limited |
| **File Downloads** | ✅ Yes | ✅ Yes | ⚠️ Needs setup |
| **File Uploads** | ✅ Yes | ✅ Yes | ✅ Yes |
| **iframes** | ✅ Yes | ✅ Yes | ⚠️ Buggy |
| **Shadow DOM** | ✅ Yes | ✅ Yes | ⚠️ Via JS |
| **Screenshots** | ✅ Full | ✅ Full | ⚠️ Basic |
| **Videos** | ❌ No | ✅ Yes | ❌ No |
| **Tracing** | ❌ No | ✅ Yes | ❌ No |
| **Anti-detection** | ❌ Poor | ⚠️ Medium | ✅ Good |
| **Documentation** | ✅ Excellent | ✅ Excellent | ❌ Poor |
| **Community** | ✅ Large | ✅ Growing | ⚠️ Small |

## Migration Strategies

### Gradual Migration

1. **Identify Detection Points**
   - Run existing Selenium/Playwright code
   - Note where detection occurs
   - Migrate only those parts to nodriver

2. **Hybrid Approach**
   ```python
   # Use nodriver for login (anti-detection)
   browser = await uc.start()
   tab = await browser.get("https://site.com/login")
   # ... login with nodriver ...
   cookies = await tab.get_cookies()

   # Switch to Playwright for complex automation
   # Load cookies into Playwright session
   ```

3. **Feature-by-Feature**
   - Start with simple navigations
   - Add element interactions
   - Implement waits and conditions
   - Add error handling

### Common Patterns Translation

**Page Object Pattern:**

Selenium:
```python
class LoginPage:
    def __init__(self, driver):
        self.driver = driver

    def login(self, username, password):
        self.driver.find_element(By.ID, "username").send_keys(username)
        self.driver.find_element(By.ID, "password").send_keys(password)
        self.driver.find_element(By.ID, "submit").click()
```

Nodriver:
```python
class LoginPage:
    def __init__(self, tab):
        self.tab = tab

    async def login(self, username, password):
        user_field = await self.tab.select("#username")
        await user_field.send_keys(username)

        pass_field = await self.tab.select("#password")
        await pass_field.send_keys(password)

        submit = await self.tab.select("#submit")
        await submit.click()
```

### Testing Considerations

Nodriver is NOT recommended for testing:
- No test framework integration
- Limited assertion capabilities
- No video recording
- Poor debugging tools

For testing, stick with Selenium or Playwright.
For scraping protected sites, consider nodriver.

## Migration Checklist

- [ ] Convert to async/await syntax
- [ ] Replace WebDriver with CDP approach
- [ ] Update element selectors to CSS
- [ ] Implement text-based selection where helpful
- [ ] Add human-like delays
- [ ] Handle nodriver-specific bugs (send_keys, iframes)
- [ ] Implement proper error handling
- [ ] Test anti-detection effectiveness
- [ ] Document nodriver limitations for team

## Best Practices

1. **Always use async/await** - nodriver is fully async
2. **Prefer CSS selectors** - faster than XPath
3. **Use text selection** - unique nodriver feature
4. **Add human behavior** - delays, scrolling, mouse movement
5. **Handle errors gracefully** - nodriver has more edge cases
6. **Test thoroughly** - less mature than alternatives
7. **Keep fallbacks** - for when nodriver fails
8. **Monitor detection** - anti-detection is an arms race