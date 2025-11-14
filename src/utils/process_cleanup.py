"""
Process cleanup utility for detecting and terminating orphaned browser processes.

This module provides safe detection and cleanup of Chrome/Chromium processes that were
left running from previous crashed GEO-Perplex automation runs. It carefully distinguishes
between automated browser instances and the user's normal browser sessions to prevent
accidental termination of legitimate browsers.

SAFETY FEATURES:
- Only terminates processes with automation indicators (remote debugging port, etc.)
- Never kills user's normal browser sessions
- Graceful termination with SIGTERM before forcing SIGKILL
- Comprehensive error handling for permission issues
- Detailed logging of all actions for audit trail
- Dry-run mode for safe testing
- Configurable via SHUTDOWN_CONFIG in src.config

TYPICAL USAGE:
    # Safe startup cleanup (recommended)
    from src.utils.process_cleanup import cleanup_on_startup

    stats = cleanup_on_startup()
    # Output: "Cleaned up 2 orphaned browser processes"

    # Dry run to preview what would be cleaned
    stats = cleanup_on_startup(dry_run=True)
    # Output: "Would kill 2 orphaned browsers (dry run)"

    # Manual cleanup with custom process list
    from src.utils.process_cleanup import find_orphaned_browsers, cleanup_orphaned_browsers

    orphans = find_orphaned_browsers()
    if orphans:
        stats = cleanup_orphaned_browsers(orphans)
        print(f"Cleaned up {stats['killed']} processes")

AUTOMATION DETECTION:
The module identifies automated browsers by checking for these indicators:
- --remote-debugging-port=XXXXX command line argument (all nodriver browsers)
- --disable-blink-features=AutomationControlled (nodriver-specific flag)
- --user-data-dir with temporary directory paths (automation profiles)
- Parent process is Python interpreter (launched by automation script)

PROCESS STATES HANDLED:
- Running processes: Gracefully terminated then force-killed if needed
- Zombie processes: Detected and skipped (already terminating)
- Missing processes: Handled gracefully (race condition)
- Access denied: Logged as error, counted as failed

CONFIGURATION:
All timeouts and settings are loaded from src.config.SHUTDOWN_CONFIG:
- browser_kill_timeout: Graceful termination timeout (default 3.0s)
- enable_orphan_cleanup: Global enable/disable flag (default True)
- orphan_cleanup_patterns: Process names to detect (default ['chrome', 'chromium'])
"""

import logging
import time
from typing import List, Dict, Optional

try:
    import psutil
except ImportError:
    raise ImportError(
        "psutil is required for process cleanup. Install with: pip install psutil"
    )

from src.config import SHUTDOWN_CONFIG

# Module logger
logger = logging.getLogger(__name__)


