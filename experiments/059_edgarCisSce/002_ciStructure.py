"""
실험 ID: 059-002
실험명: AAPL CI/EQ 태그 실제 값 구조 분석

목적:
- AAPL companyfacts에서 CI/EQ 관련 태그의 실제 값과 기간 구조를 확인
- CI 태그가 duration(기간)인지 instant(시점)인지 → IS처럼 처리할지 BS처럼 처리할지
- EQ 태그 중 BS 잔액과 겹치지 않는 순수 "변동" 태그 식별
- CI를 IS에 합칠지, 별도 stmt로 분리할지 판단

가설:
1. CI 핵심 태그(comprehensiveIncome, otherComprehensiveIncome)는 duration 기반이며
   IS와 동일한 방식으로 standalone 추출 가능
2. EQ 순수 변동 태그는 소수이며, 대부분 BS 잔액 태그의 중복

방법:
1. AAPL CIK 파일 로드
2. CI/EQ 키워드 태그의 fp, start, end, val, frame 구조 출력
3. duration vs instant 비율 분석
4. BS 기존 snakeId와 겹치는 EQ 태그 분리

결과 (AAPL 분석):

  CI 태그 43개 발견:
    - 대부분 **duration** 기반 (IS와 동일 처리 가능)
    - 4개만 instant (AccumulatedOCI 잔액 → 이미 BS에 있음)
    - ComprehensiveIncomeNetOfTax: FY2025=96.6B (최근 활성)
    - OtherComprehensiveIncomeLossNetOfTaxPortionAttributableToParent: FY2025=-343M
    - 핵심 2~3개 태그로 CIS 핵심 행 복원 가능

  EQ 태그 74개 발견:
    - BS 겹침: 12개 (stockholdersEquity, retainedEarnings, AOCI 등 잔액)
    - 순수 EQ: 62개 — **대부분 ShareBasedCompensation 세부 항목** (50+개)
    - 실질적 자본변동 태그: StockRepurchasedAndRetiredDuringPeriodValue(FY 48행),
      PaymentsRelatedToTaxWithholdingForShareBasedCompensation(FY 132행)
    - 자본변동표를 구성하는 "행"이 아니라 주석(footnote) 세부 공시
    - SEC XBRL에서 자본변동표(SCE)를 행렬 형태로 제출하지 않음

결론:
  1. 가설 1 채택 — CI 태그는 duration 기반이며 IS와 동일 방식 처리 가능.
     ComprehensiveIncomeNetOfTax(57.2%), OtherComprehensiveIncome 계열로
     CIS 핵심 행 복원 가능. 별도 "CI" stmt로 분리하는 것이 맞음.

  2. 가설 2 채택 — EQ 순수 태그 62개 중 50+개가 ShareBasedCompensation 세부.
     SEC XBRL은 자본변동표를 행렬(period × equity component)로 제출하지 않고,
     개별 태그로 footnote에 공시. DART의 SCE(자본변동표 매트릭스)와 구조적으로 다름.
     → SCE를 DART처럼 매트릭스로 구성하는 것은 SEC XBRL에서는 불가능.

  3. 결론: CI는 추가할 가치 있음 (IS 동일 처리). SCE는 SEC 구조상 불가.

실험일: 2026-03-14
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "src"))

import polars as pl


def main():
    from dartlab import config

    edgarDir = Path(config.dataDir) / "edgar" / "finance"

    aaplCik = "0000320193"
    aaplPath = edgarDir / f"{aaplCik}.parquet"
    if not aaplPath.exists():
        print(f"AAPL 파일 없음: {aaplPath}")
        return

    df = pl.read_parquet(aaplPath)
    df = df.filter(pl.col("namespace") == "us-gaap")
    print(f"AAPL us-gaap 태그 행 수: {df.height}")
    print(f"컬럼: {df.columns}")
    print()

    allTags = df.select("tag").unique().to_series().to_list()
    allTagsLower = {t.lower(): t for t in allTags}

    ciKeywords = [
        "comprehensiveincome", "othercomprehensiveincome",
    ]
    eqKeywords = [
        "stockholdersequity", "retainedearnings",
        "commonstockvalue", "additionalpaidincapital",
        "treasurystock", "dividendsdeclared",
        "stockrepurchase", "sharebasedcompensation",
        "accumulatedothercomprehensive",
    ]

    ciTags = []
    eqTags = []
    for tagLower, tagOriginal in allTagsLower.items():
        for kw in ciKeywords:
            if kw in tagLower:
                ciTags.append(tagOriginal)
                break
        for kw in eqKeywords:
            if kw in tagLower:
                eqTags.append(tagOriginal)
                break

    print(f"=== CI 태그 ({len(ciTags)}개) ===")
    for tag in sorted(ciTags):
        tagDf = df.filter(pl.col("tag") == tag)
        hasDuration = tagDf.filter(
            pl.col("start").is_not_null() & pl.col("end").is_not_null()
        ).height
        hasInstant = tagDf.filter(
            pl.col("start").is_null() & pl.col("end").is_not_null()
        ).height
        fps = tagDf.select("fp").unique().to_series().to_list()
        latestRow = tagDf.sort("filed", descending=True).head(1)
        latestVal = latestRow["val"][0] if latestRow.height > 0 else None
        latestFp = latestRow["fp"][0] if latestRow.height > 0 else None
        latestFy = latestRow["fy"][0] if latestRow.height > 0 else None
        print(
            f"  {tag}: "
            f"rows={tagDf.height}, duration={hasDuration}, instant={hasInstant}, "
            f"fps={fps}, latest={latestFy}-{latestFp}={latestVal}"
        )

    print(f"\n=== EQ 태그 ({len(eqTags)}개) ===")

    from dartlab.providers.edgar.finance.mapper import EdgarMapper

    bsSnakeIds = set()
    isSnakeIds = set()
    stmtTags = EdgarMapper.classifyTagsByStmt()
    for tag in stmtTags.get("BS", set()):
        sid = EdgarMapper.mapToDart(tag, "BS")
        if sid:
            bsSnakeIds.add(sid)

    overlapping = []
    pure = []
    for tag in sorted(eqTags):
        sid = EdgarMapper.mapToDart(tag, "BS")
        if sid and sid in bsSnakeIds:
            overlapping.append((tag, sid))
        else:
            pure.append(tag)

    print(f"\n  BS와 겹치는 EQ 태그 ({len(overlapping)}개):")
    for tag, sid in overlapping:
        print(f"    {tag} → {sid}")

    print(f"\n  순수 EQ 태그 (BS에 없음, {len(pure)}개):")
    for tag in pure:
        tagDf = df.filter(pl.col("tag") == tag)
        hasDuration = tagDf.filter(
            pl.col("start").is_not_null() & pl.col("end").is_not_null()
        ).height
        hasInstant = tagDf.filter(
            pl.col("start").is_null() & pl.col("end").is_not_null()
        ).height
        fps = tagDf.select("fp").unique().to_series().to_list()
        latestRow = tagDf.sort("filed", descending=True).head(1)
        latestVal = latestRow["val"][0] if latestRow.height > 0 else None
        latestFp = latestRow["fp"][0] if latestRow.height > 0 else None
        latestFy = latestRow["fy"][0] if latestRow.height > 0 else None
        print(
            f"    {tag}: "
            f"rows={tagDf.height}, duration={hasDuration}, instant={hasInstant}, "
            f"fps={fps}, latest={latestFy}-{latestFp}={latestVal}"
        )

    print("\n=== CI 핵심 태그 상세 (최근 FY) ===")
    coreCI = [
        "ComprehensiveIncomeNetOfTax",
        "OtherComprehensiveIncomeLossNetOfTax",
        "OtherComprehensiveIncomeLossNetOfTaxPortionAttributableToParent",
        "ComprehensiveIncomeNetOfTaxIncludingPortionAttributableToNoncontrollingInterest",
        "ComprehensiveIncomeNetOfTaxAttributableToNoncontrollingInterest",
    ]
    for tag in coreCI:
        tagDf = df.filter(pl.col("tag") == tag)
        if tagDf.height == 0:
            print(f"  {tag}: 없음")
            continue
        fyRows = tagDf.filter(pl.col("fp") == "FY").sort("fy", descending=True)
        if fyRows.height > 0:
            recent = fyRows.head(5)
            for row in recent.iter_rows(named=True):
                print(f"  {tag}: FY{row['fy']} val={row['val']:,.0f}")
        else:
            print(f"  {tag}: FY 없음 (fp: {tagDf.select('fp').unique().to_series().to_list()})")


if __name__ == "__main__":
    main()
