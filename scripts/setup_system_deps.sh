#!/usr/bin/env bash
set -e

echo "==========================================="
echo "  Igris System Dependencies Setup (Linux)  "
echo "==========================================="

if command -v apt-get &> /dev/null; then
    echo "[+] Updating apt package lists..."
    sudo apt-get update -y

    echo "[+] Installing core OS automation packages..."
    sudo apt-get install -y \
        xvfb \
        xdotool \
        imagemagick \
        ffmpeg \
        at-spi2-core \
        gir1.2-atspi-2.0 \
        python3-pip \
        python3-venv

    echo "[✓] System packages installed successfully."
else
    echo "[!] Non-Debian/Ubuntu system detected. Please install manually: xvfb, xdotool, imagemagick, ffmpeg, at-spi2-core."
fi
