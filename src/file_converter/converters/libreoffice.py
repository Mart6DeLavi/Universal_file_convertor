from __future__ import annotations

import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

from ..config import LIBREOFFICE_TIMEOUT, get_soffice_override
from ..exceptions import ConversionError, DependencyMissingError, ExternalProcessError

_FILTERS = {
    "pdf": "pdf:writer_pdf_Export",
    "odt": "odt:writer8",
    "docx": "docx:MS Word 2007 XML",
}

_INSTALL_HINT = (
    "Установите LibreOffice: Windows — с сайта libreoffice.org; "
    "macOS — brew install --cask libreoffice; "
    "Linux — sudo apt install libreoffice (или пакет вашего дистрибутива). "
    "Путь можно задать переменной UFC_SOFFICE или в config.json (soffice_path)."
)


def _candidates() -> list[Path]:
    candidates: list[Path] = []
    override = get_soffice_override()
    if override:
        candidates.append(Path(override).expanduser())
    for name in ("soffice", "libreoffice"):
        found = shutil.which(name)
        if found:
            candidates.append(Path(found))
    if sys.platform == "darwin":
        candidates += [
            Path("/Applications/LibreOffice.app/Contents/MacOS/soffice"),
            Path.home() / "Applications/LibreOffice.app/Contents/MacOS/soffice",
        ]
    elif os.name == "nt":
        for root in (os.environ.get("ProgramFiles", r"C:\Program Files"),
                     os.environ.get("ProgramFiles(x86)", r"C:\Program Files (x86)")):
            candidates.append(Path(root) / "LibreOffice" / "program" / "soffice.exe")
    else:
        candidates += [
            Path("/usr/bin/soffice"),
            Path("/usr/bin/libreoffice"),
            Path("/snap/bin/libreoffice"),
            Path("/usr/lib/libreoffice/program/soffice"),
        ]
    return candidates


def find_libreoffice() -> Path | None:
    for candidate in _candidates():
        if candidate.is_dir():
            for nested in (
                candidate / "Contents" / "MacOS" / "soffice",
                candidate / "program" / "soffice",
            ):
                if nested.is_file() and os.access(nested, os.X_OK):
                    return nested
            continue
        if candidate.is_file() and os.access(candidate, os.X_OK):
            return candidate
    return None


def is_libreoffice_available() -> bool:
    return find_libreoffice() is not None


def _produced_file(outdir: Path, source: Path, suffix: str) -> Path | None:
    expected = outdir / f"{source.stem}.{suffix}"
    if expected.is_file():
        return expected
    matches = sorted(p for p in outdir.iterdir() if p.is_file() and p.suffix.lower() == f".{suffix}")
    return matches[0] if matches else None


def convert_with_libreoffice(source: Path, target: Path) -> Path:
    source = Path(source)
    target = Path(target)
    suffix = target.suffix.lower().lstrip(".")
    if suffix not in _FILTERS:
        raise ConversionError(f"LibreOffice-конвертация в .{suffix} не поддерживается.")

    executable = find_libreoffice()
    if executable is None:
        raise DependencyMissingError(
            "LibreOffice не найден.",
            _INSTALL_HINT,
        )

    with tempfile.TemporaryDirectory(prefix="ufc-lo-out-") as out_tmp, \
            tempfile.TemporaryDirectory(prefix="ufc-lo-profile-") as profile_tmp:
        outdir = Path(out_tmp)
        profile = Path(profile_tmp)
        command = [
            str(executable),
            "--headless",
            "--invisible",
            "--norestore",
            "--nodefault",
            "--nolockcheck",
            f"-env:UserInstallation={profile.as_uri()}",
            "--convert-to",
            _FILTERS[suffix],
            "--outdir",
            str(outdir),
            str(source),
        ]
        try:
            result = subprocess.run(
                command,
                capture_output=True,
                text=True,
                timeout=LIBREOFFICE_TIMEOUT,
                check=False,
                shell=False,
            )
        except subprocess.TimeoutExpired as exc:
            raise ExternalProcessError(
                f"LibreOffice не завершил работу за {LIBREOFFICE_TIMEOUT} секунд.",
                stderr=(exc.stderr or "") if isinstance(exc.stderr, str) else "",
                hint="Закройте зависшие процессы LibreOffice и повторите попытку.",
            ) from exc
        except OSError as exc:
            raise ExternalProcessError(
                "Не удалось запустить LibreOffice.",
                stderr=str(exc),
                hint=_INSTALL_HINT,
            ) from exc

        if result.returncode != 0:
            details = (result.stderr or result.stdout or "").strip()
            raise ExternalProcessError(
                f"LibreOffice завершился с кодом {result.returncode}.",
                stderr=details[-2000:],
                hint="Проверьте, что документ не повреждён и LibreOffice работает.",
            )

        produced = _produced_file(outdir, source, suffix)
        if produced is None:
            details = (result.stderr or result.stdout or "").strip()
            raise ExternalProcessError(
                "LibreOffice не создал ожидаемый файл.",
                stderr=details[-2000:],
                hint="Проверьте поддержку формата и целостность исходного документа.",
            )
        if produced.stat().st_size == 0:
            raise ConversionError("LibreOffice создал пустой файл.", "Проверьте исходный документ.")
        try:
            os.replace(produced, target)
        except OSError as exc:
            try:
                shutil.copy2(produced, target)
            except OSError as copy_exc:
                raise ConversionError(
                    f"Не удалось сохранить результат: {target}", str(copy_exc)
                ) from exc
    return target
