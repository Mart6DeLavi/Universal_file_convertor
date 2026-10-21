from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from file_converter.logging_config import configure_logging


def main() -> int:
    configure_logging()
    try:
        from file_converter.gui.main_window import MainWindow
    except ModuleNotFoundError as exc:
        print(f"Could not load the application: {exc}", file=sys.stderr)
        print(
            "Install the dependencies: python -m pip install -r requirements.txt",
            file=sys.stderr,
        )
        return 1

    try:
        window = MainWindow()
    except Exception as exc:
        print(f"Could not start the GUI: {exc}", file=sys.stderr)
        print("Make sure Python was built with Tk support (python-tk).", file=sys.stderr)
        return 1
    window.mainloop()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
