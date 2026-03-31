# Lock Pomodoro

Minimal macOS pomodoro menu bar app built with Python and native `PyObjC/AppKit`.

## What It Does

- Runs as a menu bar utility with a small control window
- Tracks work, short break, and long break phases in a repeating round loop
- Lets you configure work duration, breaks, cycles per round, and whether macOS should lock when work ends
- Persists the last saved configuration through `NSUserDefaults`
- Supports start, pause, reset, hide, and quit actions

## Requirements

- macOS
- Python 3.11+
- `uv` for dependency management and command execution

Lock screen support uses AppleScript to send `Control + Command + Q`, so macOS may prompt for Accessibility or Automation permission.

## Run Locally

```bash
uv sync
uv run lock-pomodoro
```

The app opens a control panel window and adds a timer icon to the macOS menu bar. Clicking the menu bar icon toggles the window.

## Test

```bash
uv run python -m unittest discover -s tests
```

Tests currently focus on `PomodoroEngine` behavior such as phase transitions, reset/pause handling, fractional minute support, and lock-trigger rules.

## Build the App Bundle

```bash
uv sync --extra build
uv run pyinstaller lock_pomodoro.spec
```

The packaged app is generated at `dist/Lock Pomodoro.app`.

## Project Structure

- `src/lock_pomodoro/app.py`: AppKit UI, timer loop, saved settings, and menu bar integration
- `src/lock_pomodoro/engine.py`: Pure timer state machine and phase progression logic
- `src/lock_pomodoro/lockscreen.py`: macOS lock-screen trigger via `osascript`
- `tests/test_engine.py`: unit tests for timer behavior
- `assets/`: app icons and menu bar image assets
- `scripts/generate_assets.py`: regenerates icon files used by the app bundle

## Development Notes

Edit source files under `src/` and regenerate build output when needed. Do not manually modify generated artifacts under `build/` or `dist/`.
