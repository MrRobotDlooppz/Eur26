# Generador de mapas con pin

Genera dos imagenes PNG por lugar sobre mapa real de OpenStreetMap:

- mapa general (contexto de la ciudad)
- mapa detalle (zoom cercano de calles y zona inmediata)

Tambien permite agregar pines de referencia cercanos y puntos principales de ciudad para dar contexto espacial.

## Generador de mapa de recorrido

Tambien hay un script para generar un mapa de recorrido completo con:

- linea de ruta
- paradas numeradas en orden
- mapa general y mapa detalle del mismo recorrido

Script: `tools/maps/generate_route_map.py`

Input esperado: lista ordenada de objetos con `nombre`, `lat`, `lon` y opcional `orden`.

Ejemplo: `tools/maps/foro_palatino_route.json`

## Requisitos

- Python 3
- Dependencia: `staticmap`

Instalacion:

```bash
pip install staticmap
```

## Input

Archivo JSON (ver `tools/maps/roma_places.json`) con objetos:

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
  --input tools/maps/roma_places.json \
  --output ciudades/Roma/fotos
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

Despues de generar una imagen, agregar en `ciudades/Roma/roma.md` dentro del lugar:

```md
**Mapa del lugar**
![Mapa con pin de <NOMBRE>](fotos/<archivo>.png)

**Mapa en detalle**
![Mapa detallado de <NOMBRE>](fotos/<archivo>_detalle.png)
```

Para recorridos:

```md
**Mapa de recorrido**
![Mapa del recorrido](fotos/mapa_recorrido_<lugar>.png)

**Mapa de recorrido en detalle**
![Mapa detallado del recorrido](fotos/mapa_recorrido_<lugar>_detalle.png)
```
