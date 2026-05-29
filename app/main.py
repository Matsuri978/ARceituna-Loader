"""Ventana principal de la aplicacion Tkinter.

Modulo que contiene la clase principal GeojsonLoaderApp, la cual gestiona
las vistas, el estado global y la conexion con Supabase.
"""

import tkinter as tk

from desktop_app.app.state import AppState
from desktop_app.app.theme import apply_theme
from desktop_app.app.views.load_view import LoadView
from desktop_app.app.views.login_view import LoginView
from desktop_app.app.views.processing_view import ProcessingView
from desktop_app.app.views.profile_view import ProfileView

from desktop_app.scripts import session_store
from desktop_app.scripts.supabase_client import SupabaseClient, SupabaseError
from desktop_app.scripts.translator import set_current_language, load_language
from desktop_app.app import theme


class GeojsonLoaderApp(tk.Tk):
    """App principal que gestiona las vistas, el estado y la autenticacion."""

    def __init__(self):
        super().__init__()

        saved_lang = session_store.load_language()
        set_current_language(saved_lang)

        saved_dark = session_store.load_dark_mode()
        theme.set_dark_mode(saved_dark)

        from desktop_app.scripts.translator import t
        self.title(t("app.title"))
        self.geometry("900x620")
        self.minsize(780, 520)

        apply_theme(self)

        self.state_data = AppState()
        self.current_view = None
        self._current_view_class = None
        self.supabase_client = None

        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(0, weight=1)

        self._initialize_supabase()
        self._restore_or_show_login()

    def _show_view(self, view_class):
        """Muestra una vista reemplazando la actual."""
        self._current_view_class = view_class
        if self.current_view is not None:
            self.current_view.destroy()

        self.current_view = view_class(self, self.state_data)
        self.current_view.grid(row=0, column=0, sticky="nsew")

    def refresh_current_view(self):
        """Refresca la vista actual, recargando el tema."""
        if self._current_view_class:
            apply_theme(self)
            self._show_view(self._current_view_class)

    def show_login(self):
        """Muestra la pantalla de inicio de sesion."""
        self._show_view(LoginView)

    def show_loader(self):
        """Muestra el selector de archivos GeoJSON."""
        self._show_view(LoadView)

    def show_processing(self):
        """Muestra la vista de procesamiento en tiempo real."""
        self._show_view(ProcessingView)

    def show_profile(self):
        """Muestra el perfil de usuario y ajustes."""
        self._show_view(ProfileView)

    def logout(self):
        """Cierra la sesion del usuario y limpia el estado."""
        session_store.clear_session()
        if self.supabase_client is not None:
            self.supabase_client.sign_out_local()
        self.state_data.clear_user()
        self.state_data.selected_files.clear()
        self.show_login()

    def _initialize_supabase(self):
        """Inicializa el cliente Supabase, capturando errores de conexion."""
        try:
            self.supabase_client = SupabaseClient()
        except Exception as exc:
            self.supabase_client = None
            self.auth_startup_error = str(exc)
        else:
            self.auth_startup_error = ""

    def _restore_or_show_login(self):
        """Restaura la sesion guardada o muestra el login si no hay sesion."""
        if self.supabase_client is None:
            self.show_login()
            return

        session = session_store.load_session()
        refresh_token = (session or {}).get("refresh_token", "")
        # Si no hay refresh token, la sesion no se puede restaurar
        if not refresh_token:
            self.show_login()
            return

        try:
            refreshed = self.supabase_client.refresh_session(refresh_token)
        except SupabaseError:
            # Error al refrescar sesion: limpiar y mostrar login
            session_store.clear_session()
            self.show_login()
            return

        session_store.save_session(refreshed)
        self.state_data.set_user_from_supabase(refreshed.get("user") or {})
        self.show_loader()


def main():
    """Punto de entrada principal de la aplicacion."""
    app = GeojsonLoaderApp()
    app.mainloop()
    theme.cleanup_fonts()


if __name__ == "__main__":
    main()
