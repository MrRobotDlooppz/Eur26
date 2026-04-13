#!/usr/bin/env python3
"""
Genera las páginas interactivas del Archivo de Viajes:
  - docs/mapa.html  — Mapa interactivo con Leaflet.js (todas las ciudades y lugares)
  - docs/timeline.html — Línea de tiempo visual por época histórica

Uso:
  python tools/generate_interactive_pages.py

Lee los JSON de tools/maps/*_places.json y los datos de ciudades para construir ambas páginas.
"""

import json
import glob
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DOCS = os.path.join(ROOT, "docs")
MAPS_DIR = os.path.join(ROOT, "tools", "maps")

# ── Datos de ciudades (coordenadas centrales, país, color) ──────────────────

CITIES = {
    "Rome": {
        "display": "Roma",
        "lat": 41.9028, "lon": 12.4964,
        "country": "Italia",
        "color": "#e94560",
        "visit": "2026-03-23 → 2026-03-30",
    },
    "Firenze": {
        "display": "Firenze",
        "lat": 43.7696, "lon": 11.2558,
        "country": "Italia",
        "color": "#f5a623",
        "visit": "",
    },
    "Lucca": {
        "display": "Lucca",
        "lat": 43.8430, "lon": 10.5050,
        "country": "Italia",
        "color": "#4ecca3",
        "visit": "",
    },
    "Pisa": {
        "display": "Pisa",
        "lat": 43.7228, "lon": 10.4017,
        "country": "Italia",
        "color": "#3dc1d3",
        "visit": "",
    },
    "Granada": {
        "display": "Granada",
        "lat": 37.1773, "lon": -3.5986,
        "country": "España",
        "color": "#e55039",
        "visit": "",
    },
    "Madrid": {
        "display": "Madrid",
        "lat": 40.4168, "lon": -3.7038,
        "country": "España",
        "color": "#f8c291",
        "visit": "",
    },
}

# ── Datos históricos por lugar (año aproximado de fundación/construcción) ────
# Negativos = a.C.  Positivos = d.C.

