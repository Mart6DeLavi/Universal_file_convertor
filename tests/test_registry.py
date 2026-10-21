from __future__ import annotations

import pytest

from file_converter import registry
from file_converter.registry import (
    REGISTRY,
    available_targets,
    get_spec,
    is_supported,
    register_converter,
)


def test_available_targets_for_native_formats(monkeypatch):
    monkeypatch.setattr(registry, "is_libreoffice_available", lambda: False)
    assert available_targets("csv") == ["json"]
    assert available_targets("json") == ["csv"]
    assert available_targets("txt") == ["docx", "pdf"]
    assert available_targets("docx") == ["txt"]
    assert available_targets("odt") == ["txt"]


def test_available_targets_include_office_when_libreoffice_present(monkeypatch):
    monkeypatch.setattr(registry, "is_libreoffice_available", lambda: True)
    assert available_targets("docx") == ["txt", "odt", "pdf"]
    assert available_targets("odt") == ["txt", "docx", "pdf"]


def test_is_supported_and_get_spec():
    assert is_supported("csv", "json")
    assert is_supported(".CSV", ".JSON")
    assert not is_supported("csv", "pdf")
    assert get_spec("txt", "pdf") is not None


def test_all_required_conversions_are_registered():
    expected = {
        ("csv", "json"),
        ("json", "csv"),
        ("txt", "docx"),
        ("docx", "txt"),
        ("txt", "pdf"),
        ("docx", "pdf"),
        ("odt", "pdf"),
        ("docx", "odt"),
        ("odt", "docx"),
        ("odt", "txt"),
    }
    assert expected.issubset(set(REGISTRY))


def test_duplicate_registration_rejected():
    with pytest.raises(RuntimeError):
        register_converter("csv", "json", "duplicate")(lambda source, target: target)


def test_registry_execute_delegates_to_service(monkeypatch):
    from file_converter import service

    sentinel = object()
    monkeypatch.setattr(service, "execute", lambda request: sentinel)
    assert registry.execute(object()) is sentinel
