# Process Cleanup Utility

Automated detection and cleanup of orphaned browser processes from crashed automation runs.

## Overview

When GEO-Perplex crashes or is forcibly terminated, Chrome/Chromium browser processes may be left running in the background. These orphaned processes can:

- Consume system resources (CPU, memory)
- Hold locks on browser profiles
- Interfere with subsequent automation runs
- Accumulate over time with repeated crashes

The process cleanup utility safely detects and terminates these orphaned browsers while protecting normal user browser sessions.

## Features

### Safety Mechanisms

1. **Automation Detection**: Only targets browsers with automation indicators:
   - `--remote-debugging-port=XXXXX` flag (all automation frameworks)
   - `--disable-blink-features=AutomationControlled` (nodriver-specific)
   - Temporary user-data-dir paths (`/tmp`, `/temp`)
   - Python parent process (launched by automation script)

2. **Graceful Termination**:
   - Sends SIGTERM first for graceful shutdown
   - Waits configurable timeout (default 3s)
   - Escalates to SIGKILL if process doesn't exit

3. **Error Handling**:
   - Handles permission errors gracefully
   - Logs all actions for audit trail
   - Never crashes on unexpected errors

4. **Configuration**:
   - Global enable/disable flag
   - Configurable timeouts
   - Customizable process name patterns

## Usage

### Automatic Cleanup on Startup

Add to your main script:

```python
from src.utils.process_cleanup import cleanup_on_startup

# At application startup
stats = cleanup_on_startup()
if stats['killed'] > 0:
    print(f"Cleaned up {stats['killed']} orphaned browsers")
```

### Manual Cleanup Script

Use the standalone cleanup script:

```bash
# Preview what would be cleaned (safe, recommended first)
python scripts/cleanup_browsers.py --dry-run

# Actually cleanup orphaned browsers
python scripts/cleanup_browsers.py

# Verbose output for debugging
python scripts/cleanup_browsers.py --verbose

# List orphaned browsers without cleaning
python scripts/cleanup_browsers.py --list-only
```

### Programmatic Usage

For custom cleanup workflows:

```python
from src.utils.process_cleanup import find_orphaned_browsers, cleanup_orphaned_browsers

# Find orphaned processes
orphans = find_orphaned_browsers()
print(f"Found {len(orphans)} orphaned browsers")

# Cleanup with custom options
if orphans:
    stats = cleanup_orphaned_browsers(orphans, force=False)
    print(f"Killed: {stats['killed']}, Failed: {stats['failed']}")
```

## Configuration

Edit `src/config.py` to customize behavior:

```python
SHUTDOWN_CONFIG = {
    'browser_kill_timeout': 3.0,        # Graceful termination timeout
    'enable_orphan_cleanup': True,      # Global enable/disable
    'orphan_cleanup_patterns': [        # Process names to detect
        'chrome',
        'chromium',
    ],
}
```

## API Reference

### `cleanup_on_startup(dry_run=False)`

High-level function for startup cleanup.

**Parameters:**
- `dry_run` (bool): If True, only report what would be cleaned

**Returns:**
- Dictionary with cleanup statistics:
  - `killed`: Number of successfully terminated processes
  - `failed`: Number of processes that could not be terminated
  - `total`: Total processes found
  - `would_kill`: (dry_run only) Number that would be killed

**Example:**
```python
stats = cleanup_on_startup()
# {'killed': 2, 'failed': 0, 'total': 2}

stats = cleanup_on_startup(dry_run=True)
# {'would_kill': 2, 'total': 2}
```

### `find_orphaned_browsers()`

Scan for orphaned browser processes.

**Returns:**
- List of `psutil.Process` objects representing orphaned browsers

**Example:**
```python
orphans = find_orphaned_browsers()
for proc in orphans:
    print(f"PID {proc.pid}: {proc.name()}")
```

### `cleanup_orphaned_browsers(processes, force=False)`

Terminate browser processes.

**Parameters:**
- `processes` (List[psutil.Process]): Processes to terminate
- `force` (bool): If True, skip graceful termination and kill immediately

**Returns:**
- Dictionary with cleanup statistics

**Example:**
```python
orphans = find_orphaned_browsers()
stats = cleanup_orphaned_browsers(orphans)
print(f"Cleaned up {stats['killed']} processes")
```

### `is_automation_browser(process)`

Check if a process is an automated browser.

**Parameters:**
- `process` (psutil.Process): Process to check

**Returns:**
- True if automated browser, False otherwise

**Example:**
```python
import psutil
proc = psutil.Process(1234)
if is_automation_browser(proc):
    print("This is an automated browser")
```

## How It Works

### Detection Process

1. **Scan all processes** using `psutil.process_iter()`
2. **Filter by name** using patterns from config (chrome, chromium)
3. **Check automation indicators**:
   - Remote debugging port in cmdline
   - Automation-specific flags
   - Temporary profile directory
   - Python parent process
4. **Return matching processes** as orphaned list

### Termination Process

1. **Log process details** (PID, name, cmdline snippet)
2. **Send SIGTERM** (graceful shutdown signal)
3. **Wait for exit** (default 3 seconds)
4. **Check if running**:
   - If exited: Count as success
   - If still running: Send SIGKILL (force kill)
5. **Verify termination** and update statistics
6. **Handle errors**:
   - NoSuchProcess: Already gone (success)
   - AccessDenied: Permission error (failure)
   - TimeoutExpired: Graceful timeout (escalate to kill)