def is_automation_browser(process: psutil.Process) -> bool:
    """
    Determine if a browser process is an automated/nodriver browser.

    Checks command line arguments for indicators that distinguish automated
    browsers from normal user browser sessions. This prevents accidental
    termination of legitimate browsers.

    Automation Indicators:
    - --remote-debugging-port=XXXXX (all automation frameworks)
    - --disable-blink-features=AutomationControlled (nodriver specific)
    - --user-data-dir with 'tmp' or 'temp' in path (temporary profiles)
    - Parent process is Python (launched by automation script)

    Args:
        process: psutil.Process object to check

    Returns:
        True if process is an automated browser, False otherwise

    Error Handling:
        Returns False if cmdline cannot be accessed (permission denied)
        or if process no longer exists (race condition).

    Examples:
        >>> import psutil
        >>> proc = psutil.Process(1234)
        >>> if is_automation_browser(proc):
        ...     print("This is an automated browser")
    """
    try:
        # Get command line arguments
        cmdline = process.cmdline()
        cmdline_str = ' '.join(cmdline).lower()

        # Check for remote debugging port (strongest indicator)
        if '--remote-debugging-port=' in cmdline_str:
            logger.debug(
                f"Process {process.pid} has remote debugging port - automated browser"
            )
            return True

        # Check for automation-specific flags
        if '--disable-blink-features=automationcontrolled' in cmdline_str:
            logger.debug(
                f"Process {process.pid} has automation flags - nodriver browser"
            )
            return True

        # Check for temporary user data directory (automation profiles)
        if '--user-data-dir' in cmdline_str:
            # Look for temp directory indicators in the path
            if any(temp_marker in cmdline_str for temp_marker in ['tmp', 'temp', '/t/']):
                logger.debug(
                    f"Process {process.pid} uses temp user-data-dir - automated browser"
                )
                return True

        # Check if parent process is Python (launched by our script)
        try:
            parent = psutil.Process(process.ppid())
            parent_name = parent.name().lower()
            if 'python' in parent_name:
                logger.debug(
                    f"Process {process.pid} has Python parent ({parent_name}) - likely automated"
                )
                return True
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            # Parent process might be gone or inaccessible
            pass

        # No automation indicators found
        logger.debug(
            f"Process {process.pid} has no automation indicators - normal browser"
        )
        return False

    except psutil.AccessDenied:
        # Cannot read process cmdline - assume not automation for safety
        logger.debug(
            f"Cannot access cmdline for process {process.pid} - assuming not automated"
        )
        return False

    except psutil.NoSuchProcess:
        # Process disappeared during check - race condition
        logger.debug(
            f"Process {process.pid} no longer exists during automation check"
        )
        return False

    except Exception as e:
        # Unexpected error - log and assume not automation for safety
        logger.warning(
            f"Unexpected error checking process {process.pid}: {e}"
        )
        return False


def find_orphaned_browsers() -> List[psutil.Process]:
    """
    Find orphaned Chrome/Chromium processes from previous crashed runs.

    Scans all running processes to identify browser instances that were likely
    launched by GEO-Perplex automation but left running after a crash. Uses
    multiple criteria to distinguish automated browsers from normal user sessions.

    Detection Strategy:
    1. Filter processes by name (chrome, chromium) from SHUTDOWN_CONFIG
    2. Check each process for automation indicators via is_automation_browser()
    3. Return only processes that appear to be orphaned automation instances

    Returns:
        List of psutil.Process objects representing orphaned automation browsers.
        Empty list if none found.

    Error Handling:
        Catches and logs permission errors, zombie processes, and terminated processes.
        These are silently skipped to avoid disrupting the scan.

    Configuration:
        Uses SHUTDOWN_CONFIG['orphan_cleanup_patterns'] for process names.
        Default patterns: ['chrome', 'chromium']

    Examples:
        >>> orphans = find_orphaned_browsers()
        >>> print(f"Found {len(orphans)} orphaned browsers")
        Found 2 orphaned browsers

        >>> for proc in orphans:
        ...     print(f"PID {proc.pid}: {proc.name()}")
        PID 1234: chrome
        PID 5678: chrome
    """
    orphaned = []
    patterns = SHUTDOWN_CONFIG.get('orphan_cleanup_patterns', ['chrome', 'chromium'])

    logger.debug(f"Scanning for orphaned browsers matching patterns: {patterns}")

    # Iterate through all running processes
    for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
        try:
            # Get process name and normalize to lowercase
            proc_name = proc.info['name']
            if proc_name is None:
                continue

            proc_name_lower = proc_name.lower()

            # Check if process name matches our patterns
            matches_pattern = any(
                pattern.lower() in proc_name_lower
                for pattern in patterns
            )

            if not matches_pattern:
                continue

            logger.debug(f"Found browser process: PID {proc.pid}, name {proc_name}")

            # Check if this is an automation browser
            if is_automation_browser(proc):
                logger.debug(f"Identified orphaned automation browser: PID {proc.pid}")
                orphaned.append(proc)

        except psutil.NoSuchProcess:
            # Process terminated during iteration - ignore
            pass

        except psutil.AccessDenied:
            # Cannot access process info (permission issue) - log warning
            logger.warning(
                f"Access denied when checking process {proc.pid} - skipping"
            )

        except psutil.ZombieProcess:
            # Zombie process - already terminating, ignore
            logger.debug(f"Skipping zombie process {proc.pid}")

        except Exception as e:
            # Unexpected error - log and continue
            logger.warning(
                f"Unexpected error checking process {proc.pid}: {e}"
            )

    logger.info(f"Found {len(orphaned)} orphaned automation browser(s)")
    return orphaned


