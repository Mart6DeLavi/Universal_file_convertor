from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

from .exceptions import ValidationError
from .utils.paths import human_size


@dataclass(frozen=True)
class SourceInfo:
    path: Path
    name: str
    extension: str
    size: int

    @property
    def size_human(self) -> str:
        return human_size(self.size)

    @classmethod
    def from_path(cls, path: Path) -> "SourceInfo":
        path = Path(path)
        try:
            stat = path.stat()
        except OSError as exc:
            raise ValidationError(
                f"Не удалось прочитать файл: {path}", "Проверьте права доступа к файлу."
            ) from exc
        return cls(
            path=path,
            name=path.name,
            extension=path.suffix.lower().lstrip("."),
            size=stat.st_size,
        )


@dataclass
class ConversionRequest:
    source: Path
    target_format: str
    output_dir: Path
    output_name: str | None = None
    overwrite: bool = False

    def __post_init__(self) -> None:
        self.source = Path(self.source).expanduser()
        self.output_dir = Path(self.output_dir).expanduser()
        self.target_format = (self.target_format or "").strip().lower().lstrip(".")
        if self.output_name is not None:
            self.output_name = self.output_name.strip()

    @property
    def source_format(self) -> str:
        return self.source.suffix.lower().lstrip(".")

    @property
    def resolved_output_name(self) -> str:
        if self.output_name:
            return self.output_name
        return f"{self.source.stem}.{self.target_format}"

    @property
    def output_path(self) -> Path:
        return self.output_dir / self.resolved_output_name


@dataclass(frozen=True)
class ConversionResult:
    request: ConversionRequest
    output_path: Path
    duration_seconds: float
    warnings: tuple[str, ...] = field(default_factory=tuple)

    @property
    def source(self) -> Path:
        return self.request.source

    @property
    def target_format(self) -> str:
        return self.request.target_format

    @property
    def output_name(self) -> str:
        return self.output_path.name

    @property
    def size(self) -> int:
        try:
            return self.output_path.stat().st_size
        except OSError:
            return 0
