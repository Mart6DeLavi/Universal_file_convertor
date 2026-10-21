from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from .config import SOURCE_FORMATS, TARGET_FORMATS
from .exceptions import (
    DependencyMissingError,
    OutputConflictError,
    UnsupportedConversionError,
    ValidationError,
)
from .models import ConversionRequest, SourceInfo
from .registry import ConverterSpec, available_targets, get_spec, supported_sources
from .utils.paths import (
    build_output_name,
    directory_is_writable,
    same_file,
    unique_path,
    validate_output_name,
)


@dataclass(frozen=True)
class ValidatedRequest:
    request: ConversionRequest
    source_info: SourceInfo
    spec: ConverterSpec
    output_name: str
    output_path: Path

    @property
    def conflict(self) -> bool:
        return self.output_path.exists()


def validate_source(source: Path) -> SourceInfo:
    if source is None or str(source).strip() == "":
        raise ValidationError("Не выбран исходный файл.")
    source = Path(source)
    if not source.exists():
        raise ValidationError(
            f"Исходный файл не найден: {source}",
            "Проверьте путь и выберите существующий файл.",
        )
    if not source.is_file():
        raise ValidationError(
            f"Путь не является обычным файлом: {source}",
            "Выберите файл, а не каталог.",
        )
    extension = source.suffix.lower().lstrip(".")
    if not extension:
        raise ValidationError("У исходного файла нет расширения.")
    if extension not in SOURCE_FORMATS or extension not in supported_sources():
        raise UnsupportedConversionError(
            f"Исходный формат .{extension} не поддерживается.",
            f"Доступные исходные форматы: {', '.join(supported_sources()).upper()}.",
        )
    return SourceInfo.from_path(source)


def validate_target_format(source_format: str, target_format: str) -> ConverterSpec:
    target = (target_format or "").strip().lower().lstrip(".")
    if not target:
        raise ValidationError("Целевой формат не выбран.")
    if target not in TARGET_FORMATS:
        raise UnsupportedConversionError(
            f"Целевой формат .{target} неизвестен.",
            f"Доступные форматы: {', '.join(TARGET_FORMATS).upper()}.",
        )
    spec = get_spec(source_format, target)
    if spec is None:
        raise UnsupportedConversionError(
            f"Преобразование {source_format.upper()} → {target.upper()} не поддерживается.",
            "Выберите формат из списка доступных для этого файла.",
        )
    if spec.requires_libreoffice:
        available = available_targets(source_format)
        if target not in available:
            raise DependencyMissingError(
                "Для этой конвертации требуется LibreOffice, но он не найден.",
                "Установите LibreOffice или укажите путь к soffice в переменной UFC_SOFFICE.",
            )
    return spec


def validate_output_dir(output_dir: Path) -> Path:
    if output_dir is None or str(output_dir).strip() == "":
        raise ValidationError("Каталог назначения не выбран.")
    output_dir = Path(output_dir).expanduser()
    if not output_dir.exists():
        raise ValidationError(
            f"Каталог назначения не существует: {output_dir}",
            "Выберите существующую папку.",
        )
    if not output_dir.is_dir():
        raise ValidationError(f"Путь назначения не является каталогом: {output_dir}")
    if not directory_is_writable(output_dir):
        raise ValidationError(
            f"Нет прав на запись в каталог: {output_dir}",
            "Выберите другую папку или измените права доступа.",
        )
    return output_dir


def build_output_path(
    source: Path, target_format: str, output_dir: Path, output_name: str | None
) -> tuple[str, Path]:
    name = build_output_name(source.stem, target_format, output_name)
    name = validate_output_name(name)
    suffix = Path(name).suffix.lower().lstrip(".")
    if not suffix:
        name = f"{name}.{target_format}"
        suffix = target_format
    if suffix != target_format:
        raise ValidationError(
            f"Расширение файла .{suffix} не совпадает с целевым форматом .{target_format}.",
            f"Используйте имя с расширением .{target_format}.",
        )
    return name, Path(output_dir) / name


def validate_request(
    request: ConversionRequest, *, check_conflict: bool = True
) -> ValidatedRequest:
    if not isinstance(request, ConversionRequest):
        raise ValidationError("Некорректный запрос конвертации.")
    source_info = validate_source(request.source)
    spec = validate_target_format(source_info.extension, request.target_format)
    output_dir = validate_output_dir(request.output_dir)
    if request.output_name is not None and not request.output_name.strip():
        raise ValidationError("Имя выходного файла не может быть пустым.")
    output_name, output_path = build_output_path(
        request.source, request.target_format, output_dir, request.output_name
    )

    if output_path.exists() and same_file(output_path, request.source):
        raise ValidationError(
            "Путь результата совпадает с исходным файлом.",
            "Выберите другой каталог или имя.",
        )

    if output_path.exists() and not request.overwrite and check_conflict:
        suggested = unique_path(output_path)
        raise OutputConflictError(
            output_path,
            f"Файл уже существует. Разрешите перезапись, выберите другое имя "
            f"или используйте {suggested.name}.",
        )

    return ValidatedRequest(
        request=request,
        source_info=source_info,
        spec=spec,
        output_name=output_name,
        output_path=output_path,
    )
