# Como anadir un nuevo idioma

## Pasos

### 1. Crear el archivo de traduccion

Copia un archivo JSON existente como plantilla:

```bash
cp i18n/es.json i18n/xx.json
```

Donde `xx` es el codigo ISO del idioma (ej: `ar` para arabe, `hi` para hindi, `zh` para chino simplificado).

### 2. Traducir las claves

Abre `i18n/xx.json` y traduce todos los valores. Mantén las claves tal cual, solo cambia los textos entre comillas.

Ejemplo:
```json
{
    "_meta": {
        "name": "العربية",
        "flag": "🇸🇦",
        "font": "Noto Sans",
        "font_file": null
    },
    "app": {
        "title": "تحميل GeoJSON - مدير الميدان"
    }
}
```

### 3. Configurar la fuente (si es necesario)

Si el idioma usa caracteres que no estan en "Segoe UI" (latino, cirilico), necesitas configurar una fuente en `_meta`:

| Idioma | Fuente recomendada | font_file |
|--------|-------------------|-----------|
| Latino/Cirilico | `Noto Sans` | null |
| Japones | `Noto Sans CJK JP` | `NotoSansCJKjp-Regular.otf` |
| Chino simplificado | `Noto Sans CJK SC` | `NotoSansCJKsc-Regular.otf` |
| Chino tradicional | `Noto Sans CJK TC` | `NotoSansCJKtc-Regular.otf` |
| Coreano | `Noto Sans CJK KR` | `NotoSansCJKkr-Regular.otf` |
| Arabe/Hebreo | `Noto Sans` | null |

Si la fuente no esta en el sistema, la app intentara cargarla desde `fonts/`.

### 4. Anadir soporte de fuente en theme.py (opcional)

Si el idioma necesita una fuente del sistema que no esta en la lista, edita `app/theme.py`:

```python
_CJK_FONT_MAP = {
    "ja": ["Yu Gothic", "Meiryo", "Hiragino Sans", "Noto Sans CJK JP"],
    "zh": ["Microsoft YaHei", "PingFang SC", "Noto Sans CJK SC"],
    "ko": ["Malgun Gothic", "Apple SD Gothic Neo", "Noto Sans CJK KR"],
    "ar": ["Noto Sans Arabic", "Geeza Pro"],  # Ejemplo para arabe
}
```

### 5. Probar

1. Abre la app.
2. Cambia al nuevo idioma desde el selector.
3. Comprueba que todos los textos se muestran correctamente.
4. Verifica que los caracteres especiales no aparecen como cuadros.

## Estructura del archivo JSON

El archivo tiene 11 secciones:

| Seccion | Contenido |
|---------|-----------|
| `_meta` | Nombre del idioma, bandera, fuente |
| `app` | Titulo de la aplicacion |
| `login` | Textos de la pantalla de login |
| `register` | Textos de la pantalla de registro |
| `load` | Textos del selector de archivos |
| `processing` | Textos del procesamiento |
| `profile` | Textos del perfil de usuario |
| `log` | Mensajes de log del procesador GeoJSON |
| `summary` | Textos del resumen de carga |
| `inspector` | Textos del inspector de archivos |
| `dialog` | Textos de los botones de dialogo (Si/No/OK) |

## Notas

- Los archivos JSON se cargan automaticamente al iniciar la app.
- No es necesario reiniciar la app para ver los cambios (se aplica al cambiar de idioma).
- Si falta una clave, el sistema muestra la clave original como fallback.
- Los archivos de config (`supabase_config.json`, `session.json`) no se traducen.
