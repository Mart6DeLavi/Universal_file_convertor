# 02 — Installation and launch

This page describes how to prepare the environment and start the application on macOS, Windows, and Linux.

## Requirements

| Requirement | Details |
|---|---|
| Python | 3.11 or newer. The project was verified on Python 3.14.8. |
| Tk | Tk 8.6+ and a Python build with `_tkinter` support (CustomTkinter depends on it). |
| OS | macOS, Windows, or Linux with a graphical session. |
| LibreOffice | Optional. Needed only for `DOCX → PDF`, `ODT → PDF`, `DOCX → ODT`, and `ODT → DOCX`. |
| Disk | A writable output folder (the app also writes `logs/` and `~/.config/universal-file-converter/`). |

Python packages are listed in [`requirements.txt`](../requirements.txt):

```text
customtkinter>=5.2
python-docx>=1.1
odfpy>=1.4
reportlab>=4.0
Pillow>=10.0
pytest>=8.0
pypdf>=4.0
```

`pytest` and `pypdf` are needed for the test suite; the application itself imports CustomTkinter, python-docx, odfpy, ReportLab, and (indirectly) Pillow.

## Install once (recommended)

From the project root:

```bash
./run.sh --install
```

The launcher creates `.venv` with `python3 -m venv` if it does not exist, upgrades `pip`, installs `requirements.txt`, and then starts the application.

Equivalent manual steps:

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

## Launch

### With the launcher (all platforms with Bash)

```bash
./run.sh            # start the GUI
./run.sh --install  # create .venv if needed, install requirements, then start
./run.sh --help     # print usage
```

`run.sh` works from any current directory: it resolves its own location, then changes to the project root. It also:

1. Picks the interpreter in this order: `$PYTHON` if set → `.venv/bin/python` → `python3` from `PATH`.
2. Checks Python is at least 3.11.
3. Checks that `customtkinter`, `docx`, `odf`, `reportlab`, `PIL`, and `pypdf` are importable; missing packages produce a message with the fix command.
4. Checks that `tkinter` imports; otherwise it prints platform-specific Tk installation hints.
5. Warns if an SSH session is detected (the window appears on the Mac's own screen, not in the terminal).
6. Prints the interpreter path and starts `app.py`, forwarding any extra arguments, using `exec` so the exit code belongs to the GUI process.

Possible outputs:

| Message | Meaning |
|---|---|
| `Starting Universal File Converter with …` | The interpreter was found and all checks passed. |
| `GUI window opened. If you do not see it, check the Dock …` | `app.py` created the main window. |
| `error: missing Python packages: …` | Run `./run.sh --install`. |
| `error: this Python has no Tk support …` | Install Tk for the interpreter in use. |
| `error: Python 3.11 or newer is required …` | Point `PYTHON` to a newer interpreter or recreate `.venv`. |

### Manual launch

```bash
python app.py
```

or, without activating the virtual environment:

```bash
.venv/bin/python app.py
```

To also send the log to the console:

```bash
UFC_LOG_CONSOLE=1 python app.py
```

`app.py` adds `src/` to `sys.path`, configures logging, imports the GUI, and opens the window. It performs no conversion by itself.

## Tk support

CustomTkinter needs a Python built with Tk support. If `import tkinter` fails or the window cannot be created:

**macOS (Homebrew Python):**

```bash
brew install python-tk@3.14   # match the installed Python version
```

**Debian/Ubuntu:**

```bash
sudo apt install python3-tk
```

**Fedora:**

```bash
sudo dnf install python3-tkinter
```

**Windows:** the official python.org installer includes Tk by default; the Microsoft Store build also works.

## LibreOffice (optional)

LibreOffice is used in headless mode for the four office conversions. Without it the application still works and simply hides those directions.

### Install

**macOS:**

```bash
brew install --cask libreoffice
```

Or download the installer from [libreoffice.org](https://www.libreoffice.org/download/) and drag LibreOffice into `/Applications`.

**Windows:** install from [libreoffice.org](https://www.libreoffice.org/download/). The executable is usually:

```text
C:\Program Files\LibreOffice\program\soffice.exe
```

**Debian/Ubuntu:**

```bash
sudo apt update
sudo apt install libreoffice
```

**Fedora:** `sudo dnf install libreoffice`

**Arch Linux:** `sudo pacman -S libreoffice-fresh`

### Verify

```bash
soffice --version
```

On macOS you can check the bundle directly:

```bash
/Applications/LibreOffice.app/Contents/MacOS/soffice --headless --version
```

### Point the application at a custom path

The application searches for `soffice` in this order:

1. `UFC_SOFFICE` environment variable.
2. `LIBREOFFICE_PATH` environment variable.
3. `soffice_path` in `~/.config/universal-file-converter/config.json`.
4. `soffice` and `libreoffice` on `PATH`.
5. Standard installation directories for macOS, Windows, and Linux.

Example:

```bash
export UFC_SOFFICE="/Applications/LibreOffice.app/Contents/MacOS/soffice"
```

```json
{
  "soffice_path": "/Applications/LibreOffice.app/Contents/MacOS/soffice"
}
```

See [09 — Configuration](09-configuration.md) for the full configuration reference.

## First launch checklist

1. `./run.sh --install` completes without errors.
2. The window opens and shows **Universal File Converter** and version `1.0.0`.
3. Selecting `test_data/sample.csv` offers **JSON** as the only target.
4. Selecting `test_data/sample.docx` offers **TXT**, **ODT**, and **PDF**; without LibreOffice, only **TXT** appears.
5. Converting `sample.csv` to JSON creates a file in the chosen folder and the success card shows its path.

If step 2 fails, see [13 — Troubleshooting](13-troubleshooting.md).

## Uninstall / reset

- Delete the virtual environment: `rm -rf .venv`.
- Delete user settings: `rm -rf ~/.config/universal-file-converter`.
- Delete logs: `rm -rf logs/converter.log*`.
- Uninstall LibreOffice with the platform package manager if it is no longer needed.
