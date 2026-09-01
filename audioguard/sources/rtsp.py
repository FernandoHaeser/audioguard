from __future__ import annotations

from .base import Source


class RtspSource(Source):
    protocol = "rtsp"

    def input_args(self) -> list[str]:
        return [
            "-rtsp_transport", "tcp",
            "-fflags", "+genpts",
            "-i", self.source.url,
        ]

    def probe_url(self) -> str:
        return self.source.url
