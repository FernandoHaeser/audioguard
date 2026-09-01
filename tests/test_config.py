import pytest

from audioguard.config import ConfigError, load_channel_config


def test_loads_example_channel():
    config = load_channel_config("examples/channel.yaml")
    assert config.id == "canal-01"
    assert config.source.protocol == "rtsp"
    assert config.output.segment_type == "mpegts"
    assert config.audio.mode == "auto"


def test_missing_required_field_raises(tmp_path):
    bad = tmp_path / "bad.yaml"
    bad.write_text("id: x\n")
    with pytest.raises(ConfigError):
        load_channel_config(bad)
