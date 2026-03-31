from __future__ import annotations

import subprocess
from pathlib import Path

from AppKit import (
    NSAffineTransform,
    NSBezierPath,
    NSBitmapImageRep,
    NSCalibratedRGBColorSpace,
    NSColor,
    NSFont,
    NSFontAttributeName,
    NSForegroundColorAttributeName,
    NSGraphicsContext,
    NSImageInterpolationHigh,
    NSPNGFileType,
    NSRectFill,
    NSShadow,
    NSString,
)
from Foundation import NSMakeRect

ROOT = Path(__file__).resolve().parents[1]
ASSETS_DIR = ROOT / "assets"
ICONSET_DIR = ASSETS_DIR / "icon.iconset"
MENU_ICON_PATH = ASSETS_DIR / "menu_template.png"


def rounded_rect(x: float, y: float, width: float, height: float, radius: float):
    return NSBezierPath.bezierPathWithRoundedRect_xRadius_yRadius_(
        NSMakeRect(x, y, width, height),
        radius,
        radius,
    )


def oval(x: float, y: float, width: float, height: float):
    return NSBezierPath.bezierPathWithOvalInRect_(NSMakeRect(x, y, width, height))


def fill_circle(cx: float, cy: float, radius: float, color) -> None:
    color.setFill()
    oval(cx - radius, cy - radius, radius * 2, radius * 2).fill()


def stroke_circle(cx: float, cy: float, radius: float, color, line_width: float) -> None:
    path = oval(cx - radius, cy - radius, radius * 2, radius * 2)
    path.setLineWidth_(line_width)
    color.setStroke()
    path.stroke()


def fill_leaf(cx: float, cy: float, scale: float, rotation_degrees: float, color) -> None:
    path = NSBezierPath.bezierPath()
    path.moveToPoint_((0.0, -11.0))
    path.curveToPoint_controlPoint1_controlPoint2_((10.0, 0.0), (4.0, -13.0), (11.0, -6.0))
    path.curveToPoint_controlPoint1_controlPoint2_((0.0, 11.0), (9.0, 6.0), (4.0, 12.0))
    path.curveToPoint_controlPoint1_controlPoint2_((-10.0, 0.0), (-4.0, 12.0), (-11.0, 6.0))
    path.curveToPoint_controlPoint1_controlPoint2_((0.0, -11.0), (-9.0, -6.0), (-4.0, -13.0))
    path.closePath()

    transform = NSAffineTransform.transform()
    transform.translateXBy_yBy_(cx, cy)
    transform.rotateByDegrees_(rotation_degrees)
    transform.scaleBy_(scale)
    path.transformUsingAffineTransform_(transform)

    color.setFill()
    path.fill()


def fill_stem(x: float, y: float, width: float, height: float, color) -> None:
    color.setFill()
    rounded_rect(x, y, width, height, width / 2).fill()


