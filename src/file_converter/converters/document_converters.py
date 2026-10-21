from __future__ import annotations

from pathlib import Path

from .libreoffice import convert_with_libreoffice


def docx_to_pdf(source: Path, target: Path) -> Path:
    return convert_with_libreoffice(source, Path(target).with_suffix(".pdf"))


def odt_to_pdf(source: Path, target: Path) -> Path:
    return convert_with_libreoffice(source, Path(target).with_suffix(".pdf"))


def docx_to_odt(source: Path, target: Path) -> Path:
    return convert_with_libreoffice(source, Path(target).with_suffix(".odt"))


def odt_to_docx(source: Path, target: Path) -> Path:
    return convert_with_libreoffice(source, Path(target).with_suffix(".docx"))
