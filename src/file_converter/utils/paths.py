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
    for unit in ("Б", "КБ", "МБ", "ГБ", "ТБ"):
        if value < 1024 or unit == "ТБ":
            if unit == "Б":
                return f"{int(value)} {unit}"
            return f"{value:.1f} {unit}"
        value /= 1024
    return f"{size} Б"


def sanitize_stem(stem: str) -> str:
    cleaned = _INVALID_CHARS.sub("_", stem).strip().strip(".")
    if not cleaned:
        cleaned = "converted"
    if cleaned.split(".")[0].upper() in _WINDOWS_RESERVED:
        cleaned = f"_{cleaned}"
    return cleaned


def validate_output_name(name: str) -> str:
    if name is None:
        raise ValidationError("Имя выходного файла не задано.")
    name = name.strip()
    if not name:
        raise ValidationError("Имя выходного файла не может быть пустым.")
    if name in {".", ".."}:
        raise ValidationError("Недопустимое имя выходного файла.")
    if Path(name).name != name:
        raise ValidationError(
            "Имя выходного файла не должно содержать путь.",
            "Укажите только имя файла, например report.pdf.",
        )
    if _INVALID_CHARS.search(name):
        raise ValidationError(
            "Имя содержит недопустимые символы: < > : \" / \\ | ? *",
            "Уберите эти символы из имени.",
        )
    if name.split(".")[0].upper() in _WINDOWS_RESERVED:
        raise ValidationError("Это имя зарезервировано Windows.", "Выберите другое имя.")
    if len(name) > 200:
        raise ValidationError("Имя файла слишком длинное (более 200 символов).")
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
