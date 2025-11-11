# Login Automation Template Guide

Comprehensive guide for using the login automation template with nodriver browser automation.

## Overview

The login automation template provides a flexible, adaptable framework for handling various authentication systems, including:

- **Form-based login** (username/password)
- **OAuth simulation** (OAuth 2.0 flows)
- **Custom JavaScript login** (dynamic authentication)
- **API-based login** (token extraction)
- **Two-factor authentication** (SMS, email, authenticator, security questions)
- **Session persistence** (across browser sessions)
- **Account switching** (multiple user accounts)
- **Remember me functionality** (faster re-login)

## Quick Start

### Basic Form-Based Login

```python
import asyncio
from pathlib import Path
from login_automation import (
    LoginManager,
    LoginConfig,
    create_simple_form_config,
)

async def main():
    # Create login configuration
    form_config = create_simple_form_config(
        username_selector="input[name='username']",
        password_selector="input[name='password']",
        submit_selector="button[type='submit']",
        success_indicator="div.dashboard",  # Element visible after login
    )

    config = LoginConfig(
        username="user@example.com",
        password="secure_password",
        login_url="https://example.com/login",
        form_config=form_config,
        timeout=30,
    )

    # Initialize manager (pass your nodriver tab instance)
    manager = LoginManager(config, tab=my_tab)

    # Perform login
    if await manager.login():
        print("Successfully logged in!")
        session_info = manager.get_session_info()
        print(f"Session: {session_info}")
    else:
        print("Login failed")

asyncio.run(main())
```

## Login Strategies

### 1. Form-Based Login (Most Common)

Use this for traditional username/password login forms.

```python
from login_automation import LoginFormConfig, FormField, LoginConfig, LoginStrategy

form_config = LoginFormConfig(
    username_field=FormField(
        selector="input[id='email']",
        input_type="email",
        clear_before_input=True,
        wait_for_visible=True,
    ),
    password_field=FormField(
        selector="input[id='password']",
        input_type="password",
        clear_before_input=True,
    ),
    submit_button=FormField(
        selector="button[type='submit']",
    ),
    form_selector="form#login-form",  # Optional: wait for form to appear
    success_indicator="div.user-dashboard",  # What appears after login
    additional_fields={
        "two_factor_method": FormField(
            selector="select[name='2fa_method']",
            fill_value="sms",  # Auto-select 2FA method
        ),
    },
)

config = LoginConfig(
    username="user@example.com",
    password="secure_password",
    login_url="https://example.com/login",
    strategy=LoginStrategy.FORM_BASED,
    form_config=form_config,
)
```

#### FormField Options

- `selector`: CSS selector for the field
- `input_type`: Type of input (text, password, email, number, etc.)
- `fill_value`: Value to fill (if different from username/password)
- `clear_before_input`: Clear field before filling (default: True)
- `wait_for_visible`: Wait for field to be visible before filling (default: True)
- `timeout`: How long to wait for field (default: 10 seconds)

### 2. OAuth Login Simulation

For OAuth 2.0 flows.

```python
from login_automation import OAuthConfig, LoginStrategy, create_oauth_config

oauth_config = create_oauth_config(
    client_id="your_client_id",
    redirect_uri="https://example.com/callback",
    auth_endpoint="https://oauth.example.com/authorize",
    scope="openid profile email",
)

config = LoginConfig(
    username="user@example.com",
    password="secure_password",
    login_url="https://example.com/login",
    strategy=LoginStrategy.OAUTH_SIMULATION,
    oauth_config=oauth_config,
)

# Additional OAuth parameters
oauth_config.additional_params = {
    "prompt": "login",
    "login_hint": "user@example.com",
}
```

### 3. Custom JavaScript Login

For sites with custom authentication logic.

```python
custom_js = """
// 'username' and 'password' are injected by the manager
const loginBtn = document.querySelector('button.custom-login');

// Perform custom login logic
async function customLogin() {
    await fetch('/api/login', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
            username: username,
            password: password
        })
    });

    return { success: true };
}

return await customLogin();
"""

config = LoginConfig(
    username="user@example.com",
    password="secure_password",
    login_url="https://example.com/login",
    strategy=LoginStrategy.CUSTOM_JAVASCRIPT,
    custom_javascript=custom_js,
)
```

## Two-Factor Authentication (2FA)

### Waiting for User Input

The template supports waiting for users to complete 2FA in the browser:

