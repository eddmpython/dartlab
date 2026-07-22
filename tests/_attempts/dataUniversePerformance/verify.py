"""Real-data parity check against the current EDGAR owner."""

from __future__ import annotations

import json
import sys
import time
from pathlib import Path

from polars.testing import assert_frame_equal

ATTEMPT_DIR = Path(__file__).resolve().parent
if str(ATTEMPT_DIR) not in sys.path:
    sys.path.insert(0, str(ATTEMPT_DIR))

from prototype import runtimeContext, scanDuckDbNative, scanPolarsNative  # noqa: E402


def _canonical(frame):
    identity = [name for name in ("stockCode", "corpName") if name in frame.columns]
    periods = sorted(name for name in frame.columns if name not in identity)
    return frame.select([*identity, *periods]).sort("stockCode")


def main() -> None:
    from dartlab.providers.edgar.finance.scanAccount import scanAccount

    started = time.perf_counter()
    baseline = _canonical(scanAccount("sales", freq="Q"))
    context = runtimeContext("sales")
    results = []
    for name, candidate in (
        ("duckdb", scanDuckDbNative(context, threads=8)),
        ("polars", scanPolarsNative(context)),
    ):
        canonical = _canonical(candidate)
        try:
            assert_frame_equal(baseline, canonical, check_exact=True)
            equal = True
            error = None
        except AssertionError as exc:
            equal = False
            error = str(exc).splitlines()[0]
        results.append({"candidate": name, "equal": equal, "shape": list(canonical.shape), "error": error})
    print(
        json.dumps(
            {
                "elapsedSec": round(time.perf_counter() - started, 6),
                "baselineShape": list(baseline.shape),
                "results": results,
            },
            ensure_ascii=False,
        )
    )


if __name__ == "__main__":
    main()
