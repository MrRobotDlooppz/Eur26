# Claude Instructions — Travel Notes & Places Archive

## Rol y propósito del repositorio

Este repositorio es un archivo personal de notas, fotos, datos históricos e información de lugares visitados. El objetivo es construir un archivo rico, interesante y confiable: contexto histórico profundo, conexiones entre lugares, leyendas, mitología y cultura. La prioridad es que la información sea precisa y no inventada, pero sin sacrificar la riqueza narrativa.

---

## Reglas de integridad de datos

### 1. No inventar — nunca

- No fabricar datos factuales (fechas, nombres propios, estadísticas, cifras) de la nada.
- Si un dato específico no está disponible, marcarlo con `[DATO PENDIENTE — verificar fuente]`.
- La diferencia clave: **investigar y aportar información real es bienvenido**; inventar datos es inaceptable.

### 2. Preservar nombres originales

- Los nombres de lugares, monumentos, regiones, personas históricas y entidades deben preservarse en su idioma y grafía originales.
- No traducir, transliterar ni adaptar nombres propios salvo que el archivo fuente lo haga explícitamente.
- Ejemplo correcto: `Hallstatt`, `Chefchaouen`, `Göreme`, `Sigiriya`.
- Ejemplo incorrecto: `Halstat`, `la ciudad azul`, `Goreme` (sin diéresis).

### 3. Consistencia de nomenclatura interna

- Si un lugar ya tiene un nombre canónico dentro del repositorio, ese nombre debe usarse en todas las sugerencias subsiguientes.
- No crear variantes ortográficas, abreviaciones ni alias a menos que ya existan en el repositorio.

### 4. Fuentes confiables

- La información debe provenir de fuentes confiables. No se requiere citar fuente para cada oración, pero sí incluir un campo `fuente:` al final de cada sección de lugar con las referencias principales usadas en caso de aplicar.
- Fuentes aceptadas: organismos oficiales, museos, publicaciones académicas, guías de referencia establecidas, enciclopedias, libros de historia. Wikipedia es aceptable si la información es verificable y no controvertida.
- Fuentes **no** aceptadas: blogs personales sin respaldo, contenido generado por IA, sitios de dudosa reputación.
- Las leyendas y tradiciones populares se pueden incluir libremente, siempre que se identifiquen como tales (ej. "según la leyenda...", "la tradición cuenta que...").

---

## Enfoque del contenido

### 5. Priorizar lo interesante y el contexto profundo

- El foco principal es la **historia**, la **cultura**, las **leyendas**, la **mitología** y los **datos interesantes** de cada lugar.
- Explicar el **por qué** de las cosas: ¿por qué se construyó? ¿qué problema resolvía? ¿qué simboliza? ¿cómo conecta con otros lugares o eventos?
- Incluir **relaciones entre lugares**: si un monumento se construyó con material de otro, si un emperador conecta dos sitios, si una leyenda une varios puntos de la ciudad, etc.
- Las leyendas, mitos fundacionales y tradiciones populares son contenido valioso — incluirlas señalando que son tradición/leyenda.
- Buscar el ángulo narrativo que haga cada lugar memorable.

### 6. Encabezado de lugar — campos mínimos

```yaml
lugar:
  nombre_original: ""
  pais: ""
  fecha_visita: ""             # ISO 8601: YYYY-MM-DD o rango
```

Campos opcionales (incluir solo si se conocen o son relevantes): `nombre_alternativo`, `region_admin`, `coordenadas`, `altitud_m`.

### 7. Estructura de contenido sugerida

Cada lugar puede incluir las secciones que sean relevantes. No es obligatorio completar todas:

- **Historia** — Origen, construcción, transformaciones, eventos clave.
- **Mitología y leyendas** — Mitos fundacionales, tradiciones populares, historias asociadas.
- **Cultura** — Significado cultural, influencia artística, uso actual.
- **Conexiones** — Relación con otros lugares del repositorio o de la misma ciudad/región.
- **Datos interesantes** — Curiosidades verificables que enriquezcan la visita.

### 8. Contexto temporal

- Incluir cuándo ocurrió la visita y en qué época histórica se enmarca el lugar.
- No hace falta un bloque formal separado; puede integrarse en la narrativa.

---

## Reglas de comportamiento general

### 9. No asumir en caso de ambigüedad