```python
from login_automation import TwoFactorConfig, TwoFactorMethod

two_fa_config = TwoFactorConfig(
    enabled=True,
    method=TwoFactorMethod.SMS,
    input_selector="input[name='verification_code']",
    submit_selector="button[type='submit']",
    success_indicator="div.dashboard",
    timeout=120,  # Wait up to 2 minutes
    remember_device=True,
    device_name="Automation Agent",
)

config = LoginConfig(
    username="user@example.com",
    password="secure_password",
    login_url="https://example.com/login",
    form_config=form_config,
    two_factor_config=two_fa_config,
)

manager = LoginManager(config, tab=my_tab)
if await manager.login():
    # User has manually entered 2FA code in the browser
    print(f"2FA verified: {manager.current_session.two_factor_verified}")
```

### Supported 2FA Methods

- `SMS`: SMS code sent to phone
- `EMAIL`: Code sent to email
- `AUTHENTICATOR`: Time-based authenticator app
- `SECURITY_QUESTIONS`: Security question answers
- `BACKUP_CODE`: Pre-generated backup codes
- `PUSH_NOTIFICATION`: Push notification approval

### How 2FA Waiting Works

1. Form login completes
2. 2FA input field appears
3. Manager prints message asking user to enter code
4. Manager waits up to `timeout` seconds for one of:
   - Success indicator element to appear
   - Page URL to change (indicating successful auth)
   - `two_factor_verified` flag to be set
5. If user enters code and authenticates, login completes

## Session Management

### Persisting Sessions

Sessions are automatically saved to disk after successful login:

```python
# Sessions stored in ~/.sessions/ by default
manager = LoginManager(
    config,
    tab=my_tab,
    session_storage_path=Path(".custom_sessions"),
)

# Session contains:
# - Username
# - Login timestamp
# - Session cookies
# - Authentication tokens
# - 2FA verification status
# - Device trust status
```

### Restoring Sessions

Restore a previously saved session without re-entering credentials:

```python
manager = LoginManager(config, tab=my_tab)

# Try to restore session for a user
if manager.try_restore_session("user@example.com"):
    print("Session restored - already logged in!")
else:
    print("Need to login again")
    await manager.login()
```

### Listing Available Accounts

```python
available_accounts = manager.list_available_accounts()
print(f"Saved accounts: {available_accounts}")
# Output: Saved accounts: ['user@example.com', 'other@example.com']
```

### Getting Session Information

```python
session_info = manager.get_session_info()
print(f"Current user: {session_info['username']}")
print(f"Logged in: {session_info['logged_in_at']}")
print(f"2FA verified: {session_info['two_factor_verified']}")
print(f"Device trusted: {session_info['device_trusted']}")
print(f"Time until expiry: {session_info['time_until_expiry']} seconds")
```

## Remember Me Functionality

Enable "Remember Me" for faster logins:

```python
from login_automation import RememberMeConfig

remember_me_config = RememberMeConfig(
    enabled=True,
    selector="input[name='remember_me']",  # Checkbox selector
    cookie_name="remember_me_token",
    duration_days=30,
    auto_login_enabled=True,  # Auto-login on next session
)

config = LoginConfig(
    username="user@example.com",
    password="secure_password",
    login_url="https://example.com/login",
    form_config=form_config,
    remember_me_config=remember_me_config,
)
```

## Account Switching

Switch between accounts without creating new browser instances:

```python
manager = LoginManager(config, tab=my_tab)

# Login with first account
await manager.login()
print(f"Current user: {manager.get_session_info()['username']}")

# Switch to different account
await manager.switch_account("other@example.com", "other_password")
print(f"Current user: {manager.get_session_info()['username']}")
```

## Logout Handling

Properly logout from the current session:

```python
manager = LoginManager(config, tab=my_tab)
await manager.login()

# Logout
if await manager.logout():
    print("Successfully logged out")
    assert manager.current_session is None
```

## Session Validation and Refresh

### Automatic Validation

Configure session validation:

```python
from login_automation import SessionConfig

session_config = SessionConfig(
    session_cookie_name="sessionid",
    token_key="access_token",  # For JWT tokens
    refresh_endpoint="/api/auth/refresh",
    refresh_interval=3600,  # Refresh every hour
    timeout=86400,  # Session timeout (24 hours)
    validation_endpoint="/api/auth/validate",
)

config = LoginConfig(
    username="user@example.com",
    password="secure_password",
    login_url="https://example.com/login",
    form_config=form_config,
    session_config=session_config,
)
```

