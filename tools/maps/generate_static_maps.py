#!/usr/bin/env python3
"""Generate static map images with a pin for places listed in a JSON file.

Usage:
  python tools/maps/generate_static_maps.py \
    --input tools/maps/roma_places.json \
    --output Roma/fotos
"""

import argparse
import json
import math
import sys
from pathlib import Path

from PIL import ImageDraw, ImageFont
from staticmap import CircleMarker, StaticMap


# Puntos de referencia globales para dar contexto urbano en todos los mapas.
ROMA_PUNTOS_PRINCIPALES = [
    {"nombre": "Colosseo", "lat": 41.8902, "lon": 12.4922},
    {"nombre": "Pantheon", "lat": 41.8986, "lon": 12.4769},
    {"nombre": "Piazza del Popolo", "lat": 41.9106, "lon": 12.4764},
    {"nombre": "Basilica di San Pietro", "lat": 41.9022, "lon": 12.4539},
    {"nombre": "Termini", "lat": 41.9010, "lon": 12.5018},
    {"nombre": "Vittoriano", "lat": 41.8946, "lon": 12.4833},
]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Generate static map images with a pin")
    parser.add_argument(
        "--input",
        required=True,
        help="Path to JSON file with places",
    )
    parser.add_argument(
        "--output",
        required=True,
        help="Output directory for PNG images",
    )
    parser.add_argument("--width", type=int, default=900, help="Image width")
    parser.add_argument("--height", type=int, default=650, help="Image height")
    parser.add_argument("--zoom", type=int, default=14, help="Map zoom level")
    parser.add_argument(
        "--marker-color",
        default="red",
        help="Marker color name understood by PIL (default: red)",
    )
    parser.add_argument("--marker-size", type=int, default=12, help="Marker radius in px")
    parser.add_argument(
        "--detail-zoom",
        type=int,
        default=19,
        help="Zoom level for the additional detailed map",
    )
    parser.add_argument(
        "--detail-suffix",
        default="_detalle",
        help="Suffix added before .png for the additional detailed map",
    )
    parser.add_argument(
        "--no-detail-map",
        action="store_true",
        help="Generate only the main map and skip the additional detail map",
    )
    parser.add_argument(
        "--no-city-context",
        action="store_true",
        help="Disable global city reference markers",
    )
    return parser.parse_args()


def load_places(input_path: Path) -> list[dict]:
    with input_path.open("r", encoding="utf-8") as f:
        data = json.load(f)

    if not isinstance(data, list):
        raise ValueError("Input JSON must be a list of place objects")

    required = {"nombre", "archivo", "lat", "lon"}
    for idx, place in enumerate(data, start=1):
        if not isinstance(place, dict):
            raise ValueError(f"Place #{idx} is not an object")
        missing = required - set(place.keys())
        if missing:
            raise ValueError(f"Place #{idx} missing keys: {', '.join(sorted(missing))}")

    return data


def add_reference_markers(m: StaticMap, place: dict) -> None:
    refs = place.get("referencias", [])
    if not isinstance(refs, list):
        return

    for ref in refs:
        if not isinstance(ref, dict):
            continue
        if "lat" not in ref or "lon" not in ref:
            continue
        try:
            ref_lon = float(ref["lon"])
            ref_lat = float(ref["lat"])
        except (TypeError, ValueError):
            continue
        m.add_marker(CircleMarker((ref_lon, ref_lat), "#2563eb", 7))


def add_city_context_markers(m: StaticMap) -> None:
    for ref in ROMA_PUNTOS_PRINCIPALES:
        m.add_marker(CircleMarker((float(ref["lon"]), float(ref["lat"])), "#64748b", 5))


def project_lonlat_to_pixel(
    lon: float,
    lat: float,
    center_lon: float,
    center_lat: float,
    zoom: int,
    width: int,
    height: int,
) -> tuple[float, float]:
    """Project lon/lat to image pixel using Web Mercator at fixed center and zoom."""

    def mercator_x(lon_deg: float, z: int) -> float:
        return (lon_deg + 180.0) / 360.0 * (256 * (2**z))

    def mercator_y(lat_deg: float, z: int) -> float:
        lat_rad = math.radians(max(min(lat_deg, 85.0511), -85.0511))
        return (
            (1.0 - math.log(math.tan(lat_rad) + 1.0 / math.cos(lat_rad)) / math.pi)
            / 2.0
            * (256 * (2**z))
        )

    px = mercator_x(lon, zoom)
    py = mercator_y(lat, zoom)
    cpx = mercator_x(center_lon, zoom)
    cpy = mercator_y(center_lat, zoom)

    return (width / 2.0 + (px - cpx), height / 2.0 + (py - cpy))