HISTORICAL_DATA = {
    # Roma
    "Colosseo": {"year": 72, "era": "Roma Imperial", "desc": "Anfiteatro Flavio, iniciado por Vespasiano"},
    "Foro Romano e Palatino": {"year": -600, "era": "Roma Monárquica", "desc": "Centro político de la Roma antigua"},
    "Foro di Traiano": {"year": 107, "era": "Roma Imperial", "desc": "Último y más grande de los foros imperiales"},
    "Monumento a Vittorio Emanuele II": {"year": 1885, "era": "Italia moderna", "desc": "Altar de la Patria, unificación italiana"},
    "Terme di Caracalla": {"year": 212, "era": "Roma Imperial", "desc": "Termas monumentales del emperador Caracalla"},
    "Terme di Traiano": {"year": 109, "era": "Roma Imperial", "desc": "Termas sobre la Domus Aurea de Nerón"},
    "Largo di Torre Argentina": {"year": -300, "era": "Roma Republicana", "desc": "Templos republicanos; sitio del asesinato de César (44 a.C.)"},
    "Fontana di Trevi": {"year": 1762, "era": "Roma barroca", "desc": "La fuente más famosa del mundo, sobre el Aqua Virgo (19 a.C.)"},
    "Pantheon": {"year": 125, "era": "Roma Imperial", "desc": "Templo de todos los dioses, reconstruido por Adriano"},
    "Piazza di Spagna": {"year": 1725, "era": "Roma barroca", "desc": "Escalinata de Trinità dei Monti"},
    "Piazza del Popolo": {"year": 1589, "era": "Roma renacentista", "desc": "Puerta norte de Roma, obelisco de Ramsés II"},
    "Musei Vaticani": {"year": 1506, "era": "Renacimiento", "desc": "Colección papal desde Julio II; Capilla Sistina (1473)"},
    "Basilica di Santa Maria Maggiore": {"year": 435, "era": "Roma paleocristiana", "desc": "Una de las cuatro basílicas mayores, mosaicos del s. V"},
    "Villa Borghese": {"year": 1620, "era": "Roma barroca", "desc": "Villa y jardines del cardenal Scipione Borghese"},
    "Archibasilica di San Giovanni in Laterano": {"year": 324, "era": "Roma paleocristiana", "desc": "Primera basílica cristiana, catedral de Roma"},
    "Piazza Navona": {"year": 86, "era": "Roma Imperial", "desc": "Sobre el Stadio di Domiziano; fuentes de Bernini (1651)"},
    "Quartiere Coppedè": {"year": 1919, "era": "Italia moderna", "desc": "Barrio art nouveau de Gino Coppedè"},

    # Firenze
    "Duomo di Firenze": {"year": 1296, "era": "Gótico / Renacimiento", "desc": "Catedral con la cúpula de Brunelleschi (1436)"},
    "Battistero di San Giovanni": {"year": 1059, "era": "Románico", "desc": "Baptisterio octogonal, Puertas del Paraíso de Ghiberti"},
    "Palazzo Vecchio": {"year": 1299, "era": "Gótico", "desc": "Sede del gobierno florentino, Arnolfo di Cambio"},
    "Galleria degli Uffizi": {"year": 1560, "era": "Renacimiento", "desc": "Oficinas de Cosimo I, hoy el museo más importante de Italia"},
    "Ponte Vecchio": {"year": 1345, "era": "Medieval", "desc": "El puente más antiguo de Firenze, joyerías desde 1593"},
    "Palazzo Pitti e Giardino di Boboli": {"year": 1458, "era": "Renacimiento", "desc": "Palacio de los Medici, jardines manieristas"},
    "Basilica di Santa Croce": {"year": 1294, "era": "Gótico", "desc": "Panteón de glorias italianas: Galileo, Miguel Ángel, Maquiavelo"},
    "Basilica di Santa Maria Novella": {"year": 1246, "era": "Gótico", "desc": "Iglesia dominica, fachada de Leon Battista Alberti"},
    "Galleria dell'Accademia": {"year": 1784, "era": "Ilustración", "desc": "Hogar del David de Miguel Ángel desde 1873"},
    "Basilica e Museo di San Marco": {"year": 1436, "era": "Renacimiento", "desc": "Frescos de Fra Angelico, convento de Savonarola"},
    "Museo Nazionale del Bargello": {"year": 1255, "era": "Medieval", "desc": "Palazzo del Podestà, primer museo nacional de Italia (1865)"},
    "Fiesole": {"year": -700, "era": "Etrusco", "desc": "Asentamiento etrusco anterior a Florencia"},
    "San Lorenzo e Cappelle Medicee": {"year": 393, "era": "Roma paleocristiana", "desc": "Iglesia más antigua de Firenze; Sacristía Nueva de Miguel Ángel"},
    "Museo Galileo": {"year": 1930, "era": "Italia moderna", "desc": "Instrumentos científicos desde la Accademia del Cimento (1657)"},
    "Piazzale Michelangelo": {"year": 1869, "era": "Italia moderna", "desc": "Mirador panorámico de Giuseppe Poggi"},
    "Loggia dei Lanzi": {"year": 1382, "era": "Gótico", "desc": "Galería de esculturas al aire libre en Piazza della Signoria"},
    "Mercato Centrale di San Lorenzo": {"year": 1874, "era": "Italia moderna", "desc": "Mercado de hierro y vidrio de Giuseppe Mengoni"},
    "Sinagoga e Museo Ebraico": {"year": 1882, "era": "Italia moderna", "desc": "Sinagoga morisca, testimonio del ghetto florentino (1571)"},
    "Abbazia di San Miniato al Monte": {"year": 1013, "era": "Románico", "desc": "Joya del románico florentino sobre la colina"},

    # Lucca
    "Mura di Lucca": {"year": 1544, "era": "Renacimiento", "desc": "Murallas renacentistas intactas, hoy paseo arbolado"},
    "Cattedrale di San Martino": {"year": 1060, "era": "Románico", "desc": "Catedral con el Volto Santo, crucifijo legendario"},
    "Basilica di San Frediano": {"year": 550, "era": "Alta Edad Media", "desc": "Fundada por el obispo irlandés San Frediano"},
    "San Michele in Foro": {"year": 1070, "era": "Románico", "desc": "Iglesia sobre el antiguo foro romano"},
    "Piazza dell'Anfiteatro": {"year": 180, "era": "Roma Imperial", "desc": "Plaza elíptica sobre el anfiteatro romano del s. II"},
    "Torre Guinigi": {"year": 1390, "era": "Medieval", "desc": "Torre con encinas en la cima, familia Guinigi"},

    # Pisa
    "Campo dei Miracoli": {"year": 1064, "era": "Románico", "desc": "Conjunto monumental tras la victoria sobre Palermo"},
    "Duomo di Pisa": {"year": 1064, "era": "Románico", "desc": "Catedral de Buscheto, estilo románico pisano"},
    "Torre Pendente di Pisa": {"year": 1173, "era": "Románico", "desc": "La torre inclinada, 199 años de construcción"},
    "Battistero di San Giovanni (Pisa)": {"year": 1152, "era": "Románico / Gótico", "desc": "El baptisterio más grande de Italia"},
    "Camposanto Monumentale": {"year": 1278, "era": "Gótico", "desc": "Cementerio monumental con tierra santa de Jerusalén"},
    "Piazza dei Cavalieri": {"year": 1562, "era": "Renacimiento", "desc": "Rediseño de Vasari; Torre della Fame del Conde Ugolino"},

    # Granada
    "Alhambra": {"year": 1238, "era": "Nazarí", "desc": "Palacio-fortaleza de Muhammad I, joya del arte islámico"},
    "Albaicín": {"year": 1013, "era": "Zirí / Nazarí", "desc": "Barrio medieval árabe, Patrimonio UNESCO"},
    "Catedral de Granada y Capilla Real": {"year": 1523, "era": "Renacimiento", "desc": "Primera iglesia renacentista de España; tumba de los Reyes Católicos"},
    "Mirador de San Nicolás": {"year": 1525, "era": "Renacimiento", "desc": "La mejor vista de la Alhambra con Sierra Nevada"},
    "Sacromonte": {"year": 1500, "era": "Edad Moderna", "desc": "Barrio gitano de cuevas, zambras flamencas"},
    "Monasterio de San Jerónimo": {"year": 1504, "era": "Renacimiento", "desc": "Primer monasterio fundado tras la Reconquista"},

    # Madrid
    "Palacio Real de Madrid": {"year": 1738, "era": "Borbón", "desc": "Sobre el antiguo Alcázar, el mayor palacio real de Europa occidental"},
    "Museo Nacional del Prado": {"year": 1819, "era": "Ilustración", "desc": "Una de las mejores pinacotecas del mundo; edificio de Villanueva (1785)"},
    "Catedral de la Almudena": {"year": 1883, "era": "España moderna", "desc": "Catedral de Madrid, consagrada en 1993"},
    "Templo de Debod": {"year": -200, "era": "Egipto ptolemaico", "desc": "Templo del s. II a.C. donado por Egipto a España (1968)"},
    "Plaza Mayor de Madrid": {"year": 1619, "era": "Siglo de Oro", "desc": "Plaza mayor de Juan Gómez de Mora"},
    "Puerta del Sol": {"year": 1857, "era": "España moderna", "desc": "Km 0 de España; escenario del levantamiento del 2 de mayo (1808)"},
    "Museo Reina Sofía": {"year": 1992, "era": "España contemporánea", "desc": "Arte contemporáneo; hogar del Guernica de Picasso"},
    "Parque del Retiro": {"year": 1630, "era": "Siglo de Oro", "desc": "Jardines del Palacio del Buen Retiro de Felipe IV"},
    "Gran Vía": {"year": 1910, "era": "España moderna", "desc": "La gran avenida de Madrid, construida en tres fases"},
    "Mercado de San Miguel": {"year": 1916, "era": "España moderna", "desc": "Mercado de hierro de Alfonso Palacios"},
}


