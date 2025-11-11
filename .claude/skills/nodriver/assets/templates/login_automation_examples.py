#!/usr/bin/env python3
"""
Practical examples of using the login automation template.

These examples demonstrate real-world usage patterns for different
authentication systems and scenarios.
"""

import asyncio
from pathlib import Path
from login_automation import (
    LoginManager,
    LoginConfig,
    LoginStrategy,
    LoginFormConfig,
    FormField,
    OAuthConfig,
    TwoFactorConfig,
    TwoFactorMethod,
    RememberMeConfig,
    SessionConfig,
    create_simple_form_config,
    create_oauth_config,
)


# ==============================================================================
# Example 1: Simple Email/Password Form Login
# ==============================================================================

async def example_simple_login(tab):
    """
    Simple form-based login with minimal configuration.

    This is the most straightforward approach for traditional login forms.
    """
    form_config = create_simple_form_config(
        username_selector="input[name='email']",
        password_selector="input[name='password']",
        submit_selector="button[type='submit']",
        success_indicator="div.dashboard",
    )

    config = LoginConfig(
        username="user@example.com",
        password="secure_password",
        login_url="https://example.com/login",
        form_config=form_config,
        timeout=30,
    )

    manager = LoginManager(config, tab=tab)
    if await manager.login():
        print("Successfully logged in!")
        return manager
    return None


# ==============================================================================
# Example 2: Advanced Form Login with Additional Fields
# ==============================================================================

async def example_advanced_form_login(tab):
    """
    Form login with company field, remember me checkbox, and 2FA.

    Demonstrates handling multiple form fields and 2FA.
    """
    form_config = LoginFormConfig(
        username_field=FormField(
            selector="input[id='email']",
            input_type="email",
        ),
        password_field=FormField(
            selector="input[id='password']",
            input_type="password",
        ),
        submit_button=FormField(
            selector="button[id='login-btn']",
        ),
        success_indicator="span[data-test='user-name']",
        additional_fields={
            "company": FormField(
                selector="input[name='company']",
                fill_value="My Company",
            ),
        },
    )

    two_factor_config = TwoFactorConfig(
        enabled=True,
        method=TwoFactorMethod.SMS,
        input_selector="input[placeholder='Enter verification code']",
        submit_selector="button[id='verify-btn']",
        timeout=120,
        remember_device=True,
        device_name="Automation Workstation",
    )

    remember_me_config = RememberMeConfig(
        enabled=True,
        selector="input[name='remember_me']",
        duration_days=30,
    )

    config = LoginConfig(
        username="user@company.com",
        password="secure_password",
        login_url="https://example.com/login",
        form_config=form_config,
        two_factor_config=two_factor_config,
        remember_me_config=remember_me_config,
    )

    manager = LoginManager(
        config,
        tab=tab,
        session_storage_path=Path(".sessions"),
    )
    success = await manager.login()
    if success:
        print("Advanced login successful!")
        session_info = manager.get_session_info()
        print(f"2FA verified: {session_info['two_factor_verified']}")
    return manager if success else None


# ==============================================================================
# Example 3: Multi-Step Login (First Email, Then Password)
# ==============================================================================

