"""Monta os argumentos do processo ffmpeg pra um canal, dado o resultado do
detector (tem audio real ou nao).

Video sempre em `-c:v copy` (zero reencode, zero perda). So o audio
silencioso, quando necessario, e sintetizado - custo de CPU desprezivel.
"""
from __future__ import annotations

from dataclasses import dataclass

from .sources.base import Source


@dataclass(frozen=True)
class AudioConfig:
    mode: str = "auto"  # auto | force-passthrough | force-silent
    silent_bitrate_kbps: int = 32
    silent_sample_rate: int = 48000
    silent_channels: int = 2


@dataclass(frozen=True)
class OutputConfig:
    dir: str
    segment_type: str = "mpegts"  # mpegts | fmp4
    hls_time: int = 4
    hls_list_size: int = 6


def _resolve_use_silent(audio: AudioConfig, has_audio: bool) -> bool:
    if audio.mode == "force-silent":
        return True
    if audio.mode == "force-passthrough":
        return False
    return not has_audio  # auto


def build_ffmpeg_args(
    source: Source,
    audio: AudioConfig,
    output: OutputConfig,
    has_audio: bool,
) -> list[str]:
    use_silent = _resolve_use_silent(audio, has_audio)

    args: list[str] = ["-hide_banner", "-loglevel", "warning"]
    args += source.input_args()

    if use_silent:
        args += [
            "-f", "lavfi",
            "-i", (
                f"anullsrc=channel_layout="
                f"{'stereo' if audio.silent_channels == 2 else 'mono'}"
                f":sample_rate={audio.silent_sample_rate}"
            ),
            "-map", "0:v",
            "-map", "1:a",
            "-c:v", "copy",
            "-c:a", "aac",
            "-b:a", f"{audio.silent_bitrate_kbps}k",
            "-shortest",
        ]
    else:
        args += ["-c:v", "copy", "-c:a", "copy"]

    args += [
        "-f", "hls",
        "-hls_time", str(output.hls_time),
        "-hls_list_size", str(output.hls_list_size),
        "-hls_segment_type", output.segment_type,
        "-hls_flags", "delete_segments+independent_segments",
        f"{output.dir}/index.m3u8",
    ]

    return args
