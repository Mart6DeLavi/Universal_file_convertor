# 07 — Core API

The application logic lives in the `file_converter` package under `src/`. To use it from Python, make `src/` importable:

```bash
PYTHONPATH=src python
```

or:

```python
import sys
sys.path.insert(0, "src")
```

The GUI uses exactly the same API as scripts and tests.

## Quick example

```python
from pathlib import Path

from file_converter.models import ConversionRequest
from file_converter.service import execute

request = ConversionRequest(
    source=Path("test_data/sample.csv"),
    target_format="json",
    output_dir=Path("out"),
)

result = execute(request, progress=lambda value: print(f"{value:.0%}"))
print(result.output_path, result.duration_seconds, result.size)
```

`execute` raises subclasses of `FileConverterError` on expected failures.

## `file_converter.models`

### `SourceInfo`

```python
@dataclass(frozen=True)
class SourceInfo:
    path: Path
    name: str
    extension: str
    size: int

    @property
    def size_human(self) -> str: ...
    @classmethod
    def from_path(cls, path: Path) -> SourceInfo: ...
```

- `extension` is lowercase and has no dot.
- `size_human` formats bytes as `B`, `KB`, `MB`, `GB`, `TB`.
- `from_path` raises `ValidationError` when the file cannot be read.

### `ConversionRequest`

```python
@dataclass
class ConversionRequest:
    source: Path
    target_format: str
    output_dir: Path
    output_name: str | None = None
    overwrite: bool = False

    @property
    def source_format(self) -> str: ...
    @property
    def resolved_output_name(self) -> str: ...
    @property
    def output_path(self) -> Path: ...
```

Normalization in `__post_init__`: `source` and `output_dir` become `Path` with `~` expanded; `target_format` is stripped, lowercased, and loses a leading dot; `output_name` is stripped.

`resolved_output_name` is the explicit name or `<source stem>.<target_format>`; it does not sanitize the stem (validation does that).

### `ConversionResult`

```python
@dataclass(frozen=True)
class ConversionResult:
    request: ConversionRequest
    output_path: Path
    duration_seconds: float
    warnings: tuple[str, ...] = ()

    @property
    def source(self) -> Path: ...
    @property
    def target_format(self) -> str: ...
    @property
    def output_name(self) -> str: ...
    @property
    def size(self) -> int: ...
```

`size` returns the current file size and `0` if the file cannot be read.

## `file_converter.registry`

```python
Converter = Callable[[Path, Path], Path]

@dataclass(frozen=True)
class ConverterSpec:
    source_format: str
    target_format: str
    converter: Converter
    description: str
    requires_libreoffice: bool = False
    allow_empty: bool = False

    def is_available(self) -> bool: ...
```

| Function | Behavior |
|---|---|
| `register_converter(source, target, description, *, requires_libreoffice=False, allow_empty=False)` | Returns a decorator that registers a converter function. Duplicate direction raises `RuntimeError`. |
| `get_spec(source, target) -> ConverterSpec \| None` | Looks up a direction after normalization. |
| `is_supported(source, target) -> bool` | Whether a direction is registered (does not check dependencies). |
| `supported_sources() -> list[str]` | Sorted source formats present in the registry. |
| `available_targets(source) -> list[str]` | Targets for a format or `Path`, filtered by `spec.is_available()`, ordered as `TARGET_FORMATS`. |
| `all_registered_targets(source) -> list[str]` | Registered targets regardless of dependencies. |
| `execute(request, progress=None)` | Delegates to `service.execute` (kept for convenience). |

Example of adding a direction:

```python
from pathlib import Path
from file_converter.registry import register_converter
from file_converter.exceptions import ConversionError


@register_converter("txt", "md", "Plain text → Markdown", allow_empty=True)
def txt_to_md(source: Path, target: Path) -> Path:
    text = Path(source).read_text(encoding="utf-8-sig")
    Path(target).write_text(text, encoding="utf-8")
    return Path(target)
```

Registering after the GUI has imported the registry still works, but the built-in registration normally happens at import time.

## `file_converter.validators`

