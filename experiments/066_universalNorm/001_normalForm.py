"""
실험 ID: 066-001
실험명: Universal Table Normalizer — 정규형 변환 실험

목적:
- 모든 마크다운 테이블을 (row_key, col_key, value) 정규형으로 변환
- 이력형, 정형, matrix 등 모든 구조에서 동일하게 동작하는지 확인
- 정규형 기반 수평화의 실용성 검증

핵심 아이디어:
- 마크다운 테이블의 첫 컬럼 = row_key (항목)
- 나머지 컬럼 = col_key (속성)
- 각 셀 = value
- 기간(period)별로 동일 (row_key, col_key) 쌍의 value를 나란히 배치

실험일: 2026-03-18
"""

import re
import sys

sys.path.insert(0, str(__import__("pathlib").Path(__file__).resolve().parents[2] / "src"))
import polars as pl

from dartlab.providers.dart.docs.sections.pipeline import sections
from dartlab.providers.dart.docs.sections.tableParser import (
    _dataRows,
    _headerCells,
    _isJunk,
    splitSubtables,
)


def normalize_table(md: str) -> list[dict]:
    """마크다운 테이블 → [(row_key, col_key, value), ...] 정규형."""
    facts = []
    for sub in splitSubtables(md):
        hc = _headerCells(sub)
        if _isJunk(hc) or len(hc) < 2:
            continue
        dr = _dataRows(sub)
        if not dr:
            continue

        # 첫 헤더 = row_key 이름, 나머지 = col_key 이름
        colNames = hc[1:]  # 나머지 컬럼명

        for row in dr:
            if not row or not row[0].strip():
                continue
            rowKey = row[0].strip()
            if rowKey.startswith("※") or rowKey.startswith("☞"):
                continue

            for ci, colName in enumerate(colNames):
                valIdx = ci + 1
                if valIdx < len(row):
                    val = row[valIdx].strip()
                    if val and val != "-":
                        facts.append({
                            "row_key": rowKey,
                            "col_key": colName.strip() if colName.strip() else f"col{ci+1}",
                            "value": val,
                        })
    return facts


def horizontalize_normal(factsByPeriod: dict[str, list[dict]]) -> pl.DataFrame | None:
    """기간별 정규형 facts → 수평화 DataFrame."""
    # (row_key, col_key) 쌍으로 기간별 값 수집
    allKeys: list[tuple[str, str]] = []
    seenKeys: set[tuple[str, str]] = set()
    keyPeriodVal: dict[tuple[str, str], dict[str, str]] = {}

    for period, facts in factsByPeriod.items():
        for f in facts:
            key = (f["row_key"], f["col_key"])
            if key not in seenKeys:
                allKeys.append(key)
                seenKeys.add(key)
            if key not in keyPeriodVal:
                keyPeriodVal[key] = {}
            keyPeriodVal[key][period] = f["value"]

    if not allKeys:
        return None

    # 사용된 기간
    usedPeriods = sorted(set(p for vals in keyPeriodVal.values() for p in vals))
    if not usedPeriods:
        return None

    rows = []
    for rk, ck in allKeys:
        row = {"row_key": rk, "col_key": ck}
        for p in usedPeriods:
            row[p] = keyPeriodVal.get((rk, ck), {}).get(p)
        rows.append(row)

    return pl.DataFrame(rows)


if __name__ == "__main__":
    pl.Config.set_tbl_cols(8)
    pl.Config.set_fmt_str_lengths(50)

    sec = sections("005930")
    periodCols = [c for c in sec.columns if re.match(r"^\d{4}(Q[1-4])?$", c)]

    # 다양한 topic/block에서 정규형 변환 테스트
    tests = [
        ("executivePay", 3, "정형 matrix"),
        ("companyHistory", 1, "이력형 — 이사 변동"),
        ("dividend", 5, "multi_year 숫자"),
        ("salesOrder", 1, "복잡 matrix"),
        ("boardOfDirectors", 1, "이사회 회의록"),
        ("employee", 1, "임원 목록"),
    ]

    topicFrame_cache = {}

    for topic, bo, desc in tests:
        print(f"\n{'='*60}")
        print(f"=== {topic} bo={bo} ({desc}) ===")

        topicFrame = sec.filter(pl.col("topic") == topic)
        boRow = topicFrame.filter(
            (pl.col("blockOrder") == bo) & (pl.col("blockType") == "table")
        )
        if boRow.is_empty():
            print("  블록 없음")
            continue

        # 기간별 정규형 추출
        factsByPeriod = {}
        for p in periodCols[-5:]:  # 최근 5기간만
            md = boRow[p][0] if p in boRow.columns else None
            if md is None:
                continue
            facts = normalize_table(str(md))
            if facts:
                factsByPeriod[p] = facts

        if not factsByPeriod:
            print("  데이터 없음")
            continue

        print(f"  기간: {list(factsByPeriod.keys())}")
        print(f"  기간별 fact 수: {[len(v) for v in factsByPeriod.values()]}")

        # 수평화
        result = horizontalize_normal(factsByPeriod)
        if result is not None:
            print(f"  수평화 결과: {result.shape}")
            print(result.head(8))
        else:
            print("  수평화 실패")
