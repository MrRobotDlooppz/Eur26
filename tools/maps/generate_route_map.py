#!/usr/bin/env python3
"""Generate route maps with ordered stops, lines, and numbered markers.

Usage:
  python tools/maps/generate_route_map.py \
    --input tools/maps/foro_palatino_route.json \
    --output Rome/fotos/mapa_recorrido_foro_palatino.png \
    --detail-output Rome/fotos/mapa_recorrido_foro_palatino_detalle.png
"""

import argparse
import json
import math
import sys
from pathlib import Path

from PIL import ImageDraw, ImageFont
from staticmap import StaticMap


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Generate a route map with line and ordered stops")
    parser.add_argument("--input", required=True, help="Input JSON route file")
    parser.add_argument("--output", required=True, help="Output PNG for the main route map")
    parser.add_argument(
        "--detail-output",
        required=True,
        help="Output PNG for the detailed route map",
    )
    parser.add_argument("--width", type=int, default=1400, help="Image width")
    parser.add_argument("--height", type=int, default=1000, help="Image height")
    parser.add_argument(
        "--line-color",
        default="#dc2626",
        help="Route line color (hex)",
    )
    parser.add_argument("--line-width", type=int, default=6, help="Route line width")
    parser.add_argument(
        "--main-padding",
        type=float,
        default=0.76,
        help="Main map fit factor. Lower means more margin.",
    )
    parser.add_argument(
        "--detail-padding",
        type=float,
        default=0.92,
        help="Detail map fit factor. Higher means tighter zoom.",
    )
    return parser.parse_args()


def load_route_points(input_path: Path) -> list[dict]:
    with input_path.open("r", encoding="utf-8") as f:
        data = json.load(f)

    if not isinstance(data, list):
        raise ValueError("Input JSON must be a list of route stop objects")

    normalized = []
    for idx, point in enumerate(data, start=1):
        if not isinstance(point, dict):
            raise ValueError(f"Stop #{idx} is not an object")
        missing = {"nombre", "lat", "lon"} - set(point.keys())
        if missing:
            raise ValueError(f"Stop #{idx} missing keys: {', '.join(sorted(missing))}")

        try:
            lat = float(point["lat"])
            lon = float(point["lon"])
        except (TypeError, ValueError):
            raise ValueError(f"Stop #{idx} has invalid lat/lon")

        orden = point.get("orden", idx)
        try:
            orden = int(orden)
        except (TypeError, ValueError):
            orden = idx

        normalized.append(
            {
                "nombre": str(point["nombre"]),
                "lat": lat,
                "lon": lon,
                "orden": orden,
            }
        )

    normalized.sort(key=lambda p: p["orden"])
    return normalized


def mercator_x(lon_deg: float, zoom: int) -> float:
    return (lon_deg + 180.0) / 360.0 * (256 * (2**zoom))


def mercator_y(lat_deg: float, zoom: int) -> float:
    lat_rad = math.radians(max(min(lat_deg, 85.0511), -85.0511))
    return (
        (1.0 - math.log(math.tan(lat_rad) + 1.0 / math.cos(lat_rad)) / math.pi)
        / 2.0
        * (256 * (2**zoom))
    )


def route_center(points: list[dict]) -> tuple[float, float]:
    min_lat = min(p["lat"] for p in points)
    max_lat = max(p["lat"] for p in points)
    min_lon = min(p["lon"] for p in points)
    max_lon = max(p["lon"] for p in points)
    return ((min_lon + max_lon) / 2.0, (min_lat + max_lat) / 2.0)


def fit_zoom(points: list[dict], width: int, height: int, padding_factor: float) -> int:
    if len(points) == 1:
        return 18

    min_lon = min(p["lon"] for p in points)
    max_lon = max(p["lon"] for p in points)
    min_lat = min(p["lat"] for p in points)
    max_lat = max(p["lat"] for p in points)

    if min_lon == max_lon and min_lat == max_lat:
        return 18

    max_w = max(1.0, width * padding_factor)
    max_h = max(1.0, height * padding_factor)

    for zoom in range(19, 0, -1):
        x1 = mercator_x(min_lon, zoom)
        x2 = mercator_x(max_lon, zoom)
        y1 = mercator_y(min_lat, zoom)
        y2 = mercator_y(max_lat, zoom)

        dx = abs(x2 - x1)
        dy = abs(y2 - y1)

        if dx <= max_w and dy <= max_h:
            return zoom

    return 1