def draw_timer_face(size: int, monochrome: bool = False) -> NSBitmapImageRep:
    bitmap = NSBitmapImageRep.alloc().initWithBitmapDataPlanes_pixelsWide_pixelsHigh_bitsPerSample_samplesPerPixel_hasAlpha_isPlanar_colorSpaceName_bitmapFormat_bytesPerRow_bitsPerPixel_(
        None,
        size,
        size,
        8,
        4,
        True,
        False,
        NSCalibratedRGBColorSpace,
        0,
        0,
        0,
    )
    context = NSGraphicsContext.graphicsContextWithBitmapImageRep_(bitmap)
    NSGraphicsContext.saveGraphicsState()
    NSGraphicsContext.setCurrentContext_(context)
    context.setImageInterpolation_(NSImageInterpolationHigh)

    NSColor.clearColor().set()
    NSRectFill(NSMakeRect(0, 0, size, size))

    if monochrome:
        primary = NSColor.colorWithCalibratedWhite_alpha_(0.0, 1.0)
        face_color = None
        shadow = None
    else:
        shadow = NSShadow.alloc().init()
        shadow.setShadowOffset_((0, -size * 0.018))
        shadow.setShadowBlurRadius_(size * 0.05)
        shadow.setShadowColor_(NSColor.colorWithCalibratedWhite_alpha_(0.0, 0.18))
        shadow.set()

        bg = rounded_rect(size * 0.09, size * 0.09, size * 0.82, size * 0.82, size * 0.24)
        NSColor.colorWithCalibratedRed_green_blue_alpha_(0.95, 0.34, 0.22, 1.0).setFill()
        bg.fill()

        inset = rounded_rect(size * 0.14, size * 0.14, size * 0.72, size * 0.72, size * 0.20)
        NSColor.colorWithCalibratedRed_green_blue_alpha_(0.98, 0.55, 0.28, 1.0).setFill()
        inset.fill()

        primary = NSColor.colorWithCalibratedRed_green_blue_alpha_(0.97, 0.95, 0.90, 1.0)
        face_color = primary

    center_x = size * 0.5
    center_y = size * 0.5

    if not monochrome:
        fill_leaf(
            size * 0.38,
            size * 0.82,
            size * 0.013,
            -24,
            NSColor.colorWithCalibratedRed_green_blue_alpha_(0.18, 0.58, 0.29, 1.0),
        )
        fill_leaf(
            size * 0.58,
            size * 0.83,
            size * 0.0105,
            28,
            NSColor.colorWithCalibratedRed_green_blue_alpha_(0.24, 0.63, 0.30, 1.0),
        )
        fill_stem(
            size * 0.47,
            size * 0.76,
            size * 0.06,
            size * 0.08,
            NSColor.colorWithCalibratedRed_green_blue_alpha_(0.26, 0.44, 0.22, 1.0),
        )

    ring_radius = size * 0.23
    line_width = max(size * 0.038, 1.8)
    stroke_circle(center_x, center_y, ring_radius, primary, line_width)

    tick_path = NSBezierPath.bezierPath()
    tick_path.setLineWidth_(max(size * 0.03, 1.5))
    primary.setStroke()
    tick_path.moveToPoint_((center_x, center_y))
    tick_path.lineToPoint_((center_x + size * 0.10, center_y + size * 0.07))
    tick_path.stroke()

    tick_path = NSBezierPath.bezierPath()
    tick_path.setLineWidth_(max(size * 0.028, 1.4))
    tick_path.moveToPoint_((center_x, center_y))
    tick_path.lineToPoint_((center_x, center_y + size * 0.13))
    tick_path.stroke()

    fill_circle(center_x, center_y, size * 0.024, primary)

    if not monochrome and face_color is not None:
        badge = oval(size * 0.63, size * 0.20, size * 0.15, size * 0.15)
        NSColor.colorWithCalibratedRed_green_blue_alpha_(0.72, 0.16, 0.13, 1.0).setFill()
        badge.fill()
        text = NSString.stringWithString_("LP")
        attributes = {
            NSFontAttributeName: NSFont.boldSystemFontOfSize_(size * 0.072),
            NSForegroundColorAttributeName: face_color,
        }
        text.drawInRect_withAttributes_(NSMakeRect(size * 0.644, size * 0.231, size * 0.13, size * 0.08), attributes)

    NSGraphicsContext.restoreGraphicsState()
    return bitmap


def write_png(bitmap: NSBitmapImageRep, path: Path) -> None:
    data = bitmap.representationUsingType_properties_(NSPNGFileType, None)
    path.write_bytes(bytes(data))


def main() -> None:
    ICONSET_DIR.mkdir(parents=True, exist_ok=True)

    menu_image = draw_timer_face(64, monochrome=True)
    write_png(menu_image, MENU_ICON_PATH)

    master_path = ICONSET_DIR / "icon_512x512@2x.png"
    master_image = draw_timer_face(1024)
    write_png(master_image, master_path)

    outputs = {
        "icon_16x16.png": 16,
        "icon_16x16@2x.png": 32,
        "icon_32x32.png": 32,
        "icon_32x32@2x.png": 64,
        "icon_128x128.png": 128,
        "icon_128x128@2x.png": 256,
        "icon_256x256.png": 256,
        "icon_256x256@2x.png": 512,
        "icon_512x512.png": 512,
        "icon_512x512@2x.png": 1024,
    }
    for filename, target_size in outputs.items():
        output_path = ICONSET_DIR / filename
        if output_path == master_path:
            continue
        subprocess.run(
            [
                "sips",
                "-z",
                str(target_size),
                str(target_size),
                str(master_path),
                "--out",
                str(output_path),
            ],
            check=True,
            capture_output=True,
            text=True,
        )


if __name__ == "__main__":
    main()