async def example_multi_step_login(tab):
    """
    Handle login forms that appear in multiple steps.

    Common pattern in modern authentication (Gmail-like).
    """
    # Pre-fill callback to handle first step
    async def handle_email_step(tab_instance):
        """Wait for password field to appear after email submission."""
        await asyncio.sleep(1)
        # Submit email form
        email_input = await tab_instance.find("input[type='email']")
        if email_input:
            await email_input.send_keys("user@example.com")
            submit_btn = await tab_instance.find("button[aria-label='Next']")
            if submit_btn:
                await submit_btn.click()
                # Wait for password field to appear
                password_field = await tab_instance.find(
                    "input[type='password']",
                    best_match=True,
                )
                if password_field:
                    await password_field.send_keys("secure_password")

    # Use custom JavaScript for multi-step handling
    custom_js = """
    // Check if we're at email step or password step
    const emailInput = document.querySelector("input[type='email']");
    const passwordInput = document.querySelector("input[type='password']");

    if (emailInput && passwordInput) {
        // Both visible - fill both
        emailInput.value = username;
        passwordInput.value = password;
        document.querySelector("button[type='submit']").click();
        return { success: true, step: "both" };
    } else if (emailInput) {
        // Only email visible
        emailInput.value = username;
        document.querySelector("button[aria-label='Next']").click();
        return { success: true, step: "email" };
    } else if (passwordInput) {
        // Only password visible
        passwordInput.value = password;
        document.querySelector("button[type='submit']").click();
        return { success: true, step: "password" };
    }

    return { success: false };
    """

    config = LoginConfig(
        username="user@example.com",
        password="secure_password",
        login_url="https://example.com/login",
        strategy=LoginStrategy.CUSTOM_JAVASCRIPT,
        custom_javascript=custom_js,
        timeout=45,
    )

    manager = LoginManager(config, tab=tab)
    if await manager.login():
        print("Multi-step login successful!")
    return manager


# ==============================================================================
# Example 4: OAuth 2.0 Flow Simulation
# ==============================================================================

async def example_oauth_login(tab):
    """
    Simulate OAuth 2.0 authentication flow.

    Works for services like GitHub, Google, etc.
    """
    oauth_config = create_oauth_config(
        client_id="your_oauth_client_id",
        redirect_uri="http://localhost:3000/callback",
        auth_endpoint="https://oauth-provider.com/authorize",
        scope="read:user user:email repo",
    )

    # Add provider-specific parameters
    oauth_config.additional_params = {
        "state": "random_state_123",
        "allow_signup": "false",
    }

    config = LoginConfig(
        username="oauth_user",  # May not be used depending on flow
        password="oauth_token",
        login_url="https://oauth-provider.com/authorize",
        strategy=LoginStrategy.OAUTH_SIMULATION,
        oauth_config=oauth_config,
        timeout=60,
    )

    manager = LoginManager(config, tab=tab)
    if await manager.login():
        print("OAuth login successful!")
    return manager


# ==============================================================================
# Example 5: API-Based Login with Custom Headers
# ==============================================================================

async def example_api_login(tab):
    """
    Handle API-based authentication with custom headers.

    For sites that authenticate via API endpoints rather than form submission.
    """
    custom_js = """
    // Perform API-based login
    async function loginViaAPI() {
        try {
            const response = await fetch('/api/v1/login', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-Custom-Header': 'automation-agent',
                },
                credentials: 'include',
                body: JSON.stringify({
                    email: username,
                    password: password,
                    device_name: 'automation_agent',
                }),
            });

            const data = await response.json();

            if (response.ok && data.access_token) {
                // Store token in localStorage for subsequent requests
                localStorage.setItem('access_token', data.access_token);
                localStorage.setItem('refresh_token', data.refresh_token);

                // Redirect to dashboard
                window.location.href = '/dashboard';

                return { success: true, token: data.access_token };
            }

            return { success: false, error: data.message };
        } catch (error) {
            return { success: false, error: error.message };
        }
    }

    return await loginViaAPI();
    """

    config = LoginConfig(
        username="user@example.com",
        password="secure_password",
        login_url="https://example.com/login",
        strategy=LoginStrategy.CUSTOM_JAVASCRIPT,
        custom_javascript=custom_js,
        timeout=30,
    )

    manager = LoginManager(config, tab=tab)
    if await manager.login():
        print("API login successful!")
    return manager


# ==============================================================================
# Example 6: Session Restoration Without Re-login
# ==============================================================================

async def example_session_restoration(tab):
    """
    Try to restore a previously saved session to skip login.

    Useful for repeated runs or persistent sessions.
    """
    config = LoginConfig(
        username="user@example.com",
        password="secure_password",
        login_url="https://example.com/login",
        form_config=create_simple_form_config(
            username_selector="input[name='email']",
            password_selector="input[name='password']",
            submit_selector="button[type='submit']",
        ),
    )

    manager = LoginManager(
        config,
        tab=tab,
        session_storage_path=Path(".sessions"),
    )

    # Try to restore previous session
    if manager.try_restore_session("user@example.com"):
        print("Session restored! Already logged in.")
        session_info = manager.get_session_info()
        print(f"Logged in as: {session_info['username']}")
        print(f"Time until expiry: {session_info['time_until_expiry']}s")
    else:
        print("No valid session found. Performing login...")
        if await manager.login():
            print("Login successful and session saved.")
        else:
            print("Login failed.")

    return manager


