"""실험 ID: 028
실험명: 다중컬럼 단위/기준일 헤더 패치 효과 측정

목적:
- _stripUnitHeader를 다중컬럼으로 확장한 후 수평화 성공률 변화 측정
- 283종목 전수 검증

가설:
1. 다중컬럼 단위/기준일 헤더 처리로 no_data_rows 감소 → 수평화율 +2%p 이상

방법:
1. 283종목 전체 table 블록에서 _horizontalizeTableBlock 호출
2. 성공/실패 건수 카운트 + 핵심 topic별 성공률

결과:
- 11종목(동화약품 포함): 7,844/14,834 (52.9%)
- 패치 전/후 차이 없음 — 다중컬럼 단위 헤더는 splitSubtables가 분리한 빈 서브테이블이라
  _horizontalizeTableBlock에서 `if not dr: continue`로 이미 스킵되고,
  실제 데이터는 다음 서브테이블에서 정상 처리됨

- _stripUnitHeader 다중컬럼 확장: 동작 확인 (유닛테스트 통과)
- `if not dr:` 경로에서 _stripUnitHeader 복구 시도 추가: 동작 확인
- 하지만 실제 데이터에서는 빈 서브테이블이므로 복구 대상 없음

결론:
- 코드 변경은 방어적으로 유지 (향후 다른 패턴 데이터에서 효과 있을 수 있음)
- no_data_rows는 수평화율 향상의 핵심 경로가 아님
- overlap_filtered(이력형 감지)가 전체 실패의 63%로 핵심 병목

실험일: 2026-03-19
"""
import re
import sys
from collections import Counter
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "src"))

import polars as pl


def _isPeriodColumn(c: str) -> bool:
    return bool(re.match(r"\d{4}(Q[1-4])?$", c))


def measureRate(maxCompanies: int = 0):
    from dartlab.engines.company.dart.company import Company
    from dartlab.engines.gather.listing import getKindList

    kindList = getKindList()
    codes = kindList["종목코드"].to_list()
    if maxCompanies > 0:
        codes = codes[:maxCompanies]

    totalBlocks = 0
    successBlocks = 0
    topicStats = Counter()  # topic → (success, total)
    topicSuccess = Counter()
    errorCodes = []

    for ci, code in enumerate(codes):
        try:
            c = Company(code)
            sec = c.docs.sections
            if sec is None:
                continue
        except Exception:
            continue

        df = sec.raw if hasattr(sec, "raw") else (sec if isinstance(sec, pl.DataFrame) else None)
        if df is None:
            continue
        periodCols = [col for col in df.columns if _isPeriodColumn(col)]
        tableRows = df.filter(pl.col("blockType") == "table")

        if tableRows.is_empty():
            continue

        topics = tableRows["topic"].unique().to_list()
        for topic in topics:
            topicFrame = df.filter(pl.col("topic") == topic)
            tblFrame = topicFrame.filter(pl.col("blockType") == "table")
            blockOrders = tblFrame["blockOrder"].unique().sort().to_list()

            for bo in blockOrders:
                totalBlocks += 1
                topicStats[topic] += 1
                try:
                    result = c._horizontalizeTableBlock(topicFrame, bo, periodCols)
                    if result is not None:
                        successBlocks += 1
                        topicSuccess[topic] += 1
                except Exception as e:
                    errorCodes.append((code, topic, bo, str(e)))

        if (ci + 1) % 50 == 0:
            rate = successBlocks / totalBlocks * 100 if totalBlocks else 0
            print(f"  [{ci+1}/{len(codes)}] {totalBlocks} blocks, {successBlocks} success ({rate:.1f}%)")

    rate = successBlocks / totalBlocks * 100 if totalBlocks else 0
    print(f"\n=== 결과 ({len(codes)}종목) ===")
    print(f"전체: {totalBlocks} blocks, success={successBlocks} ({rate:.1f}%), none={totalBlocks-successBlocks} ({100-rate:.1f}%)")
    print(f"에러: {len(errorCodes)}건")

    # 핵심 topic별 성공률
    keyTopics = [
        "dividend", "audit", "salesOrder", "companyOverview", "employee",
        "majorHolder", "shareCapital", "executivePay", "rawMaterial",
        "riskDerivative", "internalControl", "boardOfDirectors",
        "auditSystem", "relatedPartyTx", "shareholderMeeting",
        "majorContractsAndRnd", "businessOverview",
    ]
    print(f"\n핵심 topic 성공률:")
    print(f"{'topic':<30} {'success':>8} {'total':>8} {'rate':>8}")
    for t in keyTopics:
        total = topicStats.get(t, 0)
        success = topicSuccess.get(t, 0)
        if total > 0:
            r = success / total * 100
            print(f"{t:<30} {success:>8} {total:>8} {r:>7.1f}%")

    if errorCodes:
        print(f"\n에러 샘플:")
        for code, topic, bo, err in errorCodes[:10]:
            print(f"  [{code}] {topic} bo={bo}: {err}")


if __name__ == "__main__":
    measureRate(maxCompanies=283)
