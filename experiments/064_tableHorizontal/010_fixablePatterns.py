"""
실험 ID: 064-010
실험명: 개선 가능한 패턴 분석 + 수정안 검증

목적:
- single_col_header: 단위행이 헤더로 인식되는 패턴 → 실제 헤더 탐색
- kv_matrix_ok_but_filtered: 파싱은 됐지만 필터에서 걸린 패턴 → 필터 완화
- multi_year 분기 보고서 스킵: Q 기간 multi_year도 당기값 추출 가능

방법:
1. 각 패턴의 원본 마크다운 확인
2. 수정 로직 구현 + 검증
3. 10종목 핵심 topic 재검증

결과 (실험 후 작성):
-

결론:
-

실험일: 2026-03-17
"""

import sys
import re
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
    _normalizeItemName,
    _MULTI_YEAR_KW,
)


def _isPeriodCol(c: str) -> bool:
    return bool(re.match(r"^\d{4}(Q[1-4])?$", c))


# ── 패턴1: 단위행이 헤더로 인식되는 케이스 ──
def analyzeUnitHeader():
    """단위행+실제헤더 2행 패턴 분석."""
    print("=" * 70)
    print("패턴1: 단위행이 헤더로 인식 (single_col_header)")
    print("=" * 70)

    # riskDerivative 000020 bo=1
    sec = sections("000020")
    periodCols = [c for c in sec.columns if _isPeriodCol(c)]
    topicFrame = sec.filter(pl.col("topic") == "riskDerivative")
    boRow = topicFrame.filter(
        (pl.col("blockOrder") == 1) & (pl.col("blockType") == "table")
    )

    for p in ["2024", "2023"]:
        md = boRow[p][0] if p in boRow.columns and boRow[p][0] is not None else None
        if md is None:
            continue
        print(f"\n--- {p} 원본 (처음 500자) ---")
        print(str(md)[:500])

        for sub in splitSubtables(str(md)):
            hc = _headerCells(sub)
            print(f"\n  header: {hc}")
            print(f"  isJunk: {_isJunk(hc)}")
            print(f"  classify: {_classifyStructure(hc)}")

            # 서브테이블 전체 행 출력
            for i, line in enumerate(sub[:5]):
                print(f"  [{i}] {line[:100]}")
        break

    # salesOrder 000270 bo=1
    sec2 = sections("000270")
    topicFrame2 = sec2.filter(pl.col("topic") == "salesOrder")
    boRow2 = topicFrame2.filter(
        (pl.col("blockOrder") == 1) & (pl.col("blockType") == "table")
    )
    for p in ["2024", "2023"]:
        md = boRow2[p][0] if p in boRow2.columns and boRow2[p][0] is not None else None
        if md is None:
            continue
        print(f"\nsalesOrder 000270 {p}:")
        for sub in splitSubtables(str(md)):
            hc = _headerCells(sub)
            print(f"  header: {hc}")
            print(f"  isJunk: {_isJunk(hc)}")
            # 서브테이블 전체 행 출력
            for i, line in enumerate(sub[:5]):
                print(f"  [{i}] {line[:100]}")
        break


# ── 패턴2: kv_matrix 파싱 됐지만 필터에서 걸림 ──
def analyzeFilteredItems():
    """파싱은 됐지만 _isJunkItem에서 걸린 케이스."""
    print("\n" + "=" * 70)
    print("패턴2: kv_matrix 파싱 ok but filtered")
    print("=" * 70)

    # audit 000020 bo=9 — 감사위원회 소통내용
    sec = sections("000020")
    periodCols = [c for c in sec.columns if _isPeriodCol(c)]
    topicFrame = sec.filter(pl.col("topic") == "audit")
    boRow = topicFrame.filter(
        (pl.col("blockOrder") == 9) & (pl.col("blockType") == "table")
    )

    for p in ["2024", "2023"]:
        md = boRow[p][0] if p in boRow.columns and boRow[p][0] is not None else None
        if md is None:
            continue
        print(f"\naudit 000020 bo=9 {p}:")
        for sub in splitSubtables(str(md)):
            hc = _headerCells(sub)
            print(f"  header: {hc}")
            st = _classifyStructure(hc)
            print(f"  classify: {st}")
            if st in ("key_value", "matrix"):
                rows, headerNames, unit = _parseKeyValueOrMatrix(sub)
                print(f"  headerNames: {headerNames}")
                print(f"  parsed items: {len(rows)}")
                for item, vals in rows[:5]:
                    print(f"    {item}: {vals[:3]}")

                # _isJunkItem 필터 재현
                for item, vals in rows:
                    stripped = re.sub(r"[,.\-\s]", "", item)
                    if stripped.isdigit() or not stripped:
                        print(f"    JUNK: '{item}' → stripped='{stripped}'")
        break

    # companyOverview kv_matrix_ok_but_filtered
    print("\n--- companyOverview 001200 bo=9 ---")
    sec2 = sections("001200")
    topicFrame2 = sec2.filter(pl.col("topic") == "companyOverview")
    boRow2 = topicFrame2.filter(
        (pl.col("blockOrder") == 9) & (pl.col("blockType") == "table")
    )

    for p in ["2024", "2023"]:
        md = boRow2[p][0] if p in boRow2.columns and boRow2[p][0] is not None else None
        if md is None:
            continue
        print(f"\n{p}:")
        for sub in splitSubtables(str(md)):
            hc = _headerCells(sub)
            st = _classifyStructure(hc)
            if st in ("key_value", "matrix"):
                rows, headerNames, unit = _parseKeyValueOrMatrix(sub)
                print(f"  header: {hc[:5]}")
                print(f"  items: {len(rows)}")

                # 이력형 감지 시뮬레이션
                items_set = set()
                for item, vals in rows:
                    stripped = re.sub(r"[,.\-\s]", "", item)
                    if not (stripped.isdigit() or not stripped):
                        items_set.add(item)
                print(f"  valid items: {len(items_set)}")
                for item in list(items_set)[:5]:
                    print(f"    '{item}'")
        break


