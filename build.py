"""Script de build completo: PyInstaller + Inno Setup.

Genera:
1. dist/ARceitunaLoader/  (carpeta con la app empaquetada)
2. installer/ARceitunaLoader-Setup-1.0.0.exe  (instalador)
"""
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent
APP_DIR = ROOT

# --- Paso 1: PyInstaller ---
print("=" * 50)
print("PASO 1: Empaquetando con PyInstaller...")
print("=" * 50)

tmp_config = Path(tempfile.mkdtemp()) / "config"
tmp_config.mkdir()
shutil.copy2(
    APP_DIR / "config" / "supabase_config.json",
    tmp_config / "supabase_config.json",
)

cmd = [
    sys.executable, "-m", "PyInstaller",
    "--noconfirm",
    "--onedir",
    "--windowed",
    "--name", "ARceitunaLoader",
    f"--distpath={APP_DIR / 'dist'}",
    f"--workpath={APP_DIR / 'build'}",
    f"--specpath={APP_DIR}",

    f"--add-data={APP_DIR / 'i18n'};i18n",
    f"--add-data={APP_DIR / 'fonts'};fonts",
    f"--add-data={tmp_config};config",

    "--hidden-import", "desktop_app",
    "--hidden-import", "desktop_app.app",
    "--hidden-import", "desktop_app.app.main",
    "--hidden-import", "desktop_app.app.theme",
    "--hidden-import", "desktop_app.app.state",
    "--hidden-import", "desktop_app.scripts",
    "--hidden-import", "desktop_app.scripts.translator",
    "--hidden-import", "desktop_app.scripts.session_store",
    "--hidden-import", "desktop_app.scripts.supabase_client",
    "--hidden-import", "desktop_app.scripts.app_config",
    "--hidden-import", "desktop_app.scripts.geojson_processor",

    str(APP_DIR / "run.py"),
]

subprocess.run(cmd, check=True)
shutil.rmtree(tmp_config.parent, ignore_errors=True)
print("PyInstaller completado.\n")

# --- Paso 2: Inno Setup ---
print("=" * 50)
print("PASO 2: Generando instalador con Inno Setup...")
print("=" * 50)

iscc_paths = [
    r"C:\Program Files (x86)\Inno Setup 6\ISCC.exe",
    r"C:\Program Files\Inno Setup 6\ISCC.exe",
    r"C:\Users\raula\AppData\Local\Programs\Inno Setup 6\ISCC.exe",
]
iscc = None
for p in iscc_paths:
    if Path(p).exists():
        iscc = p
        break

if iscc is None:
    # Buscar en todo el sistema
    import glob
    for pattern in [r"C:\*\Inno Setup 6\ISCC.exe", r"C:\*\Inno Setup*\ISCC.exe"]:
        found = glob.glob(pattern)
        if found:
            iscc = found[0]
            break

if iscc is None:
    print("ADVERTENCIA: Inno Setup no encontrado. Instalalo con:")
    print("  winget install JRSoftware.InnoSetup")
    print("O descargalo de: https://jrsoftware.org/isinfo.php")
    print("\nEl instalador NO se ha generado.")
    print("La app esta lista en: desktop_app/dist/ARceitunaLoader/")
else:
    iss_script = APP_DIR / "installer" / "setup.iss"
    subprocess.run([iscc, str(iss_script)], check=True)
    print("\nInstalador generado en: desktop_app/installer/ARceitunaLoader-Setup-1.0.0.exe")

    # Limpiar archivos temporales
    print("\nLimpiando archivos temporales...")
    for folder in ["dist", "build"]:
        folder_path = APP_DIR / folder
        if folder_path.exists():
            shutil.rmtree(folder_path)
            print(f"  Eliminada: {folder}/")

    spec_file = APP_DIR / "ARceitunaLoader.spec"
    if spec_file.exists():
        spec_file.unlink()
        print("  Eliminado: ARceitunaLoader.spec")

print("\n" + "=" * 50)
print("BUILD COMPLETADO")
print("=" * 50)
