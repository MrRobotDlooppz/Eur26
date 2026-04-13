#!/usr/bin/env python3
"""
Convierte archivos Markdown del repositorio en archivos MP3 usando edge-tts.

Uso:
    python tools/audio/generate_audio.py --input ciudades/Lucca/lugares/torre_guinigi.md --output docs/audio/Lucca/
    python tools/audio/generate_audio.py --input ciudades/Firenze/ --output docs/audio/
    python tools/audio/generate_audio.py --input . --output docs/audio/
    python tools/audio/generate_audio.py --list-voices
"""

import argparse
import asyncio
import os
import re
import sys
from pathlib import Path

try:
    import edge_tts
except ImportError:
    print("Error: edge-tts no está instalado. Ejecutá: pip install edge-tts", file=sys.stderr)
    sys.exit(1)

# Voz por defecto: femenina, español latinoamericano (México)
DEFAULT_VOICE = "es-MX-DaliaNeural"
DEFAULT_RATE = "+0%"

# Archivos a excluir de la generación de audio
EXCLUDED_FILES = {"README.md", "CLAUDE.md"}

# Carpetas de ciudad conocidas (se detectan automáticamente, pero esto ayuda)
CITY_FOLDERS = {"Roma", "Firenze", "Lucca", "Pisa", "Granada", "Madrid"}

# Carpeta base donde viven las ciudades
CITIES_DIR = "ciudades"


# ---------------------------------------------------------------------------
# Limpieza de Markdown → texto narrable
# ---------------------------------------------------------------------------

def clean_md_to_text(md_content: str) -> str:
    """Convierte contenido Markdown en texto limpio para narración TTS."""
    text = md_content

    # 1. Eliminar bloques de código YAML (frontmatter)
    text = re.sub(r"```yaml\s*\n.*?```", "", text, flags=re.DOTALL)

    # 2. Eliminar comentarios HTML
    text = re.sub(r"<!--.*?-->", "", text, flags=re.DOTALL)

    # 3. Eliminar imágenes markdown
    text = re.sub(r"!\[.*?\]\(.*?\)", "", text)

    # 4. Eliminar marcadores de verificación y datos pendientes
    text = re.sub(r"\[⚠\s*VERIFICAR[^\]]*\]", "", text)
    text = re.sub(r"\[DATO PENDIENTE[^\]]*\]", "", text)
    text = re.sub(r"\[AMBIGÜEDAD[^\]]*\]", "", text)

    # 5. Eliminar blockquotes con datos pendientes
    text = re.sub(r">\s*\[DATO PENDIENTE[^\]]*\]\s*\n?", "", text)

    # 6. Convertir tablas Markdown a texto narrativo
    text = _convert_tables(text)

    # 7. Convertir headers en pausas con nombre de sección
    # H1: título principal
    text = re.sub(r"^#\s+(.+)$", r"\n\1.\n", text, flags=re.MULTILINE)
    # H2: secciones principales
    text = re.sub(r"^##\s+(.+)$", r"\n\n\1.\n", text, flags=re.MULTILINE)
    # H3: subsecciones
    text = re.sub(r"^###\s+(.+)$", r"\n\1.\n", text, flags=re.MULTILINE)
    # H4+
    text = re.sub(r"^#{4,}\s+(.+)$", r"\n\1.\n", text, flags=re.MULTILINE)

    # 8. Eliminar separadores horizontales
    text = re.sub(r"^-{3,}\s*$", "", text, flags=re.MULTILINE)
    text = re.sub(r"^\*{3,}\s*$", "", text, flags=re.MULTILINE)

    # 9. Eliminar líneas de fuente al pie
    text = re.sub(r"^\*fuente:.*?\*\s*$", "", text, flags=re.MULTILINE | re.IGNORECASE)
    text = re.sub(r"^fuente:.*$", "", text, flags=re.MULTILINE | re.IGNORECASE)

    # 10. Convertir links markdown: [texto](url) → texto
    text = re.sub(r"\[([^\]]+)\]\([^)]+\)", r"\1", text)

    # 11. Limpiar formato bold e italic
    text = re.sub(r"\*\*\*(.+?)\*\*\*", r"\1", text)  # bold+italic
    text = re.sub(r"\*\*(.+?)\*\*", r"\1", text)       # bold
    text = re.sub(r"\*(.+?)\*", r"\1", text)            # italic
    text = re.sub(r"__(.+?)__", r"\1", text)            # bold alt
    text = re.sub(r"_(.+?)_", r"\1", text)              # italic alt

    # 12. Limpiar inline code
    text = re.sub(r"`(.+?)`", r"\1", text)

    # 13. Convertir listas con viñetas en oraciones
    text = re.sub(r"^\s*[-*+]\s+", "• ", text, flags=re.MULTILINE)

    # 14. Limpiar múltiples líneas en blanco
    text = re.sub(r"\n{3,}", "\n\n", text)

    # 15. Limpiar espacios extra
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r" +\n", "\n", text)

    return text.strip()


