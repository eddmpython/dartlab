"""
실험 ID: 002
실험명: Polars-only route split

목적:
- `sections/profile.facts`를 만들지 않고 raw docs/report + 기존 finance/report helper만으로
  metadata, authoritative topic, docs block index를 재현할 수 있는지 검증

가설:
1. `show("BS")`, `trace("BS")`, `availableApiTypes`, `index`, `topics`는 full sections 없이 크게 가벼워진다
2. docs topic `show()`는 latest-topic block index만으로 baseline과 상당 부분 동일하게 나올 수 있다
3. `_sections` cache를 만들지 않아도 public payload 상당수를 재현할 수 있다

방법:
1. 001 baseline harness를 import해 동일한 case matrix를 사용
2. raw docs/report는 필요한 컬럼만 `loadData(..., columns=...)`로 읽는다
3. finance/report payload는 기존 private helper를 그대로 사용한다
4. docs metadata/topics/index는 raw docs loop로 재구성한다
5. baseline과 payload digest, 시간, 피크 RSS를 비교한다

결과 (실험 후 작성):
- 총 60개 case를 baseline과 동일 조건으로 비교
- exact match: 21/60
- 6/6 exact: `init`, `availableApiTypes`, `trace("BS")`
- 3/6 exact: `show("BS")` (005930, 000660, 105560만 동일)
- `_sections` cache: 60/60 케이스에서 생성되지 않음
- availableApiTypes: 26.44~37.08x faster, peak 54.0~76.7% 절감
- trace("BS"): 45.34~78.99x faster, peak 81.7~87.1% 절감
- exact match가 난 `show("BS")` 구간은 36.03~56.54x faster, peak 75.9~80.6% 절감
- exact는 아니지만 `topics`도 6.60~10.41x faster, peak 58.2~66.3% 절감
- exact는 아니지만 docs `show()`는 30.16~56.23x faster, peak 61.0~73.7% 절감
- exact는 아니지만 report `show/trace`는 61~109x 수준으로 크게 빨라짐
- 약한 구간은 `index`: 4.52~6.57x faster이지만 peak 절감은 23.6~42.0%에 그침

결론:
- **부분 채택 가치가 매우 높다**
- `availableApiTypes`, finance authoritative `trace("BS")`, 일부 `show("BS")`는 결과 동일 + 속도/메모리 절감이 동시에 성립했다
- 그러나 `topics`, `index`, docs `show()`, report `trace()`는 아직 payload가 baseline과 다르다
- 결론적으로 `route split` 자체는 정답이고, exact 문제는 docs/report payload 재구성 세부 로직에서 남아 있다

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


BASELINE = _loadModule(Path(__file__).with_name("001_baselineHarness.py"), "exp089Baseline")

from dartlab.core.dataLoader import loadData
from dartlab.core.reportSelector import selectReport
from dartlab.engines.common.show import buildBlockIndex
from dartlab.engines.company.dart._report_accessor import reportFrameInner
from dartlab.engines.company.dart._utils import _shapeString
from dartlab.engines.company.dart.company import (
    _CHAPTER_ORDER,
    _CHAPTER_TITLES,
    _REPORT_TOPIC_TO_API_TYPE,
)
from dartlab.engines.company.dart.docs.sections import displayPeriod, formatPeriodRange, sortPeriods
from dartlab.engines.company.dart.docs.sections._common import REPORT_KINDS
from dartlab.engines.company.dart.docs.sections.chunker import parseMajorNum
from dartlab.engines.company.dart.docs.sections.mapper import mapSectionTitle
from dartlab.engines.company.dart.docs.sections.views import normalizeTitle, splitMarkdownBlocks


def _chapterFromMajor(majorNum: int | None) -> str | None:
    if majorNum is None or majorNum < 1 or majorNum > 12:
        return None
    return list(_CHAPTER_TITLES.keys())[majorNum - 1]


def fastAvailableApiTypes(stockCode: str) -> list[str]:
    from dartlab.engines.company.dart.report.types import API_TYPES

    df = loadData(stockCode, category="report", columns=["apiType"])
    if df is None or df.is_empty() or "apiType" not in df.columns:
        return []
    available = {str(value) for value in df["apiType"].drop_nulls().unique().to_list()}
    return [name for name in API_TYPES if name in available]


def reportUserTopic(apiType: str) -> str:
    return "audit" if apiType == "auditOpinion" else apiType


def iterMinimalDocsSubsets(stockCode: str):
    df = loadData(
        stockCode,
        category="docs",
        sinceYear=2016,
        columns=["year", "report_type", "rcept_date", "section_order", "section_title", "section_content"],
    )
    years = sorted(df["year"].unique().to_list(), reverse=True)
    for year in years:
        for reportKind, suffix in REPORT_KINDS:
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


def buildDocsMeta(stockCode: str) -> dict[str, Any]:
    topicOrder: list[str] = []
    topicMeta: dict[str, dict[str, Any]] = {}
    allPeriods: list[str] = []

    for periodKey, subset in iterMinimalDocsSubsets(stockCode):
        allPeriods.append(periodKey)
        for record in subset.iter_rows(named=True):
            title = str(record["section_title"] or "")
            normalizedTitle = normalizeTitle(title)
            if not normalizedTitle:
                continue
            topic = mapSectionTitle(normalizedTitle)
            if not topic:
                continue
            meta = topicMeta.setdefault(
                topic,
                {
                    "periods": set(),
                    "blocks": 0,
                    "chapter": _chapterFromMajor(parseMajorNum(title)),
                    "previewByPeriod": {},
                },
            )
            if topic not in topicOrder:
                topicOrder.append(topic)
            meta["periods"].add(periodKey)
            if meta["chapter"] is None:
                meta["chapter"] = _chapterFromMajor(parseMajorNum(title))
            content = str(record["section_content"] or "")
            meta["blocks"] += len(splitMarkdownBlocks(content))
            if periodKey not in meta["previewByPeriod"]:
                previewText = content.replace("\n", " ").strip()[:80]
                if previewText:
                    meta["previewByPeriod"][periodKey] = previewText

    return {
        "topicOrder": topicOrder,
        "topicMeta": topicMeta,
        "allPeriods": sortPeriods(list(dict.fromkeys(allPeriods)), descending=True),
    }


def buildDocsTopicBlockIndex(stockCode: str, topic: str) -> pl.DataFrame | None:
    for _periodKey, subset in iterMinimalDocsSubsets(stockCode):
        rows: list[dict[str, Any]] = []
        blockOrder = 0
        for record in subset.iter_rows(named=True):
            title = str(record["section_title"] or "")
            normalizedTitle = normalizeTitle(title)
            if not normalizedTitle or mapSectionTitle(normalizedTitle) != topic:
                continue
            content = str(record["section_content"] or "")
            for block in splitMarkdownBlocks(content):
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
            return buildBlockIndex(pl.DataFrame(rows))
    return None


def buildTopicsFast(company) -> pl.DataFrame:
    docsMeta = buildDocsMeta(company.stockCode)
    reportTopics = {reportUserTopic(apiType) for apiType in fastAvailableApiTypes(company.stockCode)}
    rows: list[dict[str, Any]] = []
    for topic in docsMeta["topicOrder"]:
        meta = docsMeta["topicMeta"][topic]
        sources = ["docs"]
        if topic in reportTopics:
            sources.append("report")
        rows.append(
            {
                "topic": topic,
                "source": ",".join(sources),
                "blocks": meta["blocks"],
                "periods": len(meta["periods"]),
            }
        )

    if company._hasFinance:
        for topic in ("BS", "IS", "CIS", "CF", "SCE"):
            df = company._showFinanceTopic(topic)
            if df is None:
                continue
            rows.append(
                {
                    "topic": topic,
                    "source": "finance",
                    "blocks": 1,
                    "periods": len([column for column in df.columns if str(column).startswith("20")]),
                }
            )
        if company._ratioSeries() is not None:
            ratioDf = company._showFinanceTopic("ratios")
            rows.append(
                {
                    "topic": "ratios",
                    "source": "finance",
                    "blocks": 1,
                    "periods": 0 if ratioDf is None else len([column for column in ratioDf.columns if str(column).startswith("20")]),
                }
            )
    return pl.DataFrame(rows) if rows else pl.DataFrame({"topic": [], "source": [], "blocks": [], "periods": []})


def buildIndexDocsRowsFast(company) -> list[dict[str, Any]]:
    docsMeta = buildDocsMeta(company.stockCode)
    periodRange = formatPeriodRange(docsMeta["allPeriods"], descending=True, annualAsQ4=True)
    rows: list[dict[str, Any]] = []
    for rowIdx, topic in enumerate(docsMeta["topicOrder"]):
        meta = docsMeta["topicMeta"][topic]
        latestPeriods = sortPeriods(list(meta["periods"]), descending=True)
        latestPeriod = latestPeriods[0] if latestPeriods else None
        previewText = meta["previewByPeriod"].get(latestPeriod, "-")
        preview = "-" if latestPeriod is None else f"{displayPeriod(latestPeriod, annualAsQ4=True)}: {previewText}"
        chapter = meta["chapter"] or company._chapterForTopic(topic)
        chapterNum = _CHAPTER_ORDER.get(chapter, 12)
        rows.append(
            {
                "chapter": _CHAPTER_TITLES.get(chapter, chapter),
                "topic": topic,
                "label": company._topicLabel(topic),
                "kind": "docs",
                "source": "docs",
                "periods": periodRange,
                "shape": f"{len(meta['periods'])}기간",
                "preview": preview,
                "_sortKey": (chapterNum, 100 + rowIdx),
            }
        )
    return rows


def buildIndexReportRowsFast(company, existingTopics: set[str]) -> list[dict[str, Any]]:
    from dartlab.engines.company.dart.report.types import API_TYPE_LABELS

    rows: list[dict[str, Any]] = []
    for rIdx, apiType in enumerate(fastAvailableApiTypes(company.stockCode)):
        topic = reportUserTopic(apiType)
        if topic in existingTopics:
            continue
        try:
            df = reportFrameInner(company.stockCode, apiType, topic, raw=False)
        except (
            pl.exceptions.ColumnNotFoundError,
            pl.exceptions.InvalidOperationError,
            pl.exceptions.SchemaError,
            RuntimeError,
        ):
            df = None
        if df is None or df.is_empty():
            continue
        chapter = company._chapterForTopic(topic)
        chapterNum = _CHAPTER_ORDER.get(chapter, 12)
        rows.append(
            {
                "chapter": _CHAPTER_TITLES.get(chapter, chapter),
                "topic": topic,
                "label": API_TYPE_LABELS.get(apiType, apiType),
                "kind": "report",
                "source": "report",
                "periods": "-",
                "shape": _shapeString(df),
                "preview": API_TYPE_LABELS.get(apiType, apiType),
                "_sortKey": (chapterNum, 200 + rIdx),
            }
        )
    return rows


def buildIndexFast(company) -> pl.DataFrame:
    rows: list[dict[str, Any]] = []
    rows.extend(company._indexFinanceRows())
    rows.extend(buildIndexDocsRowsFast(company))
    rows.extend(buildIndexReportRowsFast(company, existingTopics={row["topic"] for row in rows}))
    rows.sort(key=lambda row: row.get("_sortKey", (99, 999)))
    for row in rows:
        row.pop("_sortKey", None)
    if rows:
        return pl.DataFrame(rows)
    return pl.DataFrame(
        {
            "chapter": [],
            "topic": [],
            "label": [],
            "kind": [],
            "source": [],
            "periods": [],
            "shape": [],
            "preview": [],
        }
    )


def buildFinanceTraceFast(company, topic: str) -> dict[str, Any] | None:
    rows: list[dict[str, Any]] = []
    if topic in {"BS", "IS", "CF"}:
        annual = company.finance.annual
        if annual is None:
            return None
        series, years = annual
        stmt = series.get(topic, {})
        for item, values in stmt.items():
            for idx, year in enumerate(years):
                value = values[idx] if idx < len(values) else None
                if value is None:
                    continue
                rows.append({"payloadRef": f"finance:{topic}:{item}", "summary": f"{item}={value}"})
    else:
        return None
    if not rows:
        return None
    primary = rows[0]
    return {
        "topic": topic,
        "period": None,
        "primarySource": "finance",
        "fallbackSources": [],
        "selectedPayloadRef": primary["payloadRef"],
        "availableSources": [
            {
                "source": "finance",
                "rows": len(rows),
                "payloadRef": primary["payloadRef"],
                "summary": primary["summary"],
                "priority": 300,
            }
        ],
        "whySelected": "finance authoritative priority",
    }


def buildReportTraceFast(company, topic: str) -> dict[str, Any] | None:
    apiType = _REPORT_TOPIC_TO_API_TYPE.get(topic, topic)
    df = company.report.extractAnnual(apiType)
    if df is None or df.is_empty():
        return None
    rows: list[dict[str, Any]] = []
    for record in df.iter_rows(named=True):
        quarter = record.get("quarter")
        summaryParts: list[str] = []
        for key, value in record.items():
            if key in {"stockCode", "year", "quarter", "quarterNum", "apiType", "stlm_dt"}:
                continue
            if value is None:
                continue
            summaryParts.append(f"{key}={value}")
        if summaryParts:
            rows.append(
                {
                    "source": "report",
                    "rows": len(summaryParts),
                    "payloadRef": f"report:{apiType}:{quarter}",
                    "summary": "; ".join(summaryParts[:6]),
                    "priority": 200,
                }
            )
    if not rows:
        return None
    primary = rows[0]
    return {
        "topic": topic,
        "period": None,
        "primarySource": "report",
        "fallbackSources": [],
        "selectedPayloadRef": primary["payloadRef"],
        "availableSources": [
            {
                "source": "report",
                "rows": sum(row["rows"] for row in rows),
                "payloadRef": primary["payloadRef"],
                "summary": primary["summary"],
                "priority": 200,
            }
        ],
        "whySelected": "report authoritative priority",
    }


def runPolarsRouteSplitCase(stockCode: str, caseName: str, topic: str | None) -> tuple[Any, dict[str, Any]]:
    import dartlab

    company = dartlab.Company(stockCode)
    if caseName == "init":
        payload: Any = {"stockCode": company.stockCode, "corpName": company.corpName}
    elif caseName == "availableApiTypes":
        payload = fastAvailableApiTypes(stockCode)
    elif caseName == "topics":
        payload = buildTopicsFast(company)
    elif caseName == "index":
        payload = buildIndexFast(company)
    elif caseName == "showBS":
        payload = company._showFinanceTopic("BS")
    elif caseName == "traceBS":
        payload = buildFinanceTraceFast(company, "BS")
    elif caseName == "showCompanyOverview":
        payload = buildDocsTopicBlockIndex(stockCode, "companyOverview")
    elif caseName == "showBusinessOverview":
        payload = buildDocsTopicBlockIndex(stockCode, "businessOverview")
    elif caseName == "showReportTopic":
        payload = company._showReportTopic(topic)
    elif caseName == "traceReportTopic":
        payload = buildReportTraceFast(company, topic)
    else:
        raise ValueError(f"알 수 없는 caseName: {caseName}")
    return payload, {"hasSectionsCache": "_sections" in company._cache, "reportTopic": topic}


def childMain() -> None:
    BASELINE.childMain(runPolarsRouteSplitCase)


def main() -> None:
    if "--child" in sys.argv:
        childMain()
        return
    parser = argparse.ArgumentParser()
    parser.add_argument("--child", action="store_true")
    parser.add_argument("--mode", default="polarsRouteSplit")
    parser.add_argument("--caseGroup", default="all", choices=["all", "metadataDocs", "docsOnly", "authoritative"])
    args = parser.parse_args()
    baselineRows = BASELINE.collectMode(Path(__file__).with_name("001_baselineHarness.py"), "baseline", args.caseGroup)
    candidateRows = BASELINE.collectMode(Path(__file__), "polarsRouteSplit", args.caseGroup)
    BASELINE.printSummary(f"polarsRouteSplit / {args.caseGroup}", candidateRows)
    BASELINE.printComparisonSummary(
        f"polarsRouteSplit vs baseline / {args.caseGroup}",
        BASELINE.compareRuns(baselineRows, candidateRows),
    )


if __name__ == "__main__":
    main()