# ── 패턴3: multi_year 분기 스킵 ──
def analyzeQuarterMultiYear():
    """분기보고서의 multi_year 테이블이 스킵되는 패턴."""
    print("\n" + "=" * 70)
    print("패턴3: multi_year 분기(Q) 스킵")
    print("=" * 70)

    sec = sections("000720")
    periodCols = [c for c in sec.columns if _isPeriodCol(c)]
    topicFrame = sec.filter(pl.col("topic") == "employee")
    boRow = topicFrame.filter(
        (pl.col("blockOrder") == 9) & (pl.col("blockType") == "table")
    )

    for p in periodCols:
        md = boRow[p][0] if p in boRow.columns and boRow[p][0] is not None else None
        if md is None:
            continue
        print(f"\n{p}:")
        for sub in splitSubtables(str(md)):
            hc = _headerCells(sub)
            st = _classifyStructure(hc)
            print(f"  header: {hc}")
            print(f"  classify: {st}")
            if st == "multi_year":
                m = re.match(r"\d{4}", p)
                pYear = int(m.group()) if m else None
                triples, _ = _parseMultiYear(sub, pYear) if pYear else ([], None)
                current = [t for t in triples if t[1] == str(pYear)]
                print(f"  all triples: {len(triples)}, current year: {len(current)}")
                for item, year, val in current[:5]:
                    print(f"    {item} [{year}] = {val}")
        break


# ── 패턴 종합: 단위행 → 실제 헤더 탐색 수정안 ──
def testUnitHeaderFix():
    """단위행 다음에 실제 헤더가 있는 패턴의 수정안."""
    print("\n" + "=" * 70)
    print("수정안: 단위행 뒤의 실제 헤더를 사용")
    print("=" * 70)

    _UNIT_RE = re.compile(r"^\(?단위\s*:\s*[^)]+\)?\s*$")

    def _headerCellsFixed(lines: list[str]) -> tuple[list[str], int]:
        """단위행을 건너뛰고 실제 헤더 반환. (cells, headerLineIdx)"""
        for i, line in enumerate(lines):
            cells = [c.strip() for c in line.strip("|").split("|")]
            if all(set(c.strip()) <= {"-", ":"} for c in cells if c.strip()):
                continue  # separator
            # 모든 셀이 비어있거나 단위만 포함하면 스킵
            nonEmpty = [c for c in cells if c.strip()]
            if not nonEmpty:
                continue
            if len(nonEmpty) == 1 and _UNIT_RE.match(nonEmpty[0]):
                continue  # 단위행 스킵
            return [c for c in cells if c.strip()], i
        return [], 0

    # 테스트: riskDerivative 000020
    sec = sections("000020")
    topicFrame = sec.filter(pl.col("topic") == "riskDerivative")
    boRow = topicFrame.filter(
        (pl.col("blockOrder") == 1) & (pl.col("blockType") == "table")
    )

    for p in ["2024", "2023"]:
        md = boRow[p][0] if p in boRow.columns and boRow[p][0] is not None else None
        if md is None:
            continue
        for sub in splitSubtables(str(md)):
            hc_old = _headerCells(sub)
            hc_new, idx = _headerCellsFixed(sub)
            if hc_old != hc_new:
                print(f"\n  기존 header: {hc_old}")
                print(f"  수정 header: {hc_new}")
                print(f"  classify old: {_classifyStructure(hc_old)}")
                print(f"  classify new: {_classifyStructure(hc_new)}")
        break

    # 테스트: salesOrder 000270
    sec2 = sections("000270")
    topicFrame2 = sec2.filter(pl.col("topic") == "salesOrder")
    boRow2 = topicFrame2.filter(
        (pl.col("blockOrder") == 1) & (pl.col("blockType") == "table")
    )
    for p in ["2024", "2023"]:
        md = boRow2[p][0] if p in boRow2.columns and boRow2[p][0] is not None else None
        if md is None:
            continue
        for sub in splitSubtables(str(md)):
            hc_old = _headerCells(sub)
            hc_new, idx = _headerCellsFixed(sub)
            if hc_old != hc_new:
                print(f"\n  salesOrder 기존 header: {hc_old}")
                print(f"  salesOrder 수정 header: {hc_new}")
                print(f"  classify old: {_classifyStructure(hc_old)}")
                print(f"  classify new: {_classifyStructure(hc_new)}")
        break


if __name__ == "__main__":
    analyzeUnitHeader()
    analyzeFilteredItems()
    analyzeQuarterMultiYear()
    testUnitHeaderFix()
