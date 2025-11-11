---
name: nodriver
description: Comprehensive assistance for nodriver browser automation, providing reusable scripts, patterns, and solutions for stealth web scraping, anti-bot bypass, and browser automation with Chrome DevTools Protocol.
---

# Nodriver Development Assistant

This skill provides comprehensive tools and patterns for developing with nodriver, an undetectable browser automation library that bypasses anti-bot protections.

## Purpose

This skill accelerates nodriver development by providing:
- Battle-tested scripts for common automation tasks
- Solutions to known issues and bugs
- Anti-detection patterns that work
- CDP (Chrome DevTools Protocol) integration examples
- Complete templates for scraping, login automation, and data extraction
- Docker configurations for production deployment

## When to Use This Skill

Use this skill when:
- Building web scrapers that need to bypass anti-bot protection
- Automating websites that detect and block Selenium/Playwright
- Working with Cloudflare-protected sites
- Implementing stealth browser automation
- Needing reliable element interaction patterns
- Setting up nodriver in Docker/Linux environments
- Migrating from Selenium/Playwright to nodriver
- Troubleshooting common nodriver issues

## Quick Start

### Basic Browser Setup
```python
# Use the quick_start script for optimal configuration
from scripts.quick_start import create_browser, BrowserConfig

# Basic usage with anti-detection settings
browser = await create_browser()
tab = await browser.get("https://example.com")

# Custom configuration
config = BrowserConfig(headless=False, disable_images=True)
browser = await create_browser(config, verbose=True)
```

### Docker/Linux Setup
```python
# Use docker_setup for containerized environments
from scripts.docker_setup import DockerSetupHelper

helper = DockerSetupHelper()
helper.setup()
args = helper.get_browser_args()
browser = await nodriver.start(args=args)
```

## Scripts

### Browser Initialization (`scripts/`)

#### `quick_start.py`
Complete browser initialization with anti-detection settings:
```python
from scripts.quick_start import create_browser
browser = await create_browser()
```
- Automatic retry on failures
- Optimized anti-detection configuration
- Custom user agents and viewport settings

#### `docker_setup.py`
Docker and Linux environment configuration:
```python
from scripts.docker_setup import DockerSetupHelper
helper = DockerSetupHelper()
helper.diagnose()  # Check environment
```
- Automatic environment detection
- Xvfb display server setup
- Chrome dependency checking

#### `profile_manager.py`
Session and profile persistence:
```python
from scripts.profile_manager import ProfileManager
manager = ProfileManager(base_dir="./profiles")
profile = manager.get_or_create_profile("my_account")
```
- Cookie saving/loading
- localStorage management
- Multi-profile support

### Element Interaction (`scripts/`)

#### `smart_click.py`
Reliable clicking with multiple fallback strategies:
```python
from scripts.smart_click import SmartClicker
clicker = SmartClicker(tab)
result = await clicker.click("#button")
```
- 6 different click strategies
- Automatic fallback on failure
- iframe handling

#### `safe_type.py`
Text input that handles the send_keys() bug:
```python
from scripts.safe_type import SafeTyper
typer = SafeTyper(tab)
await typer.type_with_retry("#input", "text")
```
- Character-by-character typing
- JavaScript injection fallback
- Input verification

#### `element_waiter.py`
Advanced wait conditions:
```python
from scripts.element_waiter import ElementWaiter
waiter = ElementWaiter(tab)
result = await waiter.wait_for_clickable("#submit")
```
- Wait for visibility, clickability, text
- Custom JavaScript conditions
- Network idle detection

### Anti-Detection (`scripts/`)

#### `human_behavior.py`
Natural behavior patterns:
```python
from scripts.human_behavior import HumanBehavior
behavior = HumanBehavior()
await behavior.read_page(tab)
await behavior.scroll_naturally(tab)
```
- Random delays with exponential distribution
- Bezier curve mouse movements
- Natural scrolling patterns

#### `cookie_manager.py`
Cookie and session management:
```python
from scripts.cookie_manager import create_manager
manager = create_manager(storage_dir=".cookies")
manager.load("session")
manager.apply_to_browser(browser)
```
- Cookie persistence
- Domain-specific filtering
- Session restoration

### CDP Integration (`scripts/`)

#### `network_monitor.py`
Network request/response monitoring:
```python
from scripts.network_monitor import NetworkMonitor
monitor = NetworkMonitor()
monitor.enable()
# Connect CDP events to monitor
```
- Request/response interception
- Performance metrics
- Failed request tracking

## Templates (`assets/templates/`)

### `basic_scraper.py`
Complete web scraping template:
```python
from assets.templates.basic_scraper import BasicScraper
scraper = BasicScraper(url="https://example.com")
scraper.set_extractors(item_selector=".product")
data = await scraper.scrape()
scraper.export_csv("output.csv")
```
- Pagination handling
- Error recovery
- Multiple export formats

### `login_automation.py`
Authentication flow template:
```python
from assets.templates.login_automation import LoginManager
manager = LoginManager(config)
await manager.login()
```
- Form-based login
- 2FA handling
- Session persistence
- OAuth simulation