def load_places_from_jsons():
    """Lee todos los JSON de mapas y devuelve un dict city -> lista de places con coords."""
    city_places = {}
    json_files = glob.glob(os.path.join(MAPS_DIR, "*_places*.json"))
    for jf in json_files:
        basename = os.path.basename(jf)
        # Inferir ciudad del nombre del archivo
        city_key = None
        for ck in CITIES:
            if ck.lower() in basename.lower():
                city_key = ck
                break
        if not city_key:
            continue

        with open(jf, "r", encoding="utf-8") as f:
            places = json.load(f)

        city_places[city_key] = []
        seen = set()
        for p in places:
            name = p["nombre"]
            if name in seen:
                continue
            seen.add(name)
            city_places[city_key].append({
                "name": name,
                "lat": p["lat"],
                "lon": p["lon"],
            })
    return city_places


def build_map_data(city_places):
    """Construye el JSON embebido para Leaflet."""
    data = []
    for city_key, info in CITIES.items():
        places = city_places.get(city_key, [])
        data.append({
            "city": info["display"],
            "country": info["country"],
            "lat": info["lat"],
            "lon": info["lon"],
            "color": info["color"],
            "visit": info["visit"],
            "places": places,
        })
    return data


def build_timeline_data():
    """Construye la lista de eventos para el timeline, ordenados cronológicamente."""
    events = []
    # Mapear lugares a ciudades
    place_to_city = {}
    for city_key, info in CITIES.items():
        for place_name, hist in HISTORICAL_DATA.items():
            # Buscar en qué ciudad está (heurística por sección en el código)
            pass
    # Asignar ciudades por bloques del diccionario (ya están ordenados por ciudad en HISTORICAL_DATA)
    city_ranges = {
        "Rome": ["Colosseo", "Foro Romano e Palatino", "Foro di Traiano",
                  "Monumento a Vittorio Emanuele II", "Terme di Caracalla",
                  "Terme di Traiano", "Largo di Torre Argentina", "Fontana di Trevi",
                  "Pantheon", "Piazza di Spagna", "Piazza del Popolo", "Musei Vaticani",
                  "Basilica di Santa Maria Maggiore", "Villa Borghese",
                  "Archibasilica di San Giovanni in Laterano", "Piazza Navona",
                  "Quartiere Coppedè"],
        "Firenze": ["Duomo di Firenze", "Battistero di San Giovanni", "Palazzo Vecchio",
                     "Galleria degli Uffizi", "Ponte Vecchio",
                     "Palazzo Pitti e Giardino di Boboli", "Basilica di Santa Croce",
                     "Basilica di Santa Maria Novella", "Galleria dell'Accademia",
                     "Basilica e Museo di San Marco", "Museo Nazionale del Bargello",
                     "Fiesole", "San Lorenzo e Cappelle Medicee", "Museo Galileo",
                     "Piazzale Michelangelo", "Loggia dei Lanzi",
                     "Mercato Centrale di San Lorenzo", "Sinagoga e Museo Ebraico",
                     "Abbazia di San Miniato al Monte"],
        "Lucca": ["Mura di Lucca", "Cattedrale di San Martino", "Basilica di San Frediano",
                   "San Michele in Foro", "Piazza dell'Anfiteatro", "Torre Guinigi"],
        "Pisa": ["Campo dei Miracoli", "Duomo di Pisa", "Torre Pendente di Pisa",
                  "Battistero di San Giovanni (Pisa)", "Camposanto Monumentale",
                  "Piazza dei Cavalieri"],
        "Granada": ["Alhambra", "Albaicín", "Catedral de Granada y Capilla Real",
                     "Mirador de San Nicolás", "Sacromonte", "Monasterio de San Jerónimo"],
        "Madrid": ["Palacio Real de Madrid", "Museo Nacional del Prado",
                    "Catedral de la Almudena", "Templo de Debod",
                    "Plaza Mayor de Madrid", "Puerta del Sol",
                    "Museo Reina Sofía", "Parque del Retiro", "Gran Vía",
                    "Mercado de San Miguel"],
    }

    for city_key, place_names in city_ranges.items():
        for pn in place_names:
            if pn in HISTORICAL_DATA:
                h = HISTORICAL_DATA[pn]
                events.append({
                    "name": pn,
                    "city": CITIES[city_key]["display"],
                    "color": CITIES[city_key]["color"],
                    "year": h["year"],
                    "era": h["era"],
                    "desc": h["desc"],
                })
    events.sort(key=lambda e: e["year"])
    return events


