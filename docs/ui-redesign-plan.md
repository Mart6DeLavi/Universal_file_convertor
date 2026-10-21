# UI Redesign and Localization Plan

## Goal

Rework the application so that:

- the entire workflow is visible without scrolling;
- the window has a clear two-column layout: source on the left, result on the right;
- all application UI text is in English;
- documentation is available in English and Polish;
- mouse-wheel scrolling is no longer required anywhere.

## Current Problems

1. The main window uses `CTkScrollableFrame`; the mouse wheel does not scroll it, only dragging the scrollbar works.
2. The layout is a single tall column, so the result and controls are not visible together.
3. GUI labels, dialogs, validation messages, and converter errors are in Russian.
4. `README.md`, `reports/test_report.md`, and `test_data/README.md` are in Russian only.
5. The current default size is `1040x860`, which encourages vertical scrolling.

## Target Layout

Use a fixed two-column workspace with no scrollable container.

```text
┌──────────────────────────────────────────────────────────────┐
│ Universal File Converter                    [Light theme]     │
├──────────────────────────────┬───────────────────────────────┤
│ SOURCE                       │ RESULT                        │
│                              │                               │
│ [Choose file..............]  │  No result yet                │
│ Name / format / size         │  Convert a file to see it     │
│                              │  here.                        │
│ Target format [v]            │                               │
│ Output folder [...........]  │  Result name                  │
│ Output name [.............]  │  Full path                    │
│ Preview                      │  Size / format / duration     │
│                              │                               │
│ [Convert]                    │  [Open file] [Open folder]    │
│ Status / progress            │                               │
└──────────────────────────────┴───────────────────────────────┘
```

### Window

- Default size: about `1180x720`.
- Minimum size: about `1000x620`.
- Header at the top, workspace fills the rest of the window.
- Use `grid` with column weights; both panels expand with the window.
- No `CTkScrollableFrame`, no vertical or horizontal scrollbars.
- All essential controls must remain visible at the minimum size.
- Long paths must wrap or be truncated with a tooltip; they must not push controls out of view.
- The theme switch stays in the header.

### Left Panel: Source and Options

- Source file picker and read-only path field.
- Compact source details: name, format, size.
- Target format menu with only available targets.
- Output directory picker.
- Output name field and preview.
- Convert button.
- Status indicator and indeterminate progress bar.
- All controls fit vertically at `1000x620`.

### Right Panel: Result

- Empty state before conversion: short instruction and supported-direction hint.
- Success state after conversion:
  - result file name;
  - full output path;
  - file size;
  - target format;
  - conversion duration;
  - buttons to open the file and its folder.
- Error state: concise error summary and hint; detailed diagnostics remain in the log.
- Right panel must not resize the window or introduce scrolling when a long path is shown.

## English UI

Translate every user-facing string, including:

- window title, header subtitle, section headings;
- buttons, field labels, hints, placeholders;
- status messages and progress labels;
- overwrite, confirmation, and error dialogs;
- `FileConverterError` messages and hints;
- validator messages;
- converter errors for malformed CSV/JSON/DOCX/ODT, unsupported conversions, missing fonts, and LibreOffice failures;
- LibreOffice dependency and timeout messages;
- log messages, for consistency;
- docstrings and code comments where present.

Keep internal format identifiers (`csv`, `json`, `docx`, `odt`, `pdf`, `txt`) unchanged.

Update tests that match Russian substrings, especially:

- `tests/test_document_converters.py` — timeout and exit-code messages;
- any tests matching validation hints or dependency errors.

## Documentation Localization

The application itself is English-only. Documentation is bilingual and selected through links.

Planned files:

| English | Polish |
|---|---|
| `README.md` | `README.pl.md` |
| `reports/test_report.md` | `reports/test_report.pl.md` |
| `test_data/README.md` | `test_data/README.pl.md` |

- English is the default.
- Add a language selector near the top of each document:

```markdown
[English](README.md) | [Polski](README.pl.md)
```

- Keep commands, file paths, version numbers, and test counts identical in both versions.
- Translate all explanatory text, tables, limitations, error descriptions, AI-usage notes, and author information.
- `PLAN.md` is the supplied assignment document and is not translated.
- Update links in `README.md` and `reports/test_report.md` so both language versions are reachable.
- `docs/ui-redesign-plan.md` is internal documentation and stays in English.

## Implementation Steps

1. Create the new two-column layout in `src/file_converter/gui/main_window.py`.
2. Remove `CTkScrollableFrame` and all scrollbar-dependent layout code.
3. Extract result rendering into the right panel with empty, success, and error states.
4. Compact the source/options area to fit the minimum window height.
5. Translate GUI strings in:
   - `src/file_converter/gui/main_window.py`
   - `src/file_converter/gui/dialogs.py`
   - `src/file_converter/gui/components.py`
6. Translate user-facing exceptions and hints in:
   - `src/file_converter/exceptions.py`
   - `src/file_converter/validators.py`
   - all converters under `src/file_converter/converters/`
   - `src/file_converter/service.py`
   - `src/file_converter/logging_config.py`
7. Translate startup and dependency messages in `app.py`.
8. Update tests for English messages and the new layout.
9. Translate `README.md`, `reports/test_report.md`, and `test_data/README.md` to English.
10. Add Polish versions and language links.
11. Run the full test suite and GUI smoke tests.
12. Commit and push each logical block.

## Verification Checklist

- [x] Application launches in English.
- [x] Window opens at `1180x720` and remains usable at `1000x620`.
- [x] No `CTkScrollableFrame` remains.
- [x] No scrollbar is visible at default or minimum size.
- [x] All source controls, status, and progress are visible at minimum size.
- [x] Result panel shows the empty state before conversion.
- [x] Result panel shows name, path, size, format, duration, and open buttons after conversion.
- [x] Long output paths do not create scrolling or clipped controls.
- [x] CSV → JSON works through the redesigned GUI.
- [x] TXT → PDF works through the redesigned GUI.
- [x] DOCX → PDF works through the redesigned GUI with LibreOffice.
- [x] ODT → DOCX works through the redesigned GUI with LibreOffice.
- [x] Overwrite dialog is fully English.
- [x] Validation and converter errors are fully English.
- [x] README has working English/Polish links.
- [x] Test report has working English/Polish links.
- [x] Test-data description has working English/Polish links.
- [x] All automated tests pass without skips.
- [x] Working tree is clean and commits are pushed.

## Commit Plan

1. `feat: redesign GUI without scrolling`
2. `feat: translate application UI to English`
3. `test: update expectations for English UI`
4. `docs: add English and Polish documentation`

## Assumptions

- The application UI remains English-only, as requested.
- The language choice applies to documentation through separate English and Polish files.
- `PLAN.md` remains in its original language because it is the source assignment.
- Native converters and LibreOffice behavior stay functionally unchanged; only layout, wording, and documentation change.
