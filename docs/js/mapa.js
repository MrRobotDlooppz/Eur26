/* ============================================
   Mapa — Lógica del mapa interactivo Leaflet
   + Links a guías
   ============================================ */

async function initMapa() {
  let DATA;
  try {
    const resp = await fetch("data/places.json");
    DATA = await resp.json();
  } catch (e) {
    console.error("Error cargando places.json:", e);
    document.getElementById("map").innerHTML = "<p style='padding:40px;text-align:center;color:#8b8fa3'>Error cargando datos del mapa</p>";
    return;
  }

  const map = L.map("map", {
    center: [42.5, 5.0],
    zoom: 5,
    zoomControl: true,
  });

  L.tileLayer("https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png", {
    attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OSM</a> &copy; <a href="https://carto.com/">CARTO</a>',
    maxZoom: 19,
  }).addTo(map);

  const cityGroups = {};
  const allMarkers = [];

  function makeIcon(color, size) {
    return L.divIcon({
      className: "",
      html: `<div style="width:${size}px;height:${size}px;background:${color};border-radius:50%;border:2px solid #fff;box-shadow:0 2px 6px rgba(0,0,0,0.5);"></div>`,
      iconSize: [size, size],
      iconAnchor: [size/2, size/2],
      popupAnchor: [0, -size/2],
    });
  }

  DATA.forEach(city => {
    const group = L.layerGroup();

    // City marker (larger)
    const cityPopup = `<h3>${city.city}</h3><span class="city-tag">${city.country}</span>${city.visit ? "<br><small>" + city.visit + "</small>" : ""}<br><small>${city.places.length} lugares documentados</small>`;
    const cityMarker = L.marker([city.lat, city.lon], { icon: makeIcon(city.color, 20) })
      .bindPopup(cityPopup);
    group.addLayer(cityMarker);
    allMarkers.push(cityMarker);

    // Place markers
    city.places.forEach(p => {
      let popup = `<h3>${p.name}</h3><span class="city-tag">${city.city}, ${city.country}</span>`;
      if (p.guide) {
        const guideSlug = p.guide_slug || slugify(p.name);
        popup += `<br><a class="guide-link" href="index.html?city=${encodeURIComponent(city.folder || city.city)}&track=${encodeURIComponent(guideSlug)}&guide=1">📖 Ver guía</a>`;
      }
      const m = L.marker([p.lat, p.lon], { icon: makeIcon(city.color, 12) })
        .bindPopup(popup);
      group.addLayer(m);
      allMarkers.push(m);
    });

    group.addTo(map);
    cityGroups[city.city] = { group, color: city.color, count: city.places.length, lat: city.lat, lon: city.lon };
  });

  // Legend
  const legend = document.getElementById("legend");
  legend.innerHTML = "<h3>Ciudades</h3>" + DATA.map(c =>
    `<div class="legend-item" data-city="${c.city}">
      <div class="legend-dot" style="background:${c.color}"></div>
      <span class="legend-label">${c.city}</span>
      <span class="legend-count">${c.places.length}</span>
    </div>`
  ).join("");

  legend.querySelectorAll(".legend-item").forEach(el => {
    el.addEventListener("click", () => {
      const city = el.dataset.city;
      const info = cityGroups[city];
      map.flyTo([info.lat, info.lon], 13, { duration: 1 });
    });
  });

  // Fit bounds to all markers
  if (allMarkers.length) {
    const bounds = L.latLngBounds(allMarkers.map(m => m.getLatLng()));
    map.fitBounds(bounds, { padding: [40, 40] });
  }
}

initMapa();
