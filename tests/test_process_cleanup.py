"""
Tests for process cleanup utility.

Tests the safe detection and termination of orphaned browser processes,
including edge cases, error handling, and safety features.
"""

import pytest
from unittest.mock import Mock, MagicMock, patch, call
import psutil

from src.utils.process_cleanup import (
    is_automation_browser,
    find_orphaned_browsers,
    cleanup_orphaned_browsers,
    cleanup_on_startup,
)


@pytest.fixture
def mock_automation_process():
    """Mock process that looks like an automated browser."""
    proc = Mock(spec=psutil.Process)
    proc.pid = 1234
    proc.name.return_value = 'chrome'
    proc.cmdline.return_value = [
        '/usr/bin/google-chrome',
        '--remote-debugging-port=9222',
        '--disable-blink-features=AutomationControlled',
        '--user-data-dir=/tmp/chrome-profile',
    ]
    proc.ppid.return_value = 5000
    proc.is_running.return_value = True
    return proc


@pytest.fixture
def mock_normal_process():
    """Mock process that looks like a normal user browser."""
    proc = Mock(spec=psutil.Process)
    proc.pid = 5678
    proc.name.return_value = 'chrome'
    proc.cmdline.return_value = [
        '/usr/bin/google-chrome',
        '--user-data-dir=/home/user/.config/google-chrome',
    ]
    proc.ppid.return_value = 1000
    proc.is_running.return_value = True
    return proc


@pytest.fixture
def mock_python_parent():
    """Mock Python parent process (automation launcher)."""
    parent = Mock(spec=psutil.Process)
    parent.name.return_value = 'python3'
    return parent


class TestIsAutomationBrowser:
    """Tests for is_automation_browser() function."""

    def test_detects_remote_debugging_port(self, mock_automation_process):
        """Should detect --remote-debugging-port flag."""
        assert is_automation_browser(mock_automation_process) is True

    def test_detects_automation_controlled_flag(self):
        """Should detect --disable-blink-features=AutomationControlled."""
        proc = Mock(spec=psutil.Process)
        proc.pid = 1234
        proc.cmdline.return_value = [
            '/usr/bin/chrome',
            '--disable-blink-features=AutomationControlled',
        ]
        proc.ppid.return_value = 1000

        assert is_automation_browser(proc) is True

    def test_detects_temp_user_data_dir(self):
        """Should detect temporary user-data-dir."""
        proc = Mock(spec=psutil.Process)
        proc.pid = 1234
        proc.cmdline.return_value = [
            '/usr/bin/chrome',
            '--user-data-dir=/tmp/automated-chrome',
        ]
        proc.ppid.return_value = 1000

        assert is_automation_browser(proc) is True

    def test_detects_python_parent(self, mock_python_parent):
        """Should detect Python parent process."""
        proc = Mock(spec=psutil.Process)
        proc.pid = 1234
        proc.cmdline.return_value = ['/usr/bin/chrome']
        proc.ppid.return_value = 5000

        with patch('psutil.Process', return_value=mock_python_parent):
            assert is_automation_browser(proc) is True

    def test_ignores_normal_browser(self, mock_normal_process):
        """Should not flag normal user browser as automation."""
        parent = Mock(spec=psutil.Process)
        parent.name.return_value = 'systemd'

        with patch('psutil.Process', return_value=parent):
            assert is_automation_browser(mock_normal_process) is False

    def test_handles_access_denied(self):
        """Should return False on permission error."""
        proc = Mock(spec=psutil.Process)
        proc.pid = 1234
        proc.cmdline.side_effect = psutil.AccessDenied()

        assert is_automation_browser(proc) is False

    def test_handles_no_such_process(self):
        """Should return False if process disappeared."""
        proc = Mock(spec=psutil.Process)
        proc.pid = 1234
        proc.cmdline.side_effect = psutil.NoSuchProcess(1234)

        assert is_automation_browser(proc) is False

    def test_handles_parent_access_denied(self):
        """Should handle permission error accessing parent process."""
        proc = Mock(spec=psutil.Process)
        proc.pid = 1234
        proc.cmdline.return_value = ['/usr/bin/chrome']
        proc.ppid.return_value = 1

        with patch('psutil.Process', side_effect=psutil.AccessDenied()):
            # Should not crash, should check other indicators
            result = is_automation_browser(proc)
            assert isinstance(result, bool)

    def test_handles_unexpected_error(self):
        """Should handle unexpected errors gracefully."""
        proc = Mock(spec=psutil.Process)
        proc.pid = 1234
        proc.cmdline.side_effect = RuntimeError("Unexpected error")

        assert is_automation_browser(proc) is False


