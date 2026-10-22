# Universal File Converter

[English](README.md) | [Polski](README.pl.md)

A local desktop application for converting spreadsheets, text files, and office documents. Files are never uploaded; the app shows only genuinely supported directions and never overwrites an existing file without confirmation.

The application is written in Python with a CustomTkinter interface. Office conversions are performed by LibreOffice in headless mode.

## Purpose

The user selects a source file and an output folder, sees the formats available for that file, starts a conversion, and receives a finished file. The entire workflow runs in the GUI, without a terminal. If LibreOffice is not installed, the associated directions are hidden and are not reported as available.

## Features

- Two-column interface: source and conversion settings on the left, result on the right.
- No scrolling: the complete workflow is visible at the default and minimum window sizes.
- Source and output-folder selection through native file dialogs.
- Source details: name, path, format, and size.
- Dynamic target-format list based on the source file and installed dependencies.
- Background conversion: the interface stays responsive.
- Determinate progress bar with a percentage and smooth fill, a clear final status, and a detailed result card.
- Overwrite protection: confirmation, automatic unique name, or cancel.
- Validation of inputs, output folder, dependencies, and conversion result.
- Preservation of Polish, Cyrillic, and other Unicode characters.
- Open the converted file or its folder directly from the interface.
- Operation and error logging.
- Dark and light themes.
- English and Polish user interface with a header switch; the choice is saved between launches.

## Supported Formats

Source formats: CSV, JSON, TXT, DOCX, ODT.

Target formats: CSV, JSON, TXT, DOCX, ODT, PDF.

PDF is supported only as a target format. Extracting content from PDF is not implemented.

## Conversion Matrix

| # | Source | Target | Engine | What is preserved | Limitations |
|---:|---|---|---|---|---|
| 1 | CSV | JSON | `csv`, `json` | Headers, column and key order, Unicode, empty strings | One table; types are not inferred |
| 2 | JSON | CSV | `csv`, `json` | Array of objects, combined key set, Unicode | Top level must be an array of objects; nested values are serialized into a cell |
| 3 | TXT | DOCX | `python-docx` | Each line becomes a separate paragraph; Unicode | Line breaks are paragraph boundaries; no styling is created |
| 4 | DOCX | TXT | `python-docx` | Paragraph and table text in document order | Styles, images, headers, footers, and markup are not transferred |
| 5 | TXT | PDF | `reportlab` | Text, Unicode, long-line wrapping, pagination | Basic A4 margins; images, links, and rich text are not supported |
| 6 | DOCX | PDF | LibreOffice | Layout and formatting within LibreOffice capabilities | Requires LibreOffice |
| 7 | ODT | PDF | LibreOffice | Layout and formatting within LibreOffice capabilities | Requires LibreOffice |
| 8 | DOCX | ODT | LibreOffice | Document structure and formatting | Requires LibreOffice |
| 9 | ODT | DOCX | LibreOffice | Document structure and formatting | Requires LibreOffice |
| 10 | ODT | TXT | `odfpy` | Paragraph, heading, list, and table text | Formatting and non-text objects are not transferred |

All ten directions are registered in the converter registry. Directions 6–9 become visible in the GUI only when LibreOffice is available.

## CSV → JSON Semantics

- Encoding is UTF-8; a BOM is accepted through `utf-8-sig`.
- The first non-empty row is treated as the header row.
- The delimiter is detected automatically among `,`, `;`, tab, and `|`. It can be set explicitly with the `UFC_CSV_DELIMITER` environment variable (one character; use `\t` for a tab).
- Each data row becomes a JSON object. Key order matches column order.
- All values remain strings. Numbers, dates, `true`/`false`, and `null` are not detected automatically.
- An empty field remains an empty string.
- Quotes, commas inside values, and multiline fields are supported.
- Empty and duplicate headers are rejected because the conversion would be ambiguous.
- Every row must have the same number of fields as there are headers.
- An empty file, a file without headers, and a file without data rows are errors.
- The result is written as a JSON array with two-space indentation and without ASCII-escaping Unicode.

Example:

```csv
imię,nazwisko,miasto,uwagi
Jan,Kowalski,Łódź,"Zażółć gęślą jaźń"
Anna,Nowak,Kraków,
```

```json
[
  {
    "imię": "Jan",
    "nazwisko": "Kowalski",
    "miasto": "Łódź",
    "uwagi": "Zażółć gęślą jaźń"
  },
  {
    "imię": "Anna",
    "nazwisko": "Nowak",
    "miasto": "Kraków",
    "uwagi": ""
  }
]
```

## JSON → CSV Semantics

- The top level must be a JSON array of objects. An empty array is valid and creates an empty CSV file.
- Every array element must be an object. Arrays of primitives and mixed arrays are rejected.
- Headers are formed from keys in order of first appearance.
- A missing key becomes an empty cell.
- Nested objects and arrays are written into a cell as a compact JSON string.
- `true` and `false` are written as `true` and `false`; `null` becomes an empty cell.
- Invalid JSON produces a controlled error with the line and column number.
- CSV is written as UTF-8 with `newline=""`, so quotes and line breaks are escaped correctly.

