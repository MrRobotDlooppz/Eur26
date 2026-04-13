#!/usr/bin/env python3
"""
Genera las páginas interactivas del Archivo de Viajes:
  - docs/data/places.json  — Datos de ciudades y lugares para el mapa
  - docs/data/events.json  — Datos de eventos para la línea de tiempo
  - docs/mapa.html         — HTML ligero que importa CSS/JS
  - docs/timeline.html     — HTML ligero que importa CSS/JS

Uso:
  python tools/generate_interactive_pages.py

Lee los JSON de tools/maps/*_places.json y los datos de ciudades para construir ambas páginas.
"""

import json
import glob
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DOCS = os.path.join(ROOT, "docs")
MAPS_DIR = os.path.join(ROOT, "tools", "maps")

# ── Datos de ciudades (coordenadas centrales, país, color) ──────────────────

CITIES = {
    "Rome": {
        "display": "Roma",
        "folder": "Rome",
        "lat": 41.9028, "lon": 12.4964,
        "country": "Italia",
        "color": "#e94560",
        "visit": "2026-03-23 → 2026-03-30",
    },
    "Firenze": {
        "display": "Firenze",
        "folder": "Firenze",
        "lat": 43.7696, "lon": 11.2558,
        "country": "Italia",
        "color": "#f5a623",
        "visit": "",
    },
    "Lucca": {
        "display": "Lucca",
        "folder": "Lucca",
        "lat": 43.8430, "lon": 10.5050,
        "country": "Italia",
        "color": "#4ecca3",
        "visit": "",
    },
    "Pisa": {
        "display": "Pisa",
        "folder": "Pisa",
        "lat": 43.7228, "lon": 10.4017,
        "country": "Italia",
        "color": "#3dc1d3",
        "visit": "",
    },
    "Granada": {
        "display": "Granada",
        "folder": "Granada",
        "lat": 37.1773, "lon": -3.5986,
        "country": "España",
        "color": "#e55039",
        "visit": "",
    },
    "Madrid": {
        "display": "Madrid",
        "folder": "Madrid",
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

# Asignación de lugares a ciudades
CITY_PLACES = {
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


def slugify(name):
    """Genera un slug: 'Torre Guinigi' → 'torre_guinigi'"""
    import unicodedata
    s = unicodedata.normalize("NFD", name.lower())
    s = "".join(c for c in s if unicodedata.category(c) != "Mn")
    s = "".join(c if c.isalnum() else "_" for c in s)
    s = "_".join(p for p in s.split("_") if p)
    return s


def _has_guide(city_folder, slug):
    """Comprueba si existe un archivo de texto guía o audio para este slug."""
    text_path = os.path.join(DOCS, "text", city_folder, f"{slug}.html")
    audio_path = os.path.join(DOCS, "audio", city_folder, f"{slug}.mp3")
    return os.path.exists(text_path) or os.path.exists(audio_path)


def load_places_from_jsons():
    """Lee todos los JSON de mapas y devuelve un dict city -> lista de places con coords."""
    city_places = {}
    json_files = glob.glob(os.path.join(MAPS_DIR, "*_places*.json"))
    for jf in json_files:
        basename = os.path.basename(jf)
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
            slug = slugify(name)
            folder = CITIES[city_key]["folder"]
            place_entry = {
                "name": name,
                "lat": p["lat"],
                "lon": p["lon"],
            }
            if _has_guide(folder, slug):
                place_entry["guide"] = True
                place_entry["guide_slug"] = slug
            city_places[city_key].append(place_entry)
    return city_places


def build_places_json(city_places):
    """Construye el JSON para el mapa (data/places.json)."""
    data = []
    for city_key, info in CITIES.items():
        places = city_places.get(city_key, [])
        data.append({
            "city": info["display"],
            "folder": info["folder"],
            "country": info["country"],
            "lat": info["lat"],
            "lon": info["lon"],
            "color": info["color"],
            "visit": info["visit"],
            "places": places,
        })
    return data


def build_events_json():
    """Construye el JSON para el timeline (data/events.json)."""
    events = []
    for city_key, place_names in CITY_PLACES.items():
        folder = CITIES[city_key]["folder"]
        for pn in place_names:
            if pn not in HISTORICAL_DATA:
                continue
            h = HISTORICAL_DATA[pn]
            slug = slugify(pn)
            ev = {
                "name": pn,
                "city": CITIES[city_key]["display"],
                "folder": folder,
                "color": CITIES[city_key]["color"],
                "year": h["year"],
                "era": h["era"],
                "desc": h["desc"],
            }
            if _has_guide(folder, slug):
                ev["guide"] = True
                ev["guide_slug"] = slug
            events.append(ev)
    events.sort(key=lambda e: e["year"])

    city_colors = {info["display"]: info["color"] for info in CITIES.values()}
    return {"events": events, "city_colors": city_colors}


def format_year(y):
    if y < 0:
        return f"{abs(y)} a.C."
    return f"{y} d.C."


# ═══════════════════════════════════════════════════════════════════════════════
#  HTML TEMPLATES — lightweight shells that import external CSS/JS
# ═══════════════════════════════════════════════════════════════════════════════

def generate_mapa_html():
    return """<!DOCTYPE html>
<html lang="es">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Archivo de Viajes — Mapa</title>
<link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css" />
<link rel="stylesheet" href="css/theme.css">
<link rel="stylesheet" href="css/mapa.css">
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
<script src="js/shared.js"></script>
<script src="js/mapa.js"></script>
</body>
</html>"""


def generate_timeline_html():
    return """<!DOCTYPE html>
<html lang="es">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Archivo de Viajes — Línea de Tiempo</title>
<link rel="stylesheet" href="css/theme.css">
<link rel="stylesheet" href="css/timeline.css">
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

<div class="stats" id="stats"></div>

<div class="filters" id="filters"></div>

<div class="timeline-container" id="timeline"></div>

<script src="js/shared.js"></script>
<script src="js/timeline.js"></script>
</body>
</html>"""


def main():
    os.makedirs(DOCS, exist_ok=True)
    data_dir = os.path.join(DOCS, "data")
    os.makedirs(data_dir, exist_ok=True)

    print("Generando páginas interactivas...")

    # 1. Places JSON
    city_places = load_places_from_jsons()
    places_data = build_places_json(city_places)
    places_path = os.path.join(data_dir, "places.json")
    with open(places_path, "w", encoding="utf-8") as f:
        json.dump(places_data, f, ensure_ascii=False, indent=2)
    total_places = sum(len(c.get("places", [])) for c in places_data)
    print(f"  ✓ {places_path} ({len(places_data)} ciudades, {total_places} lugares)")

    # 2. Events JSON
    events_data = build_events_json()
    events_path = os.path.join(data_dir, "events.json")
    with open(events_path, "w", encoding="utf-8") as f:
        json.dump(events_data, f, ensure_ascii=False, indent=2)
    print(f"  ✓ {events_path} ({len(events_data['events'])} eventos)")

    # 3. Mapa HTML
    mapa_path = os.path.join(DOCS, "mapa.html")
    with open(mapa_path, "w", encoding="utf-8") as f:
        f.write(generate_mapa_html())
    print(f"  ✓ {mapa_path}")

    # 4. Timeline HTML
    timeline_path = os.path.join(DOCS, "timeline.html")
    with open(timeline_path, "w", encoding="utf-8") as f:
        f.write(generate_timeline_html())
    print(f"  ✓ {timeline_path}")

    print("¡Listo!")


if __name__ == "__main__":
    main()
