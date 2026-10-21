from __future__ import annotations

import json

import pytest

from file_converter.exceptions import ConversionError, DependencyMissingError, OutputConflictError
from file_converter.models import ConversionRequest
from file_converter.service import ConversionService, execute


def make_csv(tmp_path):
    source = tmp_path / "sample.csv"
    source.write_text("miasto,uwagi\nŁódź,Zażółć gęślą jaźń\n", encoding="utf-8")
    return source


def test_service_executes_conversion_and_returns_result(tmp_path):
    source = make_csv(tmp_path)
    result = execute(ConversionRequest(source, "json", tmp_path))

    assert result.output_path == tmp_path / "sample.json"
    assert result.output_path.exists()
    assert result.duration_seconds >= 0
    data = json.loads(result.output_path.read_text(encoding="utf-8"))
    assert data == [{"miasto": "Łódź", "uwagi": "Zażółć gęślą jaźń"}]


def test_service_rejects_existing_output_without_overwrite(tmp_path):
    source = make_csv(tmp_path)
    target = tmp_path / "sample.json"
    target.write_text("old", encoding="utf-8")

    with pytest.raises(OutputConflictError):
        ConversionService().execute(ConversionRequest(source, "json", tmp_path))
    assert target.read_text(encoding="utf-8") == "old"


def test_service_overwrites_when_requested(tmp_path):
    source = make_csv(tmp_path)
    target = tmp_path / "sample.json"
    target.write_text("old", encoding="utf-8")

    execute(ConversionRequest(source, "json", tmp_path, overwrite=True))

    assert json.loads(target.read_text(encoding="utf-8"))[0]["miasto"] == "Łódź"


def test_service_uses_custom_unique_name(tmp_path):
    source = make_csv(tmp_path)
    first = execute(ConversionRequest(source, "json", tmp_path))
    second = execute(ConversionRequest(source, "json", tmp_path, output_name="sample (1).json"))

    assert first.output_path != second.output_path
    assert second.output_name == "sample (1).json"


def test_service_leaves_no_temporary_directories(tmp_path):
    source = make_csv(tmp_path)
    execute(ConversionRequest(source, "json", tmp_path))
    leftovers = [p.name for p in tmp_path.iterdir() if p.name.startswith(".ufc-")]
    assert leftovers == []


def test_service_allows_empty_json_array_to_csv(tmp_path):
    source = tmp_path / "empty.json"
    source.write_text("[]", encoding="utf-8")
    result = execute(ConversionRequest(source, "csv", tmp_path))
    assert result.output_path.exists()
    assert result.output_path.stat().st_size == 0


def test_service_failure_keeps_source_untouched(tmp_path):
    source = tmp_path / "broken.docx"
    payload = b"broken-docx-content"
    source.write_bytes(payload)

    with pytest.raises(ConversionError):
        execute(ConversionRequest(source, "txt", tmp_path))

    assert source.read_bytes() == payload
    assert not (tmp_path / "broken.txt").exists()
    assert [p for p in tmp_path.iterdir() if p.name.startswith(".ufc-")] == []


def test_service_reports_missing_libreoffice(tmp_path, monkeypatch):
    from file_converter import registry
    from docx import Document

    monkeypatch.setattr(registry, "is_libreoffice_available", lambda: False)
    source = tmp_path / "input.docx"
    Document().save(str(source))

    with pytest.raises(DependencyMissingError):
        execute(ConversionRequest(source, "pdf", tmp_path))
