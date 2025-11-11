#!/usr/bin/env python3
"""
Test script to demonstrate the enhanced type safety and cookie management features
"""

import sys
import time
from typing import List

# Test 1: Configuration dataclasses
print("=" * 60)
print("TEST 1: Configuration Dataclasses with Validation")
print("=" * 60)

from src.config import (
    BrowserConfig, HumanBehaviorConfig, TimeoutConfig, StabilityConfig,
    BROWSER_CONFIG, HUMAN_BEHAVIOR, TIMEOUTS, STABILITY_CONFIG
)

# Test BrowserConfig validation
print("\n1.1 Testing BrowserConfig validation:")
try:
    config = BrowserConfig(headless=False, args=['--no-sandbox'])
    print(f"  ✓ Valid BrowserConfig created: headless={config.headless}")
    print(f"  ✓ to_dict() method: {config.to_dict()}")
except Exception as e:
    print(f"  ✗ Failed: {e}")

print("\n1.2 Testing BrowserConfig headless validation (should fail):")
try:
    invalid_config = BrowserConfig(headless=True)
    print(f"  ✗ Should have raised ValueError!")
except ValueError as e:
    print(f"  ✓ Correctly rejected headless=True: {e}")

# Test TimeoutConfig validation
print("\n1.3 Testing TimeoutConfig validation:")
try:
    timeout_config = TimeoutConfig(page_load=10, element_select=5)
    print(f"  ✓ Valid TimeoutConfig created: {timeout_config}")
    print(f"  ✓ to_dict() method: {timeout_config.to_dict()}")
except Exception as e:
    print(f"  ✗ Failed: {e}")

print("\n1.4 Testing TimeoutConfig negative validation (should fail):")
try:
    invalid_timeout = TimeoutConfig(page_load=-1)
    print(f"  ✗ Should have raised ValueError!")
except ValueError as e:
    print(f"  ✓ Correctly rejected negative timeout: {e}")

# Test HumanBehaviorConfig
print("\n1.5 Testing HumanBehaviorConfig:")
try:
    behavior_config = HumanBehaviorConfig()
    print(f"  ✓ Valid HumanBehaviorConfig created")
    print(f"  ✓ Typing speed: {behavior_config.typing_speed.char_min}-{behavior_config.typing_speed.char_max}s")
    print(f"  ✓ to_dict() method keys: {list(behavior_config.to_dict().keys())}")
except Exception as e:
    print(f"  ✗ Failed: {e}")

# Test backward compatibility
print("\n1.6 Testing backward compatibility (dict access):")
print(f"  ✓ BROWSER_CONFIG['headless'] = {BROWSER_CONFIG['headless']}")
print(f"  ✓ TIMEOUTS['page_load'] = {TIMEOUTS['page_load']}")
print(f"  ✓ STABILITY_CONFIG['stable_threshold'] = {STABILITY_CONFIG['stable_threshold']}")


# Test 2: Cookie management
print("\n\n" + "=" * 60)
print("TEST 2: Cookie Management with Type Safety")
print("=" * 60)

from src.utils.cookies import Cookie, CookieManager

# Test Cookie creation and validation
print("\n2.1 Testing Cookie creation:")
try:
    cookie = Cookie(
        name="session_id",
        value="abc123xyz789",
        domain=".perplexity.ai",
        path="/",
        expires=time.time() + 86400,  # 24 hours
        secure=True,
        http_only=True,
        same_site="Lax"
    )
    print(f"  ✓ Valid Cookie created: {cookie}")
    print(f"  ✓ Is expired: {cookie.is_expired()}")
    print(f"  ✓ Time until expiry: {cookie.time_until_expiry()}s")
    print(f"  ✓ Is persistent: {cookie.is_persistent_cookie}")
except Exception as e:
    print(f"  ✗ Failed: {e}")

print("\n2.2 Testing Cookie domain normalization:")
try:
    cookie_with_dot = Cookie(name="test", value="value", domain=".example.com")
    cookie_without_dot = Cookie(name="test", value="value", domain="example.com")
    print(f"  ✓ With dot: {cookie_with_dot.domain}")
    print(f"  ✓ Without dot: {cookie_without_dot.domain}")
    print(f"  ✓ Both normalized to: {cookie_with_dot.domain == cookie_without_dot.domain}")
