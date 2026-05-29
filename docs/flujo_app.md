# Flujo de la aplicacion

## Flujo principal

```
┌─────────────┐
│  Abrir app  │
└──────┬──────┘
       │
       ▼
┌──────────────────┐     ┌─────────────────┐
│ ¿Sesion activa?  │─No─▶│ Login / Registro │
└──────┬───────────┘     └───────┬─────────┘
       │Si                       │
       ▼                         ▼
┌──────────────────┐     ┌─────────────────┐
│ Seleccionar      │◀────│ Autenticacion   │
│ archivos GeoJSON │     │ (Supabase Auth) │
└──────┬───────────┘     └─────────────────┘
       │
       ▼
┌──────────────────┐
│ Validar GeoJSON  │
│ (estructura)     │
└──────┬───────────┘
       │
       ▼
┌──────────────────┐
│ Procesar cada    │
│ feature:         │
│ - Geometria      │
│ - Parcela        │
│ - Recinto        │
│ - Punto interior │
└──────┬───────────┘
       │
       ▼
┌──────────────────┐     ┌─────────────────┐
│ ¿Hay cliente     │─No─▶│ Resumen sin     │
│ Supabase?        │     │ insercion       │
└──────┬───────────┘     └─────────────────┘
       │Si
       ▼
┌──────────────────┐
│ Consultar        │
│ Catastro API     │
└──────┬───────────┘
       │
       ▼
┌──────────────────┐
│ Insertar en      │
│ Supabase         │
│ (parcelas,       │
│  recintos)       │
└──────┬───────────┘
       │
       ▼
┌──────────────────┐
│ Resumen final    │
│ - Procesados     │
│ - Insertados     │
│ - Errores        │
└──────────────────┘
```

## Procesamiento de cada feature

1. **Lectura**: se extraen id, parcela, poligono, recinto, uso SIGPAC y geometria.
2. **Validacion**: se comprueba que tiene id, geometria y coordenadas.
3. **Punto representativo**: se calcula un punto interior del poligono:
   - Primero intenta el centroide.
   - Si el centroide cae fuera, usa una rejilla 4x4, 8x8 o 16x16.
   - Si no hay punto interior, usa el primer vertice como fallback.
4. **Consulta Catastro**: se envia el punto a la API publica de Catastro.
5. **Referencia catastral**:
   - Si Catastro devuelve datos completos → referencia oficial.
   - Si no hay datos → fallback desde SIGPAC (provincia + municipio + sector + poligono + parcela).
6. **Construccion de payload**: se preparan los registros para `parcelas` y `recintos`.

## Comportamiento ante errores

- Si un archivo falla, se continua con el resto.
- Los errores se acumulan por archivo y por feature.
- El log detallado se muestra en tiempo real durante el procesamiento.
- Al final se muestra un resumen con estadisticas completas.
