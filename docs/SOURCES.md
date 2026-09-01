# Adicionando um novo protocolo de origem

O ponto de extensão do projeto é a classe `Source` (`audioguard/sources/base.py`). RTSP é o único protocolo implementado hoje (`audioguard/sources/rtsp.py`), mas o resto do sistema — detector, builder de argumentos do ffmpeg, supervisor, CLI — não sabe nada sobre RTSP especificamente. Eles só conhecem a interface `Source`.

## Interface

```python
class Source(ABC):
    protocol: str = ""  # nome usado em source.protocol no YAML

    def __init__(self, source: ChannelSource): ...

    @abstractmethod
    def input_args(self) -> list[str]:
        """Flags de ffmpeg que antecedem -i <url>, mais o -i <url> em si."""

    @abstractmethod
    def probe_url(self) -> str:
        """URL a passar pro ffprobe do detector."""
```

## Passo a passo pra adicionar RTMP, SRT ou HLS

1. Criar `audioguard/sources/rtmp.py` (ou `srt.py`, `hls.py`):

```python
from .base import Source

class RtmpSource(Source):
    protocol = "rtmp"

    def input_args(self) -> list[str]:
        return ["-i", self.source.url]

    def probe_url(self) -> str:
        return self.source.url
```

2. Registrar em `audioguard/sources/__init__.py`:

```python
from .rtmp import RtmpSource

_REGISTRY = {
    RtspSource.protocol: RtspSource,
    RtmpSource.protocol: RtmpSource,  # <- essa linha
}
```

3. Pronto. `protocol: rtmp` no YAML do canal já funciona — `config.py`, `detector.py`, `ffmpeg_builder.py` e `supervisor.py` não precisam de nenhuma mudança.

## Particularidades por protocolo (referência)

- **RTSP** (implementado) — `-rtsp_transport tcp` (evita UDP em redes com perda/NAT ruim), `-fflags +genpts` (regenera PTS quando a origem manda timestamps quebrados/não-monotônicos — problema comum em câmeras baratas).
- **RTMP** — geralmente não precisa de flags de transporte especiais; `-i url` direto costuma bastar.
- **SRT** — depende do binário `ffmpeg` ter sido compilado com `--enable-libsrt`. Validar com `ffmpeg -protocols 2>&1 | grep srt` antes de assumir suportado. Flags de latência (`?latency=...`) normalmente vão embutidas na própria URL, não como argumento separado.
- **HLS como origem** (relay de outro HLS) — `ffprobe`/`ffmpeg` consomem `.m3u8` nativamente como input; não precisa de tratamento especial na maioria dos casos, mas vale testar com playlists live (`#EXT-X-PLAYLIST-TYPE` ausente) separadamente de VOD.

Nenhuma dessas particularidades deve vazar para fora do arquivo `sources/<protocolo>.py` correspondente — é exatamente esse isolamento que permite adicionar protocolo sem tocar no resto.
