#!/usr/bin/env bash
# =============================================================================
# serve.sh — Genera todo y levanta el server con link público
#
# Uso:
#   ./tools/audio/serve.sh              # genera todo + sirve
#   ./tools/audio/serve.sh --skip-build # solo sirve (si ya generaste)
#   ./tools/audio/serve.sh --force      # regenera todo desde cero + sirve
# =============================================================================
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
PORT=8080
SKIP_BUILD=false
BUILD_ARGS=""

cd "$REPO_ROOT"

# Colores
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
BOLD='\033[1m'
NC='\033[0m'

# --- Parsear args ---
for arg in "$@"; do
    case "$arg" in
        --skip-build|-s) SKIP_BUILD=true ;;
        --port=*)        PORT="${arg#*=}" ;;
        *)               BUILD_ARGS="$BUILD_ARGS $arg" ;;
    esac
done

# --- 1. Build (a menos que --skip-build) ---
if [[ "$SKIP_BUILD" == false ]]; then
    echo -e "${GREEN}${BOLD}=== Generando audio y player ===${NC}"
    echo ""
    bash "$SCRIPT_DIR/build_audio_site.sh" $BUILD_ARGS
else
    echo -e "${YELLOW}Saltando build (--skip-build)${NC}"
    if [[ ! -f "docs/index.html" ]]; then
        echo -e "${RED}Error: docs/index.html no existe. Corré sin --skip-build primero.${NC}"
        exit 1
    fi
fi

# --- 2. Matar servidor previo en el mismo puerto ---
if lsof -ti :"$PORT" &>/dev/null; then
    echo -e "${YELLOW}Matando servidor previo en puerto $PORT...${NC}"
    kill $(lsof -ti :"$PORT") 2>/dev/null || true
    sleep 1
fi

# --- 3. Detectar entorno (Codespaces vs local) ---
echo ""
echo -e "${GREEN}${BOLD}=== Levantando servidor ===${NC}"
echo ""

if [[ -n "${CODESPACE_NAME:-}" ]]; then
    # Codespaces: hacer el puerto público
    echo -e "${YELLOW}Detectado GitHub Codespaces${NC}"
    echo -e "${YELLOW}Haciendo puerto $PORT público...${NC}"
    gh codespace ports visibility "$PORT:public" -c "$CODESPACE_NAME" 2>/dev/null || true

    PUBLIC_URL="https://${CODESPACE_NAME}-${PORT}.app.github.dev"

    echo ""
    echo -e "${GREEN}${BOLD}════════════════════════════════════════════════════${NC}"
    echo ""
    echo -e "  ${BOLD}🎧 Player listo!${NC}"
    echo ""
    echo -e "  ${CYAN}${BOLD}$PUBLIC_URL${NC}"
    echo ""
    echo -e "  Mandá ese link por WhatsApp."
    echo -e "  Solo tiene que abrirlo, tocar play y ponerse los auris."
    echo ""
    echo -e "${GREEN}${BOLD}════════════════════════════════════════════════════${NC}"
    echo ""
    echo -e "  ${YELLOW}Ctrl+C para parar el servidor${NC}"
    echo ""
else
    echo -e "${GREEN}${BOLD}════════════════════════════════════════════════════${NC}"
    echo ""
    echo -e "  ${BOLD}🎧 Player listo!${NC}"
    echo ""
    echo -e "  Local:  ${CYAN}${BOLD}http://localhost:$PORT${NC}"
    echo ""
    echo -e "  Para acceso remoto (GitHub Pages):"
    echo -e "    git add docs/ && git commit -m 'audio' && git push"
    echo -e "    Luego: Settings → Pages → main → /docs"
    echo ""
    echo -e "${GREEN}${BOLD}════════════════════════════════════════════════════${NC}"
    echo ""
    echo -e "  ${YELLOW}Ctrl+C para parar el servidor${NC}"
    echo ""
fi

# --- 4. Servir ---
cd docs
exec python3 -m http.server "$PORT" --bind 0.0.0.0