Example:

```json
[
  {"b": 1, "a": "Żółw", "nested": {"x": 1}},
  {"a": "Zażółć gęślą jaźń", "c": true}
]
```

```csv
b,a,nested,c
1,Żółw,"{""x"":1}",
,Zażółć gęślą jaźń,,true
```

## Interface

The main window contains:

- a header with the application name, version, language switch, and theme switch;
- a left panel with the source file, source details, target format, output folder, output name, result preview, Convert button, and a progress bar with a percentage;
- a right panel with an empty state before conversion, a success state with the result name, full path, format, size, duration, and open buttons, or an error state with a hint.

The layout has no scrollable containers. The window opens at `1180x720` and remains usable at the minimum size of `1000x620`. Long paths wrap inside their labels instead of pushing controls out of view.

Conversion runs in a background thread. Widget updates and progress events are delivered to the main thread through a queue, so the window does not freeze. The right panel switches to a centered conversion state while the file is being processed.

## Architecture

```text
FileConvertor/
├── app.py                         # entry point, starts the GUI
├── requirements.txt               # Python dependencies
├── README.md                      # English documentation
├── README.pl.md                   # Polish documentation
├── PLAN.md                        # supplied assignment
├── docs/                          # internal implementation notes
├── logs/                          # application logs
├── reports/
│   ├── test_report.md             # English test report
│   └── test_report.pl.md          # Polish test report
├── src/
│   └── file_converter/
│       ├── config.py              # constants, formats, LibreOffice path
│       ├── exceptions.py          # unified error hierarchy
│       ├── logging_config.py      # rotating file logger
│       ├── models.py              # request, result, and source models
│       ├── registry.py            # converter registry and available targets
│       ├── validators.py          # request and path validation
│       ├── service.py             # execution, temp folder, atomic write
│       ├── converters/
│       │   ├── csv_json.py        # CSV ↔ JSON
│       │   ├── text_converters.py # TXT, DOCX, ODT, PDF
│       │   ├── document_converters.py # office conversion wrappers
│       │   └── libreoffice.py     # headless LibreOffice integration
│       ├── gui/
│       │   ├── main_window.py     # main window and background operations
│       │   ├── components.py      # cards and status indicator
│       │   ├── dialogs.py         # overwrite and message dialogs
│       │   └── i18n.py            # English and Polish interface strings
│       └── utils/
│           ├── paths.py           # names, conflicts, write permissions
│           └── platform_utils.py  # open file and folder
├── tests/                         # pytest suite
└── test_data/                     # example files and expected results
```

Execution flow: GUI → validators → registry → service → concrete converter. The service creates a temporary folder inside the output directory, verifies the result, and only then atomically replaces the target file through `os.replace`. The source file is never modified.

## Requirements

- Python 3.11 or newer. The project was verified on Python 3.14.8.
- Tk 8.6 or newer. CustomTkinter requires a Python build with Tk support.
- macOS, Windows, or Linux.
- LibreOffice only for DOCX → PDF, ODT → PDF, DOCX → ODT, and ODT → DOCX.

## Installing Python Dependencies

macOS/Linux:

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

Windows PowerShell:

