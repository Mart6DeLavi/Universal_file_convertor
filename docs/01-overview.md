# 01 — Overview

Universal File Converter is a desktop application for converting small office and data files. Everything runs locally: files are read from disk, converted, and written back to a folder chosen by the user. Nothing is uploaded anywhere.

The interface is built with CustomTkinter. Most conversions are implemented in pure Python (`csv`, `json`, `python-docx`, `odfpy`, `reportlab`). Four office directions are delegated to LibreOffice in headless mode.

## What the application guarantees

1. **Only real directions are offered.** The target-format list is generated from the converter registry and filtered by installed dependencies. If LibreOffice is missing, `DOCX → PDF`, `ODT → PDF`, `DOCX → ODT`, and `ODT → DOCX` are hidden instead of failing later.
2. **No silent overwrites.** An existing target file triggers a dialog: overwrite, save under a unique name, or cancel.
3. **The source file is never modified.** Sources are opened read-only. The service verifies the result before publishing it.
4. **No partial results.** Conversion happens in a temporary directory inside the output folder. The final file appears only after the converter produced a non-empty file and the result passed checks (`os.replace` is atomic on the same filesystem).
5. **Errors are explained.** Every failure carries a message and, usually, a hint. The GUI shows both; the log keeps the traceback.
6. **Unicode is preserved.** Polish, Cyrillic, and other characters survive CSV ↔ JSON, TXT ↔ DOCX, ODT → TXT, and TXT → PDF.

## Supported formats

| Role | Formats |
|---|---|
| Source | CSV, JSON, TXT, DOCX, ODT |
| Target | CSV, JSON, TXT, DOCX, ODT, PDF |

PDF is a target only. Reading text out of PDF is not implemented.

## Conversion matrix

All ten directions are registered in `file_converter.registry`. Directions 6–9 are visible only when LibreOffice is found.

| # | Source | Target | Engine | Requires LibreOffice |
|---:|---|---|---|---|
| 1 | CSV | JSON | Python `csv` + `json` | No |
| 2 | JSON | CSV | Python `json` + `csv` | No |
| 3 | TXT | DOCX | `python-docx` | No |
| 4 | DOCX | TXT | `python-docx` | No |
| 5 | TXT | PDF | `reportlab` | No |
| 6 | DOCX | PDF | LibreOffice (`writer_pdf_Export`) | Yes |
| 7 | ODT | PDF | LibreOffice (`writer_pdf_Export`) | Yes |
| 8 | DOCX | ODT | LibreOffice (`writer8`) | Yes |
| 9 | ODT | DOCX | LibreOffice (`MS Word 2007 XML`) | Yes |
| 10 | ODT | TXT | `odfpy` | No |

Detailed semantics and limitations of each direction are in [06 — Conversion pipeline](06-conversion-pipeline.md).

## Feature summary

- Two-column, non-scrolling window: source and settings on the left, result on the right.
- Source details: name, format, size, full path in the read-only field.
- Auto-filled output folder (the source folder unless the user changed it).
- Auto-generated output name, editable at any time.
- Live result preview with the final path and an "already exists" warning.
- Background conversion with a determinate progress bar and percentage.
- Success card with file name, path, format, size, duration, and open buttons.
- Dedicated error card with the message and hint.
- Overwrite dialog: overwrite / save as `name (1).ext` / cancel.
- Dark and light theme.
- English and Polish interface, persisted in the config file.
- Rotating log file.

## What the application does not do

- Batch conversion of several files at once.
- PDF as a source.
- Legacy `.doc` or `.xls` files.
- Cloud storage or uploads.
- OCR, password-protected documents, digital signatures, PDF/A.
- Conversion from a command line (there is no CLI; `app.py` only starts the GUI).

## Glossary

| Term | Meaning |
|---|---|
| **Source** | The file selected by the user; its extension defines the source format. |
| **Target** | The desired output format, for example `pdf`. |
| **Direction** | A registered source → target pair, for example `docx → pdf`. |
| **Converter** | A function `(source: Path, target: Path) -> Path` registered for one direction. |
| **Registry** | The in-memory table of all directions (`file_converter.registry.REGISTRY`). |
| **Spec** | `ConverterSpec`: registry metadata for one direction (function, description, dependency flags). |
| **Request** | `ConversionRequest`: source, target, output directory, optional name, overwrite flag. |
| **Result** | `ConversionResult`: request, output path, duration, warnings. |
| **soffice** | The LibreOffice executable used for headless conversions. |

## Related documents

- Installation and launch: [02 — Installation and launch](02-installation-and-launch.md)
- Using the GUI: [03 — Usage](03-usage.md)
- Code architecture: [04 — Architecture](04-architecture.md)
