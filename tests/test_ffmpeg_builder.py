from audioguard.ffmpeg_builder import AudioConfig, OutputConfig, build_ffmpeg_args
from audioguard.sources import build_source
from audioguard.sources.base import ChannelSource


def _rtsp_source():
    return build_source(ChannelSource(url="rtsp://origem/canal", protocol="rtsp", extra={}))


def test_passthrough_when_has_audio():
    args = build_ffmpeg_args(
        _rtsp_source(), AudioConfig(), OutputConfig(dir="/tmp/out"), has_audio=True
    )
    assert "-c:a" in args
    assert args[args.index("-c:a") + 1] == "copy"
    assert "anullsrc" not in " ".join(args)


def test_silent_audio_when_no_audio():
    args = build_ffmpeg_args(
        _rtsp_source(), AudioConfig(), OutputConfig(dir="/tmp/out"), has_audio=False
    )
    joined = " ".join(args)
    assert "anullsrc" in joined
    assert "-map 0:v" in joined
    assert "-map 1:a" in joined
    assert "-shortest" in args


def test_force_silent_overrides_detection():
    args = build_ffmpeg_args(
        _rtsp_source(), AudioConfig(mode="force-silent"), OutputConfig(dir="/tmp/out"), has_audio=True
    )
    assert "anullsrc" in " ".join(args)


def test_force_passthrough_overrides_detection():
    args = build_ffmpeg_args(
        _rtsp_source(), AudioConfig(mode="force-passthrough"), OutputConfig(dir="/tmp/out"), has_audio=False
    )
    assert "anullsrc" not in " ".join(args)


def test_segment_type_propagates():
    args = build_ffmpeg_args(
        _rtsp_source(), AudioConfig(), OutputConfig(dir="/tmp/out", segment_type="fmp4"), has_audio=True
    )
    assert "fmp4" in args


def test_publish_mode_rtsp():
    output = OutputConfig(mode="publish", publish_url="rtsp://127.0.0.1:8554/ag_canal01")
    args = build_ffmpeg_args(_rtsp_source(), AudioConfig(), output, has_audio=True)
    assert "-f" in args and args[args.index("-f") + 1] == "rtsp"
    assert args[-1] == "rtsp://127.0.0.1:8554/ag_canal01"
    assert "hls" not in args


def test_publish_mode_rtmp():
    output = OutputConfig(mode="publish", publish_url="rtmp://127.0.0.1:1935/live/ag_canal01")
    args = build_ffmpeg_args(_rtsp_source(), AudioConfig(), output, has_audio=True)
    assert "-f" in args and args[args.index("-f") + 1] == "flv"
    assert args[-1] == "rtmp://127.0.0.1:1935/live/ag_canal01"


def test_publish_mode_requires_url():
    output = OutputConfig(mode="publish")
    try:
        build_ffmpeg_args(_rtsp_source(), AudioConfig(), output, has_audio=True)
        assert False, "deveria ter levantado ValueError"
    except ValueError:
        pass