def format_year(y):
    if y < 0:
        return f"{abs(y)} a.C."
    return f"{y} d.C."


# ═══════════════════════════════════════════════════════════════════════════════
#  MAPA INTERACTIVO
# ═══════════════════════════════════════════════════════════════════════════════

MAP_HTML_TEMPLATE = r"""<!DOCTYPE html>
<html lang="es">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Archivo de Viajes — Mapa</title>
<link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css" />
<style>
* { margin: 0; padding: 0; box-sizing: border-box; }
:root {
  --bg: #1a1a2e;
  --bg-card: #16213e;
  --accent: #e94560;
  --text: #eaeaea;
  --text-muted: #8b8fa3;
  --border: #2a2d45;
}
body {
  font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
  background: var(--bg);
  color: var(--text);
  min-height: 100vh;
}
nav {
  background: linear-gradient(135deg, #0f3460 0%, var(--bg-card) 100%);
  padding: 14px 20px;
  display: flex;
  align-items: center;
  gap: 16px;
  border-bottom: 1px solid var(--border);
  flex-wrap: wrap;
}
nav h1 { font-size: 1.15rem; font-weight: 600; white-space: nowrap; }
nav .links { display: flex; gap: 12px; margin-left: auto; }
nav a {
  color: var(--text-muted);
  text-decoration: none;
  font-size: 0.85rem;
  padding: 4px 10px;
  border-radius: 6px;
  transition: background 0.2s, color 0.2s;
}
nav a:hover, nav a.active { background: var(--accent); color: #fff; }
#map { height: calc(100vh - 52px); width: 100%; }
.city-legend {
  position: absolute;
  bottom: 20px;
  left: 10px;
  z-index: 1000;
  background: rgba(26,26,46,0.92);
  border-radius: 10px;
  padding: 12px 16px;
  border: 1px solid var(--border);
  max-width: 200px;
}
.city-legend h3 { font-size: 0.8rem; color: var(--text-muted); margin-bottom: 8px; text-transform: uppercase; letter-spacing: 0.5px; }
.legend-item { display: flex; align-items: center; gap: 8px; margin-bottom: 4px; cursor: pointer; padding: 2px 4px; border-radius: 4px; }
.legend-item:hover { background: rgba(255,255,255,0.05); }
.legend-dot { width: 12px; height: 12px; border-radius: 50%; flex-shrink: 0; }
.legend-label { font-size: 0.82rem; }
.legend-count { font-size: 0.72rem; color: var(--text-muted); margin-left: auto; }
.leaflet-popup-content-wrapper {
  background: var(--bg-card) !important;
  color: var(--text) !important;
  border-radius: 10px !important;
  border: 1px solid var(--border) !important;
}
.leaflet-popup-tip { background: var(--bg-card) !important; }
.leaflet-popup-content { font-family: inherit !important; font-size: 0.88rem !important; line-height: 1.5 !important; }
.leaflet-popup-content h3 { color: var(--accent); margin-bottom: 4px; font-size: 1rem; }
.leaflet-popup-content .city-tag { color: var(--text-muted); font-size: 0.78rem; }
.leaflet-control-zoom a { background: var(--bg-card) !important; color: var(--text) !important; border-color: var(--border) !important; }
</style>
</head>
<body>
<nav>
  <h1>🗺️ Mapa de Viajes</h1>
  <div class="links">
    <a href="index.html">🎧 Audio</a>
    <a href="mapa.html" class="active">🗺️ Mapa</a>
    <a href="timeline.html">⏳ Timeline</a>
  </div>
</nav>
<div id="map"></div>
<div class="city-legend" id="legend"></div>
<script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js"></script>
<script>
const DATA = %%MAP_DATA%%;

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
  const cityMarker = L.marker([city.lat, city.lon], { icon: makeIcon(city.color, 20) })
    .bindPopup(`<h3>${city.city}</h3><span class="city-tag">${city.country}</span>${city.visit ? "<br><small>" + city.visit + "</small>" : ""}<br><small>${city.places.length} lugares documentados</small>`);
  group.addLayer(cityMarker);
  allMarkers.push(cityMarker);

  // Place markers
  city.places.forEach(p => {
    const m = L.marker([p.lat, p.lon], { icon: makeIcon(city.color, 12) })
      .bindPopup(`<h3>${p.name}</h3><span class="city-tag">${city.city}, ${city.country}</span>`);
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
</script>
</body>
</html>"""


