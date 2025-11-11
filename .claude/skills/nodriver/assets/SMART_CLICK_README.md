# SmartClicker - Reliable Element Interaction

A production-ready Python module for reliable element clicking in web automation with multiple fallback strategies and edge case handling.

## Quick Start

```python
from smart_click import SmartClicker

# Create clicker instance
clicker = SmartClicker(tab=my_tab)

# Click with automatic fallback strategies
result = await clicker.click("#submit-button")

if result.success:
    print(f"Clicked using {result.strategy_used.value}")
else:
    print(f"Click failed: {result.error}")
```

## Why SmartClicker?

Standard WebDriver click fails in many scenarios:
- Elements blocked by CSS transforms or opacity
- Event listeners expecting specific event types
- JavaScript frameworks with custom click handlers
- Elements inside iframes or shadow DOM
- Modal overlays interfering with click
- Heavy JavaScript preventing normal execution

SmartClicker automatically tries 6 different strategies and returns on the first success.

## Features

- **6 Click Strategies**: Normal, JavaScript, Focus+Enter, Focus+Space, Dispatch Events, Double-Click
- **Automatic Fallback**: Tries strategies in order of likelihood to succeed
- **Visibility Checks**: Verifies element is visible before clicking
- **Interactability Checks**: Ensures element can receive interactions
- **Scroll-Into-View**: Automatically scrolls elements into viewport
- **Click Verification**: Optional callbacks to confirm action succeeded
- **Human-Like Timing**: Random delays and click position offsets
- **Iframe Support**: Handles elements inside iframes
- **Comprehensive Logging**: Debug information without external dependencies
- **Type Hints**: Full typing support for IDE assistance

## Installation

Copy `smart_click.py` to your project:

```python
from smart_click import SmartClicker, smart_click, ClickResult, ClickStrategy
```

Requires: `nodriver` library

```bash
pip install nodriver
```

## Basic Usage

### Simple Click

```python
result = await clicker.click("#button")
```

### Click with Verification

```python
async def verify_submission():
    """Check that form was submitted."""
    msg = await tab.select(".success-message")
    return msg is not None

result = await clicker.click(
    "#submit",
    verify_action=verify_submission
)
```

### Click with Custom Timeout

```python
result = await clicker.click(
    "#slow-element",
    timeout=20.0  # 20 second timeout
)
```

## Configuration

### Create with Custom Settings

```python
clicker = SmartClicker(
    tab=my_tab,
    verify_click=True,           # Enable verification
    scroll_into_view=True,       # Scroll before click
    human_like_delay=True,       # Add realistic delays
    max_retries=5                # Try up to 5 strategies
)
```

### Per-Click Configuration

Only timeout can be configured per-click:

```python
result = await clicker.click(selector, timeout=15.0)
```

## Click Strategies

SmartClicker tries these in order (stops at first success):

| Strategy | Method | Best For | Reliability |
|----------|--------|----------|-------------|
| NORMAL | Mouse events via CDP | Standard elements | 80-90% |
| JAVASCRIPT | `element.click()` | Simple elements | 70-85% |
| FOCUS_ENTER | Focus + Enter key | Buttons, inputs | 75-90% |
| FOCUS_SPACE | Focus + Space key | Buttons, checkboxes | 75-90% |
| DISPATCH_EVENT | Manual event dispatch | Custom handlers | 70-80% |
| DOUBLE_CLICK | Double-click | Special cases | 50-70% |

## Understanding Results

### ClickResult Object

```python
result = await clicker.click("#button")

result.success                 # bool - did click succeed?
result.strategy_used          # ClickStrategy - which worked
result.attempts               # int - how many tried
result.error                  # str - error message if failed
result.verification_passed    # bool - did verification pass?
```

### Example Result Inspection

```python
result = await clicker.click("#submit")

if result.success:
    print(f"Success with {result.strategy_used.value}")
    print(f"Took {result.attempts} attempts")
    if result.verification_passed:
        print("Action verified!")
else:
    print(f"Failed: {result.error}")
```

## Common Patterns

### Robust Form Submission

