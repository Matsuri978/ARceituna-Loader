"""Perfil de usuario, ajustes de idioma y modo oscuro.

Modulo que contiene la vista ProfileView con informacion del usuario,
selector de idioma, switch de modo oscuro y boton de cerrar sesion.
"""

import tkinter as tk

from desktop_app.app import theme
from desktop_app.scripts import session_store
from desktop_app.scripts.translator import (
    get_available_languages, get_current_language, set_current_language, t,
)


class ProfileView(tk.Frame):
    """Vista de perfil con datos de usuario y ajustes."""

    def __init__(self, master, state):
        super().__init__(master, padx=32, pady=32, bg=theme.BG_ROOT)
        self.master = master
        self.state = state

        self.grid_columnconfigure(0, weight=1)

        header = tk.Frame(self, bg=theme.BG_ROOT)
        header.grid(row=0, column=0, sticky="ew", pady=(0, 24))
        header.grid_columnconfigure(0, weight=1)

        tk.Label(
            header, text=t("profile.title"), font=theme.FONT_TITLE_M,
            fg=theme.TEXT_TITLE, bg=theme.BG_ROOT,
        ).grid(row=0, column=0, sticky="w")

        self.lang_dropdown = theme.LanguageDropdown(
            header,
            languages=get_available_languages(),
            current_code=get_current_language(),
            on_change=self._on_language_change,
        )
        self.lang_dropdown.grid(row=0, column=1, sticky="e")

        card = tk.Frame(self, bg=theme.BG_PANEL, relief="solid", borderwidth=1)
        card.grid(row=1, column=0, sticky="ew", pady=(0, 20))
        card.grid_columnconfigure(0, weight=1)

        inner = tk.Frame(card, bg=theme.BG_PANEL, padx=24, pady=20)
        inner.grid(row=0, column=0, sticky="nsew")
        inner.grid_columnconfigure(0, weight=1)

        tk.Label(
            inner, text=t("profile.full_name") + ":", font=theme.FONT_SMALL_BOLD,
            fg=theme.TEXT_SECONDARY, bg=theme.BG_PANEL,
        ).grid(row=0, column=0, sticky="w", pady=(0, 2))
        tk.Label(
            inner, text=self.state.user_full_name or "-",
            font=theme.FONT_BODY, fg=theme.TEXT_PRIMARY, bg=theme.BG_PANEL,
        ).grid(row=1, column=0, sticky="w", pady=(0, 16))

        tk.Label(
            inner, text=t("profile.email") + ":", font=theme.FONT_SMALL_BOLD,
            fg=theme.TEXT_SECONDARY, bg=theme.BG_PANEL,
        ).grid(row=2, column=0, sticky="w", pady=(0, 2))
        tk.Label(
            inner, text=self.state.user_email or "-",
            font=theme.FONT_BODY, fg=theme.TEXT_PRIMARY, bg=theme.BG_PANEL,
        ).grid(row=3, column=0, sticky="w", pady=(0, 16))

        tk.Label(
            inner, text=t("profile.role") + ":", font=theme.FONT_SMALL_BOLD,
            fg=theme.TEXT_SECONDARY, bg=theme.BG_PANEL,
        ).grid(row=4, column=0, sticky="w", pady=(0, 2))
        tk.Label(
            inner, text=t("profile.role_value"),
            font=theme.FONT_BODY, fg=theme.TEXT_PRIMARY, bg=theme.BG_PANEL,
        ).grid(row=5, column=0, sticky="w", pady=(0, 16))

        dark_row = tk.Frame(inner, bg=theme.BG_PANEL)
        dark_row.grid(row=6, column=0, sticky="w", pady=(0, 4))
        tk.Label(
            dark_row, text=t("profile.dark_mode") + ":", font=theme.FONT_SMALL_BOLD,
            fg=theme.TEXT_SECONDARY, bg=theme.BG_PANEL,
        ).pack(side="left")
        self.dark_switch = theme.DarkModeSwitch(
            dark_row, command=self._on_dark_mode_toggle, bg=theme.BG_PANEL,
        )
        self.dark_switch.pack(side="left", padx=(12, 0))

        actions = tk.Frame(self, bg=theme.BG_ROOT)
        actions.grid(row=2, column=0, sticky="ew")
        actions.grid_columnconfigure(0, weight=1)

        theme.RoundedButton(
            actions, text=t("profile.back"), command=self.master.show_loader,
            bg=theme.BTN_PRIMARY, fg="#ffffff",
            activebackground=theme.BTN_PRIMARY_HOVER, font=theme.FONT_BODY,
            width=120, height=34,
        ).grid(row=0, column=1, padx=(0, 8))

        theme.RoundedButton(
            actions, text=t("profile.logout"), command=self._confirm_logout,
            bg=theme.BTN_DANGER, fg="#ffffff",
            activebackground="#a11d1d", font=theme.FONT_BODY,
            width=130, height=34,
        ).grid(row=0, column=2)

    def _on_language_change(self, lang_code):
        """Cambia el idioma de la aplicacion y recarga la vista."""
        set_current_language(lang_code)
        session_store.save_language(lang_code)
        self.master.title(t("app.title"))
        self.master.show_profile()

    def _on_dark_mode_toggle(self, is_dark):
        """Activa o desactiva el modo oscuro."""
        theme.set_dark_mode(is_dark)
        session_store.save_dark_mode(is_dark)
        self.master.refresh_current_view()

    def _confirm_logout(self):
        """Solicita confirmacion antes de cerrar sesion."""
        if theme.ask_yes_no(t("profile.logout"), t("profile.logout_confirm")):
            self.master.logout()
