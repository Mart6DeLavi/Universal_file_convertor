from __future__ import annotations

import queue
import threading
from pathlib import Path
from tkinter import filedialog

import customtkinter as ctk

from ..config import (
    APP_NAME,
    APP_VERSION,
    FORMAT_LABELS,
    SUPPORTED_FILETYPES,
)
from ..exceptions import FileConverterError, OutputConflictError
from ..models import ConversionRequest, SourceInfo
from ..registry import available_targets
from ..service import execute as execute_conversion
from ..utils.paths import build_output_name, unique_path
from ..utils.platform_utils import open_file, open_folder
from ..validators import build_output_path, validate_request, validate_source
from .components import ACCENT, MUTED, SectionCard, StatusDot
from .dialogs import ask_confirm, ask_overwrite, show_message


class MainWindow(ctk.CTk):
    def __init__(self) -> None:
        super().__init__()
        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("blue")

        self._source_info: SourceInfo | None = None
        self._targets: list[str] = []
        self._target_labels: dict[str, str] = {}
        self._busy = False
        self._closing = False
        self._name_edited = False
        self._output_dir_user_set = False
        self._last_auto_name = ""
        self._queue: queue.Queue = queue.Queue()
        self._thread: threading.Thread | None = None
        self._last_result_path: Path | None = None

        self.title(APP_NAME)
        self.geometry("1040x860")
        self.minsize(820, 680)
        self.configure(fg_color=("#eef0f5", "#0f0f12"))

        self._build_layout()
        self._set_status("Ожидание: выберите исходный файл", "idle")
        self._update_preview()
        self.after(100, self._poll_queue)
        self.protocol("WM_DELETE_WINDOW", self._on_close)

    def _build_layout(self) -> None:
        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(0, weight=1)

        self.content = ctk.CTkScrollableFrame(self, fg_color="transparent", corner_radius=0)
        self.content.grid(row=0, column=0, sticky="nsew")
        self.content.grid_columnconfigure(0, weight=1)

        self._build_header()
        self._build_source_card()
        self._build_settings_card()
        self._build_action_card()
        self._build_result_card()

    def _build_header(self) -> None:
        header = ctk.CTkFrame(self.content, fg_color="transparent")
        header.grid(row=0, column=0, sticky="ew", padx=24, pady=(24, 16))
        header.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(
            header,
            text=APP_NAME,
            font=ctk.CTkFont(size=30, weight="bold"),
            anchor="w",
        ).grid(row=0, column=0, sticky="w")
        ctk.CTkLabel(
            header,
            text=(
                f"Локальный конвертер файлов без загрузки в интернет · версия {APP_VERSION}"
            ),
            font=ctk.CTkFont(size=13),
            text_color=MUTED,
            anchor="w",
        ).grid(row=1, column=0, sticky="w", pady=(4, 0))

        self.theme_switch = ctk.CTkSwitch(
            header, text="Светлая тема", command=self._toggle_theme
        )
        self.theme_switch.grid(row=0, column=1, rowspan=2, sticky="e")

    def _build_source_card(self) -> None:
        card = SectionCard(
            self.content,
            "1. Исходный файл",
            "Выберите файл — доступные форматы определятся автоматически",
        )
        card.grid(row=1, column=0, sticky="ew", padx=24, pady=(0, 14))
        body = card.body

        body.grid_columnconfigure(1, weight=1)
        ctk.CTkLabel(body, text="Путь", anchor="w").grid(row=0, column=0, sticky="w", padx=(0, 12))

        self.source_path_var = ctk.StringVar(value="")
        self.source_path_entry = ctk.CTkEntry(
            body, textvariable=self.source_path_var, state="readonly", height=36
        )
        self.source_path_entry.grid(row=0, column=1, sticky="ew")
        self.browse_button = ctk.CTkButton(
            body, text="Выбрать файл", width=130, command=self._browse_source
        )
        self.browse_button.grid(row=0, column=2, sticky="e", padx=(12, 0))

        info = ctk.CTkFrame(body, fg_color="transparent")
        info.grid(row=1, column=1, columnspan=2, sticky="ew", pady=(14, 0))
        info.grid_columnconfigure((0, 1, 2), weight=1)

        self.source_name_label = self._info_tile(info, 0, "Имя файла", "—")
        self.source_format_label = self._info_tile(info, 1, "Формат", "—")
        self.source_size_label = self._info_tile(info, 2, "Размер", "—")

    def _info_tile(self, parent, column: int, caption: str, value: str) -> ctk.CTkLabel:
        frame = ctk.CTkFrame(parent, fg_color=("#f5f6fa", "#17171b"), corner_radius=10)
        frame.grid(row=0, column=column, sticky="ew", padx=(0 if column == 0 else 8, 0))
        frame.grid_columnconfigure(0, weight=1)
        ctk.CTkLabel(
            frame, text=caption, font=ctk.CTkFont(size=11), text_color=MUTED, anchor="w"
        ).grid(row=0, column=0, sticky="w", padx=12, pady=(8, 0))
        label = ctk.CTkLabel(
            frame, text=value, font=ctk.CTkFont(size=13, weight="bold"), anchor="w"
        )
        label.grid(row=1, column=0, sticky="ew", padx=12, pady=(0, 9))
        return label

    def _build_settings_card(self) -> None:
        card = SectionCard(
            self.content,
            "2. Параметры результата",
            "Форматы ограничены реально зарегистрированными конвертерами",
        )
        card.grid(row=2, column=0, sticky="ew", padx=24, pady=(0, 14))
        body = card.body
        body.grid_columnconfigure(1, weight=1)

        ctk.CTkLabel(body, text="Целевой формат", anchor="w").grid(
            row=0, column=0, sticky="w", padx=(0, 12)
        )
        self.target_var = ctk.StringVar(value="—")
        self.target_menu = ctk.CTkOptionMenu(
            body,
            values=["—"],
            variable=self.target_var,
            command=self._on_target_change,
            width=150,
        )
        self.target_menu.grid(row=0, column=1, sticky="w")
        self.target_hint = ctk.CTkLabel(
            body,
            text="Сначала выберите исходный файл",
            text_color=MUTED,
            font=ctk.CTkFont(size=11),
            anchor="w",
            justify="left",
            wraplength=680,
        )
        self.target_hint.grid(row=1, column=1, sticky="ew", pady=(6, 10))

        ctk.CTkLabel(body, text="Папка назначения", anchor="w").grid(
            row=2, column=0, sticky="w", padx=(0, 12)
        )
        self.output_dir_var = ctk.StringVar(value="")
        self.output_dir_entry = ctk.CTkEntry(body, textvariable=self.output_dir_var, height=36)
        self.output_dir_entry.grid(row=2, column=1, sticky="ew")
        self.output_dir_entry.bind("<KeyRelease>", self._on_dir_typed)
        self.output_dir_button = ctk.CTkButton(
            body, text="Выбрать папку", width=130, command=self._browse_output_dir
        )
        self.output_dir_button.grid(row=2, column=2, sticky="e", padx=(12, 0))

        ctk.CTkLabel(body, text="Имя результата", anchor="w").grid(
            row=3, column=0, sticky="w", padx=(0, 12), pady=(12, 0)
        )
        self.name_var = ctk.StringVar(value="")
        self.name_entry = ctk.CTkEntry(body, textvariable=self.name_var, height=36)
        self.name_entry.grid(row=3, column=1, sticky="ew", pady=(12, 0))
        self.name_entry.bind("<KeyRelease>", self._on_name_typed)

        self.preview_label = ctk.CTkLabel(
            body,
            text="Результат: —",
            text_color=MUTED,
            font=ctk.CTkFont(size=11),
            anchor="w",
            justify="left",
            wraplength=760,
        )
        self.preview_label.grid(row=4, column=1, columnspan=2, sticky="ew", pady=(8, 0))

    def _build_action_card(self) -> None:
        card = SectionCard(self.content, "3. Конвертация")
        card.grid(row=3, column=0, sticky="ew", padx=24, pady=(0, 14))
        body = card.body

        self.convert_button = ctk.CTkButton(
            body,
            text="Конвертировать",
            height=48,
            font=ctk.CTkFont(size=15, weight="bold"),
            fg_color=ACCENT,
            command=self._start_conversion,
        )
        self.convert_button.grid(row=0, column=0, sticky="ew", pady=(0, 14))
        body.grid_columnconfigure(0, weight=1)

        status_row = ctk.CTkFrame(body, fg_color="transparent")
        status_row.grid(row=1, column=0, sticky="ew")
        status_row.grid_columnconfigure(1, weight=1)

        self.status_dot = StatusDot(status_row)
        self.status_dot.grid(row=0, column=0, padx=(0, 8))
        self.status_label = ctk.CTkLabel(
            status_row, text="Ожидание", anchor="w", font=ctk.CTkFont(size=12)
        )
        self.status_label.grid(row=0, column=1, sticky="w")

        self.progress = ctk.CTkProgressBar(status_row, width=220, mode="indeterminate")
        self.progress.grid(row=0, column=2, sticky="e")
        self.progress.set(0)

    def _build_result_card(self) -> None:
        self.result_card = SectionCard(self.content, "Результат", "Файл успешно создан")
        self.result_card.grid(row=4, column=0, sticky="ew", padx=24, pady=(0, 24))
        body = self.result_card.body

        self.result_name_label = ctk.CTkLabel(
            body, text="", font=ctk.CTkFont(size=15, weight="bold"), anchor="w"
        )
        self.result_name_label.grid(row=0, column=0, columnspan=2, sticky="ew")
        self.result_path_label = ctk.CTkLabel(
            body, text="", text_color=MUTED, anchor="w", justify="left", wraplength=760
        )
        self.result_path_label.grid(row=1, column=0, columnspan=2, sticky="ew", pady=(4, 12))

        buttons = ctk.CTkFrame(body, fg_color="transparent")
        buttons.grid(row=2, column=0, columnspan=2, sticky="w")
        self.open_file_button = ctk.CTkButton(
            buttons, text="Открыть файл", width=150, command=self._open_result_file
        )
        self.open_file_button.grid(row=0, column=0, padx=(0, 10))
        self.open_folder_button = ctk.CTkButton(
            buttons,
            text="Открыть папку",
            width=150,
            fg_color="transparent",
            border_width=1,
            text_color=("#333333", "#dddddd"),
            command=self._open_result_folder,
        )
        self.open_folder_button.grid(row=0, column=1)
        self.result_card.grid_remove()

    def _browse_source(self) -> None:
        selected = filedialog.askopenfilename(
            title="Выберите исходный файл",
            filetypes=SUPPORTED_FILETYPES,
        )
        if selected:
            self._apply_source(Path(selected))

    def _apply_source(self, path: Path) -> None:
        self.source_path_var.set(str(path))
        self._source_info = None
        self._targets = []
        self._target_labels = {}
        self._name_edited = False
        self._last_result_path = None
        self.result_card.grid_remove()
        self.target_var.set("—")
        self.target_menu.configure(values=["—"])
        self.target_hint.configure(text="Проверка файла...")
        self.source_name_label.configure(text=path.name)
        self.source_format_label.configure(text="—")
        self.source_size_label.configure(text="—")

        try:
            info = SourceInfo.from_path(path)
        except FileConverterError as exc:
            self._show_error("Не удалось прочитать файл", exc)
            self._set_status("Ошибка чтения файла", "error")
            self._update_preview()
            return

        self._source_info = info
        self.source_format_label.configure(text=info.extension.upper())
        self.source_size_label.configure(text=info.size_human)

        try:
            validate_source(path)
        except FileConverterError as exc:
            self._source_info = None
            self.target_hint.configure(text="Формат исходного файла не поддерживается")
            self._set_status("Неподдерживаемый формат", "error")
            self._update_preview()
            self._show_error("Файл не поддерживается", exc)
            return

        targets = available_targets(info.extension)
        if not targets:
            self.target_hint.configure(
                text="Для этого формата сейчас нет доступных конвертаций. "
                "Проверьте установку LibreOffice."
            )
            self._set_status("Нет доступных форматов", "error")
            self._update_preview()
            return

        self._targets = targets
        labels = [FORMAT_LABELS[target] for target in targets]
        self._target_labels = {FORMAT_LABELS[target]: target for target in targets}
        self.target_menu.configure(values=labels)
        self.target_var.set(labels[0])
        self._on_target_change(labels[0], reset_name=True)

        if not self._output_dir_user_set or not self.output_dir_var.get().strip():
            self.output_dir_var.set(str(path.parent))
        self._update_preview()
        self._set_status("Файл выбран, можно конвертировать", "idle")

    def _current_target(self) -> str | None:
        return self._target_labels.get(self.target_var.get())

    def _on_target_change(self, choice: str, reset_name: bool = False) -> None:
        target = self._target_labels.get(choice)
        if target is None:
            self._update_preview()
            return
        self.target_hint.configure(text=self._target_description(target))
        if reset_name or not self._name_edited:
            self._set_auto_name(target)
        self._update_preview()

    def _target_description(self, target: str) -> str:
        source = self._source_info.extension if self._source_info else "?"
        mapping = {
            ("csv", "json"): "Таблица CSV будет преобразована в массив JSON-объектов.",
            ("json", "csv"): "Массив JSON-объектов будет преобразован в таблицу CSV.",
            ("txt", "docx"): "Каждая строка текста станет абзацем документа Word.",
            ("docx", "txt"): "Из документа Word будет извлечён текст абзацев и таблиц.",
            ("txt", "pdf"): "Текст будет свёрстан в PDF с поддержкой Unicode.",
            ("docx", "pdf"): "Требуется LibreOffice. Word-документ будет экспортирован в PDF.",
            ("odt", "pdf"): "Требуется LibreOffice. OpenDocument будет экспортирован в PDF.",
            ("docx", "odt"): "Требуется LibreOffice. Word будет преобразован в ODT.",
            ("odt", "docx"): "Требуется LibreOffice. ODT будет преобразован в Word.",
            ("odt", "txt"): "Из OpenDocument будет извлечён текст через odfpy.",
        }
        return mapping.get((source, target), f"Преобразование {source.upper()} → {target.upper()}.")

    def _set_auto_name(self, target: str) -> None:
        if not self._source_info:
            return
        name = build_output_name(self._source_info.path.stem, target)
        self._last_auto_name = name
        self.name_var.set(name)
        self._name_edited = False

    def _on_name_typed(self, _event=None) -> None:
        self._name_edited = True
        self._update_preview()

    def _on_dir_typed(self, _event=None) -> None:
        self._output_dir_user_set = True
        self._update_preview()

    def _browse_output_dir(self) -> None:
        initial = self.output_dir_var.get().strip()
        selected = filedialog.askdirectory(
            title="Выберите папку назначения",
            initialdir=initial if Path(initial).is_dir() else None,
        )
        if selected:
            self.output_dir_var.set(selected)
            self._output_dir_user_set = True
            self._update_preview()

    def _update_preview(self) -> None:
        target = self._current_target()
        directory = self.output_dir_var.get().strip()
        name = self.name_var.get().strip()
        can_convert = False

        if not self._source_info:
            self.preview_label.configure(text="Результат: —", text_color=MUTED)
        elif not target:
            self.preview_label.configure(text="Результат: выберите целевой формат", text_color=MUTED)
        elif not directory:
            self.preview_label.configure(text="Результат: выберите папку назначения", text_color=MUTED)
        elif not Path(directory).expanduser().is_dir():
            self.preview_label.configure(
                text=f"Результат: папка не существует — {directory}", text_color="#d97706"
            )
        else:
            try:
                resolved_name, path = build_output_path(
                    self._source_info.path, target, Path(directory).expanduser(), name or None
                )
            except FileConverterError as exc:
                self.preview_label.configure(
                    text=f"Проверьте параметры: {exc.message}", text_color="#d97706"
                )
            else:
                can_convert = True
                note = " · файл существует, будет запрошено подтверждение" if path.exists() else ""
                self.preview_label.configure(
                    text=f"Результат: {path}{note}", text_color=MUTED
                )

        self._set_controls_state(can_convert)

    def _set_controls_state(self, can_convert: bool | None = None) -> None:
        if can_convert is None:
            can_convert = bool(self._source_info and self._current_target())
        state = "disabled" if self._busy else "normal"
        self.browse_button.configure(state=state)
        self.output_dir_button.configure(state=state)
        self.output_dir_entry.configure(state=state)
        self.name_entry.configure(state=state)
        self.target_menu.configure(state="disabled" if self._busy else "normal")
        self.convert_button.configure(
            state="normal" if can_convert and not self._busy else "disabled"
        )

    def _set_busy(self, busy: bool) -> None:
        self._busy = busy
        if busy:
            self.progress.start()
            self._set_status("Конвертация выполняется...", "working")
        else:
            self.progress.stop()
        self._set_controls_state()

    def _start_conversion(self) -> None:
        if self._busy or not self._source_info:
            return
        target = self._current_target()
        directory = self.output_dir_var.get().strip()
        if not target or not directory:
            show_message(
                self,
                "Недостаточно параметров",
                "Выберите целевой формат и папку назначения.",
                error=True,
            )
            return

        request = ConversionRequest(
            source=self._source_info.path,
            target_format=target,
            output_dir=Path(directory).expanduser(),
            output_name=self.name_var.get().strip() or None,
        )

        try:
            validate_request(request)
        except OutputConflictError as exc:
            suggested = unique_path(exc.path)
            decision = ask_overwrite(self, exc.path, suggested)
            if decision is None:
                return
            if decision == "unique":
                request.output_name = suggested.name
            else:
                request.overwrite = True
            try:
                validate_request(request)
            except FileConverterError as retry_exc:
                self._show_error("Не удалось начать конвертацию", retry_exc)
                return
        except FileConverterError as exc:
            self._set_status("Ошибка в параметрах", "error")
            self._show_error("Проверьте параметры", exc)
            return

        self.result_card.grid_remove()
        self._last_result_path = None
        self._set_busy(True)
        self._thread = threading.Thread(
            target=self._run_conversion, args=(request,), daemon=True
        )
        self._thread.start()

    def _run_conversion(self, request: ConversionRequest) -> None:
        try:
            result = execute_conversion(request)
        except Exception as exc:
            self._queue.put(("error", exc))
        else:
            self._queue.put(("success", result))

    def _poll_queue(self) -> None:
        try:
            while True:
                kind, payload = self._queue.get_nowait()
                if self._closing:
                    return
                if kind == "success":
                    self._finish_success(payload)
                else:
                    self._finish_error(payload)
        except queue.Empty:
            pass
        if not self._closing:
            self.after(100, self._poll_queue)

    def _finish_success(self, result) -> None:
        self._set_busy(False)
        self._last_result_path = result.output_path
        self.result_name_label.configure(text=result.output_name)
        self.result_path_label.configure(text=str(result.output_path))
        self.result_card.grid()
        self._set_status(
            f"Готово за {result.duration_seconds:.1f} с · {result.output_path.name}", "success"
        )
        self._update_preview()

    def _finish_error(self, exc: Exception) -> None:
        self._set_busy(False)
        self._set_status("Ошибка конвертации", "error")
        if isinstance(exc, FileConverterError):
            self._show_error("Конвертация не выполнена", exc)
        else:
            show_message(
                self,
                "Непредвиденная ошибка",
                f"{type(exc).__name__}: {exc}",
                "Подробности записаны в logs/converter.log.",
                error=True,
            )
        self._update_preview()

    def _show_error(self, title: str, exc: FileConverterError) -> None:
        show_message(self, title, exc.message, exc.hint, error=True)

    def _open_result_file(self) -> None:
        if not self._last_result_path:
            return
        try:
            open_file(self._last_result_path)
        except FileConverterError as exc:
            self._show_error("Не удалось открыть файл", exc)

    def _open_result_folder(self) -> None:
        if not self._last_result_path:
            return
        try:
            open_folder(self._last_result_path.parent)
        except FileConverterError as exc:
            self._show_error("Не удалось открыть папку", exc)

    def _toggle_theme(self) -> None:
        if ctk.get_appearance_mode().lower() == "dark":
            ctk.set_appearance_mode("light")
            self.theme_switch.configure(text="Тёмная тема")
        else:
            ctk.set_appearance_mode("dark")
            self.theme_switch.configure(text="Светлая тема")

    def _set_status(self, text: str, state: str) -> None:
        self.status_label.configure(text=text)
        self.status_dot.set_state(state)

    def _on_close(self) -> None:
        if self._busy:
            confirmed = ask_confirm(
                self,
                "Конвертация выполняется",
                "Закрыть приложение? Текущая операция может быть прервана.",
                confirm_text="Закрыть",
            )
            if not confirmed:
                return
        self._closing = True
        self.destroy()
