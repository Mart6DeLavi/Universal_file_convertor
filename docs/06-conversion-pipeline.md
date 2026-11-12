# 06 — Conversion pipeline

This page describes what happens between pressing **Convert** and getting a file, followed by the exact semantics of every direction.

## Stages

```text
ConversionRequest
      │
      ▼
1. validate_source        exists? regular file? extension supported?
      ▼
2. validate_target_format registered? dependency available?
      ▼
3. validate_output_dir    exists? directory? writable?
      ▼
4. build_output_path      name valid? extension matches? not the source?
      ▼
5. conflict check         target exists and overwrite not allowed?
      ▼
6. temporary directory    .ufc-XXXX inside the output folder
      ▼
7. converter              converter(source, temp_output)
      ▼
8. result validation      file exists? regular? non-empty (unless allowed)?
      ▼
9. atomic publish         os.replace(temp_output, output_path)
      ▼
ConversionResult
```

Progress values reported by `service.execute`:

| Value | Meaning |
|---:|---|
| 0.02 | request accepted, validation starting |
| 0.08 | validation finished |
| 0.15 | temporary directory prepared |
| 0.82 | converter returned |
| 0.90 | output existence and size verified |
| 0.97 | file published |
| 1.00 | result logged and returned |

The GUI smooths these values and additionally advances them with a time-based estimate while the worker is busy (see [08 — GUI reference](08-gui-reference.md)).

## Validation rules

### Source

`validate_source(source)` rejects:

- an empty / missing path (`ValidationError: No source file was selected.`);
- a non-existent path (`Source file not found`);
- a directory or special file (`The path is not a regular file`);
- a file without an extension;
- an extension outside `SOURCE_FORMATS` **or** without any registered direction.

`SourceInfo.from_path` additionally reports unreadable files (permissions) as `ValidationError`.

### Target

`validate_target_format(source_format, target_format)`:

1. normalizes the value (strip, lowercase, remove leading dot);
2. requires a non-empty target and membership in `TARGET_FORMATS`;
3. requires a registered `(source, target)` spec;
4. if `spec.requires_libreoffice`, checks `available_targets(source_format)` and raises `DependencyMissingError` when running LibreOffice is not detected.

### Output directory

`validate_output_dir` requires an existing directory and proves writability by creating and deleting a temporary file (`.ufc-check-*.tmp`) in it. This catches read-only mounts and permission problems before the conversion starts.

### Output name and path

`build_output_path`:

1. uses the user name, or generates `<sanitized stem>.<target>`;
2. validates the name (see `utils.paths.validate_output_name`);
3. appends the target extension if the name has none;
4. rejects a mismatched extension, e.g. `report.zip` for target PDF;
5. builds `output_dir / name`.

Then `validate_request` rejects an output path that resolves to the source file (`same_file`), and — unless `overwrite=True` — an existing target. The conflict error carries a suggested free name from `unique_path`, e.g. `report (1).pdf`.

### Name sanitization

`sanitize_stem`:

- replaces `< > : " / \ | ? *` and control characters with `_`;
- strips leading/trailing dots and whitespace;
- falls back to `converted` when nothing remains;
- prefixes a reserved Windows device name (`CON`, `PRN`, `AUX`, `NUL`, `COM1–9`, `LPT1–9`) with `_`.

`validate_output_name` additionally rejects names containing a path (`Path(name).name != name`), `.`/`..`, invalid characters, reserved names, and names longer than 200 characters.

## Temporary folder and atomic write

The service creates:

```python
with tempfile.TemporaryDirectory(prefix=".ufc-", dir=target_dir) as tmp:
    temp_output = Path(tmp) / output_name
    spec.converter(source, temp_output)
    ...
    os.replace(temp_output, output_path)
```

Consequences:

- a failed converter leaves no partial file at the destination;
- the destination filesystem is not crossed, so `os.replace` is atomic;
- if the temporary directory cannot be created (permissions, full disk), the error is raised before any conversion;
- after the block, the temporary directory is removed by `TemporaryDirectory`.

The service also checks that the converter wrote a **regular file** and that it is **non-empty**, unless the spec sets `allow_empty=True`. Only JSON → CSV sets this flag, because an empty JSON array legitimately produces an empty CSV.

A second conflict check runs just before `os.replace`, so a file created by another process during the conversion is not overwritten without an explicit overwrite flag.

## Direction semantics

### 1. CSV → JSON

Function: `file_converter.converters.csv_json.csv_to_json`.

- Encoding: UTF-8 with optional BOM (`utf-8-sig`). Other encodings raise `ConversionError`.
- The first non-empty row is the header row; blank rows are ignored.
- Delimiter detection: `UFC_CSV_DELIMITER` if set; otherwise `csv.Sniffer` on the first 8192 bytes with the candidate set `, ; TAB |`; fallback is the standard comma dialect.
- Headers must be non-empty and unique.
- Every data row must have exactly as many fields as the header row, otherwise a `ConversionError` names the row.
- Each row becomes an object; keys follow column order; all values remain strings (no type inference).
- Output is a JSON array with 2-space indentation, newline at the end, and `ensure_ascii=False`.

Example: a row `Jan,Kowalski` under headers `imię,nazwisko` becomes `{"imię": "Jan", "nazwisko": "Kowalski"}`.

### 2. JSON → CSV

Function: `json_to_csv`.

- The top level must be an array; every element must be an object.
- An empty array is valid and yields an empty file (`allow_empty=True`).
- Headers are the union of keys in order of first appearance.
- Missing keys become empty cells.
- Values:

  | JSON value | CSV cell |
  |---|---|
  | string | as-is |
  | number | `str(value)` |
  | `true` / `false` | `true` / `false` |
  | `null` | empty string |
  | object / array | compact JSON string |

