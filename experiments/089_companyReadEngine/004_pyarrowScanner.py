"""
실험 ID: 004
실험명: PyArrow scanner route

목적:
- Polars direct parquet read 대신 PyArrow Dataset scanner + Arrow table 경로가
  metadata/docs hot path에 더 유리한지 검증

가설:
1. report/docs raw scan은 PyArrow scanner로 읽고 마지막에만 Polars로 넘겨도 동일 payload를 만들 수 있다
2. metadata/docsOnly 경로에서 Polars direct read보다 메모리 피크가 더 낮을 가능성이 있다

방법:
1. `uv run --with pyarrow --with psutil`로 실행한다
2. 001 baseline harness의 metadataDocs case group만 사용한다
3. docs/report raw scan만 PyArrow로 바꾸고 downstream 로직은 002와 동일하게 유지한다

결과 (실험 후 작성):
- 총 30개 case(6종목 × metadataDocs 5개) 비교
- exact match: 6/30
- exact가 난 것은 `availableApiTypes` 6종목뿐
- availableApiTypes: 4.26~6.57x faster, peak 38.4~67.4% 절감
- topics: 2.75~4.66x faster, peak 32.4~59.0% 절감, exact 0/6
- index: 2.25~4.03x faster, peak 21.5~44.3% 절감, exact 0/6
- docs `show()`: 8.85~16.16x faster, peak 36.1~60.3% 절감, exact 0/12
- 같은 목적의 002와 비교하면 거의 모든 case에서 더 느리고 더 무거웠다

결론:
- **기각**
- PyArrow scanner는 “Polars로 직접 read 안 하기” 자체는 만족하지만, 현재 실험 범위에서는 002보다 우수하지 않았다
- metadata/docs 재구성에서 Arrow → Python/Polars 변환 비용이 커서 practical winner가 되지 못했다

실험일: 2026-03-23
"""

from __future__ import annotations

import argparse
import importlib.util
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT / "src") not in sys.path:
    sys.path.insert(0, str(ROOT / "src"))

import polars as pl


