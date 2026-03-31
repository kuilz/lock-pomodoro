hiddenimports = ["AppKit", "Foundation", "objc"]


a = Analysis(
    ["main.py"],
    pathex=["src"],
    binaries=[],
    datas=[("assets/menu_template.png", ".")],
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
    optimize=0,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    [],
    name="Lock Pomodoro",
    debug=False,
    bootloader_ignore_signals=False,
    exclude_binaries=True,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    argv_emulation=False,
)

coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name="Lock Pomodoro",
)

app = BUNDLE(
    coll,
    name="Lock Pomodoro.app",
    icon="assets/icon.iconset/icon_512x512@2x.png",
    bundle_identifier="com.kuilz.lockpomodoro",
    info_plist={
        "LSUIElement": True,
        "NSAppleEventsUsageDescription": "Lock Pomodoro uses Apple Events to trigger the macOS lock screen shortcut.",
    },
)