# ═══════════════════════════════════════════════════════════════════════════════
#  LÍNEA DE TIEMPO
# ═══════════════════════════════════════════════════════════════════════════════

TIMELINE_HTML_TEMPLATE = r"""<!DOCTYPE html>
<html lang="es">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Archivo de Viajes — Línea de Tiempo</title>
<style>
* { margin: 0; padding: 0; box-sizing: border-box; }
:root {
  --bg: #1a1a2e;
  --bg-card: #16213e;
  --bg-player: #0f3460;
  --accent: #e94560;
  --text: #eaeaea;
  --text-muted: #8b8fa3;
  --border: #2a2d45;
}
body {
  font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
  background: var(--bg);
  color: var(--text);
  min-height: 100vh;
}
nav {
  background: linear-gradient(135deg, #0f3460 0%, var(--bg-card) 100%);
  padding: 14px 20px;
  display: flex;
  align-items: center;
  gap: 16px;
  border-bottom: 1px solid var(--border);
  position: sticky;
  top: 0;
  z-index: 10;
  flex-wrap: wrap;
}
nav h1 { font-size: 1.15rem; font-weight: 600; white-space: nowrap; }
nav .links { display: flex; gap: 12px; margin-left: auto; }
nav a {
  color: var(--text-muted);
  text-decoration: none;
  font-size: 0.85rem;
  padding: 4px 10px;
  border-radius: 6px;
  transition: background 0.2s, color 0.2s;
}
nav a:hover, nav a.active { background: var(--accent); color: #fff; }

.filters {
  display: flex;
  gap: 8px;
  flex-wrap: wrap;
  padding: 16px 20px 8px;
  max-width: 900px;
  margin: 0 auto;
}
.filter-btn {
  background: var(--bg-card);
  color: var(--text-muted);
  border: 1px solid var(--border);
  padding: 6px 14px;
  border-radius: 20px;
  cursor: pointer;
  font-size: 0.8rem;
  transition: all 0.2s;
}
.filter-btn:hover { border-color: var(--accent); color: var(--text); }
.filter-btn.active { background: var(--accent); color: #fff; border-color: var(--accent); }

.timeline-container {
  max-width: 900px;
  margin: 0 auto;
  padding: 20px 20px 60px;
  position: relative;
}
.timeline-container::before {
  content: "";
  position: absolute;
  left: 28px;
  top: 0;
  bottom: 0;
  width: 2px;
  background: var(--border);
}
@media (min-width: 700px) {
  .timeline-container::before { left: 50%; transform: translateX(-1px); }
}

.era-label {
  position: relative;
  padding: 12px 0 8px 60px;
  font-size: 0.75rem;
  color: var(--text-muted);
  text-transform: uppercase;
  letter-spacing: 1px;
  font-weight: 700;
}
.era-label::before {
  content: "";
  position: absolute;
  left: 22px;
  top: 50%;
  width: 14px;
  height: 14px;
  background: var(--bg);
  border: 2px solid var(--text-muted);
  border-radius: 50%;
  transform: translateY(-50%);
}
@media (min-width: 700px) {
  .era-label { text-align: center; padding-left: 0; }
  .era-label::before { left: 50%; transform: translate(-50%, -50%); }
}

.event {
  position: relative;
  padding: 0 0 24px 60px;
  transition: opacity 0.3s;
}
.event.hidden { display: none; }

.event::before {
  content: "";
  position: absolute;
  left: 23px;
  top: 8px;
  width: 12px;
  height: 12px;
  border-radius: 50%;
  border: 2px solid #fff;
}

@media (min-width: 700px) {
  .event { width: 50%; padding: 0 30px 24px 0; }
  .event::before { right: -6px; left: auto; }
  .event:nth-child(even) { margin-left: 50%; padding: 0 0 24px 30px; }
  .event:nth-child(even)::before { left: -6px; right: auto; }
}

.event-card {
  background: var(--bg-card);
  border-radius: 10px;
  padding: 14px 16px;
  border: 1px solid var(--border);
  transition: border-color 0.2s, transform 0.2s;
}
.event-card:hover { border-color: var(--accent); transform: translateY(-1px); }

.event-year {
  font-size: 0.78rem;
  font-weight: 700;
  margin-bottom: 4px;
}
.event-name {
  font-size: 1rem;
  font-weight: 600;
  margin-bottom: 4px;
  color: var(--text);
}
.event-desc {
  font-size: 0.85rem;
  color: var(--text-muted);
  line-height: 1.45;
}
.event-city {
  font-size: 0.72rem;
  margin-top: 6px;
  display: inline-block;
  padding: 2px 8px;
  border-radius: 10px;
  background: rgba(255,255,255,0.06);
}

.stats {
  text-align: center;
  padding: 20px;
  color: var(--text-muted);
  font-size: 0.85rem;
}
.stats strong { color: var(--accent); }
</style>
</head>
<body>
<nav>
  <h1>⏳ Línea de Tiempo</h1>
  <div class="links">
    <a href="index.html">🎧 Audio</a>
    <a href="mapa.html">🗺️ Mapa</a>
    <a href="timeline.html" class="active">⏳ Timeline</a>
  </div>
</nav>

<div class="stats">
  <strong>%%EVENT_COUNT%%</strong> lugares · <strong>%%YEAR_SPAN%%</strong> de historia · <strong>%%CITY_COUNT%%</strong> ciudades
</div>

<div class="filters" id="filters"></div>

<div class="timeline-container" id="timeline"></div>

<script>
const EVENTS = %%TIMELINE_DATA%%;
const CITIES = %%CITY_COLORS%%;

let activeFilter = null;

function formatYear(y) {
  return y < 0 ? Math.abs(y) + " a.C." : y + " d.C.";
}

function render(filter) {
  const container = document.getElementById("timeline");
  const events = filter ? EVENTS.filter(e => e.city === filter) : EVENTS;
  let html = "";
  let lastEra = "";
  events.forEach(ev => {
    if (ev.era !== lastEra) {
      html += `<div class="era-label">${ev.era}</div>`;
      lastEra = ev.era;
    }
    html += `<div class="event" data-city="${ev.city}">
      <div class="event-card">
        <div class="event-year" style="color:${ev.color}">${formatYear(ev.year)}</div>
        <div class="event-name">${ev.name}</div>
        <div class="event-desc">${ev.desc}</div>
        <div class="event-city" style="color:${ev.color}">${ev.city}</div>
      </div>
    </div>`;
    // Set dot color via style injection
  });
  container.innerHTML = html;

  // Color the dots
  container.querySelectorAll(".event").forEach(el => {
    const city = el.dataset.city;
    const color = CITIES[city] || "#e94560";
    el.style.setProperty("--dot-color", color);
    el.querySelector(".event")?.style;
    // Use ::before color
    el.style.cssText += `; --dot: ${color}`;
  });

  // Apply dot colors via CSS
  document.querySelectorAll(".event").forEach(el => {
    const city = el.dataset.city;
    const color = CITIES[city] || "#e94560";
    el.querySelector(":scope")?.style.setProperty("color", "inherit");
    // Direct style on pseudo - use outline trick
    const before = el;
    before.style.setProperty("--c", color);
  });
}

// Inject dynamic dot color CSS
const styleEl = document.createElement("style");
styleEl.textContent = Object.entries(CITIES).map(([city, color]) =>
  `.event[data-city="${city}"]::before { background: ${color}; }`
).join("\n");
document.head.appendChild(styleEl);

// Filters
const filtersDiv = document.getElementById("filters");
const allBtn = document.createElement("button");
allBtn.className = "filter-btn active";
allBtn.textContent = "Todas";
allBtn.addEventListener("click", () => {
  activeFilter = null;
  render(null);
  filtersDiv.querySelectorAll(".filter-btn").forEach(b => b.classList.remove("active"));
  allBtn.classList.add("active");
});
filtersDiv.appendChild(allBtn);

Object.entries(CITIES).forEach(([city, color]) => {
  const btn = document.createElement("button");
  btn.className = "filter-btn";
  btn.innerHTML = `<span style="color:${color}">●</span> ${city}`;
  btn.addEventListener("click", () => {
    activeFilter = city;
    render(city);
    filtersDiv.querySelectorAll(".filter-btn").forEach(b => b.classList.remove("active"));
    btn.classList.add("active");
  });
  filtersDiv.appendChild(btn);
});

render(null);
</script>
</body>
</html>"""


