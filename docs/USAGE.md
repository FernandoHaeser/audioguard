# Uso

## Instalação (binário pronto)

Alvo de compatibilidade: **Ubuntu 20.04+** (glibc 2.31+). O build no CI roda dentro de um container `ubuntu:20.04` de propósito — glibc é forward-compatible mas não backward-compatible, então buildar num Ubuntu mais novo geraria um binário que falha com `GLIBC_X.XX not found` em produção. Por isso `requires-python = ">=3.8"` no `pyproject.toml`: é o Python que o `apt` do 20.04 fornece nativamente.

Cada tag `vX.Y.Z` gera automaticamente (`.github/workflows/release.yml`) um `audioguard-linux-x86_64.tar.gz` anexado à release no GitHub, contendo:

```
audioguard-linux-x86_64/
├── audioguard      # binário standalone (PyInstaller, sem dependência de Python instalado)
├── LICENSE
├── README.md
└── examples/
```

```bash
tar xzf audioguard-linux-x86_64.tar.gz
cd audioguard-linux-x86_64
./audioguard run examples/channel.yaml
```

O binário **não** embute `ffmpeg`/`ffprobe`, mas sabe instalar sozinho em sistemas Debian/Ubuntu:

```bash
sudo ./audioguard install-ffmpeg
```

Isso roda `apt-get update && apt-get install -y ffmpeg` — só executa com `sudo`/root explícito, nunca automaticamente dentro de `run`/`run-dir` (esses comandos só avisam no stderr se `ffmpeg`/`ffprobe` estiverem ausentes, sem instalar nada sozinhos). Em sistemas sem `apt-get` (macOS, Fedora, Arch, ...), o comando falha com instrução manual (`brew install ffmpeg`, `dnf install ffmpeg`, etc.).

Pra gerar o binário localmente (mesmo script usado pelo CI):

```bash
./scripts/build_binary.sh
# gera dist/audioguard-<os>-<arch>.tar.gz
```

## Instalação (dev)

```bash
git clone <repo> audioguard && cd audioguard
python3 -m venv .venv
.venv/bin/pip install -e .
```

Requer `ffmpeg`/`ffprobe` no `PATH` do sistema (não é dependência Python — é binário externo).

## Rodar um canal

```bash
audioguard run examples/channel.yaml
```

Roda em foreground, loga em stdout, `Ctrl+C` encerra. Útil pra debug/teste manual de um canal isolado.

## Rodar todos os canais de um diretório

```bash
audioguard run-dir /etc/audioguard/channels/
```

Sobe uma thread supervisora por arquivo `*.yaml`/`*.yml` encontrado no diretório. Cada canal roda seu próprio processo `ffmpeg` isolado — a queda de um não afeta os outros.

## Config de canal

Ver [`examples/channel.yaml`](../examples/channel.yaml) comentado, e a referência de campos em [`docs/ARCHITECTURE.md`](ARCHITECTURE.md#1-config-por-canal).

Resumo rápido:

| Campo | Obrigatório | Default | Descrição |
|---|---|---|---|
| `id` | sim | — | identificador do canal (usado em logs) |
| `source.url` | sim | — | URL da origem |
| `source.protocol` | sim | — | `rtsp` (único suportado hoje — ver [`docs/SOURCES.md`](SOURCES.md)) |
| `output.dir` | sim | — | diretório onde `.m3u8`/`.ts` são escritos |
| `output.segment_type` | não | `mpegts` | `mpegts` ou `fmp4` |
| `output.hls_time` | não | `4` | duração do segmento em segundos |
| `output.hls_list_size` | não | `6` | quantos segmentos ficam na playlist |
| `audio.mode` | não | `auto` | `auto` \| `force-passthrough` \| `force-silent` |
| `audio.silent_bitrate_kbps` | não | `32` | bitrate do AAC sintético quando em modo silencioso |
| `detector.probe_timeout_s` | não | `5.0` | timeout do `ffprobe` de detecção |

## Rodar em produção (systemd)

Não incluso ainda como template pronto — planejado (ver `docs/ARCHITECTURE.md`, seção Supervisor). Enquanto isso, `audioguard run-dir` sob uma unit `simple` de systemd com `Restart=always` já cobre o caso básico:

```ini
[Unit]
Description=audioguard - garante audio nos canais HLS
After=network.target

[Service]
ExecStart=/opt/audioguard/.venv/bin/audioguard run-dir /etc/audioguard/channels/
Restart=always
RestartSec=3

[Install]
WantedBy=multi-user.target
```

## Rodar os testes

```bash
.venv/bin/pip install -e . pytest
.venv/bin/python -m pytest -q
```
