#!/usr/bin/env python3
"""
Unit tests and verification for the HumanBehavior module.

Tests core functionality of behavior patterns without requiring
a browser instance.
"""

import asyncio
import math
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


def test_reading_speed_enum():
    """Test that ReadingSpeed enum has expected values."""
    assert ReadingSpeed.FAST.value == 0.5
    assert ReadingSpeed.NORMAL.value == 1.0
    assert ReadingSpeed.SLOW.value == 1.5
    assert ReadingSpeed.VERY_SLOW.value == 2.0
    print("✓ ReadingSpeed enum correct")


def test_interaction_style_enum():
    """Test that InteractionStyle enum has expected values."""
    assert InteractionStyle.MINIMAL.value == "minimal"
    assert InteractionStyle.CAUTIOUS.value == "cautious"
    assert InteractionStyle.NORMAL.value == "normal"
    assert InteractionStyle.ENGAGED.value == "engaged"
    print("✓ InteractionStyle enum correct")


def test_behavior_config_defaults():
    """Test BehaviorConfig default values."""
    config = BehaviorConfig()
    assert config.reading_speed == 1.0
    assert config.interaction_style == InteractionStyle.NORMAL
    assert config.mouse_speed == 1.0
    assert config.scroll_smoothness == 0.8
    assert config.typing_rhythm_variance == 0.3
    assert config.pause_probability == 0.2
    assert config.hover_probability == 0.3
    print("✓ BehaviorConfig defaults correct")


def test_behavior_config_custom():
    """Test BehaviorConfig with custom values."""
    config = BehaviorConfig(
        reading_speed=1.5,
        interaction_style=InteractionStyle.ENGAGED,
        mouse_speed=0.5,
    )
    assert config.reading_speed == 1.5
    assert config.interaction_style == InteractionStyle.ENGAGED
    assert config.mouse_speed == 0.5
    print("✓ BehaviorConfig custom values work")


def test_exponential_delay():
    """Test exponential delay generation."""
    gen = DelayGenerator()

    # Generate multiple delays
    delays = [gen.exponential_delay(0.1, 2.0) for _ in range(100)]

    # All delays should be within bounds
    assert all(0.1 <= d <= 2.0 for d in delays)

    # Should have some variance
    assert min(delays) < 0.5 or max(delays) > 0.5

    # Average should be reasonable
    avg = sum(delays) / len(delays)
    assert 0.1 < avg < 2.0

    print(f"✓ Exponential delay: avg={avg:.3f}s (100 samples)")


def test_gaussian_delay():
    """Test Gaussian delay generation."""
    gen = DelayGenerator()

    # Generate multiple delays
    delays = [gen.gaussian_delay(0.5, 0.1) for _ in range(100)]

    # All delays should be within bounds
    assert all(0.05 <= d <= 1.0 for d in delays)

    # Average should be close to mean
    avg = sum(delays) / len(delays)
    assert 0.3 < avg < 0.7

    # Should have standard deviation close to requested
    variance = sum((d - avg) ** 2 for d in delays) / len(delays)
    std_dev = math.sqrt(variance)
    assert 0.05 < std_dev < 0.2

    print(f"✓ Gaussian delay: avg={avg:.3f}s, std={std_dev:.3f}s")


def test_between_keys_delay():
    """Test keystroke delay generation."""
    gen = DelayGenerator()

    delays = []
    for wpm in [40, 60, 100]:
        delay = gen.between_keys_delay(wpm)
        delays.append(delay)
        assert delay > 0.01  # Must be positive and reasonable

    # Slower WPM should have longer delays
    assert delays[0] > delays[1] > delays[2]

    print(f"✓ Between-keys delays: 40WPM={delays[0]:.3f}s, "
          f"60WPM={delays[1]:.3f}s, 100WPM={delays[2]:.3f}s")


def test_blink_delay():
    """Test blink delay duration."""
    gen = DelayGenerator()

    blinks = [gen.blink_delay() for _ in range(50)]

    # All should be in 200-400ms range
    assert all(0.2 <= b <= 0.4 for b in blinks)

    avg = sum(blinks) / len(blinks)
    assert 0.25 < avg < 0.35

    print(f"✓ Blink delay: avg={avg:.3f}s (50 samples)")


