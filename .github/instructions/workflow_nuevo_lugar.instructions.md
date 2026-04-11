---
description: Flujo obligatorio para agregar una nueva ciudad o lugar al repositorio
applyTo: '**/*'
---

# Workflow — Agregar una nueva ciudad o lugar

Este es el flujo exacto y completo que toda AI debe seguir cada vez que se agrega una nueva ciudad o conjunto de lugares al repositorio. No saltear pasos ni cambiar el orden.

---

## Paso 1 — Estructura de carpetas

Crear las carpetas necesarias antes de crear ningún archivo:

```
NombreCiudad/
  fotos/          ← mapas PNG generados por el script
  lugares/        ← un .md por lugar
```

No usar `mkdir` si las herramientas del editor permiten crear archivos directamente (la carpeta se crea sola).

---

## Paso 2 — Archivo principal de ciudad

Crear `NombreCiudad/nombreciudad.md` con:

```yaml
ciudad:
  nombre_original: ""
  nombre_alternativo: ""     # solo si existe
  pais: ""
  region_admin: ""
  coordenadas: ""
  altitud_m:
  fecha_visita: ""           # ISO 8601 o [DATO PENDIENTE — confirmar fecha]
```

Contenido obligatorio del archivo principal:
- **Historia completa y rica**: no superficial. Incluir origen, apogeo, decadencia, conexiones políticas, personajes históricos clave, datos sorprendentes.
- **Geografía urbana**: cómo está organizada la ciudad, ejes principales, zonas.
- **Legado artístico o científico** si aplica.
- **Sección de logística** si la ciudad se visita en combinación con otra (itinerario horario sugerido).
- **Lista de lugares documentados** al final, con links relativos a `lugares/nombre_lugar.md`.
- **Fuentes** al pie (`*fuente: ...*`).

---

## Paso 3 — Archivos de lugares individuales (top N lugares)

Crear un `.md` por lugar en `NombreCiudad/lugares/nombre_lugar.md`.

### Frontmatter obligatorio

```yaml
lugar:
  nombre_original: ""
  pais: ""
  region_admin: ""
  coordenadas: ""
  altitud_m:                 # solo si es relevante
  fecha_visita: ""
```

### Bloque de mapas — colocar SIEMPRE inmediatamente después del frontmatter

```markdown
![Mapa con pin de X](../fotos/mapa_x.png)

> [DATO PENDIENTE — generar mapa con pin]
```

Este placeholder se reemplaza en el **Paso 6** por:

```markdown
![Mapa con pin de X](../fotos/mapa_x.png)

![Mapa detalle de X](../fotos/mapa_x_detalle.png)
```

### Estructura de contenido

Incluir las secciones que sean relevantes (no todas son obligatorias):

- **Qué había antes** — contexto previo al monumento/lugar actual
- **Historia** — con línea de tiempo en tabla Markdown si hay muchos hitos
- **Mitología y leyendas** — marcadas siempre como "según la tradición...", "la leyenda cuenta..."
- **Arquitectura** — descripción física detallada
- **Qué se puede ver hoy** — orientación práctica para la visita
- **Conexiones** — relación con otros lugares del repositorio
- **Datos interesantes** — curiosidades verificables
- **Fuentes** al pie

### Normas de contenido

- Usar `[⚠ VERIFICAR]` para datos cuantitativos no confirmados (cifras, fechas exactas, rankings).
- Usar `[DATO PENDIENTE — verificar fuente]` para datos que se sabe que faltan.
- No inventar nada. No usar IA como fuente de respaldo.
- Nombres propios siempre en su grafía original.

---

## Paso 4 — JSON de mapas

Crear `tools/maps/nombreciudad_places.json` con el siguiente formato, **un objeto por lugar**:

```json
[
  {
    "nombre": "Nombre legible del lugar",
    "archivo": "mapa_nombre_lugar.png",
    "lat": 00.0000,
    "lon": 00.0000,
    "referencias": [
      { "nombre": "Otro lugar cercano A", "lat": 00.0000, "lon": 00.0000 },
      { "nombre": "Otro lugar cercano B", "lat": 00.0000, "lon": 00.0000 }
    ]
  }
]
```