### Manual Validation and Refresh

```python
# Check if session is valid and refresh if needed
if await manager.validate_and_refresh_session():
    print("Session is valid and refreshed")
else:
    print("Session expired or invalid")
```

## Callback Functions

Execute custom code at specific points in the login flow:

```python
async def before_fill_form(tab):
    """Called before form is filled."""
    # Wait for specific element
    await tab.wait(selector="div.login-ready")
    # Clear cookies
    await tab.evaluate("window.localStorage.clear()")

async def after_form_submit(tab):
    """Called after form submission."""
    # Wait for redirect to complete
    await asyncio.sleep(2)
    # Verify we're on the right page
    url = await tab.evaluate("window.location.href")
    print(f"Redirected to: {url}")

form_config = LoginFormConfig(
    username_field=FormField(selector="input[name='username']"),
    password_field=FormField(selector="input[name='password']"),
    submit_button=FormField(selector="button[type='submit']"),
    pre_fill_callback=before_fill_form,
    post_submit_callback=after_form_submit,
)
```

## Complex Real-World Examples

### Gmail-Like Login (Email + Password + Optional 2FA)

```python
from login_automation import (
    LoginManager,
    LoginConfig,
    LoginFormConfig,
    FormField,
    TwoFactorConfig,
    TwoFactorMethod,
    RememberMeConfig,
)

# Email field (first step)
email_field = FormField(
    selector="input[type='email']",
    input_type="email",
    wait_for_visible=True,
)

# Password field (second step)
password_field = FormField(
    selector="input[type='password']",
    input_type="password",
    wait_for_visible=True,
)

form_config = LoginFormConfig(
    username_field=email_field,
    password_field=password_field,
    submit_button=FormField(selector="span:contains('Next')"),  # Gmail-style
    success_indicator="[data-is-authorized='true']",
)

two_fa_config = TwoFactorConfig(
    enabled=True,
    method=TwoFactorMethod.SMS,
    input_selector="input[aria-label='Enter verification code']",
    submit_selector="button:contains('Verify')",
    timeout=180,
    remember_device=True,
    device_name="Automation Client",
)

remember_me_config = RememberMeConfig(
    enabled=True,
    duration_days=30,
    auto_login_enabled=True,
)

config = LoginConfig(
    username="user@gmail.com",
    password="app_password",  # Use app-specific passwords for 2FA-enabled accounts
    login_url="https://accounts.google.com/login",
    form_config=form_config,
    two_factor_config=two_fa_config,
    remember_me_config=remember_me_config,
    timeout=45,
)

manager = LoginManager(config, tab=my_tab)
success = await manager.login()
```

### LinkedIn-Like (Multi-Step + Challenge)

```python
# First step: email
form_config = LoginFormConfig(
    username_field=FormField(
        selector="input[name='email']",
        input_type="email",
    ),
    password_field=FormField(
        selector="input[name='password']",
        input_type="password",
    ),
    submit_button=FormField(selector="button[type='submit']"),
    pre_fill_callback=async_challenge_handler,  # Handle security challenges
    success_indicator="div[data-test-id='profile-card']",
)

config = LoginConfig(
    username="user@example.com",
    password="secure_password",
    login_url="https://www.linkedin.com/login",
    form_config=form_config,
)
```

### OAuth Provider (GitHub, Google, etc.)

```python
oauth_config = create_oauth_config(
    client_id="your_client_id",
    redirect_uri="http://localhost:3000/callback",
    auth_endpoint="https://github.com/login/oauth/authorize",
    scope="read:user user:email",
)

# Add additional GitHub-specific parameters
oauth_config.additional_params = {
    "state": "random_state_value",
}

config = LoginConfig(
    username="github_username",  # Not actually used for OAuth
    password="github_token",     # GitHub personal access token
    login_url="https://github.com/login/oauth/authorize",
    strategy=LoginStrategy.OAUTH_SIMULATION,
    oauth_config=oauth_config,
)

manager = LoginManager(config, tab=my_tab)
await manager.login()
```

## Error Handling

The template handles common error scenarios:

```python
manager = LoginManager(config, tab=my_tab)

try:
    success = await manager.login()
    if success:
        print("Login successful")
    else:
        print("Login failed - check selector accuracy")
except asyncio.TimeoutError:
    print("Login timed out - page loading slowly?")
except Exception as e:
    print(f"Unexpected error: {e}")

# Check specific failure reasons
if not success:
    # Verify CSS selectors exist on the page
    # Check if page content matches expected structure
    # Confirm credentials are correct
    # Verify network connectivity
    pass
```

