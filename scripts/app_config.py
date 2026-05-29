import json
import os
from dataclasses import dataclass
from pathlib import Path

from desktop_app.scripts.paths import get_data_dir

CONFIG_DIR = get_data_dir() / "config"
CONFIG_FILE = CONFIG_DIR / "supabase_config.json"


@dataclass
class SupabaseConfig:
    url: str
    anon_key: str


def load_supabase_config():
    url = os.getenv("SUPABASE_URL", "").strip()
    anon_key = os.getenv("SUPABASE_ANON_KEY", "").strip()

    if url and anon_key:
        return SupabaseConfig(url=url.rstrip("/"), anon_key=anon_key)

    if CONFIG_FILE.exists():
        with CONFIG_FILE.open("r", encoding="utf-8") as file:
            data = json.load(file)
        url = str(data.get("supabase_url", "")).strip()
        anon_key = str(data.get("supabase_anon_key", "")).strip()

    if not url or not anon_key:
        raise RuntimeError(
            "Falta configuracion de Supabase. Crea desktop_app/config/supabase_config.json "
            "a partir de supabase_config.example.json o define SUPABASE_URL y SUPABASE_ANON_KEY."
        )

    return SupabaseConfig(url=url.rstrip("/"), anon_key=anon_key)
