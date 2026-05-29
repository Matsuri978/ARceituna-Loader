"""Tema visual, estilos, colores y widgets personalizados.

Modulo que define constantes de colores, fuentes, estilos ttk y widgets
personalizados como RoundedButton, GreenCheckbox, LanguageDropdown y DarkModeSwitch.
Proporciona funciones para aplicar el tema y gestionar el modo oscuro.
"""

import ctypes
import ctypes.util
import platform
import sys
import tkinter as tk
from tkinter import font as tkfont
from tkinter import ttk
from pathlib import Path


BG_ROOT = "#f4f7f1"
BG_PANEL = "#ffffff"
BG_CONTENT = "#ffffff"

BTN_PRIMARY = "#388E3C"
BTN_PRIMARY_HOVER = "#2E7D32"
BTN_PRIMARY_ACTIVE = "#1B5E20"
BTN_SECONDARY = "#e8ede4"
BTN_SECONDARY_HOVER = "#dce5d6"
BTN_DANGER = "#c92a2a"

TEXT_PRIMARY = "#2d3a28"
TEXT_SECONDARY = "#6b7c64"
TEXT_TITLE = "#3a4f30"
TEXT_ERROR = "#b42318"

ROW_SELECTED = "#c8ddb8"
ROW_HEADER_BG = "#e8f0de"
ROW_NORMAL = "#ffffff"
ROW_SELECTED_FG = "#2d3a28"

BORDER = "#c5d4bb"
BORDER_LIGHT = "#dde8d4"

STATUS_PENDING_FG = "#8a9a80"
STATUS_PROCESSING_FG = "#5a7a42"
STATUS_DONE_FG = "#3a8a2a"
STATUS_ERROR_FG = "#b42318"

DARK_BG_ROOT = "#1a1a1a"
DARK_BG_PANEL = "#2a2a2a"
DARK_BG_CONTENT = "#2a2a2a"
DARK_BTN_SECONDARY = "#3a3a3a"
DARK_BTN_SECONDARY_HOVER = "#4a4a4a"
DARK_TEXT_PRIMARY = "#e0e0e0"
DARK_TEXT_SECONDARY = "#a0a0a0"
DARK_TEXT_TITLE = "#c8e6c9"
DARK_ROW_SELECTED = "#2e4a2e"
DARK_ROW_HEADER_BG = "#2e3a2e"
DARK_ROW_NORMAL = "#2a2a2a"
DARK_ROW_SELECTED_FG = "#e0e0e0"
DARK_BORDER = "#4a5a4a"
DARK_STATUS_PENDING_FG = "#708070"
DARK_STATUS_DONE_FG = "#66bb6a"
DARK_STATUS_ERROR_FG = "#ef5350"

_dark_mode = False


def set_dark_mode(enabled):
    """Activa o desactiva el modo oscuro global."""
    global _dark_mode
    _dark_mode = enabled
    _apply_colors()


def is_dark_mode():
    """Devuelve True si el modo oscuro esta activado."""
    return _dark_mode


