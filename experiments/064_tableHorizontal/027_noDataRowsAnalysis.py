"""실험 ID: 027
실험명: no_data_rows 실패 패턴 분석

목적:
- no_items 11,297건 중 no_data_rows(71%)의 구체적 패턴을 분류
- _stripUnitHeader가 놓치는 다중컬럼 헤더 패턴 수집
- 수정 가능한 패턴과 불가능한 패턴 분리

가설:
1. 다중컬럼 기준일+단위 헤더가 no_data_rows의 주요 원인일 것
2. _stripUnitHeader를 다중컬럼으로 확장하면 상당수 복구 가능

방법:
1. 283종목 전체 table 블록에서 수평화 실패 케이스 수집
2. 실패 원인별 분류: no_data_rows, all_junk, single_col, 기타
3. no_data_rows의 헤더 패턴 수집 → 상위 패턴 확인
4. 다중컬럼 단위/기준일 헤더 비율 측정

결과 (30종목 기준):
- 전체 서브테이블: 108,947
- 성공(데이터 있음): 34,047 (31.3%)
- no_data_rows: 28,084 (25.8%)
- skip_type: 26,189 (24.0%)
- junk_header: 20,627 (18.9%)

no_data_rows 헤더 패턴 (28,084건):
- single_col_unit: 6,327건 (단일컬럼 단위 → splitSubtables가 분리한 빈 서브테이블)
- multi_col_unit_2col: 4,704건 (기준일+단위 2컬럼)
- multi_col_unit_4col: 4,089건 (기준일+날짜+)+단위 4컬럼)
- multi_col_other_*: 나머지 (빈 테이블, 단행 요약, 텍스트 오분류)

핵심 발견:
1. 다중컬럼 단위/기준일 헤더 ~9,089건은 splitSubtables가 분리한 **빈 서브테이블**
   (단위 행만 있고 실제 데이터는 다음 서브테이블에 존재)
2. 이 건들은 _horizontalizeTableBlock에서 `if not dr: continue`로 이미 스킵되고,
   실제 데이터 테이블은 별도 서브테이블로 정상 처리됨
3. other_Ncol 패턴은 대부분 빈 테이블, 텍스트 오분류, 단행 K-IFRS 요약행

결론:
- no_data_rows 대부분은 **정상 스킵** — 수정 불필요
- _stripUnitHeader 다중컬럼 확장은 방어 코드로 유지하되 실질 효과 없음
- 수평화율 향상의 핵심 병목은 no_data_rows가 아니라 overlap_filtered(이력형 테이블)

실험일: 2026-03-19
"""
import re
import sys
from collections import Counter, defaultdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "src"))

import polars as pl

from dartlab.engines.company.dart.docs.sections.pipeline import sections as buildSections
from dartlab.engines.company.dart.docs.sections.tableParser import (
    _classifyStructure,
    _dataRows,
    _headerCells,
    _isJunk,
    splitSubtables,
)

# ── 단위행 정규식 (company.py에서 가져옴) ──
_UNIT_ONLY_RE = re.compile(
    r"^[\(\[\（<〈]?\s*"
    r"(?:<[^>]+>\s*)?"
    r"[\(\[\（]?\s*"
    r"(?:단위|원화\s*단위|외화\s*단위|금액\s*단위)"
    r".*$",
    re.IGNORECASE,
)
_DATE_ONLY_RE = re.compile(r"^\(?\s*기준일\s*:")


def _isPeriodColumn(c: str) -> bool:
    return bool(re.match(r"\d{4}(Q[1-4])?$", c))


