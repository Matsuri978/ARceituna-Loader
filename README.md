# ARceituna Loader

Aplicacion de escritorio desarrollada en Python (Tkinter) para cargar archivos GeoJSON en una base de datos Supabase, con consulta automatica de referencias catastrales via la API publica de Catastro.

Aplicacion de soporte para [ARceituna](https://github.com/arceituna), la app movil de AR del olivar.

## Funcionalidades

- **Autenticacion**: login y registro de usuarios con rol `gestor_campo` via Supabase Auth.
- **Carga de archivos**: seleccion individual o multiples archivos `.geojson`.
- **Validacion**: comprobacion de estructura GeoJSON antes de procesar.
- **Procesamiento**: extraccion de parcelas, recintos y geometrias de cada feature.
- **Consulta Catastro**: obtencion de referencias catastrales via API REST publica.
- **Fallback SIGPAC**: reconstruccion de referencias desde datos SIGPAC cuando Catastro no responde.
- **Insercion en base de datos**: carga controlada en Supabase con permisos limitados.
- **Multiidioma**: 10 idiomas (ES, EN, PT, DE, IT, FR, JA, RU, KO, EL).
- **Modo oscuro**: tema claro y oscuro intercambiable.
- **Resumen de carga**: estadisticas detalladas y log completo del proceso.
- **Sesion encriptada**: tokens de acceso encriptados en el dispositivo.

## Requisitos

- Python 3.10 o superior
- pip
- Conexion a internet (para Supabase y Catastro)

## Instalacion

### 1. Clonar o copiar el proyecto

```bash
cdruta/donde/estee
```

### 2. Crear entorno virtual

```bash
python -m venv .venv
```

**Windows:**
```powershell
.venv\Scripts\activate
```

**Linux/macOS:**
```bash
source .venv/bin/activate
```

### 3. Instalar dependencias

```bash
pip install -r requirements.txt
```

### 4. Configurar Supabase

El archivo `config/supabase_config.json` debe contener tus credenciales:

```json
{
  "supabase_url": "https://tu-proyecto.supabase.co",
  "supabase_anon_key": "sb_publishable_tu_clave"
}
```

### 5. Ejecutar la aplicacion

```bash
python -m run
```

## Generar ejecutable (.exe)

```bash
python build.py
```

### Que genera

| Archivo | Descripcion |
|---------|-------------|
| `installer/ARceitunaLoader-Setup-1.0.0.exe` | Instalador completo (~20MB) |
| `installer/setup.iss` | Script de Inno Setup (se conserva) |

### Limpieza automatica

Si tienes [Inno Setup](https://jrsoftware.org/isinfo.php) instalado, el script genera el instalador y **borra automaticamente** los archivos temporales (`dist/`, `build/`, `.spec`).

Si no tienes Inno Setup, se conserva `dist/ARceitunaLoader/` para poder ejecutar la app directamente.

### Instalar Inno Setup (opcional)

```powershell
winget install JRSoftware.InnoSetup
```

El instalador incluye:

- Wizard de instalacion en espanol
- Seleccion de carpeta
- Acceso directo en escritorio
- Desinstalador

### Estructura despues del build

```
desktop_app/
├── dist/                         # Solo si NO tienes Inno Setup
│   └── ARceitunaLoader/
├── installer/
│   ├── setup.iss                 # Se conserva siempre
│   └── ARceitunaLoader-Setup-1.0.0.exe  # Se conserva siempre
├── app/                          # Codigo fuente
├── scripts/                      # Codigo fuente
├── i18n/                         # Traducciones
├── fonts/                        # Fuentes CJK
├── config/                       # Configuracion
└── docs/                         # Documentacion
```

## Estructura del proyecto

```
desktop_app/
├── run.py                      # Punto de entrada
├── build.py                    # Script de build (PyInstaller + Inno Setup)
├── requirements.txt            # Dependencias
├── README.md                   # Este archivo
├── app/
│   ├── main.py                 # Ventana principal (GeojsonLoaderApp)
│   ├── theme.py                # Tema, estilos, widgets y dialogos
│   ├── state.py                # Estado global de la aplicacion
│   └── views/
│       ├── login_view.py       # Pantalla de login y registro
│       ├── load_view.py        # Selector de archivos e inspector GeoJSON
│       ├── processing_view.py  # Procesamiento en tiempo real con log
│       ├── summary_view.py     # Resumen final de carga
│       └── profile_view.py     # Perfil de usuario y ajustes
├── scripts/
│   ├── translator.py           # Sistema de internacionalizacion (i18n)
│   ├── session_store.py        # Guardado encriptado de sesion y preferencias
│   ├── supabase_client.py      # Cliente HTTP para Supabase Auth y REST API
│   ├── app_config.py           # Carga de configuracion
│   ├── geojson_processor.py    # Procesamiento GeoJSON, Catastro y SIGPAC
│   ├── paths.py                # Resolucion de rutas (dev vs .exe)
│   └── uninstall_fonts.py      # Limpieza de fuentes CJK (Linux)
├── i18n/                       # Archivos de traduccion (10 idiomas)
├── fonts/                      # Fuentes CJK (Noto Sans CJK)
├── config/
│   ├── supabase_config.json    # Credenciales de Supabase
│   └── session.json            # Sesion encriptada (se crea automaticamente)
├── installer/
│   ├── setup.iss               # Script de Inno Setup
│   └── ARceitunaLoader-Setup-1.0.0.exe  # Instalador (se regenera)
└── docs/                       # Documentacion tecnica
    ├── flujo_app.md
    ├── seguridad.md
    ├── pendientes.md
    └── anadir_idioma.md
```

## Seguridad

- La **anon key** de Supabase es publica por diseno de la plataforma.
- El **token de sesion** se encripta en el dispositivo (XOR + base64, clave derivada del hardware).
- No se almacenan contrasenas.
- El rol `gestor_campo` solo tiene permisos de insercion en `parcelas` y `recintos`.

## Idiomas soportados

| Codigo | Idioma |
|--------|--------|
| es | Espanol |
| en | English |
| pt | Portugues |
| de | Deutsch |
| it | Italiano |
| fr | Francais |
| ja | Nihongo |
| ru | Russkij |
| ko | Hangug-eo |
| el | Ellinika |

## Documentacion adicional

- [Flujo de la aplicacion](docs/flujo_app.md)
- [Decisiones de seguridad](docs/seguridad.md)
- [Estado del proyecto](docs/pendientes.md)
- [Como anadir un nuevo idioma](docs/añadir_idioma.md)