def test_thinking_pause():
    """Test thinking pause generation."""
    gen = DelayGenerator()

    # Test different complexities
    pauses = {
        0.5: [gen.thinking_pause(0.5) for _ in range(20)],
        1.0: [gen.thinking_pause(1.0) for _ in range(20)],
        2.0: [gen.thinking_pause(2.0) for _ in range(20)],
    }

    # Higher complexity should have longer pauses on average
    avg_05 = sum(pauses[0.5]) / len(pauses[0.5])
    avg_10 = sum(pauses[1.0]) / len(pauses[1.0])
    avg_20 = sum(pauses[2.0]) / len(pauses[2.0])

    assert avg_05 < avg_10 < avg_20

    print(f"✓ Thinking pause: 0.5x={avg_05:.2f}s, "
          f"1.0x={avg_10:.2f}s, 2.0x={avg_20:.2f}s")


def test_quadratic_bezier():
    """Test quadratic Bezier curve generation."""
    start = (0, 0)
    end = (100, 100)

    path = MouseMovement.quadratic_bezier(start, end, steps=10)

    # Should have correct number of points
    assert len(path) == 11  # steps + 1

    # First and last points should match start and end
    assert path[0] == start
    assert path[-1] == end

    # All points should be tuples of floats
    assert all(isinstance(p, tuple) and len(p) == 2 for p in path)

    print(f"✓ Quadratic Bezier: {len(path)} points from {start} to {end}")


def test_cubic_bezier():
    """Test cubic Bezier curve generation."""
    start = (0, 0)
    end = (200, 150)

    path = MouseMovement.cubic_bezier(start, end, steps=20)

    # Should have correct number of points
    assert len(path) == 21  # steps + 1

    # First and last points should match
    assert path[0] == start
    assert path[-1] == end

    print(f"✓ Cubic Bezier: {len(path)} points from {start} to {end}")


def test_jittered_path():
    """Test jittered path generation."""
    start = (100, 100)
    end = (200, 200)

    # With different jitter amounts
    for jitter in [0.1, 0.5, 1.0]:
        path = MouseMovement.jittered_path(start, end, jitter_amount=jitter, steps=10)

        # Should have correct number of points
        assert len(path) == 11

        # Start and end should be approximately correct (within jitter range)
        assert abs(path[0][0] - start[0]) < 20  # Some tolerance for jitter
        assert abs(path[-1][0] - end[0]) < 20

    print(f"✓ Jittered path: generated with various jitter amounts")


def test_scroll_increments():
    """Test scroll increment generation."""
    scroll = ScrollingBehavior()

    increments = scroll.scroll_increments(1000, smoothness=0.8, include_pauses=True)

    # Should have multiple increments
    assert len(increments) > 1

    # At least some should be positive (actual scrolls)
    assert any(i > 0 for i in increments)

    # Some might be 0 (pauses)
    # (but not guaranteed, depends on random)

    # All should be non-negative
    assert all(i >= 0 for i in increments)

    print(f"✓ Scroll increments: generated {len(increments)} increments")


def test_dwell_time_for_scroll():
    """Test dwell time calculation."""
    scroll = ScrollingBehavior()

    # Different scroll amounts
    dwell_small = scroll.dwell_time_for_scroll(100, reading_speed=1.0)
    dwell_large = scroll.dwell_time_for_scroll(500, reading_speed=1.0)

    # Larger scroll should have longer dwell time
    assert dwell_large > dwell_small

    # Different reading speeds
    dwell_fast = scroll.dwell_time_for_scroll(300, reading_speed=0.5)
    dwell_slow = scroll.dwell_time_for_scroll(300, reading_speed=1.5)

    # Slower reading should have longer dwell
    assert dwell_slow > dwell_fast

    print(f"✓ Dwell time: small={dwell_small:.2f}s, large={dwell_large:.2f}s")


def test_keystroke_delays():
    """Test keystroke delay generation."""
    typing = TypingRhythm()

    text = "Hello World 123!"
    delays = typing.keystroke_delays(text, base_speed=60, variance=0.3)

    # Should have one delay per character
    assert len(delays) == len(text)

    # All should be positive
    assert all(d > 0 for d in delays)

    # Total typing time should be reasonable
    total_time = sum(delays)
    assert 0.5 < total_time < 5.0  # Reasonable for 16 characters

    # Numbers and symbols should have different delays than letters
    # (on average)
    print(f"✓ Keystroke delays: {len(delays)} delays for '{text}'")


def test_has_typos():
    """Test typo position generation."""
    typing = TypingRhythm()

    text = "testing error detection"
    typos = typing.has_typos(text, error_rate=0.0)

    # With 0 error rate, should have no typos
    assert len(typos) == 0

    # With high error rate, should have many
    typos_high = typing.has_typos(text, error_rate=0.5)
    assert len(typos_high) > len(text) * 0.2  # At least 20% of text

    print(f"✓ Typo detection: working correctly")