def _apply_colors():
    """Aplica los colores globales segun el modo oscuro/claro."""
    global BG_ROOT, BG_PANEL, BG_CONTENT
    global BTN_SECONDARY, BTN_SECONDARY_HOVER
    global TEXT_PRIMARY, TEXT_SECONDARY, TEXT_TITLE
    global ROW_SELECTED, ROW_HEADER_BG, ROW_NORMAL, ROW_SELECTED_FG
    global BORDER, STATUS_PENDING_FG, STATUS_DONE_FG, STATUS_ERROR_FG

    if _dark_mode:
        BG_ROOT = DARK_BG_ROOT
        BG_PANEL = DARK_BG_PANEL
        BG_CONTENT = DARK_BG_CONTENT
        BTN_SECONDARY = DARK_BTN_SECONDARY
        BTN_SECONDARY_HOVER = DARK_BTN_SECONDARY_HOVER
        TEXT_PRIMARY = DARK_TEXT_PRIMARY
        TEXT_SECONDARY = DARK_TEXT_SECONDARY
        TEXT_TITLE = DARK_TEXT_TITLE
        ROW_SELECTED = DARK_ROW_SELECTED
        ROW_HEADER_BG = DARK_ROW_HEADER_BG
        ROW_NORMAL = DARK_ROW_NORMAL
        ROW_SELECTED_FG = DARK_ROW_SELECTED_FG
        BORDER = DARK_BORDER
        STATUS_PENDING_FG = DARK_STATUS_PENDING_FG
        STATUS_DONE_FG = DARK_STATUS_DONE_FG
        STATUS_ERROR_FG = DARK_STATUS_ERROR_FG
    else:
        BG_ROOT = "#f4f7f1"
        BG_PANEL = "#ffffff"
        BG_CONTENT = "#ffffff"
        BTN_SECONDARY = "#e8ede4"
        BTN_SECONDARY_HOVER = "#dce5d6"
        TEXT_PRIMARY = "#2d3a28"
        TEXT_SECONDARY = "#6b7c64"
        TEXT_TITLE = "#3a4f30"
        ROW_SELECTED = "#c8ddb8"
        ROW_HEADER_BG = "#e8f0de"
        ROW_NORMAL = "#ffffff"
        ROW_SELECTED_FG = "#2d3a28"
        BORDER = "#c5d4bb"
        STATUS_PENDING_FG = "#8a9a80"
        STATUS_DONE_FG = "#3a8a2a"
        STATUS_ERROR_FG = "#b42318"

FONT_TITLE_L = ("Segoe UI", 24, "bold")
FONT_TITLE_M = ("Segoe UI", 20, "bold")
FONT_TITLE_S = ("Segoe UI", 16, "bold")
FONT_SUBTITLE = ("Segoe UI", 11)
FONT_SESSION = ("Segoe UI", 11, "bold")
FONT_BODY = ("Segoe UI", 10)
FONT_SMALL = ("Segoe UI", 9)
FONT_SMALL_BOLD = ("Segoe UI", 9, "bold")
FONT_STAT_VALUE = ("Segoe UI", 16, "bold")

SECTION_SEP = "─" * 40

from desktop_app.scripts.paths import get_data_dir

_FONT_DIR = get_data_dir() / "fonts"

_CJK_FONT_MAP = {
    "ja": ["Yu Gothic", "Meiryo", "Hiragino Sans", "Noto Sans CJK JP"],
    "zh": ["Microsoft YaHei", "PingFang SC", "Noto Sans CJK SC"],
    "ko": ["Malgun Gothic", "Apple SD Gothic Neo", "Noto Sans CJK KR"],
}

_CJK_BUNDLED_MAP = {
    "ja": "NotoSansCJKjp-Regular.otf",
    "zh": "NotoSansCJKsc-Regular.otf",
    "ko": "NotoSansCJKkr-Regular.otf",
}


_LOADED_FONTS = []


def _detect_cjk_font(lang_code):
    """Detecta si hay una fuente CJK disponible en el sistema."""
    try:
        available = set(tkfont.families())
    except Exception:
        return None
    candidates = _CJK_FONT_MAP.get(lang_code, [])
    # Busca la primera fuente candidata que este instalada
    for name in candidates:
        if name in available:
            return name
    return None


def _load_bundled_cjk(lang_code):
    """Carga una fuente CJK incluida en el paquete segun la plataforma."""
    filename = _CJK_BUNDLED_MAP.get(lang_code)
    if not filename:
        return None
    path = _FONT_DIR / filename
    if not path.exists():
        return None

    # Selecciona el metodo de carga segun el sistema operativo
    if sys.platform == "win32":
        return _load_font_windows(path, lang_code)
    else:
        return _load_font_tk(path, lang_code)


