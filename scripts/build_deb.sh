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

# Relay RTSP (MediaMTX, MIT) bundlado - suporta output.mode: publish sem
# depender de infra externa. Baixa a release mais recente pra linux_amd64.
#
# Nao encadear o curl direto num pipe com grep -m1/head -n1: essas ferramentas
# fecham o pipe assim que acham a 1a ocorrencia, o curl leva broken pipe
# tentando escrever o resto do corpo e sai com erro 23 - com `set -o
# pipefail` isso aborta o script inteiro antes mesmo do download real
# acontecer. Captura a resposta inteira numa variavel primeiro, so entao
# processa (grep/sed rodando sobre uma string em memoria, sem pipe pro curl).
if [ -z "${MEDIAMTX_VERSION:-}" ]; then
  MEDIAMTX_RELEASE_JSON="$(curl -fsSL https://api.github.com/repos/bluenviron/mediamtx/releases/latest)"
  MEDIAMTX_VERSION="$(printf '%s' "$MEDIAMTX_RELEASE_JSON" | sed -n 's/.*"tag_name": *"v\([^"]*\)".*/\1/p')"
fi
if [ -z "$MEDIAMTX_VERSION" ]; then
  echo "nao consegui resolver a versao do mediamtx (rate limit da API do github?) - defina MEDIAMTX_VERSION manualmente" >&2
  exit 1
fi
echo "bundlando mediamtx v${MEDIAMTX_VERSION}"
curl -fsSL -o /tmp/mediamtx.tar.gz \
  "https://github.com/bluenviron/mediamtx/releases/download/v${MEDIAMTX_VERSION}/mediamtx_v${MEDIAMTX_VERSION}_linux_amd64.tar.gz"
mkdir -p /tmp/mediamtx_extract
tar xzf /tmp/mediamtx.tar.gz -C /tmp/mediamtx_extract

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

cp /tmp/mediamtx_extract/mediamtx "$ROOT/usr/local/bin/audioguard-relay"
chmod 755 "$ROOT/usr/local/bin/audioguard-relay"
cp packaging/relay.yml "$ROOT/etc/audioguard/relay.yml"
[ -f /tmp/mediamtx_extract/LICENSE ] && cp /tmp/mediamtx_extract/LICENSE "$ROOT/usr/share/doc/audioguard/LICENSE.mediamtx"

cp packaging/audioguard.service "$ROOT/etc/systemd/system/audioguard.service"
cp packaging/audioguard-relay.service "$ROOT/etc/systemd/system/audioguard-relay.service"
cp examples/channel.yaml "$ROOT/usr/share/doc/audioguard/examples/channel.yaml"
cp README.md LICENSE "$ROOT/usr/share/doc/audioguard/"

sed "s/__VERSION__/${VERSION}/" packaging/control.template > "$ROOT/DEBIAN/control"

cp packaging/postinst "$ROOT/DEBIAN/postinst"
cp packaging/prerm "$ROOT/DEBIAN/prerm"
chmod 755 "$ROOT/DEBIAN/postinst" "$ROOT/DEBIAN/prerm"

dpkg-deb --build --root-owner-group "$ROOT" "dist/${PKG_NAME}.deb"

echo "gerado: dist/${PKG_NAME}.deb"
