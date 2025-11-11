# Human Behavior Patterns - Comprehensive Guide

## Overview

The `human_behavior.py` module provides sophisticated utilities for simulating realistic human interaction patterns with web browsers. This makes automation appear more natural while remaining completely within terms of service.

All patterns are designed for legitimate use cases:
- Natural browsing and content reading
- Normal user interaction patterns
- Realistic timing and decision-making
- Common task completion behaviors

## Table of Contents

1. [Quick Start](#quick-start)
2. [Core Components](#core-components)
3. [Delay Patterns](#delay-patterns)
4. [Mouse Movement](#mouse-movement)
5. [Scrolling Behavior](#scrolling-behavior)
6. [Typing Rhythm](#typing-rhythm)
7. [Interaction Patterns](#interaction-patterns)
8. [Configuration](#configuration)
9. [Examples](#examples)

## Quick Start

### Basic Usage

```python
import asyncio
from human_behavior import HumanBehavior, BehaviorConfig
from quick_start import create_browser

async def main():
    browser = await create_browser()
    behavior = HumanBehavior()

    try:
        page = await browser.get("https://example.com")

        # Read page naturally
        await behavior.read_page(page, reading_speed="normal")

        # Scroll through page
        await behavior.scroll_naturally(page)

    finally:
        await browser.aclose()

asyncio.run(main())
```

## Core Components

### 1. DelayGenerator

Generates random delays with natural (non-uniform) distributions that match real human behavior.

#### Exponential Delay
Short pauses are common, long pauses are rare - mimics human reaction times.

```python
from human_behavior import DelayGenerator

gen = DelayGenerator()

# Most delays will be short, occasional longer ones
delay = gen.exponential_delay(base=0.1, max_delay=2.0)
await asyncio.sleep(delay)
```

**When to use:** Natural pauses between actions, thinking time, page assessment.

#### Gaussian Delay
Delays cluster around a mean with realistic variance.

```python
# Most delays ~0.3s, some up to 1.0s
delay = gen.gaussian_delay(mean=0.3, std_dev=0.1)
await asyncio.sleep(delay)
```

**When to use:** Consistent but variable timing, like menu navigation or button clicking.

#### Between-Keys Delay
Simulates realistic typing speed based on WPM.

```python
# Simulate 60 WPM typing with natural variance
delay = gen.between_keys_delay(base_speed=60)
# This accounts for:
# - Different character difficulties (symbols vs letters)
# - Hand position changes
# - Natural typing rhythm variation
```

**When to use:** Before implementing character-by-character typing.

#### Blink Pause
Natural 200-400ms pause (like a human blink).

```python
# Realistic blink duration
await behavior.blink_pause()
```

**When to use:** Natural breaks in activity, attention shifts.

#### Thinking Pause
Variable-length pause based on content complexity.

```python
# Quick thought: complexity=0.5
await gen.thinking_pause(complexity=0.5)

# Complex decision: complexity=2.0
await gen.thinking_pause(complexity=2.0)
```

**When to use:** Before making decisions, reading complex content, form submission.

### 2. MouseMovement

Generates realistic mouse movement paths using mathematical curves.

#### Quadratic Bezier Curves
Smooth curved paths with one control point.

```python
from human_behavior import MouseMovement

start = (100, 100)
end = (500, 200)

# Generate smooth curve path
path = MouseMovement.quadratic_bezier(
    start=start,
    end=end,
    steps=20  # More steps = smoother curve
)

# Path is list of (x, y) tuples
for x, y in path:
    # Move mouse to (x, y)
    pass
```

**Characteristics:**
- Natural curved movement
- Single control point creates smooth arc
- Good for simple movements

#### Cubic Bezier Curves
More complex curves with two control points, allowing S-shaped paths.

```python
# Generate more complex curved path
path = MouseMovement.cubic_bezier(
    start=(100, 100),
    end=(500, 200),
    steps=30
)
```

**Characteristics:**
- More natural, complex paths
- S-shaped curves possible
- Better for longer movements
- More CPU intensive (generates more points)

#### Jittered Path
Smooth path with hand tremor/jitter added.

```python
# Smooth path with slight imprecision
path = MouseMovement.jittered_path(
    start=(100, 100),
    end=(500, 200),
    jitter_amount=0.3,  # 0-1, higher = more jitter
)
```

**Why jitter matters:**
- Perfect precision is suspicious (robotic)
- Humans have natural hand tremor
- Adds realism without looking broken

### 3. ScrollingBehavior

Simulates realistic scrolling patterns.

#### Scroll Increments
Generate variable-speed scroll movements with optional pauses.

```python
from human_behavior import ScrollingBehavior

scroll = ScrollingBehavior()

# Get natural scroll increments for smooth scrolling
increments = scroll.scroll_increments(
    total_scroll=1000,  # pixels to scroll
    smoothness=0.8,     # 0.1-1.0, higher = smoother
    include_pauses=True # Add reading pauses
)

# Use increments for smooth scrolling
for increment in increments:
    if increment > 0:
        # Scroll
        await page.evaluate(f"window.scrollBy(0, {increment})")
    else:
        # Pause while reading
        await asyncio.sleep(2.0)
```

#### Dwell Time
Calculate realistic reading pause duration.

```python
# How long to pause after scrolling
dwell = scroll.dwell_time_for_scroll(
    scroll_amount=300,      # pixels scrolled
    reading_speed=1.0       # 0.5-2.0 multiplier
)
await asyncio.sleep(dwell)
```

**Calculation basis:**
- ~250 words per screen
- ~240 pixels per screen
- ~200 WPM average reading speed

### 4. TypingRhythm

Simulates realistic typing patterns with rhythm variations.

#### Keystroke Delays
Generate variable delays between keystrokes.

```python
from human_behavior import TypingRhythm

typing = TypingRhythm()

# Get realistic delays for each keystroke
delays = typing.keystroke_delays(
    text="Hello World",
    base_speed=60,      # WPM
    variance=0.3        # 30% variance
)

# Type with natural rhythm
for char, delay in zip(text, delays):
    await element.type(char)
    await asyncio.sleep(delay)
```

**Features:**
- Numbers and symbols: slower
- Capitals: slightly slower
- Occasional pauses (correction simulation)
- Realistic WPM-based calculation

## Configuration

### BehaviorConfig

Fine-tune automation behavior with configuration.

```python
from human_behavior import BehaviorConfig, InteractionStyle

config = BehaviorConfig(
    reading_speed=1.0,                    # 0.5-2.0 multiplier
    interaction_style=InteractionStyle.NORMAL,  # MINIMAL, CAUTIOUS, NORMAL, ENGAGED
    mouse_speed=1.0,                      # 0.1-2.0 multiplier
    scroll_smoothness=0.8,                # 0.1-1.0
    typing_rhythm_variance=0.3,           # 0.1-1.0
    pause_probability=0.2,                # 0-1, chance of pause
    hover_probability=0.3,                # 0-1, chance of hover
)

behavior = HumanBehavior(config)
```

### Interaction Styles

Different patterns for different scenarios:

| Style | Use Case | Characteristics |
|-------|----------|-----------------|
| **MINIMAL** | Silent monitoring | Few actions, minimal interaction |
| **CAUTIOUS** | Limited interaction | Careful, deliberate movements |
| **NORMAL** | General use | Natural, typical behavior |
| **ENGAGED** | Active participation | Frequent interaction, exploring |

## Examples

### Example 1: Read a Page Naturally

```python
async def read_article():
    browser = await create_browser()
    behavior = HumanBehavior()

    try:
        page = await browser.get("https://example.com/article")

        # Read with normal pace
        await behavior.read_page(
            page,
            reading_speed="normal",
            include_scrolling=True
        )

    finally:
        await browser.aclose()
```

### Example 2: Form Filling with Natural Timing

```python
async def fill_form_naturally():
    from safe_type import SafeTyper

    browser = await create_browser()
    behavior = HumanBehavior(
        BehaviorConfig(
            typing_rhythm_variance=0.4,  # More variation
            pause_probability=0.15,      # Occasional pauses
        )
    )
    typer = SafeTyper(page)

    try:
        page = await browser.get("https://example.com/form")

        # Name field
        await behavior.hover_element(await page.find("#name"))
        await behavior.type_with_rhythm(
            await page.find("#name"),
            "John Doe",
            base_speed=60
        )

        # Pause between fields
        await behavior.thinking_pause(complexity=0.5)

        # Email field
        await behavior.type_with_rhythm(
            await page.find("#email"),
            "john@example.com",
            base_speed=70
        )

        # Think before submitting
        await behavior.thinking_pause(complexity=1.0)

        # Submit
        await (await page.find("#submit")).click()

    finally:
        await browser.aclose()
```

### Example 3: Exploration Session

```python
async def explore_site():
    browser = await create_browser()
    behavior = HumanBehavior(
        BehaviorConfig(
            interaction_style=InteractionStyle.ENGAGED,
            hover_probability=0.4
        )
    )

    try:
        page = await browser.get("https://example.com")

        # Varied interaction for ~2 minutes
        await behavior.varied_interaction_session(page, duration=120.0)

    finally:
        await browser.aclose()
```

### Example 4: Cautious Navigation

```python
async def browse_carefully():
    browser = await create_browser()
    behavior = HumanBehavior(
        BehaviorConfig(
            reading_speed=1.5,  # Slow reading
            interaction_style=InteractionStyle.CAUTIOUS,
            pause_probability=0.3  # Frequent pauses
        )
    )

    try:
        page = await browser.get("https://example.com")

        # Careful reading and minimal interaction
        await behavior.read_page(page, reading_speed="slow")
        await behavior.scroll_naturally(page, smoothness=0.6)

    finally:
        await browser.aclose()
```

## Advanced Patterns

### Custom Delay Chain

```python
async def perform_action_sequence():
    behavior = HumanBehavior()

    # Initial assessment
    await behavior.blink_pause()

    # Decide what to do
    await behavior.thinking_pause(complexity=0.8)

    # Random pause before acting
    await behavior.random_delay(0.5, 2.0)

    # Act
    # ... perform action ...

    # Pause after action
    await behavior.random_delay(0.1, 0.5)
```

### Interaction with Elements

```python
async def interact_with_elements():
    behavior = HumanBehavior(
        BehaviorConfig(hover_probability=0.5)
    )

    try:
        # Find all buttons
        buttons = await page.find_all("button")

        for button in buttons:
            # Hover before clicking
            await behavior.hover_element(button, duration=1.0)

            # Focus and interact
            await behavior.focus_and_interact(button)

            # Pause between interactions
            await behavior.random_delay(1.0, 3.0)

    except Exception as e:
        print(f"Error: {e}")
```

## Best Practices

### 1. **Match Use Case to Style**
```python
# Monitoring a status page - be minimal
config = BehaviorConfig(interaction_style=InteractionStyle.MINIMAL)

# Exploring a site - be engaged
config = BehaviorConfig(interaction_style=InteractionStyle.ENGAGED)
```

### 2. **Use Appropriate Reading Speeds**
```python
# News article - normal speed
await behavior.read_page(page, reading_speed="normal")

# Legal document - slow speed
await behavior.read_page(page, reading_speed="slow")

# Quick link check - fast speed
await behavior.read_page(page, reading_speed="fast")
```

### 3. **Combine Behaviors Naturally**
```python
# Don't just random_delay, use thinking_pause for decisions
await behavior.thinking_pause()  # Better than random_delay

# Hover before focusing on elements
await behavior.hover_element(elem)
await behavior.focus_and_interact(elem)

# Read before scrolling
await behavior.read_page(page)
await behavior.scroll_naturally(page)
```

### 4. **Context-Appropriate Pauses**
```python
# Before making a decision
await behavior.thinking_pause(complexity=1.5)

# Between unrelated actions
await behavior.random_delay(1.0, 3.0)

# After scrolling (reading)
dwell = scroll.dwell_time_for_scroll(300)
await asyncio.sleep(dwell)
```

## Performance Considerations

- **Bezier curves**: More realistic but slightly slower
  - Quadratic: ~5-10 points per curve
  - Cubic: ~20-30 points per curve

- **Distributions**: Exponential is faster than Gaussian

- **Scrolling**: Smoother scrolling (higher smoothness) generates more events

- **Typing**: Character-by-character is slower than bulk input but more realistic

## Integration with Other Modules

### With SafeTyper

```python
from safe_type import SafeTyper
from human_behavior import HumanBehavior

typer = SafeTyper(page)
behavior = HumanBehavior()

# Combine for natural typing
await behavior.hover_element(input_field)
await behavior.typing.keystroke_delays("test", base_speed=60)
await typer.type_in_field("#input", "test")
```

### With SmartClick

```python
from smart_click import SmartClick
from human_behavior import HumanBehavior

smart_click = SmartClick(page)
behavior = HumanBehavior()

# Natural interaction pattern
await behavior.hover_element(button)
await behavior.random_delay(0.5, 1.0)
await smart_click.click("#button")
```

## Troubleshooting

### Issue: Automation Still Looks Too Robotic

**Solution:** Increase variance and add more pauses
```python
config = BehaviorConfig(
    typing_rhythm_variance=0.5,  # Increased from 0.3
    pause_probability=0.3,        # Increased from 0.2
    hover_probability=0.4,        # Increased from 0.3
)
```

### Issue: Automation is Too Slow

**Solution:** Adjust reading_speed and scroll_smoothness
```python
config = BehaviorConfig(
    reading_speed=0.7,           # Faster reading
    scroll_smoothness=0.6,       # Less smooth = faster
)
```

### Issue: Elements Not Responding to Hover

**Solution:** Reduce hover_probability or use focus_and_interact instead
```python
# Instead of hover alone
await behavior.focus_and_interact(element)
```

## Ethical Considerations

This module is designed for legitimate use cases only:

✓ **Legitimate uses:**
- Testing your own applications
- Monitoring publicly accessible content you have permission to access
- Natural-looking automation of repetitive tasks you perform manually
- Bot detection testing with permission

✗ **Do not use for:**
- Circumventing rate limiting or access controls
- Impersonating humans to violate terms of service
- Scraping content without permission
- Automating unauthorized access

Always ensure you have permission to automate interactions with any website.

## See Also

- `safe_type.py` - Reliable text input
- `smart_click.py` - Intelligent element clicking
- `quick_start.py` - Browser initialization
