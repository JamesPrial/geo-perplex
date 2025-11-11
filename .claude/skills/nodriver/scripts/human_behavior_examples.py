#!/usr/bin/env python3
"""
Practical examples demonstrating HumanBehavior module usage.

This script shows real-world applications of the human behavior patterns,
including form filling, content reading, and natural browsing simulation.
"""

import asyncio
from human_behavior import (
    HumanBehavior,
    BehaviorConfig,
    ReadingSpeed,
    InteractionStyle,
)


async def example_1_read_article():
    """
    Example 1: Reading an article naturally.

    Demonstrates how to simulate reading a long-form content page
    with natural pauses and scrolling.
    """
    print("\n" + "=" * 60)
    print("Example 1: Reading Article Naturally")
    print("=" * 60)

    try:
        from quick_start import create_browser
    except ImportError:
        print("Error: quick_start module not found")
        return

    browser = await create_browser()
    behavior = HumanBehavior()

    try:
        # Navigate to article
        page = await browser.get("https://example.com")
        print("Opened article page")

        # Read the article with natural timing
        await behavior.read_page(page, reading_speed="normal")
        print("Reading complete")

    except Exception as e:
        print(f"Error: {e}")
    finally:
        await browser.aclose()


async def example_2_form_filling():
    """
    Example 2: Filling a form with natural timing.

    Shows how to interact with form fields using realistic typing
    patterns and pauses between fields.
    """
    print("\n" + "=" * 60)
    print("Example 2: Natural Form Filling")
    print("=" * 60)

    try:
        from quick_start import create_browser
        from safe_type import SafeTyper
    except ImportError:
        print("Error: Required modules not found")
        return

    browser = await create_browser()
    behavior = HumanBehavior()
    typer = SafeTyper(browser.current_page)

    try:
        page = await browser.get("https://example.com/form")
        print("Opened form page")

        # Simulate field names
        form_fields = [
            ("#name", "John Doe", 60),  # (selector, value, typing_speed)
            ("#email", "john@example.com", 70),
            ("#message", "This is a test message", 55),
        ]

        for selector, value, speed in form_fields:
            print(f"\nFilling {selector}...")

            try:
                # Find element
                element = await page.find(selector)
                if not element:
                    print(f"  Element not found: {selector}")
                    continue

                # Hover over field
                await behavior.hover_element(element, duration=0.5)
                print(f"  Hovered over element")

                # Type with natural rhythm
                await behavior.type_with_rhythm(element, value, base_speed=speed)
                print(f"  Typed: {value}")

                # Pause between fields
                await behavior.thinking_pause(complexity=0.3)
                print(f"  Paused before next field")

            except Exception as e:
                print(f"  Error: {e}")

        print("\nForm filling complete")

    except Exception as e:
        print(f"Error: {e}")
    finally:
        await browser.aclose()


async def example_3_exploration_session():
    """
    Example 3: Exploring a website with varied interactions.

    Demonstrates creating a realistic browsing session with
    multiple types of interactions over an extended period.
    """
    print("\n" + "=" * 60)
    print("Example 3: Website Exploration Session")
    print("=" * 60)

    try:
        from quick_start import create_browser
    except ImportError:
        print("Error: quick_start module not found")
        return

    browser = await create_browser()

    # Engaged exploration style
    config = BehaviorConfig(
        interaction_style=InteractionStyle.ENGAGED,
        hover_probability=0.4,
        reading_speed=1.0,
    )
    behavior = HumanBehavior(config)

    try:
        page = await browser.get("https://example.com")
        print("Starting exploration session (30 seconds)...")

        # Run varied interaction session
        await behavior.varied_interaction_session(page, duration=30.0)
        print("Exploration session complete")

    except Exception as e:
        print(f"Error: {e}")
    finally:
        await browser.aclose()


async def example_4_careful_reading():
    """
    Example 4: Careful, methodical reading.

    Demonstrates using configuration for a cautious, deliberate
    reading and interaction pattern.
    """
    print("\n" + "=" * 60)
    print("Example 4: Careful Reading with Analysis")
    print("=" * 60)

    try:
        from quick_start import create_browser
    except ImportError:
        print("Error: quick_start module not found")
        return

    browser = await create_browser()

    # Cautious, slow reading configuration
    config = BehaviorConfig(
        reading_speed=1.5,
        interaction_style=InteractionStyle.CAUTIOUS,
        pause_probability=0.3,
        hover_probability=0.2,
    )
    behavior = HumanBehavior(config)

    try:
        page = await browser.get("https://example.com/documentation")
        print("Opened documentation page")

        # Read carefully with pauses
        print("Reading with careful attention...")
        await behavior.read_page(page, reading_speed="slow")

        # Scroll with extra pauses
        print("Scrolling through content...")
        await behavior.scroll_naturally(page, smoothness=0.9)

        print("Careful reading complete")

    except Exception as e:
        print(f"Error: {e}")
    finally:
        await browser.aclose()


