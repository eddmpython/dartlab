"""
실험 ID: 064-009
실험명: no_items 실패 원인 심층 분석

목적:
- no_items 31,965건의 근본 원인을 정밀 분류
- 수평화 가능한데 실패하는 케이스 vs 정상 스킵 구분
- 개선 가능한 패턴 식별

방법:
1. 핵심 topic의 no_items 블록에서 원본 마크다운 분석
2. struct_skip (headerCells==1) / quarter_only_multi_year / all_junk 등 세분류

결과 (실험 후 작성):
-

결론:
-

실험일: 2026-03-17
"""

import sys
import re
from collections import defaultdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "src"))

import polars as pl

from dartlab.engines.dart.docs.sections.pipeline import sections
from dartlab.engines.dart.docs.sections.tableParser import (
    splitSubtables,
    _headerCells,
    _isJunk,
    _dataRows,
    _classifyStructure,
    _parseMultiYear,
    _parseKeyValueOrMatrix,
)


def _isPeriodCol(c: str) -> bool:
    return bool(re.match(r"^\d{4}(Q[1-4])?$", c))


def analyzeNoItems(sec: pl.DataFrame, topic: str, bo: int, periodCols: list[str]) -> dict:
    """no_items인 table 블록의 근본 원인을 분류."""
    topicFrame = sec.filter(pl.col("topic") == topic)
    boRow = topicFrame.filter(
        (pl.col("blockOrder") == bo) & (pl.col("blockType") == "table")
    )
    if boRow.is_empty():
        return {"sub_reason": "empty_row"}

    total_subs = 0
    struct_counts = defaultdict(int)
    all_reasons = []
    sample_md = None
    multi_year_quarter_only = 0
    multi_year_annual_noparse = 0
    header_1col = 0

    for p in periodCols:
        md = boRow[p][0] if p in boRow.columns else None
        if md is None:
            continue
        if sample_md is None:
            sample_md = str(md)[:300]
        m = re.match(r"\d{4}", p)
        if m is None:
            continue
        pYear = int(m.group())
        isQuarter = "Q" in p

        for sub in splitSubtables(str(md)):
            total_subs += 1
            hc = _headerCells(sub)

            if _isJunk(hc):
                all_reasons.append("junk")
                continue

            dr = _dataRows(sub)
            if not dr:
                all_reasons.append("no_data_rows")
                continue

            structType = _classifyStructure(hc)
            struct_counts[structType] += 1

            if structType == "skip":
                if len(hc) == 1:
                    header_1col += 1
                    all_reasons.append("single_col_header")
                else:
                    all_reasons.append("struct_skip")
                continue

            if structType == "multi_year":
                if isQuarter:
                    multi_year_quarter_only += 1
                    all_reasons.append("multi_year_quarter")
                else:
                    triples, _ = _parseMultiYear(sub, pYear)
                    if not triples:
                        multi_year_annual_noparse += 1
                        all_reasons.append("multi_year_noparse")
                    else:
                        # 파싱은 됐는데 당기값이 없음
                        current_year = [t for t in triples if t[1] == str(pYear)]
                        if not current_year:
                            all_reasons.append("multi_year_no_current")
                        else:
                            all_reasons.append("multi_year_ok_but_filtered")

            elif structType in ("key_value", "matrix"):
                rows, _, _ = _parseKeyValueOrMatrix(sub)
                if not rows:
                    all_reasons.append("kv_matrix_noparse")
                else:
                    all_reasons.append("kv_matrix_ok_but_filtered")

    # 주 원인 결정
    reason_counts = defaultdict(int)
    for r in all_reasons:
        reason_counts[r] += 1

    main_reason = max(reason_counts.items(), key=lambda x: x[1])[0] if reason_counts else "unknown"

    return {
        "sub_reason": main_reason,
        "reason_counts": dict(reason_counts),
        "total_subs": total_subs,
        "struct_counts": dict(struct_counts),
        "header_1col": header_1col,
        "multi_year_quarter_only": multi_year_quarter_only,
        "multi_year_annual_noparse": multi_year_annual_noparse,
        "sample_md": sample_md,
    }


