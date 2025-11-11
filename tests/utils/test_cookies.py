"""
Unit tests for src/utils/cookies.py
Tests cookie loading and validation functionality.
"""
import pytest
import json
from pathlib import Path
from src.utils.cookies import load_cookies, validate_auth_cookies


@pytest.fixture
def valid_cookies_file(tmp_path: Path) -> Path:
    """
    Creates a temporary auth.json file with valid cookie list format.
    """
    auth_file = tmp_path / "auth.json"
    test_cookies = [
        {
            "name": "pplx.session-id",
            "value": "test-session-id-123",
            "domain": ".perplexity.ai",
            "path": "/",
            "secure": True,
            "httpOnly": True
        },
        {
            "name": "__Secure-next-auth.session-token",
            "value": "test-token-456",
            "domain": ".perplexity.ai",
            "path": "/",
            "secure": True,
            "httpOnly": True
        },
        {
            "name": "next-auth.csrf-token",
            "value": "test-csrf-789",
            "domain": ".perplexity.ai",
            "path": "/",
            "secure": True
        }
    ]
    auth_file.write_text(json.dumps(test_cookies, indent=2))
    return auth_file


@pytest.fixture
def incomplete_cookies_file(tmp_path: Path) -> Path:
    """
    Creates a temporary auth.json file with missing required cookies.
    """
    auth_file = tmp_path / "auth_incomplete.json"
    incomplete_cookies = [
        {
            "name": "some-other-cookie",
            "value": "value",
            "domain": ".perplexity.ai",
            "path": "/"
        }
    ]
    auth_file.write_text(json.dumps(incomplete_cookies, indent=2))
    return auth_file


@pytest.fixture
def empty_list_file(tmp_path: Path) -> Path:
    """Creates a file with an empty list."""
    auth_file = tmp_path / "auth_empty.json"
    auth_file.write_text("[]")
    return auth_file


@pytest.fixture
def dict_format_file(tmp_path: Path) -> Path:
    """Creates a file with dict format instead of list (invalid)."""
    auth_file = tmp_path / "auth_dict.json"
    auth_file.write_text('{"cookie": "value"}')
    return auth_file


@pytest.mark.unit
class TestLoadCookies:
    """Tests for load_cookies() function"""

    def test_load_cookies_success(self, valid_cookies_file, capsys):
        """Test successfully loading valid cookies file"""
        cookies = load_cookies(str(valid_cookies_file))

        assert isinstance(cookies, list)
        assert len(cookies) == 3
        assert all(isinstance(c, dict) for c in cookies)

        # Check that success message was printed
        captured = capsys.readouterr()
        assert "✓ Loaded 3 cookies" in captured.out

    def test_load_cookies_has_required_fields(self, valid_cookies_file):
        """Test that loaded cookies have required fields"""
        cookies = load_cookies(str(valid_cookies_file))

        for cookie in cookies:
            assert "name" in cookie
            assert "value" in cookie

    def test_load_cookies_file_not_found(self):
        """Test that FileNotFoundError is raised for missing file"""
        with pytest.raises(FileNotFoundError) as exc_info:
            load_cookies("/nonexistent/path/auth.json")

        assert "Cookie file not found" in str(exc_info.value)

    def test_load_cookies_malformed_json(self, tmp_path):
        """Test that JSONDecodeError is raised for malformed JSON"""
        malformed_file = tmp_path / "malformed.json"
        malformed_file.write_text("{ invalid json }")

        with pytest.raises(json.JSONDecodeError):
            load_cookies(str(malformed_file))

    def test_load_cookies_empty_list(self, empty_list_file):
        """Test that ValueError is raised for empty list"""
        with pytest.raises(ValueError) as exc_info:
            load_cookies(str(empty_list_file))

        assert "Invalid cookie format" in str(exc_info.value)
        assert "non-empty array" in str(exc_info.value)

    def test_load_cookies_dict_instead_of_list(self, dict_format_file):
        """Test that ValueError is raised when dict is provided instead of list"""
        with pytest.raises(ValueError) as exc_info:
            load_cookies(str(dict_format_file))

        assert "Invalid cookie format" in str(exc_info.value)

    def test_load_cookies_default_path(self, tmp_path, monkeypatch):
        """Test loading cookies from default path (auth.json in cwd)"""
        # Change cwd to tmp_path
        monkeypatch.chdir(tmp_path)

        # Create auth.json in the new cwd
        auth_file = tmp_path / "auth.json"
        test_cookies = [
            {"name": "test-cookie", "value": "test-value"}
        ]
        auth_file.write_text(json.dumps(test_cookies))

        # Load without specifying path (should use cwd/auth.json)
        cookies = load_cookies()

        assert len(cookies) == 1
        assert cookies[0]["name"] == "test-cookie"

    def test_load_cookies_preserves_all_fields(self, valid_cookies_file):
        """Test that all cookie fields are preserved"""
        cookies = load_cookies(str(valid_cookies_file))

        first_cookie = cookies[0]
        assert first_cookie["name"] == "pplx.session-id"
        assert first_cookie["value"] == "test-session-id-123"
        assert first_cookie["domain"] == ".perplexity.ai"
        assert first_cookie["path"] == "/"
        assert first_cookie["secure"] is True
        assert first_cookie["httpOnly"] is True