def _load_font_windows(path, lang_code):
    """Carga una fuente en Windows usando AddFontResourceExW."""
    try:
        FR_PRIVATE = 0x10
        FR_NOT_ENUM = 0x20
        result = ctypes.windll.gdi32.AddFontResourceExW(
            str(path), FR_PRIVATE | FR_NOT_ENUM, 0
        )
        if result > 0:
            _LOADED_FONTS.append((str(path), FR_PRIVATE | FR_NOT_ENUM))
            return f"Noto Sans CJK {'JP' if lang_code == 'ja' else 'SC' if lang_code == 'zh' else 'KR'}"
    except Exception:
        pass
    return None


def _load_font_tk(path, lang_code):
    """Carga una fuente en plataformas no Windows usando Tk."""
    try:
        root = tk._get_default_root()
        if root is None:
            root = tk.Tk()
            root.withdraw()
        font_name = f"CJK_{lang_code}"
        root.tk.call("font", "create", font_name, "-file", str(path))
        return font_name
    except Exception:
        # Si falla la carga directa, intenta instalar en Linux
        return _install_font_linux(path, lang_code)


def _install_font_linux(path, lang_code):
    """Instala una fuente CJK en el directorio local del usuario en Linux."""
    try:
        dest_dir = Path.home() / ".local" / "share" / "fonts"
        dest_dir.mkdir(parents=True, exist_ok=True)
        dest = dest_dir / path.name
        if not dest.exists():
            import shutil
            shutil.copy2(str(path), str(dest))
        _run_fc_cache()
        font_names = {
            "ja": "Noto Sans CJK JP",
            "zh": "Noto Sans CJK SC",
            "ko": "Noto Sans CJK KR",
        }
        return font_names.get(lang_code)
    except Exception:
        return None


def _run_fc_cache():
    """Ejecuta fc-cache para actualizar la cache de fuentes en Linux."""
    import subprocess
    try:
        subprocess.run(
            ["fc-cache", "-f", str(Path.home() / ".local" / "share" / "fonts")],
            capture_output=True, timeout=10,
        )
    except Exception:
        pass


def _remove_installed_fonts():
    dest_dir = Path.home() / ".local" / "share" / "fonts"
    if not dest_dir.exists():
        return
    try:
        for filename in _CJK_BUNDLED_MAP.values():
            target = dest_dir / filename
            if target.exists():
                target.unlink()
        _run_fc_cache()
    except Exception:
        pass


def cleanup_fonts():
    """Libera las fuentes cargadas en Windows."""
    if sys.platform == "win32":
        for path, flags in _LOADED_FONTS:
            try:
                ctypes.windll.gdi32.RemoveFontResourceExW(path, flags, 0)
            except Exception:
                pass
    _LOADED_FONTS.clear()


def uninstall_fonts():
    """Libera fuentes en Windows y elimina fuentes instaladas en Linux."""
    cleanup_fonts()
    if sys.platform != "win32":
        _remove_installed_fonts()


def ask_yes_no(title, message):
    """Muestra un dialogo de confirmacion Si/No."""
    import desktop_app.scripts.translator as _tr
    t = _tr.t
    dialog = tk.Toplevel()
    dialog.title(title)
    dialog.transient(dialog.master or tk._get_default_root())
    dialog.grab_set()
    dialog.configure(bg=BG_PANEL)
    dialog.resizable(False, False)

    msg_label = tk.Label(
        dialog, text=message, font=FONT_BODY,
        fg=TEXT_PRIMARY, bg=BG_PANEL, wraplength=380, justify="left",
        padx=20, pady=10,
    )
    msg_label.pack()

    btn_frame = tk.Frame(dialog, bg=BG_PANEL)
    btn_frame.pack(pady=(0, 16))

    result = [False]

    def on_yes():
        result[0] = True
        dialog.destroy()

    def on_no():
        dialog.destroy()

    yes_btn = RoundedButton(
        btn_frame, text=t("dialog.yes"), command=on_yes,
        bg=BTN_PRIMARY, fg="#ffffff", activebackground=BTN_PRIMARY_HOVER,
        width=80, height=30,
    )
    yes_btn.pack(side="left", padx=(0, 8))

    no_btn = RoundedButton(
        btn_frame, text=t("dialog.no"), command=on_no,
        bg=BTN_SECONDARY, fg=TEXT_PRIMARY, activebackground=BTN_SECONDARY_HOVER,
        width=80, height=30,
    )
    no_btn.pack(side="left")

    dialog.update_idletasks()
    w = dialog.winfo_width()
    h = dialog.winfo_height()
    # Centrar el dialogo sobre la ventana padre o la pantalla
    root = dialog.master or tk._get_default_root()
    if root:
        x = root.winfo_rootx() + (root.winfo_width() - w) // 2
        y = root.winfo_rooty() + (root.winfo_height() - h) // 2
    else:
        x = (dialog.winfo_screenwidth() - w) // 2
        y = (dialog.winfo_screenheight() - h) // 2
    dialog.geometry(f"+{x}+{y}")

    dialog.wait_window()
    return result[0]