```powershell
py -3.11 -m venv .venv
.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

If you use a Homebrew Python on macOS and see a `_tkinter` error at startup, install Tk for the matching Python version:

```bash
brew install python-tk@3.14
```

On Debian/Ubuntu:

```bash
sudo apt install python3-tk
```

## Installing LibreOffice

LibreOffice is required for the four office directions. Without it, the application still works, but those directions are hidden.

macOS:

```bash
brew install --cask libreoffice
```

Alternatively, download the installer from [libreoffice.org](https://www.libreoffice.org/download/) and drag LibreOffice into `/Applications`.

Windows:

Download and install LibreOffice from [libreoffice.org](https://www.libreoffice.org/download/). The executable is usually located at:

```text
C:\Program Files\LibreOffice\program\soffice.exe
```

Debian/Ubuntu:

```bash
sudo apt update
sudo apt install libreoffice
```

Fedora:

```bash
sudo dnf install libreoffice
```

Arch Linux:

```bash
sudo pacman -S libreoffice-fresh
```

Verify the installation:

```bash
soffice --version
```

On macOS you can check the application bundle directly:

```bash
/Applications/LibreOffice.app/Contents/MacOS/soffice --headless --version
```

### Configuring the LibreOffice Path

The application looks for `soffice` in this order:

1. `UFC_SOFFICE` environment variable.
2. `LIBREOFFICE_PATH` environment variable.
3. `soffice_path` key in `~/.config/universal-file-converter/config.json`.
4. `soffice` and `libreoffice` commands in `PATH`.
5. Standard installation directories on macOS, Windows, and Linux.

macOS/Linux example:

```bash
export UFC_SOFFICE="/Applications/LibreOffice.app/Contents/MacOS/soffice"
```

Windows PowerShell example:

```powershell
$env:UFC_SOFFICE = "C:\Program Files\LibreOffice\program\soffice.exe"
```

`config.json` example:

```json
{
  "soffice_path": "/Applications/LibreOffice.app/Contents/MacOS/soffice"
}
```

Configuration file location: `~/.config/universal-file-converter/config.json`. On Windows, the current user's home directory is used.

## Running the Application

From the project root:

```bash
python app.py
```

If the virtual environment is not activated:

```bash
.venv/bin/python app.py
```

To send the log to the console as well:

```bash
UFC_LOG_CONSOLE=1 python app.py
```

## Running Tests

```bash
python -m pytest -v
```

Without LibreOffice, all native tests run and the four real office checks are skipped with a reason. With LibreOffice installed, the complete suite runs.

Current result on macOS with LibreOffice 26.8.1: **60 passed**. Details are in [`reports/test_report.md`](reports/test_report.md).

## Examples and Test Data

The `test_data/` directory contains:

- `sample.csv` — Unicode, an empty field, a comma, quotes, and a multiline value;
- `sample.json` — a nested object, a missing key, and boolean values;
- `sample.txt` — Polish and Cyrillic text with blank lines;
- `sample.docx` — a heading, paragraphs, a table, and Unicode;
- `sample.odt` — paragraphs, a table, and Unicode;
- `README.md` — expected results for each file.

Quick check through the GUI:

1. Run `python app.py`.
2. Select `test_data/sample.csv`.
3. Confirm that only JSON is available.
4. Choose an output folder and press **Convert**.
5. Open the result with **Open file**.
6. Repeat with `sample.docx`: TXT, ODT, and PDF should be available when LibreOffice is installed.

## Error Handling and Safety

- The source file's existence, type, and supported extension are checked.
- The target format must be registered and its dependency available.
- The output directory must exist and be writable.
- An existing file is never overwritten without explicit confirmation. The dialog offers overwrite, a unique name such as `name (1).ext`, or cancel.
- Invalid file names, an extension mismatch, and identical source and output paths are rejected before conversion starts.
- Conversion runs in a temporary folder inside the output directory. The final file appears only after a successful check.
- The converter must create a non-empty file (except an empty JSON array, which becomes an empty CSV).
- LibreOffice exit code, the 120-second timeout, and output existence and size are checked; `stdout` and `stderr` are retained.
- LibreOffice runs with an isolated temporary profile so it does not conflict with an already open instance.
- External processes are started with argument lists and `shell=False`.
- Errors are shown in the GUI with an explanation and written to the log. The application never reports success if the file was not created.
- The source file is opened read-only and is never changed.

## Logging

Log file: `logs/converter.log`.

A `RotatingFileHandler` keeps files up to 1 MB with three backups. The log records conversion start, source, target format, result, duration, and exceptions.

If the log directory is unavailable, the application continues to work and does not terminate because of a logging error.

## Known Limitations

- One file is processed per operation; batch conversion is not implemented.
- Only the listed directions are supported. PDF is not a source format.
- The legacy `.doc` format is not supported; `.docx` and `.odt` are used.
- CSV and JSON are read as UTF-8 only (a BOM is allowed). Other encodings must be converted beforehand.
- CSV uses one delimiter. It can be configured with `UFC_CSV_DELIMITER`, but not through the GUI.
- JSON → CSV does not expand nested structures into separate columns; it serializes them into a cell.
- TXT → DOCX does not create styles, lists, or tables: each line becomes a paragraph.
- DOCX → TXT and ODT → TXT extract text only; formatting, images, headers, footers, and footnotes are not preserved.
- TXT → PDF creates a simple A4 document without rich text. For Unicode it uses the first available Arial/DejaVu/Liberation system font.
- The quality of DOCX/ODT → PDF and DOCX ↔ ODT depends on the installed LibreOffice version. Complex fonts, macros, and external objects may render differently.
- Office conversions are limited by a 120-second timeout.
- Passwords, digital signatures, and PDF/A are not supported.
- The application does not upload files or use cloud services.

## Libraries and External Components

- [CustomTkinter](https://customtkinter.tomschimansky.com/) — desktop interface.
- [python-docx](https://python-docx.readthedocs.io/) — reading and creating DOCX.
- [odfpy](https://github.com/eea/odfpy) — reading ODT.
- [ReportLab](https://www.reportlab.com/opensource/) — creating PDF.
- [Pillow](https://python-pillow.org/) — graphics stack dependency.
- [pypdf](https://pypdf.readthedocs.io/) — PDF verification in tests.
- [pytest](https://pytest.org/) — automated tests.
- [LibreOffice](https://www.libreoffice.org/) — office conversions in headless mode.
- Python standard library: `csv`, `json`, `subprocess`, `tempfile`, `logging`, `pathlib`, `tkinter`.

## AI Usage

The project was implemented with the help of the opencode AI assistant. Generated code was verified with automated tests, manual GUI scenarios, and real file conversions. All limitations and environment-specific unverified capabilities are stated explicitly; the application does not present unavailable conversions as working.

## Author

Mart6DeLavi, a university programming project.
