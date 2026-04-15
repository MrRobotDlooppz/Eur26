# Archivo de Viajes

Archivo personal de notas históricas, culturales y audio guías de ciudades visitadas.

🌐 **[Ver sitio en vivo](https://mrrobotdlooppz.github.io/Eur26/)**

## Qué es

Un repositorio que combina investigación histórica con herramientas interactivas para explorar lugares visitados. Cada ciudad tiene guías detalladas en Markdown con historia, leyendas, mitología, arquitectura y datos interesantes — todo verificado y con fuentes.

## Features

- **🎧 Audio guías** — Las guías .md se convierten automáticamente en MP3 (text-to-speech) con un player web integrado
- **📖 Panel de texto** — Al escuchar un audio, podés ver la guía original con el botón 📖
- **🗺️ Mapa interactivo** — Todos los lugares en un mapa Leaflet con pins por ciudad. Click en un lugar te lleva a su guía
- **⏳ Línea de tiempo** — 64 eventos desde el 700 a.C. hasta hoy, filtrable por ciudad. Click en un evento te lleva a su guía
- **📝 Vitácora colaborativa** — Diario de viaje con autenticación, entradas por ciudad, imágenes inline (desde galería/cámara) y lightbox
- **🔗 Todo conectado** — Deep links entre mapa, timeline y player permiten navegar entre las tres vistas

## Ciudades

| Ciudad | País | Lugares |
|--------|------|---------|
| Roma | Italia | 21 |
| Firenze | Italia | 22 |
| Lucca | Italia | 7 |
| Pisa | Italia | 7 |
| Granada | España | 8 |
| Madrid | España | 11 |

## Estructura

```
ciudades/{Ciudad}/
  lugares/          ← guías .md individuales
  fotos/            ← mapas estáticos con pin
docs/               ← sitio web (GitHub Pages)
  audio/            ← MP3 generados
  text/             ← HTML de guías (para el panel 📖)
  data/             ← JSON de datos (catalog, places, events)
  css/ js/          ← frontend modular
tools/
  audio/            ← pipeline: .md → MP3 + HTML + player
  maps/             ← generador de mapas estáticos
```

## Pipeline

```bash
# Generar todo (audio + texto + player + mapa + timeline)
./tools/audio/build_audio_site.sh

# Solo una ciudad
./tools/audio/build_audio_site.sh ciudades/Firenze/

# Forzar regeneración
./tools/audio/build_audio_site.sh --force
```

Requiere Python 3.10+ con `edge-tts`, `mutagen` y `markdown` (se instalan automáticamente).
