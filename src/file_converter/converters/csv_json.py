from __future__ import annotations

import csv
import io
import json
import os
from pathlib import Path

from ..config import CSV_SNIFF_SAMPLE, DEFAULT_ENCODING
from ..exceptions import ConversionError

_DELIMITERS = ",;\t|"


def _configured_delimiter() -> str | None:
    value = os.environ.get("UFC_CSV_DELIMITER")
    if not value:
        return None
    value = value.replace("\\t", "\t")
    if len(value) != 1:
        raise ConversionError(
            "Invalid CSV delimiter in UFC_CSV_DELIMITER.",
            "Specify one character, for example ; or a comma.",
        )
    return value


def _read_text(source: Path) -> str:
    try:
        return source.read_text(encoding="utf-8-sig")
    except UnicodeDecodeError as exc:
        raise ConversionError(
            "The CSV file is not valid UTF-8.",
            "Save the file as UTF-8 and try again.",
        ) from exc
    except OSError as exc:
        raise ConversionError(f"Could not read the CSV file: {source}", str(exc)) from exc


def _detect_dialect(text: str, delimiter: str | None) -> csv.Dialect:
    if delimiter:
        class Configured(csv.excel):
            pass

        Configured.delimiter = delimiter
        return Configured

    sample = text[:CSV_SNIFF_SAMPLE]
    try:
        return csv.Sniffer().sniff(sample, delimiters=_DELIMITERS)
    except csv.Error:
        return csv.excel


def _validate_headers(headers: list[str]) -> None:
    seen: dict[str, int] = {}
    for index, header in enumerate(headers, start=1):
        if header.strip() == "":
            raise ConversionError(
                f"Empty header in column {index}.",
                "Every CSV column must have a non-empty name.",
            )
        if header in seen:
            raise ConversionError(
                f"Duplicate CSV header: {header!r}.",
                "Make column names unique; otherwise the conversion is ambiguous.",
            )
        seen[header] = index


def read_csv_records(
    source: Path, delimiter: str | None = None
) -> tuple[list[str], list[dict[str, str]]]:
    source = Path(source)
    text = _read_text(source)
    if not text.strip():
        raise ConversionError(
            "The CSV file is empty.",
            "The file must contain a header row and at least one data row.",
        )

    dialect = _detect_dialect(text, delimiter or _configured_delimiter())
    try:
        rows = list(csv.reader(io.StringIO(text, newline=""), dialect))
    except csv.Error as exc:
        raise ConversionError(
            f"Could not parse the CSV file: {exc}",
            "Check the quotes and row structure.",
        ) from exc

    rows = [row for row in rows if row]
    if not rows:
        raise ConversionError("The CSV file contains no data.")

    headers = rows[0]
    _validate_headers(headers)

    records: list[dict[str, str]] = []
    for number, row in enumerate(rows[1:], start=2):
        if len(row) != len(headers):
            raise ConversionError(
                f"Row {number} has {len(row)} fields, but there are {len(headers)} headers.",
                "Adjust the CSV so every row has the same number of fields.",
            )
        records.append(dict(zip(headers, row)))
    return headers, records


def csv_to_json(source: Path, target: Path, delimiter: str | None = None) -> Path:
    _, records = read_csv_records(source, delimiter)
    target = Path(target)
    try:
        with target.open("w", encoding=DEFAULT_ENCODING, newline="\n") as handle:
            json.dump(records, handle, ensure_ascii=False, indent=2)
            handle.write("\n")
    except OSError as exc:
        raise ConversionError(f"Could not write the JSON file: {target}", str(exc)) from exc
    return target


def _cell_value(value) -> str:
    if value is None:
        return ""
    if isinstance(value, str):
        return value
    if isinstance(value, bool):
        return "true" if value else "false"
    if isinstance(value, (dict, list)):
        return json.dumps(value, ensure_ascii=False, separators=(",", ":"))
    return str(value)


def json_to_csv(source: Path, target: Path) -> Path:
    source = Path(source)
    try:
        raw = source.read_text(encoding="utf-8-sig")
    except UnicodeDecodeError as exc:
        raise ConversionError(
            "The JSON file is not valid UTF-8.",
            "Save the file as UTF-8.",
        ) from exc
    except OSError as exc:
        raise ConversionError(f"Could not read the JSON file: {source}", str(exc)) from exc

    try:
        data = json.loads(raw)
    except json.JSONDecodeError as exc:
        raise ConversionError(
            f"Invalid JSON: {exc.msg} (line {exc.lineno}, column {exc.colno}).",
            "Fix the JSON syntax and try again.",
        ) from exc

    if not isinstance(data, list):
        raise ConversionError(
            "A JSON array is expected at the top level.",
            "The supported structure is [ {...}, {...} ].",
        )

    headers: list[str] = []
    for index, item in enumerate(data, start=1):
        if not isinstance(item, dict):
            raise ConversionError(
                f"Array element #{index} is not a JSON object.",
                "Each element must be an object such as {...}.",
            )
        for key in item:
            if key not in headers:
                headers.append(key)

    target = Path(target)
    try:
        with target.open("w", encoding=DEFAULT_ENCODING, newline="") as handle:
            if not headers:
                return target
            writer = csv.DictWriter(handle, fieldnames=headers, extrasaction="ignore")
            writer.writeheader()
            for item in data:
                row = {key: _cell_value(item.get(key)) for key in headers}
                writer.writerow(row)
    except OSError as exc:
        raise ConversionError(f"Could not write the CSV file: {target}", str(exc)) from exc
    return target
