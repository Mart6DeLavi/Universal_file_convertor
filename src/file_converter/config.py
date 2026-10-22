from __future__ import annotations

import json
import os
from pathlib import Path

APP_NAME = "Universal File Converter"
APP_VERSION = "1.0.0"

PROJECT_ROOT = Path(__file__).resolve().parents[2]
LOG_DIR = PROJECT_ROOT / "logs"
LOG_FILE = LOG_DIR / "converter.log"
LOG_MAX_BYTES = 1_000_000
LOG_BACKUP_COUNT = 3

CONFIG_DIR = Path.home() / ".config" / "universal-file-converter"
CONFIG_FILE = CONFIG_DIR / "config.json"

DEFAULT_ENCODING = "utf-8"
CSV_SNIFF_SAMPLE = 8192
LIBREOFFICE_TIMEOUT = 120

FORMAT_LABELS = {
    "csv": "CSV",
    "json": "JSON",
    "txt": "TXT",
    "docx": "DOCX",
    "odt": "ODT",
    "pdf": "PDF",
}

SOURCE_FORMATS = ("csv", "json", "txt", "docx", "odt")
TARGET_FORMATS = ("csv", "json", "txt", "docx", "odt", "pdf")

SUPPORTED_FILETYPES = [
    ("All supported files", "*.csv *.json *.txt *.docx *.odt"),
    ("CSV", "*.csv"),
    ("JSON", "*.json"),
    ("Text", "*.txt"),
    ("Word documents", "*.docx"),
    ("OpenDocument text", "*.odt"),
    ("All files", "*.*"),
]


def _read_config() -> dict:
    try:
        with CONFIG_FILE.open(encoding=DEFAULT_ENCODING) as handle:
            data = json.load(handle)
        return data if isinstance(data, dict) else {}
    except (OSError, json.JSONDecodeError):
        return {}


def get_soffice_override() -> str | None:
    for variable in ("UFC_SOFFICE", "LIBREOFFICE_PATH"):
        value = os.environ.get(variable)
        if value:
            return value
    value = _read_config().get("soffice_path")
    return str(value) if value else None


def set_soffice_override(path: str | None) -> None:
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    data = _read_config()
    if path:
        data["soffice_path"] = str(path)
    else:
        data.pop("soffice_path", None)
    with CONFIG_FILE.open("w", encoding=DEFAULT_ENCODING) as handle:
        json.dump(data, handle, ensure_ascii=False, indent=2)


def get_language() -> str:
    value = _read_config().get("language")
    return value if value in {"en", "pl"} else "en"


def set_language(language: str) -> None:
    if language not in {"en", "pl"}:
        return
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    data = _read_config()
    data["language"] = language
    with CONFIG_FILE.open("w", encoding=DEFAULT_ENCODING) as handle:
        json.dump(data, handle, ensure_ascii=False, indent=2)
