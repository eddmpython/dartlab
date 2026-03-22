"""
실험 ID: 064-017
실험명: 단위행 변형 패턴 수집 + 강화된 정규식 검증

목적:
- _stripUnitHeader가 놓치는 단위행 변형 패턴 수집
- 강화된 정규식으로 추가 커버 가능한 건수 측정

방법:
1. 283종목 전수에서 struct_skip인 1-컬럼 헤더 수집
2. 단위 관련 키워드 포함 여부 분류
3. 기존 vs 강화 정규식 비교

실험일: 2026-03-17
"""

import sys
import re
from collections import defaultdict, Counter
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "src"))

import polars as pl

from dartlab.engines.company.dart.docs.sections.pipeline import sections
from dartlab.engines.company.dart.docs.sections.tableParser import (
    splitSubtables,
    _headerCells,
    _isJunk,
    _classifyStructure,
)


def _isPeriodCol(c: str) -> bool:
    return bool(re.match(r"^\d{4}(Q[1-4])?$", c))


# 기존 정규식
_UNIT_ONLY_OLD = re.compile(r"^\(?\s*단위\s*[:/]?\s*[^)]*\)?\s*$")
_DATE_ONLY = re.compile(r"^\(?\s*기준일\s*:")

# 강화: 원화단위/외화단위/금액단위 등 + 콤마 구분
_UNIT_ONLY_NEW = re.compile(
    r"^\(?\s*"
    r"(?:단위|원화\s*단위|외화\s*단위|금액\s*단위)"
    r".*$",
    re.IGNORECASE
)


if __name__ == "__main__":
    from dartlab.core.dataLoader import _dataDir

    dataDir = _dataDir("docs")
    files = sorted(dataDir.glob("*.parquet"))
    codes = [f.stem for f in files]

    print(f"단위행 변형 패턴 수집: {len(codes)}종목")
    print("=" * 70)

    skip_headers = Counter()  # single-col header text → count
    old_match = 0
    new_match = 0
    unmatched = Counter()

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

        topics = tableRows["topic"].unique().to_list()
        for topic in topics:
            topicFrame = sec.filter(pl.col("topic") == topic)
            tTableRows = topicFrame.filter(pl.col("blockType") == "table")
            blockOrders = sorted(tTableRows["blockOrder"].unique().to_list())

            for bo in blockOrders:
                boRow = topicFrame.filter(
                    (pl.col("blockOrder") == bo) & (pl.col("blockType") == "table")
                )

                for p in periodCols[:1]:  # 첫 기간만
                    md = boRow[p][0] if p in boRow.columns else None
                    if md is None:
                        continue

                    for sub in splitSubtables(str(md)):
                        hc = _headerCells(sub)
                        if _isJunk(hc):
                            continue
                        st = _classifyStructure(hc)
                        if st == "skip" and len(hc) == 1:
                            h = hc[0].strip()
                            skip_headers[h] += 1

                            if _UNIT_ONLY_OLD.match(h) or _DATE_ONLY.match(h):
                                old_match += 1
                            elif _UNIT_ONLY_NEW.match(h):
                                new_match += 1
                            else:
                                unmatched[h] += 1

        if (i + 1) % 100 == 0:
            print(f"  [{i+1}/{len(codes)}]...")

    print(f"\n총 1-col skip 헤더: {sum(skip_headers.values())}")
    print(f"기존 정규식 매칭: {old_match}")
    print(f"강화 정규식 추가 매칭: {new_match}")
    print(f"미매칭: {sum(unmatched.values())}")

    # 강화 정규식으로 새로 잡히는 패턴
    print(f"\n{'='*70}")
    print("강화 정규식으로 새로 잡히는 패턴 (상위 20)")
    print(f"{'='*70}")
    new_caught = [(h, c) for h, c in skip_headers.items()
                  if not _UNIT_ONLY_OLD.match(h) and not _DATE_ONLY.match(h)
                  and _UNIT_ONLY_NEW.match(h)]
    for h, c in sorted(new_caught, key=lambda x: -x[1])[:20]:
        print(f"  [{c:4d}] {h[:80]}")

    # 미매칭 중 단위 관련 키워드 포함
    print(f"\n{'='*70}")
    print("미매칭 중 '단위' 키워드 포함 (상위 20)")
    print(f"{'='*70}")
    unit_related = [(h, c) for h, c in unmatched.items() if "단위" in h]
    for h, c in sorted(unit_related, key=lambda x: -x[1])[:20]:
        print(f"  [{c:4d}] {h[:80]}")

    # 미매칭 전체 상위 30
    print(f"\n{'='*70}")
    print("미매칭 전체 (상위 30)")
    print(f"{'='*70}")
    for h, c in unmatched.most_common(30):
        print(f"  [{c:4d}] {h[:80]}")