```python
@dataclass(frozen=True)
class ValidatedRequest:
    request: ConversionRequest
    source_info: SourceInfo
    spec: ConverterSpec
    output_name: str
    output_path: Path

    @property
    def conflict(self) -> bool: ...
```

| Function | Returns | Raises |
|---|---|---|
| `validate_source(source: Path) -> SourceInfo` | source metadata | `ValidationError`, `UnsupportedConversionError` |
| `validate_target_format(source_format, target_format) -> ConverterSpec` | registry spec | `ValidationError`, `UnsupportedConversionError`, `DependencyMissingError` |
| `validate_output_dir(output_dir: Path) -> Path` | the directory | `ValidationError` |
| `build_output_path(source, target_format, output_dir, output_name) -> tuple[str, Path]` | name, full path | `ValidationError` |
| `validate_request(request, *, check_conflict=True) -> ValidatedRequest` | everything resolved | any of the above, `OutputConflictError` |

`check_conflict=False` is useful for previewing a path without caring whether it exists.

## `file_converter.service`

```python
ProgressCallback = Callable[[float], None]

def execute(
    request: ConversionRequest,
    progress: ProgressCallback | None = None,
) -> ConversionResult: ...
```

Behavior:

- validates the request;
- refuses an existing target unless `request.overwrite` is true;
- converts inside a temporary directory in the output folder;
- verifies existence, type, and size of the result;
- publishes atomically with `os.replace`;
- reports monotonic progress in `[0, 1]`; exceptions raised by the callback are logged at debug level and ignored;
- logs start, failure, and success;
- returns a `ConversionResult`.

```python
class ConversionService:
    def execute(self, request, progress=None) -> ConversionResult: ...
```

A stateless object wrapper, convenient for dependency injection.

## `file_converter.exceptions`

```python
class FileConverterError(Exception):
    message: str
    hint: str
    def user_message(self) -> str: ...

class ValidationError(FileConverterError): ...
class UnsupportedConversionError(ValidationError): ...
class DependencyMissingError(FileConverterError): ...
class OutputConflictError(ValidationError):
    path: Path
    def __init__(self, path, hint: str = "") -> None: ...
class ExternalProcessError(FileConverterError):
    stderr: str
    def __init__(self, message: str, stderr: str = "", hint: str = "") -> None: ...
class ConversionError(FileConverterError): ...
```

`OutputConflictError.path` is the conflicting destination. Its default hint suggests overwriting or choosing another name.

## `file_converter.config`

Constants:

| Name | Value |
|---|---|
| `APP_NAME` | `"Universal File Converter"` |
| `APP_VERSION` | `"1.0.0"` |
| `PROJECT_ROOT` | repository root (two levels above `src/file_converter`) |
| `LOG_DIR`, `LOG_FILE` | `<root>/logs`, `<root>/logs/converter.log` |
| `LOG_MAX_BYTES` | `1_000_000` |
| `LOG_BACKUP_COUNT` | `3` |
| `CONFIG_DIR`, `CONFIG_FILE` | `~/.config/universal-file-converter`, `.../config.json` |
| `DEFAULT_ENCODING` | `"utf-8"` |
| `CSV_SNIFF_SAMPLE` | `8192` |
| `LIBREOFFICE_TIMEOUT` | `120` |
| `SOURCE_FORMATS` | `("csv", "json", "txt", "docx", "odt")` |
| `TARGET_FORMATS` | `("csv", "json", "txt", "docx", "odt", "pdf")` |
| `FORMAT_LABELS` | mapping for the GUI (`csv → CSV`, …) |
| `SUPPORTED_FILETYPES` | Tk file-dialog patterns |

Settings functions:

| Function | Behavior |
|---|---|
| `get_soffice_override() -> str \| None` | `UFC_SOFFICE` → `LIBREOFFICE_PATH` → `config.json:soffice_path` |
| `set_soffice_override(path)` | Writes/clears `soffice_path`; creates the config directory |
| `get_language() -> str` | `"en"` or `"pl"`, default `"en"` for invalid/missing values |
| `set_language(language)` | Persists `en`/`pl`; ignores other values |

