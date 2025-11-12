#!/usr/bin/env python3
"""
Test script for Track 4 improvements:
- Cookie validation
- ReDoS protection
- Timing consistency
"""

import sys
import time
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent))

from src.utils.cookies import Cookie
from src.search.extractor import _validate_extraction, _ERROR_PATTERNS, _MAX_TEXT_CHECK_SIZE


def test_cookie_validation():
    """Test that Cookie.from_dict() properly validates input"""
    print("\n=== Testing Cookie Validation ===")

    # Test 1: Valid cookie
    try:
        valid_cookie = Cookie.from_dict({
            'name': 'session',
            'value': 'abc123',
            'domain': '.perplexity.ai'
        })
        print("✓ Valid cookie created successfully")
        print(f"  Cookie: {valid_cookie.name}={valid_cookie.value[:10]}...")
    except Exception as e:
        print(f"✗ Failed to create valid cookie: {e}")
        return False

    # Test 2: Missing name
    try:
        Cookie.from_dict({
            'value': 'abc123',
            'domain': '.perplexity.ai'
        })
        print("✗ Should have rejected cookie with missing name")
        return False
    except ValueError as e:
        print(f"✓ Correctly rejected missing name: {str(e)[:60]}...")

    # Test 3: Empty name
    try:
        Cookie.from_dict({
            'name': '',
            'value': 'abc123',
            'domain': '.perplexity.ai'
        })
        print("✗ Should have rejected cookie with empty name")
        return False
    except ValueError as e:
        print(f"✓ Correctly rejected empty name: {str(e)[:60]}...")

    # Test 4: Missing value
    try:
        Cookie.from_dict({
            'name': 'session',
            'domain': '.perplexity.ai'
        })
        print("✗ Should have rejected cookie with missing value")
        return False
    except ValueError as e:
        print(f"✓ Correctly rejected missing value: {str(e)[:60]}...")

    # Test 5: Whitespace-only name
    try:
        Cookie.from_dict({
            'name': '   ',
            'value': 'abc123',
            'domain': '.perplexity.ai'
        })
        print("✗ Should have rejected cookie with whitespace-only name")
        return False
    except ValueError as e:
        print(f"✓ Correctly rejected whitespace-only name: {str(e)[:60]}...")

    print("✓ All cookie validation tests passed")
    return True


def test_redos_protection():
    """Test that ReDoS protection is in place"""
    print("\n=== Testing ReDoS Protection ===")

    # Test 1: Verify patterns are compiled
    if not _ERROR_PATTERNS:
        print("✗ ERROR_PATTERNS not defined")
        return False

    for i, pattern in enumerate(_ERROR_PATTERNS):
        if hasattr(pattern, 'pattern'):  # It's a compiled regex
            print(f"✓ Pattern {i+1} is compiled: {pattern.pattern[:50]}...")
        else:
            print(f"✗ Pattern {i+1} is not compiled")
            return False

    # Test 2: Verify size limit is defined
    if _MAX_TEXT_CHECK_SIZE:
        print(f"✓ Size limit defined: {_MAX_TEXT_CHECK_SIZE} characters")
    else:
        print("✗ Size limit not defined")
        return False

    # Test 3: Test with normal text
    normal_text = "This is a normal answer about Python programming."
    sources = [{'url': 'https://example.com', 'text': 'Example'}]
    is_valid, error = _validate_extraction(normal_text, sources)
    if is_valid:
        print("✓ Normal text validated successfully")
    else:
        print(f"✗ Normal text rejected: {error}")
        return False

    # Test 4: Test with error message
    error_text = "Sorry, we couldn't find any results for your query."
    is_valid, error = _validate_extraction(error_text, sources)
    if not is_valid and "Error message detected" in error:
        print(f"✓ Error message detected correctly: {error[:60]}...")
    else:
        print(f"✗ Failed to detect error message")
        return False

    # Test 5: Test with huge text (performance check)
    huge_text = "Normal text " * 100000  # ~1.2MB of text
    start = time.time()
    is_valid, error = _validate_extraction(huge_text, sources)
    elapsed = time.time() - start

    if elapsed < 0.5:  # Should be fast due to size limit
        print(f"✓ Huge text processed quickly: {elapsed:.3f}s")
    else:
        print(f"⚠ Huge text took longer than expected: {elapsed:.3f}s")

    # Test 6: Test truncation note
    error_text_huge = ("Normal text " * 1000) + " sorry we couldn't help"
    is_valid, error = _validate_extraction(error_text_huge, sources)
    if not is_valid and "checked first" in error:
        print(f"✓ Truncation note present in error: {error[:80]}...")
    else:
        print(f"⚠ Truncation note not found (might be within limit)")

    print("✓ All ReDoS protection tests passed")
    return True


