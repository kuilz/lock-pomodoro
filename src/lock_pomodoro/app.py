from __future__ import annotations

import time
from pathlib import Path

import objc
from AppKit import (
    NSApp,
    NSApplication,
    NSApplicationActivationPolicyAccessory,
    NSBackingStoreBuffered,
    NSBezelStyleRounded,
    NSButton,
    NSButtonTypeSwitch,
    NSControlStateValueOn,
    NSFont,
    NSImage,
    NSMakeRect,
    NSStatusBar,
    NSTextAlignmentCenter,
    NSTextField,
    NSImageOnly,
    NSSquareStatusItemLength,
    NSVariableStatusItemLength,
    NSWindow,
    NSWindowStyleMaskClosable,
    NSWindowStyleMaskMiniaturizable,
    NSWindowStyleMaskTitled,
)
from Foundation import NSObject, NSTimer, NSUserDefaults

from lock_pomodoro.engine import EngineSnapshot, PomodoroConfig, PomodoroEngine
from lock_pomodoro.lockscreen import lock_screen

WINDOW_WIDTH = 440
WINDOW_HEIGHT = 620
TIMER_INTERVAL = 0.25
DEFAULTS_WORK_MINUTES = "work_minutes"
DEFAULTS_CYCLES_PER_ROUND = "cycles_per_round"
DEFAULTS_SHORT_BREAK_MINUTES = "short_break_minutes"
DEFAULTS_LONG_BREAK_MINUTES = "long_break_minutes"
DEFAULTS_LOCK_ENABLED = "lock_enabled"


