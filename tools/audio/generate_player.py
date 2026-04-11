#!/usr/bin/env python3
"""
Genera un player web estático (HTML single-page) a partir de los MP3 generados.

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


def scan_audio_dir(audio_dir: Path) -> dict[str, list[dict]]:
    """
    Escanea la carpeta de audio y construye un catálogo.
    Retorna: {ciudad: [{name, file, duration, duration_fmt}]}
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
            # Nombre legible: reemplazar _ por espacios, capitalizar
            display_name = mp3.stem.replace("_", " ").title()

            tracks.append({
                "name": display_name,
                "file": f"audio/{city_name}/{mp3.name}",
                "duration": duration,
                "duration_fmt": format_duration(duration),
            })

        if tracks:
            catalog[city_name] = tracks

    return catalog


def generate_html(catalog: dict[str, list[dict]]) -> str:
    """Genera el HTML completo del player."""

    # Serializar catálogo para JS
    catalog_json = json.dumps(catalog, ensure_ascii=False, indent=2)

    return f"""<!DOCTYPE html>
<html lang="es">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0, user-scalable=no">
<meta name="apple-mobile-web-app-capable" content="yes">
<meta name="apple-mobile-web-app-status-bar-style" content="black-translucent">
<title>Archivo de Viajes — Audio</title>
<style>
* {{ margin: 0; padding: 0; box-sizing: border-box; }}

:root {{
  --bg: #1a1a2e;
  --bg-card: #16213e;
  --bg-player: #0f3460;
  --accent: #e94560;
  --accent-light: #f07b8d;
  --text: #eaeaea;
  --text-muted: #8b8fa3;
  --text-dim: #5c6078;
  --border: #2a2d45;
  --success: #4ecca3;
}}

html, body {{
  font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
  background: var(--bg);
  color: var(--text);
  min-height: 100vh;
  -webkit-tap-highlight-color: transparent;
}}

body {{
  padding-bottom: 140px;
}}

header {{
  background: linear-gradient(135deg, var(--bg-player) 0%, var(--bg-card) 100%);
  padding: 24px 20px 20px;
  text-align: center;
  border-bottom: 1px solid var(--border);
  position: sticky;
  top: 0;
  z-index: 10;
}}

header h1 {{
  font-size: 1.3rem;
  font-weight: 600;
  letter-spacing: 0.5px;
}}

header p {{
  color: var(--text-muted);
  font-size: 0.85rem;
  margin-top: 4px;
}}

.container {{
  max-width: 600px;
  margin: 0 auto;
  padding: 16px;
}}

/* Ciudades */
.city {{
  margin-bottom: 16px;
}}

.city-header {{
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 14px 16px;
  background: var(--bg-card);
  border-radius: 12px;
  cursor: pointer;
  border: 1px solid var(--border);
  transition: background 0.2s;
  -webkit-user-select: none;
  user-select: none;
}}

.city-header:active {{
  background: var(--bg-player);
}}

.city-header h2 {{
  font-size: 1.05rem;
  font-weight: 600;
}}

.city-header .count {{
  color: var(--text-muted);
  font-size: 0.8rem;
}}

.city-header .chevron {{
  color: var(--text-muted);
  transition: transform 0.3s;
  font-size: 1.2rem;
}}

.city.open .chevron {{
  transform: rotate(90deg);
}}

.track-list {{
  display: none;
  padding: 8px 0 0;
}}

.city.open .track-list {{
  display: block;
}}

/* Tracks */
.track {{
  display: flex;
  align-items: center;
  padding: 12px 16px;
  margin: 4px 0;
  background: var(--bg-card);
  border-radius: 10px;
  cursor: pointer;
  border: 1px solid transparent;
  transition: all 0.2s;
}}

.track:active {{
  background: var(--bg-player);
}}

.track.active {{
  border-color: var(--accent);
  background: rgba(233, 69, 96, 0.08);
}}

.track-icon {{
  width: 36px;
  height: 36px;
  border-radius: 50%;
  background: var(--bg-player);
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
  margin-right: 12px;
  font-size: 0.9rem;
}}

.track.active .track-icon {{
  background: var(--accent);
}}

.track-info {{
  flex: 1;
  min-width: 0;
}}

.track-name {{
  font-size: 0.92rem;
  font-weight: 500;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}}

.track-duration {{
  color: var(--text-muted);
  font-size: 0.78rem;
  margin-top: 2px;
}}

/* Player fijo abajo */
#player {{
  position: fixed;
  bottom: 0;
  left: 0;
  right: 0;
  background: var(--bg-player);
  border-top: 1px solid var(--border);
  padding: 12px 16px env(safe-area-inset-bottom, 12px);
  z-index: 100;
  transition: transform 0.3s;
}}

#player.hidden {{
  transform: translateY(100%);
}}

#player-track-name {{
  font-size: 0.85rem;
  font-weight: 500;
  text-align: center;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  margin-bottom: 8px;
  color: var(--text);
}}

.progress-container {{
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 10px;
}}

.time {{
  font-size: 0.72rem;
  color: var(--text-muted);
  min-width: 38px;
  text-align: center;
  font-variant-numeric: tabular-nums;
}}

.progress-bar {{
  flex: 1;
  height: 6px;
  background: var(--border);
  border-radius: 3px;
  position: relative;
  cursor: pointer;
  -webkit-tap-highlight-color: transparent;
}}

.progress-fill {{
  height: 100%;
  background: var(--accent);
  border-radius: 3px;
  width: 0%;
  position: relative;
  transition: width 0.1s linear;
}}

.progress-fill::after {{
  content: "";
  position: absolute;
  right: -6px;
  top: -5px;
  width: 16px;
  height: 16px;
  border-radius: 50%;
  background: var(--accent-light);
  opacity: 0;
  transition: opacity 0.2s;
}}

.progress-bar:active .progress-fill::after {{
  opacity: 1;
}}

.controls {{
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 24px;
}}

.ctrl-btn {{
  background: none;
  border: none;
  color: var(--text);
  font-size: 1.4rem;
  cursor: pointer;
  padding: 8px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: color 0.2s;
  -webkit-tap-highlight-color: transparent;
}}

.ctrl-btn:active {{
  color: var(--accent);
}}

.ctrl-btn.play {{
  font-size: 1.8rem;
  background: var(--accent);
  color: white;
  width: 52px;
  height: 52px;
  border-radius: 50%;
}}

.ctrl-btn.play:active {{
  background: var(--accent-light);
}}

.speed-btn {{
  font-size: 0.78rem;
  font-weight: 700;
  min-width: 44px;
  color: var(--text-muted);
}}

.speed-btn.active-speed {{
  color: var(--accent);
}}

/* Empty state */
.empty {{
  text-align: center;
  padding: 60px 20px;
  color: var(--text-muted);
}}

.empty h2 {{
  font-size: 1.2rem;
  margin-bottom: 8px;
  color: var(--text);
}}

/* Scrollbar */
::-webkit-scrollbar {{ width: 4px; }}
::-webkit-scrollbar-track {{ background: var(--bg); }}
::-webkit-scrollbar-thumb {{ background: var(--border); border-radius: 2px; }}
</style>
</head>
<body>

<header>
  <h1>🎧 Archivo de Viajes</h1>
  <p>Audio guías de ciudades y lugares</p>
</header>

<div class="container" id="app"></div>

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

<script>
const CATALOG = {catalog_json};

const SPEEDS = [0.75, 1, 1.25, 1.5, 1.75];
let speedIdx = 1;

const audio = new Audio();
let currentCity = null;
let currentTrackIdx = -1;
let allTracks = []; // flat list: {{city, idx, name, file}}

// Build flat track list
for (const [city, tracks] of Object.entries(CATALOG)) {{
  tracks.forEach((t, i) => {{
    allTracks.push({{ city, idx: i, name: t.name, file: t.file, cityTrack: t }});
  }});
}}

// DOM refs
const app = document.getElementById("app");
const player = document.getElementById("player");
const playerName = document.getElementById("player-track-name");
const btnPlay = document.getElementById("btn-play");
const btnPrev = document.getElementById("btn-prev");
const btnNext = document.getElementById("btn-next");
const btnBack = document.getElementById("btn-back");
const btnFwd = document.getElementById("btn-fwd");
const btnSpeed = document.getElementById("btn-speed");
const progressBar = document.getElementById("progress-bar");
const progressFill = document.getElementById("progress-fill");
const timeCurrent = document.getElementById("time-current");
const timeTotal = document.getElementById("time-total");

// Render catalog
function render() {{
  if (Object.keys(CATALOG).length === 0) {{
    app.innerHTML = '<div class="empty"><h2>No hay audios disponibles</h2><p>Ejecutá el pipeline para generar los MP3</p></div>';
    return;
  }}

  let html = "";
  for (const [city, tracks] of Object.entries(CATALOG)) {{
    html += `<div class="city" data-city="${{city}}">`;
    html += `<div class="city-header" onclick="toggleCity(this.parentElement)">`;
    html += `<div><h2>${{city}}</h2><span class="count">${{tracks.length}} audio${{tracks.length !== 1 ? "s" : ""}}</span></div>`;
    html += `<span class="chevron">›</span>`;
    html += `</div>`;
    html += `<div class="track-list">`;

    tracks.forEach((t, i) => {{
      const dur = t.duration_fmt ? `<div class="track-duration">${{t.duration_fmt}}</div>` : "";
      html += `<div class="track" data-city="${{city}}" data-idx="${{i}}" onclick="playTrack('${{city}}', ${{i}})">`;
      html += `<div class="track-icon">▶</div>`;
      html += `<div class="track-info"><div class="track-name">${{t.name}}</div>${{dur}}</div>`;
      html += `</div>`;
    }});

    html += `</div></div>`;
  }}
  app.innerHTML = html;
}}

function toggleCity(el) {{
  el.classList.toggle("open");
}}

// Playback
function playTrack(city, idx) {{
  const track = CATALOG[city][idx];
  if (!track) return;

  currentCity = city;
  currentTrackIdx = idx;

  audio.src = track.file;
  audio.playbackRate = SPEEDS[speedIdx];
  audio.play();

  playerName.textContent = `${{city}} — ${{track.name}}`;
  player.classList.remove("hidden");
  btnPlay.textContent = "⏸";

  // Highlight active track
  document.querySelectorAll(".track").forEach(el => el.classList.remove("active"));
  const active = document.querySelector(`.track[data-city="${{city}}"][data-idx="${{idx}}"]`);
  if (active) {{
    active.classList.add("active");
    // Expand city
    active.closest(".city").classList.add("open");
  }}
}}

function getFlatIdx() {{
  return allTracks.findIndex(t => t.city === currentCity && t.idx === currentTrackIdx);
}}

function playFlatIdx(fi) {{
  if (fi >= 0 && fi < allTracks.length) {{
    playTrack(allTracks[fi].city, allTracks[fi].idx);
  }}
}}

// Controls
btnPlay.addEventListener("click", () => {{
  if (audio.paused) {{
    if (!audio.src || audio.src === location.href) {{
      // Nothing loaded, play first track
      if (allTracks.length > 0) playTrack(allTracks[0].city, allTracks[0].idx);
      return;
    }}
    audio.play();
    btnPlay.textContent = "⏸";
  }} else {{
    audio.pause();
    btnPlay.textContent = "▶";
  }}
}});

btnPrev.addEventListener("click", () => {{
  const fi = getFlatIdx();
  if (fi > 0) playFlatIdx(fi - 1);
}});

btnNext.addEventListener("click", () => {{
  const fi = getFlatIdx();
  playFlatIdx(fi + 1);
}});

btnBack.addEventListener("click", () => {{
  audio.currentTime = Math.max(0, audio.currentTime - 15);
}});

btnFwd.addEventListener("click", () => {{
  audio.currentTime = Math.min(audio.duration || 0, audio.currentTime + 15);
}});

btnSpeed.addEventListener("click", () => {{
  speedIdx = (speedIdx + 1) % SPEEDS.length;
  audio.playbackRate = SPEEDS[speedIdx];
  btnSpeed.textContent = SPEEDS[speedIdx] + "x";
  btnSpeed.classList.toggle("active-speed", speedIdx !== 1);
}});

// Progress bar
function fmtTime(s) {{
  if (isNaN(s) || s < 0) return "0:00";
  const m = Math.floor(s / 60);
  const sec = Math.floor(s % 60);
  return m + ":" + String(sec).padStart(2, "0");
}}

audio.addEventListener("timeupdate", () => {{
  if (audio.duration) {{
    const pct = (audio.currentTime / audio.duration) * 100;
    progressFill.style.width = pct + "%";
    timeCurrent.textContent = fmtTime(audio.currentTime);
    timeTotal.textContent = fmtTime(audio.duration);
  }}
}});

audio.addEventListener("ended", () => {{
  btnPlay.textContent = "▶";
  // Auto-play next
  const fi = getFlatIdx();
  if (fi + 1 < allTracks.length) {{
    playFlatIdx(fi + 1);
  }}
}});

// Seek
function seek(e) {{
  if (!audio.duration) return;
  const rect = progressBar.getBoundingClientRect();
  const pct = Math.max(0, Math.min(1, (e.clientX - rect.left) / rect.width));
  audio.currentTime = pct * audio.duration;
}}

progressBar.addEventListener("click", seek);

// Touch seek
let seeking = false;
progressBar.addEventListener("touchstart", (e) => {{
  seeking = true;
  seek(e.touches[0]);
}}, {{ passive: true }});
progressBar.addEventListener("touchmove", (e) => {{
  if (seeking) seek(e.touches[0]);
}}, {{ passive: true }});
progressBar.addEventListener("touchend", () => {{ seeking = false; }});

// Media Session API (lock screen controls)
if ("mediaSession" in navigator) {{
  audio.addEventListener("play", () => {{
    const track = currentCity && CATALOG[currentCity] ? CATALOG[currentCity][currentTrackIdx] : null;
    if (track) {{
      navigator.mediaSession.metadata = new MediaMetadata({{
        title: track.name,
        artist: currentCity,
        album: "Archivo de Viajes"
      }});
    }}
    navigator.mediaSession.playbackState = "playing";
  }});

  audio.addEventListener("pause", () => {{
    navigator.mediaSession.playbackState = "paused";
  }});

  navigator.mediaSession.setActionHandler("play", () => {{ audio.play(); btnPlay.textContent = "⏸"; }});
  navigator.mediaSession.setActionHandler("pause", () => {{ audio.pause(); btnPlay.textContent = "▶"; }});
  navigator.mediaSession.setActionHandler("previoustrack", () => {{
    const fi = getFlatIdx();
    if (fi > 0) playFlatIdx(fi - 1);
  }});
  navigator.mediaSession.setActionHandler("nexttrack", () => {{
    const fi = getFlatIdx();
    playFlatIdx(fi + 1);
  }});
  navigator.mediaSession.setActionHandler("seekbackward", () => {{
    audio.currentTime = Math.max(0, audio.currentTime - 15);
  }});
  navigator.mediaSession.setActionHandler("seekforward", () => {{
    audio.currentTime = Math.min(audio.duration || 0, audio.currentTime + 15);
  }});
}}

// Init
render();
</script>
</body>
</html>"""


def main():
    parser = argparse.ArgumentParser(
        description="Genera un player web estático a partir de los MP3 generados"
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

    print(f"Escaneando audio en: {audio_dir}")
    catalog = scan_audio_dir(audio_dir)

    total_tracks = sum(len(tracks) for tracks in catalog.values())
    print(f"Encontradas {len(catalog)} ciudades con {total_tracks} tracks total")

    if not catalog:
        print("Advertencia: no se encontraron MP3. El player se generará vacío.")

    html = generate_html(catalog)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(html, encoding="utf-8")

    print(f"Player generado: {output_path}")
    print(f"Tamaño: {output_path.stat().st_size / 1024:.1f} KB")


if __name__ == "__main__":
    main()