def test_should_hover():
    """Test hover probability by style."""
    interactions = InteractionPatterns()

    # Run multiple samples to check probabilities
    num_trials = 1000
    for style in InteractionStyle:
        hovers = sum(
            1 for _ in range(num_trials)
            if interactions.should_hover(style)
        )
        hover_rate = hovers / num_trials

        # Rate should be roughly in expected range
        if style == InteractionStyle.MINIMAL:
            assert hover_rate < 0.15
        elif style == InteractionStyle.ENGAGED:
            assert hover_rate > 0.3

        print(f"✓ Hover probability for {style.value}: {hover_rate:.1%}")


def test_interaction_focus_pattern():
    """Test interaction pattern generation."""
    interactions = InteractionPatterns()

    pattern = interactions.interaction_focus_pattern(
        duration=10.0,
        interaction_style=InteractionStyle.NORMAL,
    )

    # Should generate some interactions
    assert len(pattern) > 0

    # Each should be (action_type, delay) tuple
    for action, delay in pattern:
        assert isinstance(action, str)
        assert isinstance(delay, float)
        assert delay > 0

    # Pattern shouldn't exceed duration
    total_delay = sum(d for _, d in pattern)
    assert total_delay <= 10.0 * 1.1  # Small tolerance

    print(f"✓ Interaction pattern: generated {len(pattern)} interactions")


def test_human_behavior_instantiation():
    """Test HumanBehavior instantiation."""
    # Default
    behavior = HumanBehavior()
    assert behavior.config is not None
    assert behavior.delay_gen is not None
    assert behavior.mouse is not None
    assert behavior.scroll is not None
    assert behavior.typing is not None

    # Custom config
    config = BehaviorConfig(reading_speed=1.5)
    behavior_custom = HumanBehavior(config)
    assert behavior_custom.config.reading_speed == 1.5

    print("✓ HumanBehavior instantiation works")


async def test_async_delays():
    """Test async delay methods."""
    behavior = HumanBehavior()

    # These should complete without error
    import time

    start = time.time()
    await behavior.random_delay(0.05, 0.1)
    elapsed = time.time() - start
    assert 0.04 < elapsed < 0.2  # Allow some tolerance

    start = time.time()
    await behavior.blink_pause()
    elapsed = time.time() - start
    assert 0.15 < elapsed < 0.5

    print("✓ Async delay methods work")


def run_all_tests():
    """Run all unit tests."""
    print("\n" + "=" * 60)
    print("HumanBehavior Module - Unit Tests")
    print("=" * 60 + "\n")

    sync_tests = [
        ("ReadingSpeed enum", test_reading_speed_enum),
        ("InteractionStyle enum", test_interaction_style_enum),
        ("BehaviorConfig defaults", test_behavior_config_defaults),
        ("BehaviorConfig custom", test_behavior_config_custom),
        ("Exponential delay", test_exponential_delay),
        ("Gaussian delay", test_gaussian_delay),
        ("Between-keys delay", test_between_keys_delay),
        ("Blink delay", test_blink_delay),
        ("Thinking pause", test_thinking_pause),
        ("Quadratic Bezier", test_quadratic_bezier),
        ("Cubic Bezier", test_cubic_bezier),
        ("Jittered path", test_jittered_path),
        ("Scroll increments", test_scroll_increments),
        ("Dwell time", test_dwell_time_for_scroll),
        ("Keystroke delays", test_keystroke_delays),
        ("Typo detection", test_has_typos),
        ("Hover probability", test_should_hover),
        ("Interaction pattern", test_interaction_focus_pattern),
        ("HumanBehavior instantiation", test_human_behavior_instantiation),
    ]

    passed = 0
    failed = 0

    for test_name, test_func in sync_tests:
        try:
            test_func()
            passed += 1
        except AssertionError as e:
            print(f"✗ {test_name}: {e}")
            failed += 1
        except Exception as e:
            print(f"✗ {test_name}: {type(e).__name__}: {e}")
            failed += 1

    # Run async tests
    print("\nAsync Tests:")
    try:
        asyncio.run(test_async_delays())
        passed += 1
    except Exception as e:
        print(f"✗ Async delays: {e}")
        failed += 1

    # Summary
    print("\n" + "=" * 60)
    print(f"Results: {passed} passed, {failed} failed")
    print("=" * 60)

    return failed == 0


if __name__ == "__main__":
    success = run_all_tests()
    exit(0 if success else 1)