def generate_map_html(city_places):
    map_data = build_map_data(city_places)
    html = MAP_HTML_TEMPLATE.replace("%%MAP_DATA%%", json.dumps(map_data, ensure_ascii=False, indent=2))
    out = os.path.join(DOCS, "mapa.html")
    with open(out, "w", encoding="utf-8") as f:
        f.write(html)
    print(f"  ✓ {out}")


def generate_timeline_html():
    events = build_timeline_data()
    city_colors = {info["display"]: info["color"] for info in CITIES.values()}

    years = [e["year"] for e in events]
    min_y, max_y = min(years), max(years)
    year_span = f"{format_year(min_y)} — {format_year(max_y)}"

    html = TIMELINE_HTML_TEMPLATE
    html = html.replace("%%TIMELINE_DATA%%", json.dumps(events, ensure_ascii=False, indent=2))
    html = html.replace("%%CITY_COLORS%%", json.dumps(city_colors, ensure_ascii=False))
    html = html.replace("%%EVENT_COUNT%%", str(len(events)))
    html = html.replace("%%YEAR_SPAN%%", year_span)
    html = html.replace("%%CITY_COUNT%%", str(len(CITIES)))

    out = os.path.join(DOCS, "timeline.html")
    with open(out, "w", encoding="utf-8") as f:
        f.write(html)
    print(f"  ✓ {out}")


def main():
    os.makedirs(DOCS, exist_ok=True)
    print("Generando páginas interactivas...")
    city_places = load_places_from_jsons()
    generate_map_html(city_places)
    generate_timeline_html()
    print("¡Listo!")


if __name__ == "__main__":
    main()
