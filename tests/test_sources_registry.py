import pytest

from audioguard.sources import UnsupportedProtocolError, build_source
from audioguard.sources.base import ChannelSource


def test_rtsp_source_builds():
    src = build_source(ChannelSource(url="rtsp://x/y", protocol="rtsp", extra={}))
    assert src.protocol == "rtsp"
    assert "-rtsp_transport" in src.input_args()


def test_unknown_protocol_raises():
    with pytest.raises(UnsupportedProtocolError):
        build_source(ChannelSource(url="rtmp://x/y", protocol="rtmp", extra={}))
