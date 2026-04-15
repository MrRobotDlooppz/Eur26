#!/usr/bin/env python3
"""
Convierte archivos Markdown del repositorio en fragmentos HTML para el panel de guía.

Genera archivos HTML individuales (sin <html>/<body>, solo contenido) en docs/text/{Ciudad}/
que el player.js carga dinámicamente cuando el usuario pulsa 📖.

Uso:
    python tools/audio/generate_text.py                           # todo el repo
    python tools/audio/generate_text.py --input ciudades/Lucca/   # solo una ciudad
    python tools/audio/generate_text.py --force                   # regenerar todo
"""

import argparse
import os
import re
import shutil
import sys
from pathlib import Path

# Reutilizar la lógica de descubrimiento de archivos de generate_audio
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from generate_audio import discover_md_files, EXCLUDED_FILES


def md_to_html(md_content: str, city: str = "", md_file: Path = None, repo_root: Path = None, output_root: Path = None) -> str:
    """Convierte Markdown a HTML fragmentario (sin wrapper html/body)."""
    text = md_content

    # 1. Eliminar frontmatter YAML
    text = re.sub(r"^```yaml\s*\n.*?```\s*\n?", "", text, flags=re.DOTALL)
    text = re.sub(r"^---\s*\n.*?---\s*\n?", "", text, flags=re.DOTALL)

    # 2. Eliminar comentarios HTML
    text = re.sub(r"<!--.*?-->", "", text, flags=re.DOTALL)

    # 3. Convertir imágenes markdown a <img> y copiar archivos a docs/fotos/
    def _convert_image(m):
        alt = m.group(1)
        src = m.group(2)
        if md_file and repo_root and output_root and city:
            # Resolver ruta absoluta de la imagen desde el .md
            img_abs = (md_file.parent / src).resolve()
            if img_abs.exists():
                # Copiar a docs/fotos/{Ciudad}/
                fotos_dir = output_root.parent / "fotos" / city
                fotos_dir.mkdir(parents=True, exist_ok=True)
                dest = fotos_dir / img_abs.name
                if not dest.exists() or img_abs.stat().st_mtime > dest.stat().st_mtime:
                    shutil.copy2(img_abs, dest)
                # Ruta relativa desde docs/ (donde se sirve index.html)
                return f'<img src="fotos/{city}/{img_abs.name}" alt="{alt}" style="max-width:100%;border-radius:8px;margin:8px 0">\n'
        return ""  # Si no se puede resolver, omitir
    text = re.sub(r"!\[([^\]]*)\]\(([^)]+)\)\s*\n?", _convert_image, text)

    # 4. Eliminar marcadores de verificación y datos pendientes
    text = re.sub(r"\[⚠\s*VERIFICAR[^\]]*\]", "", text)
    text = re.sub(r"\[DATO PENDIENTE[^\]]*\]", "", text)
    text = re.sub(r"\[AMBIGÜEDAD[^\]]*\]", "", text)

    # 5. Eliminar blockquotes con datos pendientes
    text = re.sub(r">\s*\[DATO PENDIENTE[^\]]*\]\s*\n?", "", text)

    # 6. Convertir a HTML usando markdown lib si está disponible, sino manual
    try:
        import markdown
        html = markdown.markdown(
            text,
            extensions=["tables", "fenced_code"],
            output_format="html5",
        )
    except ImportError:
        html = _manual_md_to_html(text)

    # 7. Limpiar líneas vacías excesivas en el HTML
    html = re.sub(r"\n{3,}", "\n\n", html)

    return html.strip()