@pytest.mark.unit
class TestValidateAuthCookies:
    """Tests for validate_auth_cookies() function"""

    def test_validate_auth_cookies_all_present(self, capsys):
        """Test validation passes when all required cookies are present"""
        valid_cookies = [
            {"name": "pplx.session-id", "value": "session-123"},
            {"name": "__Secure-next-auth.session-token", "value": "token-456"},
            {"name": "other-cookie", "value": "other-value"}
        ]

        result = validate_auth_cookies(valid_cookies)

        assert result is True

        # Check success message
        captured = capsys.readouterr()
        assert "✓ All required authentication cookies present" in captured.out

    def test_validate_auth_cookies_missing_session_id(self, capsys):
        """Test validation fails when session-id is missing"""
        invalid_cookies = [
            {"name": "__Secure-next-auth.session-token", "value": "token-456"}
        ]

        result = validate_auth_cookies(invalid_cookies)

        assert result is False

        # Check warning message
        captured = capsys.readouterr()
        assert "⚠ Warning: Missing required authentication cookies" in captured.out

    def test_validate_auth_cookies_missing_session_token(self, capsys):
        """Test validation fails when session token is missing"""
        invalid_cookies = [
            {"name": "pplx.session-id", "value": "session-123"}
        ]

        result = validate_auth_cookies(invalid_cookies)

        assert result is False

        captured = capsys.readouterr()
        assert "⚠ Warning" in captured.out

    def test_validate_auth_cookies_missing_both(self, capsys):
        """Test validation fails when both required cookies are missing"""
        invalid_cookies = [
            {"name": "some-other-cookie", "value": "value"}
        ]

        result = validate_auth_cookies(invalid_cookies)

        assert result is False

    def test_validate_auth_cookies_empty_list(self, capsys):
        """Test validation fails for empty cookie list"""
        result = validate_auth_cookies([])

        assert result is False

        captured = capsys.readouterr()
        assert "⚠ Warning" in captured.out

    def test_validate_auth_cookies_extra_cookies_allowed(self):
        """Test that extra cookies don't affect validation"""
        cookies_with_extras = [
            {"name": "pplx.session-id", "value": "session-123"},
            {"name": "__Secure-next-auth.session-token", "value": "token-456"},
            {"name": "extra-cookie-1", "value": "value-1"},
            {"name": "extra-cookie-2", "value": "value-2"},
            {"name": "extra-cookie-3", "value": "value-3"}
        ]

        result = validate_auth_cookies(cookies_with_extras)

        assert result is True

    def test_validate_auth_cookies_case_sensitive(self):
        """Test that cookie name validation is case-sensitive"""
        wrong_case_cookies = [
            {"name": "PPLX.SESSION-ID", "value": "session-123"},  # Wrong case
            {"name": "__Secure-next-auth.session-token", "value": "token-456"}
        ]

        result = validate_auth_cookies(wrong_case_cookies)

        assert result is False

    def test_validate_auth_cookies_handles_missing_name_field(self):
        """Test that validation handles cookies without 'name' field"""
        malformed_cookies = [
            {"value": "session-123"},  # Missing 'name' field
            {"name": "__Secure-next-auth.session-token", "value": "token-456"}
        ]

        result = validate_auth_cookies(malformed_cookies)

        assert result is False

    def test_validate_auth_cookies_displays_found_cookies(self, capsys):
        """Test that validation output shows which cookies were found"""
        invalid_cookies = [
            {"name": "some-cookie", "value": "value"},
            {"name": "another-cookie", "value": "value"}
        ]

        validate_auth_cookies(invalid_cookies)

        captured = capsys.readouterr()
        assert "Found:" in captured.out
        assert "some-cookie" in captured.out or "another-cookie" in captured.out