async def example_5_typing_demonstration():
    """
    Example 5: Demonstrating typing rhythm variations.

    Shows how the typing module generates realistic keystroke
    patterns and can simulate different typing speeds.
    """
    print("\n" + "=" * 60)
    print("Example 5: Typing Rhythm Demonstration")
    print("=" * 60)

    behavior = HumanBehavior()

    # Demonstrate keystroke delays for different text
    test_cases = [
        ("Hello", 100),  # Fast typing
        ("Important Password123!", 40),  # Slow, careful
        ("user@example.com", 80),  # Email (moderate)
    ]

    for text, speed in test_cases:
        print(f"\nText: '{text}' (Speed: {speed} WPM)")

        delays = behavior.typing.keystroke_delays(
            text,
            base_speed=speed,
            variance=0.3,
        )

        total_time = sum(delays)
        print(f"  Total typing time: {total_time:.2f} seconds")
        print(f"  Character delays (first 5):")

        for i, (char, delay) in enumerate(zip(text[:5], delays[:5])):
            print(f"    '{char}': {delay:.3f}s")

        if len(delays) > 5:
            print(f"    ... ({len(delays) - 5} more characters)")


async def example_6_delay_patterns():
    """
    Example 6: Demonstrating different delay patterns.

    Shows how different delay generators create different
    pause distributions.
    """
    print("\n" + "=" * 60)
    print("Example 6: Delay Pattern Demonstration")
    print("=" * 60)

    behavior = HumanBehavior()
    num_samples = 10

    # Exponential delays (natural reaction times)
    print("\nExponential Distribution (natural pauses):")
    print("-" * 40)
    exponential_delays = []
    for i in range(num_samples):
        delay = behavior.delay_gen.exponential_delay(0.1, 2.0)
        exponential_delays.append(delay)
        print(f"  Sample {i + 1}: {delay:.3f}s")

    avg = sum(exponential_delays) / len(exponential_delays)
    print(f"  Average: {avg:.3f}s")

    # Gaussian delays (clustered around mean)
    print("\nGaussian Distribution (clustered pauses):")
    print("-" * 40)
    gaussian_delays = []
    for i in range(num_samples):
        delay = behavior.delay_gen.gaussian_delay(0.5, 0.1)
        gaussian_delays.append(delay)
        print(f"  Sample {i + 1}: {delay:.3f}s")

    avg = sum(gaussian_delays) / len(gaussian_delays)
    print(f"  Average: {avg:.3f}s")

    # Keystroke delays
    print("\nKeystroke Delays (typing rhythm):")
    print("-" * 40)
    text = "typing"
    delays = behavior.typing.keystroke_delays(text, base_speed=60)
    for char, delay in zip(text, delays):
        print(f"  '{char}': {delay:.3f}s")
    total = sum(delays)
    print(f"  Total: {total:.3f}s")


async def example_7_mouse_movement():
    """
    Example 7: Demonstrating mouse movement paths.

    Shows how different Bezier curve types create realistic
    mouse movement patterns.
    """
    print("\n" + "=" * 60)
    print("Example 7: Mouse Movement Paths")
    print("=" * 60)

    behavior = HumanBehavior()

    start = (100, 100)
    end = (500, 300)

    # Quadratic Bezier
    print("\nQuadratic Bezier Curve (simple curve):")
    print("-" * 40)
    quad_path = behavior.mouse.quadratic_bezier(start, end, steps=10)
    print(f"  Start: {quad_path[0]}")
    for i in range(1, min(3, len(quad_path))):
        print(f"  Step {i}: {quad_path[i]}")
    print(f"  ... ({len(quad_path) - 3} more points)")
    print(f"  End: {quad_path[-1]}")

    # Cubic Bezier
    print("\nCubic Bezier Curve (complex curve):")
    print("-" * 40)
    cubic_path = behavior.mouse.cubic_bezier(start, end, steps=15)
    print(f"  Start: {cubic_path[0]}")
    for i in range(1, min(3, len(cubic_path))):
        print(f"  Step {i}: {cubic_path[i]}")
    print(f"  ... ({len(cubic_path) - 3} more points)")
    print(f"  End: {cubic_path[-1]}")

    # With jitter
    print("\nJittered Path (with hand tremor):")
    print("-" * 40)
    jittered = behavior.mouse.jittered_path(start, end, jitter_amount=0.3, steps=5)
    print(f"  Start: {jittered[0]}")
    for i in range(1, min(3, len(jittered))):
        print(f"  Step {i}: {jittered[i]}")
    print(f"  ... ({len(jittered) - 3} more points)")
    print(f"  End: {jittered[-1]}")


