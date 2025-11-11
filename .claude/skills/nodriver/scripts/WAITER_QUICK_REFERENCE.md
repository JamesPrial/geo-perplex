# ElementWaiter - Quick Reference

## Quick Start

```python
from element_waiter import ElementWaiter

waiter = ElementWaiter(tab)
result = await waiter.wait_for_clickable("#button", timeout=10)
if result.success:
    await result.element.click()
```

## All Wait Methods

| Method | What it waits for | Returns |
|--------|-------------------|---------|
| `wait_for_presence(selector)` | Element in DOM | WaitResult |
| `wait_for_visible(selector)` | Element visible | WaitResult |
| `wait_for_clickable(selector)` | Element clickable | WaitResult |
| `wait_for_text(selector, text)` | Text in element | WaitResult |
| `wait_for_attribute(selector, attr, value)` | Attribute value | WaitResult |
| `wait_for_javascript(script)` | JS returns true | WaitResult |
| `wait_for_network_idle()` | Network idle | WaitResult |
| `wait_for_custom(async_func)` | Custom condition | WaitResult |
| `wait_for_all(conditions)` | All conditions true | WaitResult |
| `wait_for_any(conditions)` | Any condition true | WaitResult |

## Condition Classes

```python
from element_waiter import (
    PresenceCondition,
    VisibilityCondition,
    ClickableCondition,
    TextPresentCondition,
    AttributeValueCondition,
    JavaScriptCondition,
    CompoundCondition
)

# Use directly
presence = PresenceCondition("#form")
if await presence.check(tab):
    print("Form exists")

# Combine conditions
conditions = [
    VisibilityCondition("#button"),
    TextPresentCondition("#label", "Click Me")
]
compound = CompoundCondition(conditions, use_and=True)
```

## Convenience Functions

```python
from element_waiter import (
    wait_for_element,
    wait_for_visible,
    wait_for_clickable,
    wait_for_text
)

# Direct calls without creating waiter instance
element = await wait_for_element(tab, "#btn", timeout=10)
element = await wait_for_visible(tab, "#modal", timeout=10)
element = await wait_for_clickable(tab, "#submit", timeout=10)
success = await wait_for_text(tab, "#msg", "Done", timeout=10)
```

## WaitResult Fields

```python
result.success          # bool - Did condition meet?
result.element          # Any - The element (if found)
result.wait_time        # float - Seconds waited
result.condition_type   # WaitConditionType - Type of condition
result.error           # str - Error message if failed
result.attempts        # int - Number of poll attempts
```

## Example Patterns

### Pattern 1: Basic Wait and Click
```python
result = await waiter.wait_for_clickable("#button", timeout=10)
if result.success:
    await result.element.click()
```

### Pattern 2: Wait for Text
```python
result = await waiter.wait_for_text("#status", "Complete", timeout=30)
if result.success:
    print("Task completed")
```

### Pattern 3: Custom JavaScript
```python
result = await waiter.wait_for_javascript(
    "return document.readyState === 'complete'",
    timeout=10
)
```

### Pattern 4: Multiple Conditions (ANY)
```python
conditions = [
    TextPresentCondition("#success", "Success"),
    TextPresentCondition("#error", "Error", partial=True)
]
result = await waiter.wait_for_any(conditions, timeout=10)
```

### Pattern 5: Multiple Conditions (ALL)
```python
conditions = [
    VisibilityCondition("#form"),
    AttributeValueCondition("#form", "data-ready", "true")
]
result = await waiter.wait_for_all(conditions, timeout=10)
```

### Pattern 6: Custom Async Condition
```python
async def data_loaded(tab):
    rows = await tab.select_all("table tr")
    return len(rows) > 5

result = await waiter.wait_for_custom(data_loaded, timeout=10)
```

### Pattern 7: Error Handling
```python
result = await waiter.wait_for_clickable("#submit", timeout=10)
if not result.success:
    print(f"Failed: {result.error}")
    print(f"Attempts: {result.attempts}")
    raise TimeoutError(f"Element not ready: {result.error}")
```

