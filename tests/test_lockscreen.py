import unittest
from unittest.mock import Mock, patch

from lock_pomodoro.lockscreen import (
    APPLE_SCRIPTS,
    LOGIN_FRAMEWORK_SYMBOL,
    LockScreenResult,
    _lock_with_login_framework,
    _run_apple_script,
    lock_screen,
)


class _CompletedProcess:
    def __init__(self, returncode: int, stderr: str = "", stdout: str = "") -> None:
        self.returncode = returncode
        self.stderr = stderr
        self.stdout = stdout


class LockScreenTests(unittest.TestCase):
    def test_lock_screen_prefers_login_framework(self) -> None:
        with patch(
            "lock_pomodoro.lockscreen._lock_with_login_framework",
            return_value=LockScreenResult(True, f"Screen locked ({LOGIN_FRAMEWORK_SYMBOL})."),
        ), patch("lock_pomodoro.lockscreen.subprocess.run") as run_mock:
            result = lock_screen()

        self.assertTrue(result.success)
        self.assertIn(LOGIN_FRAMEWORK_SYMBOL, result.message)
        run_mock.assert_not_called()

    def test_lock_screen_falls_back_to_apple_script(self) -> None:
        calls: list[list[str]] = []

        def fake_run(args, capture_output, text, check):
            calls.append(args)
            if len(calls) == 1:
                return _CompletedProcess(1, stderr="first failure")
            return _CompletedProcess(0)

        with patch(
            "lock_pomodoro.lockscreen._lock_with_login_framework",
            return_value=LockScreenResult(False, "login.framework load failed: boom"),
        ), patch("lock_pomodoro.lockscreen.subprocess.run", side_effect=fake_run):
            result = lock_screen()

        self.assertTrue(result.success)
        self.assertIn("osascript:keystroke", result.message)
        self.assertEqual(calls[0], ["/usr/bin/osascript", "-e", APPLE_SCRIPTS[0][1]])
        self.assertEqual(calls[1], ["/usr/bin/osascript", "-e", APPLE_SCRIPTS[1][1]])

    def test_lock_screen_reports_all_failures(self) -> None:
        with patch(
            "lock_pomodoro.lockscreen._lock_with_login_framework",
            return_value=LockScreenResult(False, "login.framework load failed: boom"),
        ), patch(
            "lock_pomodoro.lockscreen.subprocess.run",
            side_effect=[
                _CompletedProcess(1, stderr="first failure"),
                _CompletedProcess(1, stderr="second failure"),
            ],
        ):
            result = lock_screen()

        self.assertFalse(result.success)
        self.assertIn("login.framework load failed: boom", result.message)
        self.assertIn("osascript:key_code failed: returncode=1, details=first failure", result.message)
        self.assertIn("osascript:keystroke failed: returncode=1, details=second failure", result.message)

    def test_lock_with_login_framework_calls_private_api(self) -> None:
        lock_function = Mock()
        login_framework = Mock()
        login_framework.SACLockScreenImmediate = lock_function

        with patch("lock_pomodoro.lockscreen.cdll.LoadLibrary", return_value=login_framework):
            result = _lock_with_login_framework()

        self.assertTrue(result.success)
        self.assertIn(LOGIN_FRAMEWORK_SYMBOL, result.message)
        lock_function.assert_called_once_with()

    def test_run_apple_script_handles_missing_osascript(self) -> None:
        with patch("lock_pomodoro.lockscreen.subprocess.run", side_effect=FileNotFoundError):
            result = _run_apple_script("osascript:key_code", "tell application \"System Events\" to beep")

        self.assertEqual(
            result,
            LockScreenResult(False, "osascript:key_code failed: osascript is not available on this system."),
        )


if __name__ == "__main__":
    unittest.main()
