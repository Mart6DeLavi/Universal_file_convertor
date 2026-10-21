from __future__ import annotations


class FileConverterError(Exception):
    def __init__(self, message: str, hint: str = "") -> None:
        super().__init__(message)
        self.message = message
        self.hint = hint

    def user_message(self) -> str:
        if self.hint:
            return f"{self.message}\n\n{hint}"
        return self.message


class ValidationError(FileConverterError):
    pass


class UnsupportedConversionError(ValidationError):
    pass


class DependencyMissingError(FileConverterError):
    pass


class OutputConflictError(ValidationError):
    def __init__(self, path, hint: str = "") -> None:
        from pathlib import Path

        path = Path(path)
        message = f"File already exists: {path}"
        if not hint:
            hint = "Allow overwriting or choose a different name or folder."
        super().__init__(message, hint)
        self.path = path


class ExternalProcessError(FileConverterError):
    def __init__(self, message: str, stderr: str = "", hint: str = "") -> None:
        super().__init__(message, hint)
        self.stderr = stderr


class ConversionError(FileConverterError):
    pass
