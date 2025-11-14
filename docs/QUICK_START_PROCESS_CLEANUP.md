# Quick Start: Process Cleanup

Get started with the orphaned browser process cleanup utility in 5 minutes.

## What It Does

Automatically detects and terminates Chrome/Chromium browser processes left running from crashed GEO-Perplex automation runs, while safely protecting your normal browser sessions.

## Quick Start

### 1. Install Dependencies

```bash
pip install psutil>=5.9.0
```

### 2. Basic Usage (Recommended)

Add to the beginning of your automation scripts:

```python
from src.utils.process_cleanup import cleanup_on_startup

# At application startup
stats = cleanup_on_startup()
if stats['killed'] > 0:
    print(f"Cleaned up {stats['killed']} orphaned browsers")
```

That's it! The utility will:
- ✓ Scan for orphaned automation browsers
- ✓ Terminate them gracefully (SIGTERM → SIGKILL)
- ✓ Protect normal user browser sessions
- ✓ Return statistics about what was cleaned

### 3. Standalone Cleanup

Clean up orphaned browsers manually:

```bash
# Preview what would be cleaned (safe!)
python scripts/cleanup_browsers.py --dry-run

# Actually cleanup orphaned browsers
python scripts/cleanup_browsers.py
```

## Safety Features

**The utility ONLY kills browsers with automation indicators:**
- `--remote-debugging-port=XXXXX` flag
- `--disable-blink-features=AutomationControlled` flag
- Temporary user-data-dir (`/tmp`, `/temp`)
- Python parent process

**Your normal browser sessions are NEVER touched.**

## Common Scenarios

### Scenario 1: Automation Keeps Crashing

Add cleanup to startup to ensure clean state:

```python
from src.utils.process_cleanup import cleanup_on_startup

def main():
    # Always start clean
    cleanup_on_startup()

    # Your automation code
    run_automation()
```

### Scenario 2: Multiple Browser Instances Accumulating

Run manual cleanup periodically:

```bash
# Quick cleanup
python scripts/cleanup_browsers.py

# Check first, then cleanup
python scripts/cleanup_browsers.py --dry-run
python scripts/cleanup_browsers.py
```

### Scenario 3: Long-Running Automation

Add periodic cleanup:

```python
from src.utils.process_cleanup import cleanup_on_startup

# Initial cleanup
cleanup_on_startup()

# Run automation loop
for iteration in range(100):
    run_search()

    # Cleanup every 10 iterations
    if iteration % 10 == 0:
        cleanup_on_startup()
```

## Configuration

Edit `src/config.py` if needed:

```python
SHUTDOWN_CONFIG = {
    'browser_kill_timeout': 3.0,          # How long to wait for graceful exit
    'enable_orphan_cleanup': True,        # Enable/disable globally
    'orphan_cleanup_patterns': [          # Which browser names to check
        'chrome',
        'chromium',
    ],
}
```

## Validation

Verify everything is working:

```bash
# Run validation script
python scripts/validate_process_cleanup.py

# Run tests
pytest tests/test_process_cleanup.py -v
```

## Troubleshooting

### "Access denied when terminating process"

Run with sudo/admin privileges, or the process may be owned by another user.

### "No orphaned browsers found" but they exist

The browsers might not have automation indicators. Run with verbose logging:

```bash
python scripts/cleanup_browsers.py --list-only --verbose
```

### Cleanup seems disabled

Check configuration:

```python
from src.config import SHUTDOWN_CONFIG
print(SHUTDOWN_CONFIG['enable_orphan_cleanup'])  # Should be True
```

## Next Steps

- **Full Documentation**: See `/docs/process_cleanup.md`
- **Integration Examples**: Run `python examples/cleanup_integration.py`
- **API Reference**: See documentation for all functions
- **Testing**: Run `pytest tests/test_process_cleanup.py -v`

## Support

For issues or questions:
1. Check the full documentation: `/docs/process_cleanup.md`
2. Review examples: `python examples/cleanup_integration.py`
3. Run validation: `python scripts/validate_process_cleanup.py`

## Summary

**Three ways to use process cleanup:**

1. **Automatic** (recommended): Add `cleanup_on_startup()` to your scripts
2. **Manual**: Run `python scripts/cleanup_browsers.py`
3. **Custom**: Use low-level functions for advanced workflows

**Remember**: Always safe to run - only kills automation browsers, never normal browsers!