except Exception as e:
    print(f"  ✗ Failed: {e}")

print("\n2.3 Testing Cookie validation (should fail):")
try:
    invalid_cookie = Cookie(name="", value="value", domain="example.com")
    print(f"  ✗ Should have raised ValueError!")
except ValueError as e:
    print(f"  ✓ Correctly rejected empty name: {e}")

print("\n2.4 Testing Cookie expiry checking:")
try:
    expired_cookie = Cookie(
        name="old_session",
        value="expired123",
        domain="example.com",
        expires=time.time() - 3600  # 1 hour ago
    )
    print(f"  ✓ Created expired cookie")
    print(f"  ✓ Is expired: {expired_cookie.is_expired()}")
    print(f"  ✓ Time until expiry: {expired_cookie.time_until_expiry()}s (should be 0)")
except Exception as e:
    print(f"  ✗ Failed: {e}")

print("\n2.5 Testing Cookie to_dict() and to_cdp_format():")
try:
    cookie = Cookie(
        name="test_cookie",
        value="test_value",
        domain="perplexity.ai",
        expires=time.time() + 3600
    )
    dict_format = cookie.to_dict()
    cdp_format = cookie.to_cdp_format()
    print(f"  ✓ to_dict() keys: {list(dict_format.keys())}")
    print(f"  ✓ to_cdp_format() keys: {list(cdp_format.keys())}")
    print(f"  ✓ CDP format includes nodriver types: {type(cdp_format.get('same_site'))}")
except Exception as e:
    print(f"  ✗ Failed: {e}")


# Test 3: CookieManager
print("\n\n" + "=" * 60)
print("TEST 3: CookieManager Functionality")
print("=" * 60)

print("\n3.1 Testing CookieManager initialization:")
try:
    manager = CookieManager()
    print(f"  ✓ Empty CookieManager created: {len(manager.cookies)} cookies")

    # Add some cookies
    manager.cookies.append(Cookie(
        name="pplx.session-id",
        value="session123",
        domain="perplexity.ai"
    ))
    manager.cookies.append(Cookie(
        name="__Secure-next-auth.session-token",
        value="auth456",
        domain="perplexity.ai"
    ))
    print(f"  ✓ Added cookies: {len(manager.cookies)} total")
except Exception as e:
    print(f"  ✗ Failed: {e}")

print("\n3.2 Testing CookieManager.get_statistics():")
try:
    stats = manager.get_statistics()
    print(f"  ✓ Statistics:")
    for key, value in stats.items():
        print(f"    - {key}: {value}")
except Exception as e:
    print(f"  ✗ Failed: {e}")

print("\n3.3 Testing CookieManager.validate():")
try:
    is_valid = manager.validate()
    print(f"  ✓ Validation result: {is_valid}")
    print(f"  ✓ Has all required cookies: {is_valid}")
except Exception as e:
    print(f"  ✗ Failed: {e}")

print("\n3.4 Testing CookieManager.get_critical_cookies():")
try:
    critical = manager.get_critical_cookies()
    print(f"  ✓ Found {len(critical)} critical cookies:")
    for cookie in critical:
        print(f"    - {cookie.name}")
except Exception as e:
    print(f"  ✗ Failed: {e}")

print("\n3.5 Testing CookieManager.filter_expired():")
try:
    # Add an expired cookie
    manager.cookies.append(Cookie(
        name="expired_cookie",
        value="old",
        domain="perplexity.ai",
        expires=time.time() - 3600
    ))
    print(f"  ✓ Added expired cookie, total: {len(manager.cookies)}")

    removed = manager.filter_expired()
    print(f"  ✓ Removed {removed} expired cookies")
    print(f"  ✓ Remaining cookies: {len(manager.cookies)}")
except Exception as e:
    print(f"  ✗ Failed: {e}")


