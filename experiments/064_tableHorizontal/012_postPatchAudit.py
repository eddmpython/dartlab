"""
실험 ID: 064-012
실험명: 패치 후 283종목 전수 품질 점검

목적:
- _stripUnitHeader 패치 후 성공률 변화 측정
- 핵심 topic별 성공률 비교
- 회귀 확인

실험일: 2026-03-17
"""

import sys
import re
from collections import defaultdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "src"))

import polars as pl

from dartlab.engines.company.dart.docs.sections.pipeline import sections
from dartlab.engines.company.dart.docs.sections.tableParser import (
    splitSubtables,
    _headerCells,
    _isJunk,
    _dataRows,
    _classifyStructure,
    _parseMultiYear,
    _parseKeyValueOrMatrix,
)
from dartlab.engines.company.dart.company import Company


def _isPeriodCol(c: str) -> bool:
    return bool(re.match(r"^\d{4}(Q[1-4])?$", c))


def auditStockPatched(code: str) -> list[dict]:
    """패치된 _horizontalizeTableBlock을 사용한 품질 점검."""
    results = []

    try:
        sec = sections(code)
    except Exception as e:
        return [{"code": code, "error": str(e)}]
    if sec is None:
        return [{"code": code, "error": "sections None"}]

    periodCols = [c for c in sec.columns if _isPeriodCol(c)]
    topics = sec["topic"].unique().to_list()

    # Company 인스턴스 생성 (패치된 _horizontalizeTableBlock 사용)
    try:
        c = Company(code)
    except Exception as e:
        return [{"code": code, "error": str(e)}]

    for topic in topics:
        topicFrame = sec.filter(pl.col("topic") == topic)
        tableRows = topicFrame.filter(pl.col("blockType") == "table")
        if tableRows.is_empty():
            continue

        blockOrders = sorted(tableRows["blockOrder"].unique().to_list())
        for bo in blockOrders:
            try:
                result = c._horizontalizeTableBlock(topicFrame, bo, periodCols)
                success = result is not None
            except Exception as e:
                success = False

            results.append({
                "code": code,
                "topic": topic,
                "blockOrder": bo,
                "success": success,
            })

    return results


if __name__ == "__main__":
    from dartlab.core.dataLoader import _dataDir

    dataDir = _dataDir("docs")
    files = sorted(dataDir.glob("*.parquet"))
    codes = [f.stem for f in files]

    print(f"패치 후 품질 점검: {len(codes)}종목")
    print("=" * 70)

    allResults = []
    errorCodes = []

    for i, code in enumerate(codes):
        try:
            results = auditStockPatched(code)
            if results and "error" in results[0]:
                errorCodes.append(code)
                continue
            allResults.extend(results)
        except Exception as e:
            errorCodes.append(code)
            continue

        if (i + 1) % 50 == 0:
            print(f"  [{i+1}/{len(codes)}] 완료... ({len(allResults)} blocks)")

    print(f"\n총 {len(allResults)} table 블록")
    print(f"에러 종목: {len(errorCodes)}")
    if errorCodes:
        print(f"  에러 종목: {errorCodes[:10]}")

    successCount = sum(1 for r in allResults if r["success"])
    failCount = sum(1 for r in allResults if not r["success"])
    total = len(allResults)
    print(f"  수평화 성공: {successCount} ({successCount*100/total:.1f}%)")
    print(f"  수평화 None: {failCount} ({failCount*100/total:.1f}%)")

    # 핵심 topic별 성공률
    print(f"\n{'='*70}")
    print("핵심 topic별 성공률")
    print(f"{'='*70}")
    key_topics = ["dividend", "audit", "salesOrder", "companyOverview", "employee",
                  "majorHolder", "shareCapital", "executivePay", "rawMaterial", "riskDerivative"]
    for topic in key_topics:
        topic_results = [r for r in allResults if r["topic"] == topic]
        if not topic_results:
            continue
        ok = sum(1 for r in topic_results if r["success"])
        total_t = len(topic_results)
        print(f"  {topic}: {ok}/{total_t} ({ok*100/total_t:.0f}%)")
