from __future__ import annotations

import queue
import threading
from pathlib import Path
from tkinter import filedialog

import customtkinter as ctk

from ..config import APP_NAME, APP_VERSION, FORMAT_LABELS, SUPPORTED_FILETYPES
from ..exceptions import FileConverterError, OutputConflictError
from ..models import ConversionRequest, SourceInfo
from ..registry import available_targets
from ..service import execute as execute_conversion
from ..utils.paths import build_output_name, human_size, unique_path
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
        self.geometry("1180x720")
        self.minsize(1000, 620)
        self.configure(fg_color=("#eef0f5", "#0f0f12"))

        self._build_layout()
        self._set_status("Waiting for a source file", "idle")
        self._update_preview()
        self.after(100, self._poll_queue)
        self.protocol("WM_DELETE_WINDOW", self._on_close)

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
            text=f"Local conversion, no uploads · version {APP_VERSION}",
            font=ctk.CTkFont(size=12),
            text_color=MUTED,
            anchor="w",
        ).grid(row=1, column=0, sticky="w", pady=(2, 0))

        self.theme_switch = ctk.CTkSwitch(
            header, text="Light theme", command=self._toggle_theme
        )
        self.theme_switch.grid(row=0, column=1, rowspan=2, sticky="e")

    def _build_source_panel(self) -> None:
        container = ctk.CTkFrame(self.workspace, fg_color="transparent")
        container.grid(row=0, column=0, sticky="nsew", padx=(0, 8))
        container.grid_rowconfigure(0, weight=1)
        container.grid_columnconfigure(0, weight=1)

        card = SectionCard(
            container,
            "Source and settings",
            "Choose a file, target format, and destination",
        )
        card.grid(row=0, column=0, sticky="nsew")
        body = card.body
        body.grid_columnconfigure(0, minsize=112)
        body.grid_columnconfigure(1, weight=1)

        ctk.CTkLabel(body, text="Source file", anchor="w").grid(
            row=0, column=0, sticky="w", padx=(0, 10)
        )
        self.source_path_var = ctk.StringVar(value="")
        self.source_path_entry = ctk.CTkEntry(
            body, textvariable=self.source_path_var, state="readonly", height=34
        )
        self.source_path_entry.grid(row=0, column=1, sticky="ew")
        self.browse_button = ctk.CTkButton(
            body, text="Browse", width=92, height=34, command=self._browse_source
        )
        self.browse_button.grid(row=0, column=2, sticky="e", padx=(10, 0))

        info = ctk.CTkFrame(body, fg_color="transparent")
        info.grid(row=1, column=1, columnspan=2, sticky="ew", pady=(10, 0))
        info.grid_columnconfigure((0, 1, 2), weight=1)

        self.source_name_label = self._info_tile(info, 0, "Name", "—", 142)
        self.source_format_label = self._info_tile(info, 1, "Format", "—", 142)
        self.source_size_label = self._info_tile(info, 2, "Size", "—", 142)

        divider = ctk.CTkFrame(body, height=1, fg_color=("#e4e4ec", "#2b2b31"))
        divider.grid(row=2, column=0, columnspan=3, sticky="ew", pady=(12, 12))

        ctk.CTkLabel(body, text="Target format", anchor="w").grid(
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
            text="Select a source file first",
            text_color=MUTED,
            font=ctk.CTkFont(size=11),
            anchor="w",
            justify="left",
            wraplength=380,
        )
        self.target_hint.grid(row=4, column=1, columnspan=2, sticky="ew", pady=(4, 8))

        ctk.CTkLabel(body, text="Output folder", anchor="w").grid(
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
            text="Browse",
            width=92,
            height=34,
            command=self._browse_output_dir,
        )
        self.output_dir_button.grid(row=5, column=2, sticky="e", padx=(10, 0))

        ctk.CTkLabel(body, text="Output name", anchor="w").grid(
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
            text="Result: —",
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
            text="Convert",
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
            status_row, text="Waiting", anchor="w", font=ctk.CTkFont(size=12)
        )
        self.status_label.grid(row=0, column=1, sticky="w")

        self.progress = ctk.CTkProgressBar(status_row, width=150, mode="indeterminate")
        self.progress.grid(row=0, column=2, sticky="e")
        self.progress.set(0)

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
            "Result",
            "The converted file appears here",
        )
        self.result_card.grid(row=0, column=0, sticky="nsew")
        self.result_card.grid_rowconfigure(1, weight=1)
        body = self.result_card.body
        body.grid_rowconfigure(0, weight=1)
        body.grid_columnconfigure(0, weight=1)

        self._build_empty_result(body)
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
            text="No result yet",
            font=ctk.CTkFont(size=22, weight="bold"),
            anchor="center",
        )
        self.empty_title.grid(row=1, column=0, sticky="ew", pady=(0, 8))

        self.empty_text = ctk.CTkLabel(
            self.result_empty,
            text=(
                "Choose a source file on the left, select a target format, "
                "and press Convert."
            ),
            text_color=MUTED,
            justify="center",
            wraplength=390,
        )
        self.empty_text.grid(row=2, column=0, sticky="ew", padx=20)

        ctk.CTkLabel(
            self.result_empty,
            text=(
                "Available directions\n"
                "CSV ↔ JSON · TXT ↔ DOCX · TXT → PDF\n"
                "DOCX/ODT → PDF · DOCX ↔ ODT · ODT → TXT"
            ),
            text_color=MUTED,
            font=ctk.CTkFont(size=11),
            justify="center",
        ).grid(row=3, column=0, sticky="ew", pady=(22, 0))

    def _build_success_result(self, parent) -> None:
        self.result_success = ctk.CTkFrame(parent, fg_color="transparent")
        self.result_success.grid(row=0, column=0, sticky="nsew")
        self.result_success.grid_columnconfigure(0, weight=1)
        self.result_success.grid_rowconfigure(4, weight=1)

        ctk.CTkLabel(
            self.result_success,
            text="CONVERSION COMPLETE",
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

        self.result_format_label = self._info_tile(details, 0, "Format", "—", 140)
        self.result_size_label = self._info_tile(details, 1, "Size", "—", 140)
        self.result_time_label = self._info_tile(details, 2, "Time", "—", 140)

        actions = ctk.CTkFrame(self.result_success, fg_color="transparent")
        actions.grid(row=5, column=0, sticky="ew", pady=(14, 0))
        actions.grid_columnconfigure((0, 1), weight=1)

        self.open_file_button = ctk.CTkButton(
            actions, text="Open file", height=38, command=self._open_result_file
        )
        self.open_file_button.grid(row=0, column=0, sticky="ew", padx=(0, 5))
        self.open_folder_button = ctk.CTkButton(
            actions,
            text="Open folder",
            height=38,
            fg_color="transparent",
            border_width=1,
            text_color=("#333333", "#dddddd"),
            command=self._open_result_folder,
        )
        self.open_folder_button.grid(row=0, column=1, sticky="ew", padx=(5, 0))

        ctk.CTkLabel(
            self.result_success,
            text="The source file was not modified.",
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
            text="Conversion failed",
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
            text="Details are available in logs/converter.log.",
            justify="center",
            text_color=MUTED,
            font=ctk.CTkFont(size=11),
        ).grid(row=4, column=0, sticky="ew", pady=(18, 0))

    def _show_result_state(self, state: str) -> None:
        for frame in (self.result_empty, self.result_success, self.result_error):
            frame.grid_remove()
        target = {
            "empty": self.result_empty,
            "success": self.result_success,
            "error": self.result_error,
        }[state]
        target.grid()

    def _browse_source(self) -> None:
        selected = filedialog.askopenfilename(
            title="Select source file",
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
        self._show_result_state("empty")
        self.empty_title.configure(text="No result yet")
        self.empty_text.configure(
            text=(
                "Choose a source file on the left, select a target format, "
                "and press Convert."
            )
        )
        self.target_var.set("—")
        self.target_menu.configure(values=["—"])
        self.target_hint.configure(text="Checking file...")
        self.source_name_label.configure(text=path.name)
        self.source_format_label.configure(text="—")
        self.source_size_label.configure(text="—")

        try:
            info = SourceInfo.from_path(path)
        except FileConverterError as exc:
            self._show_error("Could not read the file", exc)
            self._set_status("Could not read the file", "error")
            self._update_preview()
            return

        self._source_info = info
        self.source_format_label.configure(text=info.extension.upper())
        self.source_size_label.configure(text=info.size_human)

        try:
            validate_source(path)
        except FileConverterError as exc:
            self._source_info = None
            self.target_hint.configure(text="This source format is not supported")
            self._set_status("Unsupported format", "error")
            self._update_preview()
            self._show_error("Unsupported file", exc)
            return

        targets = available_targets(info.extension)
        if not targets:
            self.target_hint.configure(
                text=(
                    "No conversions are available for this format. "
                    "Check that LibreOffice is installed."
                )
            )
            self._set_status("No available target formats", "error")
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
        self._set_status("File selected, ready to convert", "idle")

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
            ("csv", "json"): "The CSV table becomes an array of JSON objects.",
            ("json", "csv"): "The JSON object array becomes a CSV table.",
            ("txt", "docx"): "Each text line becomes a paragraph in a Word document.",
            ("docx", "txt"): "Paragraph and table text is extracted from the Word document.",
            ("txt", "pdf"): "Text is laid out as a Unicode-capable PDF.",
            ("docx", "pdf"): "LibreOffice exports the Word document to PDF.",
            ("odt", "pdf"): "LibreOffice exports the OpenDocument to PDF.",
            ("docx", "odt"): "LibreOffice converts the Word document to ODT.",
            ("odt", "docx"): "LibreOffice converts the OpenDocument to Word.",
            ("odt", "txt"): "Text is extracted from the OpenDocument with odfpy.",
        }
        return mapping.get(
            (source, target), f"Convert {source.upper()} → {target.upper()}."
        )

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
            title="Select output folder",
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
            self.preview_label.configure(text="Result: —", text_color=MUTED)
        elif not target:
            self.preview_label.configure(
                text="Result: select a target format", text_color=MUTED
            )
        elif not directory:
            self.preview_label.configure(
                text="Result: select an output folder", text_color=MUTED
            )
        elif not Path(directory).expanduser().is_dir():
            self.preview_label.configure(
                text=f"Result: folder does not exist — {directory}",
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
                    text=f"Check the settings: {exc.message}", text_color="#d97706"
                )
            else:
                can_convert = True
                note = (
                    " · file exists, confirmation will be requested"
                    if path.exists()
                    else ""
                )
                self.preview_label.configure(
                    text=f"Result: {path}{note}", text_color=MUTED
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
            self._set_status("Converting...", "working")
            self.empty_title.configure(text="Converting...")
            self.empty_text.configure(text="Please wait while the file is processed.")
            self._show_result_state("empty")
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
                "Missing settings",
                "Select a target format and an output folder.",
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
                self._show_error("Could not start the conversion", retry_exc)
                return
        except FileConverterError as exc:
            self._set_status("Invalid settings", "error")
            self._show_error("Check the settings", exc)
            return

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
        self.result_format_label.configure(text=result.target_format.upper())
        self.result_size_label.configure(text=human_size(result.size))
        self.result_time_label.configure(text=f"{result.duration_seconds:.1f} s")
        self._show_result_state("success")
        self._set_status(
            f"Done in {result.duration_seconds:.1f} s · {result.output_path.name}",
            "success",
        )
        self._update_preview()

    def _finish_error(self, exc: Exception) -> None:
        self._set_busy(False)
        self._set_status("Conversion failed", "error")
        if isinstance(exc, FileConverterError):
            self.error_message_label.configure(text=exc.message)
            self.error_hint_label.configure(text=exc.hint)
            self._show_error("Conversion failed", exc)
        else:
            message = f"{type(exc).__name__}: {exc}"
            self.error_message_label.configure(text=message)
            self.error_hint_label.configure(
                text="See logs/converter.log for more details."
            )
            show_message(
                self,
                "Unexpected error",
                message,
                "Details were written to logs/converter.log.",
                error=True,
            )
        self._show_result_state("error")
        self._update_preview()

    def _show_error(self, title: str, exc: FileConverterError) -> None:
        show_message(self, title, exc.message, exc.hint, error=True)

    def _open_result_file(self) -> None:
        if not self._last_result_path:
            return
        try:
            open_file(self._last_result_path)
        except FileConverterError as exc:
            self._show_error("Could not open the file", exc)

    def _open_result_folder(self) -> None:
        if not self._last_result_path:
            return
        try:
            open_folder(self._last_result_path.parent)
        except FileConverterError as exc:
            self._show_error("Could not open the folder", exc)

    def _toggle_theme(self) -> None:
        if ctk.get_appearance_mode().lower() == "dark":
            ctk.set_appearance_mode("light")
            self.theme_switch.configure(text="Dark theme")
        else:
            ctk.set_appearance_mode("dark")
            self.theme_switch.configure(text="Light theme")

    def _set_status(self, text: str, state: str) -> None:
        self.status_label.configure(text=text)
        self.status_dot.set_state(state)

    def _on_close(self) -> None:
        if self._busy:
            confirmed = ask_confirm(
                self,
                "Conversion in progress",
                "Close the application? The current operation may be interrupted.",
                confirm_text="Close",
            )
            if not confirmed:
                return
        self._closing = True
        self.destroy()
