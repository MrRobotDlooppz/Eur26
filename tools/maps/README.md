# Generador de mapas con pin

Genera dos imagenes PNG por lugar sobre mapa real de OpenStreetMap:

- mapa general (contexto de la ciudad)
- mapa detalle (zoom cercano de calles y zona inmediata)

Tambien permite agregar pines de referencia cercanos y puntos principales de ciudad para dar contexto espacial.

## Requisitos

- Python 3
- Dependencia: `staticmap`

Instalacion:

```bash
pip install staticmap
```

## Input

Archivo JSON (ver `tools/maps/rome_places.example.json`) con objetos:

- `nombre`
- `archivo`
- `lat`
- `lon`
- `referencias` (opcional): lista de objetos con `nombre`, `lat`, `lon`

Notas:

- El pin principal se dibuja en rojo.
- Las `referencias` del lugar se dibujan en azul.
- Los puntos principales de ciudad se dibujan en gris (por defecto).
- El PNG final incluye etiquetas de texto para el punto principal y para las referencias cercanas.

## Uso

```bash
python tools/maps/generate_static_maps.py \
  --input tools/maps/rome_places.example.json \
  --output Rome/fotos
```

Parametros opcionales:

- `--width` (default `900`)
- `--height` (default `650`)
- `--zoom` (default `14`)
- `--detail-zoom` (default `17`)
- `--detail-suffix` (default `_detalle`)
- `--no-detail-map` (genera solo el mapa general)
- `--marker-color` (default `red`)
- `--marker-size` (default `12`)
- `--no-city-context` (desactiva los puntos principales de ciudad)

## Integracion en notas

Despues de generar una imagen, agregar en `Rome/Lugares.md` dentro del lugar:

```md
**Mapa del lugar**
![Mapa con pin de <NOMBRE>](fotos/<archivo>.png)

**Mapa en detalle**
![Mapa detallado de <NOMBRE>](fotos/<archivo>_detalle.png)
```
