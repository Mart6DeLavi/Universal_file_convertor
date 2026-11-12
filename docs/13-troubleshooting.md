# 13 — Troubleshooting

Symptom-based guide. Start with the log (`logs/converter.log`) and the startup output in the terminal.

## The app prints "Starting…" but no window appears

This is the most common complaint on macOS. The process is running, but the window may be behind other windows, minimized, on another desktop, or on another display.

Check in this order:

1. **Look at the Dock.** A Python rocket icon indicates a running process. Click it.
2. **Check the stderr line.** `app.py` prints:

   ```text
   GUI window opened. If you do not see it, check the Dock (Python icon) or another desktop space.
   ```

   If this line is missing, the window was never created; look for an error above it.
3. **Check Mission Control / Spaces.** A new Tk window opens on the active Space; switching Spaces may reveal it.
4. **Check other displays.** The window may have opened on a second monitor.
5. **Check that it is not minimized.** Use the Dock icon's window menu or `Window` menu if available.
6. **Confirm the process exists:**

   ```bash
   pgrep -fl "app.py"
   ```

7. **Bring it forward.** The app already calls `lift()`, `focus_force()`, and a 400 ms `-topmost` pulse on macOS (`_activate_window` in `app.py`). If it still hides, click the Dock icon.
8. **Do not run over SSH.** A GUI started in an SSH session appears on the Mac's physical display (if at all). Run it from Terminal.app or the IDE on the machine itself. `run.sh` warns when it detects `SSH_CONNECTION`/`SSH_TTY`.
9. **Launch through the script** to see environment checks:

   ```bash
   ./run.sh
   ```

10. **Try a direct launch** to rule out the launcher:

    ```bash
    .venv/bin/python app.py
    ```

11. **Check for a Tk problem** (see the next section). A broken Tk can create a process with no usable window.

If the process starts and exits immediately, run it in the foreground and read the traceback; `app.py` prints a hint for the most common failures.

## `ModuleNotFoundError: No module named 'customtkinter'` (or `docx`, `odf`, `reportlab`, `PIL`, `pypdf`)

The interpreter running the app does not have the dependencies.

```bash
./run.sh --install
```

or:

```bash
.venv/bin/python -m pip install -r requirements.txt
```

If you use `python app.py`, make sure `python` is the same interpreter as `.venv/bin/python`:

```bash
which python
python --version
```

## `No module named '_tkinter'` / `No module named 'tkinter'`

The Python build lacks Tk.

**macOS (Homebrew):**

```bash
brew install python-tk@3.14
```

Use the version matching your Python (`python-tk@3.13`, etc.).

**Debian/Ubuntu:** `sudo apt install python3-tk`

**Fedora:** `sudo dnf install python3-tkinter`

**Windows:** reinstall Python from python.org with the *tcl/tk and IDLE* option enabled.

Verify:

```bash
python3 -c "import tkinter; print(tkinter.TkVersion)"
```

## `error: Python 3.11 or newer is required`

`run.sh` found an older interpreter. Either set `PYTHON` explicitly:

```bash
PYTHON=/opt/homebrew/bin/python3.14 ./run.sh
```

or recreate the environment:

```bash
rm -rf .venv
./run.sh --install
```

## `./run.sh: Permission denied`

```bash
chmod +x run.sh
```

Also ensure the file uses LF line endings. If it was edited on Windows, convert it:

```bash
sed -i '' $'s/\r$//' run.sh   # macOS
```

`run.sh` requires Bash. On Windows, use Git Bash/WSL or run `python app.py` directly.

## `python: command not found`

Use `python3`, or `./run.sh`, which searches `.venv/bin/python` and `python3` automatically.

## LibreOffice directions are missing

The registry hides `DOCX → PDF`, `ODT → PDF`, `DOCX → ODT`, and `ODT → DOCX` when LibreOffice is not detected. This is intentional.

1. Verify the executable:

   ```bash
   soffice --version
   ```

2. If it works in the shell but not in the app (common with GUI-launched apps that have a minimal `PATH`), set an explicit path:

   ```bash
   export UFC_SOFFICE="/Applications/LibreOffice.app/Contents/MacOS/soffice"
   ```

   or write it to `~/.config/universal-file-converter/config.json`:

   ```json
   {"soffice_path": "/Applications/LibreOffice.app/Contents/MacOS/soffice"}
   ```

3. Restart the application. The target menu is built at source-selection time, so the direction appears after restart.

4. Linux: install `libreoffice` (not only `libreoffice-core`). Snap installations live at `/snap/bin/libreoffice` and are detected.

## LibreOffice times out or fails

Symptoms: *LibreOffice did not finish within 120 seconds*, a non-zero exit code, or *did not create the expected file*.

- Close LibreOffice windows and kill stuck processes:

  ```bash
  pkill -f soffice
  ```

