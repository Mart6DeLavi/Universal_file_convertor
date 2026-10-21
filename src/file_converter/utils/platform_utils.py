from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

from ..exceptions import FileConverterError


def _launch(command: list[str]) -> None:
    try:
        subprocess.Popen(
            command,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            shell=False,
        )
    except OSError as exc:
        raise FileConverterError(
            "Could not open the system item.",
            f"Command: {' '.join(command)}. Reason: {exc}",
        ) from exc


def open_file(path: Path) -> None:
    path = Path(path)
    if not path.is_file():
        raise FileConverterError(f"File not found: {path}")
    if sys.platform == "darwin":
        _launch(["open", str(path)])
    elif os.name == "nt":
        os.startfile(str(path))  # type: ignore[attr-defined]
    else:
        _launch(["xdg-open", str(path)])


def open_folder(path: Path) -> None:
    path = Path(path)
    if not path.is_dir():
        raise FileConverterError(f"Folder not found: {path}")
    if sys.platform == "darwin":
        _launch(["open", str(path)])
    elif os.name == "nt":
        os.startfile(str(path))  # type: ignore[attr-defined]
    else:
        _launch(["xdg-open", str(path)])
