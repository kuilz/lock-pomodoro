from __future__ import annotations

from ctypes import cdll
import subprocess
from dataclasses import dataclass


LOGIN_FRAMEWORK_PATH = "/System/Library/PrivateFrameworks/login.framework/Versions/Current/login"
LOGIN_FRAMEWORK_SYMBOL = "SACLockScreenImmediate"

APPLE_SCRIPTS = (
    (
        "osascript:key_code",
        """
tell application "System Events"
    key code 12 using {control down, command down}
end tell
""".strip(),
    ),
    (
        "osascript:keystroke",
        """
tell application "System Events"
    keystroke "q" using {control down, command down}
end tell
""".strip(),
    ),
)


@dataclass(frozen=True)
class LockScreenResult:
    success: bool
    message: str


def lock_screen() -> LockScreenResult:
    errors: list[str] = []

    login_result = _lock_with_login_framework()
    if login_result.success:
        return login_result
    errors.append(login_result.message)

    for strategy, script in APPLE_SCRIPTS:
        result = _run_apple_script(strategy, script)
        if result.success:
            return result
        errors.append(result.message)

    return LockScreenResult(False, "Lock screen failed. " + " | ".join(errors))


def _lock_with_login_framework() -> LockScreenResult:
    try:
        login_framework = cdll.LoadLibrary(LOGIN_FRAMEWORK_PATH)
    except OSError as exc:
        return LockScreenResult(
            False,
            f"login.framework load failed: {exc}",
        )

    try:
        lock_function = getattr(login_framework, LOGIN_FRAMEWORK_SYMBOL)
    except AttributeError as exc:
        return LockScreenResult(
            False,
            f"{LOGIN_FRAMEWORK_SYMBOL} is unavailable: {exc}",
        )

    try:
        lock_function.restype = None
        lock_function()
    except Exception as exc:  # pragma: no cover - defensive path
        return LockScreenResult(
            False,
            f"{LOGIN_FRAMEWORK_SYMBOL} call failed: {exc}",
        )

    return LockScreenResult(True, f"Screen locked ({LOGIN_FRAMEWORK_SYMBOL}).")


def _run_apple_script(strategy: str, script: str) -> LockScreenResult:
    try:
        completed = subprocess.run(
            ["/usr/bin/osascript", "-e", script],
            capture_output=True,
            text=True,
            check=False,
        )
    except FileNotFoundError:
        return LockScreenResult(False, f"{strategy} failed: osascript is not available on this system.")
    except Exception as exc:  # pragma: no cover - defensive path
        return LockScreenResult(False, f"{strategy} failed: unexpected error: {exc}")

    if completed.returncode == 0:
        return LockScreenResult(True, f"Screen locked ({strategy}).")

    stderr = completed.stderr.strip() or completed.stdout.strip() or "Unknown AppleScript error."
    return LockScreenResult(
        False,
        f"{strategy} failed: returncode={completed.returncode}, details={stderr}",
    )
