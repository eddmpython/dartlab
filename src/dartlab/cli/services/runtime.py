"""Runtime helpers shared by CLI commands."""

from __future__ import annotations

from importlib import import_module

from dartlab.cli.context import CommandSpec


def load_command_module(spec: CommandSpec):
    return import_module(spec.import_path)


def configure_dartlab():
    import dartlab

    dartlab.verbose = False
    return dartlab
