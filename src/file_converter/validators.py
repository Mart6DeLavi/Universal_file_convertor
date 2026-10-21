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
        raise ValidationError("No source file was selected.")
    source = Path(source)
    if not source.exists():
        raise ValidationError(
            f"Source file not found: {source}",
            "Check the path and select an existing file.",
        )
    if not source.is_file():
        raise ValidationError(
            f"The path is not a regular file: {source}",
            "Select a file rather than a directory.",
        )
    extension = source.suffix.lower().lstrip(".")
    if not extension:
        raise ValidationError("The source file has no extension.")
    if extension not in SOURCE_FORMATS or extension not in supported_sources():
        raise UnsupportedConversionError(
            f"Source format .{extension} is not supported.",
            f"Available source formats: {', '.join(supported_sources()).upper()}.",
        )
    return SourceInfo.from_path(source)


def validate_target_format(source_format: str, target_format: str) -> ConverterSpec:
    target = (target_format or "").strip().lower().lstrip(".")
    if not target:
        raise ValidationError("No target format was selected.")
    if target not in TARGET_FORMATS:
        raise UnsupportedConversionError(
            f"Target format .{target} is unknown.",
            f"Available formats: {', '.join(TARGET_FORMATS).upper()}.",
        )
    spec = get_spec(source_format, target)
    if spec is None:
        raise UnsupportedConversionError(
            f"Conversion {source_format.upper()} → {target.upper()} is not supported.",
            "Choose a format from the list available for this file.",
        )
    if spec.requires_libreoffice:
        available = available_targets(source_format)
        if target not in available:
            raise DependencyMissingError(
                "This conversion requires LibreOffice, but it was not found.",
                "Install LibreOffice or set the path to soffice in UFC_SOFFICE.",
            )
    return spec


def validate_output_dir(output_dir: Path) -> Path:
    if output_dir is None or str(output_dir).strip() == "":
        raise ValidationError("No output folder was selected.")
    output_dir = Path(output_dir).expanduser()
    if not output_dir.exists():
        raise ValidationError(
            f"Output folder does not exist: {output_dir}",
            "Select an existing folder.",
        )
    if not output_dir.is_dir():
        raise ValidationError(f"The output path is not a directory: {output_dir}")
    if not directory_is_writable(output_dir):
        raise ValidationError(
            f"No write permission for the folder: {output_dir}",
            "Choose another folder or change its permissions.",
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
            f"File extension .{suffix} does not match the target format .{target_format}.",
            f"Use a name with the .{target_format} extension.",
        )
    return name, Path(output_dir) / name


def validate_request(
    request: ConversionRequest, *, check_conflict: bool = True
) -> ValidatedRequest:
    if not isinstance(request, ConversionRequest):
        raise ValidationError("Invalid conversion request.")
    source_info = validate_source(request.source)
    spec = validate_target_format(source_info.extension, request.target_format)
    output_dir = validate_output_dir(request.output_dir)
    if request.output_name is not None and not request.output_name.strip():
        raise ValidationError("The output file name cannot be empty.")
    output_name, output_path = build_output_path(
        request.source, request.target_format, output_dir, request.output_name
    )

    if output_path.exists() and same_file(output_path, request.source):
        raise ValidationError(
            "The output path is the same as the source file.",
            "Choose a different folder or name.",
        )

    if output_path.exists() and not request.overwrite and check_conflict:
        suggested = unique_path(output_path)
        raise OutputConflictError(
            output_path,
            f"The file already exists. Allow overwriting, choose another name, "
            f"or use {suggested.name}.",
        )

    return ValidatedRequest(
        request=request,
        source_info=source_info,
        spec=spec,
        output_name=output_name,
        output_path=output_path,
    )
