#!/usr/bin/env python3
"""
Test script demonstrating ElementWaiter capabilities.

This script shows how to use the ElementWaiter class for intelligent
waiting in browser automation.
"""
import asyncio
from src.browser.element_waiter import ElementWaiter, WaitResult, WaitCondition


def print_wait_result(result: WaitResult, description: str):
    """Pretty print a WaitResult."""
    status = "✓ SUCCESS" if result.success else "✗ FAILED"
    print(f"\n{description}")
    print(f"  Status: {status}")
    print(f"  Wait time: {result.wait_time:.2f}s")
    print(f"  Attempts: {result.attempts}")
    if result.condition_met:
        print(f"  Condition: {result.condition_met.value}")
    if result.error:
        print(f"  Error: {result.error}")


async def demo():
    """
    Demonstrate ElementWaiter usage patterns.

    Note: This is a demonstration of the API. For actual testing,
    you would need a real nodriver page object.
    """
    print("=" * 70)
    print("ElementWaiter - Intelligent Waiting System for Nodriver")
    print("=" * 70)

    print("\n📚 Available Wait Conditions:\n")
    for condition in WaitCondition:
        print(f"  • {condition.value}: {condition.name}")

    print("\n" + "=" * 70)
    print("Usage Examples")
    print("=" * 70)

    print("\n1. Wait for Element Presence:")
    print("""
    waiter = ElementWaiter(page)
    result = await waiter.wait_for_presence('#button', timeout=10)
    if result.success:
        print(f'Element found after {result.wait_time:.2f}s')
        await result.element.click()
    """)

    print("\n2. Wait for Element Visibility:")
    print("""
    result = await waiter.wait_for_visibility('.modal', timeout=5)
    if result.success:
        print('Modal is now visible')
    """)

    print("\n3. Wait for Element Clickability:")
    print("""
    result = await waiter.wait_for_clickable('button[type=submit]', timeout=10)
    if result.success:
        await result.element.click()  # Safe to click now
    """)

    print("\n4. Wait for Text Content:")
    print("""
    # Partial match (default)
    result = await waiter.wait_for_text('main', 'ask a follow-up',
                                        partial=True, timeout=30)
    if result.success:
        print('Answer completion detected!')

    # Exact match
    result = await waiter.wait_for_text('#status', 'Complete',
                                        partial=False, timeout=10)
    """)

    print("\n5. Wait for Content Stability:")
    print("""
    # Wait for dynamic content to stop changing
    result = await waiter.wait_for_stable('main', timeout=30,
                                          stable_threshold=3,
                                          min_content_length=50)
    if result.success:
        print(f'Content stable after {result.wait_time:.2f}s')
        # Safe to extract now
        content = result.element.text_all
    """)

    print("\n" + "=" * 70)
    print("WaitResult Structure")
    print("=" * 70)
    print("""
    @dataclass
    class WaitResult:
        success: bool              # Whether condition was met
        element: Optional[Any]     # The element (if found)
        wait_time: float          # Time spent waiting (seconds)
        attempts: int             # Number of polling attempts
        condition_met: WaitCondition  # Which condition was satisfied
        error: Optional[str]      # Error message (if failed)
    """)

    print("\n" + "=" * 70)
    print("Integration with Extraction")
    print("=" * 70)
    print("""
    # Example: Wait for answer completion in extractor.py

    waiter = ElementWaiter(page, poll_interval=0.1)

    # Primary: Wait for "ask a follow-up" text
    result = await waiter.wait_for_text(
        'main', 'ask a follow-up', partial=True, timeout=30
    )

    if result.success:
        logger.info(f'Answer completed after {result.wait_time:.2f}s')
    else:
        # Fallback: Use stability detection
        result = await waiter.wait_for_stable('main', timeout=30)
        if not result.success:
            logger.warning('Content stability timeout')
    """)

    print("\n" + "=" * 70)
    print("Configuration")
    print("=" * 70)
    print("""
    ElementWaiter(
        page,                  # Nodriver page object
        poll_interval=0.1,     # Time between checks (seconds)
        verbose=False          # Enable detailed logging
    )

    # All wait methods support custom timeouts:
    await waiter.wait_for_presence(selector, timeout=10.0)
    await waiter.wait_for_visibility(selector, timeout=5.0)
    await waiter.wait_for_clickable(selector, timeout=15.0)
    await waiter.wait_for_text(selector, text, timeout=30.0)
    await waiter.wait_for_stable(selector, timeout=45.0)
    """)

    print("\n" + "=" * 70)
    print("Benefits")
    print("=" * 70)
    print("""
    ✓ Replaces arbitrary asyncio.sleep() calls with intelligent polling
    ✓ Provides detailed result information for debugging
    ✓ Supports multiple wait conditions in one system
    ✓ Handles timeouts gracefully without exceptions
    ✓ Polls efficiently (0.1s intervals by default)
    ✓ Returns elements ready for immediate interaction
    ✓ Tracks timing and attempt counts for performance analysis
    """)

    print("\n" + "=" * 70)


if __name__ == "__main__":
    asyncio.run(demo())
