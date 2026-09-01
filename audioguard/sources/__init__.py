"""Registro de fontes suportadas.

Para adicionar um protocolo novo (rtmp, srt, hls, ...):
1. Criar `sources/<protocolo>.py` com uma subclasse de `Source`.
2. Importar e registrar aqui em `_REGISTRY`.

Nenhum outro módulo do projeto precisa mudar.
"""
from __future__ import annotations

from .base import ChannelSource, Source
from .rtsp import RtspSource

_REGISTRY: dict[str, type[Source]] = {
    RtspSource.protocol: RtspSource,
}


class UnsupportedProtocolError(ValueError):
    pass


def build_source(source: ChannelSource) -> Source:
    try:
        cls = _REGISTRY[source.protocol]
    except KeyError:
        supported = ", ".join(sorted(_REGISTRY)) or "(nenhum registrado)"
        raise UnsupportedProtocolError(
            f"protocolo '{source.protocol}' nao suportado. suportados: {supported}"
        ) from None
    return cls(source)


__all__ = ["ChannelSource", "Source", "build_source", "UnsupportedProtocolError"]
