"""
실험 ID: 064-013
실험명: 단위행 헤더 샘플 확인 + 패치 검증

목적:
- single_col_header_unit 패턴의 실제 마크다운 확인
- _headerCells 패치 후 분류 변화 확인
- 패치 적용 시 283종목 None 비율 변화 측정

실험일: 2026-03-17
"""

import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "src"))

import polars as pl

from dartlab.engines.company.dart.docs.sections.pipeline import sections
from dartlab.engines.company.dart.docs.sections.tableParser import (
    _classifyStructure,
    _dataRows,
    _headerCells,
    _isJunk,
    splitSubtables,
)


def _isPeriodCol(c: str) -> bool:
    return bool(re.match(r"^\d{4}(Q[1-4])?$", c))


_UNIT_ONLY_RE = re.compile(r"^\(?\s*단위\s*[:/]?\s*[^)]*\)?\s*$")
_BASEDATE_RE = re.compile(r"^\(?\s*기준일\s*:")


if __name__ == "__main__":
    # 다양한 topic에서 single_col_header_unit 샘플 확인
    samples = [
        ("000020", "riskDerivative", 1),
        ("000270", "salesOrder", 1),
        ("000270", "businessOverview", 1),
        ("003550", "affiliateGroup", 3),
        ("000020", "consolidatedNotes", 3),
    ]

    for code, topic, bo in samples:
        print(f"\n{'='*70}")
        print(f"{code} {topic} bo={bo}")
        print(f"{'='*70}")

        sec = sections(code)
        topicFrame = sec.filter(pl.col("topic") == topic)
        boRow = topicFrame.filter(
            (pl.col("blockOrder") == bo) & (pl.col("blockType") == "table")
        )
        if boRow.is_empty():
            print("  (empty)")
            continue

        periodCols = [c for c in sec.columns if _isPeriodCol(c)]
        for p in periodCols:
            md = boRow[p][0] if p in boRow.columns else None
            if md is None:
                continue
            print(f"\n  --- {p} (첫 800자) ---")
            md_str = str(md)
            # 처음 몇 줄만 출력
            lines = md_str.split("\n")
            for i, line in enumerate(lines[:15]):
                print(f"  [{i:2d}] {line[:120]}")

            # 서브테이블별 분류
            for si, sub in enumerate(splitSubtables(md_str)):
                hc = _headerCells(sub)
                junk = _isJunk(hc)
                st = _classifyStructure(hc) if not junk else "junk"

                # 패치된 헤더
                hc_patched = None
                for line in sub:
                    cells = [c.strip() for c in line.strip("|").split("|")]
                    if all(set(c.strip()) <= {"-", ":"} for c in cells if c.strip()):
                        continue
                    nonEmpty = [c for c in cells if c.strip()]
                    if not nonEmpty:
                        continue
                    if len(nonEmpty) == 1 and (_UNIT_ONLY_RE.match(nonEmpty[0]) or _BASEDATE_RE.match(nonEmpty[0])):
                        continue  # 스킵
                    hc_patched = [c for c in cells if c.strip()]
                    break
                st_patched = _classifyStructure(hc_patched) if hc_patched and not _isJunk(hc_patched) else "skip"

                if st != st_patched:
                    print(f"\n  sub[{si}] OLD: header={hc[:4]}  classify={st}")
                    print(f"  sub[{si}] NEW: header={hc_patched[:4] if hc_patched else []}  classify={st_patched}")

            break  # 첫 기간만
