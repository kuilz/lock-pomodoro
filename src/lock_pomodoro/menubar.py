from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

from AppKit import (
    NSApp,
    NSImage,
    NSStatusBar,
    NSVariableStatusItemLength,
)
from Foundation import NSObject
import objc

if TYPE_CHECKING:
    from lock_pomodoro.app import LockPomodoroApp


class _StatusBarDelegate(NSObject):
    def initWithApp_(self, app: "LockPomodoroApp"):
        self = objc.super(_StatusBarDelegate, self).init()
        if self is None:
            return None
        self.app = app
        return self

    @objc.IBAction
    def togglePanel_(self, _sender) -> None:
        self.app.toggle_window()


class MenuBarController:
    def __init__(self, app: "LockPomodoroApp") -> None:
        self.app = app
        self.is_available = False
        self.delegate = _StatusBarDelegate.alloc().initWithApp_(app)
        self.status_item = None

        try:
            self.status_item = NSStatusBar.systemStatusBar().statusItemWithLength_(
                NSVariableStatusItemLength
            )
            self._build_status_item()
            self.is_available = True
        except Exception:
            self.status_item = None
            self.is_available = False

    def _build_status_item(self) -> None:
        button = self.status_item.button()
        if button is None:
            raise RuntimeError("Status bar button is not available")
        image = self._load_template_image()
        if image is not None:
            image.setTemplate_(True)
            button.setImage_(image)
        button.setTitle_("LP")

        button.setTarget_(self.delegate)
        button.setAction_("togglePanel:")

    def update_title(self, title: str) -> None:
        if self.status_item is None:
            return
        button = self.status_item.button()
        if button is not None:
            button.setToolTip_(title)

    def remove(self) -> None:
        if self.status_item is not None:
            NSStatusBar.systemStatusBar().removeStatusItem_(self.status_item)

    def activate(self) -> None:
        if NSApp() is not None:
            NSApp().activateIgnoringOtherApps_(True)

    def _load_template_image(self):
        candidates = [
            Path(__file__).resolve().parents[2] / "assets" / "menu_template.png",
            Path(__file__).resolve().parents[3] / "Resources" / "menu_template.png",
        ]
        for path in candidates:
            if path.exists():
                return NSImage.alloc().initByReferencingFile_(str(path))
        return None