## Best Practices

### 1. Use Specific Selectors

Good:
```python
FormField(selector="input[name='email']")
FormField(selector="input[id='password-field']")
FormField(selector="button[type='submit'][data-test='login-btn']")
```

Bad:
```python
FormField(selector="input")  # Too generic, might match wrong element
FormField(selector=".btn")   # Multiple elements with this class
```

### 2. Add Success Indicators

Always specify what indicates successful login:

```python
config = LoginConfig(
    ...
    form_config=LoginFormConfig(
        ...
        success_indicator="div.user-dashboard",  # Clear indicator
    ),
)
```

### 3. Handle Dynamic Content

Use callbacks for pages with dynamic elements:

```python
async def wait_for_dynamic_form(tab):
    await tab.wait(selector="form.login-form", timeout=10)

form_config = LoginFormConfig(
    ...
    pre_fill_callback=wait_for_dynamic_form,
)
```

### 4. Store Sensitive Data Securely

Never hardcode credentials:

```python
import os

username = os.getenv("LOGIN_USERNAME")
password = os.getenv("LOGIN_PASSWORD")

config = LoginConfig(
    username=username,
    password=password,
    ...
)
```

### 5. Use Appropriate Timeouts

Set realistic timeouts based on page speed:

```python
config = LoginConfig(
    timeout=30,  # Form filling timeout
    form_config=LoginFormConfig(
        username_field=FormField(timeout=10),
        password_field=FormField(timeout=10),
    ),
    two_factor_config=TwoFactorConfig(
        timeout=120,  # 2FA can take longer
    ),
)
```

### 6. Test Selectors First

Verify selectors work before relying on them:

```python
# In browser console, test:
document.querySelector("input[name='email']")      // Should not be null
document.querySelector("input[name='password']")   // Should not be null
document.querySelector("button[type='submit']")    // Should not be null
```

## Troubleshooting

### Login Fails Silently

1. Check console for JavaScript errors: `await tab.evaluate("window.error")`
2. Verify success indicator appears
3. Add debug printing to callbacks
4. Check network requests in DevTools

### Selectors Not Finding Elements

1. Use browser DevTools to inspect element HTML
2. Verify selector works in console: `document.querySelector(...)`
3. Check for iframes that might contain elements
4. Wait for elements that load dynamically

### 2FA Code Entry Fails

1. Verify `input_selector` matches code input field
2. Check `timeout` is long enough for user input
3. Ensure `success_indicator` accurately detects completion
4. Print debug info about page state

### Session Not Persisting

1. Verify session storage path exists
2. Check file permissions on storage directory
3. Inspect saved session JSON file for completeness
4. Verify session hasn't expired

## API Reference

See the docstrings in `login_automation.py` for complete API documentation.

Key classes:
- `LoginManager`: Main interface for login operations
- `LoginConfig`: Complete login configuration
- `LoginFormConfig`: Form-based login configuration
- `OAuthConfig`: OAuth 2.0 configuration
- `TwoFactorConfig`: 2FA configuration
- `SessionConfig`: Session management configuration
- `LoginSession`: Represents an active login session
- `SessionStorage`: Handles session persistence

## Performance Considerations

- Sessions are cached in memory after loading
- Cookies are stored in JSON format for quick restoration
- Large numbers of saved sessions don't impact performance
- Network requests are asynchronous and don't block
- Session validation is lazy (only on demand)

## Security Considerations

- Never log credentials
- Use environment variables for sensitive data
- Session files should be protected (read-only by owner)
- HTTPS verification enabled by default
- Cookies marked secure/httpOnly when possible
- 2FA reduces account compromise risk

## Contributing Extensions

To add support for new authentication systems:

1. Create new `LoginStrategy` enum value
2. Implement corresponding `_login_*` method in `LoginManager`
3. Add configuration class (e.g., `CustomAuthConfig`)
4. Document new strategy with examples
5. Test thoroughly with target service

Example:

```python
class LoginStrategy(Enum):
    # ... existing strategies ...
    SAML = "saml"
    LDAP = "ldap"

class SamlConfig:
    """SAML-specific configuration."""
    idp_endpoint: str
    assertion_consumer_service: str
    # ... more fields ...

# In LoginManager:
async def _login_saml(self) -> bool:
    """Execute SAML-based login."""
    # Implementation
    pass
```
