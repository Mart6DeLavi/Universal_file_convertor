# Test Report

[English](test_report.md) | [Polski](test_report.pl.md)

Test date: 21 October 2026.

## Environment

| Component | Version |
|---|---|
| OS | macOS 26.6.2 (build 25G83) |
| Python | 3.14.8 |
| Tk / Tcl | 9.1 / 9.1 |
| pytest | 9.1.1 |
| CustomTkinter | 6.0.0 |
| python-docx | 1.2.0 |
| ReportLab | 5.0.1 |
| pypdf | 6.21.1 |
| Pillow | 13.0.0 |
| LibreOffice | 26.8.1.1 |

LibreOffice was installed with Homebrew and is discovered by the application as `/opt/homebrew/bin/soffice`. The standard application path `/Applications/LibreOffice.app/Contents/MacOS/soffice` is also detected.

## Test Command

```bash
.venv/bin/python -m pytest -v
```

## Result

```text
54 passed in 5.54s
```

There are no failures or skipped tests. All ten directions from the assignment matrix are implemented and verified in this environment.

## Automated Tests by Module

| File | Tests | What is checked |
|---|---:|---|
| `tests/test_csv_json.py` | 14 | CSV ↔ JSON, Unicode, BOM, quotes, commas, multiline fields, empty values, delimiters, header and structure errors, empty array, roundtrip |
| `tests/test_document_converters.py` | 8 | Real office conversions through LibreOffice, missing dependency, timeout, nonzero exit code, missing output, source preservation |
| `tests/test_registry.py` | 6 | Registry, registered directions, filtering of LibreOffice-dependent targets, duplicates, delegation to the service |
| `tests/test_service.py` | 8 | Full service flow, conflicts, overwrite, unique names, temporary folders, empty CSV, source preservation on failure |
| `tests/test_text_converters.py` | 6 | TXT ↔ DOCX, TXT → PDF, ODT → TXT, Unicode, tables, malformed documents |
| `tests/test_validators.py` | 12 | Source, extension, target format, directory, name, conflict, and LibreOffice dependency validation |

## Office Direction Verification

Each test uses a document with Unicode text and spaces in its filename. After conversion, both file existence and file content are checked.

| Direction | Result check | Status |
|---|---|---|
| DOCX → PDF | `%PDF` signature, text extraction with `pypdf`, presence of `Zażółć` and `Łódź` | Passed |
| ODT → PDF | `%PDF` signature, text extraction with `pypdf`, presence of Unicode text | Passed |
| DOCX → ODT | Opening with `odfpy`, text extraction, presence of Unicode text | Passed |
| ODT → DOCX | Opening with `python-docx`, presence of Unicode text | Passed |

In addition, each test compares the source file bytes before and after conversion. Source documents are not modified.

## End-to-End Verification of All 10 Directions

All directions were also executed through the public `ConversionService.execute` API using files from `test_data/`. Each result was opened with the appropriate parser: `json`, `csv`, `python-docx`, `odfpy`, or `pypdf`.

| # | Direction | Result check | Size |
|---:|---|---|---:|
| 1 | CSV → JSON | JSON array parsed successfully | 591 bytes |
| 2 | JSON → CSV | CSV read successfully | 167 bytes |
| 3 | TXT → DOCX | DOCX opened, text present | 36,845 bytes |
| 4 | DOCX → TXT | Text extracted | 230 bytes |
| 5 | TXT → PDF | PDF opened, text extracted | 36,939 bytes |
| 6 | DOCX → PDF | PDF opened, text extracted | 29,331 bytes |
| 7 | ODT → PDF | PDF opened, text extracted | 21,259 bytes |
| 8 | DOCX → ODT | ODT opened with `odfpy` | 14,964 bytes |
| 9 | ODT → DOCX | DOCX opened, text present | 5,119 bytes |
| 10 | ODT → TXT | Text extracted | 230 bytes |

All ten checks passed. Source files were not modified.

## GUI Verification

The redesigned CustomTkinter window was checked with the real `MainWindow`, the background conversion thread, and a separate empty output folder for each case.

### Layout

| Check | Result |
|---|---|
| Default window size | `1180x720` |
| Minimum window size | `1000x620` |
| Scrollable containers | None; no `CTkScrollableFrame` |
| Scrollbars visible | None at default or minimum size |
| All source controls visible at minimum size | Yes |
| Progress and status visible at minimum size | Yes |
| Result panel starts in the empty state | Yes |
| Success state shows name, path, format, size, duration, and open buttons | Yes |
| Long paths wrap without clipping controls | Yes |
| UI language | English |
| Theme switch | Works |

### Conversions Through the GUI

| Source file | Target | Available targets | Result |
|---|---|---|---|
| `test_data/sample.csv` | JSON | JSON | File created; result card updated |
| `test_data/sample.txt` | PDF | DOCX, PDF | File created; PDF opened and text extracted |
| `test_data/sample.docx` | PDF | TXT, ODT, PDF | File created; PDF contains Unicode text |
| `test_data/sample.odt` | DOCX | TXT, DOCX, PDF | File created; text readable with `python-docx` |

The interface did not freeze, the completion status was updated after the background operation, and the controls were disabled while work was in progress. The overwrite dialog opens correctly when the target name already exists.

## Behavior Without LibreOffice

Before LibreOffice was installed, the test suite produced **50 passed, 4 skipped**. The four real office checks were skipped with the reason "LibreOffice is not installed in this environment". In that state:

- the application launched;
- native conversions worked;
- DOCX → PDF, ODT → PDF, DOCX → ODT, and ODT → DOCX were not shown in the GUI;
- requesting a dependent conversion programmatically produced a clear error with installation instructions.

After LibreOffice installation, all four checks run without skips.

## Verified Limitations

- Tests check textual content and format validity, but do not perform pixel-level comparison of PDF layout.
- Office conversion quality depends on the LibreOffice version and available fonts.
- Tests do not cover password-protected documents, macros, digital signatures, or PDF/A.
- Only UTF-8 is supported for CSV, JSON, and TXT.
- Batch conversion and PDF as a source format are not implemented.

## Conclusion

All required directions work in the current environment. The tests cover successful paths as well as validation errors, name conflicts, a missing external dependency, timeout, and incorrect LibreOffice output. The verified limitations are documented in the README and are not presented as fully supported features.
