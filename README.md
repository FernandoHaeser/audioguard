# audioguard

Serviço open-source, single-purpose: recebe um stream de entrada, garante que a saída sempre tenha uma faixa de áudio válida — real, quando existe na origem, ou silenciosa sintética, quando não existe — e entrega HLS pronto para qualquer player, incluindo Roku.

Protocolo de origem suportado hoje: **RTSP**. Arquitetura pensada desde o início pra outros protocolos (RTMP, SRT, HLS) entrarem sem mexer no resto do sistema — ver [`docs/SOURCES.md`](docs/SOURCES.md).

## O problema

Vários players de TV/streaming (a spec da Roku é explícita nisso) assumem que todo stream de vídeo carrega uma faixa AAC estéreo. Quando a origem é vídeo puro (câmera sem microfone, rádio recodificado, feed institucional), o player trava, não inicia, ou simplesmente não mostra a mídia — mesmo sem nenhum erro visível no manifest.

A causa raiz não é o manifest (`#EXT-X-STREAM-INF` sem `AUDIO="..."`) — é a ausência real de um PID de áudio decodificável no stream. Não existe fix de metadado para isso: precisa haver, de fato, uma faixa de áudio codificada saindo do processo, mesmo que o conteúdo dela seja silêncio.

## Ideia central

Um processo FFmpeg por canal, sem hops desnecessários no meio (nada de RTSP relay intermediário se a origem já fala um protocolo que o FFmpeg consome nativamente).

```
[origem: RTSP/RTMP/SRT/HLS] --ffmpeg--> [garante áudio + remux] --ffmpeg hls muxer--> [HLS de saída, .ts]
```

### Caso 1 — origem já tem áudio

```bash
ffmpeg -i "rtsp://origem/canal" \
  -c:v copy -c:a copy \
  -f hls -hls_time 4 -hls_list_size 6 \
  -hls_segment_type mpegts \
  -hls_flags delete_segments+independent_segments \
  /saida/canal/index.m3u8
```

`-c:v copy` e `-c:a copy`: sem reencode, nem de vídeo nem de áudio — zero perda em relação à origem, CPU baixíssima. Só remuxa.

### Caso 2 — origem só tem vídeo

```bash
ffmpeg -i "rtsp://origem/canal" \
  -f lavfi -i anullsrc=channel_layout=stereo:sample_rate=48000 \
  -map 0:v -map 1:a \
  -c:v copy -c:a aac -b:a 32k -shortest \
  -f hls -hls_time 4 -hls_list_size 6 \
  -hls_segment_type mpegts \
  -hls_flags delete_segments+independent_segments \
  /saida/canal/index.m3u8
```

Vídeo continua em `copy` (zero perda). Só o áudio silencioso é codificado — custo de CPU desprezível (poucos kbps, sinal constante zero).

`audioguard` decide sozinho qual dos dois casos aplicar, rodando `ffprobe` na origem antes de subir o processo — sem configuração manual por canal.

## Uso rápido

**Binário pronto (recomendado):** baixe `audioguard-linux-x86_64.tar.gz` da [página de releases](../../releases), extraia e execute — sem Python, sem `pip install`.

```bash
tar xzf audioguard-linux-x86_64.tar.gz
cd audioguard-linux-x86_64
./audioguard run examples/channel.yaml
```

Requer apenas `ffmpeg`/`ffprobe` instalados no sistema (não vêm embutidos no binário — são dependência externa, não redistribuída por licenciamento/tamanho).

**A partir do código-fonte:**

```bash
python3 -m venv .venv && .venv/bin/pip install -e .
audioguard run examples/channel.yaml
```

Guia completo em [`docs/USAGE.md`](docs/USAGE.md).

## Arquitetura

Ver [`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md) para o desenho completo.

Resumo dos componentes (código em `audioguard/`):

1. **Config por canal** (`config.py`) — YAML com URL de origem, protocolo, path de saída, overrides opcionais.
2. **Fontes** (`sources/`) — uma classe por protocolo, isolando as particularidades de flags do ffmpeg. RTSP implementado (`sources/rtsp.py`); extensão documentada em [`docs/SOURCES.md`](docs/SOURCES.md).
3. **Detector** (`detector.py`) — roda `ffprobe` uma vez ao subir o canal, decide Caso 1 vs Caso 2.
4. **Builder de args** (`ffmpeg_builder.py`) — monta a linha de comando do ffmpeg a partir da fonte + resultado do detector + config de áudio/saída.
5. **Supervisor** (`supervisor.py`) — sobe um processo FFmpeg por canal, monitora, reinicia com backoff exponencial se cair.
6. **CLI** (`cli.py`) — `audioguard run <config>` (um canal) ou `audioguard run-dir <dir>` (todos os canais de um diretório, um por thread).
7. **Saída** — HLS estático (`.m3u8` + `.ts`) servido por qualquer HTTP server (nginx, Caddy) — `audioguard` não serve HTTP, só produz os arquivos.

## Por que não usar um relay RTSP intermediário (ex.: MediaMTX)

FFmpeg consome a maioria dos protocolos de origem nativamente (RTSP, RTMP, HTTP-HLS, SRT se compilado com `--enable-libsrt`) e já entrega HLS de saída num processo só. Cada camada intermediária adicional é: mais latência, mais um ponto de falha, e — se ela reencoda no meio do caminho — perda de qualidade. `audioguard` só introduz um hop RTSP/relay separado se a origem *exigir* isso explicitamente (documentar caso a caso em `docs/CONFIG.md`).

## Ponto em aberto: TS vs fMP4

Um padrão relatado (não confirmado neste projeto ainda) é que Roku tem problemas específicos com HLS em fMP4 quando áudio e vídeo estão muxados no mesmo segmento. Forçar `-hls_segment_type mpegts` na saída pode resolver isso independente de existir áudio real na origem ou não — precisa ser validado empiricamente no hardware alvo antes de virar default definitivo.

## Status

Projeto em fase de design. Este README e `docs/ARCHITECTURE.md` são a espec inicial; implementação ainda não começou.

## Licença

MIT — ver [`LICENSE`](LICENSE).

