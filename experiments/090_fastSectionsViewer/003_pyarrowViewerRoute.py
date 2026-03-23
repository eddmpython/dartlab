"""
실험 ID: 003
실험명: PyArrow topic-scoped viewer route

목적:
- Polars raw scan 대신 PyArrow Dataset scanner가 viewer hot path에서 더 낮은 RSS 또는 더 빠른 cold latency를 주는지 검증한다

가설:
1. docs/report raw read는 PyArrow scanner + 마지막 Polars 변환으로도 동일한 viewer 후보 payload를 만들 수 있다
2. topic-scoped docs read에서는 Polars direct read보다 RSS가 조금 더 낮을 수 있다

방법:
1. 002 runtime을 상속하고 docs/report raw read만 PyArrow Dataset scanner로 바꾼다
2. 001 baseline harness와 동일 case matrix로 cold/warm/RSS/bytes를 측정한다
3. baseline과 exact hash, 속도, 메모리를 비교한다

결과 (실험 후 작성):
- `safe2` 기준 exact match는 `0/12`였다
- `_sections=False`는 유지했지만 `toc` cold가 `2.273~2.725s`, peak RSS가 `470~568MB`로 Polars보다 분명히 불리했다
- docs topic은 더 무거웠다: `companyOverview cold 2.202~2.955s`, `businessOverview cold 3.869~4.901s`, warm도 Polars보다 느렸다
- report topic만은 충분히 빨랐다: `dividend cold 0.992~1.291s`, `majorHolder cold 0.964~1.284s`
- `periodSwitch:businessOverview`는 warm median `399.4ms~1066.2ms`로 baseline보다도 느린 구간이 나왔다

결론:
- PyArrow는 이번 구조에서는 winner가 아니다. raw scanner 자체보다 이후 Python-side 조립 비용이 커서 docs viewer hot path를 이기지 못했다
- report-only fast path 후보로는 남길 수 있지만, 090의 주력 read engine으로 채택할 이유는 부족하다

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


BASE = loadModule(Path(__file__).with_name("001_viewerApiBaseline.py"), "exp090Base003")
POLARS = loadModule(Path(__file__).with_name("002_polarsViewerRoute.py"), "exp090Polars003")


def pyarrowDataset():
    try:
        import pyarrow.dataset as ds
    except ImportError as exc:  # pragma: no cover
        raise RuntimeError("pyarrow가 필요합니다. `uv run --with pyarrow --with psutil ...`로 실행하세요.") from exc
    return ds


class PyarrowViewerRuntime(POLARS.PolarsViewerRuntime):
    def readDocsFrame(self) -> pl.DataFrame:
        if self.docsFrameCache is None:
            ds = pyarrowDataset()
            path = ROOT / "data" / "dart" / "docs" / f"{self.stockCode}.parquet"
            table = ds.dataset(path, format="parquet").to_table(
                columns=["year", "report_type", "rcept_date", "section_order", "section_title", "section_content"]
            )
            self.docsFrameCache = pl.from_arrow(table)
        return self.docsFrameCache

    def readReportApiFrame(self) -> pl.DataFrame:
        if self.reportApiCache is None:
            ds = pyarrowDataset()
            path = ROOT / "data" / "dart" / "report" / f"{self.stockCode}.parquet"
            table = ds.dataset(path, format="parquet").to_table(columns=["apiType"])
            self.reportApiCache = pl.from_arrow(table)
        return self.reportApiCache


def childMain() -> None:
    BASE.childMain(PyarrowViewerRuntime)


def main() -> None:
    if "--child" in sys.argv:
        childMain()
        return
    parser = argparse.ArgumentParser()
    parser.add_argument("--sample", default=BASE.DEFAULT_SAMPLE, choices=["safe2", "all6"])
    args = parser.parse_args()
    baselineRows = BASE.collectMode(Path(__file__).with_name("001_viewerApiBaseline.py"), "baseline", args.sample)
    candidateRows = BASE.collectMode(Path(__file__), "pyarrow", args.sample)
    BASE.printSummary(f"090 pyarrow / {args.sample}", candidateRows)
    BASE.printComparisonSummary(
        f"090 pyarrow vs baseline / {args.sample}",
        BASE.compareRuns(baselineRows, candidateRows),
    )


if __name__ == "__main__":
    main()