def cleanup_orphaned_browsers(
    processes: List[psutil.Process],
    force: bool = False
) -> Dict[str, int]:
    """
    Terminate orphaned browser processes gracefully with force kill fallback.

    Attempts to cleanly terminate browser processes using SIGTERM first, then
    escalates to SIGKILL if graceful termination fails. Tracks success/failure
    statistics for all termination attempts.

    Termination Strategy:
    1. Log process details (PID, name, command line snippet)
    2. If not force mode: Send SIGTERM and wait for graceful exit
    3. If still running or force mode: Send SIGKILL to force termination
    4. Verify process is gone and update statistics

    Args:
        processes: List of psutil.Process objects to terminate
        force: If True, skip graceful termination and kill immediately
               Default False for safety

    Returns:
        Dictionary with termination statistics:
        - 'killed': Number of successfully terminated processes
        - 'failed': Number of processes that could not be terminated
        - 'total': Total number of processes attempted

    Error Handling:
        - NoSuchProcess: Process already gone (counts as success)
        - AccessDenied: Permission error (counts as failure)
        - TimeoutExpired: Graceful termination timeout (proceeds to force kill)
        - Generic Exception: Unexpected errors (counts as failure)

    Configuration:
        Uses SHUTDOWN_CONFIG['browser_kill_timeout'] for graceful termination timeout.
        Default: 3.0 seconds

    Examples:
        >>> orphans = find_orphaned_browsers()
        >>> stats = cleanup_orphaned_browsers(orphans)
        >>> print(f"Killed: {stats['killed']}, Failed: {stats['failed']}")
        Killed: 2, Failed: 0

        >>> # Force kill without graceful termination
        >>> stats = cleanup_orphaned_browsers(orphans, force=True)
    """
    stats = {
        'killed': 0,
        'failed': 0,
        'total': len(processes)
    }

    if not processes:
        logger.debug("No processes to cleanup")
        return stats

    timeout = SHUTDOWN_CONFIG.get('browser_kill_timeout', 3.0)

    logger.info(
        f"Starting cleanup of {len(processes)} orphaned browser process(es) "
        f"(force={force}, timeout={timeout}s)"
    )

    for proc in processes:
        try:
            # Log process information
            try:
                cmdline = proc.cmdline()
                # Show first 100 chars of cmdline for context
                cmdline_snippet = ' '.join(cmdline)[:100]
                if len(' '.join(cmdline)) > 100:
                    cmdline_snippet += '...'

                logger.info(
                    f"Terminating process {proc.pid} ({proc.name()}): {cmdline_snippet}"
                )
            except (psutil.AccessDenied, psutil.NoSuchProcess):
                logger.info(f"Terminating process {proc.pid} ({proc.name()})")

            # Attempt graceful termination first (unless force=True)
            if not force:
                logger.debug(f"Sending SIGTERM to process {proc.pid}")
                proc.terminate()

                # Wait for graceful exit
                try:
                    proc.wait(timeout=timeout)
                    logger.info(f"Process {proc.pid} terminated gracefully")
                    stats['killed'] += 1
                    continue  # Successfully terminated

                except psutil.TimeoutExpired:
                    logger.warning(
                        f"Process {proc.pid} did not terminate gracefully after {timeout}s"
                    )
                    # Continue to force kill below

            # Force kill if still running or if force=True
            if proc.is_running():
                logger.debug(f"Sending SIGKILL to process {proc.pid}")
                proc.kill()

                # Wait briefly for kill to take effect
                time.sleep(1.0)

                # Verify process is gone
                if not proc.is_running():
                    logger.info(f"Process {proc.pid} force-killed successfully")
                    stats['killed'] += 1
                else:
                    logger.error(f"Process {proc.pid} still running after SIGKILL")
                    stats['failed'] += 1

        except psutil.NoSuchProcess:
            # Process already gone - count as success
            logger.debug(f"Process {proc.pid} already terminated")
            stats['killed'] += 1

        except psutil.AccessDenied:
            # Permission error - count as failure
            logger.error(
                f"Access denied when terminating process {proc.pid} - insufficient permissions"
            )
            stats['failed'] += 1

        except Exception as e:
            # Unexpected error - count as failure
            logger.error(
                f"Unexpected error terminating process {proc.pid}: {e}",
                exc_info=True
            )
            stats['failed'] += 1

    logger.info(
        f"Cleanup complete: {stats['killed']} killed, "
        f"{stats['failed']} failed, {stats['total']} total"
    )

    return stats


