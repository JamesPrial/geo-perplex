#!/usr/bin/env python3
"""
Human-like behavior patterns for natural-looking automation.

This module provides utilities for simulating realistic human interaction patterns
with web browsers, making automation appear more natural and human-like. All patterns
are designed to avoid detection while remaining completely within terms of service
(reading pages, natural interactions, normal browsing patterns).

Key Features:
    - Random delays with natural distribution (not uniform)
    - Realistic mouse movement using Bezier curves
    - Smooth scrolling patterns with varied speeds
    - Typing rhythm variations (not uniform keystroke timing)
    - Natural interaction patterns (hovering, focus events)
    - Tab/window switching behavior
    - Reading simulation based on content length
    - Configurable behavior patterns for different scenarios

Example:
    >>> import asyncio
    >>> from human_behavior import HumanBehavior, BehaviorConfig
    >>> from quick_start import create_browser
    >>>
    >>> async def main():
    ...     browser = await create_browser()
    ...     behavior = HumanBehavior()
    ...     try:
    ...         page = await browser.get("https://example.com")
    ...         await behavior.read_page(page, reading_speed="normal")
    ...         await behavior.scroll_naturally(page)
    ...     finally:
    ...         await browser.aclose()
    >>>
    >>> asyncio.run(main())
"""

import asyncio
import random
import math
from dataclasses import dataclass
from typing import Optional, Tuple, List
from enum import Enum


class ReadingSpeed(Enum):
    """Predefined reading speeds for different content types."""
    FAST = 0.5  # Quick skim
    NORMAL = 1.0  # Average reading
    SLOW = 1.5  # Careful reading
    VERY_SLOW = 2.0  # Very careful/complex content


class InteractionStyle(Enum):
    """Different interaction patterns (conservative to aggressive)."""
    MINIMAL = "minimal"  # Very little interaction
    CAUTIOUS = "cautious"  # Limited, careful interaction
    NORMAL = "normal"  # Natural interaction patterns
    ENGAGED = "engaged"  # Frequent interaction


@dataclass
class BehaviorConfig:
    """
    Configuration for human behavior patterns.

    Attributes:
        reading_speed: Default reading speed multiplier (0.5 to 2.0)
        interaction_style: Pattern of interaction frequency
        mouse_speed: How fast the mouse moves (0.1 to 2.0)
        scroll_smoothness: How smooth scrolling is (0.1 to 1.0)
        typing_rhythm_variance: Variance in typing speed (0.1 to 1.0)
        pause_probability: Probability of pausing during actions (0.0 to 1.0)
        hover_probability: Probability of hovering over elements (0.0 to 1.0)
    """
    reading_speed: float = 1.0
    interaction_style: InteractionStyle = InteractionStyle.NORMAL
    mouse_speed: float = 1.0
    scroll_smoothness: float = 0.8
    typing_rhythm_variance: float = 0.3
    pause_probability: float = 0.2
    hover_probability: float = 0.3