- Si el contexto es ambiguo (ej. dos ciudades con el mismo nombre), marcar con `[AMBIGÜEDAD — especificar país/región]`.

### 10. Fotos y metadata

- No inferir información a partir del nombre de archivo de una foto. Si se necesita metadata EXIF, extraerla explícitamente o marcar como `pendiente`.
- Para cada lugar nuevo referenciado, agregar una imagen de mapa con pin de ubicación en la carpeta `fotos/` de la ciudad (ej.: `ciudades/Roma/fotos/mapa_colosseo.png`).
- La imagen de mapa debe insertarse en el markdown del lugar con sintaxis de imagen y texto alternativo descriptivo.
- Si no se pudo generar la imagen de mapa, marcar explícitamente `[DATO PENDIENTE — generar mapa con pin]`.

### 10.1 Flujo recomendado para mapas

- Usar el script reusable en `tools/maps/generate_static_maps.py` con un JSON de entrada para generar mapas estáticos.
- Mantener consistencia de nombres de archivo: `mapa_<nombre_lugar>.png` en minúsculas y con `_`.
- No usar capturas ambiguas sin pin visible del lugar.

### 11. Idioma de trabajo

- El repositorio opera en español como idioma principal.
- Los nombres propios se preservan en su lengua original (ver regla 2).

---

## Señales de alerta — detener y marcar

Claude debe insertar `[⚠ VERIFICAR]` cuando:

- Afirme una clasificación oficial (UNESCO, Patrimonio Nacional, etc.) sin estar seguro de su vigencia
- Contradiga información ya existente en otro archivo del repositorio
- Un dato cuantitativo específico (fechas exactas, dimensiones, cifras) no pueda verificarse con confianza

---

## Lo que Claude NO debe hacer

- Inventar datos factuales o fabricar citas
- Reescribir notas personales cambiando el tono o el punto de vista del autor
- Traducir nombres de lugares salvo instrucción explícita
- Usar fuentes generadas por IA como respaldo de ningún dato
- Presentar leyendas o tradiciones como hechos históricos sin distinguirlas

---

*Estas instrucciones aplican a todas las interacciones de Claude en este repositorio. La riqueza narrativa y la precisión factual van de la mano.*

---

## Workflow — Agregar una nueva ciudad o lugar

Seguir este flujo exacto y completo. No saltear pasos ni cambiar el orden.

### Paso 1 — Estructura de carpetas

Crear antes de crear ningún archivo:
```
ciudades/NombreCiudad/fotos/
ciudades/NombreCiudad/lugares/
```

### Paso 2 — Archivo principal de ciudad (`ciudades/NombreCiudad/nombreciudad.md`)

- Frontmatter YAML: `nombre_original`, `pais`, `region_admin`, `coordenadas`, `altitud_m`, `fecha_visita`
- Historia completa y rica (no superficial): origen, apogeo, personajes clave, datos sorprendentes
- Geografía urbana, legado artístico/científico, logística/itinerario si aplica
- Lista final de lugares documentados con links relativos a `lugares/`
- Fuentes al pie

### Paso 3 — Archivos de lugares (`ciudades/NombreCiudad/lugares/nombre_lugar.md`)

Frontmatter YAML igual que ciudad. Inmediatamente después del frontmatter, el bloque:

```markdown
![Mapa con pin de X](../fotos/mapa_x.png)

> [DATO PENDIENTE — generar mapa con pin]
```

Secciones de contenido (incluir las relevantes): Historia (con timeline en tabla), Mitología y leyendas (identificadas como tal), Arquitectura, Qué se puede ver, Conexiones, Datos interesantes, Fuentes.

Normas: `[⚠ VERIFICAR]` para datos cuantitativos no confirmados; `[DATO PENDIENTE — verificar fuente]` para datos que faltan; nombres propios en grafía original.

### Paso 4 — JSON de mapas (`tools/maps/nombreciudad_places.json`)

```json
[{
  "nombre": "Nombre del lugar",
  "archivo": "mapa_nombre_lugar.png",
  "lat": 00.0000,
  "lon": 00.0000,
  "referencias": [{ "nombre": "Lugar cercano", "lat": 00.0, "lon": 00.0 }]
}]
```