# ==============================================================================
# Example 7: Account Switching
# ==============================================================================

async def example_account_switching(tab):
    """
    Switch between multiple user accounts.

    Useful for testing multi-user scenarios.
    """
    accounts = [
        ("user1@example.com", "password1"),
        ("user2@example.com", "password2"),
        ("admin@example.com", "admin_password"),
    ]

    form_config = create_simple_form_config(
        username_selector="input[name='email']",
        password_selector="input[name='password']",
        submit_selector="button[type='submit']",
        success_indicator="div.user-dashboard",
    )

    for username, password in accounts:
        config = LoginConfig(
            username=username,
            password=password,
            login_url="https://example.com/login",
            form_config=form_config,
        )

        manager = LoginManager(config, tab=tab)

        # Use try_restore_session to avoid re-login if possible
        if manager.try_restore_session(username):
            print(f"Restored session for {username}")
        else:
            print(f"Logging in as {username}...")
            if not await manager.login():
                print(f"Failed to login as {username}")
                continue

        # Perform actions as this user
        print(f"Performing actions as {username}...")
        await asyncio.sleep(2)  # Simulate work

        # Logout before switching
        await manager.logout()

    print("Account switching complete!")


# ==============================================================================
# Example 8: 2FA with Timeout Handling
# ==============================================================================

async def example_2fa_with_timeout(tab):
    """
    Handle 2FA with graceful timeout management.

    Includes retry logic and user-friendly error handling.
    """
    form_config = create_simple_form_config(
        username_selector="input[name='email']",
        password_selector="input[name='password']",
        submit_selector="button[type='submit']",
    )

    two_factor_config = TwoFactorConfig(
        enabled=True,
        method=TwoFactorMethod.EMAIL,
        input_selector="input[name='verification_code']",
        submit_selector="button[type='submit']",
        timeout=180,  # 3 minutes
        remember_device=True,
        device_name="Automation Runner",
        success_indicator="div.dashboard-welcome",
    )

    config = LoginConfig(
        username="user@example.com",
        password="secure_password",
        login_url="https://example.com/login",
        form_config=form_config,
        two_factor_config=two_factor_config,
    )

    manager = LoginManager(config, tab=tab)

    max_attempts = 3
    attempt = 1

    while attempt <= max_attempts:
        try:
            if await manager.login():
                print("Login successful with 2FA!")
                break
            else:
                print(f"Login attempt {attempt} failed")
        except asyncio.TimeoutError:
            print(f"Attempt {attempt}: 2FA timeout")
        except Exception as e:
            print(f"Attempt {attempt}: Error - {e}")

        attempt += 1
        if attempt <= max_attempts:
            print(f"Retrying ({max_attempts - attempt} attempts remaining)...")
            await asyncio.sleep(2)

    if attempt > max_attempts:
        print("Max login attempts exceeded")
        return None

    return manager


# ==============================================================================
# Example 9: Custom Pre/Post Login Callbacks
# ==============================================================================

