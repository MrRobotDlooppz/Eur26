#!/usr/bin/env python3
"""
Descarga la imagen principal de Wikipedia para cada lugar de Firenze
y la guarda en Firenze/fotos/.
Intenta el título en italiano, luego en inglés. Máx 2 intentos por lugar.
"""

import json
import sys
import time
import urllib.request
import urllib.parse
from pathlib import Path

WIKI_API = "https://en.wikipedia.org/w/api.php"
WIKI_API_IT = "https://it.wikipedia.org/w/api.php"

PLACES = [
    # (wiki_title_it, wiki_title_en, output_filename, md_path)
    ("Galleria dell'Accademia (Firenze)", "Galleria dell'Accademia", "foto_galleria_accademia.jpg", "Firenze/lugares/galleria_accademia.md"),
    ("Basilica di Santa Croce", "Basilica of Santa Croce, Florence", "foto_basilica_santa_croce.jpg", "Firenze/lugares/basilica_santa_croce.md"),
    ("Palazzo Pitti", "Palazzo Pitti", "foto_palazzo_pitti_boboli.jpg", "Firenze/lugares/palazzo_pitti_boboli.md"),
    ("Piazzale Michelangelo", "Piazzale Michelangelo", "foto_piazzale_michelangelo.jpg", "Firenze/lugares/piazzale_michelangelo.md"),
    ("Museo Galileo", "Museo Galileo", "foto_museo_galileo.jpg", "Firenze/lugares/museo_galileo.md"),
    ("Loggia dei Lanzi", "Loggia dei Lanzi", "foto_loggia_dei_lanzi.jpg", "Firenze/lugares/loggia_dei_lanzi.md"),
    ("Basilica di San Lorenzo (Firenze)", "Basilica of San Lorenzo, Florence", "foto_san_lorenzo_cappelle_medicee.jpg", "Firenze/lugares/san_lorenzo_cappelle_medicee.md"),
    ("Museo nazionale del Bargello", "Bargello", "foto_bargello.jpg", "Firenze/lugares/bargello.md"),
    ("Basilica di Santa Maria Novella", "Santa Maria Novella", "foto_basilica_santa_maria_novella.jpg", "Firenze/lugares/basilica_santa_maria_novella.md"),
    ("Mercato Centrale (Firenze)", "Mercato Centrale, Florence", "foto_mercato_centrale_san_lorenzo.jpg", "Firenze/lugares/mercato_centrale_san_lorenzo.md"),
    ("Basilica di San Marco (Firenze)", "San Marco, Florence", "foto_basilica_museo_san_marco.jpg", "Firenze/lugares/basilica_museo_san_marco.md"),
    ("Fiesole", "Fiesole", "foto_fiesole.jpg", "Firenze/lugares/fiesole.md"),
    ("Museo di Leonardo da Vinci", "Museo di Leonardo da Vinci", "foto_museo_da_vinci.jpg", "Firenze/lugares/museo_da_vinci.md"),
    ("Tempio Maggiore di Firenze", "Florence Synagogue", "foto_sinagoga_museo_ebraico.jpg", "Firenze/lugares/sinagoga_museo_ebraico.md"),
    ("Biblioteca nazionale centrale di Firenze", "National Central Library, Florence", "foto_biblioteca_nazionale_centrale.jpg", "Firenze/lugares/biblioteca_nazionale_centrale.md"),
    ("Basilica di San Miniato al Monte", "San Miniato al Monte", "foto_abbazia_san_miniato_al_monte.jpg", "Firenze/lugares/abbazia_san_miniato_al_monte.md"),
    ("Galleria degli Uffizi", "Uffizi", "foto_galleria_degli_uffizi.jpg", "Firenze/lugares/galleria_degli_uffizi.md"),
    ("Palazzo Vecchio", "Palazzo Vecchio", "foto_palazzo_vecchio.jpg", "Firenze/lugares/palazzo_vecchio.md"),
    ("Ponte Vecchio", "Ponte Vecchio", "foto_ponte_vecchio.jpg", "Firenze/lugares/ponte_vecchio.md"),
    ("Cattedrale di Santa Maria del Fiore", "Florence Cathedral", "foto_duomo_firenze.jpg", "Firenze/lugares/piazza_del_duomo_complesso.md"),
]