### Pattern 8: Chained Waits
```python
# Wait for form
r1 = await waiter.wait_for_visible("#form", timeout=10)
if not r1.success:
    return False

# Wait for specific field
r2 = await waiter.wait_for_clickable("#email", timeout=10)
if not r2.success:
    return False

# Fill and continue
await r2.element.type("test@example.com")
```

## Configuration

```python
# Custom poll interval
waiter = ElementWaiter(tab, poll_interval=0.05)  # Fast
waiter = ElementWaiter(tab, poll_interval=0.5)   # Slow

# Enable verbose logging
waiter = ElementWaiter(tab, verbose=True)
```

## Text Matching

```python
# Partial match (substring)
await waiter.wait_for_text("#msg", "Success", partial=True)

# Exact match
await waiter.wait_for_text("#counter", "100", partial=False)
```

## Timeout Guidelines

```python
# Quick visibility checks (element likely ready)
timeout=2

# Normal operations (API calls, animations)
timeout=10

# Long operations (uploads, heavy processing)
timeout=60
```

## JavaScript Condition Examples

```python
# Page loaded
"return document.readyState === 'complete'"

# Element visible
"return document.querySelector('#id').offsetHeight > 0"

# App state
"return window.app && window.app.ready"

# No loading spinners
"return !document.body.classList.contains('loading')"

# API call done
"return window.__apiPending === 0"

# Element has class
"return document.querySelector('#id').classList.contains('active')"

# Multiple elements
"return document.querySelectorAll('.item').length >= 10"

# Form valid
"return document.querySelector('#form').checkValidity()"
```

## Clickable Checks (wait_for_clickable)

Verifies all of:
- ✓ Element exists
- ✓ Element is visible
- ✓ Element is enabled
- ✓ Element is in viewport
- ✓ Element has dimensions (width, height > 0)
- ✓ No pointer-events: none
- ✓ Not covered by parent hidden elements

## Common Issues

| Issue | Solution |
|-------|----------|
| Timeout on fast operations | Reduce timeout (e.g., 2s for ready elements) |
| Timeout on slow operations | Increase timeout (e.g., 60s for uploads) |
| Condition never true | Check selector/condition, enable verbose mode |
| High CPU usage | Increase poll_interval (e.g., 0.5s) |
| Element not found | Verify selector, check for iframes |
| Race conditions | Use AND conditions, chain waits properly |

## Imports

```python
# Main class
from element_waiter import ElementWaiter

# Convenience functions
from element_waiter import (
    wait_for_element,
    wait_for_visible,
    wait_for_clickable,
    wait_for_text
)

# Condition classes
from element_waiter import (
    PresenceCondition,
    VisibilityCondition,
    ClickableCondition,
    TextPresentCondition,
    AttributeValueCondition,
    JavaScriptCondition,
    NetworkIdleCondition,
    CompoundCondition
)

# Data classes
from element_waiter import (
    WaitResult,
    WaitConditionType,
    NetworkIdleStrategy
)
```

## Performance Tips

1. **Use specific conditions** - More specific = faster failure
2. **Appropriate timeouts** - Not too long, not too short
3. **Fast polling for quick checks** - poll_interval=0.05
4. **Slow polling for long waits** - poll_interval=0.5
5. **Combine conditions wisely** - AND for safety, OR for flexibility
6. **Check logs** - Enable verbose=True to debug

## Integration with SmartClicker

```python
from smart_click import SmartClicker
from element_waiter import ElementWaiter

# Wait for element to be safe to click
waiter = ElementWaiter(tab)
result = await waiter.wait_for_clickable("#button")

# Then use SmartClicker for reliable clicking
clicker = SmartClicker(tab)
click_result = await clicker.click("#button")
```

## Integration with SafeTyper

```python
from safe_type import SafeTyper
from element_waiter import ElementWaiter

# Wait for field to be ready
waiter = ElementWaiter(tab)
result = await waiter.wait_for_visible("#input")

# Then type safely
typer = SafeTyper(tab)
success = await typer.type_in_field("#input", "text")
```

---

For complete documentation, see `WAITER_GUIDE.md`
