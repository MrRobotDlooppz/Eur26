# Audio — Archivo de Viajes

Convierte los archivos `.md` del repositorio en MP3 narrados y genera un player web mobile-friendly servido via GitHub Pages.

## Requisitos

- Python 3.10+
- Conexión a internet (edge-tts usa los servidores de Microsoft Edge)

## Uso rápido

```bash
# Desde la raíz del repo:
chmod +x tools/audio/build_audio_site.sh
./tools/audio/build_audio_site.sh
```

Esto:
1. Instala `edge-tts` y `mutagen` en el venv
2. Convierte todos los `.md` de ciudades y lugares en MP3
3. Genera el player web en `docs/index.html`

## Uso individual

### Generar audio de un solo archivo

```bash
python tools/audio/generate_audio.py --input Lucca/lugares/torre_guinigi.md
```

### Generar audio de una ciudad

```bash
python tools/audio/generate_audio.py --input Firenze/
```

### Regenerar todo (ignorar cache)

```bash
python tools/audio/generate_audio.py --input . --force
```

### Cambiar voz

```bash
# Listar voces disponibles en español
python tools/audio/generate_audio.py --list-voices

# Usar una voz específica
python tools/audio/generate_audio.py --input . --voice es-ES-ElviraNeural
```

### Solo regenerar el player HTML (sin regenerar audio)

```bash
python tools/audio/generate_player.py
```

## Voces recomendadas

| Voz | Locale | Género | Notas |
|---|---|---|---|
| `es-MX-DaliaNeural` | México | Femenina | **Default** — clara, ritmo natural |
| `es-AR-ElenaNeural` | Argentina | Femenina | Acento rioplatense |
| `es-ES-ElviraNeural` | España | Femenina | Acento castellano |
| `es-MX-JorgeNeural` | México | Masculina | Clara, neutra |
| `es-ES-AlvaroNeural` | España | Masculina | Acento castellano |

Listado completo: `python tools/audio/generate_audio.py --list-voices`

## Estructura de salida

```
docs/
  index.html          ← Player web (abrir en navegador)
  .nojekyll           ← Flag para GitHub Pages
  audio/
    Firenze/
      firenze.mp3
      ponte_vecchio.mp3
      galleria_degli_uffizi.mp3
      ...
    Rome/
      ...
    Granada/
      ...
```

## GitHub Pages

Para publicar el player online:

1. `git add docs/` y hacer push
2. Ir a **Settings → Pages**
3. Source: **Deploy from a branch**
4. Branch: **main**, folder: **/docs**
5. Guardar — el sitio estará en `https://<usuario>.github.io/Eur26/`

## Cómo funciona

### Pipeline

```
.md → clean_md_to_text() → texto plano narrable → edge-tts → .mp3
                                                              ↓
                                          scan + generate → index.html
```

### Limpieza de Markdown

El script limpia automáticamente:
- Bloques YAML frontmatter
- Imágenes y mapas (`![...](..)`)
- Comentarios HTML (`<!-- ... -->`)
- Marcadores `[DATO PENDIENTE...]` y `[⚠ VERIFICAR]`
- Tablas → se convierten en texto narrativo ("En 1345, se construye...")
- Separadores `---`
- Bloques de fuentes al pie
- Sintaxis Markdown (`**bold**`, `*italic*`, `[links](url)`) → texto plano

### Cache

Por defecto, el script solo regenera un MP3 si el archivo `.md` fuente es más nuevo que el `.mp3` existente. Usar `--force` para regenerar todo.

### Player web

- Single-page HTML, sin dependencias externas
- Mobile-first — funciona en iPhone y Android
- Player fijo abajo con play/pause, seek, velocidad (0.75x–1.75x)
- Reproducción secuencial automática dentro de cada ciudad
- Controles de lock screen (Media Session API) — funciona con auriculares
- Tema oscuro suave
