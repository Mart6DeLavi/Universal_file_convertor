from __future__ import annotations

import math
import queue
import threading
import time
from pathlib import Path
from tkinter import filedialog

import customtkinter as ctk

from ..config import (
    APP_NAME,
    APP_VERSION,
    FORMAT_LABELS,
    SUPPORTED_FILETYPES,
    get_language,
    set_language,
)
from ..exceptions import FileConverterError, OutputConflictError
from ..models import ConversionRequest, SourceInfo
from ..registry import available_targets
from ..service import execute as execute_conversion
from ..utils.paths import build_output_name, human_size, unique_path
from ..utils.platform_utils import open_file, open_folder
from ..validators import build_output_path, validate_request, validate_source
from .components import ACCENT, MUTED, SectionCard, StatusDot
from .dialogs import ask_confirm, ask_overwrite, show_message
from .i18n import has_translation, translate


class MainWindow(ctk.CTk):
    def __init__(self) -> None:
        super().__init__()
        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("blue")

        self._language = get_language()
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
        self._last_result = None
        self._last_error: tuple[str, str] | None = None
        self._poll_id: str | None = None
        self._progress_after_id: str | None = None
        self._progress_value = 0.0
        self._progress_target = 0.0
        self._busy_started = 0.0

        self.title(APP_NAME)
        self.geometry("1180x720")
        self.minsize(1000, 620)
        self.configure(fg_color=("#eef0f5", "#0f0f12"))

        self._build_layout()
        self._set_status(self._t("status.waiting_source"), "idle")
        self._update_preview()
        self._poll_id = self.after(100, self._poll_queue)
        self.protocol("WM_DELETE_WINDOW", self._on_close)

    def _t(self, key: str, **values) -> str:
        return translate(self._language, key, **values)

    def _build_layout(self) -> None:
        self.grid_rowconfigure(1, weight=1)
        self.grid_columnconfigure(0, weight=1)

        self._build_header()

        self.workspace = ctk.CTkFrame(self, fg_color="transparent")
        self.workspace.grid(
            row=1, column=0, sticky="nsew", padx=24, pady=(0, 22)
        )
        self.workspace.grid_rowconfigure(0, weight=1)
        self.workspace.grid_columnconfigure(0, weight=1, uniform="panel")
        self.workspace.grid_columnconfigure(1, weight=1, uniform="panel")

        self._build_source_panel()
        self._build_result_panel()

    def _build_header(self) -> None:
        header = ctk.CTkFrame(self, fg_color="transparent")
        header.grid(row=0, column=0, sticky="ew", padx=24, pady=(18, 12))
        header.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(
            header,
            text=APP_NAME,
            font=ctk.CTkFont(size=28, weight="bold"),
            anchor="w",
        ).grid(row=0, column=0, sticky="w")
        ctk.CTkLabel(
            header,
            text=self._t("app.subtitle", version=APP_VERSION),
            font=ctk.CTkFont(size=12),
            text_color=MUTED,
            anchor="w",
        ).grid(row=1, column=0, sticky="w", pady=(2, 0))

        self.language_switch = ctk.CTkSegmentedButton(
            header,
            values=["EN", "PL"],
            width=104,
            command=self._on_language_change,
        )
        self.language_switch.set(self._language.upper())
        self.language_switch.grid(
            row=0, column=1, rowspan=2, sticky="e", padx=(0, 16)
        )

        self.theme_switch = ctk.CTkSwitch(
            header, text=self._theme_label(), command=self._toggle_theme
        )
        self.theme_switch.grid(row=0, column=2, rowspan=2, sticky="e")

    def _build_source_panel(self) -> None:
        container = ctk.CTkFrame(self.workspace, fg_color="transparent")
        container.grid(row=0, column=0, sticky="nsew", padx=(0, 8))
        container.grid_rowconfigure(0, weight=1)
        container.grid_columnconfigure(0, weight=1)

        card = SectionCard(
            container,
            self._t("source.title"),
            self._t("source.subtitle"),
        )
        card.grid(row=0, column=0, sticky="nsew")
        body = card.body
        body.grid_columnconfigure(0, minsize=112)
        body.grid_columnconfigure(1, weight=1)

        ctk.CTkLabel(body, text=self._t("source.file"), anchor="w").grid(
            row=0, column=0, sticky="w", padx=(0, 10)
        )
        self.source_path_var = ctk.StringVar(value="")
        self.source_path_entry = ctk.CTkEntry(
            body, textvariable=self.source_path_var, state="readonly", height=34
        )
        self.source_path_entry.grid(row=0, column=1, sticky="ew")
        self.browse_button = ctk.CTkButton(
            body, text=self._t("source.browse"), width=92, height=34, command=self._browse_source
        )
        self.browse_button.grid(row=0, column=2, sticky="e", padx=(10, 0))

        info = ctk.CTkFrame(body, fg_color="transparent")
        info.grid(row=1, column=1, columnspan=2, sticky="ew", pady=(10, 0))
        info.grid_columnconfigure((0, 1, 2), weight=1)

        self.source_name_label = self._info_tile(info, 0, self._t("tile.name"), "—", 142)
        self.source_format_label = self._info_tile(info, 1, self._t("tile.format"), "—", 142)
        self.source_size_label = self._info_tile(info, 2, self._t("tile.size"), "—", 142)

        divider = ctk.CTkFrame(body, height=1, fg_color=("#e4e4ec", "#2b2b31"))
        divider.grid(row=2, column=0, columnspan=3, sticky="ew", pady=(12, 12))

        ctk.CTkLabel(body, text=self._t("source.target"), anchor="w").grid(
            row=3, column=0, sticky="w", padx=(0, 10)
        )
        self.target_var = ctk.StringVar(value="—")
        self.target_menu = ctk.CTkOptionMenu(
            body,
            values=["—"],
            variable=self.target_var,
            command=self._on_target_change,
            width=150,
            height=32,
        )
        self.target_menu.grid(row=3, column=1, sticky="w")

        self.target_hint = ctk.CTkLabel(
            body,
            text=self._t("source.target.initial"),
            text_color=MUTED,
            font=ctk.CTkFont(size=11),
            anchor="w",
            justify="left",
            wraplength=380,
        )
        self.target_hint.grid(row=4, column=1, columnspan=2, sticky="ew", pady=(4, 8))

        ctk.CTkLabel(body, text=self._t("source.output_dir"), anchor="w").grid(
            row=5, column=0, sticky="w", padx=(0, 10)
        )
        self.output_dir_var = ctk.StringVar(value="")
        self.output_dir_entry = ctk.CTkEntry(
            body, textvariable=self.output_dir_var, height=34
        )
        self.output_dir_entry.grid(row=5, column=1, sticky="ew")
        self.output_dir_entry.bind("<KeyRelease>", self._on_dir_typed)
        self.output_dir_button = ctk.CTkButton(
            body,
            text=self._t("source.browse"),
            width=92,
            height=34,
            command=self._browse_output_dir,
        )
        self.output_dir_button.grid(row=5, column=2, sticky="e", padx=(10, 0))

        ctk.CTkLabel(body, text=self._t("source.output_name"), anchor="w").grid(
            row=6, column=0, sticky="w", padx=(0, 10), pady=(8, 0)
        )
        self.name_var = ctk.StringVar(value="")
        self.name_entry = ctk.CTkEntry(body, textvariable=self.name_var, height=34)
        self.name_entry.grid(
            row=6, column=1, columnspan=2, sticky="ew", pady=(8, 0)
        )
        self.name_entry.bind("<KeyRelease>", self._on_name_typed)

        self.preview_label = ctk.CTkLabel(
            body,
            text=self._t("preview.empty"),
            text_color=MUTED,
            font=ctk.CTkFont(size=11),
            anchor="w",
            justify="left",
            wraplength=520,
        )
        self.preview_label.grid(
            row=7, column=1, columnspan=2, sticky="ew", pady=(6, 0)
        )

        self.convert_button = ctk.CTkButton(
            body,
            text=self._t("source.convert"),
            height=44,
            font=ctk.CTkFont(size=15, weight="bold"),
            fg_color=ACCENT,
            command=self._start_conversion,
        )
        self.convert_button.grid(
            row=8, column=0, columnspan=3, sticky="ew", pady=(14, 0)
        )

        status_row = ctk.CTkFrame(body, fg_color="transparent")
        status_row.grid(row=9, column=0, columnspan=3, sticky="ew", pady=(10, 0))
        status_row.grid_columnconfigure(1, weight=1)

        self.status_dot = StatusDot(status_row)
        self.status_dot.grid(row=0, column=0, padx=(0, 8))
        self.status_label = ctk.CTkLabel(
            status_row, text=self._t("status.waiting"), anchor="w", font=ctk.CTkFont(size=12)
        )
        self.status_label.grid(row=0, column=1, sticky="w")

        progress_box = ctk.CTkFrame(status_row, fg_color="transparent")
        progress_box.grid(row=0, column=2, sticky="e")
        progress_box.grid_columnconfigure(0, weight=1)

        self.progress = ctk.CTkProgressBar(
            progress_box, width=120, mode="determinate"
        )
        self.progress.grid(row=0, column=0, sticky="e")
        self.progress.set(0)

        self.progress_percent_label = ctk.CTkLabel(
            progress_box,
            text="0%",
            width=42,
            anchor="e",
            font=ctk.CTkFont(size=11),
            text_color=MUTED,
        )
        self.progress_percent_label.grid(row=0, column=1, sticky="e", padx=(8, 0))

    def _info_tile(
        self, parent, column: int, caption: str, value: str, wrap: int
    ) -> ctk.CTkLabel:
        frame = ctk.CTkFrame(
            parent, fg_color=("#f5f6fa", "#17171b"), corner_radius=9
        )
        frame.grid(
            row=0, column=column, sticky="nsew", padx=(0 if column == 0 else 6, 0)
        )
        frame.grid_columnconfigure(0, weight=1)
        ctk.CTkLabel(
            frame,
            text=caption,
            font=ctk.CTkFont(size=10),
            text_color=MUTED,
            anchor="w",
        ).grid(row=0, column=0, sticky="w", padx=10, pady=(6, 0))
        label = ctk.CTkLabel(
            frame,
            text=value,
            font=ctk.CTkFont(size=12, weight="bold"),
            anchor="w",
            justify="left",
            wraplength=wrap,
        )
        label.grid(row=1, column=0, sticky="ew", padx=10, pady=(0, 7))
        return label

    def _build_result_panel(self) -> None:
        container = ctk.CTkFrame(self.workspace, fg_color="transparent")
        container.grid(row=0, column=1, sticky="nsew", padx=(8, 0))
        container.grid_rowconfigure(0, weight=1)
        container.grid_columnconfigure(0, weight=1)

        self.result_card = SectionCard(
            container,
            self._t("result.title"),
            self._t("result.subtitle"),
        )
        self.result_card.grid(row=0, column=0, sticky="nsew")
        self.result_card.grid_rowconfigure(1, weight=1)
        body = self.result_card.body
        body.grid_rowconfigure(0, weight=1)
        body.grid_columnconfigure(0, weight=1)

        self._build_empty_result(body)
        self._build_busy_result(body)
        self._build_success_result(body)
        self._build_error_result(body)
        self._show_result_state("empty")

    def _build_empty_result(self, parent) -> None:
        self.result_empty = ctk.CTkFrame(parent, fg_color="transparent")
        self.result_empty.grid(row=0, column=0, sticky="nsew")
        self.result_empty.grid_columnconfigure(0, weight=1)
        self.result_empty.grid_rowconfigure(0, weight=1)
        self.result_empty.grid_rowconfigure(5, weight=1)

        self.empty_title = ctk.CTkLabel(
            self.result_empty,
            text=self._t("result.empty.title"),
            font=ctk.CTkFont(size=22, weight="bold"),
            anchor="center",
            justify="center",
        )
        self.empty_title.grid(row=1, column=0, sticky="ew", pady=(0, 8))

        self.empty_text = ctk.CTkLabel(
            self.result_empty,
            text=self._t("result.empty.text"),
            text_color=MUTED,
            justify="center",
            wraplength=390,
        )
        self.empty_text.grid(row=2, column=0, sticky="ew", padx=20)

        ctk.CTkLabel(
            self.result_empty,
            text=self._t("result.empty.directions"),
            text_color=MUTED,
            font=ctk.CTkFont(size=11),
            justify="center",
        ).grid(row=3, column=0, sticky="ew", pady=(22, 0))

    def _build_busy_result(self, parent) -> None:
        self.result_busy = ctk.CTkFrame(parent, fg_color="transparent")
        self.result_busy.grid(row=0, column=0, sticky="nsew")
        self.result_busy.grid_columnconfigure(0, weight=1)
        self.result_busy.grid_rowconfigure(0, weight=1)
        self.result_busy.grid_rowconfigure(2, weight=1)

        content = ctk.CTkFrame(self.result_busy, fg_color="transparent")
        content.grid(row=1, column=0)
        content.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(
            content,
            text=self._t("result.busy.title"),
            font=ctk.CTkFont(size=22, weight="bold"),
            anchor="center",
            justify="center",
        ).grid(row=0, column=0, sticky="ew", pady=(0, 10))

        self.busy_percent_label = ctk.CTkLabel(
            content,
            text="0%",
            font=ctk.CTkFont(size=38, weight="bold"),
            text_color=ACCENT,
            anchor="center",
            justify="center",
        )
        self.busy_percent_label.grid(row=1, column=0, sticky="ew", pady=(0, 12))

        ctk.CTkLabel(
            content,
            text=self._t("result.busy.text"),
            text_color=MUTED,
            anchor="center",
            justify="center",
            wraplength=360,
        ).grid(row=2, column=0, sticky="ew")

    def _build_success_result(self, parent) -> None:
        self.result_success = ctk.CTkFrame(parent, fg_color="transparent")
        self.result_success.grid(row=0, column=0, sticky="nsew")
        self.result_success.grid_columnconfigure(0, weight=1)
        self.result_success.grid_rowconfigure(4, weight=1)

        ctk.CTkLabel(
            self.result_success,
            text=self._t("result.success.title"),
            font=ctk.CTkFont(size=10, weight="bold"),
            text_color=("#15803d", "#4ade80"),
            anchor="w",
        ).grid(row=0, column=0, sticky="w", pady=(0, 8))

        self.result_name_label = ctk.CTkLabel(
            self.result_success,
            text="",
            font=ctk.CTkFont(size=20, weight="bold"),
            anchor="w",
            justify="left",
            wraplength=420,
        )
        self.result_name_label.grid(row=1, column=0, sticky="ew")

        self.result_path_label = ctk.CTkLabel(
            self.result_success,
            text="",
            text_color=MUTED,
            anchor="w",
            justify="left",
            wraplength=420,
        )
        self.result_path_label.grid(row=2, column=0, sticky="ew", pady=(6, 14))

        details = ctk.CTkFrame(self.result_success, fg_color="transparent")
        details.grid(row=3, column=0, sticky="ew")
        details.grid_columnconfigure((0, 1, 2), weight=1)

        self.result_format_label = self._info_tile(
            details, 0, self._t("tile.format"), "—", 140
        )
        self.result_size_label = self._info_tile(
            details, 1, self._t("tile.size"), "—", 140
        )
        self.result_time_label = self._info_tile(
            details, 2, self._t("tile.time"), "—", 140
        )

        actions = ctk.CTkFrame(self.result_success, fg_color="transparent")
        actions.grid(row=5, column=0, sticky="ew", pady=(14, 0))
        actions.grid_columnconfigure((0, 1), weight=1)

        self.open_file_button = ctk.CTkButton(
            actions,
            text=self._t("result.open_file"),
            height=38,
            command=self._open_result_file,
        )
        self.open_file_button.grid(row=0, column=0, sticky="ew", padx=(0, 5))
        self.open_folder_button = ctk.CTkButton(
            actions,
            text=self._t("result.open_folder"),
            height=38,
            fg_color="transparent",
            border_width=1,
            text_color=("#333333", "#dddddd"),
            command=self._open_result_folder,
        )
        self.open_folder_button.grid(row=0, column=1, sticky="ew", padx=(5, 0))

        ctk.CTkLabel(
            self.result_success,
            text=self._t("result.success.note"),
            text_color=MUTED,
            font=ctk.CTkFont(size=11),
            anchor="w",
        ).grid(row=6, column=0, sticky="w", pady=(10, 0))

    def _build_error_result(self, parent) -> None:
        self.result_error = ctk.CTkFrame(parent, fg_color="transparent")
        self.result_error.grid(row=0, column=0, sticky="nsew")
        self.result_error.grid_columnconfigure(0, weight=1)
        self.result_error.grid_rowconfigure(0, weight=1)
        self.result_error.grid_rowconfigure(5, weight=1)

        ctk.CTkLabel(
            self.result_error,
            text=self._t("result.error.title"),
            font=ctk.CTkFont(size=22, weight="bold"),
            text_color=("#b91c1c", "#f87171"),
            anchor="center",
        ).grid(row=1, column=0, sticky="ew", pady=(0, 8))

        self.error_message_label = ctk.CTkLabel(
            self.result_error,
            text="",
            justify="center",
            wraplength=390,
        )
        self.error_message_label.grid(row=2, column=0, sticky="ew", padx=20)

        self.error_hint_label = ctk.CTkLabel(
            self.result_error,
            text="",
            justify="center",
            text_color=MUTED,
            wraplength=390,
        )
        self.error_hint_label.grid(row=3, column=0, sticky="ew", padx=20, pady=(8, 0))

        ctk.CTkLabel(
            self.result_error,
            text=self._t("result.error.details"),
            justify="center",
            text_color=MUTED,
            font=ctk.CTkFont(size=11),
        ).grid(row=4, column=0, sticky="ew", pady=(18, 0))

    def _show_result_state(self, state: str) -> None:
        for frame in (
            self.result_empty,
            self.result_busy,
            self.result_success,
            self.result_error,
        ):
            frame.grid_remove()
        target = {
            "empty": self.result_empty,
            "busy": self.result_busy,
            "success": self.result_success,
            "error": self.result_error,
        }[state]
        target.grid()

    def _browse_source(self) -> None:
        selected = filedialog.askopenfilename(
            title=self._t("source.select_file"),
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
        self._last_result = None
        self._last_error = None
        self._reset_progress()
        self._show_result_state("empty")
        self.empty_title.configure(text=self._t("result.empty.title"))
        self.empty_text.configure(text=self._t("result.empty.text"))
        self.target_var.set("—")
        self.target_menu.configure(values=["—"])
        self.target_hint.configure(text=self._t("status.checking"))
        self.source_name_label.configure(text=path.name)
        self.source_format_label.configure(text="—")
        self.source_size_label.configure(text="—")

        try:
            info = SourceInfo.from_path(path)
        except FileConverterError as exc:
            self._show_error(self._t("dialog.could_not_read"), exc)
            self._set_status(self._t("status.read_error"), "error")
            self._update_preview()
            return

        self._source_info = info
        self.source_format_label.configure(text=info.extension.upper())
        self.source_size_label.configure(text=info.size_human)

        try:
            validate_source(path)
        except FileConverterError as exc:
            self._source_info = None
            self.target_hint.configure(text=self._t("source.target.unsupported"))
            self._set_status(self._t("status.unsupported"), "error")
            self._update_preview()
            self._show_error(self._t("dialog.unsupported"), exc)
            return

        targets = available_targets(info.extension)
        if not targets:
            self.target_hint.configure(text=self._t("source.target.unavailable"))
            self._set_status(self._t("status.no_targets"), "error")
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
        self._set_status(self._t("status.ready"), "idle")

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
        key = f"target.{source}.{target}"
        if has_translation(self._language, key):
            return self._t(key)
        return self._t("target.default", source=source.upper(), target=target.upper())

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
            title=self._t("source.select_folder"),
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
            self.preview_label.configure(
                text=self._t("preview.empty"), text_color=MUTED
            )
        elif not target:
            self.preview_label.configure(
                text=self._t("preview.select_target"), text_color=MUTED
            )
        elif not directory:
            self.preview_label.configure(
                text=self._t("preview.select_folder"), text_color=MUTED
            )
        elif not Path(directory).expanduser().is_dir():
            self.preview_label.configure(
                text=self._t("preview.folder_missing", directory=directory),
                text_color="#d97706",
            )
        else:
            try:
                resolved_name, path = build_output_path(
                    self._source_info.path,
                    target,
                    Path(directory).expanduser(),
                    name or None,
                )
            except FileConverterError as exc:
                self.preview_label.configure(
                    text=self._t("preview.check", message=exc.message),
                    text_color="#d97706",
                )
            else:
                can_convert = True
                note = self._t("preview.exists") if path.exists() else ""
                self.preview_label.configure(
                    text=self._t("preview.path", path=path, note=note),
                    text_color=MUTED,
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

    def _set_progress_display(self) -> None:
        self.progress.set(self._progress_value)
        percent = int(round(self._progress_value * 100))
        self.progress_percent_label.configure(text=f"{percent}%")
        self.busy_percent_label.configure(text=f"{percent}%")

    def _reset_progress(self) -> None:
        self._cancel_progress_animation()
        self._progress_value = 0.0
        self._progress_target = 0.0
        self._set_progress_display()

    def _cancel_progress_animation(self) -> None:
        if self._progress_after_id is not None:
            self.after_cancel(self._progress_after_id)
            self._progress_after_id = None

    def _set_progress_target(self, value: float) -> None:
        self._progress_target = max(self._progress_target, min(1.0, value))
        self._ensure_progress_animation()

    def _ensure_progress_animation(self) -> None:
        if self._progress_after_id is None:
            self._progress_after_id = self.after(30, self._tick_progress)

    def _tick_progress(self) -> None:
        self._progress_after_id = None
        if self._busy:
            elapsed = time.monotonic() - self._busy_started
            estimate = 0.9 - 0.85 * math.exp(-elapsed / 0.8)
            self._progress_target = max(self._progress_target, estimate)

        delta = self._progress_target - self._progress_value
        if delta > 0.0007:
            self._progress_value += delta * 0.28
            if self._progress_target - self._progress_value < 0.0007:
                self._progress_value = self._progress_target
            self._set_progress_display()

        if self._busy or self._progress_value < self._progress_target - 0.0007:
            self._progress_after_id = self.after(30, self._tick_progress)

    def _set_busy(self, busy: bool) -> None:
        self._busy = busy
        if busy:
            self._progress_value = 0.0
            self._progress_target = 0.03
            self._busy_started = time.monotonic()
            self._set_progress_display()
            self._show_result_state("busy")
            self._set_status(self._t("status.converting"), "working")
            self._ensure_progress_animation()
        self._set_controls_state()

    def _start_conversion(self) -> None:
        if self._busy or not self._source_info:
            return
        target = self._current_target()
        directory = self.output_dir_var.get().strip()
        if not target or not directory:
            show_message(
                self,
                self._t("dialog.missing_settings"),
                self._t("dialog.missing_settings.text"),
                error=True,
                language=self._language,
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
            decision = ask_overwrite(
                self, exc.path, suggested, language=self._language
            )
            if decision is None:
                return
            if decision == "unique":
                request.output_name = suggested.name
            else:
                request.overwrite = True
            try:
                validate_request(request)
            except FileConverterError as retry_exc:
                self._show_error(
                    self._t("dialog.could_not_start"), retry_exc
                )
                return
        except FileConverterError as exc:
            self._set_status(self._t("status.invalid"), "error")
            self._show_error(self._t("dialog.check_settings"), exc)
            return

        self._last_result_path = None
        self._last_result = None
        self._last_error = None
        self._set_busy(True)
        self._thread = threading.Thread(
            target=self._run_conversion, args=(request,), daemon=True
        )
        self._thread.start()

    def _run_conversion(self, request: ConversionRequest) -> None:
        try:
            result = execute_conversion(
                request, progress=lambda value: self._queue.put(("progress", value))
            )
        except Exception as exc:
            self._queue.put(("error", exc))
        else:
            self._queue.put(("success", result))

    def _poll_queue(self) -> None:
        self._poll_id = None
        try:
            while True:
                kind, payload = self._queue.get_nowait()
                if self._closing:
                    return
                if kind == "progress":
                    self._set_progress_target(payload)
                elif kind == "success":
                    self._finish_success(payload)
                else:
                    self._finish_error(payload)
        except queue.Empty:
            pass
        if not self._closing:
            self._poll_id = self.after(100, self._poll_queue)

    def _finish_success(self, result) -> None:
        self._set_busy(False)
        self._last_result = result
        self._last_result_path = result.output_path
        self.result_name_label.configure(text=result.output_name)
        self.result_path_label.configure(text=str(result.output_path))
        self.result_format_label.configure(text=result.target_format.upper())
        self.result_size_label.configure(text=human_size(result.size))
        self.result_time_label.configure(text=f"{result.duration_seconds:.1f} s")
        self._show_result_state("success")
        self._complete_progress()
        self._set_status(
            self._t(
                "status.done",
                duration=result.duration_seconds,
                name=result.output_path.name,
            ),
            "success",
        )
        self._update_preview()

    def _finish_error(self, exc: Exception) -> None:
        self._set_busy(False)
        self._set_status(self._t("status.failed"), "error")
        if isinstance(exc, FileConverterError):
            self._last_error = (exc.message, exc.hint)
            self.error_message_label.configure(text=exc.message)
            self.error_hint_label.configure(text=exc.hint)
            self._show_error(self._t("dialog.conversion_failed"), exc)
        else:
            message = f"{type(exc).__name__}: {exc}"
            self._last_error = (
                message,
                self._t("dialog.unexpected.hint"),
            )
            self.error_message_label.configure(text=message)
            self.error_hint_label.configure(
                text=self._t("dialog.unexpected.hint")
            )
            show_message(
                self,
                self._t("dialog.unexpected"),
                message,
                self._t("dialog.unexpected.hint"),
                error=True,
                language=self._language,
            )
        self._show_result_state("error")
        self._update_preview()

    def _show_error(self, title: str, exc: FileConverterError) -> None:
        show_message(
            self,
            title,
            exc.message,
            exc.hint,
            error=True,
            language=self._language,
        )

    def _open_result_file(self) -> None:
        if not self._last_result_path:
            return
        try:
            open_file(self._last_result_path)
        except FileConverterError as exc:
            self._show_error(self._t("dialog.open_file"), exc)

    def _open_result_folder(self) -> None:
        if not self._last_result_path:
            return
        try:
            open_folder(self._last_result_path.parent)
        except FileConverterError as exc:
            self._show_error(self._t("dialog.open_folder"), exc)

    def _theme_label(self) -> str:
        if ctk.get_appearance_mode().lower() == "dark":
            return self._t("theme.light")
        return self._t("theme.dark")

    def _toggle_theme(self) -> None:
        if ctk.get_appearance_mode().lower() == "dark":
            ctk.set_appearance_mode("light")
        else:
            ctk.set_appearance_mode("dark")
        self.theme_switch.configure(text=self._theme_label())

    def _set_status(self, text: str, state: str) -> None:
        self.status_label.configure(text=text)
        self.status_dot.set_state(state)

    def _complete_progress(self) -> None:
        self._cancel_progress_animation()
        self._progress_value = 1.0
        self._progress_target = 1.0
        self._set_progress_display()

    def _on_language_change(self, value: str) -> None:
        code = "pl" if value == "PL" else "en"
        if code == self._language:
            return
        if self._busy:
            self.language_switch.set(self._language.upper())
            return
        try:
            set_language(code)
        except OSError:
            pass
        self._language = code
        self._rebuild_ui()

    def _rebuild_ui(self) -> None:
        state = {
            "source_path": self.source_path_var.get().strip(),
            "target": self._current_target(),
            "output_dir": self.output_dir_var.get().strip(),
            "output_name": self.name_var.get().strip(),
            "name_edited": self._name_edited,
            "output_dir_user_set": self._output_dir_user_set,
            "last_result": self._last_result,
            "last_error": self._last_error,
        }

        if self._poll_id is not None:
            self.after_cancel(self._poll_id)
            self._poll_id = None
        self._cancel_progress_animation()
        while True:
            try:
                self._queue.get_nowait()
            except queue.Empty:
                break

        for child in list(self.winfo_children()):
            child.destroy()

        self._source_info = None
        self._targets = []
        self._target_labels = {}

        self._build_layout()
        self._poll_id = self.after(100, self._poll_queue)
        self._restore_ui_state(state)
        self._set_controls_state()

    def _restore_ui_state(self, state: dict) -> None:
        source_path = state["source_path"]
        restored_source = False
        if source_path and Path(source_path).is_file():
            self._apply_source(Path(source_path))
            restored_source = self._source_info is not None

            target = state["target"]
            label = FORMAT_LABELS.get(target) if target else None
            if label in self._target_labels:
                self.target_var.set(label)
                self._on_target_change(label, reset_name=False)

            if state["output_dir"]:
                self.output_dir_var.set(state["output_dir"])
            self._output_dir_user_set = state["output_dir_user_set"]
            if state["output_name"]:
                self.name_var.set(state["output_name"])
            self._name_edited = state["name_edited"]
            self._update_preview()

        last_result = state["last_result"]
        last_error = state["last_error"]
        if last_result is not None:
            self._finish_success(last_result)
            self._complete_progress()
        elif last_error is not None:
            message, hint = last_error
            self._last_error = last_error
            self.error_message_label.configure(text=message)
            self.error_hint_label.configure(text=hint)
            self._show_result_state("error")
            self._set_status(self._t("status.failed"), "error")
            self._reset_progress()
        elif restored_source:
            self._set_status(self._t("status.ready"), "idle")
            self._reset_progress()
        else:
            self._set_status(self._t("status.waiting_source"), "idle")
            self._reset_progress()

    def _on_close(self) -> None:
        if self._busy:
            confirmed = ask_confirm(
                self,
                self._t("dialog.close_in_progress"),
                self._t("dialog.close_in_progress.text"),
                confirm_text=self._t("dialog.close_button"),
                language=self._language,
            )
            if not confirmed:
                return
        self._closing = True
        if self._poll_id is not None:
            self.after_cancel(self._poll_id)
            self._poll_id = None
        self._cancel_progress_animation()
        self.destroy()
