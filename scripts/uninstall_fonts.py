import shutil
from pathlib import Path

FONT_FILES = [
    "NotoSansCJKjp-Regular.otf",
    "NotoSansCJKsc-Regular.otf",
    "NotoSansCJKkr-Regular.otf",
    "NotoSansCJKtc-Regular.otf",
]


def uninstall():
    fonts_dir = Path.home() / ".local" / "share" / "fonts"
    removed = 0
    for filename in FONT_FILES:
        target = fonts_dir / filename
        if target.exists():
            target.unlink()
            removed += 1

    if removed > 0:
        try:
            import subprocess
            subprocess.run(["fc-cache", "-f"], capture_output=True, timeout=10)
        except Exception:
            pass

    print(f"Eliminadas {removed} fuentes CJK.")


if __name__ == "__main__":
    uninstall()
