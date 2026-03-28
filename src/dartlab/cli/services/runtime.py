"""Runtime helpers shared by CLI commands."""

from __future__ import annotations

from importlib import import_module

from dartlab.cli.context import CommandSpec


def load_command_module(spec: CommandSpec):
    """커맨드 스펙에 해당하는 모듈을 동적 로드."""
    return import_module(spec.import_path)


def configure_dartlab():
    """dartlab 기본 설정 적용 (verbose off)."""
    import dartlab

    dartlab.verbose = False
    return dartlab
