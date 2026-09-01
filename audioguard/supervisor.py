"""Sobe e mantem vivo o processo ffmpeg de um canal.

Backoff exponencial em restart (1s, 2s, 4s, ... ate um teto) - nunca loop
apertado batendo numa origem fora do ar. Cada canal e isolado: falha num
canal nao afeta os outros (processos separados, sem estado compartilhado).
"""
from __future__ import annotations

import logging
import subprocess
import time
from pathlib import Path

from .config import ChannelConfig
from .detector import AudioDetector
from .ffmpeg_builder import build_ffmpeg_args
from .sources import build_source

logger = logging.getLogger("audioguard.supervisor")


class ChannelSupervisor:
    def __init__(
        self,
        config: ChannelConfig,
        max_backoff_s: float = 30.0,
        ffmpeg_bin: str = "ffmpeg",
    ):
        self.config = config
        self.max_backoff_s = max_backoff_s
        self.ffmpeg_bin = ffmpeg_bin
        self.detector = AudioDetector(probe_timeout_s=config.probe_timeout_s)
        self._stop = False

    def stop(self) -> None:
        self._stop = True

    def run_forever(self) -> None:
        """Bloqueia rodando o canal, reiniciando o ffmpeg quando ele cai.
        Chame em uma thread/processo dedicado por canal.
        """
        backoff = 1.0
        while not self._stop:
            started_at = time.monotonic()
            try:
                self._run_once()
            except Exception:
                logger.exception("erro inesperado no canal %s", self.config.id)

            if self._stop:
                return

            uptime = time.monotonic() - started_at
            if uptime > self.max_backoff_s:
                backoff = 1.0  # ficou de pe tempo suficiente, reseta o backoff
            logger.warning(
                "canal %s caiu apos %.1fs, reiniciando em %.1fs", self.config.id, uptime, backoff
            )
            time.sleep(backoff)
            backoff = min(backoff * 2, self.max_backoff_s)

    def _run_once(self) -> None:
        if self.config.output.mode == "hls":
            Path(self.config.output.dir).mkdir(parents=True, exist_ok=True)

        source = build_source(self.config.source)
        has_audio = self.detector.has_audio(source)
        logger.info("canal %s: audio na origem = %s", self.config.id, has_audio)

        args = build_ffmpeg_args(source, self.config.audio, self.config.output, has_audio)
        cmd = [self.ffmpeg_bin, *args]
        logger.info("canal %s: %s", self.config.id, " ".join(cmd))

        proc = subprocess.Popen(cmd, stderr=subprocess.PIPE, text=True)
        try:
            assert proc.stderr is not None
            for line in proc.stderr:
                logger.debug("[%s] %s", self.config.id, line.rstrip())
        finally:
            proc.wait()
            if proc.returncode != 0:
                logger.warning("canal %s: ffmpeg saiu com codigo %s", self.config.id, proc.returncode)
