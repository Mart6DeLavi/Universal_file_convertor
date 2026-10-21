from __future__ import annotations

import csv
import json

import pytest

from file_converter.converters.csv_json import csv_to_json, json_to_csv
from file_converter.exceptions import ConversionError


def test_csv_to_json_preserves_headers_order_unicode_and_empty(tmp_path):
    source = tmp_path / "input.csv"
    source.write_text(
        "imię,nazwisko,miasto,uwagi\n"
        'Jan,Kowalski,Łódź,"Zażółć gęślą jaźń"\n'
        "Anna,Nowak,Kraków,\n",
        encoding="utf-8-sig",
    )
    target = tmp_path / "output.json"

    csv_to_json(source, target)
    data = json.loads(target.read_text(encoding="utf-8"))

    assert isinstance(data, list)
    assert len(data) == 2
    assert list(data[0].keys()) == ["imię", "nazwisko", "miasto", "uwagi"]
    assert data[0]["miasto"] == "Łódź"
    assert data[0]["uwagi"] == "Zażółć gęślą jaźń"
    assert data[1]["uwagi"] == ""


def test_csv_to_json_handles_commas_quotes_and_multiline(tmp_path):
    source = tmp_path / "complex.csv"
    with source.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.writer(handle)
        writer.writerow(["name", "note"])
        writer.writerow(["Jan", "Wartość, z przecinkiem"])
        writer.writerow(["Anna", 'Cytat: "Żółw"'])
        writer.writerow(["Piotr", "linia 1\nlinia 2"])
    target = tmp_path / "complex.json"

    csv_to_json(source, target)
    data = json.loads(target.read_text(encoding="utf-8"))

    assert data[0]["note"] == "Wartość, z przecinkiem"
    assert data[1]["note"] == 'Cytat: "Żółw"'
    assert data[2]["note"] == "linia 1\nlinia 2"


def test_csv_to_json_semicolon_delimiter_detected(tmp_path):
    source = tmp_path / "semicolon.csv"
    source.write_text("a;b\n1;2\n", encoding="utf-8")
    target = tmp_path / "semicolon.json"

    csv_to_json(source, target)

    assert json.loads(target.read_text(encoding="utf-8")) == [{"a": "1", "b": "2"}]


def test_csv_to_json_custom_delimiter(tmp_path):
    source = tmp_path / "pipe.csv"
    source.write_text("a|b\n1|2\n", encoding="utf-8")
    target = tmp_path / "pipe.json"

    csv_to_json(source, target, delimiter="|")

    assert json.loads(target.read_text(encoding="utf-8")) == [{"a": "1", "b": "2"}]


@pytest.mark.parametrize(
    "content",
    [
        "a,a\n1,2\n",
        ",b\n1,2\n",
    ],
)
def test_csv_invalid_headers_raise(tmp_path, content):
    source = tmp_path / "bad.csv"
    source.write_text(content, encoding="utf-8")
    with pytest.raises(ConversionError):
        csv_to_json(source, tmp_path / "bad.json")


def test_csv_inconsistent_field_count_raises(tmp_path):
    source = tmp_path / "bad.csv"
    source.write_text("a,b\n1\n", encoding="utf-8")
    with pytest.raises(ConversionError, match="Row 2"):
        csv_to_json(source, tmp_path / "bad.json")


def test_csv_empty_file_raises(tmp_path):
    source = tmp_path / "empty.csv"
    source.write_text("", encoding="utf-8")
    with pytest.raises(ConversionError, match="empty"):
        csv_to_json(source, tmp_path / "empty.json")


def test_json_to_csv_headers_order_missing_nested_and_unicode(tmp_path):
    source = tmp_path / "input.json"
    source.write_text(
        json.dumps(
            [
                {"b": 1, "a": "Żółw", "nested": {"x": 1}},
                {"a": "Zażółć gęślą jaźń", "c": True},
            ],
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )
    target = tmp_path / "output.csv"

    json_to_csv(source, target)

    with target.open(encoding="utf-8", newline="") as handle:
        rows = list(csv.reader(handle))
    assert rows[0] == ["b", "a", "nested", "c"]
    assert rows[1] == ["1", "Żółw", '{"x":1}', ""]
    assert rows[2] == ["", "Zażółć gęślą jaźń", "", "true"]


def test_json_to_csv_empty_array_creates_empty_file(tmp_path):
    source = tmp_path / "empty.json"
    source.write_text("[]", encoding="utf-8")
    target = tmp_path / "empty.csv"

    json_to_csv(source, target)

    assert target.exists()
    assert target.read_text(encoding="utf-8") == ""


def test_json_invalid_raises(tmp_path):
    source = tmp_path / "bad.json"
    source.write_text('{"a": ', encoding="utf-8")
    with pytest.raises(ConversionError, match="Invalid JSON"):
        json_to_csv(source, tmp_path / "out.csv")


def test_json_top_level_must_be_array(tmp_path):
    source = tmp_path / "object.json"
    source.write_text('{"a": 1}', encoding="utf-8")
    with pytest.raises(ConversionError, match="JSON array"):
        json_to_csv(source, tmp_path / "out.csv")


def test_json_non_object_element_raises(tmp_path):
    source = tmp_path / "list.json"
    source.write_text("[1, 2]", encoding="utf-8")
    with pytest.raises(ConversionError, match="not a JSON object"):
        json_to_csv(source, tmp_path / "out.csv")


def test_unicode_roundtrip(tmp_path):
    original = tmp_path / "original.csv"
    original.write_text("miasto,uwagi\nŁódź,Zażółć gęślą jaźń\n", encoding="utf-8")
    as_json = tmp_path / "step.json"
    restored = tmp_path / "restored.csv"

    csv_to_json(original, as_json)
    json_to_csv(as_json, restored)

    with restored.open(encoding="utf-8", newline="") as handle:
        rows = list(csv.reader(handle))
    assert rows == [["miasto", "uwagi"], ["Łódź", "Zażółć gęślą jaźń"]]
