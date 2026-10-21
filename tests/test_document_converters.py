from __future__ import annotations

import subprocess
from pathlib import Path

import pytest
from docx import Document

from file_converter.converters import libreoffice
from file_converter.converters.document_converters import docx_to_odt, docx_to_pdf
from file_converter.converters.text_converters import odt_to_txt
from file_converter.exceptions import ConversionError, DependencyMissingError, ExternalProcessError


@pytest.fixture
def docx_source(tmp_path):
    source = tmp_path / "document.docx"
    document = Document()
    document.add_paragraph("Zażółć gęślą jaźń")
    document.save(str(source))
    return source


def test_missing_libreoffice_raises(docx_source, tmp_path, monkeypatch):
    monkeypatch.setattr(libreoffice, "find_libreoffice", lambda: None)
    with pytest.raises(DependencyMissingError, match="LibreOffice"):
        docx_to_pdf(docx_source, tmp_path / "out.pdf")


def test_libreoffice_timeout(docx_source, tmp_path, monkeypatch):
    monkeypatch.setattr(libreoffice, "find_libreoffice", lambda: Path("/bin/echo"))

    def raise_timeout(*args, **kwargs):
        raise subprocess.TimeoutExpired(cmd=args[0], timeout=120)

    monkeypatch.setattr(libreoffice.subprocess, "run", raise_timeout)
    with pytest.raises(ExternalProcessError, match="не завершил работу"):
        docx_to_pdf(docx_source, tmp_path / "out.pdf")


def test_libreoffice_nonzero_exit(docx_source, tmp_path, monkeypatch):
    monkeypatch.setattr(libreoffice, "find_libreoffice", lambda: Path("/bin/echo"))
    completed = subprocess.CompletedProcess(["soffice"], 3, "", "conversion failed")
    monkeypatch.setattr(libreoffice.subprocess, "run", lambda *a, **k: completed)
    with pytest.raises(ExternalProcessError, match="кодом 3") as error:
        docx_to_pdf(docx_source, tmp_path / "out.pdf")
    assert "conversion failed" in error.value.stderr


def test_libreoffice_success_without_output_is_error(docx_source, tmp_path, monkeypatch):
    monkeypatch.setattr(libreoffice, "find_libreoffice", lambda: Path("/bin/echo"))
    completed = subprocess.CompletedProcess(["soffice"], 0, "ok", "")
    monkeypatch.setattr(libreoffice.subprocess, "run", lambda *a, **k: completed)
    with pytest.raises(ExternalProcessError, match="не создал"):
        docx_to_pdf(docx_source, tmp_path / "out.pdf")


@pytest.mark.skipif(
    not libreoffice.is_libreoffice_available(),
    reason="LibreOffice не установлен в этой среде",
)
def test_real_docx_to_pdf_and_odt(docx_source, tmp_path):
    pdf_target = tmp_path / "document.pdf"
    docx_to_pdf(docx_source, pdf_target)
    assert pdf_target.exists()
    assert pdf_target.stat().st_size > 0
    assert pdf_target.read_bytes().startswith(b"%PDF")

    odt_target = tmp_path / "document.odt"
    docx_to_odt(docx_source, odt_target)
    assert odt_target.exists()
    assert odt_target.stat().st_size > 0

    txt_target = tmp_path / "document.txt"
    odt_to_txt(odt_target, txt_target)
    assert "Zażółć" in txt_target.read_text(encoding="utf-8")