### `data_extractor.py`
Structured data extraction:
```python
from assets.templates.data_extractor import DataExtractor
extractor = DataExtractor(tab)
products = await extractor.extract_products(".product")
```
- Table extraction
- Infinite scroll handling
- Image collection
- Data validation

## Docker Support (`assets/docker/`)

### Production-Ready Dockerfile
```dockerfile
FROM python:3.11-slim
# Optimized for browser automation
# Includes Chrome, Xvfb, and all dependencies
```

### Docker Compose Configuration
```yaml
services:
  nodriver-app:
    build: .
    environment:
      - DISPLAY=:99
    volumes:
      - ./profiles:/app/profiles
```

## Reference Documentation (`references/`)

### `common_patterns.md`
Frequently used code patterns:
- Browser initialization patterns
- Element selection strategies
- Wait strategies
- Error handling patterns
- Anti-detection techniques

### `known_issues.md`
Solutions to common problems:
- send_keys() truncation bug workarounds
- Headless mode issues
- Docker/Linux setup problems
- Detection bypass techniques
- Performance optimization

### `migration_guide.md`
Migration from Selenium/Playwright:
- Syntax conversion tables
- Feature comparison
- Migration strategies
- When to use nodriver vs alternatives

## Common Workflows

### Stealth Web Scraping
```python
from scripts.quick_start import create_browser
from scripts.human_behavior import HumanBehavior
from assets.templates.basic_scraper import BasicScraper

# Initialize with anti-detection
browser = await create_browser()
behavior = HumanBehavior()

# Navigate with human-like behavior
tab = await browser.get(url)
await behavior.read_page(tab)

# Scrape data
scraper = BasicScraper(tab=tab)
data = await scraper.scrape()
```

### Authenticated Sessions
```python
from scripts.profile_manager import ProfileManager
from assets.templates.login_automation import LoginManager

# Load or create profile
profile_manager = ProfileManager()
profile = profile_manager.get_or_create_profile("user1")

# Login if needed
if not profile.has_cookies():
    login_manager = LoginManager(config, tab)
    await login_manager.login()
    profile.save_cookies(await tab.get_cookies())
```

### Docker Deployment
```bash
# Build and run with Docker Compose
docker-compose up -d

# Or use the Dockerfile directly
docker build -t nodriver-app .
docker run -d nodriver-app
```

## Best Practices

1. **Always use visible mode** when possible (better anti-detection)
2. **Add human-like delays** between actions using `human_behavior.py`
3. **Persist sessions** with `profile_manager.py` to avoid re-authentication
4. **Use fallback strategies** with `smart_click.py` for reliable interactions
5. **Monitor network** with `network_monitor.py` for dynamic content
6. **Handle errors gracefully** with screenshots and retries
7. **Test locally first** before deploying to Docker
8. **Check known issues** in `references/known_issues.md` for solutions

## Troubleshooting

### Element Not Found
- Use `element_waiter.py` for dynamic content
- Try text-based selection: `tab.find("text", best_match=True)`
- Check if element is in iframe

### Click Not Working
- Use `smart_click.py` with automatic fallbacks
- Try JavaScript click as last resort

### Text Input Issues
- Use `safe_type.py` for reliable typing
- Type character-by-character with delays

### Docker/Linux Issues
- Run `docker_setup.py` diagnostics
- Ensure `no_sandbox=True` is set
- Check Xvfb is running

### Detection Issues
- Use `human_behavior.py` patterns
- Avoid headless mode
- Use real Chrome (not Chromium)
- Add random delays between actions

## Advanced Usage

### Custom CDP Commands
```python
import nodriver.cdp as cdp

# Network interception
await tab.send(cdp.network.enable())

# Custom user agent
await tab.send(cdp.network.set_user_agent_override(
    user_agent="Custom User Agent"
))

# JavaScript execution
result = await tab.send(cdp.runtime.evaluate(
    expression="document.title"
))
```

### Performance Monitoring
```python
from scripts.network_monitor import NetworkMonitor

monitor = NetworkMonitor()
# ... perform actions ...
metrics = monitor.get_metrics()
print(f"Total requests: {metrics['total_requests']}")
print(f"Failed requests: {len(metrics['failed_requests'])}")
print(f"Average response time: {metrics['avg_response_time']}ms")
```

## Resources

- **GitHub Issues**: Check for known problems and solutions
- **Examples**: See `scripts/*_examples.py` for working code
- **Templates**: Use `assets/templates/` as starting points
- **References**: Consult `references/` for patterns and guides

## Summary

This skill transforms nodriver development from trial-and-error to productive automation by providing:
- ✅ Tested solutions to common problems
- ✅ Reliable interaction patterns
- ✅ Anti-detection techniques that work
- ✅ Complete templates for common tasks
- ✅ Docker configurations for deployment
- ✅ Comprehensive documentation

Start with the scripts that match your needs, refer to the references for patterns and issues, and use the templates for complete solutions. The skill handles the complexity so you can focus on your automation goals.