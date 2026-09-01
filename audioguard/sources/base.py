"""Interface que toda fonte de entrada (RTSP, RTMP, SRT, HLS, ...) implementa.

Adicionar suporte a um protocolo novo = criar uma subclasse de `Source` e
registrar em `sources/__init__.py`. Nada no detector, no builder de args do
ffmpeg ou no supervisor precisa mudar.
"""
from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass


@dataclass(frozen=True)
class ChannelSource:
    """Config de origem de um canal, como vem do YAML (`source:` block)."""

    url: str
    protocol: str
    extra: dict


class Source(ABC):
    """Estratégia de input do ffmpeg para um protocolo específico.

    Cada protocolo tem particularidades de flags de entrada (ex.: RTSP quer
    `-rtsp_transport tcp`; SRT quer flags próprias de latência). Isolar isso
    aqui evita que o resto do código precise saber a diferença.
    """

    #: nome do protocolo como aparece em `source.protocol` no YAML do canal
    protocol: str = ""

    def __init__(self, source: ChannelSource):
        self.source = source

    @abstractmethod
    def input_args(self) -> list[str]:
        """Argumentos de ffmpeg que precedem `-i <url>` para este protocolo,
        mais o próprio `-i <url>`. Ex.: `["-rtsp_transport", "tcp", "-i", url]`.
        """
        raise NotImplementedError

    @abstractmethod
    def probe_url(self) -> str:
        """URL a passar para o `ffprobe` do detector. Normalmente igual a
        `self.source.url`, mas alguns protocolos precisam de flags/wrapping
        diferentes (documentar no override caso surja).
        """
        raise NotImplementedError