class TestFindOrphanedBrowsers:
    """Tests for find_orphaned_browsers() function."""

    def test_finds_automated_chrome(self, mock_automation_process):
        """Should find automated Chrome processes."""
        mock_info = {
            'pid': 1234,
            'name': 'chrome',
            'cmdline': mock_automation_process.cmdline.return_value
        }
        mock_automation_process.info = mock_info

        with patch('psutil.process_iter', return_value=[mock_automation_process]):
            orphans = find_orphaned_browsers()

        assert len(orphans) == 1
        assert orphans[0].pid == 1234

    def test_ignores_normal_browsers(self, mock_normal_process):
        """Should not include normal user browsers."""
        mock_info = {
            'pid': 5678,
            'name': 'chrome',
            'cmdline': mock_normal_process.cmdline.return_value
        }
        mock_normal_process.info = mock_info

        # Mock parent process as non-Python
        parent = Mock(spec=psutil.Process)
        parent.name.return_value = 'systemd'

        with patch('psutil.process_iter', return_value=[mock_normal_process]):
            with patch('psutil.Process', return_value=parent):
                orphans = find_orphaned_browsers()

        assert len(orphans) == 0

    def test_filters_by_process_name(self):
        """Should only check chrome/chromium processes."""
        firefox_proc = Mock(spec=psutil.Process)
        firefox_proc.info = {'pid': 9999, 'name': 'firefox', 'cmdline': ['/usr/bin/firefox']}
        firefox_proc.pid = 9999

        with patch('psutil.process_iter', return_value=[firefox_proc]):
            orphans = find_orphaned_browsers()

        assert len(orphans) == 0

    def test_handles_none_process_name(self):
        """Should handle processes with None name."""
        proc = Mock(spec=psutil.Process)
        proc.info = {'pid': 1234, 'name': None, 'cmdline': []}

        with patch('psutil.process_iter', return_value=[proc]):
            orphans = find_orphaned_browsers()

        assert len(orphans) == 0

    def test_handles_no_such_process_during_iteration(self):
        """Should handle process terminating during iteration."""
        proc = Mock(spec=psutil.Process)
        proc.info = {'pid': 1234, 'name': 'chrome', 'cmdline': []}
        proc.pid = 1234
        proc.cmdline.side_effect = psutil.NoSuchProcess(1234)

        with patch('psutil.process_iter', return_value=[proc]):
            orphans = find_orphaned_browsers()

        # Should not crash
        assert isinstance(orphans, list)

    def test_handles_access_denied_during_iteration(self, mock_automation_process):
        """Should log warning but continue on permission error."""
        mock_info = {
            'pid': 1234,
            'name': 'chrome',
            'cmdline': None
        }
        mock_automation_process.info = mock_info
        mock_automation_process.cmdline.side_effect = psutil.AccessDenied()

        with patch('psutil.process_iter', return_value=[mock_automation_process]):
            orphans = find_orphaned_browsers()

        # Should skip this process
        assert len(orphans) == 0

    def test_handles_zombie_process(self):
        """Should skip zombie processes."""
        proc = Mock(spec=psutil.Process)
        proc.info = {'pid': 1234, 'name': 'chrome', 'cmdline': []}
        proc.pid = 1234

        with patch('psutil.process_iter', side_effect=psutil.ZombieProcess(1234)):
            orphans = find_orphaned_browsers()

        # Should not crash
        assert isinstance(orphans, list)

    def test_finds_multiple_orphaned_browsers(self):
        """Should find multiple orphaned processes."""
        proc1 = Mock(spec=psutil.Process)
        proc1.pid = 1111
        proc1.info = {
            'pid': 1111,
            'name': 'chrome',
            'cmdline': ['chrome', '--remote-debugging-port=9222']
        }
        proc1.cmdline.return_value = ['chrome', '--remote-debugging-port=9222']
        proc1.ppid.return_value = 5000

        proc2 = Mock(spec=psutil.Process)
        proc2.pid = 2222
        proc2.info = {
            'pid': 2222,
            'name': 'chromium',
            'cmdline': ['chromium', '--remote-debugging-port=9223']
        }
        proc2.cmdline.return_value = ['chromium', '--remote-debugging-port=9223']
        proc2.ppid.return_value = 5001

        with patch('psutil.process_iter', return_value=[proc1, proc2]):
            orphans = find_orphaned_browsers()

        assert len(orphans) == 2
        assert orphans[0].pid == 1111
        assert orphans[1].pid == 2222


