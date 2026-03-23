"""
실험 ID: 005
실험명: DuckDB parquet_scan route

목적:
- Polars direct parquet read 대신 DuckDB `parquet_scan()` 경로가 metadata/docs hot path에 더 유리한지 검증

가설:
1. DuckDB relation + Arrow fetch로 필요한 컬럼만 읽으면 metadata/docs 경로 피크 메모리를 줄일 수 있다
2. downstream 로직을 002와 유지하면 payload 동일성 비교가 가능하다

방법:
1. `uv run --with duckdb --with psutil`로 실행한다
2. 001 baseline harness의 metadataDocs case group만 사용한다
3. docs/report raw scan만 DuckDB로 바꾸고 downstream 로직은 002와 동일하게 유지한다

결과 (실험 후 작성):
- 총 30개 case(6종목 × metadataDocs 5개) 비교
- exact match: 6/30
- exact가 난 것은 `availableApiTypes` 6종목뿐
- availableApiTypes: 3.26~6.00x faster, peak 39.5~67.4% 절감
- topics: 1.99~3.23x faster, peak -4.8~42.1% 절감, exact 0/6
- index: 1.79~2.61x faster, peak -10.9~29.8% 절감, exact 0/6
- docs `show()`: 3.96~7.08x faster지만, 005930에서는 baseline보다 peak가 더 높았다
- 005930 기준 `topics/index/show(companyOverview/showBusinessOverview)`는 peak 882~887MB까지 올라 PyArrow보다도 나빴다

결론:
- **기각**
- DuckDB는 availableApiTypes 하나만 보면 괜찮지만, 현재 실험 구조에서는 docs/meta path에서 memory advantage가 거의 없거나 역전되었다
- 이 repo의 병목은 SQL pushdown보다 이후 Python 재구성에 더 많이 걸려 있다는 증거다

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


BASELINE = _loadModule(Path(__file__).with_name("001_baselineHarness.py"), "exp089Baseline005")
POLARS_SPLIT = _loadModule(Path(__file__).with_name("002_polarsRouteSplit.py"), "exp089PolarsSplit005")

from dartlab.core.reportSelector import selectReport


def _duckdbConnect():
    try:
        import duckdb
    except ImportError as exc:  # pragma: no cover - runtime guard
        raise RuntimeError("duckdb가 필요합니다. `uv run --with duckdb --with psutil ...`로 실행하세요.") from exc
    return duckdb.connect()


def readReportApiFrameDuckdb(stockCode: str) -> pl.DataFrame:
    con = _duckdbConnect()
    path = ROOT / "data" / "dart" / "report" / f"{stockCode}.parquet"
    rows = con.execute("select apiType from parquet_scan(?)", [str(path)]).fetchall()
    return pl.DataFrame({"apiType": [row[0] for row in rows]})


def readDocsFrameDuckdb(stockCode: str) -> pl.DataFrame:
    con = _duckdbConnect()
    path = ROOT / "data" / "dart" / "docs" / f"{stockCode}.parquet"
    rows = con.execute(
        "select year, report_type, rcept_date, section_order, section_title, section_content from parquet_scan(?)",
        [str(path)],
    ).fetchall()
    return pl.DataFrame(
        rows,
        schema=["year", "report_type", "rcept_date", "section_order", "section_title", "section_content"],
        orient="row",
    )


def fastAvailableApiTypesDuckdb(stockCode: str) -> list[str]:
    from dartlab.engines.company.dart.report.types import API_TYPES

    df = readReportApiFrameDuckdb(stockCode)
    available = {str(value) for value in df["apiType"].drop_nulls().unique().to_list()}
    return [name for name in API_TYPES if name in available]


def iterMinimalDocsSubsetsDuckdb(stockCode: str):
    df = readDocsFrameDuckdb(stockCode)
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


def buildDocsMetaDuckdb(stockCode: str) -> dict[str, Any]:
    topicOrder: list[str] = []
    topicMeta: dict[str, dict[str, Any]] = {}
    allPeriods: list[str] = []
    for periodKey, subset in iterMinimalDocsSubsetsDuckdb(stockCode):
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


def buildDocsTopicBlockIndexDuckdb(stockCode: str, topic: str):
    for _periodKey, subset in iterMinimalDocsSubsetsDuckdb(stockCode):
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


def buildTopicsDuckdb(company) -> pl.DataFrame:
    docsMeta = buildDocsMetaDuckdb(company.stockCode)
    reportTopics = {POLARS_SPLIT.reportUserTopic(apiType) for apiType in fastAvailableApiTypesDuckdb(company.stockCode)}
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


def buildIndexDuckdb(company) -> pl.DataFrame:
    docsMeta = buildDocsMetaDuckdb(company.stockCode)
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


def runDuckdbScanCase(stockCode: str, caseName: str, topic: str | None) -> tuple[Any, dict[str, Any]]:
    import dartlab

    company = dartlab.Company(stockCode)
    if caseName == "availableApiTypes":
        payload: Any = fastAvailableApiTypesDuckdb(stockCode)
    elif caseName == "topics":
        payload = buildTopicsDuckdb(company)
    elif caseName == "index":
        payload = buildIndexDuckdb(company)
    elif caseName == "showCompanyOverview":
        payload = buildDocsTopicBlockIndexDuckdb(stockCode, "companyOverview")
    elif caseName == "showBusinessOverview":
        payload = buildDocsTopicBlockIndexDuckdb(stockCode, "businessOverview")
    else:
        raise ValueError(f"metadataDocs 실험에 없는 caseName: {caseName}")
    return payload, {"hasSectionsCache": "_sections" in company._cache, "reportTopic": topic}


def childMain() -> None:
    BASELINE.childMain(runDuckdbScanCase)


def main() -> None:
    if "--child" in sys.argv:
        childMain()
        return
    parser = argparse.ArgumentParser()
    parser.add_argument("--child", action="store_true")
    parser.add_argument("--mode", default="duckdbScan")
    parser.add_argument("--caseGroup", default="metadataDocs", choices=["metadataDocs"])
    args = parser.parse_args()
    baselineRows = BASELINE.collectMode(Path(__file__).with_name("001_baselineHarness.py"), "baseline", "metadataDocs")
    candidateRows = BASELINE.collectMode(Path(__file__), "duckdbScan", "metadataDocs")
    BASELINE.printSummary("duckdbScan / metadataDocs", candidateRows)
    BASELINE.printComparisonSummary(
        "duckdbScan vs baseline / metadataDocs",
        BASELINE.compareRuns(baselineRows, candidateRows),
    )


if __name__ == "__main__":
    main()