def _manual_md_to_html(text: str) -> str:
    """Conversión manual básica Markdown → HTML (fallback sin lib markdown)."""
    lines = text.split("\n")
    html_lines = []
    in_list = False
    in_table = False

    for line in lines:
        stripped = line.strip()

        # Headers
        m = re.match(r"^(#{1,6})\s+(.+)$", stripped)
        if m:
            if in_list:
                html_lines.append("</ul>")
                in_list = False
            level = len(m.group(1))
            html_lines.append(f"<h{level}>{_inline_fmt(m.group(2))}</h{level}>")
            continue

        # Horizontal rules
        if re.match(r"^[-*]{3,}\s*$", stripped):
            html_lines.append("<hr>")
            continue

        # List items
        if re.match(r"^[-*+]\s+", stripped):
            if not in_list:
                html_lines.append("<ul>")
                in_list = True
            content = re.sub(r"^[-*+]\s+", "", stripped)
            html_lines.append(f"<li>{_inline_fmt(content)}</li>")
            continue

        # End list if not list item
        if in_list and not stripped:
            html_lines.append("</ul>")
            in_list = False

        # Table rows (basic)
        if "|" in stripped and stripped.startswith("|"):
            if re.match(r"^\|[\s\-:|]+\|$", stripped):
                continue  # separator row
            cells = [c.strip() for c in stripped.split("|")[1:-1]]
            if not in_table:
                html_lines.append("<table>")
                html_lines.append("<tr>" + "".join(f"<th>{_inline_fmt(c)}</th>" for c in cells) + "</tr>")
                in_table = True
            else:
                html_lines.append("<tr>" + "".join(f"<td>{_inline_fmt(c)}</td>" for c in cells) + "</tr>")
            continue

        if in_table and not ("|" in stripped):
            html_lines.append("</table>")
            in_table = False

        # Empty line
        if not stripped:
            html_lines.append("")
            continue

        # Regular paragraph
        html_lines.append(f"<p>{_inline_fmt(stripped)}</p>")

    if in_list:
        html_lines.append("</ul>")
    if in_table:
        html_lines.append("</table>")

    return "\n".join(html_lines)


def _inline_fmt(text: str) -> str:
    """Aplica formato inline: bold, italic, links, code."""
    # Links: [text](url)
    text = re.sub(r"\[([^\]]+)\]\(([^)]+)\)", r'<a href="\2">\1</a>', text)
    # Bold+italic
    text = re.sub(r"\*\*\*(.+?)\*\*\*", r"<strong><em>\1</em></strong>", text)
    # Bold
    text = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", text)
    text = re.sub(r"__(.+?)__", r"<strong>\1</strong>", text)
    # Italic
    text = re.sub(r"\*(.+?)\*", r"<em>\1</em>", text)
    text = re.sub(r"_(.+?)_", r"<em>\1</em>", text)
    # Inline code
    text = re.sub(r"`(.+?)`", r"<code>\1</code>", text)
    return text


def needs_regeneration(md_file: Path, html_file: Path, force: bool) -> bool:
    if force:
        return True
    if not html_file.exists():
        return True
    return md_file.stat().st_mtime > html_file.stat().st_mtime


def main():
    parser = argparse.ArgumentParser(
        description="Convierte archivos .md en fragmentos HTML para el panel de guía"
    )
    parser.add_argument("--input", "-i", type=str, default=".",
                        help="Archivo .md o carpeta a procesar (default: repo completo)")
    parser.add_argument("--output", "-o", type=str, default="docs/text",
                        help="Carpeta de salida (default: docs/text/)")
    parser.add_argument("--force", "-f", action="store_true",
                        help="Regenerar todo aunque los HTML sean más nuevos")
    args = parser.parse_args()

    repo_root = Path(__file__).resolve().parent.parent.parent
    input_path = Path(args.input)
    if not input_path.is_absolute():
        input_path = repo_root / input_path

    output_dir = Path(args.output)
    if not output_dir.is_absolute():
        output_dir = repo_root / output_dir

    print(f"Buscando archivos .md en: {input_path}")
    files = discover_md_files(input_path, repo_root)
    print(f"Encontrados {len(files)} archivos con contenido narrativo")

    generated = 0
    skipped = 0
    errors = 0

    for md_file, city in files:
        html_name = md_file.stem + ".html"
        html_file = output_dir / city / html_name

        if not needs_regeneration(md_file, html_file, args.force):
            skipped += 1
            continue

        try:
            md_content = md_file.read_text(encoding="utf-8")
            html_content = md_to_html(md_content, city=city, md_file=md_file, repo_root=repo_root, output_root=output_dir)

            if not html_content.strip():
                skipped += 1
                continue

            html_file.parent.mkdir(parents=True, exist_ok=True)
            html_file.write_text(html_content, encoding="utf-8")
            rel = md_file.relative_to(repo_root)
            print(f"  ✓ {rel} → {html_file.relative_to(repo_root)}")
            generated += 1
        except Exception as e:
            print(f"  ✗ {md_file}: {e}", file=sys.stderr)
            errors += 1

    print(f"\nResultado: {generated} generados, {skipped} sin cambios, {errors} errores")


if __name__ == "__main__":
    main()
