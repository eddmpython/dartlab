"""
실험 ID: 064-014
실험명: 실제 company.py _horizontalizeTableBlock을 통한 None 비율 측정

목적:
- 012는 tableParser 함수만 직접 사용해서 _stripUnitHeader 패치 미반영
- 실제 company.py 경로를 통한 정확한 None 비율 측정

방법:
1. DartCompany 인스턴스를 사용하여 show(topic, block) 호출
2. 또는 _horizontalizeTableBlock 직접 호출

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
from dartlab.engines.company.dart.company import Company as DartCompany


def _isPeriodCol(c: str) -> bool:
    return bool(re.match(r"^\d{4}(Q[1-4])?$", c))


if __name__ == "__main__":
    from dartlab.core.dataLoader import _dataDir

    dataDir = _dataDir("docs")
    files = sorted(dataDir.glob("*.parquet"))
    codes = [f.stem for f in files]

    print(f"실제 _horizontalizeTableBlock 경로 None 비율 측정")
    print(f"종목 수: {len(codes)}")
    print("=" * 70)

    topic_stats = defaultdict(lambda: {"total": 0, "success": 0, "none": 0})
    failure_reasons = defaultdict(lambda: defaultdict(int))

    # _SUFFIX_RE / _KISU_RE 등은 company.py 내부와 동일
    _SUFFIX_RE = re.compile(r"(사업)?부문$")
    _KISU_RE = re.compile(r"제\d+기\s*(?:\d*분기)?\s*\(?(당기|전기|전전기|당반기|전반기)\)?")
    _UNIT_ONLY_RE = re.compile(r"^\(?\s*단위\s*[:/]?\s*[^)]*\)?\s*$")
    _BASEDATE_RE = re.compile(r"^\(?\s*기준일\s*:")

    for i, code in enumerate(codes):
        try:
            sec = sections(code)
        except (FileNotFoundError, ValueError):
            continue
        if sec is None:
            continue

        periodCols = [c for c in sec.columns if _isPeriodCol(c)]
        tableRows = sec.filter(pl.col("blockType") == "table")
        if tableRows.is_empty():
            continue

        # DartCompany 인스턴스 생성하여 _horizontalizeTableBlock 호출
        try:
            c = DartCompany(code)
        except (FileNotFoundError, ValueError, KeyError):
            continue

        topics_list = tableRows["topic"].unique().to_list()

        for topic in topics_list:
            topicFrame = sec.filter(pl.col("topic") == topic)
            tTableRows = topicFrame.filter(pl.col("blockType") == "table")
            blockOrders = sorted(tTableRows["blockOrder"].unique().to_list())

            for bo in blockOrders:
                topic_stats[topic]["total"] += 1

                try:
                    result = c._horizontalizeTableBlock(topicFrame, bo, periodCols)
                except Exception:
                    topic_stats[topic]["none"] += 1
                    failure_reasons[topic]["error"] += 1
                    continue

                if result is None:
                    topic_stats[topic]["none"] += 1

                    # 원인 분석 (012와 동일 방식)
                    boRow = topicFrame.filter(
                        (pl.col("blockOrder") == bo) & (pl.col("blockType") == "table")
                    )
                    reasons = defaultdict(int)
                    for p in periodCols:
                        md = boRow[p][0] if p in boRow.columns else None
                        if md is None:
                            continue
                        m = re.match(r"\d{4}", p)
                        if m is None:
                            continue
                        pYear = int(m.group())
                        isQ = "Q" in p
                        for sub in splitSubtables(str(md)):
                            hc = _headerCells(sub)
                            if _isJunk(hc):
                                reasons["junk_header"] += 1
                                continue
                            dr = _dataRows(sub)
                            if not dr:
                                reasons["no_data_rows"] += 1
                                continue
                            structType = _classifyStructure(hc)

                            if structType == "skip":
                                nonEmpty = [c2 for c2 in hc if c2.strip()]
                                if len(nonEmpty) == 1 and _UNIT_ONLY_RE.match(nonEmpty[0]):
                                    # _stripUnitHeader가 처리했을 것 → 이후 단계에서 걸림
                                    reasons["unit_header_post_strip"] += 1
                                elif len(nonEmpty) == 1 and _BASEDATE_RE.match(nonEmpty[0]):
                                    reasons["basedate_post_strip"] += 1
                                else:
                                    reasons["struct_skip_other"] += 1
                                continue

                            if structType == "multi_year":
                                if isQ:
                                    reasons["multi_year_quarter"] += 1
                                else:
                                    triples, _ = _parseMultiYear(sub, pYear)
                                    current = [t for t in triples if t[1] == str(pYear)]
                                    if not current:
                                        reasons["multi_year_no_current"] += 1
                                    else:
                                        reasons["multi_year_ok_but_filtered"] += 1
                            elif structType in ("key_value", "matrix"):
                                rows, _, _ = _parseKeyValueOrMatrix(sub)
                                if rows:
                                    reasons["kv_ok_but_filtered"] += 1
                                else:
                                    reasons["kv_noparse"] += 1

                    top = max(reasons.items(), key=lambda x: x[1])[0] if reasons else "unknown"
                    failure_reasons[topic][top] += 1
                else:
                    topic_stats[topic]["success"] += 1

        if (i + 1) % 50 == 0:
            print(f"  [{i+1}/{len(codes)}]...")

    # --- 결과 출력 ---
    print(f"\n{'='*70}")
    print("topic별 성공/None 비율 (빈도 상위 30)")
    print(f"{'='*70}")

    sorted_topics = sorted(topic_stats.items(), key=lambda x: x[1]["total"], reverse=True)
    for topic, stats in sorted_topics[:30]:
        total = stats["total"]
        success = stats["success"]
        none_ct = stats["none"]
        success_pct = success * 100 / total if total else 0
        none_pct = none_ct * 100 / total if total else 0
        print(f"  {topic:35s} total={total:5d}  success={success:5d}({success_pct:5.1f}%)  none={none_ct:5d}({none_pct:5.1f}%)")

    # 실패 원인
    print(f"\n{'='*70}")
    print("topic별 주요 실패 원인 (빈도 상위 15)")
    print(f"{'='*70}")
    for topic, stats in sorted_topics[:15]:
        if topic not in failure_reasons:
            continue
        reasons = failure_reasons[topic]
        total_fail = sum(reasons.values())
        print(f"\n  {topic} (실패 {total_fail}건):")
        for reason, count in sorted(reasons.items(), key=lambda x: -x[1])[:5]:
            pct = count * 100 / total_fail if total_fail else 0
            print(f"    {reason:35s} {count:5d} ({pct:.0f}%)")

    # 전체 요약
    total_blocks = sum(s["total"] for s in topic_stats.values())
    total_success = sum(s["success"] for s in topic_stats.values())
    total_none = sum(s["none"] for s in topic_stats.values())
    print(f"\n{'='*70}")
    print(f"전체 요약: {total_blocks} blocks, success={total_success}({total_success*100/total_blocks:.1f}%), none={total_none}({total_none*100/total_blocks:.1f}%)")
    print(f"{'='*70}")
