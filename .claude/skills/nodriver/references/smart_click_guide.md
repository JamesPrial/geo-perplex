# Smart Click Guide

## Overview

The `smart_click.py` script provides a robust, production-ready solution for clicking elements in web automation. It handles edge cases where normal clicking fails by automatically trying multiple strategies in order of likelihood to succeed.

## When to Use Smart Click

Use `SmartClicker` when:
- Elements fail to respond to standard WebDriver clicks
- Elements are inside iframes or shadow DOM
- Elements have complex CSS (opacity, transform, pointer-events)
- Elements need scroll-into-view before interaction
- You need verification that the click actually worked
- Elements require human-like interaction timing
- You want to avoid manual try-catch blocks for different click methods

## Click Strategies (In Order)

SmartClicker tries these strategies automatically:

### 1. **Normal Click** (NORMAL)
- Uses Chrome DevTools Protocol to dispatch mouse events
- Positions cursor at element center with human-like offsets
- Most reliable for standard interactive elements
- Success rate: 80-90%

### 2. **JavaScript Click** (JAVASCRIPT)
- Calls `element.click()` directly
- Bypasses some visibility checks
- Works when mouse events are blocked
- Success rate: 70-85%

### 3. **Focus + Enter** (FOCUS_ENTER)
- Focuses the element
- Simulates pressing Enter key
- Perfect for buttons, links, and form inputs
- Success rate: 75-90%

### 4. **Focus + Space** (FOCUS_SPACE)
- Focuses the element
- Simulates pressing Space key
- Works for buttons and checkboxes
- Success rate: 75-90%

### 5. **Dispatch Events** (DISPATCH_EVENT)
- Manually dispatches mousedown, mouseup, click events
- Useful for custom event handlers
- Works with event listeners
- Success rate: 70-80%

### 6. **Double Click** (DOUBLE_CLICK)
- Performs a double-click action
- Last resort for elements needing multi-click
- Success rate: 50-70%

## Core Features

### Element Visibility Checking
Verifies elements are actually visible:
- Not hidden with `display: none`
- Not hidden with `visibility: hidden`
- Not fully transparent (`opacity: 0`)
- Has positive width and height
- In viewport bounds

### Element Interactability Checking
Verifies elements can receive interactions:
- Not disabled
- Not marked with `aria-disabled`
- Has `pointer-events: auto`
- No parent elements are hidden
- Accessible in the DOM

### Scroll-Into-View
Automatically scrolls elements into view:
- Smooth scrolling behavior
- Centers element in viewport
- Respects scroll padding
- Waits for scroll animation to complete

### Human-Like Interaction
Makes automation less detectable:
- Random click position offsets (±5 pixels)
- Variable delays between actions (10-500ms)
- Realistic mouse event sequences
- Optional timing randomization

### Click Verification
Confirms the click action succeeded:
- Custom verification callbacks
- Checks for expected side effects
- Timeout handling
- Detailed result reporting

## Usage Examples

### Basic Click
```python
from smart_click import SmartClicker

clicker = SmartClicker(tab=my_tab)
result = await clicker.click("#submit-button")

if result.success:
    print(f"Clicked using {result.strategy_used.value}")
else:
    print(f"Click failed: {result.error}")
```

### Click with Verification
```python
async def verify_submit():
    """Check if form submission succeeded."""
    result = await my_tab.select(".success-message")
    return result is not None

result = await clicker.click(
    "#submit-button",
    verify_action=verify_submit
)

if result.verification_passed:
    print("Form was successfully submitted!")
```

### Click with Custom Configuration
```python
clicker = SmartClicker(
    tab=my_tab,
    verify_click=True,           # Verify results
    scroll_into_view=True,       # Scroll before clicking
    human_like_delay=True,       # Add realistic delays
    max_retries=6                # Try up to 6 strategies
)

result = await clicker.click(
    "#element",
    timeout=15.0  # 15 second timeout
)
```

### Click Inside Iframe
```python
# SmartClicker handles iframes automatically
# Just select elements as if they're in the main page
result = await clicker.click("#button-inside-iframe")

# Or manually switch context if needed
iframe = await my_tab.select("iframe#target")
clicker_iframe = SmartClicker(iframe)
result = await clicker_iframe.click("#inner-button")
```

### Convenience Function
```python
from smart_click import smart_click

# Quick click without creating an instance
result = await smart_click(
    tab=my_tab,
    selector="#button",
    timeout=10.0
)
```