def _convert_tables(text: str) -> str:
    """Convierte tablas Markdown en texto narrativo."""
    lines = text.split("\n")
    result = []
    i = 0

    while i < len(lines):
        # Detectar inicio de tabla (línea con |)
        if "|" in lines[i] and i + 1 < len(lines) and re.match(r"\s*\|[\s\-:|]+\|", lines[i + 1]):
            table_lines = []
            # Leer header
            header = [c.strip() for c in lines[i].split("|") if c.strip()]
            i += 2  # saltar header y separador

            # Leer filas
            while i < len(lines) and "|" in lines[i] and lines[i].strip():
                cols = [c.strip() for c in lines[i].split("|") if c.strip()]
                table_lines.append(cols)
                i += 1

            # Convertir a texto narrativo
            result.append(_table_to_narrative(header, table_lines))
        else:
            result.append(lines[i])
            i += 1

    return "\n".join(result)


def _table_to_narrative(header: list[str], rows: list[list[str]]) -> str:
    """Convierte una tabla con header y filas en texto narrativo."""
    if not rows:
        return ""

    # Detectar si es tabla de timeline (columnas: Fecha/Año + Hito/Evento)
    header_lower = [h.lower() for h in header]
    is_timeline = any(
        w in h for h in header_lower for w in ("fecha", "año", "siglo", "periodo", "date", "year")
    )

    narratives = []
    for row in rows:
        if len(row) >= 2:
            if is_timeline:
                narratives.append(f"En {row[0]}: {row[1]}.")
            else:
                # Tabla genérica: "Header1: valor1. Header2: valor2."
                parts = []
                for j, cell in enumerate(row):
                    if j < len(header):
                        parts.append(f"{header[j]}: {cell}")
                    else:
                        parts.append(cell)
                narratives.append(". ".join(parts) + ".")
        elif len(row) == 1:
            narratives.append(row[0] + ".")

    return "\n".join(narratives)


# ---------------------------------------------------------------------------
# Descubrimiento de archivos
# ---------------------------------------------------------------------------

def discover_md_files(input_path: Path, repo_root: Path) -> list[tuple[Path, str]]:
    """
    Descubre archivos .md para convertir.
    Retorna lista de (ruta_md, ciudad) donde ciudad es el nombre de la carpeta padre.
    """
    results = []

    if input_path.is_file():
        if input_path.suffix == ".md":
            city = _get_city_name(input_path, repo_root)
            results.append((input_path, city))
        return results

    if not input_path.is_dir():
        print(f"Error: {input_path} no existe", file=sys.stderr)
        return results

    # Si es la raíz del repo, buscar en todas las carpetas de ciudad
    for md_file in sorted(input_path.rglob("*.md")):
        # Excluir archivos de nivel raíz que no son contenido
        if md_file.name in EXCLUDED_FILES:
            continue

        # Excluir archivos dentro de tools/, .github/, docs/
        rel = md_file.relative_to(repo_root)
        first_part = rel.parts[0] if rel.parts else ""
        if first_part in ("tools", ".github", "docs", ".venv"):
            continue

        # Solo incluir archivos dentro de ciudades/ (estructura: ciudades/Ciudad/...)
        # o directamente en una carpeta de ciudad conocida (compatibilidad)
        if first_part == CITIES_DIR:
            # ciudades/Roma/archivo.md → needs at least 3 parts
            if len(rel.parts) < 3:
                continue
        elif first_part in CITY_FOLDERS:
            # Legacy: Roma/archivo.md
            if len(rel.parts) < 2:
                continue
        else:
            continue

        # Verificar que tiene contenido narrativo (mínimo 10 líneas de texto)
        if not _is_narrative(md_file):
            print(f"  Saltando (no narrativo): {rel}")
            continue

        city = _get_city_name(md_file, repo_root)
        results.append((md_file, city))

    return results


def _get_city_name(md_file: Path, repo_root: Path) -> str:
    """Obtiene el nombre de la ciudad a partir de la ruta del archivo."""
    try:
        rel = md_file.relative_to(repo_root)
        # Si está en ciudades/Roma/... → parts[1] es la ciudad
        if rel.parts[0] == CITIES_DIR and len(rel.parts) > 2:
            return rel.parts[1]
        # Legacy: Roma/... → parts[0] es la ciudad
        return rel.parts[0] if len(rel.parts) > 1 else "General"
    except ValueError:
        return "General"


def _is_narrative(md_file: Path) -> bool:
    """Determina si un archivo .md tiene suficiente contenido narrativo."""
    try:
        content = md_file.read_text(encoding="utf-8")
    except Exception:
        return False

    # Limpiar y contar líneas no vacías de texto puro
    cleaned = clean_md_to_text(content)
    lines = [l for l in cleaned.split("\n") if l.strip()]
    return len(lines) >= 5


# ---------------------------------------------------------------------------
# Generación de audio
# ---------------------------------------------------------------------------

