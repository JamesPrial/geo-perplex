#!/usr/bin/env python3
"""
Example: Integrating process cleanup into your automation workflow.

This example demonstrates how to add orphaned browser cleanup to the
GEO-Perplex search automation workflow for robust error recovery.

Use Cases:
- Run cleanup on application startup
- Cleanup after crashes or interruptions
- Scheduled cleanup in long-running automation
- Integration with CI/CD pipelines
"""

import sys
import logging
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.utils.process_cleanup import cleanup_on_startup


def example_1_basic_startup_cleanup():
    """
    Example 1: Basic startup cleanup (recommended for all scripts).

    Add this to the beginning of your main automation script to ensure
    clean state before starting new browser automation.
    """
    print("=== Example 1: Basic Startup Cleanup ===\n")

    # Simple cleanup at startup
    stats = cleanup_on_startup()

    if stats['killed'] > 0:
        print(f"✓ Cleaned up {stats['killed']} orphaned browser(s)")
    else:
        print("✓ No orphaned browsers found")

    print()


def example_2_dry_run_before_cleanup():
    """
    Example 2: Preview before cleanup (safe testing).

    Use dry-run mode to see what would be cleaned before actually
    terminating processes. Useful for testing and debugging.
    """
    print("=== Example 2: Dry Run Before Cleanup ===\n")

    # First, preview what would be cleaned
    print("Previewing cleanup (dry run)...")
    stats = cleanup_on_startup(dry_run=True)

    if stats.get('would_kill', 0) > 0:
        print(f"Would clean up {stats['would_kill']} orphaned browser(s)")

        # Ask for confirmation (in real script)
        # response = input("Proceed with cleanup? (y/n): ")
        # if response.lower() == 'y':
        #     stats = cleanup_on_startup()
        #     print(f"✓ Cleaned up {stats['killed']} browsers")

        print("(Skipping actual cleanup in example)")
    else:
        print("No orphaned browsers found")

    print()


def example_3_integration_with_error_handling():
    """
    Example 3: Integration with error handling and logging.

    Shows how to properly integrate cleanup with comprehensive
    error handling and logging for production use.
    """
    print("=== Example 3: Integration with Error Handling ===\n")

    logger = logging.getLogger(__name__)

    try:
        # Startup cleanup
        logger.info("Running startup cleanup...")
        stats = cleanup_on_startup()

        # Log results
        if stats['total'] > 0:
            if stats['failed'] > 0:
                logger.warning(
                    f"Partial cleanup: {stats['killed']} killed, "
                    f"{stats['failed']} failed"
                )
            else:
                logger.info(f"Successfully cleaned up {stats['killed']} orphaned browser(s)")

        # Your main automation code here
        print("✓ Ready to start automation (cleanup complete)")

    except Exception as e:
        logger.error(f"Startup cleanup failed: {e}", exc_info=True)
        # Decide whether to continue or abort
        print("⚠ Cleanup failed but continuing anyway...")

    print()


def example_4_conditional_cleanup():
    """
    Example 4: Conditional cleanup based on configuration.

    Shows how to make cleanup optional based on environment
    or configuration settings.
    """
    print("=== Example 4: Conditional Cleanup ===\n")

    from src.config import SHUTDOWN_CONFIG

    # Check if cleanup is enabled
    if SHUTDOWN_CONFIG.get('enable_orphan_cleanup', True):
        print("Cleanup enabled in config, running...")
        stats = cleanup_on_startup()
        print(f"✓ Cleanup complete: {stats['killed']} killed, {stats['failed']} failed")
    else:
        print("Cleanup disabled in config, skipping...")

    print()


def example_5_custom_cleanup_logic():
    """
    Example 5: Custom cleanup logic with manual control.

    Shows how to use lower-level functions for custom cleanup
    workflows (e.g., age-based cleanup, selective termination).
    """
    print("=== Example 5: Custom Cleanup Logic ===\n")

    from src.utils.process_cleanup import find_orphaned_browsers, cleanup_orphaned_browsers

    # Find orphaned browsers
    orphans = find_orphaned_browsers()
    print(f"Found {len(orphans)} orphaned browser(s)")

    if orphans:
        # Custom filtering logic (example)
        # In real code, you might filter by process age, memory usage, etc.
        print("\nOrphaned browsers:")
        for proc in orphans:
            try:
                cmdline = ' '.join(proc.cmdline())[:60]
                print(f"  - PID {proc.pid}: {cmdline}...")
            except Exception:
                print(f"  - PID {proc.pid}: [cmdline unavailable]")

        # Cleanup with custom options
        print("\nCleaning up...")
        stats = cleanup_orphaned_browsers(orphans, force=False)
        print(f"✓ Done: {stats['killed']} killed, {stats['failed']} failed")
    else:
        print("No orphaned browsers to clean up")

    print()


def example_6_scheduled_cleanup():
    """
    Example 6: Scheduled cleanup in long-running automation.

    Shows how to periodically cleanup during long-running
    automation sessions (e.g., continuous monitoring).
    """
    print("=== Example 6: Scheduled Cleanup ===\n")

    import time

    # Simulated long-running automation
    print("Starting long-running automation...")

    # Initial cleanup
    stats = cleanup_on_startup()
    print(f"Initial cleanup: {stats['killed']} killed")

    # Simulated work with periodic cleanup
    for iteration in range(3):
        print(f"\nIteration {iteration + 1}...")

        # Your automation work here
        time.sleep(1)  # Simulated work

        # Periodic cleanup (e.g., every N iterations)
        if (iteration + 1) % 2 == 0:  # Every 2 iterations
            print("Running periodic cleanup...")
            stats = cleanup_on_startup()
            if stats['killed'] > 0:
                print(f"  Cleaned up {stats['killed']} orphaned browser(s)")

    print("\n✓ Automation complete")
    print()


def main():
    """Run all examples."""
    # Setup logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(levelname)s: %(message)s'
    )

    print("=" * 60)
    print("Process Cleanup Integration Examples")
    print("=" * 60)
    print()

    # Run examples
    example_1_basic_startup_cleanup()
    example_2_dry_run_before_cleanup()
    example_3_integration_with_error_handling()
    example_4_conditional_cleanup()
    example_5_custom_cleanup_logic()
    example_6_scheduled_cleanup()

    print("=" * 60)
    print("Examples complete!")
    print("=" * 60)


if __name__ == '__main__':
    main()