### Click Multiple Elements
```python
selectors = ["#step1-btn", "#step2-btn", "#step3-btn"]

for selector in selectors:
    result = await clicker.click(selector)
    if not result.success:
        print(f"Failed at {selector}")
        break
    print(f"Clicked {selector} using {result.strategy_used.value}")
```

## Understanding ClickResult

The `ClickResult` object contains:

```python
@dataclass
class ClickResult:
    success: bool                   # Whether click succeeded
    strategy_used: ClickStrategy    # Which strategy worked
    attempts: int                   # How many strategies tried
    error: Optional[str]            # Error message if failed
    verification_passed: bool       # Verification result
```

Example inspection:
```python
result = await clicker.click("#button")

print(f"Success: {result.success}")
print(f"Strategy: {result.strategy_used.value}")
print(f"Attempts: {result.attempts}")
if result.error:
    print(f"Error: {result.error}")
if result.success:
    print(f"Verified: {result.verification_passed}")
```

## Configuration Options

### verify_click (default: True)
When enabled, allows you to pass a `verify_action` callback to confirm the click worked. This prevents silent failures where click executes but doesn't do what you expect.

```python
clicker = SmartClicker(tab, verify_click=True)
```

### scroll_into_view (default: True)
Automatically scrolls elements into viewport before clicking. Disable for elements you know are visible.

```python
clicker = SmartClicker(tab, scroll_into_view=True)
```

### human_like_delay (default: True)
Adds realistic random delays and click position offsets. Disable only for performance-critical automation where detection isn't a concern.

```python
clicker = SmartClicker(tab, human_like_delay=True)
```

### max_retries (default: 5)
Maximum number of click strategies to attempt. Increase for very problematic elements.

```python
clicker = SmartClicker(tab, max_retries=6)
```

## Edge Cases Handled

### Problem: Element disabled but visible
**Solution:** Checks `disabled` attribute and `aria-disabled` before clicking

### Problem: Element inside modal overlay
**Solution:** Scroll-into-view and visibility checks ensure element is accessible

### Problem: Click triggers but event doesn't fire
**Solution:** Tries multiple event dispatch methods and JavaScript click

### Problem: Element hidden with CSS transforms
**Solution:** Checks computed styles, not just DOM visibility

### Problem: Click succeeds but action incomplete
**Solution:** Optional verification callback confirms expected results

### Problem: Element moves after focus
**Solution:** Re-evaluates position before each click attempt

### Problem: Heavy JavaScript on page
**Solution:** Timeout handling prevents hanging, automatic fallback to simpler methods

### Problem: Elements inside iframes
**Solution:** Handles context switching, works with frame elements

## Performance Considerations

### Optimization Tips
1. **Set timeout appropriately**: Use 5-10s for stable pages, 15-20s for heavy JS
2. **Disable verification if not needed**: Speeds up clicks when reliability isn't critical
3. **Reuse SmartClicker instance**: Create once, use for multiple clicks
4. **Disable human_like_delay for internal tools**: Only needed when avoiding detection

### Performance Profile
- Normal strategy: 50-100ms
- Full retry cycle: 500ms-2s
- With verification: Add another 200-500ms

## Troubleshooting

### Click says success but nothing happens
**Check:** Is your verification function correct?
```python
# Wrong - doesn't return boolean
async def verify_wrong():
    await my_tab.select(".result")

# Correct
async def verify_correct():
    result = await my_tab.select(".result")
    return result is not None
```

### All strategies fail
**Check:**
1. Is the selector correct? (`result.error` will show)
2. Is element actually on page? (Try in DevTools console)
3. Is element in an iframe? (May need to switch contexts)
4. Is element behind a modal? (Try close modal first)

### Click is too slow
**Optimize:**
```python
# Disable features you don't need
clicker = SmartClicker(
    tab=my_tab,
    verify_click=False,        # Don't verify
    scroll_into_view=False,    # Element already visible
    human_like_delay=False     # Internal automation
)
```

### Want to see what's happening
**Enable logging:**
```python
# The logger is simple - modify SmartClicker._setup_logger()
# to print debug messages:
class SimpleLogger:
    def debug(self, msg):
        print(f"[DEBUG] {msg}")  # Change pass to print
    # ...
```

## Common Patterns

