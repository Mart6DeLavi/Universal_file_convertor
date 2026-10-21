from __future__ import annotations

from pathlib import Path

import customtkinter as ctk

from .components import MUTED


class _Modal(ctk.CTkToplevel):
    def __init__(self, parent, title: str, width: int, height: int):
        super().__init__(parent)
        self.result: str | None = None
        self.title(title)
        self.resizable(False, False)
        self.transient(parent)
        self.protocol("WM_DELETE_WINDOW", self._cancel)
        self.update_idletasks()
        x = parent.winfo_rootx() + max(0, (parent.winfo_width() - width) // 2)
        y = parent.winfo_rooty() + max(0, (parent.winfo_height() - height) // 3)
        self.geometry(f"{width}x{height}+{x}+{y}")
        self.after(20, self._activate)

    def _activate(self) -> None:
        self.grab_set()
        self.focus_force()

    def _cancel(self) -> None:
        self.result = None
        self.destroy()


class OverwriteDialog(_Modal):
    def __init__(self, parent, path: Path, suggested: Path):
        super().__init__(parent, "Файл уже существует", 520, 250)
        self.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(
            self,
            text="Целевой файл уже существует",
            font=ctk.CTkFont(size=18, weight="bold"),
            anchor="w",
        ).grid(row=0, column=0, sticky="ew", padx=24, pady=(24, 8))
        ctk.CTkLabel(
            self,
            text=str(path),
            text_color=MUTED,
            wraplength=460,
            justify="left",
            anchor="w",
        ).grid(row=1, column=0, sticky="ew", padx=24)
        ctk.CTkLabel(
            self,
            text="Перезаписать файл, сохранить под новым именем или отменить операцию?",
            wraplength=460,
            justify="left",
            anchor="w",
        ).grid(row=2, column=0, sticky="ew", padx=24, pady=(10, 0))

        buttons = ctk.CTkFrame(self, fg_color="transparent")
        buttons.grid(row=3, column=0, sticky="ew", padx=24, pady=(16, 20))
        buttons.grid_columnconfigure((0, 1, 2), weight=1)

        ctk.CTkButton(
            buttons, text="Отмена", fg_color="transparent", border_width=1,
            text_color=("#333333", "#dddddd"), command=self._cancel,
        ).grid(row=0, column=0, sticky="ew", padx=(0, 6))
        ctk.CTkButton(
            buttons, text=f"Сохранить как {suggested.name}", command=self._unique,
        ).grid(row=0, column=1, sticky="ew", padx=6)
        ctk.CTkButton(
            buttons, text="Перезаписать", fg_color="#b91c1c", hover_color="#991b1b",
            command=self._overwrite,
        ).grid(row=0, column=2, sticky="ew", padx=(6, 0))

    def _unique(self) -> None:
        self.result = "unique"
        self.destroy()

    def _overwrite(self) -> None:
        self.result = "overwrite"
        self.destroy()


class ConfirmDialog(_Modal):
    def __init__(self, parent, title: str, message: str, confirm_text: str = "Продолжить"):
        super().__init__(parent, title, 440, 210)
        self.grid_columnconfigure(0, weight=1)
        ctk.CTkLabel(
            self,
            text=title,
            font=ctk.CTkFont(size=17, weight="bold"),
            anchor="w",
        ).grid(row=0, column=0, sticky="ew", padx=24, pady=(24, 8))
        ctk.CTkLabel(
            self,
            text=message,
            wraplength=390,
            justify="left",
            anchor="w",
        ).grid(row=1, column=0, sticky="ew", padx=24)

        buttons = ctk.CTkFrame(self, fg_color="transparent")
        buttons.grid(row=2, column=0, sticky="ew", padx=24, pady=(18, 20))
        buttons.grid_columnconfigure((0, 1), weight=1)
        ctk.CTkButton(
            buttons, text="Отмена", fg_color="transparent", border_width=1,
            text_color=("#333333", "#dddddd"), command=self._cancel,
        ).grid(row=0, column=0, sticky="ew", padx=(0, 6))
        ctk.CTkButton(buttons, text=confirm_text, command=self._confirm).grid(
            row=0, column=1, sticky="ew", padx=(6, 0)
        )

    def _confirm(self) -> None:
        self.result = "confirm"
        self.destroy()


class MessageDialog(_Modal):
    def __init__(self, parent, title: str, message: str, hint: str = "", error: bool = False):
        height = 300 if hint else 230
        super().__init__(parent, title, 540, height)
        self.grid_columnconfigure(0, weight=1)
        ctk.CTkLabel(
            self,
            text=title,
            font=ctk.CTkFont(size=18, weight="bold"),
            anchor="w",
            text_color=("#b91c1c", "#f87171") if error else None,
        ).grid(row=0, column=0, sticky="ew", padx=24, pady=(24, 8))
        ctk.CTkLabel(
            self,
            text=message,
            wraplength=480,
            justify="left",
            anchor="w",
        ).grid(row=1, column=0, sticky="ew", padx=24)
        if hint:
            ctk.CTkLabel(
                self,
                text=hint,
                wraplength=480,
                justify="left",
                anchor="w",
                text_color=MUTED,
            ).grid(row=2, column=0, sticky="ew", padx=24, pady=(10, 0))
        ctk.CTkButton(self, text="Закрыть", command=self.destroy).grid(
            row=3, column=0, sticky="ew", padx=24, pady=(18, 20)
        )


def ask_overwrite(parent, path: Path, suggested: Path) -> str | None:
    dialog = OverwriteDialog(parent, path, suggested)
    parent.wait_window(dialog)
    return dialog.result


def ask_confirm(parent, title: str, message: str, confirm_text: str = "Продолжить") -> bool:
    dialog = ConfirmDialog(parent, title, message, confirm_text)
    parent.wait_window(dialog)
    return dialog.result == "confirm"


def show_message(parent, title: str, message: str, hint: str = "", error: bool = False) -> None:
    dialog = MessageDialog(parent, title, message, hint, error)
    parent.wait_window(dialog)
