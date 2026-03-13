"""Packaging contracts for the public CLI entrypoint."""

from __future__ import annotations

import tomllib
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_pyproject_cli_entrypoint_is_package_main():
    pyproject = ROOT / "pyproject.toml"
    data = tomllib.loads(pyproject.read_text(encoding="utf-8"))

    assert data["project"]["scripts"]["dartlab"] == "dartlab.cli.main:main"
