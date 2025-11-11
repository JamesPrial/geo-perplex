# Known Issues and Troubleshooting

This document covers common issues with nodriver and their solutions.

## Table of Contents
1. [Installation Issues](#installation-issues)
2. [Browser Launch Problems](#browser-launch-problems)
3. [Element Interaction Issues](#element-interaction-issues)
4. [Headless Mode Problems](#headless-mode-problems)
5. [Docker/Linux Issues](#dockerlinux-issues)
6. [Network & Proxy Issues](#network--proxy-issues)
7. [Performance Issues](#performance-issues)
8. [Detection Issues](#detection-issues)

## Installation Issues

### Issue: Import Error - nodriver not found
```python
ModuleNotFoundError: No module named 'nodriver'
```

**Solution:**
```bash
pip install nodriver
# or for specific version
pip install nodriver==0.36.0
```

### Issue: Chrome/Chromium not found
```
FileNotFoundError: Could not determine browser executable
```

**Solution:**
```python
# Specify browser path explicitly
browser = await uc.start(
    browser_executable_path="/path/to/chrome"
)

# Common paths:
# Windows: "C:/Program Files/Google/Chrome/Application/chrome.exe"
# Mac: "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
# Linux: "/usr/bin/google-chrome" or "/usr/bin/chromium"
```

## Browser Launch Problems

### Issue: Browser crashes immediately
**Symptoms:** Browser opens and closes immediately

**Solutions:**
```python
# 1. Disable sandbox (especially for Docker/Linux)
browser = await uc.start(no_sandbox=True)

# 2. Add stability flags
browser = await uc.start(
    browser_args=[
        '--disable-gpu',
        '--disable-dev-shm-usage',
        '--disable-setuid-sandbox',
        '--no-first-run',
        '--no-zygote'
    ]
)

# 3. Use subprocess mode
browser = await uc.start(use_subprocess=True)
```

### Issue: Connection refused error
```
ConnectionRefusedError: Cannot connect to browser
```

**Solutions:**
```python
# 1. Kill existing Chrome processes
import os
os.system("pkill chrome")  # Linux/Mac
os.system("taskkill /f /im chrome.exe")  # Windows

# 2. Use a different port
browser = await uc.start(port=9223)  # Default is 9222

# 3. Check firewall settings
# Ensure localhost connections are allowed
```

## Element Interaction Issues

### Issue: send_keys() cuts off text
**Symptoms:** Only part of the text is typed

**Solution:**
```python
# Type character by character with delays
async def safe_type(element, text):
    for char in text:
        await element.send_keys(char)
        await asyncio.sleep(0.05)

# Or use JavaScript injection
await tab.evaluate(f'''
    document.querySelector("input").value = "{text}";
''')
```

### Issue: Element not clickable
```
Element is not clickable at point (x, y)
```

**Solutions:**
```python
# 1. Scroll element into view first
element = await tab.select("#button")
await element.scroll_into_view()
await asyncio.sleep(0.5)
await element.click()

# 2. Use JavaScript click
await tab.evaluate('''
    document.querySelector("#button").click();
''')

# 3. Wait for element to be ready
async def wait_and_click(tab, selector):
    for attempt in range(10):
        try:
            element = await tab.select(selector)
            await element.click()
            return
        except:
            await asyncio.sleep(1)
    raise Exception(f"Could not click {selector}")
```

### Issue: Element not found in iframe
**Symptoms:** Elements inside iframes cannot be selected

**Solution:**
```python
# Iframes should auto-switch but if not:

# 1. Access iframe as a target
targets = browser.targets
for target in targets:
    if target.type == "iframe":
        # Work with iframe target
        iframe_tab = target
        element = await iframe_tab.select("#element-in-iframe")

# 2. Use JavaScript to access iframe content
await tab.evaluate('''
    const iframe = document.querySelector("iframe");
    const iframeDoc = iframe.contentDocument || iframe.contentWindow.document;
    iframeDoc.querySelector("#element-in-iframe").click();
''')
```

## Headless Mode Problems

### Issue: Headless mode doesn't work
```
TypeError: cannot unpack non-iterable NoneType object
```

**Solutions:**
```python
# 1. Use new headless mode
browser = await uc.start(
    browser_args=['--headless=new']
)

# 2. Add required flags for headless
browser = await uc.start(
    headless=True,
    browser_args=[
        '--headless=new',
        '--disable-gpu',
        '--no-sandbox',
        '--disable-dev-shm-usage'
    ]
)

# 3. Consider not using headless (better for anti-detection anyway)
browser = await uc.start(headless=False)
```

### Issue: Screenshots don't work in headless
**Solution:**
```python
# Ensure window size is set
browser = await uc.start(
    headless=True,
    browser_args=['--window-size=1920,1080']
)

# Take screenshot with explicit viewport
await tab.set_viewport(width=1920, height=1080)
await tab.save_screenshot("screenshot.png")
```

## Docker/Linux Issues

### Issue: Chrome crashes in Docker
```
Failed to move to new namespace: PID namespaces supported...
```

**Solution:**
```python
# Required Docker configuration
browser = await uc.start(
    no_sandbox=True,
    browser_args=[
        '--disable-gpu',
        '--disable-dev-shm-usage',
        '--disable-setuid-sandbox'
    ]
)
```

**Dockerfile requirements:**
```dockerfile
# Install dependencies
RUN apt-get update && apt-get install -y \
    chromium \
    chromium-driver \
    xvfb

# Run with xvfb for display
CMD xvfb-run -a python your_script.py
```

### Issue: No display in Linux server
```
Cannot open display
```

**Solution:**
```bash
# Install and run Xvfb
sudo apt-get install xvfb

# Run with virtual display
xvfb-run -a python your_script.py

# Or in Python:
import os
os.environ['DISPLAY'] = ':99'
os.system('Xvfb :99 -screen 0 1920x1080x24 &')
```

## Network & Proxy Issues

### Issue: Proxy authentication not working
**Symptoms:** Authenticated proxies fail to connect

**Current Limitation:** nodriver doesn't have built-in authenticated proxy support

**Workarounds:**
```python
# 1. Use proxy without auth
browser = await uc.start(
    browser_args=['--proxy-server=http://proxy.example.com:8080']
)

# 2. Use external proxy tools
# - Use proxychains on Linux
# - Use system-wide proxy settings
# - Use proxy extensions (though detectable)

# 3. Set proxy via CDP (experimental)
await tab.send(cdp.network.set_user_agent_override(
    user_agent="...",
    platform="...",
))
```

### Issue: Downloads not working
**Solution:**
```python
import pathlib
from nodriver import cdp

# Set download behavior
download_path = pathlib.Path("./downloads").resolve()
await tab.send(cdp.browser.set_download_behavior(
    behavior="allow",
    download_path=str(download_path),
    events_enabled=True
))
```

## Performance Issues

### Issue: Slow on dynamic websites
**Symptoms:** Operations timeout on JavaScript-heavy sites

**Solutions:**
```python
# 1. Increase timeouts
element = await tab.select("#element", timeout=30)

# 2. Wait for network idle
await tab.sleep(2)  # Simple wait
# Or implement network monitoring

# 3. Disable images and unnecessary resources
browser = await uc.start(
    browser_args=[
        '--disable-images',
        '--disable-javascript',  # If possible
    ]
)

# 4. Use explicit waits
async def wait_for_element(tab, selector, timeout=30):
    start = time.time()
    while time.time() - start < timeout:
        try:
            return await tab.select(selector, timeout=1)
        except:
            await asyncio.sleep(0.5)
    raise TimeoutError(f"Element {selector} not found")
```

### Issue: Memory leaks
**Symptoms:** Memory usage grows over time

**Solutions:**
```python
# 1. Close tabs when done
await tab.close()

# 2. Restart browser periodically
async def process_with_restart(urls, batch_size=50):
    for i in range(0, len(urls), batch_size):
        browser = await uc.start()
        batch = urls[i:i+batch_size]

        for url in batch:
            tab = await browser.get(url)
            # Process...
            await tab.close()

        await browser.stop()

# 3. Clear cache periodically
await tab.send(cdp.network.clear_browser_cache())
```

## Detection Issues

### Issue: Still getting detected by Cloudflare
**Current Status:** nodriver has ~25% success rate against Cloudflare

**Best Practices:**
```python
# 1. Use real Chrome (not Chromium)
browser = await uc.start(
    browser_executable_path="/path/to/real/chrome"
)

# 2. Use existing profile with history
browser = await uc.start(
    user_data_dir="/path/to/real/profile"
)

# 3. Add human-like behavior
await tab.sleep(random.uniform(2, 5))  # Random delays
await tab.scroll_down(random.randint(100, 300))  # Random scrolls

# 4. Don't use headless mode
browser = await uc.start(headless=False)

# 5. Use residential proxies if possible
```

### Issue: Google/GitHub detecting bot
**Solutions:**
```python
# 1. Login with cookies from real session
# 2. Use delays between requests
# 3. Vary behavior patterns
# 4. Use tab.cf_verify() for Cloudflare
await tab.cf_verify()  # Attempts to click checkbox
```

## CDP (Chrome DevTools Protocol) Issues

### Issue: CDP commands timeout
```python
# Increase CDP timeout
tab._timeout = 30  # seconds

# Or retry CDP commands
async def retry_cdp(command, max_attempts=3):
    for attempt in range(max_attempts):
        try:
            return await tab.send(command)
        except:
            if attempt == max_attempts - 1:
                raise
            await asyncio.sleep(2 ** attempt)
```

### Issue: get_response_body hangs
**Known Issue:** Some responses can't be retrieved

**Workaround:**
```python
# Add timeout to prevent hanging
async def get_body_safe(tab, request_id, timeout=5):
    try:
        return await asyncio.wait_for(
            tab.send(cdp.network.get_response_body(request_id)),
            timeout=timeout
        )
    except asyncio.TimeoutError:
        return None, None
```

## Debug Techniques

### Enable Verbose Logging
```python
import logging
logging.basicConfig(level=logging.DEBUG)

# See what nodriver is doing
```

### Save Page Source on Error
```python
try:
    # Your automation
    pass
except Exception as e:
    # Save debugging info
    await tab.save_screenshot("error.png")

    source = await tab.get_content()
    with open("error.html", "w") as f:
        f.write(source)

    print(f"Error: {e}")
    print(f"URL: {await tab.get_url()}")
```

### Use External Debugger
```python
# Open Chrome DevTools
await tab.open_external_debugger()

# Browser stays connected while you debug manually
```

## Version-Specific Issues

### Version 0.36.0+
- `browser.cookies.set_all()` has reassignment bug
- Use `tab.set_cookies()` instead

### Version 0.35.0
- Memory leak issues (fixed in 0.36.0)

### Recommendations
- Use latest stable version
- Check GitHub issues for known problems
- Test thoroughly before production deployment

## Getting Help

1. Check GitHub Issues: https://github.com/ultrafunkamsterdam/nodriver/issues
2. Read the source code (documentation is limited)
3. Test in visible mode first
4. Use logging to understand failures
5. Take screenshots on errors
6. Try alternative approaches (Selenium, Playwright) if nodriver doesn't work for your use case