class LockPomodoroApp(NSObject):
    def init(self):
        self = objc.super(LockPomodoroApp, self).init()
        if self is None:
            return None

        self.engine: PomodoroEngine | None = None
        self.timer = None
        self.window_visible = False

        self.work_input = None
        self.cycles_input = None
        self.short_break_input = None
        self.long_break_input = None
        self.lock_checkbox = None

        self.phase_label = None
        self.time_label = None
        self.progress_label = None
        self.status_label = None

        self.start_button = None
        self.pause_button = None
        self.reset_button = None
        self.config_controls: list[object] = []
        self.status_item = None
        self.window = None
        return self

    def applicationDidFinishLaunching_(self, _notification) -> None:
        NSApp().setActivationPolicy_(NSApplicationActivationPolicyAccessory)
        self._set_application_icon()
        self._build_status_item()
        self._build_window()
        self._load_saved_config()
        self.reset()
        self.show_window()
        self._start_timer_loop()

    def applicationShouldTerminateAfterLastWindowClosed_(self, _application) -> bool:
        return False

    def windowShouldClose_(self, _sender) -> bool:
        self.hide_window()
        return False

    @objc.IBAction
    def toggleWindow_(self, _sender) -> None:
        if self._is_window_showing():
            self.hide_window()
        else:
            self.show_window()

    @objc.IBAction
    def start_(self, _sender) -> None:
        self.start()

    @objc.IBAction
    def pause_(self, _sender) -> None:
        self.pause()

    @objc.IBAction
    def reset_(self, _sender) -> None:
        self.reset()

    @objc.IBAction
    def hideWindow_(self, _sender) -> None:
        self.hide_window()

    @objc.IBAction
    def quit_(self, _sender) -> None:
        self.quit()

    @objc.IBAction
    def saveConfig_(self, _sender) -> None:
        self._save_current_config_if_valid()

    @objc.python_method
    def start(self) -> None:
        try:
            config = self._read_config()
        except ValueError as exc:
            self._set_status(str(exc))
            return
        self._save_config(config)

        if self.engine is None or self.engine.config != config:
            self.engine = PomodoroEngine(config)
            self._update_display(self.engine.snapshot())

        snapshot = self.engine.start(time.monotonic())
        self._update_display(snapshot)
        self._set_inputs_enabled(False)
        self._set_status("Running")

    @objc.python_method
    def pause(self) -> None:
        if self.engine is None:
            return
        snapshot = self.engine.pause(time.monotonic())
        self._set_status("Paused")
        self._update_display(snapshot)

    @objc.python_method
    def reset(self) -> None:
        if self.engine is None:
            try:
                config = self._read_config()
            except ValueError:
                config = PomodoroConfig()
            self._save_config(config)
            snapshot = PomodoroEngine(config).snapshot()
        else:
            snapshot = self.engine.reset(time.monotonic())
            self.engine = None
        self._set_inputs_enabled(True)
        self._set_status("Ready")
        self._update_display(snapshot)

    @objc.python_method
    def show_window(self) -> None:
        if self.window is None:
            return
        self.window_visible = True
        NSApp().activateIgnoringOtherApps_(True)
        if self.window.isMiniaturized():
            self.window.deminiaturize_(None)
        self.window.makeKeyAndOrderFront_(None)
        self.window.orderFrontRegardless()

    @objc.python_method
    def hide_window(self) -> None:
        if self.window is None:
            return
        self.window_visible = False
        if self.window.isMiniaturized():
            self.window.deminiaturize_(None)
        self.window.orderOut_(None)

    @objc.python_method
    def quit(self) -> None:
        if self.timer is not None:
            self.timer.invalidate()
            self.timer = None
        if self.status_item is not None:
            NSStatusBar.systemStatusBar().removeStatusItem_(self.status_item)
            self.status_item = None
        NSApp().terminate_(None)

    def handleTimer_(self, _timer) -> None:
        now = time.monotonic()
        if self.engine is None or not self.engine.is_running:
            return

        result = self.engine.tick(now)
        self._update_display(result.snapshot)
        if result.work_completion_count > 0:
            lock_result = None
            for _ in range(result.work_completion_count):
                lock_result = lock_screen()
            if lock_result is not None:
                self._set_status(lock_result.message)
        elif result.phase_changed:
            self._set_status(f"{result.snapshot.phase_label} started")

    @objc.python_method
    def _start_timer_loop(self) -> None:
        if self.timer is not None:
            return
        self.timer = NSTimer.scheduledTimerWithTimeInterval_target_selector_userInfo_repeats_(
            TIMER_INTERVAL,
            self,
            "handleTimer:",
            None,
            True,
        )

    @objc.python_method
    def _build_status_item(self) -> None:
        self.status_item = NSStatusBar.systemStatusBar().statusItemWithLength_(
            NSSquareStatusItemLength
        )
        button = self.status_item.button()
        if button is None:
            raise RuntimeError("Status bar button is not available")

        image = self._load_status_icon()
        if image is not None:
            image.setTemplate_(True)
            button.setImage_(image)
        button.setTitle_("")
        button.setImagePosition_(NSImageOnly)
        button.setTarget_(self)
        button.setAction_("toggleWindow:")
        button.setToolTip_("Lock Pomodoro")

    @objc.python_method
    def _build_window(self) -> None:
        style_mask = (
            NSWindowStyleMaskTitled
            | NSWindowStyleMaskClosable
            | NSWindowStyleMaskMiniaturizable
        )
        self.window = NSWindow.alloc().initWithContentRect_styleMask_backing_defer_(
            NSMakeRect(0, 0, WINDOW_WIDTH, WINDOW_HEIGHT),
            style_mask,
            NSBackingStoreBuffered,
            False,
        )
        self.window.setTitle_("Lock Pomodoro")
        self.window.center()
        self.window.setReleasedWhenClosed_(False)
        self.window.setDelegate_(self)

        content = self.window.contentView()

        title = self._label(24, 570, 392, 32, "Lock Pomodoro", size=27, bold=True)
        subtitle = self._label(
            24,
            544,
            392,
            34,
            "Minimal pomodoro timer with optional lock screen on work completion.",
            size=12,
        )
        subtitle.setLineBreakMode_(0)
        subtitle.setUsesSingleLineMode_(False)

        self.phase_label = self._label(24, 492, 392, 24, "Work", size=16, bold=True, centered=True)
        self.time_label = self._label(24, 430, 392, 56, "25:00", size=46, bold=True, centered=True)
        self.progress_label = self._label(24, 404, 392, 22, "Cycle 1 / 4", size=12, centered=True)
        self.status_label = self._label(24, 374, 392, 26, "Ready", size=12, centered=True)

        config_title = self._label(24, 336, 392, 24, "Configuration", size=14, bold=True)
        fields_top = 298
        row_gap = 46
        self.work_input = self._number_field(content, 24, fields_top, "Work (minutes)", "25")
        self.cycles_input = self._number_field(content, 24, fields_top - row_gap, "Pomodoros per round", "4")
        self.short_break_input = self._number_field(content, 24, fields_top - row_gap * 2, "Short break (minutes)", "5")
        self.long_break_input = self._number_field(content, 24, fields_top - row_gap * 3, "Long break (minutes)", "15")

        self.lock_checkbox = NSButton.alloc().initWithFrame_(NSMakeRect(24, 118, 280, 24))
        self.lock_checkbox.setButtonType_(NSButtonTypeSwitch)
        self.lock_checkbox.setTitle_("Lock screen when work ends")
        self.lock_checkbox.setState_(NSControlStateValueOn)
        self.lock_checkbox.setFont_(NSFont.systemFontOfSize_(12))
        self.lock_checkbox.setTarget_(self)
        self.lock_checkbox.setAction_("saveConfig:")
        content.addSubview_(self.lock_checkbox)
        self.config_controls.append(self.lock_checkbox)

        self.start_button = self._button(24, 60, 118, 34, "Start", "start:")
        self.pause_button = self._button(160, 60, 118, 34, "Pause", "pause:")
        self.reset_button = self._button(298, 60, 118, 34, "Reset", "reset:")
        hide_button = self._button(292, 22, 60, 30, "Hide", "hideWindow:")
        quit_button = self._button(356, 22, 60, 30, "Quit", "quit:")

        for view in [
            title,
            subtitle,
            self.phase_label,
            self.time_label,
            self.progress_label,
            self.status_label,
            config_title,
            self.start_button,
            self.pause_button,
            self.reset_button,
            hide_button,
            quit_button,
        ]:
            content.addSubview_(view)

    @objc.python_method
    def _label(
        self,
        x: float,
        y: float,
        width: float,
        height: float,
        text: str,
        size: float,
        bold: bool = False,
        centered: bool = False,
    ):
        field = NSTextField.labelWithString_(text)
        field.setFrame_(NSMakeRect(x, y, width, height))
        font = NSFont.boldSystemFontOfSize_(size) if bold else NSFont.systemFontOfSize_(size)
        field.setFont_(font)
        if centered:
            field.setAlignment_(NSTextAlignmentCenter)
        return field

    @objc.python_method
    def _number_field(self, parent, x: float, y: float, label: str, value: str):
        label_view = self._label(x, y + 16, 260, 22, label, size=12)
        field = NSTextField.alloc().initWithFrame_(NSMakeRect(x + 286, y + 10, 106, 30))
        field.setFont_(NSFont.systemFontOfSize_(13))
        field.setStringValue_(value)
        field.setTarget_(self)
        field.setAction_("saveConfig:")
        parent.addSubview_(label_view)
        parent.addSubview_(field)
        self.config_controls.append(field)
        return field

    @objc.python_method
    def _button(self, x: float, y: float, width: float, height: float, title: str, action: str):
        button = NSButton.alloc().initWithFrame_(NSMakeRect(x, y, width, height))
        button.setTitle_(title)
        button.setBezelStyle_(NSBezelStyleRounded)
        button.setFont_(NSFont.systemFontOfSize_(13))
        button.setTarget_(self)
        button.setAction_(action)
        return button

    @objc.python_method
    def _load_status_icon(self):
        symbol = NSImage.imageWithSystemSymbolName_accessibilityDescription_(
            "timer",
            "Lock Pomodoro",
        )
        if symbol is not None:
            return symbol

        candidates = [
            Path(__file__).resolve().parents[2] / "assets" / "menu_template.png",
            Path(__file__).resolve().parents[3] / "Resources" / "menu_template.png",
        ]
        for path in candidates:
            if path.exists():
                return NSImage.alloc().initByReferencingFile_(str(path))
        return None

    @objc.python_method
    def _set_application_icon(self) -> None:
        candidates = [
            Path(__file__).resolve().parents[2] / "assets" / "icon.iconset" / "icon_512x512@2x.png",
            Path(__file__).resolve().parents[3] / "Resources" / "icon_512x512@2x.png",
        ]
        for path in candidates:
            if not path.exists():
                continue
            image = NSImage.alloc().initByReferencingFile_(str(path))
            if image is not None:
                NSApp().setApplicationIconImage_(image)
                return

    @objc.python_method
    def _defaults(self):
        return NSUserDefaults.standardUserDefaults()

    @objc.python_method
    def _load_saved_config(self) -> None:
        defaults = self._defaults()
        defaults.registerDefaults_(
            {
                DEFAULTS_WORK_MINUTES: PomodoroConfig.work_minutes,
                DEFAULTS_CYCLES_PER_ROUND: PomodoroConfig.cycles_per_round,
                DEFAULTS_SHORT_BREAK_MINUTES: PomodoroConfig.short_break_minutes,
                DEFAULTS_LONG_BREAK_MINUTES: PomodoroConfig.long_break_minutes,
                DEFAULTS_LOCK_ENABLED: PomodoroConfig.lock_enabled,
            }
        )

        self.work_input.setStringValue_(self._format_minutes(defaults.doubleForKey_(DEFAULTS_WORK_MINUTES)))
        self.cycles_input.setStringValue_(str(defaults.integerForKey_(DEFAULTS_CYCLES_PER_ROUND)))
        self.short_break_input.setStringValue_(self._format_minutes(defaults.doubleForKey_(DEFAULTS_SHORT_BREAK_MINUTES)))
        self.long_break_input.setStringValue_(self._format_minutes(defaults.doubleForKey_(DEFAULTS_LONG_BREAK_MINUTES)))
        self.lock_checkbox.setState_(
            NSControlStateValueOn if defaults.boolForKey_(DEFAULTS_LOCK_ENABLED) else 0
        )

    @objc.python_method
    def _save_current_config_if_valid(self) -> None:
        try:
            config = self._read_config()
        except ValueError:
            return
        self._save_config(config)

    @objc.python_method
    def _save_config(self, config: PomodoroConfig) -> None:
        defaults = self._defaults()
        defaults.setDouble_forKey_(config.work_minutes, DEFAULTS_WORK_MINUTES)
        defaults.setInteger_forKey_(config.cycles_per_round, DEFAULTS_CYCLES_PER_ROUND)
        defaults.setDouble_forKey_(config.short_break_minutes, DEFAULTS_SHORT_BREAK_MINUTES)
        defaults.setDouble_forKey_(config.long_break_minutes, DEFAULTS_LONG_BREAK_MINUTES)
        defaults.setBool_forKey_(config.lock_enabled, DEFAULTS_LOCK_ENABLED)

    @objc.python_method
    def _format_minutes(self, value: float) -> str:
        return f"{value:g}"

    @objc.python_method
    def _read_config(self) -> PomodoroConfig:
        try:
            config = PomodoroConfig(
                work_minutes=float(self.work_input.stringValue().strip()),
                cycles_per_round=int(self.cycles_input.stringValue().strip()),
                short_break_minutes=float(self.short_break_input.stringValue().strip()),
                long_break_minutes=float(self.long_break_input.stringValue().strip()),
                lock_enabled=self.lock_checkbox.state() == NSControlStateValueOn,
            )
        except ValueError as exc:
            raise ValueError("Time values must be positive numbers. Cycles must be a positive integer.") from exc

        config.validate()
        return config

    @objc.python_method
    def _set_inputs_enabled(self, enabled: bool) -> None:
        for control in self.config_controls:
            control.setEnabled_(enabled)

    @objc.python_method
    def _is_window_showing(self) -> bool:
        if self.window is None:
            return False
        return bool(self.window.isVisible()) and not bool(self.window.isMiniaturized())

    @objc.python_method
    def _set_status(self, text: str) -> None:
        self.status_label.setStringValue_(text)
        self._sync_status_item_tooltip()

    @objc.python_method
    def _update_display(self, snapshot: EngineSnapshot) -> None:
        minutes, seconds = divmod(snapshot.remaining_seconds, 60)
        self.phase_label.setStringValue_(snapshot.phase_label)
        self.time_label.setStringValue_(f"{minutes:02d}:{seconds:02d}")
        self.progress_label.setStringValue_(
            f"Cycle {snapshot.current_cycle} / {snapshot.cycles_per_round}"
        )
        self._sync_status_item_tooltip()

    @objc.python_method
    def _sync_status_item_tooltip(self) -> None:
        if self.status_item is None:
            return
        button = self.status_item.button()
        if button is None:
            return
        button.setToolTip_(
            f"{self.phase_label.stringValue()} · {self.time_label.stringValue()} · {self.status_label.stringValue()}"
        )

def main() -> None:
    app = NSApplication.sharedApplication()
    delegate = LockPomodoroApp.alloc().init()
    app.setDelegate_(delegate)
    app.run()


if __name__ == "__main__":
    main()
