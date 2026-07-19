"""U2 격리 worker 검증용 deterministic failure fixture."""

from __future__ import annotations

import subprocess
import time


class TransientExecutionError(RuntimeError):
    pass


def deterministicFixture(value: int = 1):
    return {"value": value, "stable": True}


def transientFixture(value: int = 1, attempt: int = 1):
    if attempt == 1:
        raise TransientExecutionError("first attempt")
    return {"value": value, "attempt": attempt}


def slowFixture(delayMs: int = 1000):
    time.sleep(delayMs / 1000)
    return {"done": True}


def partialFrameFixture(rows: int = 10):
    import polars as pl

    return pl.DataFrame({"row": list(range(rows)), "value": [item * 2 for item in range(rows)]})


def partialListFixture(rows: int = 10):
    return [{"row": item, "value": item * 2} for item in range(rows)]


def hardCodedWriteFixture(path: str):
    with open(path, "w", encoding="utf-8") as stream:
        stream.write("mutated")
    return {"written": True}


def subprocessWriteFixture():
    subprocess.run(["cmd", "/c", "echo", "blocked"], check=True)
    return {"spawned": True}


def wrongOutputFixture():
    return "wrong"