def show_info(title, message):
    """Muestra un dialogo informativo con boton OK."""
    _show_single_button_dialog(title, message, BTN_PRIMARY, BTN_PRIMARY_HOVER)


def show_warning(title, message):
    """Muestra un dialogo de advertencia."""
    _show_single_button_dialog(title, message, BTN_SECONDARY, BTN_SECONDARY_HOVER)


def show_error(title, message):
    """Muestra un dialogo de error critico."""
    _show_single_button_dialog(title, message, BTN_DANGER, "#a11d1d")


def _show_single_button_dialog(title, message, btn_bg, btn_hover):
    import desktop_app.scripts.translator as _tr
    t = _tr.t
    dialog = tk.Toplevel()
    dialog.title(title)
    dialog.transient(dialog.master or tk._get_default_root())
    dialog.grab_set()
    dialog.configure(bg=BG_PANEL)
    dialog.resizable(False, False)

    msg_label = tk.Label(
        dialog, text=message, font=FONT_BODY,
        fg=TEXT_PRIMARY, bg=BG_PANEL, wraplength=380, justify="left",
        padx=20, pady=10,
    )
    msg_label.pack()

    btn_frame = tk.Frame(dialog, bg=BG_PANEL)
    btn_frame.pack(pady=(0, 16))

    ok_btn = RoundedButton(
        btn_frame, text=t("dialog.ok"), command=dialog.destroy,
        bg=btn_bg, fg="#ffffff", activebackground=btn_hover,
        width=80, height=30,
    )
    ok_btn.pack()

    dialog.update_idletasks()
    w = dialog.winfo_width()
    h = dialog.winfo_height()
    root = dialog.master or tk._get_default_root()
    if root:
        x = root.winfo_rootx() + (root.winfo_width() - w) // 2
        y = root.winfo_rooty() + (root.winfo_height() - h) // 2
    else:
        x = (dialog.winfo_screenwidth() - w) // 2
        y = (dialog.winfo_screenheight() - h) // 2
    dialog.geometry(f"+{x}+{y}")

    dialog.wait_window()


def set_font_for_language(lang_code):
    """Configura las fuentes globales segun el idioma (soporte CJK)."""
    global FONT_TITLE_L, FONT_TITLE_M, FONT_TITLE_S
    global FONT_SUBTITLE, FONT_SESSION, FONT_BODY
    global FONT_SMALL, FONT_SMALL_BOLD, FONT_STAT_VALUE

    cjk = _detect_cjk_font(lang_code)
    if not cjk:
        cjk = _load_bundled_cjk(lang_code)
    base = cjk if cjk else "Segoe UI"

    FONT_TITLE_L = (base, 24, "bold")
    FONT_TITLE_M = (base, 20, "bold")
    FONT_TITLE_S = (base, 16, "bold")
    FONT_SUBTITLE = (base, 11)
    FONT_SESSION = (base, 11, "bold")
    FONT_BODY = (base, 10)
    FONT_SMALL = (base, 9)
    FONT_SMALL_BOLD = (base, 9, "bold")
    FONT_STAT_VALUE = (base, 16, "bold")