if __name__ == "__main__":
    from dartlab.core.dataLoader import _dataDir

    dataDir = _dataDir("docs")
    files = sorted(dataDir.glob("*.parquet"))
    codes = [f.stem for f in files]

    # 핵심 topic에서 no_items 케이스만 분석
    key_topics = ["dividend", "audit", "executivePay", "riskDerivative",
                  "companyOverview", "employee", "salesOrder"]

    print(f"no_items 심층 분석: {len(codes)}종목 × {len(key_topics)} topics")
    print("=" * 70)

    sub_reasons = defaultdict(lambda: defaultdict(int))
    total_by_topic = defaultdict(int)
    samples = defaultdict(list)

    for i, code in enumerate(codes):
        try:
            sec = sections(code)
        except Exception:
            continue
        if sec is None:
            continue

        periodCols = [c for c in sec.columns if _isPeriodCol(c)]

        for topic in key_topics:
            topicFrame = sec.filter(pl.col("topic") == topic)
            tableRows = topicFrame.filter(pl.col("blockType") == "table")
            if tableRows.is_empty():
                continue

            blockOrders = sorted(tableRows["blockOrder"].unique().to_list())
            for bo in blockOrders:
                boRow = topicFrame.filter(
                    (pl.col("blockOrder") == bo) & (pl.col("blockType") == "table")
                )
                if boRow.is_empty():
                    continue

                # _horizontalizeTableBlock 로직 재현 (간략)
                _SUFFIX_RE = re.compile(r"(사업)?부문$")
                _KISU_RE = re.compile(r"제\d+기\s*(?:\d*분기)?\s*\(?(당기|전기|전전기|당반기|전반기)\)?")

                allItems = []
                seenItems = set()

                for p in periodCols:
                    md = boRow[p][0] if p in boRow.columns else None
                    if md is None:
                        continue
                    m = re.match(r"\d{4}", p)
                    if m is None:
                        continue
                    pYear = int(m.group())

                    for sub in splitSubtables(str(md)):
                        hc = _headerCells(sub)
                        if _isJunk(hc):
                            continue
                        dr = _dataRows(sub)
                        if not dr:
                            continue
                        structType = _classifyStructure(hc)

                        if structType == "multi_year" and "Q" not in p:
                            triples, _ = _parseMultiYear(sub, pYear)
                            for rawItem, year, val in triples:
                                item_name = _SUFFIX_RE.sub("", rawItem).strip()
                                m2 = _KISU_RE.search(item_name)
                                if m2:
                                    item_name = m2.group(1)
                                if year == str(pYear):
                                    if item_name not in seenItems:
                                        allItems.append(item_name)
                                        seenItems.add(item_name)
                        elif structType in ("key_value", "matrix"):
                            rows, _, _ = _parseKeyValueOrMatrix(sub)
                            for rawItem, vals in rows:
                                item_name = _SUFFIX_RE.sub("", rawItem).strip()
                                m2 = _KISU_RE.search(item_name)
                                if m2:
                                    item_name = m2.group(1)
                                val = " | ".join(v for v in vals if v).strip()
                                if val and item_name not in seenItems:
                                    allItems.append(item_name)
                                    seenItems.add(item_name)

                # 필터링
                def _isJunkItem(name):
                    stripped = re.sub(r"[,.\-\s]", "", name)
                    return stripped.isdigit() or not stripped

                allItems = [item for item in allItems if not _isJunkItem(item)]

                if len(allItems) == 0:
                    # no_items — 원인 분석
                    result = analyzeNoItems(sec, topic, bo, periodCols)
                    sub_reasons[topic][result["sub_reason"]] += 1
                    total_by_topic[topic] += 1
                    if len(samples[topic]) < 3 and result.get("sample_md"):
                        samples[topic].append({
                            "code": code, "bo": bo,
                            "sub_reason": result["sub_reason"],
                            "reason_counts": result["reason_counts"],
                            "sample_md": result["sample_md"][:200],
                        })

        if (i + 1) % 50 == 0:
            print(f"  [{i+1}/{len(codes)}]...")

    print(f"\n{'='*70}")
    print("topic별 no_items 세부 원인")
    print(f"{'='*70}")
    for topic in key_topics:
        if topic not in sub_reasons:
            continue
        total = total_by_topic[topic]
        print(f"\n{topic}: {total}건")
        for reason, count in sorted(sub_reasons[topic].items(), key=lambda x: -x[1]):
            pct = count * 100 / total if total else 0
            print(f"  {reason}: {count}건 ({pct:.0f}%)")

    print(f"\n{'='*70}")
    print("샘플 마크다운")
    print(f"{'='*70}")
    for topic in key_topics:
        if topic not in samples:
            continue
        print(f"\n--- {topic} ---")
        for s in samples[topic]:
            print(f"  {s['code']} bo={s['bo']} reason={s['sub_reason']}")
            print(f"  counts={s['reason_counts']}")
            print(f"  md: {s['sample_md'][:150]}")
