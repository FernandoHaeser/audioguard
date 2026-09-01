# Arquitetura

## Objetivo

Um serviço que roda por canal (1 processo FFmpeg supervisionado por canal), decide automaticamente se precisa injetar áudio silencioso, e produz HLS pronto para consumo direto por qualquer player — sem depender de flags de manifest, sem depender de comportamento específico de nenhum packetizer downstream fechado.

## Componentes

```
┌─────────────┐     ┌───────────┐     ┌────────────┐     ┌─────────────┐
│ config/*.yml│ ──▶ │ detector  │ ──▶ │ supervisor │ ──▶ │ ffmpeg (N)  │
│ (por canal) │     │ (ffprobe) │     │            │     │ 1 por canal │
└─────────────┘     └───────────┘     └────────────┘     └──────┬──────┘
                                                                  │
                                                          ┌───────▼───────┐
                                                          │ HLS output dir │
                                                          │ (.m3u8 + .ts)  │
                                                          └───────┬───────┘
                                                                  │
                                                          ┌───────▼───────┐
                                                          │ nginx/Caddy   │
                                                          │ (fora do      │
                                                          │  escopo)      │
                                                          └───────────────┘
```

### 1. Config por canal

Um arquivo por canal (ver `examples/channel.yaml`), campos mínimos:

```yaml
id: canal-01
source:
  url: rtsp://origem/canal
  protocol: rtsp   # rtsp | rtmp | srt | hls
output:
  dir: /var/audioguard/canal-01
  segment_type: mpegts   # mpegts | fmp4 (default: mpegts, ver README "Ponto em aberto")
  hls_time: 4
  hls_list_size: 6
audio:
  mode: auto   # auto | force-passthrough | force-silent
  silent_bitrate_kbps: 32
```

`audio.mode: auto` é o default — o detector decide. `force-silent` existe para o caso em que a origem tem áudio, mas ele é inutilizável (ex.: canal de idioma com faixa corrompida) e você quer forçar silêncio mesmo assim.

### 2. Detector

Roda uma vez por start de canal (e de novo a cada restart do supervisor, já que a origem pode ter mudado):

```bash
ffprobe -v error -show_streams -select_streams a -of json "$SOURCE_URL"
```

- Stream de áudio presente e decodificável → Caso 1 (passthrough).
- Nenhum stream de áudio, ou `ffprobe` falha em decodificar → Caso 2 (silêncio sintético).
- Timeout de `ffprobe` (ex.: 5s) — trata como "sem áudio", loga warning, segue para Caso 2. Nunca trava a subida do canal esperando a origem responder.

### 3. Supervisor

Responsabilidades:

- Monta o comando FFmpeg (Caso 1 ou 2, conforme detector) e sobe como subprocesso.
- Monitora saída de stderr do FFmpeg para detectar erros recorrentes (ex.: reconexão constante, `Non-monotonous DTS` em excesso) e loga estruturado.
- Se o processo morre, reinicia com backoff exponencial (1s, 2s, 4s, ... até um teto, ex. 30s) — nunca em loop apertado.
- Expõe estado por canal (rodando / reiniciando / erro) via um endpoint simples (HTTP local) ou arquivo de status — a decidir na implementação.

Pode ser implementado como script Python/Node com `subprocess`, ou delegado a `systemd` (uma unit template `audioguard@canal.service`) + um gerador de units a partir dos YAMLs. A segunda opção reaproveita todo o restart/backoff/logging que o systemd já garante e evita reimplementar um supervisor do zero — abordagem preferida para v1.

### 4. Saída

`audioguard` só escreve `.m3u8` + segmentos `.ts` (ou `.m4s`, se `segment_type: fmp4`) em disco. Servir isso via HTTP é responsabilidade de outra camada (nginx, Caddy) — fora do escopo deste projeto, documentado apenas como exemplo de config de referência em `examples/nginx.conf` (a fazer).

## Decisões de design e porquês

- **Sem relay RTSP intermediário por padrão.** FFmpeg consome a maioria dos protocolos de origem nativamente. Um hop a mais é: mais latência, mais ponto de falha, possível perda de qualidade se reencodar no meio. Só se justifica se a origem expuser um protocolo que o FFmpeg não suporta diretamente.
- **`-c:v copy` sempre que possível.** Vídeo nunca é reencodado a menos que a origem exija (ex.: codec incompatível com o segmentador de saída). Preserva qualidade e mantém CPU baixa.
- **Áudio silencioso é o único componente realmente sintetizado.** Custo de CPU desprezível (`anullsrc` + AAC em bitrate baixo, ~32kbps).
- **Detecção automática, não configuração manual por canal.** Menos operação manual = menos erro humano quando a origem muda de estado (canal que tinha áudio e perdeu, por exemplo).
- **1 processo por canal, sem multiplexação de canais num único FFmpeg.** Isolamento de falha: um canal com origem instável não deve afetar os outros.

## Não resolvido / a validar

- **TS vs fMP4 para Roku.** Ver README, seção "Ponto em aberto". Precisa de teste real em hardware Roku antes de fixar o default.
- **SRT.** Depende do binário FFmpeg ter sido compilado com `--enable-libsrt`. Documentar como pré-requisito de build/instalação, não assumir presente.
- **Múltiplas faixas de áudio / idiomas.** Fora do escopo inicial — v1 assume 1 faixa de áudio por canal (real ou silenciosa). Multi-áudio fica para uma v2 se houver demanda.
