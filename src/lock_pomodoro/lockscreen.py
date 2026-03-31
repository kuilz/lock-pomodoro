from __future__ import annotations

import subprocess
from dataclasses import dataclass


APPLE_SCRIPT = """
tell application "System Events"
    key code 12 using {control down, command down}
end tell
""".strip()


@dataclass(frozen=True)
class LockScreenResult:
    success: bool
    message: str


def lock_screen() -> LockScreenResult:
    try:
        completed = subprocess.run(
            ["/usr/bin/osascript", "-e", APPLE_SCRIPT],
            capture_output=True,
            text=True,
            check=False,
        )
    except FileNotFoundError:
        return LockScreenResult(False, "osascript is not available on this system.")
    except Exception as exc:  # pragma: no cover - defensive path
        return LockScreenResult(False, f"Lock screen failed: {exc}")

    if completed.returncode == 0:
        return LockScreenResult(True, "Screen locked.")

    stderr = completed.stderr.strip() or completed.stdout.strip() or "Unknown AppleScript error."
    return LockScreenResult(
        False,
        "Lock screen failed. macOS may require Accessibility or Automation permission. "
        f"Details: {stderr}",
    )