class TestCleanupOrphanedBrowsers:
    """Tests for cleanup_orphaned_browsers() function."""

    def test_graceful_termination_success(self, mock_automation_process):
        """Should terminate process gracefully with SIGTERM."""
        mock_automation_process.wait.return_value = None  # Successful wait
        mock_automation_process.is_running.return_value = False

        stats = cleanup_orphaned_browsers([mock_automation_process])

        assert stats['killed'] == 1
        assert stats['failed'] == 0
        assert stats['total'] == 1
        mock_automation_process.terminate.assert_called_once()
        mock_automation_process.kill.assert_not_called()

    def test_force_kill_after_timeout(self, mock_automation_process):
        """Should force kill if graceful termination times out."""
        mock_automation_process.wait.side_effect = psutil.TimeoutExpired(3.0)
        mock_automation_process.is_running.side_effect = [True, False]

        stats = cleanup_orphaned_browsers([mock_automation_process])

        assert stats['killed'] == 1
        assert stats['failed'] == 0
        mock_automation_process.terminate.assert_called_once()
        mock_automation_process.kill.assert_called_once()

    def test_force_mode_skips_graceful(self, mock_automation_process):
        """Should skip graceful termination when force=True."""
        mock_automation_process.is_running.side_effect = [True, False]

        stats = cleanup_orphaned_browsers([mock_automation_process], force=True)

        assert stats['killed'] == 1
        assert stats['failed'] == 0
        mock_automation_process.terminate.assert_not_called()
        mock_automation_process.kill.assert_called_once()

    def test_handles_already_terminated_process(self, mock_automation_process):
        """Should count already-terminated process as success."""
        mock_automation_process.terminate.side_effect = psutil.NoSuchProcess(1234)

        stats = cleanup_orphaned_browsers([mock_automation_process])

        assert stats['killed'] == 1
        assert stats['failed'] == 0

    def test_handles_access_denied(self, mock_automation_process):
        """Should count permission error as failure."""
        mock_automation_process.terminate.side_effect = psutil.AccessDenied()

        stats = cleanup_orphaned_browsers([mock_automation_process])

        assert stats['killed'] == 0
        assert stats['failed'] == 1

    def test_handles_kill_failure(self, mock_automation_process):
        """Should count as failure if process survives SIGKILL."""
        mock_automation_process.wait.side_effect = psutil.TimeoutExpired(3.0)
        mock_automation_process.is_running.return_value = True  # Still running

        stats = cleanup_orphaned_browsers([mock_automation_process])

        assert stats['killed'] == 0
        assert stats['failed'] == 1

    def test_empty_process_list(self):
        """Should handle empty process list gracefully."""
        stats = cleanup_orphaned_browsers([])

        assert stats['killed'] == 0
        assert stats['failed'] == 0
        assert stats['total'] == 0

    def test_multiple_processes_mixed_results(self):
        """Should handle mix of successful and failed terminations."""
        proc1 = Mock(spec=psutil.Process)
        proc1.pid = 1111
        proc1.name.return_value = 'chrome'
        proc1.cmdline.return_value = ['chrome']
        proc1.wait.return_value = None
        proc1.is_running.return_value = False

        proc2 = Mock(spec=psutil.Process)
        proc2.pid = 2222
        proc2.name.return_value = 'chrome'
        proc2.cmdline.return_value = ['chrome']
        proc2.terminate.side_effect = psutil.AccessDenied()

        stats = cleanup_orphaned_browsers([proc1, proc2])

        assert stats['killed'] == 1
        assert stats['failed'] == 1
        assert stats['total'] == 2

    def test_handles_cmdline_access_denied(self, mock_automation_process):
        """Should handle permission error when logging cmdline."""
        mock_automation_process.cmdline.side_effect = psutil.AccessDenied()
        mock_automation_process.wait.return_value = None
        mock_automation_process.is_running.return_value = False

        stats = cleanup_orphaned_browsers([mock_automation_process])

        # Should still terminate successfully
        assert stats['killed'] == 1
        assert stats['failed'] == 0


