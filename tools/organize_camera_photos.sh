#!/bin/bash
# Script idempotente para asegurar que existen todas las carpetas de fotos
# para cada lugar registrado en el repositorio.
# Ejecutar desde la raíz del repositorio: bash tools/organize_camera_photos.sh
#
# Uso:
#   bash tools/organize_camera_photos.sh          → crea carpetas faltantes
#   bash tools/organize_camera_photos.sh --status  → solo muestra estado actual

set -e
cd "$(dirname "$0")/.."

FOTOS="Rome/fotos"

# ─── Lista canónica de carpetas de fotos (una por lugar o grupo) ───
# Actualizar esta lista cada vez que se agregue un lugar nuevo.
LUGARES=(
    colosseo
    fontana_di_trevi
    foro_di_traiano
    iglesias
    musei_vaticani
    pantheon
    piazza_del_popolo
    piazza_navona
    santa_maria_maggiore
    vittorio_emanuele_ii
    termas_di_caracalla
    termas_di_traiano
    san_giovanni_laterano
    palazzo_barberini
    palazzo_colonna
    largo_torre_argentina
    quartiere_coppede
)

# ─── Modo status ───
if [[ "${1:-}" == "--status" ]]; then
    echo "=== Estado actual de carpetas de fotos ==="
    for lugar in "${LUGARES[@]}"; do
        dir="$FOTOS/$lugar"
        if [[ -d "$dir" ]]; then
            count=$(find "$dir" -maxdepth 1 -type f \( -name "*.jpeg" -o -name "*.jpg" -o -name "*.png" -o -name "*.heic" \) 2>/dev/null | wc -l)
            echo "  ✓ $lugar/: $count archivo(s)"
        else
            echo "  ✗ $lugar/: NO EXISTE"
        fi
    done
    exit 0
fi

# ─── Crear carpetas faltantes ───
echo "=== Asegurando carpetas de fotos ==="
created=0
for lugar in "${LUGARES[@]}"; do
    dir="$FOTOS/$lugar"
    if [[ ! -d "$dir" ]]; then
        mkdir -p "$dir"
        echo "  + Creada: $lugar/"
        ((created++))
    fi
done

if [[ $created -eq 0 ]]; then
    echo "  Todas las carpetas ya existen."
else
    echo "  $created carpeta(s) creada(s)."
fi

echo ""
echo "=== Resumen de fotos ==="
for lugar in "${LUGARES[@]}"; do
    dir="$FOTOS/$lugar"
    count=$(find "$dir" -maxdepth 1 -type f \( -name "*.jpeg" -o -name "*.jpg" -o -name "*.png" -o -name "*.heic" \) 2>/dev/null | wc -l)
    echo "  $lugar/: $count archivo(s)"
done

echo ""
echo "✅ Listo"
