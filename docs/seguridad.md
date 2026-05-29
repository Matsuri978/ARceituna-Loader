# Decisiones de seguridad

## Arquitectura

La app usa un cliente HTTP propio (`supabase_client.py`) que se conecta directamente a Supabase Auth y a la API REST. No se usa `DATABASE_URL` con permisos amplios.

```
┌──────────────┐     ┌──────────────┐     ┌──────────────┐
│ App escritorio│────▶│ Supabase Auth│────▶│   Supabase   │
│  (Tkinter)   │     │  (login)     │     │  (REST API)  │
└──────────────┘     └──────────────┘     └──────────────┘
```

## Credenciales

| Archivo | Contenido | Encriptado | Versionado |
|---------|-----------|------------|------------|
| `supabase_config.json` | URL + anon key | No | No |
| `session.json` | Token de sesion + preferencias | Si (XOR + base64) | No |

La **anon key** de Supabase es publica por diseno de la plataforma. No da acceso a datos privados.

El **token de sesion** se encripta con una clave derivada del dispositivo (nombre del PC + arquitectura). Solo la app en ese dispositivo puede descifrarlo.

## Rol `gestor_campo`

Permisos en Supabase:

| Tabla | Permiso |
|-------|---------|
| `parcelas` | INSERT, SELECT |
| `recintos` | INSERT, SELECT |
| Otras tablas | Sin acceso |

## Principios de seguridad

1. **No distribuir credenciales de administrador** en la app.
2. **No guardar contrasenas** — solo tokens de sesion encriptados.
3. **Permisos minimos** — el rol solo puede insertar en las tablas necesarias.
4. **Configuracion separada** — las credenciales van en un archivo no versionado.
5. **Sesion encriptada** — los tokens se cifran en el disco local.

## Riesgos conocidos

- La anon key de Supabase esta en la app. Es de uso publico, pero da acceso limitado a la API.
- La consulta a Catastro usa la API publica sin autenticacion.
- No hay rate limiting en la app.
- La encriptacion del session es ligera (XOR), no criptografia de grado militar.

## Recomendaciones

- Monitorizar el uso de la API de Catastro.
- Revisar periodicamente los permisos del rol `gestor_campo`.
- Considerar Edge Functions para operaciones criticas en el futuro.
