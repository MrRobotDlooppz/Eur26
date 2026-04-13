/* ============================================
   Player — Lógica del reproductor de audio
   + Panel de texto de guía
   ============================================ */

let CATALOG = {};

const SPEEDS = [0.75, 1, 1.25, 1.5, 1.75];
let speedIdx = 1;

const audio = new Audio();
let currentCity = null;
let currentTrackIdx = -1;
let allTracks = []; // flat list: {city, idx, name, file, text}
let guideCache = {}; // cache de textos de guía cargados

// DOM refs
const app = document.getElementById("app");
const guidePanel = document.getElementById("guide-panel");
const guideContent = document.getElementById("guide-content");
const guideTitle = document.getElementById("guide-title");
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

// Init: cargar catálogo desde JSON externo
async function initPlayer() {
  try {
    const resp = await fetch("data/catalog.json");
    CATALOG = await resp.json();
  } catch (e) {
    console.error("Error cargando catálogo:", e);
    app.innerHTML = '<div class="empty"><h2>Error cargando datos</h2><p>No se pudo cargar data/catalog.json</p></div>';
    return;
  }

  // Build flat track list
  allTracks = [];
  for (const [city, tracks] of Object.entries(CATALOG)) {
    tracks.forEach((t, i) => {
      allTracks.push({ city, idx: i, name: t.name, file: t.file, text: t.text || null });
    });
  }

  render();
  setupControls();
  setupProgressBar();
  setupMediaSession();
  handleDeepLink();
}

// Render catalog
function render() {
  if (Object.keys(CATALOG).length === 0) {
    app.innerHTML = '<div class="empty"><h2>No hay audios disponibles</h2><p>Ejecutá el pipeline para generar los MP3</p></div>';
    return;
  }

  let html = "";
  for (const [city, tracks] of Object.entries(CATALOG)) {
    html += `<div class="city" data-city="${city}">`;
    html += `<div class="city-header" onclick="toggleCity(this.parentElement)">`;
    html += `<div><h2>${city}</h2><span class="count">${tracks.length} audio${tracks.length !== 1 ? "s" : ""}</span></div>`;
    html += `<span class="chevron">›</span>`;
    html += `</div>`;
    html += `<div class="track-list">`;

    tracks.forEach((t, i) => {
      const dur = t.duration_fmt ? `<div class="track-duration">${t.duration_fmt}</div>` : "";
      const guideBtn = t.text ? `<button class="track-guide-btn" onclick="event.stopPropagation(); showGuide('${city}', ${i})" title="Ver guía">📖</button>` : "";
      html += `<div class="track" data-city="${city}" data-idx="${i}" onclick="playTrack('${city}', ${i})">`;
      html += `<div class="track-icon">▶</div>`;
      html += `<div class="track-info"><div class="track-name">${t.name}</div>${dur}</div>`;
      html += guideBtn;
      html += `</div>`;
    });

    html += `</div></div>`;
  }
  app.innerHTML = html;
}

function toggleCity(el) {
  el.classList.toggle("open");
}

// Guía de texto
async function showGuide(city, idx) {
  const track = CATALOG[city][idx];
  if (!track || !track.text) return;

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

  guideTitle.textContent = `📖 ${track.name}`;
  guideContent.innerHTML = guideCache[cacheKey];
  guidePanel.classList.add("open");
  guidePanel.scrollIntoView({ behavior: "smooth", block: "start" });
}

function closeGuide() {
  guidePanel.classList.remove("open");
}

// Playback
function playTrack(city, idx) {
  const track = CATALOG[city][idx];
  if (!track) return;

  currentCity = city;
  currentTrackIdx = idx;

  audio.src = track.file;
  audio.playbackRate = SPEEDS[speedIdx];
  audio.play();

  playerName.textContent = `${city} — ${track.name}`;
  player.classList.remove("hidden");
  btnPlay.textContent = "⏸";

  // Highlight active track
  document.querySelectorAll(".track").forEach(el => el.classList.remove("active"));
  const active = document.querySelector(`.track[data-city="${city}"][data-idx="${idx}"]`);
  if (active) {
    active.classList.add("active");
    active.closest(".city").classList.add("open");
  }
}

function getFlatIdx() {
  return allTracks.findIndex(t => t.city === currentCity && t.idx === currentTrackIdx);
}

function playFlatIdx(fi) {
  if (fi >= 0 && fi < allTracks.length) {
    playTrack(allTracks[fi].city, allTracks[fi].idx);
  }
}