@pytest.mark.integration
class TestCookiesIntegration:
    """Integration tests for cookie loading and validation workflow"""

    def test_load_and_validate_workflow(self, valid_cookies_file):
        """Test the complete workflow of loading and validating cookies"""
        # Load cookies
        cookies = load_cookies(str(valid_cookies_file))

        # Validate cookies
        is_valid = validate_auth_cookies(cookies)

        assert is_valid is True
        assert len(cookies) == 3

    def test_load_and_validate_invalid_cookies(self, incomplete_cookies_file):
        """Test workflow with invalid cookies"""
        # Load cookies (should succeed)
        cookies = load_cookies(str(incomplete_cookies_file))

        # Validate cookies (should fail)
        is_valid = validate_auth_cookies(cookies)

        assert is_valid is False
        assert len(cookies) == 1


@pytest.mark.unit
class TestMalformedCookieStructures:
    """Tests for malformed cookie data structures"""

    def test_cookie_missing_value_field(self, tmp_path):
        """Test cookie object with missing 'value' field"""
        auth_file = tmp_path / "auth_no_value.json"
        malformed_cookies = [
            {"name": "pplx.session-id"},  # Missing 'value'
            {"name": "__Secure-next-auth.session-token", "value": "token-456"}
        ]
        auth_file.write_text(json.dumps(malformed_cookies))

        cookies = load_cookies(str(auth_file))

        # Should load successfully (validation happens separately)
        assert len(cookies) == 2
        assert "value" not in cookies[0]

    def test_cookie_name_as_none(self, tmp_path):
        """Test cookie with None as name"""
        auth_file = tmp_path / "auth_none_name.json"
        malformed_cookies = [
            {"name": None, "value": "test-value"}
        ]
        auth_file.write_text(json.dumps(malformed_cookies))

        cookies = load_cookies(str(auth_file))

        assert len(cookies) == 1
        assert cookies[0]["name"] is None

    def test_cookie_name_as_empty_string(self, tmp_path):
        """Test cookie with empty string as name"""
        auth_file = tmp_path / "auth_empty_name.json"
        malformed_cookies = [
            {"name": "", "value": "test-value"}
        ]
        auth_file.write_text(json.dumps(malformed_cookies))

        cookies = load_cookies(str(auth_file))

        assert len(cookies) == 1
        assert cookies[0]["name"] == ""

    def test_cookie_value_as_non_string(self, tmp_path):
        """Test cookie with non-string value (int, list, dict)"""
        auth_file = tmp_path / "auth_non_string_value.json"
        malformed_cookies = [
            {"name": "cookie1", "value": 12345},  # int
            {"name": "cookie2", "value": ["a", "b"]},  # list
            {"name": "cookie3", "value": {"key": "val"}}  # dict
        ]
        auth_file.write_text(json.dumps(malformed_cookies))

        cookies = load_cookies(str(auth_file))

        assert len(cookies) == 3
        assert cookies[0]["value"] == 12345
        assert cookies[1]["value"] == ["a", "b"]
        assert cookies[2]["value"] == {"key": "val"}

    def test_cookie_list_containing_non_dict_items(self, tmp_path):
        """Test cookie list containing strings, numbers instead of dicts"""
        auth_file = tmp_path / "auth_mixed_types.json"
        malformed_cookies = [
            "string-cookie",
            123,
            {"name": "valid-cookie", "value": "valid-value"},
            None
        ]
        auth_file.write_text(json.dumps(malformed_cookies))

        cookies = load_cookies(str(auth_file))

        # Should load all items regardless of type
        assert len(cookies) == 4

    def test_cookie_with_special_char_in_name(self, tmp_path):
        """Test cookies with special characters in name"""
        auth_file = tmp_path / "auth_special_chars.json"
        cookies_special = [
            {"name": "cookie with spaces", "value": "value1"},
            {"name": "cookie\"quotes\"", "value": "value2"},
            {"name": "cookie;semicolon", "value": "value3"}
        ]
        auth_file.write_text(json.dumps(cookies_special))

        cookies = load_cookies(str(auth_file))

        assert len(cookies) == 3
        assert cookies[0]["name"] == "cookie with spaces"

    def test_cookie_with_very_long_value(self, tmp_path):
        """Test cookie with extremely long value (100KB+)"""
        auth_file = tmp_path / "auth_long_value.json"
        very_long_value = "a" * 100000  # 100KB value
        cookies_long = [
            {"name": "pplx.session-id", "value": very_long_value},
            {"name": "__Secure-next-auth.session-token", "value": "token"}
        ]
        auth_file.write_text(json.dumps(cookies_long))

        cookies = load_cookies(str(auth_file))

        assert len(cookies) == 2
        assert len(cookies[0]["value"]) == 100000

    def test_validation_with_missing_value_field(self):
        """Test validation when cookie missing 'value' field"""
        malformed_cookies = [
            {"name": "pplx.session-id"},  # Missing 'value'
            {"name": "__Secure-next-auth.session-token", "value": "token"}
        ]

        # Should handle gracefully (may fail validation but no crash)
        try:
            result = validate_auth_cookies(malformed_cookies)
            # Validation may pass or fail, just ensure no crash
            assert isinstance(result, bool)
        except (KeyError, AttributeError):
            # If it raises error, that's also acceptable behavior
            pass

    def test_validation_with_empty_value(self):
        """Test validation when required cookie has empty value"""
        cookies_empty_value = [
            {"name": "pplx.session-id", "value": ""},  # Empty value
            {"name": "__Secure-next-auth.session-token", "value": "token"}
        ]

        result = validate_auth_cookies(cookies_empty_value)

        # Empty values might be considered valid or invalid - document behavior
        assert isinstance(result, bool)


