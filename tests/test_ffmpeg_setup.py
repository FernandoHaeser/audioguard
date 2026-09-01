from unittest.mock import patch

import pytest

from audioguard.ffmpeg_setup import FfmpegInstallError, install_ffmpeg


def test_noop_when_already_installed():
    with patch("audioguard.ffmpeg_setup.has_ffmpeg", return_value=True):
        install_ffmpeg()  # nao deve levantar nem tentar rodar apt


def test_raises_when_no_apt():
    with patch("audioguard.ffmpeg_setup.has_ffmpeg", return_value=False), \
         patch("audioguard.ffmpeg_setup.shutil.which", return_value=None):
        with pytest.raises(FfmpegInstallError, match="apt-get"):
            install_ffmpeg()


def test_raises_when_not_root():
    with patch("audioguard.ffmpeg_setup.has_ffmpeg", return_value=False), \
         patch("audioguard.ffmpeg_setup.shutil.which", return_value="/usr/bin/apt-get"), \
         patch("audioguard.ffmpeg_setup.os.geteuid", return_value=1000):
        with pytest.raises(FfmpegInstallError, match="root"):
            install_ffmpeg()
