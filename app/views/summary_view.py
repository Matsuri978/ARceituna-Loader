"""Resumen final de la carga de archivos.

Modulo que contiene la vista SummaryView que muestra las metricas
finales del procesamiento y el log completo.
"""

import tkinter as tk

from desktop_app.app import theme
from desktop_app.scripts.translator import t


class SummaryView(tk.Frame):
    """Vista de resumen con metricas y log detallado."""

    def __init__(self, master, state):
        super().__init__(master, padx=32, pady=32, bg=theme.BG_ROOT)
        self.master = master
        self.state = state
        self.summary = state.summary

        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(2, weight=1)

        tk.Label(
            self, text=t("summary.title"), font=theme.FONT_TITLE_M,
            fg=theme.TEXT_TITLE, bg=theme.BG_ROOT,
        ).grid(row=0, column=0, sticky="w", pady=(0, 18))

        stats = tk.Frame(self, bg=theme.BG_ROOT)
        stats.grid(row=1, column=0, sticky="ew", pady=(0, 18))

        self._stat(stats, 0, 0, t("summary.files_processed"), self.summary.files_processed)
        self._stat(stats, 0, 1, t("summary.parcels_detected"), self.summary.parcels_detected)
        self._stat(stats, 0, 2, t("summary.enclosures_detected"), self.summary.enclosures_detected)
        self._stat(stats, 1, 0, t("summary.parcels_inserted"), self.summary.parcels_inserted)
        self._stat(stats, 1, 1, t("summary.enclosures_inserted"), self.summary.enclosures_inserted)
        self._stat(stats, 1, 2, t("summary.errors"), len(self.summary.errors))

        log_frame = tk.LabelFrame(
            self, text=t("summary.detail"),
            bg=theme.BG_PANEL, fg=theme.TEXT_TITLE, font=theme.FONT_SMALL_BOLD,
            relief="solid", borderwidth=1,
        )
        log_frame.grid(row=2, column=0, sticky="nsew")
        log_frame.grid_rowconfigure(0, weight=1)
        log_frame.grid_columnconfigure(0, weight=1)

        log_text = tk.Text(
            log_frame, wrap="word",
            bg=theme.BG_CONTENT, fg=theme.TEXT_PRIMARY, font=theme.FONT_SMALL,
            insertbackground=theme.TEXT_PRIMARY, relief="flat", borderwidth=0,
        )
        log_text.grid(row=0, column=0, sticky="nsew", padx=8, pady=8)
        log_text.insert(tk.END, "\n".join(self.state.log_lines))
        log_text.configure(state="disabled")

        actions = tk.Frame(self, bg=theme.BG_ROOT)
        actions.grid(row=3, column=0, sticky="e", pady=(18, 0))

        back_btn = theme.RoundedButton(
            actions, text=t("summary.back"), command=self.master.show_loader,
            bg=theme.BTN_PRIMARY, fg="#ffffff",
            activebackground=theme.BTN_PRIMARY_HOVER, font=theme.FONT_BODY,
            width=120, height=34,
        )
        back_btn.grid(row=0, column=0, padx=(0, 8))

        quit_btn = theme.RoundedButton(
            actions, text=t("summary.quit"), command=self.master.destroy,
            bg=theme.BTN_PRIMARY, fg="#ffffff",
            activebackground=theme.BTN_PRIMARY_HOVER, font=theme.FONT_BODY,
            width=100, height=34,
        )
        quit_btn.grid(row=0, column=1)

    def _stat(self, parent, row, column, label, value):
        """Crea una tarjeta de estadistica con valor y etiqueta."""
        frame = tk.Frame(
            parent, padx=12, pady=10, bg=theme.BG_PANEL,
            relief="solid", borderwidth=1,
        )
        frame.grid(row=row, column=column, sticky="nsew", padx=(0, 8), pady=(0, 8))
        parent.grid_columnconfigure(column, weight=1)

        tk.Label(
            frame, text=str(value), font=theme.FONT_STAT_VALUE,
            fg=theme.TEXT_TITLE, bg=theme.BG_PANEL,
        ).grid(row=0, column=0, sticky="w")
        tk.Label(
            frame, text=label, fg=theme.TEXT_SECONDARY, font=theme.FONT_SMALL,
            bg=theme.BG_PANEL,
        ).grid(row=1, column=0, sticky="w")