class RoundedButton(tk.Canvas):
    """Boton con esquinas redondeadas dibujado en Canvas."""

    def __init__(self, parent, text="", command=None, bg=BTN_PRIMARY, fg="#ffffff",
                 activebackground=BTN_PRIMARY_HOVER, font=FONT_BODY,
                 width=120, height=32, radius=10, **kwargs):
        super().__init__(parent, width=width, height=height,
                         bg=parent.cget("bg") if isinstance(parent, (tk.Frame, tk.Tk)) else BG_ROOT,
                         highlightthickness=0, **kwargs)
        self._command = command
        self._bg = bg
        self._fg = fg
        self._active_bg = activebackground
        self._font = font
        self._width = width
        self._height = height
        self._radius = radius
        self._text = text

        self._draw(bg)
        self.bind("<Button-1>", self._on_click)
        self.bind("<Enter>", self._on_enter)
        self.bind("<Leave>", self._on_leave)

    def _round_rect(self, x1, y1, x2, y2, r, **kwargs):
        points = [
            x1 + r, y1,
            x2 - r, y1,
            x2, y1,
            x2, y1 + r,
            x2, y2 - r,
            x2, y2,
            x2 - r, y2,
            x1 + r, y2,
            x1, y2,
            x1, y2 - r,
            x1, y1 + r,
            x1, y1,
        ]
        return self.create_polygon(points, smooth=True, **kwargs)

    def _draw(self, bg):
        self.delete("all")
        self._round_rect(2, 2, self._width - 2, self._height - 2,
                         self._radius, fill=bg, outline="")
        self.create_text(
            self._width // 2, self._height // 2,
            text=self._text, fill=self._fg, font=self._font,
        )

    def _on_click(self, _event):
        if self._command:
            self._command()

    def _on_enter(self, _event):
        self._draw(self._active_bg)
        self.configure(cursor="hand2")

    def _on_leave(self, _event):
        self._draw(self._bg)

    def set_text(self, text):
        self._text = text
        self._draw(self._bg)


class GreenCheckbox(tk.Canvas):
    """Checkbox personalizado con color verde y marca de tilde."""

    def __init__(self, parent, text="", variable=None, command=None,
                 size=20, **kwargs):
        super().__init__(parent, width=size + 8 + len(text) * 7, height=size + 4,
                         bg=BG_PANEL, highlightthickness=0, **kwargs)
        self._variable = variable
        self._command = command
        self._size = size
        self._text = text

        self.bind("<Button-1>", self._on_click)
        self._draw()

    def _draw(self):
        self.delete("all")
        self.configure(bg=BG_PANEL)
        s = self._size
        x0, y0 = 2, 2
        x1, y1 = x0 + s, y0 + s

        self.create_rectangle(x0, y0, x1, y1, outline=BORDER, width=2, fill=BG_CONTENT)

        if self._variable and self._variable.get():
            self.create_text(x0 + s // 2, y0 + s // 2 - 1, text="✓", fill=BTN_PRIMARY,
                             font=("Segoe UI", max(10, s - 4), "bold"))

        self.create_text(x1 + 8, y0 + s // 2, text=self._text, anchor="w",
                         fill=TEXT_PRIMARY, font=FONT_SMALL)

    def _on_click(self, _event):
        if self._variable:
            self._variable.set(not self._variable.get())
        if self._command:
            self._command()
        self._draw()


