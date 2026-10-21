from __future__ import annotations

import pytest
from docx import Document

from file_converter import registry
from file_converter.exceptions import (
    DependencyMissingError,
    OutputConflictError,
    UnsupportedConversionError,
    ValidationError,
)
from file_converter.models import ConversionRequest
from file_converter.validators import (
    build_output_path,
    validate_request,
    validate_source,
    validate_target_format,
)


def make_source(tmp_path, name="input.csv", content="a,b\n1,2\n"):
    source = tmp_path / name
    source.write_text(content, encoding="utf-8")
    return source


def test_validate_missing_source(tmp_path):
    with pytest.raises(ValidationError, match="not found"):
        validate_source(tmp_path / "missing.csv")


def test_validate_source_is_directory(tmp_path):
    directory = tmp_path / "folder.csv"
    directory.mkdir()
    with pytest.raises(ValidationError, match="regular file"):
        validate_source(directory)


def test_validate_unsupported_extension(tmp_path):
    source = make_source(tmp_path, "input.exe", "data")
    with pytest.raises(UnsupportedConversionError):
        validate_source(source)


def test_validate_target_unknown_and_unregistered(tmp_path):
    with pytest.raises(ValidationError, match="No target format"):
        validate_target_format("csv", "")
    with pytest.raises(UnsupportedConversionError, match="is unknown"):
        validate_target_format("csv", "exe")
    with pytest.raises(UnsupportedConversionError, match="is not supported"):
        validate_target_format("csv", "pdf")


def test_validate_request_success(tmp_path):
    source = make_source(tmp_path)
    request = ConversionRequest(source, "json", tmp_path)
    validated = validate_request(request)
    assert validated.output_name == "input.json"
    assert validated.output_path == tmp_path / "input.json"
    assert not validated.conflict


def test_validate_missing_output_directory(tmp_path):
    source = make_source(tmp_path)
    request = ConversionRequest(source, "json", tmp_path / "missing")
    with pytest.raises(ValidationError, match="does not exist"):
        validate_request(request)


def test_validate_output_path_is_not_directory(tmp_path):
    source = make_source(tmp_path)
    output_file = make_source(tmp_path, "not_a_dir", "x")
    request = ConversionRequest(source, "json", output_file)
    with pytest.raises(ValidationError, match="not a directory"):
        validate_request(request)


def test_output_name_extension_mismatch(tmp_path):
    source = make_source(tmp_path)
    request = ConversionRequest(source, "json", tmp_path, output_name="result.txt")
    with pytest.raises(ValidationError, match="does not match"):
        validate_request(request)


def test_output_name_without_extension_gets_target(tmp_path):
    source = make_source(tmp_path)
    name, path = build_output_path(source, "json", tmp_path, "result")
    assert name == "result.json"
    assert path == tmp_path / "result.json"


def test_empty_output_name_rejected(tmp_path):
    source = make_source(tmp_path)
    request = ConversionRequest(source, "json", tmp_path, output_name="   ")
    with pytest.raises(ValidationError, match="cannot be empty"):
        validate_request(request)


def test_existing_target_requires_confirmation(tmp_path):
    source = make_source(tmp_path)
    (tmp_path / "input.json").write_text("old", encoding="utf-8")
    request = ConversionRequest(source, "json", tmp_path)
    with pytest.raises(OutputConflictError):
        validate_request(request)

    overwrite = ConversionRequest(source, "json", tmp_path, overwrite=True)
    assert validate_request(overwrite).output_path.exists()


def test_libreoffice_dependency_detected(tmp_path, monkeypatch):
    monkeypatch.setattr(registry, "is_libreoffice_available", lambda: False)
    source = tmp_path / "input.docx"
    Document().save(str(source))
    with pytest.raises(DependencyMissingError, match="LibreOffice"):
        validate_target_format("docx", "pdf")
