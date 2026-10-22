from __future__ import annotations

from file_converter.gui.i18n import DEFAULT_LANGUAGE, _STRINGS, has_translation, translate


def test_catalogs_have_the_same_keys():
    english = set(_STRINGS["en"])
    polish = set(_STRINGS["pl"])
    assert english == polish


def test_translate_uses_requested_language():
    assert translate("en", "source.convert") == "Convert"
    assert translate("pl", "source.convert") == "Konwertuj"
    assert translate("pl", "status.done", duration=1.25, name="plik.pdf") == (
        "Gotowe w 1.2 s · plik.pdf"
    )


def test_translate_falls_back_to_english():
    assert translate("de", "source.convert") == translate(DEFAULT_LANGUAGE, "source.convert")


def test_has_translation_distinguishes_missing_keys():
    assert has_translation("pl", "source.convert")
    assert not has_translation("pl", "missing.key")