def draw_label(
    draw: ImageDraw.ImageDraw,
    text: str,
    x: float,
    y: float,
    font: ImageFont.ImageFont,
    text_color: str,
) -> None:
    # Offset so text does not sit directly over the marker.
    tx = int(x + 10)
    ty = int(y - 18)

    bbox = draw.textbbox((tx, ty), text, font=font)
    pad = 3
    draw.rectangle(
        [bbox[0] - pad, bbox[1] - pad, bbox[2] + pad, bbox[3] + pad],
        fill="white",
        outline="#d1d5db",
    )
    draw.text((tx, ty), text, fill=text_color, font=font)


def annotate_labels(
    image,
    place: dict,
    zoom: int,
    width: int,
    height: int,
) -> None:
    draw = ImageDraw.Draw(image)
    font = ImageFont.load_default()

    center_lon = float(place["lon"])
    center_lat = float(place["lat"])

    # Main place label.
    mx, my = project_lonlat_to_pixel(
        lon=center_lon,
        lat=center_lat,
        center_lon=center_lon,
        center_lat=center_lat,
        zoom=zoom,
        width=width,
        height=height,
    )
    draw_label(draw, place["nombre"], mx, my, font, "#b91c1c")

    # Reference labels.
    refs = place.get("referencias", [])
    if isinstance(refs, list):
        for ref in refs:
            if not isinstance(ref, dict):
                continue
            if "lat" not in ref or "lon" not in ref or "nombre" not in ref:
                continue
            try:
                rx, ry = project_lonlat_to_pixel(
                    lon=float(ref["lon"]),
                    lat=float(ref["lat"]),
                    center_lon=center_lon,
                    center_lat=center_lat,
                    zoom=zoom,
                    width=width,
                    height=height,
                )
            except (TypeError, ValueError):
                continue

            # Skip labels that would be far outside image bounds.
            if rx < -80 or rx > width + 80 or ry < -40 or ry > height + 40:
                continue
            draw_label(draw, str(ref["nombre"]), rx, ry, font, "#1d4ed8")


def render_place(
    place: dict,
    output_dir: Path,
    width: int,
    height: int,
    zoom: int,
    marker_color: str,
    marker_size: int,
    include_city_context: bool,
) -> Path:
    out_path = output_dir / place["archivo"]
    lon = float(place["lon"])
    lat = float(place["lat"])

    m = StaticMap(width, height)

    if include_city_context:
        add_city_context_markers(m)

    # Main place marker.
    m.add_marker(CircleMarker((lon, lat), marker_color, marker_size))

    # Optional nearby reference markers to give context on the same map tile.
    add_reference_markers(m, place)

    # Keep map centered on the main place so label projection is deterministic.
    image = m.render(zoom=zoom, center=(lon, lat))
    annotate_labels(image=image, place=place, zoom=zoom, width=width, height=height)
    image.save(out_path)
    return out_path


def detail_map_filename(base_filename: str, suffix: str) -> str:
    base_path = Path(base_filename)
    stem = base_path.stem + suffix
    return f"{stem}{base_path.suffix}"


def main() -> int:
    args = parse_args()

    input_path = Path(args.input)
    output_dir = Path(args.output)

    if not input_path.exists():
        print(f"ERROR: input file not found: {input_path}", file=sys.stderr)
        return 1

    output_dir.mkdir(parents=True, exist_ok=True)

    try:
        places = load_places(input_path)
    except Exception as exc:
        print(f"ERROR loading input JSON: {exc}", file=sys.stderr)
        return 1

    generated = []
    for place in places:
        try:
            out_path = render_place(
                place=place,
                output_dir=output_dir,
                width=args.width,
                height=args.height,
                zoom=args.zoom,
                marker_color=args.marker_color,
                marker_size=args.marker_size,
                include_city_context=not args.no_city_context,
            )
            generated.append(out_path)
            print(f"OK {place['nombre']}: {out_path}")

            if not args.no_detail_map:
                detail_place = dict(place)
                detail_place["archivo"] = detail_map_filename(place["archivo"], args.detail_suffix)
                detail_out_path = render_place(
                    place=detail_place,
                    output_dir=output_dir,
                    width=args.width,
                    height=args.height,
                    zoom=args.detail_zoom,
                    marker_color=args.marker_color,
                    marker_size=args.marker_size,
                    include_city_context=False,
                )
                generated.append(detail_out_path)
                print(f"OK {place['nombre']} (detalle): {detail_out_path}")
        except Exception as exc:
            print(f"ERROR {place.get('nombre', '<sin nombre>')}: {exc}", file=sys.stderr)
            return 1

    print(f"Generated {len(generated)} map images in {output_dir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