- Written with `newline=""` so quoting and embedded line breaks are valid CSV.
- Invalid JSON reports the line and column from `json.JSONDecodeError`.

### 3. TXT → DOCX

Function: `txt_to_docx`.

- Reads UTF-8 (BOM accepted).
- Normalizes `CRLF`/`CR` to `LF`.
- Each line becomes one paragraph. A single trailing newline does not create an extra empty paragraph.
- An empty file produces a document with one empty paragraph.
- No styles, headings, lists, or page setup are added.

### 4. DOCX → TXT

Function: `docx_to_txt`.

- Walks the document body in order, including paragraphs and tables.
- Paragraph text is emitted as a line.
- Each table row becomes one line; cell paragraphs are joined with spaces, cells with tabs.
- Headers, footers, footnotes, images, comments, and styles are not extracted.
- A damaged or non-Word file raises `ConversionError`.

### 5. TXT → PDF

Function: `txt_to_pdf`.

- Reads UTF-8 (BOM accepted).
- A4 page, 56 pt margins, 11 pt font, 15 pt leading.
- Lines are wrapped by words; a word longer than the line is split.
- New pages are started automatically at the bottom margin.
- The PDF title is the source stem.
- Unicode font candidates, in order:

  1. `/System/Library/Fonts/Supplemental/Arial Unicode.ttf` (macOS)
  2. `/Library/Fonts/Arial Unicode.ttf` (macOS)
  3. `/System/Library/Fonts/Supplemental/Arial.ttf` (macOS)
  4. `/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf` (Linux)
  5. `/usr/share/fonts/TTF/DejaVuSans.ttf` (Linux)
  6. `/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf`
  7. `C:\Windows\Fonts\arial.ttf`
  8. `C:\Windows\Fonts\DejaVuSans.ttf`

  The font is registered once as `UFCUnicode`. If none is found, `DependencyMissingError` explains what to install.
- Blank lines are preserved as vertical space.
- No images, links, tables, headers, or rich text.

### 6–9. LibreOffice directions

Functions: `docx_to_pdf`, `odt_to_pdf`, `docx_to_odt`, `odt_to_docx`, all delegating to `convert_with_libreoffice`.

- `DOCX → PDF` and `ODT → PDF` use the `pdf:writer_pdf_Export` filter.
- `DOCX → ODT` uses `odt:writer8`.
- `ODT → DOCX` uses `docx:MS Word 2007 XML`.
- Layout and formatting quality depend on the installed LibreOffice version.
- Sources are opened read-only; output is produced in a separate temporary directory and then moved to the requested target path.

Details of process invocation are below.

### 10. ODT → TXT

Function: `odt_to_txt`.

- Uses `odfpy` to load the document.
- Recursively collects text from paragraphs (`p`) and headings (`h`).
- Tables: each row becomes one line, cells are joined with spaces inside a cell and tabs between cells.
- Other blocks (lists etc.) are traversed and their text collected.
- Formatting, images, headers, footers, and notes are not extracted.
- A damaged file raises `ConversionError`.

## LibreOffice integration

`file_converter.converters.libreoffice`:

### Discovery

`find_libreoffice()` tests candidates in order:

1. `UFC_SOFFICE`
2. `LIBREOFFICE_PATH`
3. `soffice_path` in `config.json`
4. `shutil.which("soffice")`, `shutil.which("libreoffice")`
5. macOS: `/Applications/LibreOffice.app/Contents/MacOS/soffice`, `~/Applications/LibreOffice.app/Contents/MacOS/soffice`
6. Windows: `%ProgramFiles%\LibreOffice\program\soffice.exe`, `%ProgramFiles(x86)%\LibreOffice\program\soffice.exe`
7. Linux: `/usr/bin/soffice`, `/usr/bin/libreoffice`, `/snap/bin/libreoffice`, `/usr/lib/libreoffice/program/soffice`

A directory candidate is searched for `Contents/MacOS/soffice` or `program/soffice`. A candidate must be a file and executable.

### Invocation

```text
soffice
  --headless --invisible --norestore --nodefault --nolockcheck
  -env:UserInstallation=file:///tmp/ufc-lo-profile-XXXX
  --convert-to <filter>
  --outdir /tmp/ufc-lo-out-XXXX
  <source>
```

Notes:

- An isolated temporary user profile avoids conflicts with a running LibreOffice instance.
- The process runs with `shell=False`, `capture_output=True`, `text=True`, and a **120-second timeout** (`LIBREOFFICE_TIMEOUT`).
- The produced file is located by expected name (`<stem>.<suffix>`), falling back to the first file with the right extension in the output directory.
- An empty result is rejected.
- `os.replace` publishes the file; if that fails across filesystems, `shutil.copy2` is used as a fallback.

### Errors

| Condition | Exception |
|---|---|
| executable not found | `DependencyMissingError` with install hints |
| timeout | `ExternalProcessError` with partial stderr |
| non-zero exit code | `ExternalProcessError` with the last 2000 characters of output |
| expected file missing | `ExternalProcessError` |
| empty output | `ConversionError` |
| cannot save result | `ConversionError` |

## Failure guarantees

- A failed conversion never leaves the destination partially written.
- The source is never opened for writing.
- The existing destination is only replaced after a successful conversion and only with `overwrite=True`.
- Log entries are written for the start and for any failure; a successful conversion logs source, target, output, size, and duration.
- The GUI never reports success unless `ConversionResult` was returned.
