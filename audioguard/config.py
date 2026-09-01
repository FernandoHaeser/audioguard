"""Carrega um YAML de canal (ver examples/channel.yaml) e valida os campos
minimos. Sem dependencia de framework de validacao pesado - o escopo e
pequeno o bastante pra um parse manual explicito ser mais claro que um
schema declarativo.
"""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import yaml

from .ffmpeg_builder import AudioConfig, OutputConfig
from .sources.base import ChannelSource


class ConfigError(ValueError):
    pass


@dataclass(frozen=True)
class ChannelConfig:
    id: str
    source: ChannelSource
    output: OutputConfig
    audio: AudioConfig
    probe_timeout_s: float = 5.0


def _require(d: dict, key: str, ctx: str) -> object:
    if key not in d:
        raise ConfigError(f"campo obrigatorio ausente: '{key}' em {ctx}")
    return d[key]


def load_channel_config(path: str | Path) -> ChannelConfig:
    raw = yaml.safe_load(Path(path).read_text())
    if not isinstance(raw, dict):
        raise ConfigError(f"{path}: yaml raiz precisa ser um mapeamento")

    ch_id = _require(raw, "id", str(path))

    src_raw = _require(raw, "source", ch_id)
    source = ChannelSource(
        url=_require(src_raw, "url", f"{ch_id}.source"),
        protocol=_require(src_raw, "protocol", f"{ch_id}.source"),
        extra={k: v for k, v in src_raw.items() if k not in ("url", "protocol")},
    )

    out_raw = _require(raw, "output", ch_id)
    output = OutputConfig(
        dir=_require(out_raw, "dir", f"{ch_id}.output"),
        segment_type=out_raw.get("segment_type", "mpegts"),
        hls_time=int(out_raw.get("hls_time", 4)),
        hls_list_size=int(out_raw.get("hls_list_size", 6)),
    )

    audio_raw = raw.get("audio", {})
    audio = AudioConfig(
        mode=audio_raw.get("mode", "auto"),
        silent_bitrate_kbps=int(audio_raw.get("silent_bitrate_kbps", 32)),
        silent_sample_rate=int(audio_raw.get("silent_sample_rate", 48000)),
        silent_channels=int(audio_raw.get("silent_channels", 2)),
    )

    detector_raw = raw.get("detector", {})
    probe_timeout_s = float(detector_raw.get("probe_timeout_s", 5.0))

    return ChannelConfig(
        id=ch_id,
        source=source,
        output=output,
        audio=audio,
        probe_timeout_s=probe_timeout_s,
    )
