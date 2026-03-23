"""
실험 ID: 004
실험명: DuckDB topic-scoped viewer route

목적:
- DuckDB `read_parquet` / `parquet_scan` 기반 raw read가 viewer hot path에서 실전 후보가 될 수 있는지 검증한다

가설:
1. topic-scoped docs/report read는 DuckDB도 충분히 구현 가능하며 exact match보다 cold I/O 경로 비교에 의미가 있다
2. metadata pruning은 강하지만, Python으로 다시 옮기는 비용 때문에 warm path는 Polars보다 불리할 수 있다

방법:
1. 002 runtime을 상속하고 docs/report raw read만 DuckDB 쿼리로 바꾼다
2. 001 baseline harness와 동일 case matrix로 cold/warm/RSS/bytes를 측정한다
3. baseline과 exact hash, 속도, 메모리를 비교한다

결과 (실험 후 작성):
- 초기 구현은 `duckdb -> arrow` 경로 때문에 `pyarrow` 의존 오류가 발생했고, 이후 `fetchall -> Polars`로 수정해 재실행했다
- `safe2` 기준 exact match는 `0/12`였다
- `toc` cold는 `2.268~2.944s`였지만 peak RSS가 `563~852MB`까지 올라 Polars 대비 크게 불리했다
- docs topic warm도 무거웠다: `businessOverview warm 1036.7~1798.1ms`, `periodSwitch warm 297.7~990.9ms`
- report topic은 빠르다: `dividend cold 0.593~0.615s`, `majorHolder cold 0.611~0.639s`

결론:
- DuckDB는 이번 Python-only 조립 경로에서 reject다. docs topic에서 `fetchall` 비용이 커져 RSS와 warm latency가 나빠졌다
- 향후 DuckDB를 다시 보려면 Python row materialization이 아니라 native vectorized bridge가 필요하다

실험일: 2026-03-23
"""

from __future__ import annotations

import argparse
import importlib.util
import sys
from pathlib import Path

import polars as pl

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT / "src") not in sys.path:
    sys.path.insert(0, str(ROOT / "src"))


def loadModule(path: Path, moduleName: str):
    spec = importlib.util.spec_from_file_location(moduleName, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"module load failed: {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


BASE = loadModule(Path(__file__).with_name("001_viewerApiBaseline.py"), "exp090Base004")
POLARS = loadModule(Path(__file__).with_name("002_polarsViewerRoute.py"), "exp090Polars004")


def duckdbConn():
    try:
        import duckdb
    except ImportError as exc:  # pragma: no cover
        raise RuntimeError("duckdb가 필요합니다. `uv run --with duckdb --with psutil ...`로 실행하세요.") from exc
    return duckdb.connect(database=":memory:")


class DuckdbViewerRuntime(POLARS.PolarsViewerRuntime):
    def queryToPolars(self, query: str) -> pl.DataFrame:
        conn = duckdbConn()
        cursor = conn.execute(query)
        columns = [desc[0] for desc in cursor.description]
        rows = cursor.fetchall()
        conn.close()
        if not rows:
            return pl.DataFrame({column: [] for column in columns})
        return pl.DataFrame(rows, schema=columns, orient="row")

    def readDocsFrame(self) -> pl.DataFrame:
        if self.docsFrameCache is None:
            path = ROOT / "data" / "dart" / "docs" / f"{self.stockCode}.parquet"
            query = (
                "select year, report_type, rcept_date, section_order, section_title, section_content "
                f"from read_parquet('{path.as_posix()}')"
            )
            self.docsFrameCache = self.queryToPolars(query)
        return self.docsFrameCache

    def readReportApiFrame(self) -> pl.DataFrame:
        if self.reportApiCache is None:
            path = ROOT / "data" / "dart" / "report" / f"{self.stockCode}.parquet"
            self.reportApiCache = self.queryToPolars(f"select apiType from read_parquet('{path.as_posix()}')")
        return self.reportApiCache


def childMain() -> None:
    BASE.childMain(DuckdbViewerRuntime)


def main() -> None:
    if "--child" in sys.argv:
        childMain()
        return
    parser = argparse.ArgumentParser()
    parser.add_argument("--sample", default=BASE.DEFAULT_SAMPLE, choices=["safe2", "all6"])
    args = parser.parse_args()
    baselineRows = BASE.collectMode(Path(__file__).with_name("001_viewerApiBaseline.py"), "baseline", args.sample)
    candidateRows = BASE.collectMode(Path(__file__), "duckdb", args.sample)
    BASE.printSummary(f"090 duckdb / {args.sample}", candidateRows)
    BASE.printComparisonSummary(
        f"090 duckdb vs baseline / {args.sample}",
        BASE.compareRuns(baselineRows, candidateRows),
    )


if __name__ == "__main__":
    main()