class DelayGenerator:
    """
    Generate random delays with natural human-like distributions.

    Uses realistic delay patterns that match how humans interact with
    computers, avoiding the obvious uniformity of simple random delays.
    """

    @staticmethod
    def exponential_delay(
        base: float = 0.1,
        max_delay: float = 2.0,
        variance: float = 0.5,
    ) -> float:
        """
        Generate an exponential delay (many short pauses, few long ones).

        This mimics human reaction time patterns - most actions happen
        quickly, but occasionally longer pauses occur naturally.

        Args:
            base: Minimum delay in seconds
            max_delay: Maximum delay in seconds
            variance: Multiplier for variance (higher = more varied)

        Returns:
            Delay time in seconds
        """
        # Exponential distribution creates realistic pause patterns
        delay = random.expovariate(1 / base) * variance
        return min(delay, max_delay)

    @staticmethod
    def gaussian_delay(
        mean: float = 0.3,
        std_dev: float = 0.1,
        min_delay: float = 0.05,
        max_delay: float = 1.0,
    ) -> float:
        """
        Generate a Gaussian (normal) distributed delay.

        Most delays cluster around the mean with occasional outliers,
        which matches typical human timing patterns.

        Args:
            mean: Average delay in seconds
            std_dev: Standard deviation
            min_delay: Minimum allowed delay
            max_delay: Maximum allowed delay

        Returns:
            Delay time in seconds
        """
        delay = random.gauss(mean, std_dev)
        return max(min_delay, min(delay, max_delay))

    @staticmethod
    def between_keys_delay(base_speed: float = 100) -> float:
        """
        Generate delay between keypresses (WPM-based).

        Simulates natural typing rhythm where keystroke intervals
        vary realistically based on typing speed.

        Args:
            base_speed: Words per minute equivalent

        Returns:
            Delay between keys in seconds
        """
        # Average word is ~5 characters, so base calculation
        chars_per_second = (base_speed * 5) / 60
        base_delay = 1 / chars_per_second

        # Add realistic variance (not all keys have same delay)
        variance = random.gauss(1.0, 0.2)  # 20% variance
        return max(0.02, base_delay * variance)

    @staticmethod
    def blink_delay() -> float:
        """
        Generate a realistic blink duration pause (200-400ms).

        Used for natural breaks in activity that feel like human attention shifts.

        Returns:
            Delay time in seconds
        """
        return random.uniform(0.2, 0.4)

    @staticmethod
    def thinking_pause(complexity: float = 1.0) -> float:
        """
        Generate a thinking/consideration pause.

        Args:
            complexity: Content complexity (0.5 to 2.0)

        Returns:
            Delay time in seconds
        """
        base = random.uniform(0.5, 2.0) * complexity
        return min(base, 5.0)


class MouseMovement:
    """
    Generate realistic mouse movement paths using Bezier curves.

    Humans don't move their mouse in straight lines - they use curved
    paths with acceleration and deceleration patterns.
    """

    @staticmethod
    def quadratic_bezier(
        start: Tuple[float, float],
        end: Tuple[float, float],
        control: Optional[Tuple[float, float]] = None,
        steps: int = 20,
    ) -> List[Tuple[float, float]]:
        """
        Generate points along a quadratic Bezier curve.

        Creates a smooth curved path from start to end point, with
        optional control point for curve direction.

        Args:
            start: Starting (x, y) coordinates
            end: Ending (x, y) coordinates
            control: Control point for curve shape (generated if None)
            steps: Number of points to generate

        Returns:
            List of (x, y) coordinate tuples along the curve
        """
        if control is None:
            # Generate a random control point for natural curve
            mid_x = (start[0] + end[0]) / 2
            mid_y = (start[1] + end[1]) / 2
            offset_x = random.gauss(0, abs(end[0] - start[0]) / 4)
            offset_y = random.gauss(0, abs(end[1] - start[1]) / 4)
            control = (mid_x + offset_x, mid_y + offset_y)

        points = []
        for i in range(steps + 1):
            t = i / steps
            # Quadratic Bezier formula: B(t) = (1-t)^2*P0 + 2(1-t)t*P1 + t^2*P2
            x = (
                (1 - t) ** 2 * start[0]
                + 2 * (1 - t) * t * control[0]
                + t ** 2 * end[0]
            )
            y = (
                (1 - t) ** 2 * start[1]
                + 2 * (1 - t) * t * control[1]
                + t ** 2 * end[1]
            )
            points.append((x, y))

        return points

    @staticmethod
    def cubic_bezier(
        start: Tuple[float, float],
        end: Tuple[float, float],
        control1: Optional[Tuple[float, float]] = None,
        control2: Optional[Tuple[float, float]] = None,
        steps: int = 30,
    ) -> List[Tuple[float, float]]:
        """
        Generate points along a cubic Bezier curve.

        More complex than quadratic - allows for S-shaped curves and
        more natural mouse movement patterns.

        Args:
            start: Starting (x, y) coordinates
            end: Ending (x, y) coordinates
            control1: First control point (generated if None)
            control2: Second control point (generated if None)
            steps: Number of points to generate

        Returns:
            List of (x, y) coordinate tuples along the curve
        """
        if control1 is None or control2 is None:
            # Generate control points for smooth curve
            dx = end[0] - start[0]
            dy = end[1] - start[1]

            if control1 is None:
                control1 = (
                    start[0] + dx / 3 + random.gauss(0, dx / 8),
                    start[1] + dy / 3 + random.gauss(0, dy / 8),
                )
            if control2 is None:
                control2 = (
                    start[0] + 2 * dx / 3 + random.gauss(0, dx / 8),
                    start[1] + 2 * dy / 3 + random.gauss(0, dy / 8),
                )

        points = []
        for i in range(steps + 1):
            t = i / steps
            # Cubic Bezier formula
            mt = 1 - t
            x = (
                mt ** 3 * start[0]
                + 3 * mt ** 2 * t * control1[0]
                + 3 * mt * t ** 2 * control2[0]
                + t ** 3 * end[0]
            )
            y = (
                mt ** 3 * start[1]
                + 3 * mt ** 2 * t * control1[1]
                + 3 * mt * t ** 2 * control2[1]
                + t ** 3 * end[1]
            )
            points.append((x, y))

        return points

    @staticmethod
    def jittered_path(
        start: Tuple[float, float],
        end: Tuple[float, float],
        jitter_amount: float = 0.3,
        steps: int = 20,
    ) -> List[Tuple[float, float]]:
        """
        Generate a path with natural hand tremor/jitter.

        Adds slight imprecision that makes movement look more human,
        as perfect precision is suspicious.

        Args:
            start: Starting (x, y) coordinates
            end: Ending (x, y) coordinates
            jitter_amount: Amount of jitter (0.0 to 1.0)
            steps: Number of points to generate

        Returns:
            List of (x, y) coordinate tuples with jitter
        """
        # Start with smooth Bezier curve
        smooth_points = MouseMovement.quadratic_bezier(start, end, steps=steps)

        # Add jitter to each point
        dx = abs(end[0] - start[0])
        dy = abs(end[1] - start[1])
        jitter_x = dx * jitter_amount * 0.1
        jitter_y = dy * jitter_amount * 0.1

        jittered = []
        for x, y in smooth_points:
            jittered_x = x + random.gauss(0, jitter_x)
            jittered_y = y + random.gauss(0, jitter_y)
            jittered.append((jittered_x, jittered_y))

        return jittered


