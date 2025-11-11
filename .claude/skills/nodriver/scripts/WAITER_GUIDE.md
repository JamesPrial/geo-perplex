# ElementWaiter - Advanced Wait Strategies Guide

## Overview

The `ElementWaiter` module provides intelligent waiting mechanisms for reliable browser automation with nodriver. Instead of using simple fixed timeouts, it implements sophisticated condition-based waiting that makes automation more robust and responsive.

## Why Advanced Waiting Matters

Simple timeouts are unreliable:
- Too short: Tests fail sporadically on slow networks
- Too long: Tests take unnecessarily long on fast networks
- No feedback: You don't know what the code is actually waiting for

Advanced waiting strategies:
- Wait for specific conditions (not just time)
- Adapt to varying network speeds
- Provide detailed information about wait results
- Support complex multi-condition scenarios
- Fail fast when conditions can't be met

## Core Components

### 1. WaitResult - Standard Return Type

Every wait operation returns a `WaitResult` object:

```python
@dataclass
class WaitResult:
    success: bool              # Did the condition meet?
    element: Optional[Any]     # The element (if found)
    wait_time: float          # How long we waited (seconds)
    condition_type: WaitConditionType  # Type of condition
    error: Optional[str]      # Error message if failed
    attempts: int             # Number of poll attempts
```

Example usage:
```python
result = await waiter.wait_for_clickable("#button", timeout=10)
if result.success:
    print(f"Ready after {result.wait_time:.2f}s")
    await result.element.click()
else:
    print(f"Failed: {result.error}")
```

### 2. WaitCondition Classes - Building Blocks

Base class for all conditions:

```python
class WaitCondition(ABC):
    async def check(self, tab: Any) -> bool:
        """Check if condition is met."""
    def describe(self) -> str:
        """Human-readable description."""
```

**Built-in condition types:**

- `PresenceCondition` - Element exists in DOM
- `VisibilityCondition` - Element is visible in viewport
- `ClickableCondition` - Element is clickable (comprehensive checks)
- `TextPresentCondition` - Text appears in element
- `AttributeValueCondition` - Attribute has specific value
- `JavaScriptCondition` - Custom JavaScript returns true
- `NetworkIdleCondition` - No pending network requests
- `CompoundCondition` - Combine conditions with AND/OR logic

### 3. ElementWaiter - Main Class

The primary interface for waiting operations:

```python
waiter = ElementWaiter(
    tab,                    # nodriver tab object
    poll_interval=0.1,      # Check interval (seconds)
    verbose=False           # Enable debug logging
)
```

## Wait Methods

### Basic Waits

#### 1. Wait for Presence

```python
result = await waiter.wait_for_presence(selector, timeout=10)
# Element exists in DOM (may not be visible)
```

#### 2. Wait for Visibility

```python
result = await waiter.wait_for_visible(selector, timeout=10)
# Element is visible in viewport with non-zero dimensions
```

#### 3. Wait for Clickability

```python
result = await waiter.wait_for_clickable(selector, timeout=10)
# Element is:
# - Visible
# - Enabled (not disabled)
# - In viewport
# - Not covered by other elements
# - Has pointer-events enabled
```

### Content Waits

#### 4. Wait for Text

```python
# Partial match (substring)
result = await waiter.wait_for_text(
    selector="#message",
    text="Success",
    partial=True,
    timeout=10
)

# Exact match
result = await waiter.wait_for_text(
    selector="#counter",
    text="100",
    partial=False,
    timeout=10
)
```

#### 5. Wait for Attribute

```python
result = await waiter.wait_for_attribute(
    selector="#button",
    attribute="data-ready",
    value="true",
    timeout=10
)
```

### Advanced Waits

#### 6. Wait for JavaScript Condition

Execute arbitrary JavaScript and wait for it to return true:

```python
# Page load state
result = await waiter.wait_for_javascript(
    "return document.readyState === 'complete'",
    timeout=10
)

# Application state
result = await waiter.wait_for_javascript(
    """
    const app = window.__appState;
    return app && app.isReady && app.data.length > 0;
    """,
    timeout=10
)

# DOM state
result = await waiter.wait_for_javascript(
    "return !document.body.classList.contains('loading')",
    timeout=10
)
```

#### 7. Wait for Network Idle

```python
result = await waiter.wait_for_network_idle(
    timeout=10,
    strategy=NetworkIdleStrategy.NO_REQUESTS
)
```

### Compound Conditions

#### 8. Wait for ALL Conditions (AND Logic)

```python
conditions = [
    VisibilityCondition("#button"),
    TextPresentCondition("#label", "Click Me"),
    AttributeValueCondition("#button", "data-enabled", "true")
]

result = await waiter.wait_for_all(conditions, timeout=10)
# All three conditions must be true
```

#### 9. Wait for ANY Condition (OR Logic)

```python
conditions = [
    TextPresentCondition("#error", "Error", partial=True),
    TextPresentCondition("#success", "Success"),
    JavaScriptCondition("return window.done === true")
]

result = await waiter.wait_for_any(conditions, timeout=10)
# At least one condition must be true
```

#### 10. Custom Async Conditions

```python
async def all_rows_loaded(tab):
    """Custom condition function."""
    try:
        rows = await tab.select_all("table tbody tr")
        return len(rows) >= 5
    except Exception:
        return False

result = await waiter.wait_for_custom(all_rows_loaded, timeout=10)
```

## Convenience Functions

For quick, simple operations:

```python
# Wait and get element
element = await wait_for_element(tab, "#button", timeout=10)

# Wait for visibility
element = await wait_for_visible(tab, "#modal", timeout=10)

# Wait for clickability
element = await wait_for_clickable(tab, "#submit", timeout=10)

# Wait for text
success = await wait_for_text(
    tab, "#message", "Done", timeout=10
)
```

## Practical Patterns

### Pattern 1: Safe Element Interaction

```python
result = await waiter.wait_for_clickable("#submit", timeout=10)
if result.success:
    await result.element.click()
    print(f"Clicked after {result.wait_time:.2f}s")
else:
    raise TimeoutError(f"Submit button not clickable: {result.error}")
```

### Pattern 2: Multi-Step Workflow

```python
waiter = ElementWaiter(tab)

# Step 1: Wait for form
if not (await waiter.wait_for_visible("#login-form")).success:
    raise TimeoutError("Form not visible")

# Step 2: Wait for field and fill
if (await waiter.wait_for_clickable("#email")).success:
    await waiter.wait_for_text("#email", "user@example.com")

# Step 3: Wait for success or error
conditions = [
    TextPresentCondition("#success", "Success"),
    TextPresentCondition("#error", "Error", partial=True)
]
result = await waiter.wait_for_any(conditions, timeout=10)
```

### Pattern 3: Retry with Backoff

```python
async def robust_operation():
    """Retry operation with exponential backoff."""
    waiter = ElementWaiter(tab, poll_interval=0.05)  # Fast polling

    for attempt in range(3):
        try:
            result = await waiter.wait_for_clickable(
                "#button",
                timeout=5
            )
            if result.success:
                return result.element
        except Exception as e:
            if attempt < 2:
                await asyncio.sleep(2 ** attempt)
            else:
                raise

    return None
```

### Pattern 4: Conditional Waiting

```python
# Wait for either success or error message
conditions = [
    TextPresentCondition("#success", "Uploaded", partial=True),
    TextPresentCondition("#error", "Failed", partial=True),
    JavaScriptCondition("return window.uploadComplete")
]

result = await waiter.wait_for_any(conditions, timeout=30)

if result.success:
    # Check which condition was met
    status_elem = await tab.find("#success")
    if status_elem:
        print("Upload successful")
    else:
        print("Upload failed")
```

## Performance Tuning

### Poll Interval