class TestCleanupOnStartup:
    """Tests for cleanup_on_startup() function."""

    @patch('src.utils.process_cleanup.find_orphaned_browsers')
    @patch('src.utils.process_cleanup.cleanup_orphaned_browsers')
    def test_normal_cleanup(self, mock_cleanup, mock_find, mock_automation_process):
        """Should find and cleanup orphaned browsers."""
        mock_find.return_value = [mock_automation_process]
        mock_cleanup.return_value = {'killed': 1, 'failed': 0, 'total': 1}

        stats = cleanup_on_startup()

        assert stats['killed'] == 1
        assert stats['failed'] == 0
        mock_find.assert_called_once()
        mock_cleanup.assert_called_once_with([mock_automation_process])

    @patch('src.utils.process_cleanup.find_orphaned_browsers')
    def test_no_orphans_found(self, mock_find):
        """Should return empty stats if no orphans found."""
        mock_find.return_value = []

        stats = cleanup_on_startup()

        assert stats['killed'] == 0
        assert stats['failed'] == 0
        assert stats['total'] == 0

    @patch('src.utils.process_cleanup.find_orphaned_browsers')
    def test_dry_run_mode(self, mock_find, mock_automation_process):
        """Should report what would be cleaned without actually killing."""
        mock_automation_process.cmdline.return_value = ['chrome', '--remote-debugging-port=9222']
        mock_find.return_value = [mock_automation_process]

        stats = cleanup_on_startup(dry_run=True)

        assert stats['would_kill'] == 1
        assert stats['total'] == 1
        # Should not call cleanup function
        mock_automation_process.terminate.assert_not_called()
        mock_automation_process.kill.assert_not_called()

    @patch('src.utils.process_cleanup.find_orphaned_browsers')
    @patch('src.utils.process_cleanup.SHUTDOWN_CONFIG', {'enable_orphan_cleanup': False})
    def test_respects_disabled_config(self, mock_find):
        """Should skip cleanup if disabled in config."""
        stats = cleanup_on_startup()

        assert stats['killed'] == 0
        assert stats['failed'] == 0
        assert stats['total'] == 0
        mock_find.assert_not_called()

    @patch('src.utils.process_cleanup.find_orphaned_browsers')
    @patch('src.utils.process_cleanup.cleanup_orphaned_browsers')
    def test_dry_run_handles_access_denied_cmdline(self, mock_cleanup, mock_find):
        """Should handle permission error when logging in dry run."""
        proc = Mock(spec=psutil.Process)
        proc.pid = 1234
        proc.name.return_value = 'chrome'
        proc.cmdline.side_effect = psutil.AccessDenied()
        mock_find.return_value = [proc]

        stats = cleanup_on_startup(dry_run=True)

        # Should not crash
        assert stats['would_kill'] == 1
        assert stats['total'] == 1

    @patch('src.utils.process_cleanup.find_orphaned_browsers')
    @patch('src.utils.process_cleanup.cleanup_orphaned_browsers')
    def test_logs_cleanup_failures(self, mock_cleanup, mock_find, mock_automation_process):
        """Should log warning if cleanup had failures."""
        mock_find.return_value = [mock_automation_process]
        mock_cleanup.return_value = {'killed': 0, 'failed': 1, 'total': 1}

        stats = cleanup_on_startup()

        assert stats['killed'] == 0
        assert stats['failed'] == 1
        # Function should complete successfully even with failures


@pytest.mark.integration
class TestProcessCleanupIntegration:
    """Integration tests using real psutil (if safe to run)."""

    def test_find_orphaned_browsers_real_processes(self):
        """Should scan real processes without crashing."""
        # This test runs against actual system processes
        # It should not find any orphans (unless there actually are some)
        orphans = find_orphaned_browsers()

        # Just verify it returns a list
        assert isinstance(orphans, list)
        # Each item should be a psutil.Process
        for proc in orphans:
            assert isinstance(proc, psutil.Process)

    @pytest.mark.skip(reason="Don't actually kill processes in tests")
    def test_cleanup_orphaned_browsers_real(self):
        """Would test real cleanup - skipped for safety."""
        # This test is skipped to avoid killing actual processes
        # Could be enabled in isolated test environment
        pass