class ScrollingBehavior:
    """
    Generate realistic scrolling patterns with varied speeds and pauses.

    Humans don't scroll at constant speeds - they pause, read, scroll,
    maybe scroll back up. This module simulates those patterns.
    """

    @staticmethod
    def scroll_increments(
        total_scroll: float,
        smoothness: float = 0.8,
        include_pauses: bool = True,
    ) -> List[float]:
        """
        Generate scroll increments for smooth, natural scrolling.

        Args:
            total_scroll: Total pixels to scroll
            smoothness: How smooth (0.1 to 1.0, higher = smoother)
            include_pauses: Whether to include pause intervals

        Returns:
            List of scroll increments
        """
        num_increments = max(5, int(total_scroll / (50 * smoothness)))
        increments = []

        for _ in range(num_increments):
            # Create varying scroll speeds (some fast, some slow)
            base_increment = total_scroll / num_increments
            variance = random.gauss(1.0, 0.3)  # 30% variance
            increment = max(10, base_increment * variance)
            increments.append(increment)

        # Sometimes add pauses (represented as 0 increment)
        if include_pauses and random.random() < 0.3:
            pause_positions = random.sample(
                range(len(increments)), k=random.randint(1, len(increments) // 3)
            )
            for pos in pause_positions:
                increments[pos] = 0  # 0 means pause, not scroll

        return increments

    @staticmethod
    def dwell_time_for_scroll(
        scroll_amount: float,
        reading_speed: float = 1.0,
    ) -> float:
        """
        Calculate how long to dwell after scrolling based on content.

        Args:
            scroll_amount: Amount scrolled (approximates content amount)
            reading_speed: Reading speed multiplier (0.5 to 2.0)

        Returns:
            Time to dwell in seconds
        """
        # Assume ~250 words per screen, ~240 pixels per screen
        estimated_words = (scroll_amount / 240) * 250
        # Average reading is ~200 WPM
        base_reading_time = (estimated_words / 200) * 60
        return base_reading_time * reading_speed


class TypingRhythm:
    """
    Generate realistic typing patterns with natural rhythm variations.

    Real typists have patterns - faster on familiar words, slower
    on unfamiliar text, with occasional corrections and pauses.
    """

    @staticmethod
    def keystroke_delays(
        text: str,
        base_speed: float = 60,
        variance: float = 0.3,
    ) -> List[float]:
        """
        Generate delays between keystrokes for realistic typing.

        Args:
            text: Text to be typed
            base_speed: Average WPM (words per minute)
            variance: Typing variance (0.1 to 1.0)

        Returns:
            List of delays (one per character)
        """
        delays = []

        for i, char in enumerate(text):
            # Some characters are naturally slower (numbers, symbols)
            if char.isdigit() or char in "!@#$%^&*()_+-=[]{}|;:,.<>?/":
                speed_multiplier = 1.3  # Slower for special chars
            elif char.isupper():
                speed_multiplier = 1.1  # Slightly slower for capitals
            else:
                speed_multiplier = 1.0

            # Occasional corrections (backspace-like pauses)
            if random.random() < 0.01:  # 1% chance of a pause
                delays.append(random.uniform(0.3, 0.7))
                continue

            # Generate keystroke delay
            base_delay = DelayGenerator.between_keys_delay(base_speed)
            variance_factor = random.gauss(1.0, variance)
            delay = base_delay * speed_multiplier * variance_factor
            delays.append(max(0.02, delay))

        return delays

    @staticmethod
    def has_typos(text: str, error_rate: float = 0.02) -> List[int]:
        """
        Identify positions where typos might occur.

        Args:
            text: Text being typed
            error_rate: Probability of error per character (0.0 to 0.1)

        Returns:
            List of character positions that have errors
        """
        error_positions = []
        for i in range(len(text)):
            if random.random() < error_rate:
                error_positions.append(i)
        return error_positions


class InteractionPatterns:
    """
    Generate natural interaction patterns (hovering, focusing, etc).
    """

    @staticmethod
    def should_hover(interaction_style: InteractionStyle) -> bool:
        """
        Determine if an element should be hovered over.

        Args:
            interaction_style: The interaction style to use

        Returns:
            True if should hover, False otherwise
        """
        probabilities = {
            InteractionStyle.MINIMAL: 0.05,
            InteractionStyle.CAUTIOUS: 0.15,
            InteractionStyle.NORMAL: 0.3,
            InteractionStyle.ENGAGED: 0.5,
        }
        threshold = probabilities.get(interaction_style, 0.3)
        return random.random() < threshold

    @staticmethod
    def interaction_focus_pattern(
        duration: float = 10.0,
        interaction_style: InteractionStyle = InteractionStyle.NORMAL,
    ) -> List[Tuple[str, float]]:
        """
        Generate a pattern of focus/interaction events over time.

        Returns: List of (action_type, delay_until_action) tuples
        """
        actions = []
        elapsed = 0.0
        frequencies = {
            InteractionStyle.MINIMAL: 1,
            InteractionStyle.CAUTIOUS: 2,
            InteractionStyle.NORMAL: 3,
            InteractionStyle.ENGAGED: 5,
        }

        num_interactions = random.randint(
            1, frequencies.get(interaction_style, 3)
        )

        for _ in range(num_interactions):
            if elapsed >= duration:
                break

            action_types = ["hover", "focus", "click", "scroll"]
            action = random.choice(action_types)
            delay = random.uniform(0.5, 3.0)
            actions.append((action, delay))
            elapsed += delay

        return actions


class HumanBehavior:
    """
    Orchestrator for human-like behavior patterns.

    Combines all behavior modules to provide coordinated, natural-looking
    automation that simulates realistic human web browsing.
    """

    def __init__(self, config: Optional[BehaviorConfig] = None):
        """
        Initialize HumanBehavior with optional custom configuration.

        Args:
            config: BehaviorConfig instance or None for defaults
        """
        self.config = config or BehaviorConfig()
        self.delay_gen = DelayGenerator()
        self.mouse = MouseMovement()
        self.scroll = ScrollingBehavior()
        self.typing = TypingRhythm()
        self.interactions = InteractionPatterns()

    async def random_delay(self, min_delay: float = 0.1, max_delay: float = 2.0) -> None:
        """
        Wait a random amount of time using natural distribution.

        Args:
            min_delay: Minimum delay in seconds
            max_delay: Maximum delay in seconds
        """
        delay = self.delay_gen.exponential_delay(min_delay, max_delay)
        await asyncio.sleep(delay)

    async def thinking_pause(self, complexity: float = 1.0) -> None:
        """
        Simulate human thinking/consideration pause.

        Args:
            complexity: Content complexity (0.5 to 2.0)
        """
        delay = self.delay_gen.thinking_pause(complexity)
        await asyncio.sleep(delay)

    async def blink_pause(self) -> None:
        """Simulate a human blink pause (200-400ms)."""
        delay = self.delay_gen.blink_delay()
        await asyncio.sleep(delay)

    async def read_page(
        self,
        page,
        reading_speed: str | ReadingSpeed = "normal",
        include_scrolling: bool = True,
    ) -> None:
        """
        Simulate reading a page with natural pauses and scrolling.

        Args:
            page: nodriver page object
            reading_speed: ReadingSpeed enum or string ("fast", "normal", "slow")
            include_scrolling: Whether to scroll while reading
        """
        # Normalize reading speed
        if isinstance(reading_speed, str):
            try:
                reading_speed = ReadingSpeed[reading_speed.upper()]
            except KeyError:
                reading_speed = ReadingSpeed.NORMAL

        speed_multiplier = reading_speed.value

        # Initial page assessment
        await self.blink_pause()
        await asyncio.sleep(random.uniform(1.0, 3.0) * speed_multiplier)

        if include_scrolling:
            # Scroll through page naturally
            await self.scroll_naturally(page)

    async def scroll_naturally(
        self,
        page,
        smoothness: Optional[float] = None,
    ) -> None:
        """
        Scroll through a page with natural patterns.

        Args:
            page: nodriver page object
            smoothness: Scroll smoothness (0.1 to 1.0), uses config default if None
        """
        smoothness = smoothness or self.config.scroll_smoothness

        try:
            # Get approximate page height
            viewport_height = await page.evaluate("window.innerHeight")
            scroll_height = await page.evaluate("document.body.scrollHeight")

            if scroll_height <= viewport_height:
                return  # Page doesn't need scrolling

            # Calculate how much to scroll
            total_scroll = scroll_height - viewport_height

            # Get scroll increments
            increments = self.scroll.scroll_increments(
                total_scroll, smoothness=smoothness, include_pauses=True
            )

            # Scroll through page
            for increment in increments:
                if increment > 0:
                    # Scroll by the increment
                    await page.evaluate(f"window.scrollBy(0, {increment})")

                    # Pause for reading
                    dwell_time = self.scroll.dwell_time_for_scroll(
                        increment, self.config.reading_speed
                    )
                    await asyncio.sleep(dwell_time)
                else:
                    # Increment is 0 (pause)
                    await self.random_delay(0.5, 2.0)

        except Exception as e:
            print(f"Error during natural scrolling: {e}")

    async def hover_element(
        self,
        element,
        duration: float = 1.0,
    ) -> None:
        """
        Hover over an element naturally.

        Args:
            element: Element to hover over
            duration: How long to hover in seconds
        """
        try:
            # Check if we should hover based on interaction style
            if not self.interactions.should_hover(self.config.interaction_style):
                return

            # Move to element
            await element.hover()

            # Random dwell time while hovering
            dwell = random.uniform(duration * 0.5, duration * 1.5)
            await asyncio.sleep(dwell)

        except Exception as e:
            print(f"Error hovering element: {e}")

    async def focus_and_interact(self, element) -> None:
        """
        Focus on an element and optionally interact with it.

        Args:
            element: Element to interact with
        """
        try:
            # Hover first if appropriate
            await self.hover_element(element, duration=0.5)

            # Focus the element
            await element.focus()

            # Random pause after focusing
            await self.random_delay(0.1, 0.5)

        except Exception as e:
            print(f"Error focusing element: {e}")

    async def type_with_rhythm(
        self,
        element,
        text: str,
        base_speed: float = 60,
    ) -> None:
        """
        Type text with realistic typing rhythm and variations.

        Args:
            element: Input element to type into
            text: Text to type
            base_speed: Average typing speed in WPM
        """
        try:
            # Focus the element
            await element.focus()
            await self.random_delay(0.1, 0.3)

            # Get keystroke delays
            delays = self.typing.keystroke_delays(text, base_speed, self.config.typing_rhythm_variance)

            # Type each character with varied delays
            for i, (char, delay) in enumerate(zip(text, delays)):
                if char == "\n":
                    await element.press("Enter")
                elif char == "\t":
                    await element.press("Tab")
                else:
                    await element.type(char)

                await asyncio.sleep(delay)

                # Occasional pause for thought
                if random.random() < self.config.pause_probability:
                    await self.thinking_pause(complexity=0.5)

        except Exception as e:
            print(f"Error typing with rhythm: {e}")

    async def switch_tabs(
        self,
        browser,
        count: int = 1,
    ) -> None:
        """
        Simulate switching between browser tabs.

        Args:
            browser: nodriver browser object
            count: Number of tab switches to simulate
        """
        try:
            for _ in range(count):
                # Random delay before switching
                await self.random_delay(1.0, 3.0)

                # In a real implementation, this would use browser tab APIs
                # For now, just simulate the time spent
                await self.random_delay(0.5, 2.0)

        except Exception as e:
            print(f"Error switching tabs: {e}")

    async def varied_interaction_session(
        self,
        page,
        duration: float = 30.0,
    ) -> None:
        """
        Simulate a varied interaction session with multiple activities.

        This demonstrates combining multiple behavior patterns into
        a cohesive, realistic browsing session.

        Args:
            page: nodriver page object
            duration: How long to maintain the session (seconds)
        """
        start_time = asyncio.get_event_loop().time()

        while (asyncio.get_event_loop().time() - start_time) < duration:
            # Random activity choice
            activity = random.choice([
                "read",
                "scroll",
                "hover",
                "pause",
                "refocus",
            ])

            if activity == "read":
                await self.read_page(page, reading_speed="normal")
            elif activity == "scroll":
                await self.scroll_naturally(page)
            elif activity == "hover":
                try:
                    # Try to find and hover over random element
                    elements = await page.find_all("a, button, [role='button']")
                    if elements:
                        element = random.choice(elements)
                        await self.hover_element(element)
                except Exception:
                    pass
            elif activity == "pause":
                await self.thinking_pause()
            elif activity == "refocus":
                await self.random_delay(0.5, 2.0)

            # Check if session should continue
            elapsed = asyncio.get_event_loop().time() - start_time
            if elapsed >= duration:
                break

            # Random delay before next activity
            await self.random_delay(1.0, 3.0)


async def example_human_behavior() -> None:
    """
    Example demonstrating HumanBehavior usage with different configurations.

    This example shows how to use the HumanBehavior class to create
    realistic automation patterns.
    """
    try:
        from quick_start import create_browser, BrowserConfig
    except ImportError:
        print("Error: quick_start module not found.")
        return

    config = BrowserConfig(headless=False)
    browser = await create_browser(config, verbose=True)

    try:
        print("\nNavigating to example page...")
        page = await browser.get("https://example.com")

        # Create behavior instance with normal interaction style
        behavior = HumanBehavior(
            BehaviorConfig(
                reading_speed=1.0,
                interaction_style=InteractionStyle.NORMAL,
            )
        )

        # Example 1: Read a page naturally
        print("\n[Example 1] Reading page naturally")
        print("-" * 50)
        await behavior.read_page(page, reading_speed="normal")

        # Example 2: Varied interaction session
        print("\n[Example 2] Varied interaction session (30 seconds)")
        print("-" * 50)
        await behavior.varied_interaction_session(page, duration=30.0)

        # Example 3: Random delays with natural distribution
        print("\n[Example 3] Random delays")
        print("-" * 50)
        for i in range(5):
            delay = behavior.delay_gen.exponential_delay()
            print(f"Delay {i + 1}: {delay:.2f} seconds")
            await asyncio.sleep(delay)

        print("\nExamples completed!")

    finally:
        await browser.aclose()


def main() -> None:
    """Run examples."""
    print("HumanBehavior - Natural Automation Patterns")
    print("=" * 50)

    try:
        asyncio.run(example_human_behavior())
    except KeyboardInterrupt:
        print("\n\nInterrupted by user")
    except ImportError as e:
        print(f"Error: {e}")


if __name__ == "__main__":
    main()
