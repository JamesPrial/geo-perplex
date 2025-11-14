#!/usr/bin/env python3
"""
Standalone script to cleanup orphaned browser processes.

This script provides a command-line interface to the process cleanup utility,
allowing manual cleanup of orphaned Chrome/Chromium processes from crashed runs.

Usage:
    # Preview what would be cleaned (safe, recommended first)
    python scripts/cleanup_browsers.py --dry-run

    # Actually cleanup orphaned browsers
    python scripts/cleanup_browsers.py

    # Force kill without graceful termination
    python scripts/cleanup_browsers.py --force

    # Verbose output
    python scripts/cleanup_browsers.py --verbose

Safety:
    - Only kills processes with automation indicators
    - Never kills normal user browser sessions
    - Dry-run mode available for testing
    - Detailed logging of all actions
"""

import sys
import logging
import argparse
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.utils.process_cleanup import cleanup_on_startup, find_orphaned_browsers
from src.config import SHUTDOWN_CONFIG


def setup_logging(verbose: bool = False) -> None:
    """Configure logging for the script."""
    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(
        level=level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )


def main() -> int:
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description='Cleanup orphaned browser processes from crashed automation runs',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__
    )
    parser.add_argument(
        '--dry-run',
        action='store_true',
        help='Preview what would be cleaned without actually killing processes'
    )
    parser.add_argument(
        '--force',
        action='store_true',
        help='Force kill immediately without graceful termination'
    )
    parser.add_argument(
        '--verbose', '-v',
        action='store_true',
        help='Enable verbose debug logging'
    )
    parser.add_argument(
        '--list-only',
        action='store_true',
        help='Only list orphaned browsers without cleaning'
    )

    args = parser.parse_args()

    # Setup logging
    setup_logging(args.verbose)
    logger = logging.getLogger(__name__)

    # Check if cleanup is enabled
    if not SHUTDOWN_CONFIG.get('enable_orphan_cleanup', True):
        logger.error('Orphaned browser cleanup is disabled in configuration')
        logger.error('Set SHUTDOWN_CONFIG["enable_orphan_cleanup"] = True to enable')
        return 1

    # List mode
    if args.list_only:
        logger.info('Scanning for orphaned browser processes...')
        orphans = find_orphaned_browsers()

        if not orphans:
            logger.info('No orphaned browser processes found')
            return 0

        logger.info(f'Found {len(orphans)} orphaned browser process(es):')
        for proc in orphans:
            try:
                cmdline = ' '.join(proc.cmdline())[:100]
                print(f'  PID {proc.pid} ({proc.name()}): {cmdline}...')
            except Exception as e:
                print(f'  PID {proc.pid} ({proc.name()}): [cmdline unavailable]')

        return 0

    # Cleanup mode
    try:
        stats = cleanup_on_startup(dry_run=args.dry_run)

        if stats['total'] == 0:
            logger.info('No orphaned browser processes found')
            return 0

        if args.dry_run:
            print(f"\nDry Run Summary:")
            print(f"  Would clean: {stats.get('would_kill', 0)} process(es)")
            print(f"  Total found: {stats['total']}")
            print(f"\nRun without --dry-run to actually cleanup")
            return 0

        # Actual cleanup results
        print(f"\nCleanup Summary:")
        print(f"  Successfully killed: {stats['killed']}")
        print(f"  Failed: {stats['failed']}")
        print(f"  Total: {stats['total']}")

        if stats['failed'] > 0:
            logger.warning('Some processes could not be terminated (check permissions)')
            return 2

        logger.info('Cleanup completed successfully')
        return 0

    except KeyboardInterrupt:
        logger.info('Cleanup cancelled by user')
        return 130

    except Exception as e:
        logger.error(f'Unexpected error during cleanup: {e}', exc_info=True)
        return 1


if __name__ == '__main__':
    sys.exit(main())