```python
# Fast polling (50ms) - responsive but more CPU
waiter_fast = ElementWaiter(tab, poll_interval=0.05)

# Slow polling (500ms) - less responsive but lower CPU
waiter_slow = ElementWaiter(tab, poll_interval=0.5)

# Default (100ms) - good balance
waiter = ElementWaiter(tab, poll_interval=0.1)
```

### Timeout Selection

```python
# Quick checks (page already ready)
result = await waiter.wait_for_visible("#content", timeout=2)

# Normal operations (API call, animation)
result = await waiter.wait_for_clickable("#button", timeout=10)

# Long operations (file upload, processing)
result = await waiter.wait_for_text("#status", "Complete", timeout=60)
```

## Error Handling

```python
result = await waiter.wait_for_clickable("#submit", timeout=10)

if not result.success:
    # Access detailed error information
    print(f"Error: {result.error}")
    print(f"Attempts: {result.attempts}")
    print(f"Wait time: {result.wait_time:.2f}s")
    print(f"Condition: {result.condition_type}")

    # Handle different failure reasons
    if result.wait_time >= 10:
        print("Timeout reached")
    elif result.attempts < 5:
        print("Condition never checked enough times")
    else:
        print("Condition never met despite multiple checks")
```

## Advanced Condition Construction

### Complex JavaScript

```python
# Check multiple application states
result = await waiter.wait_for_javascript("""
    return (
        window.app &&
        window.app.initialized &&
        window.app.data.loaded &&
        document.readyState === 'complete' &&
        !document.body.classList.contains('loading')
    )
""", timeout=10)
```

### Chained Conditions

```python
# Condition 1: Wait for form to appear
result1 = await waiter.wait_for_visible("#form", timeout=5)

# Condition 2: Wait for specific field
if result1.success:
    result2 = await waiter.wait_for_attribute(
        "#form",
        "data-ready",
        "true",
        timeout=5
    )

# Condition 3: All good - proceed
if result2.success:
    result3 = await waiter.wait_for_clickable("#submit", timeout=5)
```

## Comparison with Alternatives

### vs. Fixed Timeout

```python
# Bad: Fixed timeout
await asyncio.sleep(5)  # May be too short or too long
await element.click()

# Good: Condition-based
result = await waiter.wait_for_clickable("#button", timeout=10)
if result.success:
    await element.click()
```

### vs. Multiple Retries

```python
# Inefficient: Many retries with sleeps
for i in range(10):
    try:
        element = await tab.find("#button")
        if element.is_visible():
            break
    except Exception:
        pass
    await asyncio.sleep(1)  # 10 second total wait if fails

# Efficient: Single wait operation
result = await waiter.wait_for_visible("#button", timeout=10)
```

## Troubleshooting

### Wait is Timing Out

1. Check if element selector is correct
2. Increase timeout if operation takes longer
3. Enable verbose mode to see polling activity
4. Check JavaScript console for errors
5. Verify element is not inside iframe

### Wait Completes Too Quickly

1. Use stricter conditions (e.g., `wait_for_clickable` instead of `wait_for_visible`)
2. Add additional compound conditions
3. Use JavaScript conditions to check application state

### High CPU Usage

1. Increase `poll_interval` (e.g., 0.5 seconds)
2. Use more efficient conditions
3. Set appropriate timeouts to avoid long waits

## Summary

ElementWaiter provides:

1. **Multiple wait strategies** - Presence, visibility, clickability, content, attributes, JavaScript, network
2. **Compound logic** - AND/OR combinations of conditions
3. **Detailed results** - Success, time, attempts, element, errors
4. **Performance tuning** - Adjustable polling intervals and timeouts
5. **Clean API** - Simple methods with sensible defaults
6. **Robust error handling** - Detailed error information
7. **Flexible extensibility** - Custom conditions and JavaScript evaluation

Use these patterns to build reliable, responsive automation that adapts to varying network speeds and application behavior.