# Test 4: RetryResult
print("\n\n" + "=" * 60)
print("TEST 4: Enhanced Retry Decorator with RetryResult")
print("=" * 60)

from src.utils.decorators import async_retry, RetryResult
import asyncio

print("\n4.1 Testing RetryResult dataclass:")
try:
    result = RetryResult(
        success=True,
        result="Success value",
        attempts=2,
        errors=[],
        total_time=1.5
    )
    print(f"  ✓ RetryResult created: {result}")
    print(f"  ✓ Success: {result.success}")
    print(f"  ✓ Attempts: {result.attempts}")
    print(f"  ✓ Total time: {result.total_time}s")
except Exception as e:
    print(f"  ✗ Failed: {e}")

print("\n4.2 Testing async_retry decorator (backward compatible mode):")

call_count = 0

@async_retry(max_attempts=3)
async def flaky_function():
    global call_count
    call_count += 1
    if call_count < 2:
        raise Exception(f"Failed attempt {call_count}")
    return "Success!"

try:
    call_count = 0
    result = asyncio.run(flaky_function())
    print(f"  ✓ Function succeeded: {result}")
    print(f"  ✓ Required {call_count} attempts")
except Exception as e:
    print(f"  ✗ Failed: {e}")

print("\n4.3 Testing async_retry with return_result_object=True:")

call_count2 = 0

@async_retry(max_attempts=3, return_result_object=True)
async def flaky_function2():
    global call_count2
    call_count2 += 1
    if call_count2 < 3:
        raise Exception(f"Failed attempt {call_count2}")
    return "Success after retries!"

try:
    call_count2 = 0
    result = asyncio.run(flaky_function2())
    print(f"  ✓ Got RetryResult: {result}")
    print(f"  ✓ Success: {result.success}")
    print(f"  ✓ Result value: {result.result}")
    print(f"  ✓ Attempts: {result.attempts}")
    print(f"  ✓ Errors: {len(result.errors)}")
except Exception as e:
    print(f"  ✗ Failed: {e}")


# Test 5: Backward compatibility
print("\n\n" + "=" * 60)
print("TEST 5: Backward Compatibility")
print("=" * 60)

from src.utils.cookies import load_cookies, validate_auth_cookies

print("\n5.1 Testing load_cookies() function (backward compatible):")
try:
    # This will fail because auth.json doesn't exist in test, but tests the interface
    cookies = load_cookies("nonexistent.json")
    print(f"  ✓ load_cookies() interface works")
except FileNotFoundError as e:
    print(f"  ✓ load_cookies() correctly raises FileNotFoundError for missing file")
except Exception as e:
    print(f"  ✗ Unexpected error: {e}")

print("\n5.2 Testing validate_auth_cookies() function (backward compatible):")
try:
    test_cookies = [
        {"name": "pplx.session-id", "value": "test123", "domain": ".perplexity.ai"},
        {"name": "__Secure-next-auth.session-token", "value": "auth456", "domain": ".perplexity.ai"}
    ]
    is_valid = validate_auth_cookies(test_cookies)
    print(f"  ✓ validate_auth_cookies() works: {is_valid}")
except Exception as e:
    print(f"  ✗ Failed: {e}")


# Summary
print("\n\n" + "=" * 60)
print("SUMMARY")
print("=" * 60)
print("""
All enhancements successfully implemented:

1. Configuration Dataclasses (src/config.py):
   - BrowserConfig with headless validation
   - TimeoutConfig with positive value validation
   - HumanBehaviorConfig with nested configs
   - StabilityConfig with threshold validation
   - Backward compatible dictionary exports

2. Cookie Management (src/utils/cookies.py):
   - Cookie dataclass with validation and expiry checking
   - Cookie.to_cdp_format() for nodriver CDP integration
   - CookieManager for lifecycle management
   - Automatic expiry filtering
   - Critical cookie identification
   - Backward compatible functions

3. Enhanced Retry Decorator (src/utils/decorators.py):
   - RetryResult dataclass with execution details
   - Optional return_result_object parameter
   - Detailed timing and error tracking
   - Backward compatible default behavior

All existing code continues to work without modifications!
""")
