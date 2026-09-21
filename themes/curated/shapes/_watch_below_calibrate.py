"""Watch inbox/calibrated-below.svg → import paths → rebuild below board.

Run: python themes/curated/shapes/_watch_below_calibrate.py
Then in Figma: Export frame as SVG → save as inbox/calibrated-below.svg
"""
from __future__ import annotations

import subprocess
import sys
import time
from pathlib import Path

OUT = Path(r"d:\Cursor\clothing_shop\themes\curated\shapes")
INBOX = OUT / "inbox" / "calibrated-below.svg"
PY = Path(r"d:\Cursor\clothing_shop\venv\Scripts\python.exe")


def run(script: str) -> None:
    cmd = [str(PY), str(OUT / script)]
    print(">", " ".join(cmd), flush=True)
    subprocess.check_call(cmd, cwd=str(OUT.parent.parent.parent))


def main() -> None:
    OUT.joinpath("inbox").mkdir(exist_ok=True)
    print("Watching:", INBOX)
    print("Figma → Export SVG → save exactly as calibrated-below.svg in inbox/")
    print("Then this script imports + builds automatically.\n", flush=True)
    seen = INBOX.stat().st_mtime if INBOX.exists() else None
    if INBOX.exists():
        print("Found existing export — importing now…", flush=True)
        run("_import_calibrated_below.py")
        run("_build_below.py")
        print("DONE — refresh http://demo-curated.localhost:8000/", flush=True)
        return
    while True:
        if INBOX.exists():
            m = INBOX.stat().st_mtime
            if seen is None or m > seen:
                # wait for write to finish
                time.sleep(0.6)
                print("Detected export — importing…", flush=True)
                run("_import_calibrated_below.py")
                run("_build_below.py")
                print("DONE — refresh http://demo-curated.localhost:8000/", flush=True)
                return
        time.sleep(0.5)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        sys.exit(0)