### Safety Features

**Process Name Filtering**:
```python
# Only checks chrome/chromium, ignores firefox, etc.
patterns = ['chrome', 'chromium']
matches = any(pattern in proc.name().lower() for pattern in patterns)
```

**Automation Detection**:
```python
# Requires automation indicators
cmdline = proc.cmdline()
has_debug_port = '--remote-debugging-port=' in ' '.join(cmdline)
has_automation_flag = '--disable-blink-features=AutomationControlled' in cmdline
is_python_child = proc.parent().name() == 'python'
```

**Graceful Before Force**:
```python
proc.terminate()  # SIGTERM (graceful)
proc.wait(timeout=3.0)
if proc.is_running():
    proc.kill()  # SIGKILL (force)
```

## Logging

The utility logs detailed information at different levels:

**DEBUG**: Technical details
- Process command lines
- Automation indicator checks
- Timing and status updates

**INFO**: User-facing progress
- Scan results
- Cleanup statistics
- Success messages

**WARNING**: Non-fatal issues
- Permission denied
- Graceful termination timeouts
- Partial failures

**ERROR**: Failures
- Unexpected errors
- Access denied on critical operations

**Example log output:**
```
2025-01-13 10:30:00 - src.utils.process_cleanup - INFO - Starting orphaned browser cleanup check
2025-01-13 10:30:00 - src.utils.process_cleanup - INFO - Found 2 orphaned automation browser(s)
2025-01-13 10:30:00 - src.utils.process_cleanup - INFO - Terminating process 1234 (chrome): /usr/bin/chrome --remote-debugging-port=9222...
2025-01-13 10:30:01 - src.utils.process_cleanup - INFO - Process 1234 terminated gracefully
2025-01-13 10:30:01 - src.utils.process_cleanup - INFO - Successfully cleaned up 2 orphaned browser process(es)
```

## Testing

Run the comprehensive test suite:

```bash
# All tests
pytest tests/test_process_cleanup.py -v

# Specific test class
pytest tests/test_process_cleanup.py::TestIsAutomationBrowser -v

# With coverage
pytest tests/test_process_cleanup.py --cov=src.utils.process_cleanup
```

**Test Coverage**:
- Unit tests for all functions
- Edge cases (permission errors, race conditions)
- Integration test with real processes (safe, read-only)
- Mock-based tests for cleanup operations

## Troubleshooting

### "Access denied when terminating process"

**Cause**: Insufficient permissions to kill the process

**Solutions**:
1. Run script with sudo/admin privileges
2. Process may be owned by different user
3. Check system security policies

### "No orphaned browsers found" but they exist

**Cause**: Browsers not detected as automation instances

**Solutions**:
1. Check if browsers have automation indicators
2. Run with `--verbose` to see detection logic
3. Use `--list-only` to see what's detected
4. Manually check process cmdline

### Cleanup fails silently

**Cause**: Cleanup disabled in config

**Solutions**:
1. Check `SHUTDOWN_CONFIG['enable_orphan_cleanup']` is True
2. Verify configuration loaded correctly
3. Enable verbose logging for details

## Best Practices

1. **Always test with --dry-run first**
   ```bash
   python scripts/cleanup_browsers.py --dry-run
   ```

2. **Enable verbose logging when debugging**
   ```python
   import logging
   logging.getLogger('src.utils.process_cleanup').setLevel(logging.DEBUG)
   ```

3. **Add to startup routine**
   ```python
   # In main application
   from src.utils.process_cleanup import cleanup_on_startup

   stats = cleanup_on_startup()
   logger.info(f"Startup cleanup: {stats}")
   ```

4. **Monitor cleanup statistics**
   ```python
   stats = cleanup_on_startup()
   if stats['failed'] > 0:
       logger.warning(f"Failed to clean {stats['failed']} processes")
   ```

5. **Use configuration for environment-specific settings**
   ```python
   # Development: shorter timeout, more verbose
   SHUTDOWN_CONFIG['browser_kill_timeout'] = 1.0

   # Production: longer timeout, more conservative
   SHUTDOWN_CONFIG['browser_kill_timeout'] = 5.0
   ```

## Dependencies

- **psutil** >= 5.9.0: Cross-platform process and system utilities
  ```bash
  pip install psutil
  ```

## Platform Support

- **Linux**: Full support
- **macOS**: Full support
- **Windows**: Full support (with some command line differences)

Process signals:
- Linux/macOS: SIGTERM (15), SIGKILL (9)
- Windows: TerminateProcess (closest equivalent)

## Security Considerations

1. **Privilege Escalation**: Script should run with minimum required privileges
2. **Audit Trail**: All actions are logged for security review
3. **User Confirmation**: Dry-run mode allows verification before cleanup
4. **Error Recovery**: Graceful handling of permission errors prevents security issues

## Future Enhancements

Potential improvements:

- [ ] Age-based filtering (only kill old processes)
- [ ] Interactive mode with confirmation prompts
- [ ] Support for other automation browsers (Edge, Firefox)
- [ ] Process tree cleanup (kill child processes)
- [ ] Scheduled cleanup via cron/systemd timer
- [ ] Metrics collection (cleanup success rates)
- [ ] Integration with system monitoring tools

## License

Same license as GEO-Perplex project.
