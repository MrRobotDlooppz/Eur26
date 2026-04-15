/* ============================================
   Player — Guías de texto con audio inline
   ============================================ */

let CATALOG = {};

const SPEEDS = [0.75, 1, 1.25, 1.5, 1.75];
let speedIdx = 1;

const audio = new Audio();
let currentCity = null;
let currentTrackIdx = -1;
let guideCache = {}; // cache de textos de guía cargados

const app = document.getElementById("app");

// ── Init ──────────────────────────────────────
async function initPlayer() {
  try {
    const resp = await fetch("data/catalog.json");
    CATALOG = await resp.json();
  } catch (e) {
    console.error("Error cargando catálogo:", e);
    app.innerHTML = '<div class="empty"><h2>Error cargando datos</h2><p>No se pudo cargar data/catalog.json</p></div>';
    return;
  }

  render();
  setupAudioEvents();
  setupMediaSession();
  handleDeepLink();
}

// ── Render ────────────────────────────────────
function render() {
  if (Object.keys(CATALOG).length === 0) {
    app.innerHTML = '<div class="empty"><h2>No hay guías disponibles</h2><p>Ejecutá el pipeline para generar los textos</p></div>';
    return;
  }

  let html = "";
  for (const [city, tracks] of Object.entries(CATALOG)) {
    html += `<div class="city" data-city="${city}">`;
    html += `<div class="city-header" onclick="toggleCity(this.parentElement)">`;
    html += `<div><h2>${city}</h2><span class="count">${tracks.length} guía${tracks.length !== 1 ? "s" : ""}</span></div>`;
    html += `<span class="chevron">›</span>`;
    html += `</div>`;
    html += `<div class="track-list">`;

    tracks.forEach((t, i) => {
      const dur = t.duration_fmt ? `<span class="place-duration">${t.duration_fmt}</span>` : "";
      html += `<div class="place-item" data-city="${city}" data-idx="${i}">`;
      html += `<div class="place-header" onclick="togglePlace('${city}', ${i})">`;
      html += `<div class="place-icon">📖</div>`;
      html += `<div class="place-info"><span class="place-name">${t.name}</span>${dur}</div>`;
      html += `<span class="place-chevron">›</span>`;
      html += `</div>`;
      html += `<div class="place-content"></div>`;
      html += `</div>`;
    });

    html += `</div></div>`;
  }
  app.innerHTML = html;
}

function toggleCity(el) {
  el.classList.toggle("open");
}

// ── Expand / Collapse lugar ───────────────────
async function togglePlace(city, idx) {
  const el = document.querySelector(`.place-item[data-city="${city}"][data-idx="${idx}"]`);
  if (!el) return;

  // Si ya está abierto → colapsar
  if (el.classList.contains("open")) {
    el.classList.remove("open");
    return;
  }

  // Expandir
  el.classList.add("open");

  const contentEl = el.querySelector(".place-content");
  // Si ya tiene contenido cargado, no volver a cargar
  if (contentEl.dataset.loaded) {
    el.querySelector(".place-header").scrollIntoView({ behavior: "smooth", block: "start" });
    return;
  }

  const track = CATALOG[city][idx];
  contentEl.dataset.loaded = "1";

  // Mini-player (solo si tiene audio)
  let miniPlayerHtml = "";
  if (track.file) {
    miniPlayerHtml = `
      <div class="mini-player" data-city="${city}" data-idx="${idx}">
        <button class="mp-play" onclick="event.stopPropagation(); toggleAudio('${city}', ${idx})" title="Reproducir">▶</button>
        <button class="mp-back" onclick="event.stopPropagation(); seekAudio(-15)" title="-15s">↩</button>
        <div class="mp-progress" onclick="event.stopPropagation(); seekBar(event, '${city}', ${idx})">
          <div class="mp-fill"></div>
        </div>
        <button class="mp-fwd" onclick="event.stopPropagation(); seekAudio(15)" title="+15s">↪</button>
        <span class="mp-time">0:00 / ${track.duration_fmt || "—"}</span>
        <button class="mp-speed" onclick="event.stopPropagation(); cycleSpeed()" title="Velocidad">${SPEEDS[speedIdx]}x</button>
      </div>`;
  }

  // Cargar texto
  let textHtml = "<p>Cargando guía…</p>";
  if (track.text) {
    const cacheKey = track.text;
    if (!guideCache[cacheKey]) {
      try {
        const resp = await fetch(track.text);
        if (!resp.ok) throw new Error(resp.status);
        guideCache[cacheKey] = await resp.text();
      } catch (e) {
        guideCache[cacheKey] = "<p>No se pudo cargar la guía.</p>";
      }
    }
    textHtml = guideCache[cacheKey];
  } else {
    textHtml = "<p>No hay texto disponible para este lugar.</p>";
  }

  contentEl.innerHTML = miniPlayerHtml + `<div class="place-text">${textHtml}</div>`;

  // Setup touch seek en la barra de progreso
  const progBar = contentEl.querySelector(".mp-progress");
  if (progBar) {
    let seeking = false;
    progBar.addEventListener("touchstart", (e) => {
      seeking = true;
      seekBarTouch(e.touches[0], city, idx);
    }, { passive: true });
    progBar.addEventListener("touchmove", (e) => {
      if (seeking) seekBarTouch(e.touches[0], city, idx);
    }, { passive: true });
    progBar.addEventListener("touchend", () => { seeking = false; });
  }

  // Scroll suave al contenido
  setTimeout(() => {
    el.querySelector(".place-header").scrollIntoView({ behavior: "smooth", block: "start" });
  }, 50);
}

