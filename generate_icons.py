"""Generate tray icon assets for Transcriptor."""

from pathlib import Path
from PIL import Image, ImageDraw

ASSETS_DIR = Path(__file__).parent / "transcriptor" / "assets"
SIZE = 64
MARGIN = 4


def make_icon(color: str, filename: str) -> None:
    img = Image.new("RGBA", (SIZE, SIZE), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)

    # Outer circle (dark border)
    draw.ellipse([MARGIN, MARGIN, SIZE - MARGIN, SIZE - MARGIN], fill="#333333")
    # Inner circle (colored)
    inner = MARGIN + 4
    draw.ellipse([inner, inner, SIZE - inner, SIZE - inner], fill=color)

    # Microphone symbol (simple vertical line + base)
    cx, cy = SIZE // 2, SIZE // 2
    # Mic body
    draw.rounded_rectangle(
        [cx - 5, cy - 12, cx + 5, cy + 4],
        radius=5, fill="white",
    )
    # Mic stand
    draw.line([cx, cy + 4, cx, cy + 10], fill="white", width=2)
    draw.line([cx - 6, cy + 10, cx + 6, cy + 10], fill="white", width=2)

    ASSETS_DIR.mkdir(parents=True, exist_ok=True)
    img.save(ASSETS_DIR / filename)
    print(f"  Created {filename}")


if __name__ == "__main__":
    print("Generating icons...")
    make_icon("#4CAF50", "icon_idle.png")        # Green
    make_icon("#F44336", "icon_recording.png")    # Red
    make_icon("#FFC107", "icon_processing.png")   # Yellow/Amber
    print("Done.")
