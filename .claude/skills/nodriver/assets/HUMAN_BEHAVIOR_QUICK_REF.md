# Human Behavior - Quick Reference

## Import

```python
from human_behavior import (
    HumanBehavior,
    BehaviorConfig,
    ReadingSpeed,
    InteractionStyle,
    DelayGenerator,
    MouseMovement,
    ScrollingBehavior,
    TypingRhythm,
    InteractionPatterns,
)
```

## Basic Setup

```python
# Default behavior
behavior = HumanBehavior()

# Custom configuration
config = BehaviorConfig(
    reading_speed=1.0,
    interaction_style=InteractionStyle.NORMAL,
    scroll_smoothness=0.8,
)
behavior = HumanBehavior(config)
```

## Delays (Most Common)

| Function | Use Case | Example |
|----------|----------|---------|
| `random_delay()` | General pause | `await behavior.random_delay(0.5, 2.0)` |
| `thinking_pause()` | Before decision | `await behavior.thinking_pause(1.0)` |
| `blink_pause()` | Natural break | `await behavior.blink_pause()` |

## Page Interaction

```python
# Read page naturally
await behavior.read_page(page, reading_speed="normal")

# Scroll with pauses
await behavior.scroll_naturally(page)

# Hover element
await behavior.hover_element(element, duration=1.0)

# Focus and interact
await behavior.focus_and_interact(element)

# Type naturally
await behavior.type_with_rhythm(element, "text", base_speed=60)

# Full session
await behavior.varied_interaction_session(page, duration=30.0)
```

## Delays (Advanced)

```python
# Exponential (many short, few long)
delay = behavior.delay_gen.exponential_delay(0.1, 2.0)

# Gaussian (clustered around mean)
delay = behavior.delay_gen.gaussian_delay(0.3, 0.1)

# Between keystrokes
delay = behavior.delay_gen.between_keys_delay(base_speed=60)

# Thinking pause
delay = behavior.delay_gen.thinking_pause(complexity=1.0)
```

## Mouse Movement

```python
# Quadratic Bezier (smooth curve)
path = behavior.mouse.quadratic_bezier((0, 0), (100, 100), steps=20)

# Cubic Bezier (complex curves)
path = behavior.mouse.cubic_bezier((0, 0), (100, 100), steps=30)

# With hand tremor
path = behavior.mouse.jittered_path((0, 0), (100, 100), jitter_amount=0.3)
```

## Scrolling

```python
# Natural scroll increments
increments = behavior.scroll.scroll_increments(1000, smoothness=0.8)

# Reading pause duration
dwell = behavior.scroll.dwell_time_for_scroll(300, reading_speed=1.0)
```

## Typing

```python
# Keystroke delays with rhythm
delays = behavior.typing.keystroke_delays("text", base_speed=60, variance=0.3)

# Potential typo positions
errors = behavior.typing.has_typos("text", error_rate=0.02)
```

## Interaction Styles

```python
# Minimal interaction
InteractionStyle.MINIMAL

# Careful, deliberate
InteractionStyle.CAUTIOUS

# Natural behavior
InteractionStyle.NORMAL

# Frequent exploration
InteractionStyle.ENGAGED
```

## Reading Speeds

```python
# Quick skim (0.5x)
ReadingSpeed.FAST

# Normal reading (1.0x)
ReadingSpeed.NORMAL

# Careful reading (1.5x)
ReadingSpeed.SLOW

# Very careful/complex (2.0x)
ReadingSpeed.VERY_SLOW
```

## Common Patterns

### Natural Form Filling

```python
# Hover over field
await behavior.hover_element(field, 0.5)

# Focus and type naturally
await behavior.type_with_rhythm(field, "data", base_speed=60)

# Pause between fields
await behavior.thinking_pause(0.5)

# Submit
await button.click()
```

### Reading Session

```python
# Read page
await behavior.read_page(page, reading_speed="normal")

# Maybe scroll more
await behavior.scroll_naturally(page)

# Random pause
await behavior.random_delay(1.0, 3.0)
```

### Exploration

```python
# Extended varied interaction
await behavior.varied_interaction_session(page, duration=120.0)
```

## Configuration Presets

### Fast Scanning
```python
BehaviorConfig(
    reading_speed=0.5,
    interaction_style=InteractionStyle.MINIMAL,
    scroll_smoothness=0.5,
)
```

### Normal Browsing
```python
BehaviorConfig(
    reading_speed=1.0,
    interaction_style=InteractionStyle.NORMAL,
    scroll_smoothness=0.8,
)
```

### Careful Reading
```python
BehaviorConfig(
    reading_speed=1.5,
    interaction_style=InteractionStyle.CAUTIOUS,
    scroll_smoothness=0.9,
    pause_probability=0.3,
)
```

### Active Exploration
```python
BehaviorConfig(
    reading_speed=1.0,
    interaction_style=InteractionStyle.ENGAGED,
    hover_probability=0.5,
    pause_probability=0.15,
)
```

## Performance Tips

- Use `exponential_delay()` for realistic pauses
- Higher `scroll_smoothness` = more CPU, more realistic
- Combine behaviors (don't just use `random_delay()` everywhere)
- Match `reading_speed` to content type
- Use `interaction_style` to control overall behavior intensity

## Troubleshooting

| Problem | Solution |
|---------|----------|
| Too robotic | Increase variance, add more pauses |
| Too slow | Lower reading_speed, scroll_smoothness |
| Too much hovering | Lower hover_probability |
| Elements not responding | Use focus_and_interact() |

## Methods Summary

### HumanBehavior
- `random_delay(min, max)` - Random pause
- `thinking_pause(complexity)` - Decision pause
- `blink_pause()` - Natural break
- `read_page(page, speed)` - Read naturally
- `scroll_naturally(page)` - Smooth scroll
- `hover_element(elem, duration)` - Hover
- `focus_and_interact(elem)` - Focus element
- `type_with_rhythm(elem, text, speed)` - Type naturally
- `switch_tabs(browser, count)` - Tab switching
- `varied_interaction_session(page, duration)` - Full session

### DelayGenerator
- `exponential_delay()` - Natural pauses
- `gaussian_delay()` - Clustered delays
- `between_keys_delay()` - Typing timing
- `blink_delay()` - Blink pause
- `thinking_pause()` - Decision pause

### MouseMovement
- `quadratic_bezier()` - Simple curves
- `cubic_bezier()` - Complex curves
- `jittered_path()` - With hand tremor

### ScrollingBehavior
- `scroll_increments()` - Variable speed scrolling
- `dwell_time_for_scroll()` - Reading pause

### TypingRhythm
- `keystroke_delays()` - Keystroke timing
- `has_typos()` - Typo positions
