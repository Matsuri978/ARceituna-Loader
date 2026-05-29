"""Estado global de la aplicacion.

Modulo que define las estructuras de datos para el estado de la aplicacion,
incluyendo resultados de procesamiento, archivos seleccionados y datos de usuario.
"""

from dataclasses import dataclass, field
from pathlib import Path


STATUS_PENDING = "pending"
STATUS_PROCESSING = "processing"
STATUS_DONE = "done"
STATUS_ERROR = "error"


@dataclass
class ProcessingSummary:
    """Resumen global del procesamiento de archivos."""
    files_processed: int = 0
    parcels_detected: int = 0
    enclosures_detected: int = 0
    parcels_inserted: int = 0
    enclosures_inserted: int = 0
    errors: list[str] = field(default_factory=list)


@dataclass
class FileProcessingResult:
    """Resultado del procesamiento de un archivo GeoJSON individual."""
    path: Path
    status: str = STATUS_PENDING
    logs: list[str] = field(default_factory=list)
    parcelas: list[dict] = field(default_factory=list)
    recintos: list[dict] = field(default_factory=list)
    feature_errors: list[str] = field(default_factory=list)
    insertion_errors: list[str] = field(default_factory=list)
    parcels_detected: int = 0
    enclosures_detected: int = 0
    parcels_inserted: int = 0
    enclosures_inserted: int = 0
    error: str = ""


@dataclass
class AppState:
    """Estado central de la aplicacion, contiene usuario, archivos y resultados."""
    user_email: str = ""
    user_full_name: str = ""
    user_id: str = ""
    selected_files: list[Path] = field(default_factory=list)
    log_lines: list[str] = field(default_factory=list)
    file_results: dict[str, FileProcessingResult] = field(default_factory=dict)
    summary: ProcessingSummary = field(default_factory=ProcessingSummary)

    def reset_processing(self):
        """Reinicia el estado de procesamiento (logs, resultados, resumen)."""
        self.log_lines.clear()
        self.file_results.clear()
        self.summary = ProcessingSummary()

    def add_log(self, message: str):
        """Agrega una linea al log de procesamiento."""
        self.log_lines.append(message)

    def set_file_result(self, result: FileProcessingResult):
        """Almacena el resultado de procesamiento de un archivo."""
        self.file_results[str(result.path)] = result

    def set_user_from_supabase(self, user):
        """Extrae y guarda los datos del usuario desde Supabase."""
        metadata = user.get("user_metadata") or {}
        display_name = metadata.get("display_name") or metadata.get("full_name") or ""

        self.user_id = user.get("id", "")
        self.user_email = user.get("email", "")
        self.user_full_name = display_name.strip()

    def clear_user(self):
        """Limpia los datos del usuario (logout)."""
        self.user_email = ""
        self.user_full_name = ""
        self.user_id = ""
