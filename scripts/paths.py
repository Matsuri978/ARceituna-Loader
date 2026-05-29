"""Utilidad para resolver rutas de datos tanto en desarrollo como en .exe."""
import sys
from pathlib import Path


def get_data_dir():
    """Devuelve el directorio raiz de datos de la app.

    En desarrollo: desktop_app/
    En .exe (PyInstaller --onedir): dist/ARceitunaLoader/_internal/
    """
    if getattr(sys, "frozen", False):
        return Path(sys.executable).parent / "_internal"
    return Path(__file__).resolve().parent.parent