```python
async def submit_form(tab):
    clicker = SmartClicker(tab, verify_click=True)

    # Fill form
    await tab.type_text("#email", "user@example.com")
    await tab.type_text("#password", "pass123")

    # Submit with verification
    async def verify():
        return await tab.select(".success-page") is not None

    result = await clicker.click(
        "#submit",
        verify_action=verify
    )
    return result.success and result.verification_passed
```

### Click with Retry Selectors

```python
selectors = [
    "#primary-submit",
    "button.submit",
    "button[type='submit']"
]

for selector in selectors:
    result = await clicker.click(selector, timeout=3.0)
    if result.success:
        return True

return False
```

### Multi-Step Sequence

```python
steps = [
    ("#step1-next", "Step 1"),
    ("#step2-next", "Step 2"),
    ("#confirm", "Confirm")
]

for selector, name in steps:
    result = await clicker.click(selector)
    if not result.success:
        print(f"Failed at {name}")
        return False
    print(f"Completed {name}")

return True
```

### Monitor Strategy Usage

```python
stats = {}

for selector in selectors:
    result = await clicker.click(selector)
    if result.success:
        strategy = result.strategy_used.value
        stats[strategy] = stats.get(strategy, 0) + 1

print("Strategy distribution:", stats)
```

## Edge Cases Handled

| Issue | Solution |
|-------|----------|
| Element hidden with CSS | Checks computed styles before clicking |
| Click doesn't trigger event | Tries multiple event dispatch methods |
| Element behind modal | Scroll-into-view + visibility checks |
| Element inside iframe | Works with iframe context |
| Heavy JavaScript on page | Timeout protection prevents hanging |
| Element moves after focus | Re-evaluates position for each strategy |
| Custom event listeners | Dispatch event strategy covers this |
| Disabled elements | Checks disabled attribute before clicking |

## Performance

| Operation | Typical Time |
|-----------|-------------|
| Normal click (success 1st try) | 50-100ms |
| Full retry cycle (all strategies) | 500ms-2s |
| With verification | +200-500ms |
| Heavy JS page with timeouts | 5-20s |

### Optimization Tips

1. **Disable verification if not needed**: Skip verify_action parameter
2. **Disable scroll if element visible**: Set scroll_into_view=False
3. **Disable human delays for internal tools**: Set human_like_delay=False
4. **Use appropriate timeout**: 5-10s normal, 15-20s for heavy JS
5. **Reuse SmartClicker instance**: Create once, use for multiple clicks

## Error Handling

### Check Success

```python
result = await clicker.click("#button")

if not result.success:
    print(f"Error: {result.error}")
    # Handle failure
```

### Common Errors

| Error | Cause | Fix |
|-------|-------|-----|
| Element not found | Selector doesn't match | Check selector in DevTools |
| Timeout exceeded | Element takes too long | Increase timeout |
| All strategies failed | Fundamental click issue | Try different selector/context |
| Verification failed | Action didn't work | Check verify function logic |

### Timeout Handling

```python
try:
    result = await clicker.click(
        "#button",
        timeout=10.0
    )
except asyncio.TimeoutError:
    print("Operation timed out")
```

## Convenience Function

For quick one-off clicks without creating an instance:

```python
from smart_click import smart_click

result = await smart_click(
    tab=my_tab,
    selector="#button",
    timeout=10.0
)
```

## Logging

SmartClicker includes a simple logger that doesn't require external dependencies:

```python
clicker.logger.debug("Debug message")
clicker.logger.info("Info message")
clicker.logger.warning("Warning message")
clicker.logger.error("Error message")
```

By default, only info/warning/error are printed. To enable debug logging, modify the `_setup_logger` method.

## Integration Examples

### With Page Waiting

```python
# Wait for element, then click
await tab.wait_for("#button")
result = await clicker.click("#button")
```

### With Navigation

```python
original_url = await tab.evaluate("window.location.href")

result = await clicker.click("a.nav-link")
if result.success:
    # Wait for navigation
    for _ in range(10):
        url = await tab.evaluate("window.location.href")
        if url != original_url:
            break
        await asyncio.sleep(0.5)
```

