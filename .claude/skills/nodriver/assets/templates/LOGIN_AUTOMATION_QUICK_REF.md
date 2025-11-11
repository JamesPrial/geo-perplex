# Login Automation Quick Reference

Quick lookup guide for common login automation patterns.

## Imports

```python
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
```

## Most Common Pattern

```python
# Create form config
form_config = create_simple_form_config(
    username_selector="input[name='email']",
    password_selector="input[name='password']",
    submit_selector="button[type='submit']",
    success_indicator="div.dashboard",
)

# Create config
config = LoginConfig(
    username="user@example.com",
    password="password",
    login_url="https://example.com/login",
    form_config=form_config,
)

# Login
manager = LoginManager(config, tab=my_tab)
if await manager.login():
    print("Success!")
```

## Form Field Types

| Type | Input Type | Purpose |
|------|-----------|---------|
| `username_field` | text/email | Login username |
| `password_field` | password | Login password |
| `submit_button` | button | Form submit |
| Additional fields | any | Extra form inputs |

## FormField Options

```python
FormField(
    selector="css_selector",          # Required: CSS selector
    input_type="text",                # Type of input field
    fill_value="value",               # Override value to fill
    clear_before_input=True,          # Clear field first
    wait_for_visible=True,            # Wait for field
    timeout=10,                       # Timeout in seconds
)
```

## Login Strategies

```python
# Form-based (most common)
strategy=LoginStrategy.FORM_BASED
form_config=...

# OAuth 2.0
strategy=LoginStrategy.OAUTH_SIMULATION
oauth_config=OAuthConfig(...)

# Custom JavaScript
strategy=LoginStrategy.CUSTOM_JAVASCRIPT
custom_javascript="..."

# API-based
strategy=LoginStrategy.API_BASED
# Custom implementation
```

## Two-Factor Authentication

```python
two_factor_config = TwoFactorConfig(
    enabled=True,
    method=TwoFactorMethod.SMS,           # SMS, EMAIL, AUTHENTICATOR, etc.
    input_selector="input[name='code']",  # Where to enter code
    submit_selector="button[type='submit']",
    timeout=120,                          # Wait up to 2 minutes
    remember_device=True,                 # Remember this device
    device_name="My Device",
    success_indicator="div.dashboard",    # What indicates success
)
```

## Remember Me

```python
remember_me_config = RememberMeConfig(
    enabled=True,
    selector="input[name='remember']",    # Checkbox selector
    duration_days=30,
    auto_login_enabled=True,
)
```

## Session Management

```python
session_config = SessionConfig(
    session_cookie_name="sessionid",
    token_key="access_token",             # For JWT
    refresh_endpoint="/api/refresh",
    refresh_interval=3600,                # 1 hour
    timeout=86400,                        # 24 hours
    validation_endpoint="/api/validate",
)
```

## Common Selectors

```python
# Text input
"input[name='email']"
"input[type='text']"
"input[id='username']"

# Password input
"input[type='password']"
"input[name='password']"

# Submit button
"button[type='submit']"
"input[type='submit']"
"a[href='/login']"

# Success indicators
"div.dashboard"
"span[data-test='username']"
"div[role='main']"
```

## Manager Methods

```python
manager = LoginManager(config, tab=my_tab)

# Login operations
await manager.login()                     # Perform login
await manager.logout()                    # Logout
await manager.switch_account(user, pwd)   # Switch users

# Session operations
manager.try_restore_session(username)     # Restore saved session
await manager.validate_and_refresh_session()
manager.get_session_info()                # Get session details
manager.list_available_accounts()         # List saved accounts

# Storage
manager.session_storage.save_session()
manager.session_storage.load_session()
manager.session_storage.delete_session()
manager.session_storage.list_saved_sessions()
```

## Get Session Info

```python
info = manager.get_session_info()
# Returns:
# {
#     "username": "user@example.com",
#     "logged_in_at": "2024-01-15T10:30:00",
#     "last_activity": "2024-01-15T10:35:00",
#     "two_factor_verified": True,
#     "device_trusted": False,
#     "is_active": True,
#     "time_until_expiry": 82350,  # seconds
# }
```

## Error Handling

```python
try:
    if await manager.login():
        print("Logged in")
    else:
        print("Login returned False - check selectors")
except asyncio.TimeoutError:
    print("Login timed out")
except Exception as e:
    print(f"Error: {e}")
```

## Selector Testing

Test selectors in browser console:

```javascript
// Find element
document.querySelector("input[name='email']")

// Check visibility
document.querySelector("input[name='email']").offsetParent !== null

// Get all matching elements
document.querySelectorAll("input[type='password']")

// Find by text
[...document.querySelectorAll("button")].find(b => b.textContent.includes("Sign In"))
```

## Callbacks

```python
async def before_login(tab):
    """Called before form filling."""
    await tab.wait(selector="form.login-form")

async def after_login(tab):
    """Called after form submission."""
    url = await tab.evaluate("window.location.href")
    print(f"Redirected to: {url}")

form_config = LoginFormConfig(
    username_field=...,
    password_field=...,
    submit_button=...,
    pre_fill_callback=before_login,
    post_submit_callback=after_login,
)
```

