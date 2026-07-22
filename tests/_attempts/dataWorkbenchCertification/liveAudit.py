"""Queryable catalog 전체를 격리 프로세스로 실제 호출하는 인증 runner."""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
import time
from collections import Counter
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from typing import Any

import dartlab


def _run(worker: Path, assetId: str, timeout: float) -> dict[str, Any]:
    started = time.perf_counter()
    try:
        completed = subprocess.run(
            [sys.executable, "-X", "utf8", str(worker), assetId, str(max(1_000, int((timeout - 2) * 1000)))],
            capture_output=True,
            text=True,
            encoding="utf-8",
            timeout=timeout,
            check=False,
        )
    except subprocess.TimeoutExpired:
        return {
            "assetId": assetId,
            "status": "processTimeout",
            "elapsedMs": round((time.perf_counter() - started) * 1000, 3),
        }
    lines = [line for line in completed.stdout.splitlines() if line.strip().startswith("{")]
    if not lines:
        return {
            "assetId": assetId,
            "status": "processFailed",
            "returnCode": completed.returncode,
            "stderr": completed.stderr[-1000:],
            "elapsedMs": round((time.perf_counter() - started) * 1000, 3),
        }
    result = json.loads(lines[-1])
    result["returnCode"] = completed.returncode
    if completed.stderr:
        result["stderr"] = completed.stderr[-1000:]
    return result


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--workers", type=int, default=4)
    parser.add_argument("--timeout", type=float, default=25.0)
    parser.add_argument("--output", type=Path)
    parser.add_argument("--owner")
    parser.add_argument("--asset", action="append", dest="assetIds")
    args = parser.parse_args()

    assets = [asset for asset in dartlab.data("catalog").assets if asset.queryable]
    if args.owner:
        assets = [asset for asset in assets if asset.owner == args.owner]
    if args.assetIds:
        requested = set(args.assetIds)
        assets = [asset for asset in assets if asset.assetId in requested]
        missing = requested - {asset.assetId for asset in assets}
        if missing:
            parser.error(f"queryable asset이 아님: {', '.join(sorted(missing))}")
    worker = Path(__file__).with_name("liveAuditWorker.py")
    results = []
    with ThreadPoolExecutor(max_workers=args.workers) as pool:
        futures = {pool.submit(_run, worker, asset.assetId, args.timeout): asset.assetId for asset in assets}
        for future in as_completed(futures):
            result = future.result()
            results.append(result)
            print(
                f"{len(results):>3}/{len(assets)} {result['assetId']} {result['status']} "
                f"{result.get('elapsedMs', 0):.0f}ms",
                flush=True,
            )
    results.sort(key=lambda item: item["assetId"])
    summary = {
        "assetCount": len(assets),
        "statusCounts": dict(Counter(item["status"] for item in results)),
        "gapCounts": dict(Counter(code for item in results for code in item.get("gapCodes", ()))),
    }
    payload = {"summary": summary, "results": results}
    if args.output:
        args.output.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(summary, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