// Controls
function setupControls() {
  btnPlay.addEventListener("click", () => {
    if (audio.paused) {
      if (!audio.src || audio.src === location.href) {
        if (allTracks.length > 0) playTrack(allTracks[0].city, allTracks[0].idx);
        return;
      }
      audio.play();
      btnPlay.textContent = "⏸";
    } else {
      audio.pause();
      btnPlay.textContent = "▶";
    }
  });

  btnPrev.addEventListener("click", () => {
    const fi = getFlatIdx();
    if (fi > 0) playFlatIdx(fi - 1);
  });

  btnNext.addEventListener("click", () => {
    const fi = getFlatIdx();
    playFlatIdx(fi + 1);
  });

  btnBack.addEventListener("click", () => {
    audio.currentTime = Math.max(0, audio.currentTime - 15);
  });

  btnFwd.addEventListener("click", () => {
    audio.currentTime = Math.min(audio.duration || 0, audio.currentTime + 15);
  });

  btnSpeed.addEventListener("click", () => {
    speedIdx = (speedIdx + 1) % SPEEDS.length;
    audio.playbackRate = SPEEDS[speedIdx];
    btnSpeed.textContent = SPEEDS[speedIdx] + "x";
    btnSpeed.classList.toggle("active-speed", speedIdx !== 1);
  });

  audio.addEventListener("timeupdate", () => {
    if (audio.duration) {
      const pct = (audio.currentTime / audio.duration) * 100;
      progressFill.style.width = pct + "%";
      timeCurrent.textContent = fmtTime(audio.currentTime);
      timeTotal.textContent = fmtTime(audio.duration);
    }
  });

  audio.addEventListener("ended", () => {
    btnPlay.textContent = "▶";
    const fi = getFlatIdx();
    if (fi + 1 < allTracks.length) {
      playFlatIdx(fi + 1);
    }
  });
}

// Progress bar seek
function setupProgressBar() {
  function seek(e) {
    if (!audio.duration) return;
    const rect = progressBar.getBoundingClientRect();
    const pct = Math.max(0, Math.min(1, (e.clientX - rect.left) / rect.width));
    audio.currentTime = pct * audio.duration;
  }

  progressBar.addEventListener("click", seek);

  let seeking = false;
  progressBar.addEventListener("touchstart", (e) => {
    seeking = true;
    seek(e.touches[0]);
  }, { passive: true });
  progressBar.addEventListener("touchmove", (e) => {
    if (seeking) seek(e.touches[0]);
  }, { passive: true });
  progressBar.addEventListener("touchend", () => { seeking = false; });
}

// Media Session API (lock screen controls)
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

  navigator.mediaSession.setActionHandler("play", () => { audio.play(); btnPlay.textContent = "⏸"; });
  navigator.mediaSession.setActionHandler("pause", () => { audio.pause(); btnPlay.textContent = "▶"; });
  navigator.mediaSession.setActionHandler("previoustrack", () => {
    const fi = getFlatIdx();
    if (fi > 0) playFlatIdx(fi - 1);
  });
  navigator.mediaSession.setActionHandler("nexttrack", () => {
    const fi = getFlatIdx();
    playFlatIdx(fi + 1);
  });
  navigator.mediaSession.setActionHandler("seekbackward", () => {
    audio.currentTime = Math.max(0, audio.currentTime - 15);
  });
  navigator.mediaSession.setActionHandler("seekforward", () => {
    audio.currentTime = Math.min(audio.duration || 0, audio.currentTime + 15);
  });
}

// Deep link via query params: ?city=Firenze&track=ponte_vecchio&guide=1
function handleDeepLink() {
  const params = getQueryParams();
  if (!params.city) return;

  const cityName = params.city;
  const trackSlug = params.track;

  if (!CATALOG[cityName]) return;

  // Expand city
  const cityEl = document.querySelector(`.city[data-city="${cityName}"]`);
  if (cityEl) cityEl.classList.add("open");

  if (trackSlug) {
    // Find track by slug match
    const tracks = CATALOG[cityName];
    const idx = tracks.findIndex(t => slugify(t.name) === trackSlug);
    if (idx >= 0) {
      if (params.guide === "1" && tracks[idx].text) {
        showGuide(cityName, idx);
      }
      // Don't auto-play, just highlight and show guide
      const trackEl = document.querySelector(`.track[data-city="${cityName}"][data-idx="${idx}"]`);
      if (trackEl) {
        trackEl.classList.add("active");
        trackEl.scrollIntoView({ behavior: "smooth", block: "center" });
      }
    }
  }
}

// Boot
initPlayer();
