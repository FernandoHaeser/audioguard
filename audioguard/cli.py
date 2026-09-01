"""CLI de entrada. Uso:

    audioguard run <config.yaml>          # roda um canal em foreground
    audioguard run-dir <dir-com-yamls>    # roda todos os canais de um dir,
                                           # um por thread, ate Ctrl+C
    audioguard install-ffmpeg             # instala ffmpeg/ffprobe via apt (precisa root)
"""
from __future__ import annotations

import argparse
import logging
import sys
import threading
from pathlib import Path

from .config import load_channel_config
from .ffmpeg_setup import FfmpegInstallError, has_ffmpeg, install_ffmpeg
from .supervisor import ChannelSupervisor


def _setup_logging(verbose: bool) -> None:
    logging.basicConfig(
        level=logging.DEBUG if verbose else logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    )


def _warn_if_ffmpeg_missing() -> None:
    if not has_ffmpeg():
        print(
            "aviso: ffmpeg/ffprobe nao encontrados no PATH. "
            "rode 'sudo audioguard install-ffmpeg' ou instale manualmente.",
            file=sys.stderr,
        )


def cmd_install_ffmpeg(args: argparse.Namespace) -> int:
    if has_ffmpeg():
        print("ffmpeg/ffprobe ja instalados.")
        return 0
    try:
        install_ffmpeg()
    except FfmpegInstallError as e:
        print(f"erro: {e}", file=sys.stderr)
        return 1
    print("ffmpeg/ffprobe instalados com sucesso.")
    return 0


def cmd_run(args: argparse.Namespace) -> int:
    _warn_if_ffmpeg_missing()
    config = load_channel_config(args.config)
    supervisor = ChannelSupervisor(config)
    try:
        supervisor.run_forever()
    except KeyboardInterrupt:
        supervisor.stop()
    return 0


def cmd_run_dir(args: argparse.Namespace) -> int:
    _warn_if_ffmpeg_missing()
    yml_files = sorted(Path(args.dir).glob("*.yaml")) + sorted(Path(args.dir).glob("*.yml"))
    if not yml_files:
        print(f"nenhum .yaml/.yml encontrado em {args.dir}", file=sys.stderr)
        return 1

    supervisors = [ChannelSupervisor(load_channel_config(f)) for f in yml_files]
    threads = [threading.Thread(target=s.run_forever, daemon=True) for s in supervisors]
    for t in threads:
        t.start()

    try:
        for t in threads:
            t.join()
    except KeyboardInterrupt:
        for s in supervisors:
            s.stop()
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="audioguard")
    parser.add_argument("-v", "--verbose", action="store_true")
    sub = parser.add_subparsers(dest="command", required=True)

    p_run = sub.add_parser("run", help="roda um unico canal em foreground")
    p_run.add_argument("config", help="path do channel.yaml")
    p_run.set_defaults(func=cmd_run)

    p_run_dir = sub.add_parser("run-dir", help="roda todos os canais de um diretorio")
    p_run_dir.add_argument("dir", help="diretorio com *.yaml, um por canal")
    p_run_dir.set_defaults(func=cmd_run_dir)

    p_install = sub.add_parser("install-ffmpeg", help="instala ffmpeg/ffprobe via apt (precisa root)")
    p_install.set_defaults(func=cmd_install_ffmpeg)

    args = parser.parse_args(argv)
    _setup_logging(args.verbose)
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
