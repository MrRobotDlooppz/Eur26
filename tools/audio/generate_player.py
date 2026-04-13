#!/usr/bin/env python3
"""
Genera el catálogo JSON y el player web estático a partir de los MP3 generados.

Uso:
    python tools/audio/generate_player.py
    python tools/audio/generate_player.py --audio-dir docs/audio --output docs/index.html
"""

import argparse
import json
import sys
from pathlib import Path

try:
    from mutagen.mp3 import MP3

    def get_duration(mp3_path: Path) -> float:
        """Retorna duración en segundos."""
        try:
            return MP3(str(mp3_path)).info.length
        except Exception:
            return 0.0
except ImportError:
    def get_duration(mp3_path: Path) -> float:
        return 0.0


def format_duration(seconds: float) -> str:
    """Formatea duración en mm:ss."""
    if seconds <= 0:
        return ""
    m, s = divmod(int(seconds), 60)
    return f"{m}:{s:02d}"


def scan_audio_dir(audio_dir: Path, text_dir: Path = None) -> dict[str, list[dict]]:
    """
    Escanea la carpeta de audio y construye un catálogo.
    Retorna: {ciudad: [{name, file, duration, duration_fmt, text?}]}
    """
    catalog = {}

    if not audio_dir.exists():
        return catalog

    for city_dir in sorted(audio_dir.iterdir()):
        if not city_dir.is_dir():
            continue

        city_name = city_dir.name
        tracks = []

        for mp3 in sorted(city_dir.glob("*.mp3")):
            duration = get_duration(mp3)
            display_name = mp3.stem.replace("_", " ").title()

            track = {
                "name": display_name,
                "file": f"audio/{city_name}/{mp3.name}",
                "duration": duration,
                "duration_fmt": format_duration(duration),
            }

            # Check if text guide exists
            if text_dir:
                text_file = text_dir / city_name / f"{mp3.stem}.html"
                if text_file.exists():
                    track["text"] = f"text/{city_name}/{mp3.stem}.html"

            tracks.append(track)

        if tracks:
            catalog[city_name] = tracks

    return catalog


def generate_html() -> str:
    """Genera un HTML ligero que importa CSS/JS externos y carga datos vía fetch."""
    return """<!DOCTYPE html>
<html lang="es">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0, user-scalable=no">
<meta name="apple-mobile-web-app-capable" content="yes">
<meta name="apple-mobile-web-app-status-bar-style" content="black-translucent">
<title>Archivo de Viajes — Audio</title>
<link rel="stylesheet" href="css/theme.css">
<link rel="stylesheet" href="css/player.css">
</head>
<body>

<header>
  <h1>🎧 Archivo de Viajes</h1>
  <p>Audio guías de ciudades y lugares</p>
  <nav style="margin-top:10px;display:flex;justify-content:center;gap:12px;">
    <a href="index.html" class="active" style="background:rgba(233,69,96,0.15);color:var(--accent);">🎧 Audio</a>
    <a href="mapa.html">🗺️ Mapa</a>
    <a href="timeline.html">⏳ Timeline</a>
  </nav>
</header>

<div class="container" id="app"></div>

<div id="guide-panel" class="guide-panel">
  <div class="container">
    <div class="guide-header">
      <h3 id="guide-title">📖 Guía</h3>
      <button class="guide-close-btn" onclick="closeGuide()" title="Cerrar">✕</button>
    </div>
    <div class="guide-content" id="guide-content"></div>
  </div>
</div>

<div id="player" class="hidden">
  <div id="player-track-name">—</div>
  <div class="progress-container">
    <span class="time" id="time-current">0:00</span>
    <div class="progress-bar" id="progress-bar">
      <div class="progress-fill" id="progress-fill"></div>
    </div>
    <span class="time" id="time-total">0:00</span>
  </div>
  <div class="controls">
    <button class="ctrl-btn" id="btn-prev" title="Anterior">⏮</button>
    <button class="ctrl-btn" id="btn-back" title="Retroceder 15s">↩️</button>
    <button class="ctrl-btn play" id="btn-play" title="Play">▶</button>
    <button class="ctrl-btn" id="btn-fwd" title="Adelantar 15s">↪️</button>
    <button class="ctrl-btn" id="btn-next" title="Siguiente">⏭</button>
    <button class="ctrl-btn speed-btn" id="btn-speed" title="Velocidad">1x</button>
  </div>
</div>

<script src="js/shared.js"></script>
<script src="js/player.js"></script>
</body>
</html>"""


def main():
    parser = argparse.ArgumentParser(
        description="Genera catálogo JSON y player web a partir de los MP3 generados"
    )
    parser.add_argument(
        "--audio-dir",
        type=str,
        default="docs/audio",
        help="Carpeta con los MP3 organizados por ciudad (default: docs/audio/)"
    )
    parser.add_argument(
        "--output", "-o",
        type=str,
        default="docs/index.html",
        help="Archivo HTML de salida (default: docs/index.html)"
    )

    args = parser.parse_args()

    repo_root = Path(__file__).resolve().parent.parent.parent
    audio_dir = Path(args.audio_dir)
    if not audio_dir.is_absolute():
        audio_dir = repo_root / audio_dir

    output_path = Path(args.output)
    if not output_path.is_absolute():
        output_path = repo_root / output_path

    docs_dir = output_path.parent
    text_dir = docs_dir / "text"
    data_dir = docs_dir / "data"

    print(f"Escaneando audio en: {audio_dir}")
    catalog = scan_audio_dir(audio_dir, text_dir if text_dir.exists() else None)

    total_tracks = sum(len(tracks) for tracks in catalog.values())
    print(f"Encontradas {len(catalog)} ciudades con {total_tracks} tracks total")

    if not catalog:
        print("Advertencia: no se encontraron MP3. El player se generará vacío.")

    # Write catalog.json
    data_dir.mkdir(parents=True, exist_ok=True)
    catalog_path = data_dir / "catalog.json"
    catalog_path.write_text(json.dumps(catalog, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Catálogo JSON: {catalog_path} ({catalog_path.stat().st_size / 1024:.1f} KB)")

    # Write index.html
    html = generate_html()
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(html, encoding="utf-8")

    print(f"Player generado: {output_path}")
    print(f"Tamaño: {output_path.stat().st_size / 1024:.1f} KB")


if __name__ == "__main__":
    main()
