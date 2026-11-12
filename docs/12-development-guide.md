# 12 — Development guide

How to modify the application safely and extend it with new conversions, formats, or languages.

## Development setup

```bash
git clone <repository>
cd FileConvertor
./run.sh --install
```

Run the app:

```bash
./run.sh
```

Run tests:

```bash
.venv/bin/python -m pytest -q
```

Make `src/` importable in your IDE or scripts:

```bash
export PYTHONPATH=src
```

The package is not installed with `pip`; `app.py` and `conftest.py` add `src/` to `sys.path` themselves.

## Code conventions

- `from __future__ import annotations` at the top of every module.
- Type hints on public functions; return types are explicit.
- `pathlib.Path` for all paths, never string concatenation.
- Dataclasses for data (`SourceInfo`, `ConversionRequest`, `ConversionResult`, `ConverterSpec`, `ValidatedRequest`).
- Raise `FileConverterError` subclasses with a user-facing message and hint. Do not raise bare `Exception`.
- The core (`config`, `models`, `registry`, `validators`, `service`, `converters`, `utils`) must not import `customtkinter` or the GUI.
- GUI user-visible strings go through `translate()`; no hard-coded English/Polish text in widgets.
- Log through `logging.getLogger(__name__)` or `get_logger`; no `print` in library code (the launcher and `app.py` startup messages are the exception).
- Keep comments in English, matching the rest of the codebase.

## Adding a conversion direction

A direction needs four things: a converter function, a registration, a UI description, and a test.

### 1. Write the converter

A converter is any callable `(source: Path, target: Path) -> Path`. Put it in the most relevant module under `converters/`, or create a new module.

```python
# src/file_converter/converters/text_converters.py

def txt_to_md(source: Path, target: Path) -> Path:
    text = read_text_file(source)
    target = Path(target)
    try:
        target.write_text(text, encoding=DEFAULT_ENCODING)
    except OSError as exc:
        raise ConversionError(f"Could not write the file: {target}", str(exc)) from exc
    return target
```

Rules:

- Read the source read-only.
- Write exactly to `target`; do not create directories or rename files.
- Wrap expected I/O and parse errors in `ConversionError` (or `DependencyMissingError` for missing tools/fonts) with a hint.
- Do not validate names or conflicts; the service already did.
- Do not log success; the service does.

### 2. Export it (optional)

If other modules should import it from `file_converter.converters`, add it to `converters/__init__.py` `__all__` and imports.

### 3. Register it

In `registry._register_builtin()`:

```python
register_converter("txt", "md", "Text → Markdown")(txt_to_md)
```

or with flags:

```python
register_converter(
    "docx", "md",
    "Word → Markdown via pandoc",
    requires_libreoffice=False,
    allow_empty=False,
)(docx_to_md)
```

- `requires_libreoffice=True` hides the direction when `find_libreoffice()` returns `None`.
- `allow_empty=True` permits a zero-byte result. Use it only when an empty result is legitimate.
- Registering the same pair twice raises `RuntimeError` at import time.

### 4. Add the UI description

In `gui/i18n.py`, add both languages:

```python
"target.txt.md": "Plain text becomes a Markdown file.",
```

```python
"target.txt.md": "Tekst staje się plikiem Markdown.",
```

The key format is `target.<source>.<target>`. Without it, the GUI falls back to `target.default` ("Convert TXT → MD.").

### 5. Add a test

```python
def test_txt_to_md_keeps_unicode(tmp_path):
    source = tmp_path / "notatka.txt"
    source.write_text("Zażółć gęślą jaźń", encoding="utf-8")
    target = tmp_path / "notatka.md"

    result = txt_to_md(source, target)

    assert result == target
    assert target.read_text(encoding="utf-8") == "Zażółć gęślą jaźń"
```

Also add a registry test if the direction introduces a new dependency rule.

### 6. Document it

- Add the direction to the matrix in [`01 — Overview`](01-overview.md).
- Describe its semantics in [`06 — Conversion pipeline`](06-conversion-pipeline.md).
- Mention limitations in the README if they are user-visible.
- Add a sample file to `test_data/` if useful.

## Adding a new format

Adding a format touches several lists. Use this checklist:

