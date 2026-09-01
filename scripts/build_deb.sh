#!/usr/bin/env bash
# Gera um .deb do audioguard a partir do binario ja compilado em dist/audioguard.
# Uso: ./scripts/build_deb.sh <versao> [nome-do-pacote-sem-extensao]
# Pressupoe que ./scripts/build_binary.sh (ou equivalente) ja rodou e deixou
# dist/audioguard (binario standalone) pronto - este script so empacota.
set -euo pipefail

cd "$(dirname "$0")/.."

VERSION="${1:?uso: build_deb.sh <versao> [nome-do-pacote]}"
PKG_NAME="${2:-audioguard_${VERSION}_amd64}"

if [ ! -f dist/audioguard ]; then
  echo "dist/audioguard nao encontrado - rode scripts/build_binary.sh primeiro" >&2
  exit 1
fi

if ! command -v dpkg-deb >/dev/null; then
  echo "dpkg-deb nao encontrado - este script precisa rodar em Debian/Ubuntu" >&2
  exit 1
fi

ROOT="dist/deb/${PKG_NAME}"
rm -rf "$ROOT"
mkdir -p \
  "$ROOT/DEBIAN" \
  "$ROOT/usr/local/bin" \
  "$ROOT/etc/systemd/system" \
  "$ROOT/etc/audioguard/channels" \
  "$ROOT/usr/share/doc/audioguard/examples"

cp dist/audioguard "$ROOT/usr/local/bin/audioguard"
chmod 755 "$ROOT/usr/local/bin/audioguard"

cp packaging/audioguard.service "$ROOT/etc/systemd/system/audioguard.service"
cp examples/channel.yaml "$ROOT/usr/share/doc/audioguard/examples/channel.yaml"
cp README.md LICENSE "$ROOT/usr/share/doc/audioguard/"

sed "s/__VERSION__/${VERSION}/" packaging/control.template > "$ROOT/DEBIAN/control"

cp packaging/postinst "$ROOT/DEBIAN/postinst"
cp packaging/prerm "$ROOT/DEBIAN/prerm"
chmod 755 "$ROOT/DEBIAN/postinst" "$ROOT/DEBIAN/prerm"

dpkg-deb --build --root-owner-group "$ROOT" "dist/${PKG_NAME}.deb"

echo "gerado: dist/${PKG_NAME}.deb"