def analyzeFailures(maxCompanies: int = 0):
    """전종목 table 블록에서 no_data_rows 패턴 분석."""
    from dartlab.engines.gather.listing import getKindList

    kindList = getKindList()
    codes = kindList["종목코드"].to_list()
    if maxCompanies > 0:
        codes = codes[:maxCompanies]

    failureReasons = Counter()
    headerPatterns = Counter()  # no_data_rows의 헤더 패턴
    multiColUnitHeaders = []  # 다중컬럼 단위/기준일 헤더 샘플
    noDataSamples = defaultdict(list)  # 패턴별 샘플

    totalBlocks = 0
    successBlocks = 0

    for ci, code in enumerate(codes):
        try:
            sec = buildSections(code)
        except Exception:
            continue

        if sec is None or sec.is_empty():
            continue

        periodCols = [c for c in sec.columns if _isPeriodColumn(c)]
        tableRows = sec.filter(pl.col("blockType") == "table")

        for record in tableRows.iter_rows(named=True):
            for p in periodCols:
                md = record.get(p)
                if md is None:
                    continue

                for sub in splitSubtables(str(md)):
                    totalBlocks += 1
                    hc = _headerCells(sub)

                    if _isJunk(hc):
                        failureReasons["junk_header"] += 1
                        continue

                    dr = _dataRows(sub)
                    structType = _classifyStructure(hc)

                    if not dr:
                        # no_data_rows — 핵심 분석 대상
                        failureReasons["no_data_rows"] += 1

                        # 헤더 셀 수와 내용 분류
                        hLen = len(hc)
                        hJoined = " | ".join(hc)

                        # 단위행 패턴 검사
                        isUnitLike = False
                        if hLen == 1:
                            h = hc[0].strip()
                            if _UNIT_ONLY_RE.match(h) or _DATE_ONLY_RE.match(h):
                                isUnitLike = True
                                headerPatterns["single_col_unit"] += 1
                        elif hLen >= 2:
                            # 다중컬럼 단위/기준일 패턴
                            fullH = " ".join(hc)
                            if re.search(r"단위\s*[:/]", fullH) or re.search(r"기준일", fullH):
                                isUnitLike = True
                                headerPatterns[f"multi_col_unit_{hLen}col"] += 1
                                if len(multiColUnitHeaders) < 50:
                                    multiColUnitHeaders.append({
                                        "code": code,
                                        "period": p,
                                        "headerCells": hc,
                                        "subLines": sub[:5],
                                    })

                        if not isUnitLike:
                            # 단위/기준일이 아닌 no_data_rows
                            if hLen == 1:
                                headerPatterns["single_col_other"] += 1
                            else:
                                headerPatterns[f"multi_col_other_{hLen}col"] += 1

                            if len(noDataSamples[f"other_{hLen}col"]) < 10:
                                noDataSamples[f"other_{hLen}col"].append({
                                    "code": code,
                                    "period": p,
                                    "headerCells": hc,
                                    "subLines": sub[:6],
                                })
                    else:
                        # 데이터 행이 있음 — 성공 후보
                        if structType == "skip":
                            failureReasons["skip_type"] += 1
                        else:
                            successBlocks += 1

        if (ci + 1) % 50 == 0:
            print(f"  [{ci+1}/{len(codes)}] blocks={totalBlocks}, success={successBlocks}")

    print(f"\n=== 결과 ({len(codes)}종목) ===")
    print(f"전체 서브테이블: {totalBlocks}")
    print(f"성공(데이터 있음): {successBlocks} ({successBlocks/totalBlocks*100:.1f}%)")
    print(f"\n실패 원인:")
    for reason, cnt in failureReasons.most_common():
        print(f"  {reason}: {cnt} ({cnt/totalBlocks*100:.1f}%)")

    print(f"\nno_data_rows 헤더 패턴:")
    for pat, cnt in headerPatterns.most_common():
        print(f"  {pat}: {cnt}")

    print(f"\n다중컬럼 단위/기준일 헤더 샘플 ({len(multiColUnitHeaders)}개):")
    for s in multiColUnitHeaders[:20]:
        print(f"  [{s['code']} {s['period']}] {s['headerCells']}")
        for line in s["subLines"]:
            print(f"    {line.strip()}")
        print()

    print(f"\n단위/기준일 아닌 no_data_rows 샘플:")
    for key, samples in noDataSamples.items():
        print(f"\n  === {key} ===")
        for s in samples[:5]:
            print(f"  [{s['code']} {s['period']}] {s['headerCells']}")
            for line in s["subLines"]:
                print(f"    {line.strip()}")
            print()

    return {
        "totalBlocks": totalBlocks,
        "successBlocks": successBlocks,
        "failureReasons": failureReasons,
        "headerPatterns": headerPatterns,
        "multiColUnitHeaders": multiColUnitHeaders,
        "noDataSamples": noDataSamples,
    }


if __name__ == "__main__":
    # 먼저 소수 종목으로 빠르게 테스트
    result = analyzeFailures(maxCompanies=30)
