# 10 — Logging and errors

The application has one log file and one exception hierarchy. This page explains both.

## Logging

### Destination

```text
logs/converter.log
```

`logs/` sits in the project root (`config.PROJECT_ROOT / "logs"`). The directory is created on first launch.

### Format

```text
%(asctime)s | %(levelname)-8s | %(name)s | %(message)s
```

Example:

```text
2026-11-12 12:04:51 | INFO     | file_converter.service | Conversion started: source=/Users/me/report.docx target=pdf output_dir=/Users/me/out
2026-11-12 12:04:53 | INFO     | file_converter.service | Success: source=/Users/me/report.docx target=pdf output=/Users/me/out/report.pdf size=48213 duration=1.842s
```

### Rotation

- Maximum size: 1 MB (`LOG_MAX_BYTES`).
- Backups: 3 (`LOG_BACKUP_COUNT`), named `converter.log.1`, `.2`, `.3`.
- Encoding: UTF-8.
- Handler: `logging.handlers.RotatingFileHandler`.

### Logger hierarchy

| Logger | Used by |
|---|---|
| `file_converter` | root application logger configured by `configure_logging` |
| `file_converter.service` | conversion start, success, failures, progress callback errors |

`logging_config.get_logger(name)` returns `file_converter.<name>`.

Loggers do not propagate to the root logger (`propagate = False`), so third-party libraries do not pollute the file unless they log through this logger.

### What is logged

| Event | Level | Content |
|---|---|---|
| Conversion start | INFO | source path, target format, output directory |
| Conversion success | INFO | source, target, output path, size, duration |
| Conversion failure | ERROR (with traceback) | source, target, exception |
| Progress callback failure | DEBUG | traceback |

File contents and user names are not logged; only paths, formats, sizes, and durations.

A failed validation inside the service is logged through the same exception handler, so a rejected conversion normally appears in the log too.

### Console logging

```bash
UFC_LOG_CONSOLE=1 python app.py
```

adds a `StreamHandler` with the same formatter. Useful when the GUI cannot start or when you want live output during development.

### Logging failures

If the log directory or file cannot be created, `configure_logging` installs a `NullHandler` instead of raising. The application keeps working; only logging is lost.

### Startup messages

`app.py` prints two lines to `stderr`:

```text
Starting Universal File Converter with /path/to/python
GUI window opened. If you do not see it, check the Dock (Python icon) or another desktop space.
```

These are intentionally on stderr, not in the log: they concern the launch process, not conversions.

## Exception hierarchy

```text
Exception
└── FileConverterError          message, hint
    ├── ValidationError
    │   ├── UnsupportedConversionError
    │   └── OutputConflictError     path
    ├── DependencyMissingError
    ├── ExternalProcessError        stderr
    └── ConversionError
```

`FileConverterError.__init__(message, hint="")` stores both strings. `user_message()` returns `message`, a blank line, and `hint` when a hint exists.

### Classes and typical triggers

| Class | Raised when | Example message |
|---|---|---|
| `ValidationError` | Inputs, names, folders, or paths are invalid | `Output folder does not exist: /tmp/nope` |
| `UnsupportedConversionError` | The extension or direction is unknown | `Conversion DOCX → CSV is not supported.` |
| `OutputConflictError` | The destination exists and overwriting is not allowed | `File already exists: /out/report.pdf` |
| `DependencyMissingError` | A required external component is missing | `LibreOffice was not found.` / `No Unicode font was found for PDF creation.` |
| `ExternalProcessError` | LibreOffice timed out, failed, or produced no file | `LibreOffice exited with code 1.` |
| `ConversionError` | The document is invalid, unreadable, or the output is empty/failed to write | `The CSV file is not valid UTF-8.` |

### Where errors appear

1. **Inline preview** — path problems are shown under the fields in orange; no dialog.
2. **Result panel** — after a failed conversion, the error state shows `exc.message` and `exc.hint`.
3. **Dialogs** — validation failures before the start, and unexpected non-`FileConverterError` exceptions, open a message dialog with title, message, and hint.
4. **Status line** — *Invalid settings*, *Conversion failed*, *Unsupported format*, *No available target formats*.
5. **Log file** — the full traceback for anything raised during conversion.

The GUI never shows a bare traceback.

### Hints

Hints are written for end users, not developers. Examples:

| Message | Hint |
|---|---|
| `No write permission for the folder: …` | `Choose another folder or change its permissions.` |
| `This conversion requires LibreOffice, but it was not found.` | `Install LibreOffice or set the path to soffice in UFC_SOFFICE.` |
| `The CSV file is not valid UTF-8.` | `Save the file as UTF-8 and try again.` |
| `Invalid JSON: Expecting ',' delimiter (line 3, column 12).` | `Fix the JSON syntax and try again.` |
| `LibreOffice did not finish within 120 seconds.` | `Close stuck LibreOffice processes and try again.` |

### Reading an error report

A minimal report contains:

1. the message and hint from the dialog or error card;
2. the last lines of `logs/converter.log`;
3. the source format, target format, and operating system;
4. for LibreOffice problems, the output of `soffice --version`.

See [13 — Troubleshooting](13-troubleshooting.md) for symptom-based guidance.

## Debugging tips

- Run with `UFC_LOG_CONSOLE=1` to see log lines live.
- Invoke the core directly to separate GUI problems from conversion problems:

  ```python
  from pathlib import Path
  from file_converter.models import ConversionRequest
  from file_converter.service import execute

  execute(ConversionRequest(Path("input.csv"), "json", Path("out")))
  ```

- Use `configure_logging(level=logging.DEBUG)` in a script for more detail. The service logs progress-callback failures at DEBUG.
- Delete `logs/converter.log*` to start a clean log; the file is recreated automatically.