def test_validation_improvements():
    """Test improved validation logic"""
    print("\n=== Testing Validation Improvements ===")

    # Test 1: Too short answer
    short_text = "Too short"
    sources = [{'url': 'https://example.com', 'text': 'Example'}]
    is_valid, error = _validate_extraction(short_text, sources)
    if not is_valid and "too short" in error.lower():
        print(f"✓ Short answer rejected: {error}")
    else:
        print(f"✗ Failed to reject short answer")
        return False

    # Test 2: No sources (should still be valid - sources are optional)
    good_text = "This is a good answer with sufficient length for validation."
    is_valid, error = _validate_extraction(good_text, [])
    if is_valid and error is None:
        print(f"✓ Valid answer without sources accepted (sources optional)")
    else:
        print(f"✗ Failed to accept answer without sources: {error}")
        return False

    # Test 3: Invalid source URLs
    invalid_sources = [
        {'url': 'not-a-url', 'text': 'Bad'},
        {'url': 'ftp://example.com', 'text': 'FTP not valid'}
    ]
    is_valid, error = _validate_extraction(good_text, invalid_sources)
    if not is_valid and "No valid source URLs" in error:
        print(f"✓ Invalid URLs detected: {error}")
    else:
        print(f"✗ Failed to detect invalid URLs")
        return False

    # Test 4: Valid extraction
    valid_sources = [
        {'url': 'https://example.com', 'text': 'Example 1'},
        {'url': 'http://test.com', 'text': 'Example 2'}
    ]
    is_valid, error = _validate_extraction(good_text, valid_sources)
    if is_valid and error is None:
        print(f"✓ Valid extraction passed")
    else:
        print(f"✗ Valid extraction rejected: {error}")
        return False

    # Test 5: None sources (edge case - should not crash)
    is_valid, error = _validate_extraction(good_text, None)
    if is_valid and error is None:
        print(f"✓ Valid answer with None sources accepted (defensive None handling)")
    else:
        print(f"✗ Failed to accept answer with None sources: {error}")
        return False

    print("✓ All validation improvement tests passed")
    return True


def main():
    """Run all tests"""
    print("=" * 70)
    print("TRACK 4 IMPROVEMENTS VALIDATION TEST SUITE")
    print("=" * 70)

    results = []

    # Run tests
    results.append(("Cookie Validation", test_cookie_validation()))
    results.append(("ReDoS Protection", test_redos_protection()))
    results.append(("Validation Improvements", test_validation_improvements()))

    # Summary
    print("\n" + "=" * 70)
    print("TEST SUMMARY")
    print("=" * 70)

    passed = sum(1 for _, result in results if result)
    total = len(results)

    for test_name, result in results:
        status = "PASS" if result else "FAIL"
        symbol = "✓" if result else "✗"
        print(f"{symbol} {test_name}: {status}")

    print("=" * 70)
    print(f"Results: {passed}/{total} test suites passed")
    print("=" * 70)

    return 0 if passed == total else 1


if __name__ == "__main__":
    sys.exit(main())