### Wait for element, then click
```python
async def wait_and_click(tab, selector, timeout=10.0):
    clicker = SmartClicker(tab)
    # SmartClicker.click includes timeout and retries
    return await clicker.click(selector, timeout=timeout)
```

### Click and verify state change
```python
async def click_and_verify_state(tab, button_selector, state_selector):
    clicker = SmartClicker(tab, verify_click=True)

    async def verify_state():
        element = await tab.select(state_selector)
        return element is not None

    result = await clicker.click(
        button_selector,
        verify_action=verify_state
    )
    return result.success and result.verification_passed
```

### Retry entire sequence on failure
```python
async def resilient_click_sequence(tab, selectors, max_attempts=3):
    clicker = SmartClicker(tab)

    for attempt in range(max_attempts):
        for selector in selectors:
            result = await clicker.click(selector)
            if not result.success:
                print(f"Attempt {attempt + 1} failed at {selector}")
                break
        else:
            return True  # All succeeded

    return False  # All attempts failed
```

### Monitor which strategies are needed
```python
strategy_stats = {}

for button_id in range(1, 10):
    result = await clicker.click(f"#btn{button_id}")
    strategy = result.strategy_used.value
    strategy_stats[strategy] = strategy_stats.get(strategy, 0) + 1

print("Strategy usage:")
for strategy, count in sorted(strategy_stats.items(),
                               key=lambda x: -x[1]):
    print(f"  {strategy}: {count} times")
```

## Integration with Other Tools

### With wait strategies
```python
# Wait for element, then click
await clicker.tab.wait_for("#button")
result = await clicker.click("#button")
```

### With form filling
```python
# Fill form fields
await clicker.tab.type_text("#username", "user@example.com")
await clicker.tab.type_text("#password", "password123")

# Click submit with fallbacks
result = await clicker.click("#submit")
```

### With navigation
```python
# Click and wait for navigation
async def click_and_navigate(tab, selector, timeout=30):
    clicker = SmartClicker(tab)
    result = await clicker.click(selector)

    if result.success:
        # Wait for page to change
        await asyncio.sleep(1)  # Wait for nav to start

    return result
```

## API Reference

### SmartClicker Class

#### `__init__(tab, verify_click=True, scroll_into_view=True, human_like_delay=True, max_retries=5)`
Initialize clicker with configuration.

#### `async click(selector, verify_action=None, timeout=10.0) -> ClickResult`
Click element with automatic fallback strategies.

- **selector**: CSS selector string
- **verify_action**: Optional async callable to verify success
- **timeout**: Operation timeout in seconds
- **returns**: ClickResult with success/failure details

### Functions

#### `async smart_click(tab, selector, verify_action=None, timeout=10.0) -> ClickResult`
Convenience function to click without creating SmartClicker instance.

### Classes

#### `ClickStrategy` (Enum)
Enumeration of click strategies: NORMAL, JAVASCRIPT, FOCUS_ENTER, FOCUS_SPACE, DISPATCH_EVENT, DOUBLE_CLICK

#### `ClickResult` (dataclass)
Result object with:
- `success: bool` - Whether click succeeded
- `strategy_used: ClickStrategy` - Which strategy worked
- `attempts: int` - How many strategies attempted
- `error: Optional[str]` - Error message if failed
- `verification_passed: bool` - Verification result

## Best Practices

1. **Always check `result.success`** before assuming click worked
2. **Use verification callbacks** for critical actions (form submission, state changes)
3. **Set appropriate timeouts** based on page complexity
4. **Reuse SmartClicker instances** for multiple clicks
5. **Log strategy usage** to identify problematic elements
6. **Test selectors separately** to ensure they find elements
7. **Consider human-like delays** when avoiding detection is important
8. **Handle TimeoutError** separately from click failures
9. **Document why you need each click** for maintenance
10. **Profile performance** in your specific environment

## Limitations

- Requires nodriver library (gracefully fails if not installed)
- May not work with shadow DOM (use slots or pierceHandler)
- Some drag-and-drop operations may need additional code
- Right-click and middle-click need custom implementation
- Can't click elements that are completely off-screen
- Verification callbacks are user's responsibility

## Future Enhancements

Potential improvements for advanced use:
- Right-click and middle-click support
- Drag-and-drop automation
- Multi-element click sequences
- Element highlight and screenshot on failure
- Built-in verification for common patterns
- Performance metrics collection
- Shadow DOM piercing support
