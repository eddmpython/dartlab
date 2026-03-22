"""
실험 ID: 059-003
실험명: CI commonTags 보강 및 파이프라인 확장

목적:
- standardAccounts.json CI 계정에 고빈도 태그 추가
- mapper/pivot에 CI 분류 추가
- 500개 기업 CI 커버리지 before/after 비교

가설:
1. commonTags 보강으로 CI known 매칭이 14.0% → 50%+ 상승

방법:
1. standardAccounts.json CI 계정에 핵심 태그 추가
2. mapper classifyTagsByStmt에 CI 키 추가
3. pivot buildTimeseries/buildAnnual에 CI 처리 추가
4. 500개 기업 CI 커버리지 재측정

결과 (실험 후 작성):
-

결론:
-

실험일: 2026-03-14
"""

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "src"))


def boostStandardAccounts():
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
        data = json.load(f)

    accounts = data["accounts"]
    existingCodes = {a["code"] for a in accounts if "code" in a}

    for a in accounts:
        if a.get("code") == "CI001":
            toAdd = ["OtherComprehensiveIncomeLossNetOfTax"]
            existing = set(a["commonTags"])
            for tag in toAdd:
                if tag not in existing:
                    a["commonTags"].append(tag)
                    print(f"  CI001에 추가: {tag}")

    newCI = [
        {
            "code": "CI002",
            "stmt": "CI",
            "snakeId": "comprehensive_income",
            "korName": "포괄손익",
            "engName": "Comprehensive Income Net of Tax",
            "level": 1,
            "line": 90,
            "parent": None,
            "commonTags": [
                "ComprehensiveIncomeNetOfTax",
                "ComprehensiveIncomeNetOfTaxIncludingPortionAttributableToNoncontrollingInterest",
                "ComprehensiveIncomeNetOfTaxAttributableToNoncontrollingInterest",
            ],
        },
        {
            "code": "CI003",
            "stmt": "CI",
            "snakeId": "other_comprehensive_income_parent",
            "korName": "지배기업 기타포괄손익",
            "engName": "OCI Attributable to Parent",
            "level": 1,
            "line": 95,
            "parent": None,
            "commonTags": [
                "OtherComprehensiveIncomeLossNetOfTaxPortionAttributableToParent",
            ],
        },
        {
            "code": "CI013",
            "stmt": "CI",
            "snakeId": "oci_foreign_currency",
            "korName": "외화환산손익",
            "engName": "OCI Foreign Currency Translation",
            "level": 2,
            "line": 140,
            "parent": "total_other_comprehensive_income",
            "commonTags": [
                "OtherComprehensiveIncomeLossForeignCurrencyTransactionAndTranslationAdjustmentNetOfTax",
                "OtherComprehensiveIncomeForeignCurrencyTransactionAndTranslationAdjustmentNetOfTaxPeriodIncreaseDecrease",
            ],
        },
        {
            "code": "CI014",
            "stmt": "CI",
            "snakeId": "oci_afs_securities",
            "korName": "매도가능증권 평가손익",
            "engName": "OCI Available-for-Sale Securities",
            "level": 2,
            "line": 150,
            "parent": "total_other_comprehensive_income",
            "commonTags": [
                "OtherComprehensiveIncomeLossAvailableForSaleSecuritiesAdjustmentNetOfTax",
                "OtherComprehensiveIncomeUnrealizedHoldingGainLossOnSecuritiesArisingDuringPeriodNetOfTax",
            ],
        },
        {
            "code": "CI015",
            "stmt": "CI",
            "snakeId": "oci_derivatives",
            "korName": "파생상품 평가손익",
            "engName": "OCI Derivatives Qualifying as Hedges",
            "level": 2,
            "line": 160,
            "parent": "total_other_comprehensive_income",
            "commonTags": [
                "OtherComprehensiveIncomeLossDerivativesQualifyingAsHedgesNetOfTax",
                "OtherComprehensiveIncomeUnrealizedGainLossOnDerivativesArisingDuringPeriodNetOfTax",
                "OtherComprehensiveIncomeLossCashFlowHedgeGainLossAfterReclassificationAndTax",
            ],
        },
        {
            "code": "CI016",
            "stmt": "CI",
            "snakeId": "oci_reclassification_afs",
            "korName": "매도가능증권 재분류조정",
            "engName": "OCI Reclassification for Sale of Securities",
            "level": 2,
            "line": 170,
            "parent": "total_other_comprehensive_income",
            "commonTags": [
                "OtherComprehensiveIncomeLossReclassificationAdjustmentFromAOCIForSaleOfSecuritiesNetOfTax",
            ],
        },
        {
            "code": "CI017",
            "stmt": "CI",
            "snakeId": "oci_reclassification_derivatives",
            "korName": "파생상품 재분류조정",
            "engName": "OCI Reclassification on Derivatives",
            "level": 2,
            "line": 180,
            "parent": "total_other_comprehensive_income",
            "commonTags": [
                "OtherComprehensiveIncomeLossReclassificationAdjustmentFromAOCIOnDerivativesNetOfTax",
                "OtherComprehensiveIncomeLossCashFlowHedgeGainLossReclassificationAfterTax",
            ],
        },
        {
            "code": "CI018",
            "stmt": "CI",
            "snakeId": "oci_tax",
            "korName": "기타포괄손익 세효과",
            "engName": "OCI Tax",
            "level": 2,
            "line": 190,
            "parent": "total_other_comprehensive_income",
            "commonTags": [
                "OtherComprehensiveIncomeLossTax",
            ],
        },
    ]

    added = 0
    for newAcct in newCI:
        if newAcct["code"] not in existingCodes:
            accounts.append(newAcct)
            existingCodes.add(newAcct["code"])
            added += 1
            print(f"  추가: {newAcct['code']} {newAcct['snakeId']}")

    data["_metadata"]["totalAccounts"] = len(accounts)

    with open(stdPath, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

    ciNow = [a for a in accounts if a["stmt"] == "CI"]
    totalCommonTags = sum(len(a.get("commonTags", [])) for a in ciNow)
    print(f"\n  총 계정: {len(accounts)}개, CI: {len(ciNow)}개, CI commonTags: {totalCommonTags}개")
    return added


def measureCoverage():
    import polars as pl

    from dartlab import config
    from dartlab.engines.company.edgar.finance.mapper import EdgarMapper

    EdgarMapper._tagMap = None
    EdgarMapper._ensureLoaded()

    stmtTags = EdgarMapper.classifyTagsByStmt()
    ciTags = stmtTags.get("CI", set())
    ciTagsLower = {t.lower() for t in ciTags}

    edgarDir = Path(config.dataDir) / "edgar" / "finance"
    parquetFiles = sorted(edgarDir.glob("*.parquet"))
    totalFiles = len(parquetFiles)
    sample = min(totalFiles, 500)
    step = max(1, totalFiles // sample)
    scanFiles = parquetFiles[::step][:sample]

    ciHit = 0
    ciTagFreq: dict[str, int] = {}

    for i, fp in enumerate(scanFiles):
        df = pl.read_parquet(fp)
        df = df.filter(pl.col("namespace") == "us-gaap")
        tags = df.select("tag").unique().to_series().to_list()
        tagsLowerSet = {t.lower() for t in tags}

        matched = ciTagsLower & tagsLowerSet
        if matched:
            ciHit += 1
            for tag in matched:
                ciTagFreq[tag] = ciTagFreq.get(tag, 0) + 1

        if (i + 1) % 100 == 0:
            print(f"  스캔 {i + 1}/{sample}...")

    print(f"\n=== CI 커버리지 (보강 후, {sample}개 샘플) ===")
    print(f"CI commonTags 보유 기업: {ciHit}/{sample} ({ciHit / sample * 100:.1f}%)")
    print(f"\n--- CI 태그 빈도 Top 15 ---")
    for tag, cnt in sorted(ciTagFreq.items(), key=lambda x: -x[1])[:15]:
        print(f"  {tag}: {cnt}/{sample} ({cnt / sample * 100:.1f}%)")

    return ciHit, sample


def main():
    print("=== 1단계: standardAccounts.json CI 보강 ===")
    added = boostStandardAccounts()
    if added == 0:
        print("  이미 보강됨 (재실행)")

    print("\n=== 2단계: CI 커버리지 측정 ===")
    ciHit, sample = measureCoverage()

    print(f"\n=== 최종 비교 ===")
    print(f"  보강 전: 70/500 (14.0%)")
    print(f"  보강 후: {ciHit}/{sample} ({ciHit / sample * 100:.1f}%)")


if __name__ == "__main__":
    main()