@pytest.mark.unit
class TestFileEncodingEdgeCases:
    """Tests for file encoding and special character edge cases"""

    def test_load_cookies_with_utf8_bom(self, tmp_path):
        """Test loading file with UTF-8 BOM (Byte Order Mark)"""
        auth_file = tmp_path / "auth_bom.json"
        test_cookies = [{"name": "test", "value": "value"}]

        # Write with UTF-8 BOM
        with open(auth_file, 'w', encoding='utf-8-sig') as f:
            json.dump(test_cookies, f)

        # Fixed behavior: now handles BOM gracefully with utf-8-sig encoding
        cookies = load_cookies(str(auth_file))
        assert len(cookies) == 1
        assert cookies[0]["name"] == "test"

    def test_cookie_value_with_newlines(self, tmp_path):
        """Test cookie values containing newlines"""
        auth_file = tmp_path / "auth_newlines.json"
        cookies_with_newlines = [
            {"name": "pplx.session-id", "value": "value\nwith\nnewlines"},
            {"name": "__Secure-next-auth.session-token", "value": "token"}
        ]
        auth_file.write_text(json.dumps(cookies_with_newlines))

        cookies = load_cookies(str(auth_file))

        assert len(cookies) == 2
        assert "\n" in cookies[0]["value"]

    def test_cookie_value_with_unicode_emoji(self, tmp_path):
        """Test cookie values with Unicode emoji"""
        auth_file = tmp_path / "auth_emoji.json"
        cookies_with_emoji = [
            {"name": "pplx.session-id", "value": "session-🔒-secure"},
            {"name": "__Secure-next-auth.session-token", "value": "token-🚀"}
        ]
        auth_file.write_text(json.dumps(cookies_with_emoji, ensure_ascii=False))

        cookies = load_cookies(str(auth_file))

        assert len(cookies) == 2
        assert "🔒" in cookies[0]["value"]
        assert "🚀" in cookies[1]["value"]

    def test_cookie_name_with_unicode(self, tmp_path):
        """Test cookie names with Unicode characters"""
        auth_file = tmp_path / "auth_unicode_names.json"
        cookies_unicode = [
            {"name": "cookie-测试", "value": "value1"},
            {"name": "cookie-العربية", "value": "value2"}
        ]
        auth_file.write_text(json.dumps(cookies_unicode, ensure_ascii=False))

        cookies = load_cookies(str(auth_file))

        assert len(cookies) == 2

    def test_load_binary_file_as_json(self, tmp_path):
        """Test loading binary file (image) renamed as .json"""
        auth_file = tmp_path / "auth_binary.json"
        # Write random binary data
        auth_file.write_bytes(b'\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR')

        # Fixed behavior: Binary files now raise helpful ValueError
        with pytest.raises(ValueError, match="binary or not UTF-8 encoded"):
            load_cookies(str(auth_file))


