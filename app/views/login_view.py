"""Pantalla de inicio de sesion y registro de usuarios.

Modulo que contiene la vista LoginView con formularios de login y registro,
selector de idioma y switch de modo oscuro.
"""

import tkinter as tk

from desktop_app.app import theme
from desktop_app.scripts import session_store
from desktop_app.scripts.supabase_client import SupabaseError
from desktop_app.scripts.translator import (
    get_available_languages, get_current_language, set_current_language, t,
)


class LoginView(tk.Frame):
    """Vista de login con pestanas de inicio de sesion y registro."""

    def __init__(self, master, state):
        super().__init__(master, padx=32, pady=32, bg=theme.BG_ROOT)
        self.master = master
        self.state = state

        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(0, weight=1)

        self.lang_dropdown = theme.LanguageDropdown(
            self,
            languages=get_available_languages(),
            current_code=get_current_language(),
            on_change=self._on_language_change,
        )
        self.lang_dropdown.place(x=0, y=0)

        self.dark_switch = theme.DarkModeSwitch(
            self, command=self._on_dark_mode_toggle, bg=theme.BG_ROOT,
        )
        self.dark_switch.place(relx=1.0, x=0, y=0, anchor="ne")

        panel = tk.Frame(self, bg=theme.BG_ROOT)
        panel.grid(row=0, column=0)

        header_row = tk.Frame(panel, bg=theme.BG_ROOT)
        header_row.grid(row=0, column=0, sticky="ew", pady=(0, 4))

        title = tk.Label(
            header_row, text=t("login.title"), font=theme.FONT_TITLE_L,
            fg=theme.TEXT_TITLE, bg=theme.BG_ROOT,
        )
        title.grid(row=0, column=0)

        subtitle = tk.Label(
            header_row, text=t("login.subtitle"),
            font=theme.FONT_SUBTITLE,
            fg=theme.TEXT_SECONDARY, bg=theme.BG_ROOT,
        )
        subtitle.grid(row=1, column=0, columnspan=2, sticky="w", pady=(4, 24))

        self.notebook = tk.Frame(panel, bg=theme.BG_PANEL, relief="solid", borderwidth=1)
        self.notebook.grid(row=2, column=0, columnspan=2, sticky="ew")

        self.tab_bar = tk.Frame(self.notebook, bg=theme.BTN_SECONDARY)
        self.tab_bar.pack(fill="x")

        self.login_tab_btn = tk.Label(
            self.tab_bar, text=t("login.tab_login"), font=theme.FONT_BODY,
            bg=theme.BTN_PRIMARY, fg="#ffffff", padx=16, pady=6, cursor="hand2",
        )
        self.login_tab_btn.pack(side="left")
        self.register_tab_btn = tk.Label(
            self.tab_bar, text=t("login.tab_register"), font=theme.FONT_BODY,
            bg=theme.BTN_SECONDARY, fg=theme.TEXT_PRIMARY, padx=16, pady=6, cursor="hand2",
        )
        self.register_tab_btn.pack(side="left")

        self.tab_content = tk.Frame(self.notebook, bg=theme.BG_PANEL, padx=16, pady=16)
        self.tab_content.pack(fill="both", expand=True)
        self.tab_content.grid_columnconfigure(0, weight=1)

        self._build_login_tab()
        self._build_register_tab()

        self._show_login_tab()

        note = tk.Label(
            panel, text=t("login.session_info"),
            font=theme.FONT_SMALL, fg=theme.TEXT_SECONDARY, bg=theme.BG_ROOT,
        )
        note.grid(row=4, column=0, columnspan=2, sticky="w", pady=(20, 0))

        if getattr(self.master, "auth_startup_error", ""):
            config_warning = tk.Label(
                panel, text=self.master.auth_startup_error,
                font=theme.FONT_SMALL, fg=theme.TEXT_ERROR, bg=theme.BG_ROOT,
                wraplength=420, justify="left",
            )
            config_warning.grid(row=5, column=0, columnspan=2, sticky="w", pady=(10, 0))

    def _build_login_tab(self):
        """Construye el formulario de inicio de sesion."""
        self.login_frame = tk.Frame(self.tab_content, bg=theme.BG_PANEL)
        self.login_frame.grid_columnconfigure(0, weight=1)

        tk.Label(self.login_frame, text=t("login.email"), font=theme.FONT_SMALL,
                 fg=theme.TEXT_PRIMARY, bg=theme.BG_PANEL).grid(row=0, column=0, sticky="w", pady=(0, 4))
        self.login_email_entry = tk.Entry(
            self.login_frame, width=42, font=theme.FONT_BODY, bg=theme.BG_CONTENT,
            fg=theme.TEXT_PRIMARY, insertbackground=theme.TEXT_PRIMARY,
            relief="solid", borderwidth=1,
        )
        self.login_email_entry.grid(row=1, column=0, sticky="ew", pady=(0, 12))

        tk.Label(self.login_frame, text=t("login.password"), font=theme.FONT_SMALL,
                 fg=theme.TEXT_PRIMARY, bg=theme.BG_PANEL).grid(row=2, column=0, sticky="w", pady=(0, 4))
        self.login_password_entry = tk.Entry(
            self.login_frame, width=42, show="*", font=theme.FONT_BODY, bg=theme.BG_CONTENT,
            fg=theme.TEXT_PRIMARY, insertbackground=theme.TEXT_PRIMARY,
            relief="solid", borderwidth=1,
        )
        self.login_password_entry.grid(row=3, column=0, sticky="ew", pady=(0, 18))

        theme.RoundedButton(
            self.login_frame, text=t("login.submit"), command=self._login,
            bg=theme.BTN_PRIMARY, fg="#ffffff", activebackground=theme.BTN_PRIMARY_HOVER,
            font=theme.FONT_BODY, width=380, height=34,
        ).grid(row=4, column=0, sticky="ew")

    def _build_register_tab(self):
        """Construye el formulario de registro de usuario."""
        self.register_frame = tk.Frame(self.tab_content, bg=theme.BG_PANEL)
        self.register_frame.grid_columnconfigure(0, weight=1)

        tk.Label(self.register_frame, text=t("register.name"), font=theme.FONT_SMALL,
                 fg=theme.TEXT_PRIMARY, bg=theme.BG_PANEL).grid(row=0, column=0, sticky="w", pady=(0, 4))
        self.register_name_entry = tk.Entry(
            self.register_frame, width=42, font=theme.FONT_BODY, bg=theme.BG_CONTENT,
            fg=theme.TEXT_PRIMARY, insertbackground=theme.TEXT_PRIMARY,
            relief="solid", borderwidth=1,
        )
        self.register_name_entry.grid(row=1, column=0, sticky="ew", pady=(0, 12))

        tk.Label(self.register_frame, text=t("register.surname"), font=theme.FONT_SMALL,
                 fg=theme.TEXT_PRIMARY, bg=theme.BG_PANEL).grid(row=2, column=0, sticky="w", pady=(0, 4))
        self.register_surname_entry = tk.Entry(
            self.register_frame, width=42, font=theme.FONT_BODY, bg=theme.BG_CONTENT,
            fg=theme.TEXT_PRIMARY, insertbackground=theme.TEXT_PRIMARY,
            relief="solid", borderwidth=1,
        )
        self.register_surname_entry.grid(row=3, column=0, sticky="ew", pady=(0, 12))

        tk.Label(self.register_frame, text=t("register.email"), font=theme.FONT_SMALL,
                 fg=theme.TEXT_PRIMARY, bg=theme.BG_PANEL).grid(row=4, column=0, sticky="w", pady=(0, 4))
        self.register_email_entry = tk.Entry(
            self.register_frame, width=42, font=theme.FONT_BODY, bg=theme.BG_CONTENT,
            fg=theme.TEXT_PRIMARY, insertbackground=theme.TEXT_PRIMARY,
            relief="solid", borderwidth=1,
        )
        self.register_email_entry.grid(row=5, column=0, sticky="ew", pady=(0, 12))

        tk.Label(self.register_frame, text=t("register.password"), font=theme.FONT_SMALL,
                 fg=theme.TEXT_PRIMARY, bg=theme.BG_PANEL).grid(row=6, column=0, sticky="w", pady=(0, 4))
        self.register_password_entry = tk.Entry(
            self.register_frame, width=42, show="*", font=theme.FONT_BODY, bg=theme.BG_CONTENT,
            fg=theme.TEXT_PRIMARY, insertbackground=theme.TEXT_PRIMARY,
            relief="solid", borderwidth=1,
        )
        self.register_password_entry.grid(row=7, column=0, sticky="ew", pady=(0, 18))

        theme.RoundedButton(
            self.register_frame, text=t("register.submit"), command=self._register,
            bg=theme.BTN_PRIMARY, fg="#ffffff", activebackground=theme.BTN_PRIMARY_HOVER,
            font=theme.FONT_BODY, width=380, height=34,
        ).grid(row=8, column=0, sticky="ew")

    def _show_login_tab(self):
        """Muestra la pestana de login y oculta la de registro."""
        self.register_frame.grid_forget()
        self.login_frame.grid(row=0, column=0, sticky="ew")
        self.login_tab_btn.configure(bg=theme.BTN_PRIMARY, fg="#ffffff")
        self.register_tab_btn.configure(bg=theme.BTN_SECONDARY, fg=theme.TEXT_PRIMARY)
        self.login_tab_btn.bind("<Button-1>", lambda e: self._show_login_tab())
        self.register_tab_btn.bind("<Button-1>", lambda e: self._show_register_tab())

    def _show_register_tab(self):
        """Muestra la pestana de registro y oculta la de login."""
        self.login_frame.grid_forget()
        self.register_frame.grid(row=0, column=0, sticky="ew")
        self.register_tab_btn.configure(bg=theme.BTN_PRIMARY, fg="#ffffff")
        self.login_tab_btn.configure(bg=theme.BTN_SECONDARY, fg=theme.TEXT_PRIMARY)
        self.register_tab_btn.bind("<Button-1>", lambda e: self._show_register_tab())
        self.login_tab_btn.bind("<Button-1>", lambda e: self._show_login_tab())

    def _on_language_change(self, lang_code):
        """Cambia el idioma de la aplicacion y recarga la vista."""
        set_current_language(lang_code)
        session_store.save_language(lang_code)
        self.master.title(t("app.title"))
        self.master.show_login()

    def _on_dark_mode_toggle(self, is_dark):
        """Activa o desactiva el modo oscuro."""
        theme.set_dark_mode(is_dark)
        session_store.save_dark_mode(is_dark)
        self.master.refresh_current_view()

    def _login(self):
        """Ejecuta el inicio de sesion con las credenciales proporcionadas."""
        email = self.login_email_entry.get().strip()
        password = self.login_password_entry.get()

        if not email or not password:
            theme.show_warning(t("login.email"), t("login.email"))
            return

        if self.master.supabase_client is None:
            theme.show_error("Supabase", self.master.auth_startup_error)
            return

        try:
            session = self.master.supabase_client.sign_in(email, password)
            self.master.supabase_client.create_field_manager_profile()
        except SupabaseError as exc:
            theme.show_error(t("login.tab_login"), str(exc))
            return

        session_store.save_session(self.master.supabase_client.current_session())
        self.state.set_user_from_supabase(session.get("user") or {})
        theme.show_info(t("login.success"), t("login.success_msg"))
        self.master.show_loader()

    def _register(self):
        """Registra un nuevo usuario con los datos del formulario."""
        name = self.register_name_entry.get().strip()
        surnames = self.register_surname_entry.get().strip()
        email = self.register_email_entry.get().strip()
        password = self.register_password_entry.get()

        if not name or not surnames or not email or not password:
            theme.show_warning(t("register.name"), t("register.name"))
            return

        if self.master.supabase_client is None:
            theme.show_error("Supabase", self.master.auth_startup_error)
            return

        try:
            session = self.master.supabase_client.sign_up(email, password, name, surnames)
            if self.master.supabase_client.is_authenticated:
                self.master.supabase_client.create_field_manager_profile()
        except SupabaseError as exc:
            theme.show_error(t("register.submit"), str(exc))
            return

        if not self.master.supabase_client.is_authenticated:
            theme.show_info(t("register.confirm_email"), t("register.confirm_email_msg"))
            return

        session_store.save_session(self.master.supabase_client.current_session())
        self.state.set_user_from_supabase(session.get("user") or {})
        theme.show_info(t("register.success"), t("register.success_msg"))
        self.master.show_loader()