def project_lonlat_to_pixel(
    lon: float,
    lat: float,
    center_lon: float,
    center_lat: float,
    zoom: int,
    width: int,
    height: int,
) -> tuple[float, float]:
    px = mercator_x(lon, zoom)
    py = mercator_y(lat, zoom)
    cpx = mercator_x(center_lon, zoom)
    cpy = mercator_y(center_lat, zoom)
    return (width / 2.0 + (px - cpx), height / 2.0 + (py - cpy))


def draw_route_overlay(
    image,
    points: list[dict],
    center_lon: float,
    center_lat: float,
    zoom: int,
    width: int,
    height: int,
    line_color: str,
    line_width: int,
) -> None:
    draw = ImageDraw.Draw(image)
    font = ImageFont.load_default()

    projected = [
        project_lonlat_to_pixel(
            lon=p["lon"],
            lat=p["lat"],
            center_lon=center_lon,
            center_lat=center_lat,
            zoom=zoom,
            width=width,
            height=height,
        )
        for p in points
    ]

    if len(projected) >= 2:
        draw.line(projected, fill=line_color, width=line_width, joint="curve")

    marker_radius = 10
    for idx, ((x, y), point) in enumerate(zip(projected, points), start=1):
        if idx == 1:
            fill = "#16a34a"
        elif idx == len(points):
            fill = "#b91c1c"
        else:
            fill = "#1d4ed8"

        draw.ellipse(
            [
                (x - marker_radius, y - marker_radius),
                (x + marker_radius, y + marker_radius),
            ],
            fill=fill,
            outline="white",
            width=2,
        )

        num_text = str(idx)
        bbox = draw.textbbox((0, 0), num_text, font=font)
        tx = x - (bbox[2] - bbox[0]) / 2
        ty = y - (bbox[3] - bbox[1]) / 2
        draw.text((tx, ty), num_text, fill="white", font=font)

        label = f"{idx}. {point['nombre']}"
        lx = int(x + 14)
        ly = int(y - 14)
        lb = draw.textbbox((lx, ly), label, font=font)
        draw.rectangle([lb[0] - 3, lb[1] - 2, lb[2] + 3, lb[3] + 2], fill="white", outline="#d1d5db")
        draw.text((lx, ly), label, fill="#111827", font=font)

    draw.rectangle([12, 12, 370, 80], fill="white", outline="#d1d5db")
    draw.text((22, 22), "Recorrido sugerido Foro Romano + Palatino", fill="#111827", font=font)
    draw.text((22, 42), "1 = inicio | ultimo = fin", fill="#111827", font=font)


def render_route_map(
    points: list[dict],
    output_path: Path,
    width: int,
    height: int,
    padding_factor: float,
    line_color: str,
    line_width: int,
) -> int:
    center_lon, center_lat = route_center(points)
    zoom = fit_zoom(points, width, height, padding_factor=padding_factor)

    m = StaticMap(width, height)
    image = m.render(zoom=zoom, center=(center_lon, center_lat))

    draw_route_overlay(
        image=image,
        points=points,
        center_lon=center_lon,
        center_lat=center_lat,
        zoom=zoom,
        width=width,
        height=height,
        line_color=line_color,
        line_width=line_width,
    )

    output_path.parent.mkdir(parents=True, exist_ok=True)
    image.save(output_path)
    return zoom


def main() -> int:
    args = parse_args()

    input_path = Path(args.input)
    output_main = Path(args.output)
    output_detail = Path(args.detail_output)

    if not input_path.exists():
        print(f"ERROR: input file not found: {input_path}", file=sys.stderr)
        return 1

    try:
        points = load_route_points(input_path)
    except Exception as exc:
        print(f"ERROR loading route JSON: {exc}", file=sys.stderr)
        return 1

    if len(points) < 2:
        print("ERROR: route needs at least two points", file=sys.stderr)
        return 1

    try:
        zoom_main = render_route_map(
            points=points,
            output_path=output_main,
            width=args.width,
            height=args.height,
            padding_factor=args.main_padding,
            line_color=args.line_color,
            line_width=args.line_width,
        )
        print(f"OK main route map: {output_main} (zoom={zoom_main})")

        zoom_detail = render_route_map(
            points=points,
            output_path=output_detail,
            width=args.width,
            height=args.height,
            padding_factor=args.detail_padding,
            line_color=args.line_color,
            line_width=args.line_width,
        )
        print(f"OK detailed route map: {output_detail} (zoom={zoom_detail})")
    except Exception as exc:
        print(f"ERROR generating route maps: {exc}", file=sys.stderr)
        return 1

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