## OAuth Parameters

```python
oauth_config = OAuthConfig(
    auth_endpoint="https://oauth.provider.com/authorize",
    client_id="your_client_id",
    redirect_uri="http://localhost:3000/callback",
    scope="read write",
    grant_type="authorization_code",
)

# Add custom parameters
oauth_config.additional_params = {
    "prompt": "login",
    "state": "random_value",
}
```

## Storage Paths

```python
manager = LoginManager(
    config,
    tab=my_tab,
    cookie_storage_path=Path(".cookies"),      # For cookies
    session_storage_path=Path(".sessions"),    # For sessions
)
```

## Common Issues

| Issue | Solution |
|-------|----------|
| Selector not found | Use DevTools to inspect HTML, test in console |
| Timeout waiting | Increase timeout value, check network speed |
| 2FA input field not found | Verify selector, check if popup/modal |
| Session not saved | Check file permissions on storage directory |
| Login appears to fail silently | Add success_indicator, check page content |

## Performance Tips

1. **Reuse sessions** - Restore sessions instead of re-logging in
2. **Use specific selectors** - Avoid generic selectors like "button"
3. **Set realistic timeouts** - Account for network latency
4. **Use callbacks sparingly** - Minimal custom logic
5. **Cache credentials** - Use environment variables, not files

## Security Tips

1. **Never hardcode credentials** - Use environment variables
2. **Protect session files** - Use restrictive file permissions
3. **Validate certificates** - Keep `verify_ssl=True`
4. **Use HTTPS** - Verify URLs are HTTPS
5. **Clear sensitive data** - Don't log credentials

## Quick Examples

### Minimal Login
```python
manager = LoginManager(config, tab=tab)
await manager.login()
```

### With Session Restore
```python
if not manager.try_restore_session("user@example.com"):
    await manager.login()
```

### With 2FA
```python
config = LoginConfig(..., two_factor_config=TwoFactorConfig(enabled=True, ...))
await manager.login()  # User enters 2FA code manually
```

### Account Switching
```python
await manager.switch_account("newuser@example.com", "password")
```

### Get Saved Accounts
```python
accounts = manager.list_available_accounts()
for account in accounts:
    if manager.try_restore_session(account):
        # Use account
```

## Files and Paths

```
Templates:
  ├── login_automation.py                  # Main template
  ├── login_automation_examples.py         # 10 practical examples
  ├── LOGIN_AUTOMATION_GUIDE.md            # Detailed guide
  └── LOGIN_AUTOMATION_QUICK_REF.md        # This file

Default Storage:
  ~/.sessions/                             # Saved sessions
  ~/.cookies/                              # Stored cookies
```

## Configuration Checklist

Before running login:

- [ ] Valid username/password
- [ ] Correct login URL
- [ ] CSS selectors verified (test in console)
- [ ] Success indicator identified
- [ ] Timeout values realistic
- [ ] 2FA method configured (if needed)
- [ ] Storage paths writable
- [ ] No SSL/certificate issues
- [ ] Network connectivity OK
- [ ] Credentials in environment variables

## Testing Template

```python
async def test_login():
    # Verify selectors first
    email_field = await my_tab.find("input[name='email']")
    assert email_field is not None

    pwd_field = await my_tab.find("input[name='password']")
    assert pwd_field is not None

    # Test login
    manager = LoginManager(config, tab=my_tab)
    assert await manager.login()

    # Verify session
    session_info = manager.get_session_info()
    assert session_info is not None
    assert session_info['username'] == "user@example.com"

    # Test session restore
    assert manager.try_restore_session("user@example.com")
```

## Related Utilities

The nodriver skills package includes:

- `cookie_manager.py` - Cookie management
- `smart_click.py` - Reliable element clicking
- `element_waiter.py` - Wait for elements
- `network_monitor.py` - Network interception
- `human_behavior.py` - Human-like interactions

Use these alongside login automation for more robust scripts.

## Next Steps

1. Read `LOGIN_AUTOMATION_GUIDE.md` for detailed explanations
2. Review `login_automation_examples.py` for real-world patterns
3. Inspect target site selectors using DevTools
4. Start with simple form-based example
5. Customize selectors and add 2FA as needed
6. Test thoroughly before production use

## Support

For detailed API documentation, see docstrings in `login_automation.py`.

Common questions:

**Q: How do I find the right CSS selector?**
A: Open DevTools (F12), right-click element, "Inspect", copy selector.

**Q: Can I use XPath instead of CSS?**
A: No, the template uses CSS selectors. Adapt XPath to CSS using DevTools.

**Q: How long does login take?**
A: Typically 5-10 seconds, configurable via timeout parameter.

**Q: Are credentials stored securely?**
A: Credentials are NOT stored. Sessions/cookies are - protect files.

**Q: Can I automate 2FA?**
A: Partially - SMS/email codes must be entered manually by user.

**Q: How many accounts can I save?**
A: Unlimited - one session file per account.
