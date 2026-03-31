# Repository Guidelines

## Project Structure & Module Organization
Application code lives in `src/lock_pomodoro/`. `app.py` contains the macOS menu bar UI, `engine.py` holds timer state and phase transitions, and `lockscreen.py` / `menubar.py` wrap platform behavior. Tests live in `tests/`, currently centered on `tests/test_engine.py`. Static assets and generated icons are under `assets/`; `scripts/generate_assets.py` rebuilds icon files. Treat `build/`, `dist/`, and `__pycache__/` as generated output, not source.

## Build, Test, and Development Commands
Use `uv` for local setup and execution:

- `uv sync` installs runtime dependencies into the project environment.
- `uv run lock-pomodoro` launches the app through the console entry point.
- `uv run python -m unittest discover -s tests` runs the test suite.
- `uv sync --extra build` installs PyInstaller and other build-only dependencies.
- `uv run pyinstaller lock_pomodoro.spec` builds `dist/Lock Pomodoro.app`.

Run commands from the repository root.

## Coding Style & Naming Conventions
Follow existing Python style: 4-space indentation, type hints on public methods, and small focused classes. Use `snake_case` for functions, methods, and modules; `PascalCase` for classes; `UPPER_SNAKE_CASE` for constants such as phase names and defaults keys. Prefer standard library features plus the declared PyObjC dependency over adding new packages. No formatter or linter is configured in `pyproject.toml`, so keep edits consistent with surrounding code and imports grouped cleanly.

## Testing Guidelines
Tests use the standard `unittest` framework. Add new test cases in `tests/test_<module>.py` and name methods `test_<behavior>`. Favor deterministic engine-level tests over UI automation; cover phase transitions, lock behavior, and config validation when changing timer logic.

## Commit & Pull Request Guidelines
Git history is not included in this workspace snapshot, so no repository-specific commit pattern can be inferred. Use short, imperative commit subjects such as `Add long-break reset test`. PRs should describe the user-visible change, list verification steps, and include screenshots when UI layout or menu bar behavior changes.

## Agent Notes
Do not hand-edit packaged app contents in `dist/` or PyInstaller output in `build/`. Change source files, then rebuild artifacts from source when needed.
