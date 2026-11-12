# 05 — Project structure

This page maps the repository: what every file does and where to make a change.

## Tree

```text
FileConvertor/
├── app.py                         # entry point: sys.path, logging, MainWindow, mainloop
├── run.sh                         # launcher: selects Python, checks deps/Tk, starts app.py
├── requirements.txt               # runtime + test dependencies
├── README.md                      # English project overview
├── README.pl.md                   # Polish project overview
├── .venv/                         # local virtual environment (generated, not committed)
├── .idea/                         # IDE project files (not part of the app)
├── .gitignore                     # ignores .venv, __pycache__, logs, caches
├── docs/                          # this documentation set
│   ├── README.md                  # documentation index
│   ├── 01-overview.md
│   ├── 02-installation-and-launch.md
│   ├── 03-usage.md
│   ├── 04-architecture.md
│   ├── 05-project-structure.md
│   ├── 06-conversion-pipeline.md
│   ├── 07-core-api.md
│   ├── 08-gui-reference.md
│   ├── 09-configuration.md
│   ├── 10-logging-and-errors.md
│   ├── 11-testing.md
│   ├── 12-development-guide.md
│   ├── 13-troubleshooting.md
│   └── archive/
│       └── ui-redesign-plan.md    # historical redesign plan
├── logs/
│   ├── .gitkeep
│   └── converter.log              # active log (generated)
├── reports/
│   ├── test_report.md             # English test report
│   └── test_report.pl.md          # Polish test report
├── src/
│   └── file_converter/            # the application package
│       ├── __init__.py            # package docstring only
│       ├── config.py              # constants, formats, user configuration
│       ├── exceptions.py          # error hierarchy
│       ├── logging_config.py      # rotating logger setup
│       ├── models.py              # dataclasses for source, request, result
│       ├── registry.py            # converter registry and target lookup
│       ├── validators.py          # input validation and path resolution
│       ├── service.py             # conversion execution and atomic output
│       ├── converters/
│       │   ├── __init__.py        # re-exports converter functions
│       │   ├── csv_json.py        # CSV → JSON, JSON → CSV
│       │   ├── text_converters.py # TXT, DOCX, ODT, PDF text conversions
│       │   ├── document_converters.py # office directions via LibreOffice
│       │   └── libreoffice.py     # executable discovery and headless run
│       ├── gui/
│       │   ├── __init__.py
│       │   ├── main_window.py     # the window, state, threading, progress
│       │   ├── components.py      # palette, SectionCard, StatusDot
│       │   ├── dialogs.py         # modal overwrite/confirm/message dialogs
│       │   └── i18n.py            # EN/PL string catalogs and translate()
│       └── utils/
│           ├── __init__.py
│           ├── paths.py           # names, unique paths, writability
│           └── platform_utils.py  # open file/folder in the OS
├── tests/
│   ├── conftest.py                # adds src/ to sys.path, shared fixtures
│   ├── test_csv_json.py           # 14 tests
│   ├── test_document_converters.py# 8 tests (4 real LibreOffice checks, skipped if absent)
│   ├── test_i18n.py               # 4 tests
│   ├── test_registry.py           # 6 tests
│   ├── test_service.py            # 10 tests
│   ├── test_text_converters.py    # 6 tests
│   └── test_validators.py         # 12 tests
└── test_data/
    ├── README.md                  # expected results for the sample files
    ├── README.pl.md
    ├── sample.csv
    ├── sample.docx
    ├── sample.json
    ├── sample.odt
    └── sample.txt
```

Generated or local-only items (`.venv/`, `__pycache__/`, `.pytest_cache/`, `.idea/`, `logs/*.log`, `*.iml`) are not part of the application logic and can be recreated or deleted.

## Entry points

| Entry point | Purpose |
|---|---|
| `app.py` | Real startup: prepares imports and logging, opens the GUI. Use it for debugging. |
| `run.sh` | Convenience launcher with environment checks, `--install`, and `--help`. |
| `python -m pytest` | Test suite. |

There is no conversion CLI.

## Module responsibilities

### `src/file_converter/config.py`

Constants and user settings:

- `APP_NAME`, `APP_VERSION`;
- `PROJECT_ROOT`, `LOG_DIR`, `LOG_FILE`, `LOG_MAX_BYTES`, `LOG_BACKUP_COUNT`;
- `CONFIG_DIR`, `CONFIG_FILE`;
- `DEFAULT_ENCODING`, `CSV_SNIFF_SAMPLE`, `LIBREOFFICE_TIMEOUT`;
- `FORMAT_LABELS`, `SOURCE_FORMATS`, `TARGET_FORMATS`, `SUPPORTED_FILETYPES`;
- `get_soffice_override`, `set_soffice_override`;
- `get_language`, `set_language`.

