from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Callable

from .config import TARGET_FORMATS
from .converters import (
    csv_to_json,
    docx_to_odt,
    docx_to_pdf,
    docx_to_txt,
    is_libreoffice_available,
    json_to_csv,
    odt_to_docx,
    odt_to_pdf,
    odt_to_txt,
    txt_to_docx,
    txt_to_pdf,
)

Converter = Callable[[Path, Path], Path]


@dataclass(frozen=True)
class ConverterSpec:
    source_format: str
    target_format: str
    converter: Converter
    description: str
    requires_libreoffice: bool = False
    allow_empty: bool = False

    def is_available(self) -> bool:
        if self.requires_libreoffice and not is_libreoffice_available():
            return False
        return True


REGISTRY: dict[tuple[str, str], ConverterSpec] = {}


def register_converter(
    source_format: str,
    target_format: str,
    description: str,
    *,
    requires_libreoffice: bool = False,
    allow_empty: bool = False,
):
    key = (source_format.lower().lstrip("."), target_format.lower().lstrip("."))

    def decorator(func: Converter) -> Converter:
        if key in REGISTRY:
            raise RuntimeError(f"Конвертер {key[0]} → {key[1]} уже зарегистрирован.")
        REGISTRY[key] = ConverterSpec(
            source_format=key[0],
            target_format=key[1],
            converter=func,
            description=description,
            requires_libreoffice=requires_libreoffice,
            allow_empty=allow_empty,
        )
        return func

    return decorator


def _register_builtin() -> None:
    register_converter("csv", "json", "Таблица CSV → массив JSON-объектов")(csv_to_json)
    register_converter(
        "json", "csv", "Массив JSON-объектов → таблица CSV", allow_empty=True
    )(json_to_csv)
    register_converter("txt", "docx", "Текст → документ Word (абзацы по строкам)")(txt_to_docx)
    register_converter("docx", "txt", "Документ Word → обычный текст")(docx_to_txt)
    register_converter("txt", "pdf", "Текст → PDF с Unicode-шрифтом")(txt_to_pdf)
    register_converter(
        "docx", "pdf", "Word → PDF через LibreOffice", requires_libreoffice=True
    )(docx_to_pdf)
    register_converter(
        "odt", "pdf", "OpenDocument → PDF через LibreOffice", requires_libreoffice=True
    )(odt_to_pdf)
    register_converter(
        "docx", "odt", "Word → OpenDocument через LibreOffice", requires_libreoffice=True
    )(docx_to_odt)
    register_converter(
        "odt", "docx", "OpenDocument → Word через LibreOffice", requires_libreoffice=True
    )(odt_to_docx)
    register_converter("odt", "txt", "OpenDocument → обычный текст через odfpy")(odt_to_txt)


_register_builtin()


def normalize_format(value: str | None) -> str:
    return (value or "").strip().lower().lstrip(".")


def get_spec(source_format: str, target_format: str) -> ConverterSpec | None:
    return REGISTRY.get((normalize_format(source_format), normalize_format(target_format)))


def is_supported(source_format: str, target_format: str) -> bool:
    return get_spec(source_format, target_format) is not None


def supported_sources() -> list[str]:
    return sorted({source for source, _ in REGISTRY})


def available_targets(source: str | Path) -> list[str]:
    if isinstance(source, Path):
        source_format = source.suffix
    else:
        source_format = str(source)
    source_format = normalize_format(source_format)
    targets = {
        target
        for (registered_source, target), spec in REGISTRY.items()
        if registered_source == source_format and spec.is_available()
    }
    return [target for target in TARGET_FORMATS if target in targets]


def all_registered_targets(source: str | Path) -> list[str]:
    source_format = source.suffix if isinstance(source, Path) else str(source)
    source_format = normalize_format(source_format)
    targets = {target for (registered_source, target) in REGISTRY if registered_source == source_format}
    return [target for target in TARGET_FORMATS if target in targets]


def execute(request):
    from .service import execute as _execute

    return _execute(request)
