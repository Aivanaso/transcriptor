#!/usr/bin/env bash
# Instalador completo de Transcriptor para Ubuntu/Debian.
set -euo pipefail

PROJECT_DIR="$(cd "$(dirname "$0")" && pwd)"
VENV_DIR="$PROJECT_DIR/venv"
DESKTOP_FILE="$HOME/.local/share/applications/transcriptor.desktop"

echo "==> [1/4] Instalando dependencias del sistema..."
sudo apt install -y \
    python3-pip python3-venv \
    libportaudio2 portaudio19-dev \
    xdotool xclip \
    libcairo2-dev pkg-config python3-dev \
    libgirepository-2.0-dev libgirepository1.0-dev gir1.2-gtk-3.0 \
    gir1.2-appindicator3-0.1 gir1.2-ayatanaappindicator3-0.1 \
    libnotify-bin

echo ""
echo "==> [2/4] Creando entorno virtual..."
python3 -m venv "$VENV_DIR"

echo ""
echo "==> [3/4] Instalando Transcriptor..."
"$VENV_DIR/bin/pip" install --upgrade pip -q
"$VENV_DIR/bin/pip" install -e "$PROJECT_DIR"

echo ""
echo "==> [4/4] Añadiendo al menú de aplicaciones..."
mkdir -p "$(dirname "$DESKTOP_FILE")"
cat > "$DESKTOP_FILE" <<EOF
[Desktop Entry]
Name=Transcriptor
Comment=Transcripción de voz a texto con IA local
Exec=$VENV_DIR/bin/transcriptor
Icon=$PROJECT_DIR/transcriptor/assets/icon_idle.png
Type=Application
Categories=Utility;Audio;
Keywords=voice;speech;whisper;transcription;
EOF
update-desktop-database "$HOME/.local/share/applications" 2>/dev/null || true

echo ""
echo "========================================="
echo "  Transcriptor instalado correctamente"
echo "========================================="
echo ""
echo "  Puedes ejecutarlo de dos formas:"
echo ""
echo "  1. Desde el menú de aplicaciones (busca 'Transcriptor')"
echo "  2. Desde terminal:  $VENV_DIR/bin/transcriptor"
echo ""
echo "  La primera ejecución descargará el modelo de Whisper (~461 MB)."
echo ""
