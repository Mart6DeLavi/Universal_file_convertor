from __future__ import annotations

import logging
import os
import tempfile
import time
from pathlib import Path

from .exceptions import ConversionError, OutputConflictError
from .models import ConversionRequest, ConversionResult
from .validators import validate_request

logger = logging.getLogger(__name__)


def _log_start(request: ConversionRequest) -> float:
    logger.info(
        "Conversion started: source=%s target=%s output_dir=%s",
        request.source,
        request.target_format,
        request.output_dir,
    )
    return time.monotonic()


def execute(request: ConversionRequest) -> ConversionResult:
    started = _log_start(request)
    validated = validate_request(request)
    spec = validated.spec
    output_path = validated.output_path
    output_name = validated.output_name

    if output_path.exists() and not request.overwrite:
        raise OutputConflictError(output_path)

    target_dir = validated.request.output_dir
    try:
        with tempfile.TemporaryDirectory(prefix=".ufc-", dir=target_dir) as tmp:
            temp_output = Path(tmp) / output_name
            spec.converter(validated.request.source, temp_output)

            if not temp_output.exists() or not temp_output.is_file():
                raise ConversionError(
                    "The converter did not create an output file.",
                    f"Expected file: {output_name}",
                )
            size = temp_output.stat().st_size
            if size == 0 and not spec.allow_empty:
                raise ConversionError(
                    "The converter created an empty file.",
                    "Check the source document and try again.",
                )

            if output_path.exists() and not request.overwrite:
                raise OutputConflictError(output_path)

            try:
                os.replace(temp_output, output_path)
            except OSError as exc:
                raise ConversionError(
                    f"Could not save the result: {output_path}", str(exc)
                ) from exc
    except Exception:
        logger.exception(
            "Conversion error: source=%s target=%s",
            request.source,
            request.target_format,
        )
        raise

    duration = time.monotonic() - started
    try:
        result_size = output_path.stat().st_size
    except OSError:
        result_size = 0
    logger.info(
        "Success: source=%s target=%s output=%s size=%s duration=%.3fs",
        request.source,
        request.target_format,
        output_path,
        result_size,
        duration,
    )
    return ConversionResult(
        request=request,
        output_path=output_path,
        duration_seconds=duration,
    )


class ConversionService:
    def execute(self, request: ConversionRequest) -> ConversionResult:
        return execute(request)