async def example_8_configuration_styles():
    """
    Example 8: Demonstrating different configuration styles.

    Shows how to configure behavior for different scenarios
    (minimal, cautious, normal, engaged).
    """
    print("\n" + "=" * 60)
    print("Example 8: Configuration Styles")
    print("=" * 60)

    styles = [
        ("MINIMAL", BehaviorConfig(
            interaction_style=InteractionStyle.MINIMAL,
            reading_speed=0.5,
            hover_probability=0.05,
        )),
        ("CAUTIOUS", BehaviorConfig(
            interaction_style=InteractionStyle.CAUTIOUS,
            reading_speed=1.5,
            hover_probability=0.15,
        )),
        ("NORMAL", BehaviorConfig(
            interaction_style=InteractionStyle.NORMAL,
            reading_speed=1.0,
            hover_probability=0.3,
        )),
        ("ENGAGED", BehaviorConfig(
            interaction_style=InteractionStyle.ENGAGED,
            reading_speed=1.0,
            hover_probability=0.5,
        )),
    ]

    for style_name, config in styles:
        print(f"\n{style_name} Configuration:")
        print("-" * 40)
        print(f"  Reading Speed: {config.reading_speed}x")
        print(f"  Interaction Style: {config.interaction_style.value}")
        print(f"  Hover Probability: {config.hover_probability * 100:.0f}%")
        print(f"  Pause Probability: {config.pause_probability * 100:.0f}%")
        print(f"  Scroll Smoothness: {config.scroll_smoothness}")
        print(f"  Typing Variance: {config.typing_rhythm_variance * 100:.0f}%")


async def example_9_scrolling_behavior():
    """
    Example 9: Demonstrating scrolling patterns.

    Shows how the scrolling module generates natural scroll
    increments and reading pauses.
    """
    print("\n" + "=" * 60)
    print("Example 9: Scrolling Behavior")
    print("=" * 60)

    behavior = HumanBehavior()

    # Generate scroll increments
    increments = behavior.scroll.scroll_increments(
        total_scroll=1000,
        smoothness=0.8,
        include_pauses=True,
    )

    print("\nScroll Increments (1000 pixels total):")
    print("-" * 40)
    total = 0
    for i, increment in enumerate(increments[:10]):
        if increment > 0:
            print(f"  Scroll {i + 1}: {increment:.1f}px")
            total += increment
        else:
            print(f"  Pause {i + 1}: Reading pause (0px)")

    if len(increments) > 10:
        print(f"  ... ({len(increments) - 10} more increments)")

    # Calculate dwell times
    print("\nReading Pause Durations:")
    print("-" * 40)
    scroll_amounts = [100, 300, 500]
    for amount in scroll_amounts:
        dwell = behavior.scroll.dwell_time_for_scroll(amount, reading_speed=1.0)
        print(f"  After scrolling {amount}px: {dwell:.2f}s")


async def main():
    """Run all examples."""
    print("\n" + "=" * 60)
    print("HumanBehavior Module - Practical Examples")
    print("=" * 60)

    examples = [
        (1, "Read Article", example_1_read_article),
        (2, "Form Filling", example_2_form_filling),
        (3, "Exploration Session", example_3_exploration_session),
        (4, "Careful Reading", example_4_careful_reading),
        (5, "Typing Demonstration", example_5_typing_demonstration),
        (6, "Delay Patterns", example_6_delay_patterns),
        (7, "Mouse Movement", example_7_mouse_movement),
        (8, "Configuration Styles", example_8_configuration_styles),
        (9, "Scrolling Behavior", example_9_scrolling_behavior),
    ]

    print("\nAvailable Examples:")
    for num, title, _ in examples:
        print(f"  {num}. {title}")

    print("\nRunning non-browser examples...")
    print("(Browser-based examples require nodriver setup)")

    # Run non-browser examples
    non_browser = [5, 6, 7, 8, 9]
    for num, _, func in examples:
        if num in non_browser:
            try:
                await func()
            except Exception as e:
                print(f"Error in example {num}: {e}")

    print("\n" + "=" * 60)
    print("Examples Complete")
    print("=" * 60)
    print("\nNote: Browser-based examples (1-4) require:")
    print("  - nodriver library installed")
    print("  - Chromium/Chrome browser available")
    print("  - Modify selectors for actual pages")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n\nInterrupted by user")
