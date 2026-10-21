from __future__ import annotations

import customtkinter as ctk

CARD_COLOR = ("#ffffff", "#1a1a1e")
CARD_BORDER = ("#d9d9e3", "#2b2b31")
MUTED = ("#6b6b76", "#9a9aa5")
ACCENT = ("#2563eb", "#4f8cff")


class SectionCard(ctk.CTkFrame):
    def __init__(self, master, title: str, subtitle: str | None = None, **kwargs):
        super().__init__(
            master,
            corner_radius=14,
            fg_color=CARD_COLOR,
            border_width=1,
            border_color=CARD_BORDER,
            **kwargs,
        )
        self.grid_columnconfigure(0, weight=1)
        header = ctk.CTkFrame(self, fg_color="transparent")
        header.grid(row=0, column=0, sticky="ew", padx=20, pady=(16, 0))
        header.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(
            header,
            text=title,
            font=ctk.CTkFont(size=15, weight="bold"),
            anchor="w",
        ).grid(row=0, column=0, sticky="w")
        if subtitle:
            ctk.CTkLabel(
                header,
                text=subtitle,
                font=ctk.CTkFont(size=11),
                text_color=MUTED,
                anchor="w",
            ).grid(row=1, column=0, sticky="w", pady=(2, 0))

        self.body = ctk.CTkFrame(self, fg_color="transparent")
        self.body.grid(row=1, column=0, sticky="nsew", padx=20, pady=(12, 18))
        self.body.grid_columnconfigure(1, weight=1)


class StatusDot(ctk.CTkLabel):
    COLORS = {
        "idle": ("#9aa0aa", "#6f7480"),
        "working": ("#d97706", "#fbbf24"),
        "success": ("#15803d", "#4ade80"),
        "error": ("#b91c1c", "#f87171"),
    }

    def __init__(self, master):
        super().__init__(master, text="●", font=ctk.CTkFont(size=16), text_color=self.COLORS["idle"])

    def set_state(self, state: str) -> None:
        self.configure(text_color=self.COLORS.get(state, self.COLORS["idle"]))
