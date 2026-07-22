"""Isolated-process benchmark for EDGAR universe account scan candidates."""

from __future__ import annotations

import argparse
import importlib
import json
import os
import subprocess
import sys
import threading
import time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import psutil

ATTEMPT_DIR = Path(__file__).resolve().parent
if str(ATTEMPT_DIR) not in sys.path:
    sys.path.insert(0, str(ATTEMPT_DIR))

from prototype import (  # noqa: E402
    runtimeContext,
    scanAccountsDuckDbNative,
    scanArrowBatched,
    scanDuckDbBatched,
    scanDuckDbNative,
    scanPolarsNative,
)


def _shape(frame) -> list[int]:
    return [int(frame.height), int(frame.width)]


def _edgar(method: str):
    if method == "current":
        from dartlab.providers.edgar.finance.scanAccount import scanAccount

        return scanAccount("sales", freq="Q")
    context = runtimeContext("sales")
    if method == "duckdb1":
        return scanDuckDbNative(context, threads=1)
    if method == "duckdb4":
        return scanDuckDbNative(context, threads=4)
    if method == "duckdb8":
        return scanDuckDbNative(context, threads=8)
    if method == "duckdb128":
        return scanDuckDbNative(context, threads=4, memoryLimitMb=128)
    if method == "duckdb256":
        return scanDuckDbNative(context, threads=4, memoryLimitMb=256)
    if method == "duckdb64":
        return scanDuckDbNative(context, threads=4, memoryLimitMb=64)
    if method == "duckdb64x2":
        return scanDuckDbNative(context, threads=2, memoryLimitMb=64)
    if method == "duckdbBatch256":
        return scanDuckDbBatched(context, batchFiles=256)
    if method == "duckdbBatch512":
        return scanDuckDbBatched(context, batchFiles=512)
    if method == "duckdbFused2":
        contexts = {
            "sales": context,
            "operating_profit": runtimeContext("operating_profit"),
        }
        frames = scanAccountsDuckDbNative(contexts)
        return frames["sales"], frames["operating_profit"]
    if method == "arrowBatch256":
        return scanArrowBatched(context, batchFiles=256)
    if method == "arrowBatch512":
        return scanArrowBatched(context, batchFiles=512)
    if method == "current2":
        from dartlab.providers.edgar.finance.scanAccount import scanAccount

        return scanAccount("sales", freq="Q"), scanAccount("operating_profit", freq="Q")
    if method == "duckdbAll":
        return scanDuckDbNative(context, threads=4, pruneListed=False)
    if method == "polars":
        return scanPolarsNative(context)
    raise ValueError(f"unknown EDGAR method: {method}")


def _dart():
    from dartlab.providers.dart.finance.scanAccount import scanAccount

    return scanAccount("sales", freq="Q")


def _runWorker(method: str) -> dict[str, object]:
    process = psutil.Process(os.getpid())
    peakRss = process.memory_info().rss
    stop = threading.Event()

    def sample() -> None:
        nonlocal peakRss
        while not stop.wait(0.01):
            try:
                peakRss = max(peakRss, process.memory_info().rss)
            except psutil.Error:
                return

    sampler = threading.Thread(target=sample, daemon=True)
    sampler.start()
    if method.startswith("pair-"):
        importlib.import_module("dartlab.core.dataLoader")
        importlib.import_module("dartlab.core.edgarClient")
        importlib.import_module("dartlab.providers.dart.finance.scanAccount")
        importlib.import_module("dartlab.providers.edgar.finance.scanAccount")

    started = time.perf_counter()
    try:
        if method.startswith("pair-"):
            _, edgarMethod, schedule = method.split("-", 2)
            if schedule == "sequential":
                dartFrame = _dart()
                edgarFrame = _edgar(edgarMethod)
            elif schedule == "parallel":
                with ThreadPoolExecutor(max_workers=2) as pool:
                    dartFuture = pool.submit(_dart)
                    edgarFuture = pool.submit(_edgar, edgarMethod)
                    dartFrame = dartFuture.result()
                    edgarFrame = edgarFuture.result()
            else:
                raise ValueError(f"unknown schedule: {schedule}")
            result = {
                "method": method,
                "elapsedSec": round(time.perf_counter() - started, 6),
                "dartShape": _shape(dartFrame),
                "edgarShape": _shape(edgarFrame),
            }
        else:
            frame = _edgar(method)
            shape = [_shape(item) for item in frame] if isinstance(frame, tuple) else _shape(frame)
            result = {
                "method": method,
                "elapsedSec": round(time.perf_counter() - started, 6),
                "shape": shape,
            }
    finally:
        stop.set()
        sampler.join(timeout=1)
    result["peakRssMiB"] = round(peakRss / 1024 / 1024, 3)
    return result


def _measure(method: str) -> dict[str, object]:
    command = [sys.executable, "-X", "utf8", str(Path(__file__).resolve()), "--worker", method]
    process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    stdout, stderr = process.communicate()
    if process.returncode:
        raise RuntimeError(f"{method} failed ({process.returncode})\n{stdout}\n{stderr}")
    return json.loads(stdout.strip().splitlines()[-1])


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--worker")
    parser.add_argument(
        "--methods",
        default="current,duckdb1,duckdb4,duckdb8,duckdbAll,polars",
    )
    args = parser.parse_args()
    if args.worker:
        print(json.dumps(_runWorker(args.worker), ensure_ascii=False))
        return

    for method in args.methods.split(","):
        print(json.dumps(_measure(method.strip()), ensure_ascii=False), flush=True)


if __name__ == "__main__":
    main()