async def example_with_callbacks(tab):
    """
    Use callbacks to execute custom logic before/after login steps.

    Useful for handling dynamic page content or custom validations.
    """
    async def wait_for_login_page(tab_instance):
        """Callback: Wait for login page to fully load."""
        print("Waiting for login page to load...")
        # Wait for both fields to be visible
        await tab_instance.find("input[name='email']", best_match=True)
        await tab_instance.find("input[name='password']", best_match=True)
        print("Login page ready!")

    async def validate_after_login(tab_instance):
        """Callback: Validate successful login."""
        print("Validating login success...")
        # Check for user profile or welcome message
        profile = await tab_instance.find(
            "div[data-test='user-profile']",
            best_match=True,
        )
        if profile:
            username = await profile.text
            print(f"Confirmed logged in as: {username}")

    form_config = LoginFormConfig(
        username_field=FormField(selector="input[name='email']"),
        password_field=FormField(selector="input[name='password']"),
        submit_button=FormField(selector="button[type='submit']"),
        pre_fill_callback=wait_for_login_page,
        post_submit_callback=validate_after_login,
    )

    config = LoginConfig(
        username="user@example.com",
        password="secure_password",
        login_url="https://example.com/login",
        form_config=form_config,
    )

    manager = LoginManager(config, tab=tab)
    if await manager.login():
        print("Login with callbacks successful!")
    return manager


# ==============================================================================
# Example 10: Comprehensive Login with Session Management
# ==============================================================================

async def example_comprehensive_login(tab):
    """
    Complete example combining multiple features:
    - Form-based login
    - 2FA handling
    - Remember me
    - Session persistence
    - Error handling
    """
    form_config = LoginFormConfig(
        username_field=FormField(
            selector="input[id='email-input']",
            input_type="email",
            wait_for_visible=True,
            timeout=15,
        ),
        password_field=FormField(
            selector="input[id='password-input']",
            input_type="password",
            clear_before_input=True,
        ),
        submit_button=FormField(
            selector="button[id='login-button']",
        ),
        form_selector="form[id='login-form']",
        success_indicator="div[role='main']",
    )

    two_factor_config = TwoFactorConfig(
        enabled=True,
        method=TwoFactorMethod.SMS,
        input_selector="input[aria-label='2FA Code']",
        submit_selector="button[type='submit']",
        timeout=120,
        remember_device=True,
        device_name="Automation Server",
        success_indicator="span[data-testid='dashboard-header']",
    )

    remember_me_config = RememberMeConfig(
        enabled=True,
        selector="input[type='checkbox'][name='remember']",
        duration_days=30,
        auto_login_enabled=True,
    )

    session_config = SessionConfig(
        session_cookie_name="session_id",
        refresh_endpoint="/api/auth/refresh",
        refresh_interval=3600,
        timeout=86400,
        validation_endpoint="/api/auth/validate",
    )

    config = LoginConfig(
        username="user@example.com",
        password="secure_password",
        login_url="https://example.com/login",
        form_config=form_config,
        two_factor_config=two_factor_config,
        remember_me_config=remember_me_config,
        session_config=session_config,
        timeout=45,
    )

    manager = LoginManager(
        config,
        tab=tab,
        session_storage_path=Path(".sessions"),
    )

    # Try to restore session first
    if not manager.try_restore_session(config.username):
        print("Performing fresh login...")
        if not await manager.login():
            print("Login failed!")
            return None

    # Validate session
    if await manager.validate_and_refresh_session():
        session_info = manager.get_session_info()
        print("Session is valid and active")
        print(f"  Username: {session_info['username']}")
        print(f"  2FA Verified: {session_info['two_factor_verified']}")
        print(f"  Device Trusted: {session_info['device_trusted']}")
        print(f"  Time until expiry: {session_info['time_until_expiry']}s")
    else:
        print("Session validation failed!")
        return None

    return manager


# ==============================================================================
# Main Runner
# ==============================================================================

async def main():
    """Run all examples (demonstrative only, requires actual browser instance)."""
    print("Login Automation Examples")
    print("=" * 60)
    print("\nThese examples show how to use the login automation template.")
    print("To run them, you need:")
    print("1. A nodriver browser instance (tab)")
    print("2. Valid credentials for the target site")
    print("3. Site-specific CSS selectors (customized per site)")
    print("\nExample usage:")
    print("  manager = await example_simple_login(my_tab)")
    print("  if manager:")
    print("      session_info = manager.get_session_info()")
    print("      print(f'Logged in as: {session_info[\"username\"]}')")
    print("\nRefer to LOGIN_AUTOMATION_GUIDE.md for detailed documentation.")


if __name__ == "__main__":
    asyncio.run(main())
