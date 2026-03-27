#!/usr/bin/env python3
"""Export an ordered JSON route into GPX format.

Usage:
  python tools/maps/export_route_gpx.py \
    --input tools/maps/foro_palatino_route.json \
    --output Rome/fotos/foro_romano_palatino/recorrido_foro_palatino.gpx \
    --name "Recorrido Foro Romano y Palatino"
"""

import argparse
import json
import sys
import xml.etree.ElementTree as ET
from pathlib import Path


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Export route JSON to GPX")
    parser.add_argument("--input", required=True, help="Input JSON route file")
    parser.add_argument("--output", required=True, help="Output GPX file")
    parser.add_argument("--name", default="Recorrido", help="Route name")
    return parser.parse_args()


def load_points(path: Path) -> list[dict]:
    with path.open("r", encoding="utf-8") as f:
        data = json.load(f)

    if not isinstance(data, list):
        raise ValueError("Input JSON must be a list")

    points = []
    for idx, item in enumerate(data, start=1):
        if not isinstance(item, dict):
            raise ValueError(f"Point #{idx} is not an object")

        missing = {"nombre", "lat", "lon"} - set(item.keys())
        if missing:
            raise ValueError(f"Point #{idx} missing keys: {', '.join(sorted(missing))}")

        try:
            lat = float(item["lat"])
            lon = float(item["lon"])
        except (TypeError, ValueError):
            raise ValueError(f"Point #{idx} has invalid coordinates")

        orden = item.get("orden", idx)
        try:
            orden = int(orden)
        except (TypeError, ValueError):
            orden = idx

        points.append(
            {
                "orden": orden,
                "nombre": str(item["nombre"]),
                "lat": lat,
                "lon": lon,
            }
        )

    points.sort(key=lambda p: p["orden"])
    if len(points) < 2:
        raise ValueError("At least two points are required")

    return points


def write_gpx(points: list[dict], output_path: Path, route_name: str) -> None:
    gpx = ET.Element(
        "gpx",
        {
            "version": "1.1",
            "creator": "Eur26 route exporter",
            "xmlns": "http://www.topografix.com/GPX/1/1",
        },
    )

    metadata = ET.SubElement(gpx, "metadata")
    ET.SubElement(metadata, "name").text = route_name

    rte = ET.SubElement(gpx, "rte")
    ET.SubElement(rte, "name").text = route_name

    for idx, p in enumerate(points, start=1):
        rtept = ET.SubElement(
            rte,
            "rtept",
            {"lat": f"{p['lat']:.7f}", "lon": f"{p['lon']:.7f}"},
        )
        ET.SubElement(rtept, "name").text = f"{idx}. {p['nombre']}"

    trk = ET.SubElement(gpx, "trk")
    ET.SubElement(trk, "name").text = route_name
    seg = ET.SubElement(trk, "trkseg")

    for p in points:
        ET.SubElement(seg, "trkpt", {"lat": f"{p['lat']:.7f}", "lon": f"{p['lon']:.7f}"})

    output_path.parent.mkdir(parents=True, exist_ok=True)
    tree = ET.ElementTree(gpx)
    tree.write(output_path, encoding="utf-8", xml_declaration=True)


def main() -> int:
    args = parse_args()
    in_path = Path(args.input)
    out_path = Path(args.output)

    if not in_path.exists():
        print(f"ERROR: input file not found: {in_path}", file=sys.stderr)
        return 1

    try:
        points = load_points(in_path)
        write_gpx(points, out_path, args.name)
    except Exception as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1

    print(f"OK GPX exported: {out_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