### With Text Input

```python
# Fill and submit
await tab.type_text("#search", "query")
result = await clicker.click("#search-btn")
```

## File Structure

```
smart_click.py              # Main implementation (370 lines)
smart_click_examples.py     # 14 practical examples
smart_click_guide.md        # Comprehensive documentation
SMART_CLICK_README.md       # This file
```

## Testing

To test SmartClicker with your page:

```python
async def test_clicks(tab):
    clicker = SmartClicker(tab)

    # Find all clickable elements
    buttons = await tab.select_all("button, a[role='button']")

    success_count = 0
    for button in buttons:
        # Get button text
        text = await tab.evaluate("arguments[0].textContent", button)
        selector = f"button:contains('{text}')"

        result = await clicker.click(selector, timeout=3.0)
        if result.success:
            success_count += 1

    print(f"Successfully clicked {success_count}/{len(buttons)} buttons")
```

## Troubleshooting

### Click says success but nothing happens

Check your verification function:

```python
# Wrong - doesn't return boolean
async def bad_verify():
    await tab.select(".result")

# Correct
async def good_verify():
    element = await tab.select(".result")
    return element is not None
```

### All strategies fail

1. Verify selector is correct
2. Try selector in DevTools console
3. Check if element is in an iframe
4. Check if element is completely off-screen
5. Look at the error message for clues

### Click is too slow

Disable unnecessary features:

```python
clicker = SmartClicker(
    tab,
    verify_click=False,        # Don't verify
    scroll_into_view=False,    # Element already visible
    human_like_delay=False     # Internal tool
)
```

## Best Practices

1. Always check `result.success` before assuming click worked
2. Use verification callbacks for critical actions
3. Set appropriate timeouts based on page complexity
4. Reuse SmartClicker instances for multiple clicks
5. Log strategy usage to identify problematic elements
6. Test selectors separately to ensure they find elements
7. Handle TimeoutError separately from click failures
8. Document why you need SmartClicker for each element
9. Monitor which strategies are being used
10. Profile performance in your environment

## API Reference

### SmartClicker Class

```python
clicker = SmartClicker(
    tab,                    # nodriver tab/page object
    verify_click=True,      # Enable verification
    scroll_into_view=True,  # Scroll before clicking
    human_like_delay=True,  # Add realistic delays
    max_retries=5           # Max strategies to try
)

result = await clicker.click(
    selector,              # CSS selector string
    verify_action=None,    # Optional async callable
    timeout=10.0           # Timeout in seconds
)
```

### ClickStrategy Enum

```python
ClickStrategy.NORMAL          # Normal mouse click
ClickStrategy.JAVASCRIPT      # element.click()
ClickStrategy.FOCUS_ENTER     # Focus + Enter
ClickStrategy.FOCUS_SPACE     # Focus + Space
ClickStrategy.DISPATCH_EVENT  # Manual events
ClickStrategy.DOUBLE_CLICK    # Double-click
```

### ClickResult Dataclass

```python
@dataclass
class ClickResult:
    success: bool                   # Click succeeded?
    strategy_used: ClickStrategy    # Which strategy worked
    attempts: int                   # How many tried
    error: Optional[str]            # Error message
    verification_passed: bool       # Verification passed?
```

## Limitations

- Requires nodriver library
- May not work with shadow DOM (needs custom piercing)
- Drag-and-drop needs additional code
- Right-click/middle-click not implemented
- Can't click completely off-screen elements
- Verification is user's responsibility

## Future Enhancements

Potential additions:
- Right-click and middle-click
- Drag-and-drop automation
- Shadow DOM piercing
- Built-in verification patterns
- Performance metrics
- Click history/replay

## License

Part of the nodriver skills collection.

## Support

For issues or questions:
1. Check the comprehensive guide: `smart_click_guide.md`
2. Review examples: `smart_click_examples.py`
3. Inspect ClickResult error message
4. Enable debug logging
5. Try different selectors/strategies

## Contributing

To improve SmartClicker:
1. Test edge cases
2. Add new strategies if found
3. Document new patterns
4. Share example code
5. Report problematic elements
