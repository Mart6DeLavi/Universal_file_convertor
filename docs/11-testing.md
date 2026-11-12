# 11 — Testing

The project uses `pytest`. Tests cover converters, the service, validators, the registry, localization, and real LibreOffice conversions when available.

## Running the suite

```bash
.venv/bin/python -m pytest -v
```

or, with the environment activated:

```bash
python -m pytest -v
```

Useful variants:

```bash
python -m pytest -q                          # compact output
python -m pytest tests/test_service.py -v    # one module
python -m pytest -k "csv and unicode" -v     # by keyword
python -m pytest --collect-only -q           # list tests without running
```

Current result in this environment:

```text
60 passed in 59.47s
```

The historical report [`reports/test_report.md`](../reports/test_report.md) records 60 passed in 5.62 s on 21 October 2026. Timing varies with LibreOffice warm-up and disk speed; the count and outcomes are what matter.

## Test files

| File | Tests | Scope |
|---|---:|---|
| `tests/test_csv_json.py` | 14 | CSV ↔ JSON, BOM, Unicode, quotes, commas, multiline fields, delimiters, header/row errors, empty array, roundtrip |
| `tests/test_document_converters.py` | 8 | Missing LibreOffice, timeout, non-zero exit, missing output, four real office conversions with content checks |
| `tests/test_i18n.py` | 4 | Catalog parity, requested language, English fallback, missing keys |
| `tests/test_registry.py` | 6 | Registered directions, availability filtering, lookup, duplicates, delegation to the service |
| `tests/test_service.py` | 10 | End-to-end conversion, conflicts, overwrite, unique names, temp cleanup, empty CSV, failure safety, missing dependency, progress behavior |
| `tests/test_text_converters.py` | 6 | TXT ↔ DOCX, TXT → PDF, ODT → TXT, tables, malformed documents |
| `tests/test_validators.py` | 12 | Source, extension, target, directory, name, extension mismatch, conflict, dependency detection |

Total: **60 tests**.

## Test environment

`tests/conftest.py`:

- resolves the repository root and inserts `src/` into `sys.path`, so `import file_converter` works without installation;
- provides a `sample_dir` fixture pointing at `test_data/`.

No `pytest.ini` or `pyproject.toml` is needed. Tests that require LibreOffice are decorated with:

```python
REQUIRES_LIBREOFFICE = pytest.mark.skipif(
    not libreoffice.is_libreoffice_available(),
    reason="LibreOffice is not installed",
)
```

Without LibreOffice, the four real conversion tests are skipped, while the mocked error tests and everything else still run. The report states "no skipped tests" for the reference machine, where LibreOffice was installed.

## What the tests assert

### CSV / JSON

- header order and key order are preserved;
- Unicode survives both directions;
- BOM is accepted;
- empty fields stay empty strings;
- quoted commas and embedded newlines are parsed correctly;
- `;` is auto-detected, and `UFC_CSV_DELIMITER` overrides detection;
- empty and duplicate headers fail;
- inconsistent field counts fail and name the row;
- empty files fail;
- JSON must be an array of objects;
- a nested object is serialized into a cell;
- `null` becomes an empty cell;
- an empty array produces an empty CSV and is allowed by the service;
- invalid JSON reports position;
- a full CSV → JSON → CSV roundtrip preserves values.

### Text and office conversions

- TXT → DOCX keeps one paragraph per line and Unicode;
- DOCX → TXT extracts paragraphs and table cells in order;
- TXT → PDF produces a document whose extracted text contains the Unicode input (read with `pypdf`);
- ODT → TXT extracts paragraphs;
- malformed DOCX/ODT raise `ConversionError`;
- real DOCX/ODT → PDF/ODT/DOCX conversions are checked by reopening the result (`pypdf`, `odfpy`, `python-docx`) and looking for `Zażółć` / `Łódź`;
- the source bytes are compared before and after each office conversion.

### Service and safety

- a successful conversion returns a `ConversionResult` with the expected path;
- an existing target without `overwrite` raises `OutputConflictError`;
- `overwrite=True` replaces the file;
- a custom unique name is honored;
- no `.ufc-*` temporary directories remain;
- an empty JSON array → CSV is accepted;
- a failing converter leaves the source untouched and no destination file behind;
- a missing LibreOffice raises before conversion;
- progress values are monotonic and bounded;
- a progress callback that raises does not break the conversion.

### Validators and registry

- missing source, directory as source, unknown extension;
- unknown target and unregistered direction;
- missing/non-directory output folder;
- extension mismatch and extension auto-append;
- empty output name;
- existing target requires confirmation;
- LibreOffice-dependent direction is reported missing when `find_libreoffice` is patched to `None`;
- all ten directions are registered;
- duplicate registration raises `RuntimeError`;
- `registry.execute` delegates to `service.execute`.

### i18n

- `en` and `pl` catalogs have exactly the same keys;
- `translate` uses the requested language;
- unknown language falls back to English;
- `has_translation` distinguishes missing keys.

## Writing new tests

Conventions used in the suite:

- Put files under `tmp_path`; never write into the repository.
- Use `monkeypatch` for external dependencies, e.g. `monkeypatch.setattr(libreoffice, "find_libreoffice", lambda: None)`.
- Use real Unicode text and sometimes spaces in file names to catch encoding/path regressions.
- Assert both the artifact (exists, non-empty, signature) and its content (reopen it and inspect text).
- For the service, assert cleanup (no leftover `.ufc-*`) and source integrity.
- Keep the test independent of the developer's config: prefer explicit arguments over `config.json`.

Example skeleton:

```python
from pathlib import Path

from file_converter.models import ConversionRequest
from file_converter.service import execute


def test_txt_to_docx_keeps_unicode(tmp_path):
    source = tmp_path / "zażółć.txt"
    source.write_text("Zażółć gęślą jaźń\nŁódź", encoding="utf-8")
    out = tmp_path / "out"
    out.mkdir()

    result = execute(ConversionRequest(source, "docx", out))

    assert result.output_path.is_file()
    assert result.output_path.suffix == ".docx"
    assert result.size > 0
```

## Manual checks

Automated tests do not cover the GUI. Use `test_data/` for a quick manual pass:

1. `./run.sh` and confirm the window appears.
2. `test_data/sample.csv` → JSON; open the result.
3. `test_data/sample.json` → CSV.
4. `test_data/sample.txt` → PDF; confirm Polish/Cyrillic text renders.
5. `test_data/sample.docx` → TXT, and (with LibreOffice) PDF and ODT.
6. `test_data/sample.odt` → TXT, and (with LibreOffice) PDF and DOCX.
7. Convert twice to the same name; check the overwrite dialog's three actions.
8. Switch language and theme; select another file and confirm state is preserved.
9. Start a conversion and close the window; confirm the confirmation dialog.

Expected results per sample file are documented in [`test_data/README.md`](../test_data/README.md).
