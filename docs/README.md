# Documentation

Project documentation for **Universal File Converter** — a local desktop application that converts CSV, JSON, TXT, DOCX, and ODT files, with PDF as a target format.

The main [`README.md`](../README.md) is the short project overview. This folder contains the detailed reference: how the application is built, where each part lives, how conversions work, and how to extend or debug it.

## Documentation index

| Document | What it answers |
|---|---|
| [01 — Overview](01-overview.md) | What the application does, supported formats, conversion matrix, guarantees, limitations |
| [02 — Installation and launch](02-installation-and-launch.md) | Requirements, dependency setup, LibreOffice, `run.sh`, manual launch |
| [03 — Usage](03-usage.md) | Step-by-step GUI workflow, overwrite dialog, language and theme, error states |
| [04 — Architecture](04-architecture.md) | Layers, request lifecycle, threading model, key design decisions |
| [05 — Project structure](05-project-structure.md) | Every folder and file, and where to change what |
| [06 — Conversion pipeline](06-conversion-pipeline.md) | Validation, execution, atomic writes, semantics of all ten directions, LibreOffice integration |
| [07 — Core API](07-core-api.md) | Public functions and classes of the `file_converter` package, with examples |
| [08 — GUI reference](08-gui-reference.md) | Window layout, widgets, states, event flow, progress animation, i18n |
| [09 — Configuration](09-configuration.md) | `config.json`, environment variables, constants, file locations |
| [10 — Logging and errors](10-logging-and-errors.md) | Log format and rotation, exception hierarchy, error messages and hints |
| [11 — Testing](11-testing.md) | How to run tests, what is covered, test data, writing new tests |
| [12 — Development guide](12-development-guide.md) | Adding a conversion, adding a format, adding a language, code conventions |
| [13 — Troubleshooting](13-troubleshooting.md) | Startup problems, missing Tk, LibreOffice issues, encoding errors, conflict dialogs |
| [Archive: UI redesign plan](archive/ui-redesign-plan.md) | Historical design plan that produced the current two-column interface |

## Reading paths

- **I just want to use the app:** [02 — Installation and launch](02-installation-and-launch.md) → [03 — Usage](03-usage.md) → [13 — Troubleshooting](13-troubleshooting.md) when something fails.
- **I need to understand the code:** [01 — Overview](01-overview.md) → [04 — Architecture](04-architecture.md) → [05 — Project structure](05-project-structure.md) → [06 — Conversion pipeline](06-conversion-pipeline.md) → [07 — Core API](07-core-api.md).
- **I need to modify or extend it:** [04 — Architecture](04-architecture.md) → [07 — Core API](07-core-api.md) → [12 — Development guide](12-development-guide.md) → [11 — Testing](11-testing.md).
- **Something is broken:** [13 — Troubleshooting](13-troubleshooting.md) → [10 — Logging and errors](10-logging-and-errors.md).

## Project at a glance

| Item | Value |
|---|---|
| Application name | Universal File Converter |
| Version | 1.0.0 (`APP_VERSION` in `src/file_converter/config.py`) |
| Entry point | `app.py` (`python app.py`), launcher: `run.sh` |
| Package | `file_converter` in `src/` |
| GUI toolkit | CustomTkinter on top of Tk |
| Source formats | CSV, JSON, TXT, DOCX, ODT |
| Target formats | CSV, JSON, TXT, DOCX, ODT, PDF |
| Conversion directions | 10 (4 require LibreOffice) |
| Log file | `logs/converter.log` |
| User configuration | `~/.config/universal-file-converter/config.json` |
| Tests | `pytest`, 60 tests in `tests/` |
| Platforms | macOS, Windows, Linux |

## Documentation conventions

- Paths are relative to the project root unless stated otherwise.
- Code references use `module.symbol` notation, for example `file_converter.service.execute`.
- "Direction" means one source → target pair, for example `DOCX → PDF`.
- Light/dark colors are written as customtkinter tuples `(light, dark)`.
