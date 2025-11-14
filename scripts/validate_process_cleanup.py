#!/usr/bin/env python3
"""
Validation script for process cleanup implementation.

Runs a series of checks to verify the process cleanup utility is working
correctly and all components are properly integrated.

Usage:
    python scripts/validate_process_cleanup.py
"""

import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))


def validate_imports():
    """Validate all imports work correctly."""
    print("✓ Validating imports...")
    try:
        from src.utils.process_cleanup import (
            cleanup_on_startup,
            find_orphaned_browsers,
            cleanup_orphaned_browsers,
            is_automation_browser,
        )
        from src.config import SHUTDOWN_CONFIG
        import psutil
        print("  ✓ All imports successful")
        return True
    except ImportError as e:
        print(f"  ✗ Import failed: {e}")
        return False


def validate_configuration():
    """Validate configuration is properly set up."""
    print("\n✓ Validating configuration...")
    try:
        from src.config import SHUTDOWN_CONFIG

        # Check required keys exist
        required_keys = [
            'browser_kill_timeout',
            'enable_orphan_cleanup',
            'orphan_cleanup_patterns'
        ]

        for key in required_keys:
            if key not in SHUTDOWN_CONFIG:
                print(f"  ✗ Missing config key: {key}")
                return False

        # Check types
        if not isinstance(SHUTDOWN_CONFIG['browser_kill_timeout'], (int, float)):
            print("  ✗ browser_kill_timeout must be numeric")
            return False

        if not isinstance(SHUTDOWN_CONFIG['enable_orphan_cleanup'], bool):
            print("  ✗ enable_orphan_cleanup must be boolean")
            return False

        if not isinstance(SHUTDOWN_CONFIG['orphan_cleanup_patterns'], list):
            print("  ✗ orphan_cleanup_patterns must be list")
            return False

        # Print current config
        print(f"  ✓ Configuration valid:")
        print(f"    - browser_kill_timeout: {SHUTDOWN_CONFIG['browser_kill_timeout']}")
        print(f"    - enable_orphan_cleanup: {SHUTDOWN_CONFIG['enable_orphan_cleanup']}")
        print(f"    - orphan_cleanup_patterns: {SHUTDOWN_CONFIG['orphan_cleanup_patterns']}")

        return True

    except Exception as e:
        print(f"  ✗ Configuration validation failed: {e}")
        return False


def validate_function_signatures():
    """Validate function signatures are correct."""
    print("\n✓ Validating function signatures...")
    try:
        import inspect
        from src.utils.process_cleanup import (
            cleanup_on_startup,
            find_orphaned_browsers,
            cleanup_orphaned_browsers,
            is_automation_browser,
        )

        # Check cleanup_on_startup
        sig = inspect.signature(cleanup_on_startup)
        if 'dry_run' not in sig.parameters:
            print("  ✗ cleanup_on_startup missing dry_run parameter")
            return False

        # Check cleanup_orphaned_browsers
        sig = inspect.signature(cleanup_orphaned_browsers)
        if 'processes' not in sig.parameters or 'force' not in sig.parameters:
            print("  ✗ cleanup_orphaned_browsers missing required parameters")
            return False

        # Check is_automation_browser
        sig = inspect.signature(is_automation_browser)
        if 'process' not in sig.parameters:
            print("  ✗ is_automation_browser missing process parameter")
            return False

        print("  ✓ All function signatures correct")
        return True

    except Exception as e:
        print(f"  ✗ Function signature validation failed: {e}")
        return False


