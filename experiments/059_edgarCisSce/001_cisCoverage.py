"""
실험 ID: 059-001
실험명: SEC XBRL CIS/SCE 태그 커버리지 분석

목적:
- EDGAR companyfacts parquet에서 Comprehensive Income(CI)과
  Statement of Changes in Equity(EQ) 관련 태그가 얼마나 존재하는지 측정
- 현재 IS/BS/CF 3개만 처리하는 파이프라인에 CI/EQ를 추가할 가치가 있는지 판단

가설:
1. CI 태그는 대부분 기업에 존재하며, OtherComprehensiveIncome 계열 태그로
   포괄손익 항목을 복원할 수 있다
2. EQ(자본변동표) 태그는 SEC XBRL에서 coverage가 매우 낮다
   (US-GAAP에서 별도 statement가 아니라 footnote에 공시하는 경우가 많음)

방법:
1. 전체 EDGAR parquet 파일 스캔
2. us-gaap namespace 태그 중 comprehensiveincome, oci, equity 관련 키워드 매칭
3. standardAccounts.json의 CI/EQ 계정 commonTags와 실제 데이터 대조
4. 기업별 CI/EQ 태그 보유율 계산

결과 (16,601개 중 500개 균등 샘플):

  CI(포괄손익):
    키워드 보유 기업: 369/500 (73.8%)
    known commonTags 보유: 70/500 (14.0%)
    핵심 태그:
      comprehensiveIncomeLossNetOfTax: 57.2%
      otherComprehensiveIncomeLossNetOfTax: 33.4%
      OCI foreignCurrencyTranslation: 26.2%
    고유 태그 수: 521개

  EQ(자본변동):
    키워드 보유 기업: 477/500 (95.4%)
    known commonTags 보유: 187/500 (37.4%)
    핵심 태그:
      stockholdersEquity: 92.4%
      retainedEarningsAccumulatedDeficit: 88.2%
      commonStockValue: 81.4%
      shareBasedCompensation: 71.4%
      additionalPaidInCapital: 64.2%
    고유 태그 수: 309개

  주의: EQ 태그 대부분은 이미 BS에 매핑되어 있는 잔액 계정
  (stockholdersEquity, retainedEarnings 등). 진짜 "자본변동" 흐름 태그
  (dividendsDeclared, shareRepurchase 등)은 별도 확인 필요.

결론:
  1. 가설 1 부분 채택 — CI 태그는 73.8% 기업에 존재하지만,
     known commonTags 매칭은 14.0%로 매우 낮음.
     comprehensiveIncomeLossNetOfTax(57.2%)를 핵심 태그로 추가하면
     CI 커버리지 대폭 개선 가능.

  2. 가설 2 기각 — EQ 키워드 보유가 95.4%로 예상보다 매우 높음.
     다만 대부분 BS 잔액 계정(stockholdersEquity 92.4%)이며,
     실제 "변동" 흐름 태그는 별도 분석 필요 (002 실험).

  3. 다음 과제:
     - CI: comprehensiveIncomeLossNetOfTax 등 핵심 5개 태그를 CI 분류에 추가
     - EQ: BS 잔액과 겹치지 않는 순수 "변동" 태그를 분리 식별 (002)

실험일: 2026-03-14
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "src"))

import json

import polars as pl


def main():
    from dartlab import config

    edgarDir = Path(config.dataDir) / "edgar" / "finance"
    parquetFiles = sorted(edgarDir.glob("*.parquet"))

    print(f"EDGAR parquet 파일 수: {len(parquetFiles)}")
    if not parquetFiles:
        print("데이터 없음")
        return

    stdPath = (
        Path(__file__).resolve().parents[2]
        / "src"
        / "dartlab"
        / "engines"
        / "edgar"
        / "finance"
        / "mapperData"
        / "standardAccounts.json"
    )
    with open(stdPath, encoding="utf-8") as f:
        stdData = json.load(f)

    ciTags = set()
    eqTags = set()
    ciAccounts = []
    eqAccounts = []
    for acct in stdData["accounts"]:
        stmt = acct["stmt"]
        if stmt == "CI":
            ciAccounts.append(acct)
            for tag in acct.get("commonTags", []):
                ciTags.add(tag.lower())
        elif stmt == "EQ":
            eqAccounts.append(acct)
            for tag in acct.get("commonTags", []):
                eqTags.add(tag.lower())

    print(f"\nstandardAccounts CI 계정: {len(ciAccounts)}개, commonTags: {len(ciTags)}개")
    for acct in ciAccounts:
        print(f"  {acct['code']} {acct['snakeId']}: {acct.get('commonTags', [])}")

    print(f"\nstandardAccounts EQ 계정: {len(eqAccounts)}개, commonTags: {len(eqTags)}개")
    for acct in eqAccounts:
        print(f"  {acct['code']} {acct['snakeId']}: {acct.get('commonTags', [])}")

    ciKeywords = [
        "comprehensiveincome", "othercomprehensiveincome",
        "unrealizedgainloss", "foreigncurrencytranslation",
        "pensionadjustment", "hedgegainloss",
        "availableforsale", "reclassification",
    ]
    eqKeywords = [
        "stockholdersequity", "retainedearnings",
        "accumulatedothercomprehensive", "treasurystock",
        "commonstockvalue", "additionalpaidincapital",
        "dividendsdeclared", "stockrepurchase",
        "sharebasedcompensation",
    ]

    totalFiles = len(parquetFiles)
    ciHitCount = 0
    eqHitCount = 0
    ciTagFreq: dict[str, int] = {}
    eqTagFreq: dict[str, int] = {}
    ciKnownHit = 0
    eqKnownHit = 0

    sample = min(totalFiles, 500)
    step = max(1, totalFiles // sample)
    scanFiles = parquetFiles[::step][:sample]

    for i, fp in enumerate(scanFiles):
        df = pl.read_parquet(fp)
        df = df.filter(pl.col("namespace") == "us-gaap")
        tags = df.select("tag").unique().to_series().to_list()
        tagsLower = [t.lower() for t in tags]
        tagsLowerSet = set(tagsLower)

        hasCi = False
        hasEq = False

        if ciTags & tagsLowerSet:
            ciKnownHit += 1

        if eqTags & tagsLowerSet:
            eqKnownHit += 1

        for tag in tagsLower:
            for kw in ciKeywords:
                if kw in tag:
                    hasCi = True
                    ciTagFreq[tag] = ciTagFreq.get(tag, 0) + 1
                    break

            for kw in eqKeywords:
                if kw in tag:
                    hasEq = True
                    eqTagFreq[tag] = eqTagFreq.get(tag, 0) + 1
                    break

        if hasCi:
            ciHitCount += 1
        if hasEq:
            eqHitCount += 1

        if (i + 1) % 50 == 0:
            print(f"  스캔 {i + 1}/{sample}...")

    print(f"\n=== 결과 ({sample}개 스캔) ===")
    print(f"CI 키워드 보유 기업: {ciHitCount}/{sample} ({ciHitCount/sample*100:.1f}%)")
    print(f"EQ 키워드 보유 기업: {eqHitCount}/{sample} ({eqHitCount/sample*100:.1f}%)")
    print(f"CI known commonTags 보유: {ciKnownHit}/{sample} ({ciKnownHit/sample*100:.1f}%)")
    print(f"EQ known commonTags 보유: {eqKnownHit}/{sample} ({eqKnownHit/sample*100:.1f}%)")

    print(f"\n--- CI 태그 빈도 Top 20 ---")
    for tag, cnt in sorted(ciTagFreq.items(), key=lambda x: -x[1])[:20]:
        print(f"  {tag}: {cnt}/{sample} ({cnt/sample*100:.1f}%)")

    print(f"\n--- EQ 태그 빈도 Top 20 ---")
    for tag, cnt in sorted(eqTagFreq.items(), key=lambda x: -x[1])[:20]:
        print(f"  {tag}: {cnt}/{sample} ({cnt/sample*100:.1f}%)")

    print(f"\n--- CI 전체 고유 태그 수: {len(ciTagFreq)} ---")
    print(f"--- EQ 전체 고유 태그 수: {len(eqTagFreq)} ---")


if __name__ == "__main__":
    main()
