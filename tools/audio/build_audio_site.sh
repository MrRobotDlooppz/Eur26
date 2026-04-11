#!/usr/bin/env bash
# =============================================================================
# build_audio_site.sh — Pipeline completo: .md → MP3 → Player web
#
# Uso:
#   ./tools/audio/build_audio_site.sh                  # todo el repo
#   ./tools/audio/build_audio_site.sh Firenze/         # solo una ciudad
#   ./tools/audio/build_audio_site.sh --force           # regenerar todo
#   ./tools/audio/build_audio_site.sh --voice es-AR-ElenaNeural
# =============================================================================
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"

cd "$REPO_ROOT"

# Colores
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo -e "${GREEN}=== Archivo de Viajes — Audio Pipeline ===${NC}"
echo ""

# --- 1. Activar venv ---
if [[ -d ".venv" ]]; then
    echo -e "${YELLOW}Activando entorno virtual...${NC}"
    source .venv/bin/activate
else
    echo -e "${RED}No se encontró .venv/ — creando uno...${NC}"
    python3 -m venv .venv
    source .venv/bin/activate
fi

# --- 2. Instalar dependencias ---
echo -e "${YELLOW}Verificando dependencias...${NC}"
pip install -q edge-tts mutagen 2>/dev/null || {
    echo -e "${RED}Error instalando dependencias. Ejecutá manualmente:${NC}"
    echo "  pip install edge-tts mutagen"
    exit 1
}
echo "  ✓ edge-tts y mutagen instalados"

# --- 3. Parsear argumentos ---
INPUT_ARGS=""
EXTRA_ARGS=""

for arg in "$@"; do
    case "$arg" in
        --force|-f)
            EXTRA_ARGS="$EXTRA_ARGS --force"
            ;;
        --voice)
            # Next arg is the voice name, handled by shift below
            EXTRA_ARGS="$EXTRA_ARGS --voice"
            ;;
        --voice=*)
            EXTRA_ARGS="$EXTRA_ARGS $arg"
            ;;
        --rate=*)
            EXTRA_ARGS="$EXTRA_ARGS $arg"
            ;;
        *)
            # Si es una ruta, usarla como input
            if [[ -e "$arg" ]] || [[ "$arg" == *.md ]]; then
                INPUT_ARGS="--input $arg"
            else
                # Podría ser valor de --voice
                EXTRA_ARGS="$EXTRA_ARGS $arg"
            fi
            ;;
    esac
done

# Default input: todo el repo
if [[ -z "$INPUT_ARGS" ]]; then
    INPUT_ARGS="--input ."
fi

# --- 4. Generar MP3 ---
echo ""
echo -e "${GREEN}=== Paso 1/2: Generando audio (MD → MP3) ===${NC}"
echo ""
python tools/audio/generate_audio.py $INPUT_ARGS --output docs/audio $EXTRA_ARGS

# --- 5. Generar player HTML ---
echo ""
echo -e "${GREEN}=== Paso 2/2: Generando player web ===${NC}"
echo ""
python tools/audio/generate_player.py --audio-dir docs/audio --output docs/index.html

# --- 6. Asegurar .nojekyll ---
touch docs/.nojekyll

# --- Resumen ---
echo ""
echo -e "${GREEN}=== Pipeline completado ===${NC}"
echo ""

# Contar archivos generados
MP3_COUNT=$(find docs/audio -name "*.mp3" 2>/dev/null | wc -l)
TOTAL_SIZE=$(du -sh docs/audio 2>/dev/null | cut -f1 || echo "0")

echo "  📁 MP3 generados: $MP3_COUNT"
echo "  💾 Tamaño total: $TOTAL_SIZE"
echo "  🌐 Player: docs/index.html"
echo ""
echo -e "${YELLOW}Para probar localmente:${NC}"
echo "  cd docs && python3 -m http.server 8080"
echo ""
echo -e "${YELLOW}Para publicar en GitHub Pages:${NC}"
echo "  1. git add docs/"
echo "  2. git commit -m 'Generar audio guides'"
echo "  3. git push"
echo "  4. Settings → Pages → Source: main, folder: /docs"
echo ""
