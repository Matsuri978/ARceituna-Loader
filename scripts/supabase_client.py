"""Cliente HTTP para Supabase Auth y API REST.

Modulo que implementa un cliente ligero para autenticacion y llamadas RPC
a Supabase usando urllib (sin dependencias externas).
"""

import json
import urllib.error
import urllib.request

from desktop_app.scripts.app_config import load_supabase_config


class SupabaseError(Exception):
    """Excepcion personalizada para errores de Supabase."""
    pass


class SupabaseClient:
    """Cliente para autenticacion y operaciones RPC en Supabase."""

    def __init__(self):
        config = load_supabase_config()
        self.url = config.url
        self.anon_key = config.anon_key
        self.access_token = ""
        self.refresh_token = ""
        self.user = {}

    @property
    def is_authenticated(self):
        """Devuelve True si hay un token de acceso activo."""
        return bool(self.access_token)

    def set_session(self, session):
        """Establece la sesion actual con tokens y datos de usuario."""
        self.access_token = session.get("access_token", "")
        self.refresh_token = session.get("refresh_token", "")
        self.user = session.get("user") or {}

    def current_session(self):
        """Devuelve un diccionario con la sesion actual."""
        return {
            "access_token": self.access_token,
            "refresh_token": self.refresh_token,
            "user": self.user,
        }

    def sign_in(self, email, password):
        """Inicia sesion con email y contrasena."""
        response = self._request(
            "POST",
            "/auth/v1/token?grant_type=password",
            payload={"email": email, "password": password},
            authorized=False,
        )
        session = _normalize_auth_session(response)
        self.set_session(session)
        return session

    def sign_up(self, email, password, name, surnames):
        """Registra un nuevo usuario con nombre y apellidos."""
        display_name = " ".join(part for part in (name, surnames) if part).strip()
        response = self._request(
            "POST",
            "/auth/v1/signup",
            payload={
                "email": email,
                "password": password,
                "data": {
                    "display_name": display_name,
                    "full_name": display_name,
                    "rol_solicitado": "gestor_campo",
                },
            },
            authorized=False,
        )

        session = _normalize_auth_session(response)
        if session.get("access_token"):
            self.set_session(session)
        else:
            self.user = session.get("user") or {}
        return session

    def refresh_session(self, refresh_token):
        """Renueva la sesion usando un refresh token."""
        response = self._request(
            "POST",
            "/auth/v1/token?grant_type=refresh_token",
            payload={"refresh_token": refresh_token},
            authorized=False,
        )
        session = _normalize_auth_session(response)
        self.set_session(session)
        return session

    def create_field_manager_profile(self):
        """Crea el perfil de gestor de campo para el usuario actual."""
        return self.rpc("crear_perfil_gestor_campo", {})

    def insert_parcela(self, parcela):
        """Inserta una parcela en la base de datos via RPC."""
        response = self.rpc(
            "insertar_parcela_gestor_campo",
            {
                "p_ref_catastral": parcela.get("ref_catastral", ""),
                "p_codigo_hoja": parcela.get("codigo_hoja", ""),
                "p_num_parcela": parcela.get("num_parcela", ""),
            },
        )
        return bool(response)

    def insert_recinto(self, recinto):
        """Inserta un recinto en la base de datos via RPC."""
        response = self.rpc(
            "insertar_recinto_desde_geojson",
            {
                "p_id_recinto_sigpac": str(recinto.get("id_recinto_sigpac", "")),
                "p_ref_catastral": recinto.get("ref_catastral", ""),
                "p_num_poligono": recinto.get("num_poligono", ""),
                "p_num_recinto": recinto.get("num_recinto", ""),
                "p_uso_sigpac": recinto.get("uso_sigpac", ""),
                "p_geom_geojson": recinto.get("geom") or {},
            },
        )
        return bool(response)

    def rpc(self, function_name, payload):
        """Ejecuta una funcion RPC en Supabase."""
        return self._request(
            "POST",
            f"/rest/v1/rpc/{function_name}",
            payload=payload,
            authorized=True,
        )

    def sign_out_local(self):
        """Limpia la sesion local (no invalida el token en el servidor)."""
        self.access_token = ""
        self.refresh_token = ""
        self.user = {}

    def _request(self, method, path, payload=None, authorized=False):
        """Realiza una peticion HTTP a Supabase."""
        url = self.url + path
        body = None
        headers = {
            "apikey": self.anon_key,
            "Content-Type": "application/json",
            "Accept": "application/json",
        }

        # Agregar token de autorizacion si es necesario
        if authorized:
            if not self.access_token:
                raise SupabaseError("No hay sesion activa.")
            headers["Authorization"] = f"Bearer {self.access_token}"

        if payload is not None:
            body = json.dumps(payload).encode("utf-8")

        request = urllib.request.Request(url, data=body, headers=headers, method=method)

        try:
            with urllib.request.urlopen(request, timeout=30) as response:
                content = response.read().decode("utf-8")
                if not content:
                    return {}
                return json.loads(content)
        except urllib.error.HTTPError as exc:
            message = exc.read().decode("utf-8", errors="replace")
            raise SupabaseError(_extract_error_message(message, exc.code)) from exc
        except urllib.error.URLError as exc:
            raise SupabaseError(f"No se pudo conectar con Supabase: {exc.reason}") from exc


def _extract_error_message(raw_message, status_code):
    try:
        data = json.loads(raw_message)
    except json.JSONDecodeError:
        return f"Error HTTP {status_code}: {raw_message}"

    for key in ("msg", "message", "error_description", "error"):
        value = data.get(key)
        if value:
            return f"Error HTTP {status_code}: {value}"

    return f"Error HTTP {status_code}: {raw_message}"


def _normalize_auth_session(response):
    session = response.get("session") or response
    user = session.get("user") or response.get("user") or {}

    return {
        "access_token": session.get("access_token", ""),
        "refresh_token": session.get("refresh_token", ""),
        "user": user,
    }


def _first_rpc_row(response):
    if isinstance(response, list):
        return response[0] if response else {}
    return response or {}
