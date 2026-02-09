#!/usr/bin/env bash
# Desinstalador de Transcriptor.
set -euo pipefail

PROJECT_DIR="$(cd "$(dirname "$0")" && pwd)"
DESKTOP_FILE="$HOME/.local/share/applications/transcriptor.desktop"

echo "==> Desinstalando Transcriptor..."

if [ -f "$DESKTOP_FILE" ]; then
    rm "$DESKTOP_FILE"
    update-desktop-database "$HOME/.local/share/applications" 2>/dev/null || true
    echo "  - Eliminado del menú de aplicaciones"
fi

if [ -d "$PROJECT_DIR/venv" ]; then
    rm -rf "$PROJECT_DIR/venv"
    echo "  - Eliminado entorno virtual"
fi

if [ -d "$PROJECT_DIR/__pycache__" ]; then
    rm -rf "$PROJECT_DIR/__pycache__"
fi

if [ -d "$PROJECT_DIR/transcriptor.egg-info" ]; then
    rm -rf "$PROJECT_DIR/transcriptor.egg-info"
fi

find "$PROJECT_DIR/transcriptor" -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true

echo ""
echo "  Transcriptor desinstalado."
echo ""
echo "  La configuración se ha mantenido en:"
echo "    ~/.config/transcriptor/config.json"
echo ""
echo "  Los modelos descargados están en:"
echo "    ~/.cache/huggingface/hub/"
echo ""
echo "  Para eliminarlos también:"
echo "    rm -rf ~/.config/transcriptor"
echo "    rm -rf ~/.cache/huggingface/hub/models--Systran--faster-whisper-*"
echo ""
