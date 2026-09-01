#!/usr/bin/env bash
# Gera o binario standalone (audioguard) via PyInstaller e empacota em tar.gz.
# Uso local: ./scripts/build_binary.sh [nome-do-pacote-sem-extensao]
# Usado pelo workflow .github/workflows/release.yml no CI.
set -euo pipefail

cd "$(dirname "$0")/.."

PKG_NAME="${1:-audioguard-$(uname -s | tr '[:upper:]' '[:lower:]')-$(uname -m)}"

python3 -m venv .build-venv
. .build-venv/bin/activate
pip install -q --upgrade pip
pip install -q -e ".[dev]"

pyinstaller --onefile --name audioguard --distpath dist entrypoint.py

mkdir -p "dist/${PKG_NAME}"
cp dist/audioguard "dist/${PKG_NAME}/"
cp README.md LICENSE "dist/${PKG_NAME}/"
cp -r examples "dist/${PKG_NAME}/"

tar -C dist -czf "dist/${PKG_NAME}.tar.gz" "${PKG_NAME}"

echo "gerado: dist/${PKG_NAME}.tar.gz"