### `src/file_converter/models.py`

- `SourceInfo` — immutable path/name/extension/size with `size_human` and `from_path`.
- `ConversionRequest` — what to convert, where, under what name, and whether overwriting is allowed.
- `ConversionResult` — what was produced and how long it took.

### `src/file_converter/exceptions.py`

`FileConverterError` base plus `ValidationError`, `UnsupportedConversionError`, `DependencyMissingError`, `OutputConflictError`, `ExternalProcessError`, `ConversionError`. All carry a message and an optional hint.

### `src/file_converter/registry.py`

- `ConverterSpec` — direction metadata and `is_available()`.
- `REGISTRY` — dictionary keyed by `(source, target)`.
- `register_converter(...)` — decorator used to add directions.
- `get_spec`, `is_supported`, `supported_sources`, `available_targets`, `all_registered_targets`.
- `execute` — thin delegation to `service.execute` kept for compatibility.

The module registers all ten built-in directions at import time (`_register_builtin()`).

### `src/file_converter/validators.py`

- `ValidatedRequest` — request + resolved source info + spec + name + path.
- `validate_source`, `validate_target_format`, `validate_output_dir`.
- `build_output_path` — name resolution, extension checks.
- `validate_request` — full pipeline including conflict detection.

### `src/file_converter/service.py`

- `execute(request, progress=None) -> ConversionResult`.
- `ConversionService` — object wrapper around `execute`.

Owns temporary directories, result verification, atomic replacement, durations, and logging of start/success/failure.

### `src/file_converter/converters/`

- `csv_json.py` — `read_csv_records`, `csv_to_json`, `json_to_csv`.
- `text_converters.py` — `read_text_file`, `txt_to_docx`, `docx_to_txt`, `txt_to_pdf`, `odt_to_txt`.
- `document_converters.py` — `docx_to_pdf`, `odt_to_pdf`, `docx_to_odt`, `odt_to_docx`.
- `libreoffice.py` — `find_libreoffice`, `is_libreoffice_available`, `convert_with_libreoffice`.

### `src/file_converter/gui/`

- `main_window.py` — `MainWindow(ctk.CTk)`, all widgets, state, event handlers, worker thread, progress animation.
- `components.py` — color constants and reusable widgets.
- `dialogs.py` — `OverwriteDialog`, `ConfirmDialog`, `MessageDialog`, and helper functions.
- `i18n.py` — `LANGUAGES`, `_STRINGS`, `translate`, `has_translation`.

### `src/file_converter/utils/`

- `paths.py` — `human_size`, `sanitize_stem`, `validate_output_name`, `build_output_name`, `unique_path`, `directory_is_writable`, `same_file`.
- `platform_utils.py` — `open_file`, `open_folder` for macOS, Windows, Linux.

### `tests/`

Unit and integration tests, one file per module area. See [11 — Testing](11-testing.md).

### `test_data/`

Small real files for manual and automated checks. `test_data/README.md` lists expected results per file.

## Where to change what

| Task | Files |
|---|---|
| Change window size or layout | `gui/main_window.py` (`geometry`, `minsize`, `_build_*`) |
| Change colors or theme accents | `gui/components.py` |
| Change a UI label or add a string | `gui/i18n.py` |
| Change validation rules | `validators.py`, `utils/paths.py` |
| Change what is logged | `service.py`, `logging_config.py` |
| Change the overwrite flow | `gui/main_window.py` (`_start_conversion`), `gui/dialogs.py` |
| Add a conversion | `converters/*.py`, `registry.py` |
| Change LibreOffice discovery | `converters/libreoffice.py`, `config.py` |
| Change supported formats | `config.py` (`SOURCE_FORMATS`, `TARGET_FORMATS`, `FORMAT_LABELS`, `SUPPORTED_FILETYPES`) |
| Change log rotation | `config.py` (`LOG_MAX_BYTES`, `LOG_BACKUP_COUNT`) |
| Change default language | `config.py` (`get_language`) and `gui/i18n.py` (`DEFAULT_LANGUAGE`) |
| Add a config option | `config.py` plus the consumer |
| Fix startup problems | `app.py`, `run.sh` |