@pytest.mark.unit
class TestFilePermissionEdgeCases:
    """Tests for file permission and I/O error handling"""

    def test_load_unreadable_file(self, tmp_path):
        """Test loading file without read permissions"""
        auth_file = tmp_path / "auth_unreadable.json"
        test_cookies = [{"name": "test", "value": "value"}]
        auth_file.write_text(json.dumps(test_cookies))

        # Make file unreadable
        import os
        os.chmod(auth_file, 0o000)

        try:
            with pytest.raises((PermissionError, OSError)):
                load_cookies(str(auth_file))
        finally:
            # Restore permissions for cleanup
            os.chmod(auth_file, 0o644)

    def test_load_directory_as_file(self, tmp_path):
        """Test trying to load directory as cookie file"""
        auth_dir = tmp_path / "auth_directory"
        auth_dir.mkdir()

        with pytest.raises((IsADirectoryError, json.JSONDecodeError, OSError)):
            load_cookies(str(auth_dir))

    def test_load_symlink_to_nonexistent_file(self, tmp_path):
        """Test loading symlink pointing to non-existent file"""
        import os
        target_file = tmp_path / "nonexistent.json"
        symlink_file = tmp_path / "auth_symlink.json"

        # Create symlink to non-existent file
        try:
            os.symlink(target_file, symlink_file)
        except OSError:
            # Skip test if symlinks not supported (Windows without privileges)
            pytest.skip("Symlinks not supported on this platform")

        with pytest.raises(FileNotFoundError):
            load_cookies(str(symlink_file))

    def test_load_from_relative_path(self, tmp_path, monkeypatch):
        """Test loading cookies from relative path"""
        # Change to tmp_path directory
        monkeypatch.chdir(tmp_path)

        auth_file = Path("auth_relative.json")
        test_cookies = [{"name": "test", "value": "value"}]
        auth_file.write_text(json.dumps(test_cookies))

        # Load using relative path
        cookies = load_cookies("auth_relative.json")

        assert len(cookies) == 1
        assert cookies[0]["name"] == "test"

    def test_load_from_path_with_spaces(self, tmp_path):
        """Test loading from path with spaces"""
        nested_dir = tmp_path / "path with spaces"
        nested_dir.mkdir()
        auth_file = nested_dir / "auth file.json"
        test_cookies = [{"name": "test", "value": "value"}]
        auth_file.write_text(json.dumps(test_cookies))

        cookies = load_cookies(str(auth_file))

        assert len(cookies) == 1

    def test_load_from_very_long_path(self, tmp_path):
        """Test loading from very long file path"""
        # Create nested directory structure
        deep_path = tmp_path
        for i in range(10):
            deep_path = deep_path / f"very_long_directory_name_{i}"
        deep_path.mkdir(parents=True)

        auth_file = deep_path / "auth.json"
        test_cookies = [{"name": "test", "value": "value"}]
        auth_file.write_text(json.dumps(test_cookies))

        cookies = load_cookies(str(auth_file))

        assert len(cookies) == 1