def _loadModule(path: Path, moduleName: str):
    spec = importlib.util.spec_from_file_location(moduleName, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"module load failed: {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


BASELINE = _loadModule(Path(__file__).with_name("001_baselineHarness.py"), "exp089Baseline004")
POLARS_SPLIT = _loadModule(Path(__file__).with_name("002_polarsRouteSplit.py"), "exp089PolarsSplit004")

from dartlab.core.reportSelector import selectReport


def _pyarrowDataset():
    try:
        import pyarrow.dataset as ds
    except ImportError as exc:  # pragma: no cover - runtime guard
        raise RuntimeError("pyarrow가 필요합니다. `uv run --with pyarrow --with psutil ...`로 실행하세요.") from exc
    return ds


def readReportApiFrameArrow(stockCode: str) -> pl.DataFrame:
    ds = _pyarrowDataset()
    path = ROOT / "data" / "dart" / "report" / f"{stockCode}.parquet"
    table = ds.dataset(path, format="parquet").to_table(columns=["apiType"])
    return pl.from_arrow(table)


def readDocsFrameArrow(stockCode: str) -> pl.DataFrame:
    ds = _pyarrowDataset()
    path = ROOT / "data" / "dart" / "docs" / f"{stockCode}.parquet"
    table = ds.dataset(path, format="parquet").to_table(
        columns=["year", "report_type", "rcept_date", "section_order", "section_title", "section_content"]
    )
    return pl.from_arrow(table)


def fastAvailableApiTypesArrow(stockCode: str) -> list[str]:
    from dartlab.engines.company.dart.report.types import API_TYPES

    df = readReportApiFrameArrow(stockCode)
    available = {str(value) for value in df["apiType"].drop_nulls().unique().to_list()}
    return [name for name in API_TYPES if name in available]


def iterMinimalDocsSubsetsArrow(stockCode: str):
    df = readDocsFrameArrow(stockCode)
    years = sorted(df["year"].unique().to_list(), reverse=True)
    for year in years:
        for reportKind, suffix in POLARS_SPLIT.REPORT_KINDS:
            periodKey = f"{year}{suffix}"
            report = selectReport(df, year, reportKind=reportKind)
            if report is None or "section_content" not in report.columns:
                continue
            subset = (
                report.select(["section_order", "section_title", "section_content"])
                .filter(pl.col("section_content").is_not_null() & (pl.col("section_content").str.len_chars() > 0))
                .sort("section_order")
            )
            if subset.height == 0:
                continue
            yield periodKey, subset


def buildDocsMetaArrow(stockCode: str) -> dict[str, Any]:
    topicOrder: list[str] = []
    topicMeta: dict[str, dict[str, Any]] = {}
    allPeriods: list[str] = []
    for periodKey, subset in iterMinimalDocsSubsetsArrow(stockCode):
        allPeriods.append(periodKey)
        for record in subset.iter_rows(named=True):
            title = str(record["section_title"] or "")
            normalizedTitle = POLARS_SPLIT.normalizeTitle(title)
            if not normalizedTitle:
                continue
            topic = POLARS_SPLIT.mapSectionTitle(normalizedTitle)
            if not topic:
                continue
            meta = topicMeta.setdefault(
                topic,
                {
                    "periods": set(),
                    "blocks": 0,
                    "chapter": POLARS_SPLIT._chapterFromMajor(POLARS_SPLIT.parseMajorNum(title)),
                    "previewByPeriod": {},
                },
            )
            if topic not in topicOrder:
                topicOrder.append(topic)
            meta["periods"].add(periodKey)
            content = str(record["section_content"] or "")
            meta["blocks"] += len(POLARS_SPLIT.splitMarkdownBlocks(content))
            if periodKey not in meta["previewByPeriod"]:
                previewText = content.replace("\n", " ").strip()[:80]
                if previewText:
                    meta["previewByPeriod"][periodKey] = previewText
    return {
        "topicOrder": topicOrder,
        "topicMeta": topicMeta,
        "allPeriods": POLARS_SPLIT.sortPeriods(list(dict.fromkeys(allPeriods)), descending=True),
    }


def buildDocsTopicBlockIndexArrow(stockCode: str, topic: str):
    for _periodKey, subset in iterMinimalDocsSubsetsArrow(stockCode):
        rows: list[dict[str, Any]] = []
        blockOrder = 0
        for record in subset.iter_rows(named=True):
            title = str(record["section_title"] or "")
            normalizedTitle = POLARS_SPLIT.normalizeTitle(title)
            if not normalizedTitle or POLARS_SPLIT.mapSectionTitle(normalizedTitle) != topic:
                continue
            content = str(record["section_content"] or "")
            for block in POLARS_SPLIT.splitMarkdownBlocks(content):
                rows.append(
                    {
                        "blockOrder": blockOrder,
                        "blockType": str(block["blockType"]),
                        "source": "docs",
                        "2025": str(block["blockText"]),
                    }
                )
                blockOrder += 1
        if rows:
            return POLARS_SPLIT.buildBlockIndex(pl.DataFrame(rows))
    return None


def buildTopicsArrow(company) -> pl.DataFrame:
    docsMeta = buildDocsMetaArrow(company.stockCode)
    reportTopics = {POLARS_SPLIT.reportUserTopic(apiType) for apiType in fastAvailableApiTypesArrow(company.stockCode)}
    rows: list[dict[str, Any]] = []
    for topic in docsMeta["topicOrder"]:
        meta = docsMeta["topicMeta"][topic]
        sources = ["docs"]
        if topic in reportTopics:
            sources.append("report")
        rows.append(
            {"topic": topic, "source": ",".join(sources), "blocks": meta["blocks"], "periods": len(meta["periods"])}
        )
    if company._hasFinance:
        for topic in ("BS", "IS", "CIS", "CF", "SCE"):
            df = company._showFinanceTopic(topic)
            if df is None:
                continue
            rows.append(
                {"topic": topic, "source": "finance", "blocks": 1, "periods": len([c for c in df.columns if str(c).startswith('20')])}
            )
    return pl.DataFrame(rows) if rows else pl.DataFrame({"topic": [], "source": [], "blocks": [], "periods": []})


def buildIndexArrow(company) -> pl.DataFrame:
    docsMeta = buildDocsMetaArrow(company.stockCode)
    periodRange = POLARS_SPLIT.formatPeriodRange(docsMeta["allPeriods"], descending=True, annualAsQ4=True)
    rows: list[dict[str, Any]] = []
    rows.extend(company._indexFinanceRows())
    for rowIdx, topic in enumerate(docsMeta["topicOrder"]):
        meta = docsMeta["topicMeta"][topic]
        latestPeriod = POLARS_SPLIT.sortPeriods(list(meta["periods"]), descending=True)[0]
        chapter = meta["chapter"] or company._chapterForTopic(topic)
        rows.append(
            {
                "chapter": POLARS_SPLIT._CHAPTER_TITLES.get(chapter, chapter),
                "topic": topic,
                "label": company._topicLabel(topic),
                "kind": "docs",
                "source": "docs",
                "periods": periodRange,
                "shape": f"{len(meta['periods'])}기간",
                "preview": f"{POLARS_SPLIT.displayPeriod(latestPeriod, annualAsQ4=True)}: {meta['previewByPeriod'].get(latestPeriod, '-')}",
                "_sortKey": (POLARS_SPLIT._CHAPTER_ORDER.get(chapter, 12), 100 + rowIdx),
            }
        )
    rows.extend(POLARS_SPLIT.buildIndexReportRowsFast(company, existingTopics={row["topic"] for row in rows}))
    rows.sort(key=lambda row: row.get("_sortKey", (99, 999)))
    for row in rows:
        row.pop("_sortKey", None)
    return pl.DataFrame(rows)


def runPyarrowScannerCase(stockCode: str, caseName: str, topic: str | None) -> tuple[Any, dict[str, Any]]:
    import dartlab

    company = dartlab.Company(stockCode)
    if caseName == "availableApiTypes":
        payload: Any = fastAvailableApiTypesArrow(stockCode)
    elif caseName == "topics":
        payload = buildTopicsArrow(company)
    elif caseName == "index":
        payload = buildIndexArrow(company)
    elif caseName == "showCompanyOverview":
        payload = buildDocsTopicBlockIndexArrow(stockCode, "companyOverview")
    elif caseName == "showBusinessOverview":
        payload = buildDocsTopicBlockIndexArrow(stockCode, "businessOverview")
    else:
        raise ValueError(f"metadataDocs 실험에 없는 caseName: {caseName}")
    return payload, {"hasSectionsCache": "_sections" in company._cache, "reportTopic": topic}


def childMain() -> None:
    BASELINE.childMain(runPyarrowScannerCase)


def main() -> None:
    if "--child" in sys.argv:
        childMain()
        return
    parser = argparse.ArgumentParser()
    parser.add_argument("--child", action="store_true")
    parser.add_argument("--mode", default="pyarrowScanner")
    parser.add_argument("--caseGroup", default="metadataDocs", choices=["metadataDocs"])
    args = parser.parse_args()
    baselineRows = BASELINE.collectMode(Path(__file__).with_name("001_baselineHarness.py"), "baseline", "metadataDocs")
    candidateRows = BASELINE.collectMode(Path(__file__), "pyarrowScanner", "metadataDocs")
    BASELINE.printSummary("pyarrowScanner / metadataDocs", candidateRows)
    BASELINE.printComparisonSummary(
        "pyarrowScanner vs baseline / metadataDocs",
        BASELINE.compareRuns(baselineRows, candidateRows),
    )


if __name__ == "__main__":
    main()
