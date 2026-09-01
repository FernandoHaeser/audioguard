"""Decide se a origem tem uma faixa de audio decodificavel.

Roda `ffprobe` uma vez por start/restart de canal (a origem pode mudar de
estado entre uma tentativa e outra: camera que ganhou microfone, fonte que
perdeu audio, etc). Nunca deve travar a subida do canal esperando resposta -
timeout curto, e qualquer falha vira "sem audio" (fallback seguro: sempre
silencio em vez de travar o canal).
"""
from __future__ import annotations

import json
import logging
import subprocess

from .sources.base import Source

logger = logging.getLogger("audioguard.detector")


class AudioDetector:
    def __init__(self, probe_timeout_s: float = 5.0):
        self.probe_timeout_s = probe_timeout_s

    def has_audio(self, source: Source) -> bool:
        """True se a origem expoe pelo menos uma stream de audio valida."""
        url = source.probe_url()
        cmd = [
            "ffprobe", "-v", "error",
            "-select_streams", "a",
            "-show_entries", "stream=codec_type",
            "-of", "json",
            url,
        ]
        try:
            result = subprocess.run(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                timeout=self.probe_timeout_s,
            )
        except subprocess.TimeoutExpired:
            logger.warning("ffprobe timeout em %.1fs para %s, assumindo sem audio", self.probe_timeout_s, url)
            return False

        if result.returncode != 0:
            logger.warning("ffprobe falhou para %s (rc=%s): %s", url, result.returncode, result.stderr.strip())
            return False

        try:
            data = json.loads(result.stdout)
        except json.JSONDecodeError:
            logger.warning("ffprobe retornou json invalido para %s", url)
            return False

        streams = data.get("streams", [])
        return len(streams) > 0