El campo `"archivo"` debe coincidir exactamente con el placeholder en el `.md`. Convención: `mapa_<nombre_lugar>.png` en minúsculas con `_`.

### Paso 5 — Generar los mapas

```bash
source .venv/bin/activate
python tools/maps/generate_static_maps.py \
  --input tools/maps/nombreciudad_places.json \
  --output ciudades/NombreCiudad/fotos \
  --no-city-context
```

Genera `mapa_x.png` + `mapa_x_detalle.png` por cada lugar.

**⚠ Bug conocido: ENOPRO en dev containers.** En Codespaces / dev containers, `run_in_terminal` falla frecuentemente con `ENOPRO: No se ha encontrado ningún proveedor de sistema de archivos`. Es un problema de Copilot, no del comando. **Protocolo**: intentar `run_in_terminal` **una sola vez**. Si falla con ENOPRO, dar inmediatamente el comando exacto al usuario. No reintentar.

### Paso 6 — Actualizar los .md con los mapas reales

Reemplazar en cada `.md` (usar `multi_replace_string_in_file` para hacerlo todo en una llamada):

```
# Antes:
![Mapa con pin de X](../fotos/mapa_x.png)
> [DATO PENDIENTE — generar mapa con pin]

# Después:
![Mapa con pin de X](../fotos/mapa_x.png)
![Mapa detalle de X](../fotos/mapa_x_detalle.png)
```

### Paso 7 — Generar audios y player web

Usar el script genérico `tools/audio/build_audio_site.sh` que genera MP3 a partir de los `.md` y reconstruye el player HTML:

```bash
# Solo una ciudad
./tools/audio/build_audio_site.sh ciudades/NombreCiudad/

# Todo el repositorio
./tools/audio/build_audio_site.sh

# Forzar regeneración (ignorar cache)
./tools/audio/build_audio_site.sh ciudades/NombreCiudad/ --force
```

El script:
1. Activa `.venv` (o lo crea si no existe)
2. Instala `edge-tts` y `mutagen` si faltan
3. Genera MP3 en `docs/audio/NombreCiudad/` (un archivo por `.md` con contenido narrativo)
4. Regenera `docs/index.html` con el player web actualizado
5. Crea `docs/.nojekyll` para GitHub Pages

**⚠ Bug ENOPRO**: aplica el mismo protocolo del Paso 5. Intentar una vez; si falla, dar el comando al usuario.

### Paso 8 — Verificar coherencia

- Todos los lugares del `.md` principal tienen su archivo en `lugares/`
- Todos los `../fotos/mapa_x.png` existen físicamente
- No quedan `> [DATO PENDIENTE — generar mapa con pin]` en ningún `.md`
- Links del archivo principal apuntan correctamente a los lugares
- Los MP3 existen en `docs/audio/NombreCiudad/`
- `docs/data/catalog.json` incluye la nueva ciudad (lo genera automáticamente `build_audio_site.sh`)
- `docs/data/places.json` incluye la nueva ciudad con coordenadas y lugares — **alimenta el mapa interactivo**
- `docs/data/events.json` incluye eventos históricos de la nueva ciudad (opcional, solo si hay eventos relevantes para el timeline)
- `docs/js/vitacora.js` → array `CIUDADES` incluye la nueva ciudad (hardcodeado, orden alfabético)
- Los 4 archivos de nav (`index.html`, `mapa.html`, `timeline.html`, `vitacora.html`) tienen links consistentes entre sí

### Ciudades existentes (referencia)

| Ciudad | Carpeta | JSON de mapas |
|---|---|---|
| Roma | `ciudades/Roma/` | `tools/maps/roma_places.json` |
| Firenze | `ciudades/Firenze/` | `tools/maps/firenze_places.json` |
| Lucca | `ciudades/Lucca/` | `tools/maps/lucca_places.json` |
| Pisa | `ciudades/Pisa/` | `tools/maps/pisa_places.json` |
| Granada | `ciudades/Granada/` | — |
| Madrid | `ciudades/Madrid/` | `tools/maps/madrid_places.json` |
| Benalmádena | `ciudades/Benalmadena/` | `tools/maps/benalmadena_places.json` |
| Málaga | `ciudades/Malaga/` | `tools/maps/malaga_places.json` |
| Toledo | `ciudades/Toledo/` | `tools/maps/toledo_places.json` |