class LanguageDropdown(tk.Canvas):
    """Dropdown para seleccion de idioma con popup scrollable."""

    def __init__(self, parent, languages, current_code, on_change=None,
                 **kwargs):
        super().__init__(parent, width=110, height=28, bg=BG_ROOT,
                         highlightthickness=0, **kwargs)
        self._languages = languages
        self._current_code = current_code
        self._on_change = on_change
        self._popup = None
        self._max_visible = 5

        self._draw()
        self.bind("<Button-1>", self._toggle_popup)

    def _current_lang(self):
        for lang in self._languages:
            if lang["code"] == self._current_code:
                return lang
        return self._languages[0] if self._languages else {"code": "?", "name": "?", "flag": "?"}

    def _draw(self):
        self.delete("all")
        self.configure(bg=BG_ROOT)
        lang = self._current_lang()
        code = lang["code"].upper()
        self.create_rectangle(4, 4, 36, 24, fill=BTN_PRIMARY, outline="", width=0)
        self.create_text(20, 14, text=code, font=("Segoe UI", 9, "bold"), fill="#ffffff")
        self.create_text(44, 14, text=lang["name"], font=FONT_SMALL, anchor="w", fill=TEXT_PRIMARY)
        self.create_text(98, 14, text="\u25BC", font=("Segoe UI", 7), anchor="w", fill=TEXT_SECONDARY)

    def _toggle_popup(self, _event):
        if self._popup and self._popup.winfo_exists():
            self._close_popup()
            return

        self._popup = tw = tk.Toplevel(self)
        tw.wm_overrideredirect(True)
        tw.wm_attributes("-topmost", True)
        tw.configure(bg=BORDER)

        x = self.winfo_rootx()
        y = self.winfo_rooty() + self.winfo_height() + 2
        tw.wm_geometry(f"+{x}+{y}")

        container = tk.Frame(tw, bg=BG_PANEL)
        container.pack(fill="both", expand=True)

        canvas = tk.Canvas(container, bg=BG_PANEL, highlightthickness=0,
                           height=min(self._max_visible, len(self._languages)) * 32)
        scrollbar = ttk.Scrollbar(container, orient=tk.VERTICAL, command=canvas.yview)
        inner = tk.Frame(canvas, bg=BG_PANEL)

        inner.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        canvas.create_window((0, 0), window=inner, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)

        for lang in self._languages:
            row = tk.Frame(inner, bg=BG_PANEL, cursor="hand2")
            row.pack(fill="x", padx=2, pady=1)
            badge = tk.Canvas(row, width=28, height=22, bg=BG_PANEL, highlightthickness=0)
            badge.pack(side="left", padx=(4, 6))
            badge.create_rectangle(0, 0, 28, 22, fill=BTN_PRIMARY if lang["code"] == self._current_code else BTN_SECONDARY, outline="")
            badge.create_text(14, 11, text=lang["code"].upper(), font=("Segoe UI", 8, "bold"),
                              fill="#ffffff" if lang["code"] == self._current_code else TEXT_PRIMARY)
            tk.Label(row, text=lang["name"], font=FONT_BODY, bg=BG_PANEL, fg=TEXT_PRIMARY, anchor="w").pack(
                side="left", fill="x", expand=True)
            if lang["code"] == self._current_code:
                tk.Label(row, text="\u2713", font=FONT_BODY, bg=BG_PANEL, fg=BTN_PRIMARY).pack(side="right", padx=4)
            row.bind("<Button-1>", lambda e, code=lang["code"]: self._select(code))
            for child in row.winfo_children():
                child.bind("<Button-1>", lambda e, code=lang["code"]: self._select(code))

        if len(self._languages) > self._max_visible:
            canvas.pack(side="left", fill="both", expand=True)
            scrollbar.pack(side="right", fill="y")
        else:
            canvas.pack(fill="both", expand=True)

        def _on_mousewheel(event):
            canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")

        canvas.bind("<MouseWheel>", _on_mousewheel)
        inner.bind("<MouseWheel>", _on_mousewheel)
        for child in inner.winfo_children():
            child.bind("<MouseWheel>", _on_mousewheel)
            for subchild in child.winfo_children():
                subchild.bind("<MouseWheel>", _on_mousewheel)

        tw.update_idletasks()
        tw.bind("<FocusOut>", lambda e: self._close_popup())
        tw.focus_set()

    def _select(self, code):
        self._current_code = code
        self._draw()
        self._close_popup()
        if self._on_change:
            self._on_change(code)

    def _close_popup(self):
        if self._popup and self._popup.winfo_exists():
            self._popup.destroy()
        self._popup = None

    def set_language(self, code):
        self._current_code = code
        self._draw()