// ── Audio playback ────────────────────────────
function toggleAudio(city, idx) {
  const track = CATALOG[city][idx];
  if (!track || !track.file) return;

  // Si es el mismo track → toggle play/pause
  if (currentCity === city && currentTrackIdx === idx) {
    if (audio.paused) {
      audio.play();
    } else {
      audio.pause();
    }
    return;
  }

  // Nuevo track → reset anterior y reproducir
  resetActiveMiniPlayer();
  currentCity = city;
  currentTrackIdx = idx;
  audio.src = track.file;
  audio.playbackRate = SPEEDS[speedIdx];
  audio.play();
}

function seekAudio(delta) {
  if (!audio.duration) return;
  audio.currentTime = Math.max(0, Math.min(audio.duration, audio.currentTime + delta));
}

function seekBar(e, city, idx) {
  // Solo permitir seek si es el track activo
  if (currentCity !== city || currentTrackIdx !== idx) {
    // Empezar a reproducir primero
    toggleAudio(city, idx);
    return;
  }
  if (!audio.duration) return;
  const rect = e.currentTarget.getBoundingClientRect();
  const pct = Math.max(0, Math.min(1, (e.clientX - rect.left) / rect.width));
  audio.currentTime = pct * audio.duration;
}

function seekBarTouch(touch, city, idx) {
  if (currentCity !== city || currentTrackIdx !== idx) return;
  if (!audio.duration) return;
  const bar = getActiveMiniPlayer()?.querySelector(".mp-progress");
  if (!bar) return;
  const rect = bar.getBoundingClientRect();
  const pct = Math.max(0, Math.min(1, (touch.clientX - rect.left) / rect.width));
  audio.currentTime = pct * audio.duration;
}

function cycleSpeed() {
  speedIdx = (speedIdx + 1) % SPEEDS.length;
  audio.playbackRate = SPEEDS[speedIdx];
  // Actualizar todos los botones de velocidad visibles
  document.querySelectorAll(".mp-speed").forEach(btn => {
    btn.textContent = SPEEDS[speedIdx] + "x";
  });
}

// ── Mini-player helpers ───────────────────────
function getActiveMiniPlayer() {
  if (currentCity === null) return null;
  return document.querySelector(`.mini-player[data-city="${currentCity}"][data-idx="${currentTrackIdx}"]`);
}

function resetActiveMiniPlayer() {
  const mp = getActiveMiniPlayer();
  if (mp) {
    mp.querySelector(".mp-play").textContent = "▶";
    mp.querySelector(".mp-fill").style.width = "0%";
    mp.querySelector(".mp-time").textContent = "0:00 / " + (CATALOG[currentCity]?.[currentTrackIdx]?.duration_fmt || "—");
  }
}

function updateActiveMiniPlayer() {
  const mp = getActiveMiniPlayer();
  if (!mp || !audio.duration) return;
  const pct = (audio.currentTime / audio.duration) * 100;
  mp.querySelector(".mp-fill").style.width = pct + "%";
  mp.querySelector(".mp-time").textContent = fmtTime(audio.currentTime) + " / " + fmtTime(audio.duration);
}

// ── Audio events ──────────────────────────────
function setupAudioEvents() {
  audio.addEventListener("timeupdate", updateActiveMiniPlayer);

  audio.addEventListener("play", () => {
    const mp = getActiveMiniPlayer();
    if (mp) mp.querySelector(".mp-play").textContent = "⏸";
  });

  audio.addEventListener("pause", () => {
    const mp = getActiveMiniPlayer();
    if (mp) mp.querySelector(".mp-play").textContent = "▶";
  });

  audio.addEventListener("ended", () => {
    const mp = getActiveMiniPlayer();
    if (mp) {
      mp.querySelector(".mp-play").textContent = "▶";
      mp.querySelector(".mp-fill").style.width = "0%";
    }
  });
}

// ── Media Session API ─────────────────────────
function setupMediaSession() {
  if (!("mediaSession" in navigator)) return;

  audio.addEventListener("play", () => {
    const track = currentCity && CATALOG[currentCity] ? CATALOG[currentCity][currentTrackIdx] : null;
    if (track) {
      navigator.mediaSession.metadata = new MediaMetadata({
        title: track.name,
        artist: currentCity,
        album: "Archivo de Viajes"
      });
    }
    navigator.mediaSession.playbackState = "playing";
  });

  audio.addEventListener("pause", () => {
    navigator.mediaSession.playbackState = "paused";
  });

  navigator.mediaSession.setActionHandler("play", () => audio.play());
  navigator.mediaSession.setActionHandler("pause", () => audio.pause());
  navigator.mediaSession.setActionHandler("seekbackward", () => seekAudio(-15));
  navigator.mediaSession.setActionHandler("seekforward", () => seekAudio(15));
}

// ── Deep link ─────────────────────────────────
function handleDeepLink() {
  const params = getQueryParams();
  if (!params.city) return;

  const cityName = params.city;
  if (!CATALOG[cityName]) return;

  // Expand city
  const cityEl = document.querySelector(`.city[data-city="${cityName}"]`);
  if (cityEl) cityEl.classList.add("open");

  if (params.track) {
    const tracks = CATALOG[cityName];
    const idx = tracks.findIndex(t => slugify(t.name) === params.track);
    if (idx >= 0) {
      togglePlace(cityName, idx);
    }
  }
}

// Boot
initPlayer();
