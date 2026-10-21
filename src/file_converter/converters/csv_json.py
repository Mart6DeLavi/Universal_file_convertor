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
            "Некорректный разделитель CSV в UFC_CSV_DELIMITER.",
            "Укажите один символ, например ; или запятую.",
        )
    return value


def _read_text(source: Path) -> str:
    try:
        return source.read_text(encoding="utf-8-sig")
    except UnicodeDecodeError as exc:
        raise ConversionError(
            "CSV-файл не является корректным UTF-8.",
            "Сохраните файл в кодировке UTF-8 и повторите попытку.",
        ) from exc
    except OSError as exc:
        raise ConversionError(f"Не удалось прочитать CSV: {source}", str(exc)) from exc


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
                f"Пустой заголовок в колонке {index}.",
                "Каждая колонка CSV должна иметь непустое имя.",
            )
        if header in seen:
            raise ConversionError(
                f"Дублирующийся заголовок CSV: {header!r}.",
                "Сделайте имена колонок уникальными, иначе преобразование неоднозначно.",
            )
        seen[header] = index


def read_csv_records(
    source: Path, delimiter: str | None = None
) -> tuple[list[str], list[dict[str, str]]]:
    source = Path(source)
    text = _read_text(source)
    if not text.strip():
        raise ConversionError(
            "CSV-файл пуст.",
            "Файл должен содержать строку заголовков и хотя бы одну строку данных.",
        )

    dialect = _detect_dialect(text, delimiter or _configured_delimiter())
    try:
        rows = list(csv.reader(io.StringIO(text, newline=""), dialect))
    except csv.Error as exc:
        raise ConversionError(
            f"Не удалось разобрать CSV: {exc}",
            "Проверьте кавычки и структуру строк.",
        ) from exc

    rows = [row for row in rows if row]
    if not rows:
        raise ConversionError("CSV не содержит данных.")

    headers = rows[0]
    _validate_headers(headers)

    records: list[dict[str, str]] = []
    for number, row in enumerate(rows[1:], start=2):
        if len(row) != len(headers):
            raise ConversionError(
                f"Строка {number} содержит {len(row)} полей, а заголовков — {len(headers)}.",
                "Исправьте CSV так, чтобы число полей в каждой строке совпадало.",
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
        raise ConversionError(f"Не удалось записать JSON: {target}", str(exc)) from exc
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
            "JSON-файл не является корректным UTF-8.",
            "Сохраните файл в кодировке UTF-8.",
        ) from exc
    except OSError as exc:
        raise ConversionError(f"Не удалось прочитать JSON: {source}", str(exc)) from exc

    try:
        data = json.loads(raw)
    except json.JSONDecodeError as exc:
        raise ConversionError(
            f"Невалидный JSON: {exc.msg} (строка {exc.lineno}, колонка {exc.colno}).",
            "Исправьте синтаксис JSON и повторите попытку.",
        ) from exc

    if not isinstance(data, list):
        raise ConversionError(
            "Ожидается массив JSON на верхнем уровне.",
            "Поддерживается структура [ {...}, {...} ].",
        )

    headers: list[str] = []
    for index, item in enumerate(data, start=1):
        if not isinstance(item, dict):
            raise ConversionError(
                f"Элемент массива №{index} не является JSON-объектом.",
                "Каждый элемент должен быть объектом вида {...}.",
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
        raise ConversionError(f"Не удалось записать CSV: {target}", str(exc)) from exc
    return target