All config reads tolerate a missing or malformed file and return defaults.

## `file_converter.logging_config`

```python
def configure_logging(log_file: Path | None = None, level: int = logging.INFO) -> logging.Logger: ...
def get_logger(name: str) -> logging.Logger: ...
```

- Logger name: `file_converter`; `get_logger("service")` returns `file_converter.service`.
- Adds a `RotatingFileHandler` (1 MB, 3 backups, UTF-8) once; subsequent calls are no-ops.
- On `OSError` (unwritable directory) falls back to `NullHandler`.
- Adds a console handler only when `UFC_LOG_CONSOLE=1`.
- `propagate = False`.

## `file_converter.converters`

Public functions (also re-exported from `converters/__init__.py`):

| Function | Direction |
|---|---|
| `read_csv_records(source, delimiter=None) -> (headers, records)` | CSV parsing used by CSV → JSON |
| `csv_to_json(source, target, delimiter=None) -> Path` | CSV → JSON |
| `json_to_csv(source, target) -> Path` | JSON → CSV |
| `txt_to_docx(source, target) -> Path` | TXT → DOCX |
| `docx_to_txt(source, target) -> Path` | DOCX → TXT |
| `txt_to_pdf(source, target) -> Path` | TXT → PDF |
| `odt_to_txt(source, target) -> Path` | ODT → TXT |
| `docx_to_pdf(source, target) -> Path` | DOCX → PDF |
| `odt_to_pdf(source, target) -> Path` | ODT → PDF |
| `docx_to_odt(source, target) -> Path` | DOCX → ODT |
| `odt_to_docx(source, target) -> Path` | ODT → DOCX |
| `find_libreoffice() -> Path \| None` | Discovery |
| `is_libreoffice_available() -> bool` | Discovery convenience |
| `convert_with_libreoffice(source, target) -> Path` | Generic headless conversion |

Converters write to the exact `target` path they receive (or, for LibreOffice, to a temp output that is then moved) and return that path. They do not validate user-facing rules, create directories, or decide names.

## `file_converter.utils`

### `paths`

| Function | Behavior |
|---|---|
| `human_size(size: int) -> str` | `1.5 MB`, `512 B` |
| `sanitize_stem(stem: str) -> str` | Replaces invalid characters, avoids reserved names |
| `validate_output_name(name: str) -> str` | Raises `ValidationError` for invalid names |
| `build_output_name(source_stem, target_format, name=None) -> str` | Explicit or generated name |
| `unique_path(path: Path) -> Path` | First free `name (N).ext` |
| `directory_is_writable(directory: Path) -> bool` | Probes with a temporary file |
| `same_file(first, second) -> bool` | `os.path.samefile` with a `resolve()` fallback |

### `platform_utils`

| Function | Behavior |
|---|---|
| `open_file(path)` | `open` (macOS), `os.startfile` (Windows), `xdg-open` (Linux) |
| `open_folder(path)` | Same, for directories |

Both launch detached processes with output discarded and raise `FileConverterError` when the target does not exist or cannot be opened.

## `file_converter.gui.i18n`

```python
LANGUAGES = {"en": "English", "pl": "Polski"}
DEFAULT_LANGUAGE = "en"

def translate(language: str, key: str, **values) -> str: ...
def has_translation(language: str, key: str) -> bool: ...
```

`translate` falls back to English, then to the key itself. Formatting errors return the unformatted template. See [08 — GUI reference](08-gui-reference.md) for the key naming scheme.

## Error-handling example

```python
from file_converter.exceptions import FileConverterError, OutputConflictError
from file_converter.models import ConversionRequest
from file_converter.service import execute

request = ConversionRequest(
    source=Path("report.docx"),
    target_format="pdf",
    output_dir=Path("out"),
)

try:
    result = execute(request)
except OutputConflictError as exc:
    print(exc.message, "->", exc.path)
    request.output_name = f"{request.source.stem} (1).pdf"
    result = execute(request)
except FileConverterError as exc:
    print(exc.user_message())
else:
    print("written:", result.output_path)
```
