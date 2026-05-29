"""Almacenamiento encriptado de sesion y preferencias del usuario.

Modulo que gestiona el guardado local de tokens de autenticacion,
idioma y modo oscuro usando encriptacion XOR ligera.
"""

import base64
import hashlib
import json
import platform
from pathlib import Path

from desktop_app.scripts.paths import get_data_dir

SESSION_FILE = get_data_dir() / "config" / "session.json"


def _get_key():
    """Deriva una clave de encriptacion especifica del dispositivo."""
    raw = f"geojson-loader-{platform.node()}-{platform.machine()}"
    digest = hashlib.sha256(raw.encode()).digest()
    return base64.urlsafe_b64encode(digest)


def _encrypt(data):
    """Encripta un diccionario a bytes usando XOR + base64."""
    key = _get_key()
    plain = json.dumps(data, ensure_ascii=False).encode("utf-8")
    encrypted = bytes(b ^ key[i % len(key)] for i, b in enumerate(plain))
    return base64.b64encode(encrypted)


def _decrypt(raw):
    """Desencripta bytes a diccionario."""
    key = _get_key()
    encrypted = base64.b64decode(raw)
    decrypted = bytes(b ^ key[i % len(key)] for i, b in enumerate(encrypted))
    return json.loads(decrypted.decode("utf-8"))


def load_session():
    """Carga la sesion encriptada desde el archivo."""
    if not SESSION_FILE.exists():
        return None

    try:
        raw = SESSION_FILE.read_bytes()
        return _decrypt(raw)
    except Exception:
        clear_session()
        return None


def save_session(session):
    """Guarda la sesion encriptada, preservando idioma y modo oscuro."""
    existing = load_session() or {}
    SESSION_FILE.parent.mkdir(parents=True, exist_ok=True)
    data = {
        "access_token": session.get("access_token", ""),
        "refresh_token": session.get("refresh_token", ""),
        "user": session.get("user") or {},
        "language": existing.get("language", "es"),
        "dark_mode": existing.get("dark_mode", False),
    }
    SESSION_FILE.write_bytes(_encrypt(data))


def load_language():
    """Carga el idioma guardado de la sesion."""
    session = load_session()
    if session:
        return session.get("language", "es")
    return "es"


def save_language(lang_code):
    """Guarda el codigo de idioma en la sesion."""
    session = load_session() or {}
    session["language"] = lang_code
    SESSION_FILE.parent.mkdir(parents=True, exist_ok=True)
    SESSION_FILE.write_bytes(_encrypt(session))


def load_dark_mode():
    """Carga el estado del modo oscuro desde la sesion."""
    session = load_session()
    if session:
        return session.get("dark_mode", False)
    return False


def save_dark_mode(enabled):
    """Guarda el estado del modo oscuro en la sesion."""
    session = load_session() or {}
    session["dark_mode"] = enabled
    SESSION_FILE.parent.mkdir(parents=True, exist_ok=True)
    SESSION_FILE.write_bytes(_encrypt(session))


def clear_session():
    """Elimina el archivo de sesion."""
    try:
        SESSION_FILE.unlink()
    except FileNotFoundError:
        pass
