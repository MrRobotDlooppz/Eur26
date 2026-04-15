#!/usr/bin/env python3
"""
Descarga la imagen principal de Wikipedia para cada lugar y la guarda
en la carpeta fotos/ de la ciudad correspondiente.

Uso:
  python tools/fetch_wiki_images.py --config tools/wiki_images/roma.json
  python tools/fetch_wiki_images.py --config tools/wiki_images/toledo.json --only-failed
  python tools/fetch_wiki_images.py --all          # procesa todos los JSON en tools/wiki_images/
"""

import argparse
import json
import sys
import time
import urllib.request
import urllib.parse
from pathlib import Path

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
    if foto_rel in content:
        print(f"  [skip] imagen ya referenciada en {md_path.name}")
        return
    # Insertar después del bloque de mapa (buscar última línea de mapa_*)
    import re
    # Buscar la última referencia a mapa_*
    last_map = None
    for m in re.finditer(r"!\[.*?\]\(\.\./fotos/mapa_.*?\)", content):
        last_map = m
    if last_map:
        insert_at = content.index("\n", last_map.end()) + 1
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


def load_config(config_path: Path) -> dict:
    """Carga un JSON de configuración de ciudad."""
    with open(config_path, encoding="utf-8") as f:
        return json.load(f)


def process_city(config: dict, only_failed: bool = False) -> dict:
    """Procesa una ciudad: descarga fotos y actualiza markdowns."""
    city_name = config["city"]
    city_dir = config["city_dir"]  # e.g. "ciudades/Roma"
    lang = config.get("lang", "en")  # idioma local de Wikipedia
    places = config["places"]

    out_dir = REPO_ROOT / city_dir / "fotos"
    out_dir.mkdir(parents=True, exist_ok=True)

    results = {"ok": [], "fail": [], "skip": []}

    for place in places:
        wiki_local = place["wiki_local"]
        wiki_en = place["wiki_en"]
        filename = place["filename"]
        md_rel = place["md_path"]

        dest = out_dir / filename
        md_path = REPO_ROOT / city_dir / md_rel

        if only_failed and dest.exists():
            print(f"  [skip exists] {wiki_local}")
            results["skip"].append(wiki_local)
            continue

        if dest.exists():
            print(f"  [skip exists] {wiki_local}")
            results["skip"].append(wiki_local)
            continue

        print(f"\n→ [{city_name}] {wiki_local}")

        if not md_path.exists():
            print(f"  [skip] {md_rel} no existe")
            results["fail"].append(wiki_local)
            continue

        # Intento 1: Wikipedia en idioma local
        url = wiki_image_url(wiki_local, lang=lang)
        if not url:
            # Intento 2: Wikipedia inglés
            url = wiki_image_url(wiki_en, lang="en")

        if not url:
            print(f"  [FAIL] no se encontró imagen")
            results["fail"].append(wiki_local)
            continue

        print(f"  URL: {url[:80]}...")
        ok = download_image(url, dest)
        if ok:
            print(f"  [OK] guardado en {city_dir}/fotos/{filename}")
            add_image_to_md(md_path, filename, f"Vista de {wiki_local}")
            results["ok"].append(wiki_local)
        else:
            print(f"  [FAIL] descarga fallida")
            results["fail"].append(wiki_local)

        time.sleep(3)

    return results


def main():
    parser = argparse.ArgumentParser(description="Descarga imágenes de Wikipedia para lugares")
    parser.add_argument("--config", type=Path, help="Archivo JSON de configuración de ciudad")
    parser.add_argument("--all", action="store_true", help="Procesar todos los JSON en tools/wiki_images/")
    parser.add_argument("--only-failed", action="store_true", help="Solo reintentar los que fallaron")
    args = parser.parse_args()

    configs_dir = REPO_ROOT / "tools" / "wiki_images"

    if args.all:
        config_files = sorted(configs_dir.glob("*.json"))
    elif args.config:
        config_files = [args.config]
    else:
        print("Uso: --config <archivo.json> o --all")
        sys.exit(1)

    all_results = {"ok": [], "fail": [], "skip": []}

    for cf in config_files:
        print(f"\n{'='*50}")
        print(f"Procesando: {cf.name}")
        print(f"{'='*50}")
        config = load_config(cf)
        results = process_city(config, only_failed=args.only_failed)
        for k in all_results:
            all_results[k].extend(results[k])

    print(f"\n{'='*50}")
    print(f"RESUMEN TOTAL")
    print(f"OK ({len(all_results['ok'])}): {', '.join(all_results['ok'])}")
    print(f"FAIL ({len(all_results['fail'])}): {', '.join(all_results['fail'])}")
    print(f"SKIP ({len(all_results['skip'])}): {len(all_results['skip'])} ya existían")


if __name__ == "__main__":
    main()