1. **`config.py`**
   - add the extension to `SOURCE_FORMATS` if it can be a source;
   - add it to `TARGET_FORMATS` if it can be a target (this also controls menu order);
   - add a label to `FORMAT_LABELS`;
   - add a pattern to `SUPPORTED_FILETYPES`.
2. **`registry.py`**
   - register at least one direction for the new source and/or target;
   - implement or delegate the converter.
3. **`i18n.py`**
   - add `target.<source>.<target>` descriptions;
   - update `result.empty.directions`, which lists available groups.
4. **`tests/`**
   - add converter tests;
   - extend `test_registry.py::test_all_required_conversions_are_registered` if the format is part of the required set.
5. **Docs**
   - update the overview matrix, pipeline, and usage tables.

If the format needs an external library, add it to `requirements.txt`, check it in `run.sh` if it is essential for startup, and document the dependency.

## Adding a language

1. `gui/i18n.py`:
   - add `"de": "Deutsch"` to `LANGUAGES`;
   - add a complete `_STRINGS["de"]` catalog with exactly the same keys as `en`.
2. `config.py`:
   - extend the allowed set in `get_language` and `set_language`.
3. `gui/main_window.py`:
   - add the code to the segmented button values (`["EN", "PL", ...]`);
   - map the button value to the language code in `_on_language_change`.
4. `tests/test_i18n.py` automatically checks catalog parity for all languages in `_STRINGS`; run it.
5. Update the language switch documentation in [`08 — GUI reference`](08-gui-reference.md).

The rest of the UI rebuilds itself: `_rebuild_ui` preserves the selected source, target, folder, name, result, and error.

## Changing the UI

| Change | Where |
|---|---|
| Colors | `gui/components.py` |
| Window size / minimum size | `MainWindow.__init__` |
| Header controls | `_build_header` |
| Source panel rows | `_build_source_panel` |
| Result states | `_build_result_panel` and `_show_result_state` |
| Dialog sizes/content | `gui/dialogs.py` |
| Progress behavior | `_tick_progress`, `_set_progress_target` |
| Busy-state locking | `_set_controls_state`, `_set_busy` |

Keep the no-scroll constraint: the full workflow must remain visible at `1000×620`. Avoid adding containers that push content out of view; wrap long text instead.

## Changing core behavior

| Goal | Read first |
|---|---|
| Validation rules | `validators.py`, `utils/paths.py` |
| Atomic write / temp dirs | `service.py` |
| Errors and hints | `exceptions.py` |
| LibreOffice flags, filters, timeout | `converters/libreoffice.py`, `config.py` |
| Encoding and CSV dialect | `converters/csv_json.py` |
| PDF layout and fonts | `converters/text_converters.py` |

When touching the service, preserve these invariants:

- validate before writing anything;
- write only inside a temporary directory in the destination filesystem;
- never publish an empty file unless `allow_empty`;
- never overwrite without `request.overwrite`;
- never modify the source;
- clean up temporary files;
- keep progress monotonic in `[0, 1]`.

## Debugging

- Start with `UFC_LOG_CONSOLE=1 ./run.sh` to see log lines and startup errors in the terminal.
- Reproduce the conversion without the GUI (see [07 — Core API](07-core-api.md)).
- For LibreOffice, run the equivalent command manually:

  ```bash
  soffice --headless --convert-to pdf --outdir /tmp/out input.docx
  ```

- For windows that do not appear, see [13 — Troubleshooting](13-troubleshooting.md).
- Use `python -X dev app.py` to surface resource warnings.

## Pre-commit checklist

1. `.venv/bin/python -m pytest -q` — all tests pass (or skip only LibreOffice-dependent tests).
2. The GUI starts with `./run.sh` and the changed screen works at `1000×620`.
3. The source file is unchanged after a conversion.
4. New user-visible strings exist in both `en` and `pl`.
5. The log contains start and success entries for a conversion.
6. Documentation is updated (matrix, pipeline, usage, API).
7. No `.venv/`, `__pycache__/`, logs, or personal config files are added to Git.

## Commit style

The history uses short conventional prefixes, for example:

```text
feat: add determinate progress and bilingual interface
fix: center result panel content
docs: add English and Polish documentation
style: soften green accent and improve contrast
chore: finalize repository hygiene and track plan
```

Keep commits focused and describe the user-visible effect.
