# 09 — Configuration

The application has deliberately little configuration: one JSON file for user preferences and a small set of environment variables for development and troubleshooting.

## Configuration file

Location:

```text
~/.config/universal-file-converter/config.json
```

On Windows, `Path.home()` points to the user profile, so the file is:

```text
C:\Users\<name>\.config\universal-file-converter\config.json
```

The file is optional. A missing, unreadable, or malformed file is treated as empty; the application falls back to defaults and does not crash.

### Schema

```json
{
  "soffice_path": "/Applications/LibreOffice.app/Contents/MacOS/soffice",
  "language": "pl"
}
```

| Key | Type | Values | Default |
|---|---|---|---|
| `soffice_path` | string | Path to the LibreOffice executable (or its `.app` directory on macOS) | none — auto-discovery |
| `language` | string | `"en"` or `"pl"` | `"en"` |

Unknown keys are preserved when the application writes the file.

### Reading and writing

| Function | Effect |
|---|---|
| `config.get_soffice_override()` | Returns the first non-empty value from `UFC_SOFFICE`, `LIBREOFFICE_PATH`, `config.json:soffice_path` |
| `config.set_soffice_override(path)` | Creates the config directory and writes/removes `soffice_path` |
| `config.get_language()` | Returns `en`/`pl`; any other stored value becomes `en` |
| `config.set_language(code)` | Ignores codes other than `en`/`pl`; creates the directory and writes the key |

The GUI writes `language` when the user switches languages. There is no GUI for `soffice_path`; edit the file or use an environment variable.

### Reset

```bash
rm -rf ~/.config/universal-file-converter
```

The next launch starts with English and automatic LibreOffice discovery.

## Environment variables

| Variable | Values | Effect |
|---|---|---|
| `UFC_SOFFICE` | path | Highest-priority LibreOffice executable override |
| `LIBREOFFICE_PATH` | path | Second-priority override; useful for tools that already set it |
| `UFC_CSV_DELIMITER` | one character | Forces the CSV delimiter instead of auto-detection. Use a literal tab or the two characters `\t`. Any other length raises a conversion error. |
| `UFC_LOG_CONSOLE` | `1` | Adds a console log handler in addition to the file handler |
| `PYTHON` | path | Read by `run.sh` to choose the interpreter |

Examples:

```bash
UFC_SOFFICE=/opt/homebrew/bin/soffice ./run.sh
UFC_CSV_DELIMITER=';' python app.py
UFC_LOG_CONSOLE=1 ./run.sh
PYTHON=/opt/homebrew/bin/python3.14 ./run.sh
```

`UFC_CSV_DELIMITER` accepts one character. The sequence `\t` is converted to a tab. It applies to CSV → JSON only; JSON → CSV always writes commas.

## Constants

Defined in `src/file_converter/config.py`:

| Constant | Value | Meaning |
|---|---|---|
| `APP_NAME` | `Universal File Converter` | Window title and header |
| `APP_VERSION` | `1.0.0` | Shown in the header |
| `PROJECT_ROOT` | two parents above `src/file_converter` | Repository root |
| `LOG_DIR` | `<root>/logs` | Log directory |
| `LOG_FILE` | `<root>/logs/converter.log` | Active log |
| `LOG_MAX_BYTES` | `1_000_000` | Rotation threshold (1 MB) |
| `LOG_BACKUP_COUNT` | `3` | Number of rotated files |
| `CONFIG_DIR` | `~/.config/universal-file-converter` | User configuration |
| `CONFIG_FILE` | `<config dir>/config.json` | Settings file |
| `DEFAULT_ENCODING` | `utf-8` | Output encoding for text formats |
| `CSV_SNIFF_SAMPLE` | `8192` | Bytes used for delimiter detection |
| `LIBREOFFICE_TIMEOUT` | `120` | Seconds before a headless conversion is killed |
| `SOURCE_FORMATS` | `csv, json, txt, docx, odt` | Accepted source extensions |
| `TARGET_FORMATS` | `csv, json, txt, docx, odt, pdf` | Known target extensions and menu order |
| `FORMAT_LABELS` | `csv → CSV`, … | UI display labels |
| `SUPPORTED_FILETYPES` | Tk patterns | File-dialog filters |

To change rotation, timeout, or supported formats, edit these constants; they are read at import time, so restart the application afterwards.

## File locations used at runtime

| Purpose | Location | Notes |
|---|---|---|
| Application log | `logs/converter.log` | Created on first launch; rotated at 1 MB |
| Old logs | `logs/converter.log.1` … `.3` | Kept by `RotatingFileHandler` |
| User settings | `~/.config/universal-file-converter/config.json` | Language, optional soffice path |
| Temporary conversion dirs | `<output folder>/.ufc-*` | Deleted automatically |
| LibreOffice temp output | system temp `ufc-lo-out-*` | Deleted automatically |
| LibreOffice temp profile | system temp `ufc-lo-profile-*` | Isolated profile, deleted automatically |
| Test samples | `test_data/` | Committed example files |
| Test reports | `reports/` | Static reports |

The application does not write into the source file's folder unless that folder is also the chosen output folder.

## Logging configuration

Logging is configured in `app.py` through `logging_config.configure_logging()`. It cannot be changed from the GUI.

- File handler: rotating, UTF-8, format `%(asctime)s | %(levelname)-8s | %(name)s | %(message)s`.
- Console handler: only with `UFC_LOG_CONSOLE=1`.
- Level: `INFO`.
- If the log directory is not writable, a `NullHandler` is used and the application continues.

See [10 — Logging and errors](10-logging-and-errors.md).

## What is not configurable

| Setting | Why |
|---|---|
| Theme | Session-only; starts dark every launch |
| Default output folder | Taken from the source file; the user can override per session |
| Overwrite policy | Always asks; never silent |
| Window size | Fixed default `1180×720`, minimum `1000×620` |
| PDF font | Fixed candidate list, first existing font wins |
| CSV encoding | UTF-8 (BOM allowed) by design |
| Batch mode | Not implemented |
