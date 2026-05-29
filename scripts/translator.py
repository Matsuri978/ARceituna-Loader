"""Sistema de internacionalizacion (i18n) basado en archivos JSON.

Modulo que gestiona la carga de traducciones, el idioma actual y la
funcion de traduccion t() para claves anidadas.
"""

import json
from pathlib import Path

from desktop_app.scripts.paths import get_data_dir

_I18N_DIR = get_data_dir() / "i18n"
_current_language = "es"
_translations = {}


def _scan_languages():
    """Escanea el directorio i18n y devuelve los idiomas disponibles."""
    languages = []
    for f in sorted(_I18N_DIR.glob("*.json")):
        code = f.stem
        try:
            with f.open("r", encoding="utf-8") as fh:
                data = json.load(fh)
            name = data.get("_meta", {}).get("name", code)
            flag = data.get("_meta", {}).get("flag", "")
            languages.append({"code": code, "name": name, "flag": flag})
        except Exception:
            continue
    return languages


def load_language(lang_code):
    """Carga las traducciones para el codigo de idioma especificado."""
    global _current_language, _translations
    lang_file = _I18N_DIR / f"{lang_code}.json"
    if lang_file.exists():
        with lang_file.open("r", encoding="utf-8") as f:
            _translations = json.load(f)
        _current_language = lang_code
    else:
        _translations = {}
        _current_language = lang_code


def t(key):
    """Traduce una clave anidada (ej. 'log.file') usando el idioma actual."""
    parts = key.split(".")
    value = _translations
    for part in parts:
        if isinstance(value, dict):
            value = value.get(part)
        else:
            return key
    return value if value is not None else key


def get_current_language():
    """Devuelve el codigo del idioma actual."""
    return _current_language


def set_current_language(lang_code):
    """Establece el idioma actual, cargando traducciones y ajustando fuentes."""
    from desktop_app.app import theme
    load_language(lang_code)
    theme.set_font_for_language(lang_code)


def get_available_languages():
    """Devuelve la lista de idiomas disponibles en el directorio i18n."""
    return _scan_languages()