def validate_dry_run():
    """Validate dry-run mode works correctly."""
    print("\n✓ Validating dry-run mode...")
    try:
        from src.utils.process_cleanup import cleanup_on_startup

        stats = cleanup_on_startup(dry_run=True)

        # Check return value structure
        if not isinstance(stats, dict):
            print("  ✗ cleanup_on_startup should return dict")
            return False

        if 'total' not in stats:
            print("  ✗ Stats dict missing 'total' key")
            return False

        print(f"  ✓ Dry-run successful: {stats}")
        return True

    except Exception as e:
        print(f"  ✗ Dry-run validation failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def validate_find_orphaned():
    """Validate find_orphaned_browsers works correctly."""
    print("\n✓ Validating find_orphaned_browsers...")
    try:
        from src.utils.process_cleanup import find_orphaned_browsers

        orphans = find_orphaned_browsers()

        # Check return type
        if not isinstance(orphans, list):
            print("  ✗ find_orphaned_browsers should return list")
            return False

        print(f"  ✓ Found {len(orphans)} orphaned browser(s)")

        # If orphans found, verify they're process objects
        if orphans:
            import psutil
            for proc in orphans:
                if not isinstance(proc, psutil.Process):
                    print(f"  ✗ Orphan list contains non-Process object: {type(proc)}")
                    return False
            print(f"  ✓ All orphans are valid Process objects")

        return True

    except Exception as e:
        print(f"  ✗ find_orphaned_browsers validation failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def validate_documentation():
    """Validate documentation files exist."""
    print("\n✓ Validating documentation...")
    try:
        docs_file = project_root / 'docs' / 'process_cleanup.md'
        if not docs_file.exists():
            print(f"  ✗ Documentation file missing: {docs_file}")
            return False

        # Check file has content
        if docs_file.stat().st_size < 100:
            print(f"  ✗ Documentation file too small: {docs_file}")
            return False

        print(f"  ✓ Documentation exists: {docs_file}")
        return True

    except Exception as e:
        print(f"  ✗ Documentation validation failed: {e}")
        return False


def validate_tests_exist():
    """Validate test file exists."""
    print("\n✓ Validating tests...")
    try:
        test_file = project_root / 'tests' / 'test_process_cleanup.py'
        if not test_file.exists():
            print(f"  ✗ Test file missing: {test_file}")
            return False

        # Check file has content
        if test_file.stat().st_size < 100:
            print(f"  ✗ Test file too small: {test_file}")
            return False

        print(f"  ✓ Test file exists: {test_file}")
        print(f"  ✓ Test file size: {test_file.stat().st_size} bytes")
        return True

    except Exception as e:
        print(f"  ✗ Test validation failed: {e}")
        return False


def validate_psutil_dependency():
    """Validate psutil is installed and working."""
    print("\n✓ Validating psutil dependency...")
    try:
        import psutil

        # Test basic functionality
        processes = list(psutil.process_iter(['pid', 'name']))
        print(f"  ✓ psutil installed and working (found {len(processes)} processes)")
        return True

    except ImportError:
        print("  ✗ psutil not installed")
        print("  Install with: pip install psutil>=5.9.0")
        return False
    except Exception as e:
        print(f"  ✗ psutil validation failed: {e}")
        return False


def main():
    """Run all validations."""
    print("=" * 60)
    print("Process Cleanup Implementation Validation")
    print("=" * 60)

    validations = [
        ("Imports", validate_imports),
        ("Configuration", validate_configuration),
        ("Function Signatures", validate_function_signatures),
        ("Psutil Dependency", validate_psutil_dependency),
        ("Dry-Run Mode", validate_dry_run),
        ("Find Orphaned Browsers", validate_find_orphaned),
        ("Documentation", validate_documentation),
        ("Tests", validate_tests_exist),
    ]

    results = []
    for name, validator in validations:
        try:
            result = validator()
            results.append((name, result))
        except Exception as e:
            print(f"\n✗ {name} validation crashed: {e}")
            import traceback
            traceback.print_exc()
            results.append((name, False))

    # Summary
    print("\n" + "=" * 60)
    print("Validation Summary")
    print("=" * 60)

    passed = sum(1 for _, result in results if result)
    total = len(results)

    for name, result in results:
        status = "✓ PASS" if result else "✗ FAIL"
        print(f"{status}: {name}")

    print("\n" + "=" * 60)
    print(f"Results: {passed}/{total} validations passed")
    print("=" * 60)

    # Exit code
    if passed == total:
        print("\n✓ All validations passed! Implementation is ready.")
        return 0
    else:
        print(f"\n✗ {total - passed} validation(s) failed. Please review errors above.")
        return 1


if __name__ == '__main__':
    sys.exit(main())