OUTPUT_DIR = Path("Firenze/fotos")
REPO_ROOT = Path(__file__).resolve().parent.parent


def wiki_image_url(title: str, lang: str = "en", thumb_width: int = 1200) -> str | None:
    api = f"https://{lang}.wikipedia.org/w/api.php"
    params = urllib.parse.urlencode({
        "action": "query",
        "titles": title,
        "prop": "pageimages",
        "format": "json",
        "pithumbsize": thumb_width,
        "pilimit": 1,
    })
    url = f"{api}?{params}"
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "TravelNotesArchive/1.0"})
        with urllib.request.urlopen(req, timeout=10) as resp:
            data = json.loads(resp.read())
        pages = data.get("query", {}).get("pages", {})
        for page in pages.values():
            thumb = page.get("thumbnail", {})
            src = thumb.get("source")
            if src:
                return src
    except Exception as e:
        print(f"  [API error {lang}:{title}] {e}")
    return None


def download_image(url: str, dest: Path) -> bool:
    for attempt in range(3):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "TravelNotesArchive/1.0"})
            with urllib.request.urlopen(req, timeout=15) as resp:
                content = resp.read()
            dest.write_bytes(content)
            return True
        except Exception as e:
            wait = (attempt + 1) * 8
            print(f"  [attempt {attempt+1} error] {e} — esperando {wait}s...")
            time.sleep(wait)
    return False


def add_image_to_md(md_path: Path, foto_rel: str, alt_text: str) -> None:
    content = md_path.read_text(encoding="utf-8")
    img_line = f"\n![{alt_text}](../fotos/{foto_rel})\n"
    # Insertar después del bloque yaml (primer ```)
    # Buscamos la línea "## Mapa" y añadimos debajo si no existe ya la foto
    if foto_rel in content:
        print(f"  [skip] imagen ya referenciada en {md_path.name}")
        return
    # Insertar al final de la sección de Mapa o al principio del contenido
    marker = "## Mapa"
    if marker in content:
        insert_at = content.index(marker) + len(marker)
        content = content[:insert_at] + img_line + content[insert_at:]
    else:
        # Insertar después del bloque yaml de cierre
        yaml_end = content.find("```\n\n")
        if yaml_end != -1:
            insert_at = yaml_end + 5
            content = content[:insert_at] + img_line + content[insert_at:]
        else:
            content += img_line
    md_path.write_text(content, encoding="utf-8")


def main():
    only_failed = "--only-failed" in sys.argv
    out_dir = REPO_ROOT / OUTPUT_DIR
    out_dir.mkdir(parents=True, exist_ok=True)

    results = {"ok": [], "fail": []}

    for title_it, title_en, filename, md_rel in PLACES:
        dest = out_dir / filename

        # Si --only-failed, saltar los que ya tienen imagen descargada
        if only_failed and dest.exists():
            print(f"→ [skip already exists] {title_it}")
            continue

        print(f"\n→ {title_it}")
        md_path = REPO_ROOT / md_rel

        if not md_path.exists():
            print(f"  [skip] {md_rel} no existe")
            continue

        # Intento 1: Wikipedia italiano
        url = wiki_image_url(title_it, lang="it")
        if not url:
            # Intento 2: Wikipedia inglés
            url = wiki_image_url(title_en, lang="en")

        if not url:
            print(f"  [FAIL] no se encontró imagen")
            results["fail"].append(title_it)
            continue

        print(f"  URL: {url[:80]}...")
        ok = download_image(url, dest)
        if ok:
            print(f"  [OK] guardado en {OUTPUT_DIR / filename}")
            add_image_to_md(md_path, filename, f"Vista de {title_it}")
            results["ok"].append(title_it)
        else:
            print(f"  [FAIL] descarga fallida")
            results["fail"].append(title_it)

        time.sleep(3)  # rate limiting

    print("\n" + "="*50)
    print(f"OK ({len(results['ok'])}): {', '.join(results['ok'])}")
    print(f"FAIL ({len(results['fail'])}): {', '.join(results['fail'])}")


if __name__ == "__main__":
    main()
