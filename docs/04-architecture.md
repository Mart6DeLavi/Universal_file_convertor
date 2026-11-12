# 04 — Architecture

The application is a small layered desktop app. The GUI is a thin shell over a dependency-free conversion core; the only external process is LibreOffice.

## Layers

```text
┌──────────────────────────────────────────────────────────────────────┐
│ app.py                                                               │
│   adds src/ to sys.path, configures logging, creates MainWindow      │
└───────────────────────────────┬──────────────────────────────────────┘
                                │
┌───────────────────────────────▼──────────────────────────────────────┐
│ GUI  (file_converter.gui)                                             │
│   main_window  — layout, events, background thread, queue, progress   │
│   components   — SectionCard, StatusDot, palette                     │
│   dialogs      — overwrite / confirm / message (modal Toplevels)      │
│   i18n         — EN/PL string catalogs                               │
└───────────────────────────────┬──────────────────────────────────────┘
                                │ ConversionRequest
┌───────────────────────────────▼──────────────────────────────────────┐
│ Core                                                                  │
│   validators  — checks inputs, resolves paths, detects conflicts      │
│   registry    — direction table + availability filtering              │
│   service     — temp dir, converter call, result checks, atomic save  │
│   models      — SourceInfo, ConversionRequest, ConversionResult        │
│   exceptions  — error hierarchy with message + hint                   │
│   config      — constants, formats, LibreOffice path, user settings   │
│   logging_config — rotating file logger                               │
└───────────────────────────────┬──────────────────────────────────────┘
                                │ Path, Path
┌───────────────────────────────▼──────────────────────────────────────┐
│ Converters  (file_converter.converters)                               │
│   csv_json             CSV ↔ JSON                                     │
│   text_converters      TXT → DOCX, DOCX → TXT, TXT → PDF, ODT → TXT  │
│   document_converters  DOCX/ODT → PDF, DOCX ↔ ODT (wrappers)          │
│   libreoffice          discovery + headless invocation               │
└──────────────────────────────────────────────────────────────────────┘
```

Dependencies point downward only. Converters do not import the GUI; validators do not import converters; the GUI never calls a converter directly.

## Request lifecycle

1. **GUI collects input.** `MainWindow` holds the source path, selected target, output folder, and output name.
2. **Local preview.** `_update_preview` calls `validators.build_output_path` to show the resolved path and whether it already exists. Failures are shown inline, not in dialogs.
3. **Press Convert.** `_start_conversion` builds a `ConversionRequest` and calls `validators.validate_request` to catch conflicts early.
4. **Conflict resolution.** On `OutputConflictError`, `dialogs.ask_overwrite` offers overwrite, a unique name, or cancel. The request is re-validated after the choice.
5. **Background execution.** A daemon thread runs `service.execute(request, progress=…)`. The GUI immediately switches to the busy state.
6. **Validation inside the service.** `service.execute` calls `validate_request` again, so the core is safe even when used without the GUI.
7. **Conversion in a temporary folder.** A `TemporaryDirectory(prefix=".ufc-", dir=output_dir)` is created; the registered converter writes `<output_name>` inside it.
8. **Result checks.** The file must exist, be a regular file, and be non-empty (unless the direction allows an empty result, currently only JSON → CSV with an empty array).
9. **Atomic publish.** `os.replace(temp_file, output_path)` moves the file into place. A second conflict check runs right before this.
10. **Result delivery.** The worker places `("success", result)` or `("error", exc)` into a `queue.Queue`; the GUI polls it every 100 ms and updates the result panel.

```text
MainWindow ──request──▶ validators ──ValidatedRequest──▶ service
    ▲                                                      │
    │                                          temp dir + converter
    │                                                      │
    └──── queue events ◀── thread ◀── ConversionResult ◀─────┘
```

## Threading model

- Tk is not thread-safe. All widget calls happen on the main thread.
- The conversion runs in `threading.Thread(daemon=True)`.
- The worker communicates only through a `queue.Queue` with three event kinds:
  - `("progress", float)` — a clamped 0..1 progress value;
  - `("success", ConversionResult)`;
  - `("error", Exception)`.
- `_poll_queue` is scheduled with `after(100, …)` and drains the queue with `get_nowait()` until it is empty.
- Progress animation is separate: `after(30, _tick_progress)` interpolates the displayed value toward a target and adds a time-based estimate while busy:

  ```python
  estimate = 0.9 - 0.85 * math.exp(-elapsed / 0.8)
  target = max(target, estimate)
  value += (target - value) * 0.28
  ```

- Closing the window cancels the polling and animation callbacks. The worker is a daemon thread; the application will not hang on exit.

## Error model

Every expected failure is a subclass of `FileConverterError` carrying two strings:

- `message` — what happened;
- `hint` — what the user can do about it.

`user_message()` joins them. The GUI shows them in the error card and in dialogs; the service logs the traceback. Unexpected exceptions are still caught by the worker and displayed as `TypeName: message`, with details in the log.

See [10 — Logging and errors](10-logging-and-errors.md).

## Why these decisions

**Registry instead of `if/elif`.** Adding a direction is one function plus one registration call. The GUI asks the registry which targets exist, so no separate list can drift out of sync.

**Availability at runtime.** `ConverterSpec.is_available()` checks LibreOffice on every query. The menu therefore matches the machine, and the same code works with and without office support.

**Temp folder inside the output directory.** `os.replace` is atomic only on the same filesystem. Writing directly into the output folder's temporary subdirectory makes the final move atomic and avoids leaving partial files.

**Re-validation in the service.** The GUI validates for good UX; the service validates for correctness. Any future caller (tests, scripts) gets the same guarantees.

**Converters return paths, not results.** Converters only know how to transform a file. Ownership of naming, conflicts, temporary files, logging, and duration belongs to the service.

**No global state besides the registry.** The only module-level mutable state is `REGISTRY` and the cached PDF font registration. Requests are plain dataclasses.

## Startup specifics

`app.py`:

1. Computes the project root and prepends `src/` to `sys.path`.
2. Calls `configure_logging()`.
3. Imports `file_converter.gui.main_window`; a missing dependency produces a message with the `pip install` command and exit code 1.
4. Creates `MainWindow`; failure to start the GUI produces a Tk hint and exit code 1.
5. On macOS, brings the window to the front (`lift`, `focus_force`, a short `-topmost` pulse) because a Tk app started from a terminal can open behind other windows.
6. Prints a one-line status to stderr and enters `mainloop()`.

The import of `file_converter.registry` (through `validators` and the GUI) imports the converters module, which imports `python-docx`, `odfpy`, and `reportlab`. Those packages are therefore required for the application to start, even if the user only converts CSV → JSON.

## Extension points

| Goal | Where |
|---|---|
| New conversion direction | `converters/` + `registry._register_builtin` (see [12](12-development-guide.md)) |
| New source/target format | `config.py` + registry + GUI labels |
| New UI language | `gui/i18n.py` + `config.set_language` validation |
| Different logging | `logging_config.py` |
| New user setting | `config.py` helpers + consumers |
| Changed safety rules | `service.py` and `validators.py` |