- Try the conversion manually to see LibreOffice's own error:

  ```bash
  soffice --headless --convert-to pdf --outdir /tmp/out input.docx
  ```

- Check that the document opens in LibreOffice normally. Damaged files fail headless too.
- Very large or complex documents may exceed the 120-second timeout (`LIBREOFFICE_TIMEOUT` in `config.py`).
- A full disk or read-only temp directory also causes failures.
- The isolated profile (`ufc-lo-profile-*`) avoids conflicts with a running instance; do not remove it manually while a conversion runs.

## Permission denied when writing the result

- The output folder must be writable. The app tests this by creating a temporary file; a read-only folder or mounted volume is rejected before conversion.
- On macOS, access to `Desktop`, `Documents`, `Downloads`, and iCloud Drive may be protected by system privacy settings. Choose the folder through the native **Browse** dialog, which grants access; if that is not enough, grant Terminal (or your IDE) Full Disk Access in *System Settings → Privacy & Security*.
- iCloud Drive may temporarily lock files during sync. Retry when synchronization finishes.
- Do not write into the application bundle or a system directory.

## "File already exists"

This is not an error state; it is the overwrite dialog:

- **Cancel** — keep the existing file;
- **Save as `name (1).ext`** — write under the next free name;
- **Overwrite** — replace the existing file.

If you selected the source file itself as the destination, the request is rejected with *The output path is the same as the source file.* Choose another folder or name.

## `The CSV file is not valid UTF-8`

CSV and TXT inputs must be UTF-8 (a BOM is accepted). Re-save the file as UTF-8 in a text editor, or convert it first:

```bash
iconv -f ISO-8859-2 -t UTF-8 input.csv > input-utf8.csv
```

The same applies to JSON and TXT. Other encodings are not auto-detected.

## CSV parsing errors

| Message | Cause / fix |
|---|---|
| `Empty header in column N` | A header cell is blank. Fill it in. |
| `Duplicate CSV header: 'x'` | Two columns share a name. Make them unique. |
| `Row N has X fields, but there are Y headers` | Inconsistent column count. Fix quoting or add/remove separators. |
| `Could not parse the CSV file` | Broken quotes or a malformed row. |
| `The CSV file is empty` | No header row. |
| Wrong delimiter detected | Set `UFC_CSV_DELIMITER` explicitly, for example `UFC_CSV_DELIMITER=';'`. |

Supported delimiters for auto-detection: comma, semicolon, tab, pipe.

## JSON errors

| Message | Fix |
|---|---|
| `Invalid JSON: … (line L, column C)` | Repair the syntax at that position. |
| `A JSON array is expected at the top level` | Wrap objects in `[ ... ]`. |
| `Array element #N is not a JSON object` | Every element must be `{...}`; primitives and nested arrays are rejected. |
| Empty result | An empty array is valid and produces an empty CSV by design. |

## "No Unicode font was found for PDF creation"

TXT → PDF needs one of the fonts listed in [06 — Conversion pipeline](06-conversion-pipeline.md). Install one:

- macOS: Arial/Arial Unicode are normally present; if not, install Microsoft fonts or DejaVu.
- Debian/Ubuntu: `sudo apt install fonts-dejavu-core`
- Fedora: `sudo dnf install dejavu-sans-fonts`
- Windows: Arial is part of the standard fonts.

## The window is frozen

The conversion runs in a background thread, so the UI should stay responsive. If it does not:

1. Check the log for a long-running LibreOffice process.
2. Kill stuck LibreOffice processes (`pkill -f soffice`).
3. Avoid closing the app mid-conversion; confirm the close dialog if it appears.
4. Check disk space and the output folder's availability (a disconnected network volume can block I/O).

## The result looks different than expected

| Symptom | Explanation |
|---|---|
| Formatting lost after DOCX/ODT → TXT | Only text is extracted; styles, images, headers, footers are not represented in plain text. |
| DOCX → PDF layout shifts | Rendering depends on the installed LibreOffice version and available fonts. |
| Nested JSON became a JSON string in one cell | JSON → CSV does not flatten nested structures. |
| Numbers in CSV → JSON are strings | Types are not inferred. |
| PDF text is missing glyphs | The fallback font lacks the character; install Arial/DejaVu/Liberation. |
| TXT → DOCX has no styles | Each line becomes a plain paragraph by design. |

## Where to look next

- Conversion behavior: [06 — Conversion pipeline](06-conversion-pipeline.md)
- Logging format and exception meanings: [10 — Logging and errors](10-logging-and-errors.md)
- Installation requirements: [02 — Installation and launch](02-installation-and-launch.md)

## Diagnostics to collect

```bash
python3 --version
.venv/bin/python -c "import tkinter, customtkinter; print(tkinter.TkVersion, customtkinter.__version__)"
soffice --version
tail -n 50 logs/converter.log
```

Include the message and hint shown in the app, the source and target formats, and your operating system.
