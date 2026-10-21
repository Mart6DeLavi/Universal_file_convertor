from __future__ import annotations

import os
import re
import tempfile
from pathlib import Path

from ..exceptions import ValidationError

_INVALID_CHARS = re.compile(r'[<>:"/\\|?*\x00-\x1f]')
_WINDOWS_RESERVED = {
    "CON", "PRN", "AUX", "NUL",
    *(f"COM{i}" for i in range(1, 10)),
    *(f"LPT{i}" for i in range(1, 10)),
}


def human_size(size: int) -> str:
    value = float(size)
    for unit in ("B", "KB", "MB", "GB", "TB"):
        if value < 1024 or unit == "TB":
            if unit == "B":
                return f"{int(value)} {unit}"
            return f"{value:.1f} {unit}"
        value /= 1024
    return f"{size} B"


def sanitize_stem(stem: str) -> str:
    cleaned = _INVALID_CHARS.sub("_", stem).strip().strip(".")
    if not cleaned:
        cleaned = "converted"
    if cleaned.split(".")[0].upper() in _WINDOWS_RESERVED:
        cleaned = f"_{cleaned}"
    return cleaned


def validate_output_name(name: str) -> str:
    if name is None:
        raise ValidationError("The output file name was not provided.")
    name = name.strip()
    if not name:
        raise ValidationError("The output file name cannot be empty.")
    if name in {".", ".."}:
        raise ValidationError("Invalid output file name.")
    if Path(name).name != name:
        raise ValidationError(
            "The output file name must not contain a path.",
            "Provide only the file name, for example report.pdf.",
        )
    if _INVALID_CHARS.search(name):
        raise ValidationError(
            "The name contains invalid characters: < > : \" / \\ | ? *",
            "Remove these characters from the name.",
        )
    if name.split(".")[0].upper() in _WINDOWS_RESERVED:
        raise ValidationError("This name is reserved by Windows.", "Choose another name.")
    if len(name) > 200:
        raise ValidationError("The file name is too long (more than 200 characters).")
    return name


def build_output_name(source_stem: str, target_format: str, name: str | None = None) -> str:
    if name:
        return validate_output_name(name)
    return f"{sanitize_stem(source_stem)}.{target_format}"


def unique_path(path: Path) -> Path:
    path = Path(path)
    if not path.exists():
        return path
    index = 1
    while True:
        candidate = path.with_name(f"{path.stem} ({index}){path.suffix}")
        if not candidate.exists():
            return candidate
        index += 1


def directory_is_writable(directory: Path) -> bool:
    directory = Path(directory)
    if not directory.is_dir():
        return False
    try:
        with tempfile.NamedTemporaryFile(
            dir=directory, prefix=".ufc-check-", suffix=".tmp", delete=True
        ):
            return True
    except OSError:
        return False


def same_file(first: Path, second: Path) -> bool:
    try:
        return os.path.samefile(first, second)
    except OSError:
        return Path(first).resolve() == Path(second).resolve()