Reglas del JSON:
- `"archivo"` debe seguir el formato `mapa_<nombre_lugar>.png` en minúsculas con `_`.
- `"referencias"` son los 3-4 lugares más importantes de la misma ciudad (dan contexto en el mapa).
- El valor de `"archivo"` debe coincidir exactamente con el placeholder `../fotos/mapa_x.png` en el `.md` correspondiente.

---

## Paso 5 — Generar los mapas

Ejecutar en el directorio raíz del repositorio:

```bash
# Activar entorno virtual si no está activo
source .venv/bin/activate

# Generar mapas (reemplazar nombreciudad con el nombre real)
python tools/maps/generate_static_maps.py \
  --input tools/maps/nombreciudad_places.json \
  --output NombreCiudad/fotos \
  --no-city-context
```

El script genera **dos PNG por lugar**: `mapa_x.png` y `mapa_x_detalle.png`.

### ⚠ Bug conocido: ENOPRO en dev containers

En Codespaces / dev containers, la herramienta `run_in_terminal` falla frecuentemente con el error:
```
ENOPRO: No se ha encontrado ningún proveedor de sistema de archivos para el recurso "file:///workspaces/..."
```
Esto es un problema de Copilot, no del comando. La terminal manual funciona sin problema.

**Protocolo**: intentar `run_in_terminal` **una sola vez**. Si falla con ENOPRO, proporcionar inmediatamente el comando exacto al usuario para que lo ejecute él. No reintentar.

---

## Paso 6 — Actualizar los .md con los mapas reales

Una vez confirmado que los PNG existen en `NombreCiudad/fotos/`, reemplazar el bloque placeholder en cada `.md`:

**Antes:**
```markdown
![Mapa con pin de X](../fotos/mapa_x.png)

> [DATO PENDIENTE — generar mapa con pin]
```

**Después:**
```markdown
![Mapa con pin de X](../fotos/mapa_x.png)

![Mapa detalle de X](../fotos/mapa_x_detalle.png)
```

Usar `multi_replace_string_in_file` para actualizar todos los archivos de la ciudad en una sola llamada.

---

## Paso 7 — Verificar coherencia

Antes de dar por terminado:

- [ ] Todos los lugares mencionados en el `.md` principal tienen su propio archivo en `lugares/`.
- [ ] Todos los `../fotos/mapa_x.png` referenciados en los `.md` existen físicamente en `NombreCiudad/fotos/`.
- [ ] No quedan `> [DATO PENDIENTE — generar mapa con pin]` en ningún `.md`.
- [ ] El archivo principal de la ciudad tiene la lista completa de lugares con links.
- [ ] Los nombres de archivo siguen la convención `mapa_<nombre_lugar>.png` (minúsculas, guiones bajos).

---

## Referencia rápida — convenciones de nombre de archivo

| Tipo | Convención | Ejemplo |
|---|---|---|
| Archivo principal | `nombreciudad.md` | `lucca.md` |
| Lugar individual | `nombre_lugar.md` | `torre_guinigi.md` |
| Mapa general | `mapa_nombre_lugar.png` | `mapa_torre_guinigi.png` |
| Mapa detalle | `mapa_nombre_lugar_detalle.png` | `mapa_torre_guinigi_detalle.png` |
| JSON de mapas | `nombreciudad_places.json` | `lucca_places.json` |

---

## Ciudades ya en el repositorio (referencia de estructura)

| Ciudad | Carpeta | JSON de mapas |
|---|---|---|
| Roma | `Rome/` | `tools/maps/rome_places.example.json` |
| Firenze | `Firenze/` | `tools/maps/firenze_places.json` |
| Lucca | `Lucca/` | `tools/maps/lucca_places.json` |
| Pisa | `Pisa/` | `tools/maps/pisa_places.json` |