def cleanup_on_startup(dry_run: bool = False) -> Dict[str, int]:
    """
    High-level function to find and cleanup orphaned browsers on startup.

    This is the recommended entry point for orphaned browser cleanup. It handles
    the complete workflow: finding orphaned processes, optionally cleaning them up,
    and reporting statistics.

    Workflow:
    1. Check if cleanup is enabled in SHUTDOWN_CONFIG
    2. Scan for orphaned browser processes
    3. If dry_run=True: Report what would be cleaned without actually killing
    4. If dry_run=False: Actually terminate the processes
    5. Log summary statistics

    Args:
        dry_run: If True, only report what would be cleaned without killing.
                Default False (actually perform cleanup).

    Returns:
        Dictionary with cleanup statistics:
        - If dry_run=True: {'would_kill': N, 'total': N}
        - If dry_run=False: {'killed': N, 'failed': N, 'total': N}
        - If no orphans found: {'killed': 0, 'failed': 0, 'total': 0}

    Configuration:
        Respects SHUTDOWN_CONFIG['enable_orphan_cleanup'] setting.
        If disabled, returns empty stats without scanning.

    Examples:
        >>> # Normal startup cleanup
        >>> stats = cleanup_on_startup()
        >>> if stats['killed'] > 0:
        ...     print(f"Cleaned up {stats['killed']} orphaned browsers")
        Cleaned up 2 orphaned browsers

        >>> # Preview mode (no actual cleanup)
        >>> stats = cleanup_on_startup(dry_run=True)
        >>> print(f"Would kill {stats['would_kill']} orphaned browsers")
        Would kill 2 orphaned browsers
    """
    # Check if cleanup is enabled
    if not SHUTDOWN_CONFIG.get('enable_orphan_cleanup', True):
        logger.info("Orphaned browser cleanup is disabled in configuration")
        return {'killed': 0, 'failed': 0, 'total': 0}

    logger.info("Starting orphaned browser cleanup check")

    # Find orphaned processes
    orphaned = find_orphaned_browsers()

    # No orphans found
    if not orphaned:
        logger.info("No orphaned browser processes found")
        return {'killed': 0, 'failed': 0, 'total': 0}

    # Dry run mode - report what would be done
    if dry_run:
        logger.info(
            f"DRY RUN: Would terminate {len(orphaned)} orphaned browser process(es)"
        )
        for proc in orphaned:
            try:
                cmdline = ' '.join(proc.cmdline())[:100]
                logger.info(f"  - PID {proc.pid} ({proc.name()}): {cmdline}...")
            except (psutil.AccessDenied, psutil.NoSuchProcess):
                logger.info(f"  - PID {proc.pid} ({proc.name()})")

        return {
            'would_kill': len(orphaned),
            'total': len(orphaned)
        }

    # Actually perform cleanup
    logger.info(f"Terminating {len(orphaned)} orphaned browser process(es)")
    stats = cleanup_orphaned_browsers(orphaned)

    # Log summary
    if stats['failed'] > 0:
        logger.warning(
            f"Cleanup completed with errors: {stats['killed']} killed, "
            f"{stats['failed']} failed"
        )
    else:
        logger.info(
            f"Successfully cleaned up {stats['killed']} orphaned browser process(es)"
        )

    return stats
