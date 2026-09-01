"""Verifica presenca de ffmpeg/ffprobe e, se pedido explicitamente, instala.

Instalar pacote de sistema exige privilegio (apt install roda como root) -
por isso isso nunca acontece implicito dentro de `run`/`run-dir`. So o
subcomando `audioguard install-ffmpeg`, chamado deliberadamente pelo
operador, dispara isso.
"""
from __future__ import annotations

import os
import shutil
import subprocess


class FfmpegInstallError(RuntimeError):
    pass


def has_ffmpeg() -> bool:
    return shutil.which("ffmpeg") is not None and shutil.which("ffprobe") is not None


def _run(cmd: list[str]) -> None:
    result = subprocess.run(cmd)
    if result.returncode != 0:
        raise FfmpegInstallError(f"comando falhou (rc={result.returncode}): {' '.join(cmd)}")


def install_ffmpeg() -> None:
    """Instala ffmpeg via apt (Debian/Ubuntu - o alvo documentado do projeto).

    Levanta FfmpegInstallError com instrucao manual em qualquer outro caso:
    sem apt-get disponivel, ou sem privilegio de root.
    """
    if has_ffmpeg():
        return

    if shutil.which("apt-get") is None:
        raise FfmpegInstallError(
            "apt-get nao encontrado neste sistema. instale ffmpeg manualmente "
            "com o gerenciador de pacotes da sua distro (ex.: 'brew install ffmpeg', "
            "'dnf install ffmpeg', 'pacman -S ffmpeg')."
        )

    if os.geteuid() != 0:
        raise FfmpegInstallError(
            "instalar ffmpeg via apt exige root. rode: sudo audioguard install-ffmpeg"
        )

    _run(["apt-get", "update"])
    _run(["apt-get", "install", "-y", "ffmpeg"])

    if not has_ffmpeg():
        raise FfmpegInstallError(
            "apt install rodou sem erro mas ffmpeg/ffprobe continuam ausentes do PATH. "
            "verifique manualmente ('which ffmpeg')."
        )