async def generate_mp3(text: str, output_path: Path, voice: str, rate: str) -> bool:
    """Genera un archivo MP3 a partir de texto usando edge-tts."""
    try:
        communicate = edge_tts.Communicate(text, voice, rate=rate)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        await communicate.save(str(output_path))
        return True
    except Exception as e:
        print(f"  Error generando audio: {e}", file=sys.stderr)
        return False


def needs_regeneration(md_file: Path, mp3_file: Path, force: bool) -> bool:
    """Determina si el MP3 necesita ser regenerado."""
    if force:
        return True
    if not mp3_file.exists():
        return True
    # Regenerar si el .md es más nuevo que el .mp3
    return md_file.stat().st_mtime > mp3_file.stat().st_mtime


def md_to_mp3_filename(md_file: Path) -> str:
    """Convierte nombre de archivo .md a .mp3."""
    return md_file.stem + ".mp3"


# ---------------------------------------------------------------------------
# Listar voces
# ---------------------------------------------------------------------------

async def list_voices_es():
    """Lista todas las voces disponibles en español."""
    voices = await edge_tts.list_voices()
    es_voices = [v for v in voices if v["Locale"].startswith("es-")]

    print("\nVoces disponibles en español:\n")
    print(f"{'Nombre':<35} {'Locale':<10} {'Género':<12}")
    print("-" * 60)

    for v in sorted(es_voices, key=lambda x: (x["Locale"], x["Gender"])):
        print(f"{v['ShortName']:<35} {v['Locale']:<10} {v['Gender']:<12}")

    print(f"\nTotal: {len(es_voices)} voces")
    print(f"\nVoz por defecto: {DEFAULT_VOICE}")
    print("\nEjemplo de uso: --voice es-AR-ElenaNeural")


# ---------------------------------------------------------------------------
# CLI principal
# ---------------------------------------------------------------------------

async def main():
    parser = argparse.ArgumentParser(
        description="Convierte archivos Markdown en MP3 usando edge-tts"
    )
    parser.add_argument(
        "--input", "-i",
        type=str,
        default=".",
        help="Ruta a un .md, carpeta de ciudad, o raíz del repo (default: .)"
    )
    parser.add_argument(
        "--output", "-o",
        type=str,
        default="docs/audio",
        help="Carpeta destino para los MP3 (default: docs/audio/)"
    )
    parser.add_argument(
        "--voice", "-v",
        type=str,
        default=DEFAULT_VOICE,
        help=f"Voz de edge-tts (default: {DEFAULT_VOICE})"
    )
    parser.add_argument(
        "--rate", "-r",
        type=str,
        default=DEFAULT_RATE,
        help=f"Velocidad de narración (default: {DEFAULT_RATE}). Ej: +10%%, -5%%"
    )
    parser.add_argument(
        "--force", "-f",
        action="store_true",
        help="Regenerar MP3 aunque ya exista"
    )
    parser.add_argument(
        "--list-voices",
        action="store_true",
        help="Listar voces disponibles en español y salir"
    )

    args = parser.parse_args()

    if args.list_voices:
        await list_voices_es()
        return

    # Detectar raíz del repositorio
    repo_root = Path(__file__).resolve().parent.parent.parent
    input_path = Path(args.input).resolve()
    output_dir = Path(args.output)
    if not output_dir.is_absolute():
        output_dir = repo_root / output_dir

    print(f"Raíz del repo: {repo_root}")
    print(f"Input: {input_path}")
    print(f"Output: {output_dir}")
    print(f"Voz: {args.voice}")
    print(f"Rate: {args.rate}")
    print()

    # Descubrir archivos
    md_files = discover_md_files(input_path, repo_root)

    if not md_files:
        print("No se encontraron archivos .md para convertir.")
        return

    print(f"Encontrados {len(md_files)} archivos .md para convertir:\n")

    success = 0
    skipped = 0
    failed = 0

    for md_file, city in md_files:
        rel_path = md_file.relative_to(repo_root)
        mp3_name = md_to_mp3_filename(md_file)
        mp3_path = output_dir / city / mp3_name

        if not needs_regeneration(md_file, mp3_path, args.force):
            print(f"  ⏭  {rel_path} → ya existe, saltando")
            skipped += 1
            continue

        print(f"  🎙  {rel_path} → {mp3_path.relative_to(repo_root)} ...", end=" ", flush=True)

        # Leer y limpiar
        content = md_file.read_text(encoding="utf-8")
        text = clean_md_to_text(content)

        if len(text.strip()) < 50:
            print("(texto muy corto, saltando)")
            skipped += 1
            continue

        # Generar MP3
        ok = await generate_mp3(text, mp3_path, args.voice, args.rate)
        if ok:
            size_kb = mp3_path.stat().st_size / 1024
            print(f"OK ({size_kb:.0f} KB)")
            success += 1
        else:
            print("FALLÓ")
            failed += 1

    print(f"\nResultado: {success} generados, {skipped} saltados, {failed} fallidos")


if __name__ == "__main__":
    asyncio.run(main())