class DarkModeSwitch(tk.Canvas):
    """Switch toggle para modo oscuro/claro."""

    def __init__(self, parent, command=None, bg=BG_ROOT, **kwargs):
        super().__init__(parent, width=50, height=26, bg=bg,
                         highlightthickness=0, **kwargs)
        self._command = command
        self._bg = bg
        self._is_dark = is_dark_mode()
        self._draw()
        self.bind("<Button-1>", self._toggle)
        self.configure(cursor="hand2")

    def _draw(self):
        self.delete("all")
        if self._is_dark:
            self.create_rectangle(1, 1, 49, 25, fill="#1565C0", outline="", width=0)
            self.create_oval(26, 2, 48, 24, fill="#ffffff", outline="")
            self.create_text(37, 13, text="\u263D", font=("Segoe UI", 11), fill="#1565C0")
        else:
            self.create_rectangle(1, 1, 49, 25, fill="#F9A825", outline="", width=0)
            self.create_oval(2, 2, 24, 24, fill="#ffffff", outline="")
            self.create_text(13, 13, text="\u2600", font=("Segoe UI", 11), fill="#F9A825")

    def _toggle(self, _event):
        self._is_dark = not self._is_dark
        self._draw()
        if self._command:
            self._command(self._is_dark)


def apply_theme(root):
    """Aplica el tema visual completo a la ventana raiz."""
    root.configure(bg=BG_ROOT)

    style = ttk.Style(root)
    style.theme_use("clam")

    style.configure(".", background=BG_ROOT, foreground=TEXT_PRIMARY, font=FONT_BODY)

    style.configure("TNotebook", background=BG_ROOT, borderwidth=0)
    style.configure(
        "TNotebook.Tab",
        padding=[16, 6],
        font=FONT_BODY,
        background=BTN_SECONDARY,
        foreground=TEXT_PRIMARY,
    )
    style.map(
        "TNotebook.Tab",
        background=[("selected", BG_PANEL)],
        foreground=[("selected", TEXT_TITLE)],
    )

    style.configure(
        "Treeview",
        background=BG_CONTENT,
        fieldbackground=BG_CONTENT,
        foreground=TEXT_PRIMARY,
        borderwidth=0,
        font=FONT_BODY,
        rowheight=28,
    )
    style.configure(
        "Treeview.Heading",
        background=ROW_HEADER_BG,
        foreground=TEXT_TITLE,
        font=FONT_SMALL_BOLD,
        borderwidth=0,
        relief="flat",
    )
    style.map(
        "Treeview",
        background=[("selected", ROW_SELECTED)],
        foreground=[("selected", ROW_SELECTED_FG)],
    )
    style.map("Treeview.Heading", background=[("active", ROW_HEADER_BG)])

    style.configure(
        "TLabelframe",
        background=BG_PANEL,
        foreground=TEXT_TITLE,
        borderwidth=1,
        relief="solid",
    )
    style.configure(
        "TLabelframe.Label",
        background=BG_PANEL,
        foreground=TEXT_TITLE,
        font=FONT_SMALL_BOLD,
    )

    style.configure(
        "TCheckbutton",
        background=BG_PANEL,
        foreground=TEXT_PRIMARY,
        font=FONT_SMALL,
        borderwidth=0,
        relief="flat",
        indicatorsize=16,
    )
    style.map("TCheckbutton", background=[("active", BG_PANEL)])

    style.configure(
        "TFrame",
        background=BG_ROOT,
    )
    style.configure(
        "Panel.TFrame",
        background=BG_PANEL,
    )

    style.configure(
        "Vertical.TScrollbar",
        troughcolor=BG_ROOT,
        background=BORDER,
        borderwidth=0,
        relief="flat",
    )
    style.map(
        "Vertical.TScrollbar",
        background=[("active", TEXT_SECONDARY), ("pressed", TEXT_SECONDARY)],
    )
    style.configure(
        "Horizontal.TScrollbar",
        troughcolor=BG_ROOT,
        background=BORDER,
        borderwidth=0,
        relief="flat",
    )
    style.map(
        "Horizontal.TScrollbar",
        background=[("active", TEXT_SECONDARY), ("pressed", TEXT_SECONDARY)],
    )
