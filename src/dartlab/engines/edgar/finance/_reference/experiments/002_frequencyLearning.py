"""
실험 ID: 002
실험명: 태그 빈도 기반 매핑 학습

목적:
- DART 학습 메커니즘 적용: 태그 빈도 → 정규화 계정 → 역태그 학습
- 16,601개 CIK에서 미매핑 태그의 출현 빈도 측정
- 빈도 높은 미매핑 태그를 표준계정에 매핑하여 매핑률 향상
- 학습 전/후 매핑률 비교

가설:
1. 미매핑 태그 중 50개 이상이 10사+ 공통 출현 → 학습 시 매핑률 2%+ 향상
2. 이미 매핑된 태그와 camelCase 분리 기반 유사도로 자동 후보 제안 가능
3. 학습 후 핵심 21개 계정 커버리지 95%+ 달성

방법:
1. 전체 16,601개 CIK에서 us-gaap 태그 수집 (샘플 1000개)
2. 미매핑 태그의 CIK 출현 빈도 집계
3. 빈도 상위 태그 분석 → 어떤 snakeId에 매핑해야 하는지 판단
4. autoClassify 로직으로 자동 분류 가능한 것 식별
5. 학습 적용 후 001 실험 재실행

결과 (실험 후 작성):

[태그 스캔] 1000 CIK 샘플
  고유 태그: 8,446개
  매핑됨: 7,591개 (89.9%)
  미매핑: 855개 (10.1%)

[미매핑 상위 50] 대부분 Notes 주석 성격
  DeferredTax*: 17개 (deferred_tax_assets/liabilities)
  FiniteLivedIntangible*: 7개 (depreciation_amortization)
  UnrecognizedTaxBenefits*: 5개 (unrecognized_tax_benefits)
  IncomeTaxReconciliation*: 4개 (income_tax_detail)
  자동 분류 가능: 43/50 (86%)
  핵심 계정 후보: 0개 ← 미매핑이 핵심 계정과 무관!

[핵심 발견] 핵심 계정은 이미 매핑됨!
  cost_of_sales: CostOfRevenue(260), CostOfGoodsAndServicesSold(259), CostOfGoodsSold(159) → 모두 매핑됨
  gross_profit: GrossProfit(413) → 매핑됨
  operating_income: OperatingIncomeLoss(754) → 매핑됨
  non_current_assets: AssetsNoncurrent(149) → non_current_assets 매핑됨
                      NoncurrentAssets(119) → other_noncurrent_assets (잘못 매핑!!)
  total_liabilities: Liabilities(844) → 매핑됨

  ★ 001 실험에서 핵심 계정 누락은 "태그 자체가 없는 것"이 원인
    - JPM은 cost_of_sales 태그를 보고 안 함 (금융업)
    - 일부 기업은 gross_profit을 보고 안 함 (자체 계산 필요)

[NoncurrentAssets 오매핑 발견]
  NoncurrentAssets → other_noncurrent_assets (❌ 잘못됨)
  AssetsNoncurrent → non_current_assets (✅ 정확)
  → NoncurrentAssets도 non_current_assets에 매핑해야 함

[학습 영향도]
  현재 태그 기반 매핑률: 89.9%
  자동 분류 43개 추가 시: 90.4% (+0.5%)
  ← 미매핑 태그가 Notes 성격이라 매핑률 향상 효과 작음
  ← 하지만 NoncurrentAssets 오매핑 수정은 핵심 계정 커버리지에 직접 영향

결론:
- 가설1 부분 채택: 미매핑 태그 280개가 10CIK+ 출현, 하지만 대부분 Notes 주석 → 매핑률 향상 1% 미만
- 가설2 채택: autoClassify로 43/50 자동 분류 가능
- 가설3 수정: 핵심 계정은 이미 매핑됨. 누락은 기업이 보고 안 하는 것이 원인
- ★ NoncurrentAssets → non_current_assets 오매핑 수정 필요 (즉시 반영 가능)
- 학습 우선순위: Notes 태그 자동 분류보다 오매핑 수정이 더 급함
- 다음 실험: gross_profit 자체 계산(revenue - cost_of_sales) 검증

실험일: 2026-03-10
"""

import sys
import re
from pathlib import Path
from collections import Counter

PROJECT_ROOT = Path(__file__).resolve().parents[7]
sys.path.insert(0, str(PROJECT_ROOT / "src"))

import polars as pl
from dartlab.engines.edgar.finance.mapper import EdgarMapper

EDGAR_DIR = PROJECT_ROOT / "data" / "edgar" / "finance"


def splitCamelCase(tag: str) -> str:
    """CamelCase → 공백 분리."""
    s = re.sub(r"([a-z0-9])([A-Z])", r"\1 \2", tag)
    s = re.sub(r"([A-Z]+)([A-Z][a-z])", r"\1 \2", s)
    return s.lower()


def scanAllTags(sampleSize: int = 1000) -> dict:
    """전체 CIK에서 태그 스캔."""
    parquets = sorted(EDGAR_DIR.glob("*.parquet"))
    if sampleSize and sampleSize < len(parquets):
        import random
        random.seed(42)
        parquets = random.sample(parquets, sampleSize)

    tagCounts = Counter()
    mappedTagCounts = Counter()
    unmappedTagCounts = Counter()
    unmappedTagExamples = {}
    totalCiks = 0

    for p in parquets:
        cik = p.stem
        try:
            df = pl.read_parquet(p)
            df = df.filter(pl.col("namespace") == "us-gaap")
        except Exception:
            continue

        tags = df.select("tag").unique().to_series().to_list()
        totalCiks += 1

        for tag in tags:
            tagCounts[tag] += 1
            sid = EdgarMapper.mapToDart(tag)
            if sid is not None:
                mappedTagCounts[tag] += 1
            else:
                unmappedTagCounts[tag] += 1
                if tag not in unmappedTagExamples:
                    unmappedTagExamples[tag] = splitCamelCase(tag)

    return {
        "totalCiks": totalCiks,
        "totalUniqueTags": len(tagCounts),
        "mappedUniqueTags": len(mappedTagCounts),
        "unmappedUniqueTags": len(unmappedTagCounts),
        "tagCounts": tagCounts,
        "unmappedTagCounts": unmappedTagCounts,
        "unmappedTagExamples": unmappedTagExamples,
    }


def analyzeUnmappedPatterns(scanResult: dict, topN: int = 100) -> list[dict]:
    """미매핑 태그 패턴 분석 + 매핑 후보 제안."""
    unmapped = scanResult["unmappedTagCounts"]
    examples = scanResult["unmappedTagExamples"]
    totalCiks = scanResult["totalCiks"]

    topTags = unmapped.most_common(topN)

    results = []
    for tag, count in topTags:
        readable = examples.get(tag, tag)
        prevalence = count / totalCiks * 100

        suggestedSid = suggestSnakeId(tag)

        results.append({
            "tag": tag,
            "readable": readable,
            "cikCount": count,
            "prevalence": prevalence,
            "suggestedSnakeId": suggestedSid,
            "autoClassifiable": suggestedSid is not None,
        })

    return results


def suggestSnakeId(tag: str) -> str | None:
    """태그 이름 기반 snakeId 제안 (batchLearner autoClassify 확장)."""
    t = tag.lower()

    if "deferredtaxasset" in t:
        return "deferred_tax_assets"
    if "deferredtaxliabilit" in t:
        return "deferred_tax_liabilities"
    if "deferredtax" in t and "expense" in t:
        return "income_tax_expense"
    if "deferredtax" in t:
        return "deferred_tax_detail"

    if "finitelivedintangible" in t:
        if "amortization" in t:
            return "depreciation_amortization"
        return "intangible_assets_detail"

    if "unrecognizedtaxbenefit" in t:
        return "unrecognized_tax_benefits"

    if "incometaxreconciliation" in t:
        return "income_tax_detail"

    if "goodwill" in t:
        if "impairment" in t:
            return "goodwill_impairment"
        return "goodwill"

    if "operatingleaserightofuse" in t:
        return "right_of_use_assets"
    if "operatingleaseliabilit" in t:
        if "noncurrent" in t:
            return "operating_lease_liability_noncurrent"
        if "current" in t:
            return "operating_lease_liability_current"
        return "operating_lease_liability"
    if "operatinglease" in t:
        return "operating_lease_detail"

    if "financeleaseliabilit" in t or "financingleaseliabilit" in t:
        return "finance_lease_liability"
    if "financelease" in t or "financinglease" in t:
        return "finance_lease_detail"

    if "longtermdebtmaturit" in t:
        return "debt_maturity_schedule"

    if "sharebased" in t or "stockbased" in t:
        return "stock_compensation_detail"

    if "revenue" in t and "disaggregat" in t:
        return "revenue_disaggregation"

    if "restructuring" in t:
        return "restructuring_detail"

    if "foreigncurrency" in t or "effectofexchangerate" in t:
        return "fx_effect"

    if "commitmentsandcontingencies" in t:
        return "commitments_contingencies"

    if "othercomprehensiveincome" in t:
        return "other_comprehensive_income_detail"

    if "accruedliabilit" in t:
        return "accrued_liabilities"

    if "costofrevenue" in t or "costofgoodsandservicessold" in t:
        return "cost_of_sales"

    if "grossprofit" in t:
        return "gross_profit"

    if "operatingincome" in t or "operatingloss" in t:
        return "operating_income"

    if "noncurrentasset" in t:
        return "non_current_assets"

    if "liabilit" in t:
        if "total" in t:
            return "total_liabilities"
        if "current" in t and "noncurrent" not in t:
            return "current_liabilities"
        if "noncurrent" in t:
            return "non_current_liabilities"

    return None


def main():
    print("=" * 70)
    print("EDGAR 태그 빈도 기반 매핑 분석")
    print("=" * 70)

    print("\n[1] 전체 CIK 태그 스캔 (1000개 샘플)")
    print("-" * 50)
    scanResult = scanAllTags(sampleSize=1000)

    totalTags = scanResult["totalUniqueTags"]
    mappedTags = scanResult["mappedUniqueTags"]
    unmappedTags = scanResult["unmappedUniqueTags"]

    print(f"  스캔 CIK: {scanResult['totalCiks']}개")
    print(f"  고유 태그: {totalTags}개")
    print(f"  매핑됨: {mappedTags}개 ({mappedTags/totalTags*100:.1f}%)")
    print(f"  미매핑: {unmappedTags}개 ({unmappedTags/totalTags*100:.1f}%)")

    print("\n[2] 미매핑 태그 빈도 상위 50")
    print("-" * 50)
    patterns = analyzeUnmappedPatterns(scanResult, topN=50)

    autoCount = 0
    coreCandidate = 0

    print(f"  {'태그':<55s} {'CIK수':>6s} {'비율':>6s} {'제안 snakeId':<30s}")
    print("  " + "-" * 100)
    for p in patterns:
        marker = "***" if p["suggestedSnakeId"] in [
            "cost_of_sales", "gross_profit", "operating_income",
            "non_current_assets", "total_liabilities",
        ] else "   "
        sugStr = p["suggestedSnakeId"] or "(없음)"
        print(f"  {p['tag']:<55s} {p['cikCount']:>5d} {p['prevalence']:>5.1f}% {sugStr:<30s} {marker}")
        if p["autoClassifiable"]:
            autoCount += 1
        if p["suggestedSnakeId"] in [
            "cost_of_sales", "gross_profit", "operating_income",
            "non_current_assets", "total_liabilities",
            "current_liabilities", "non_current_liabilities",
        ]:
            coreCandidate += 1

    print(f"\n  자동 분류 가능: {autoCount}/50")
    print(f"  핵심 계정 후보: {coreCandidate}개")

    print("\n[3] 핵심 계정 누락 원인 분석")
    print("-" * 50)

    coreGaps = {
        "cost_of_sales": ["CostOfRevenue", "CostOfGoodsAndServicesSold", "CostOfGoodsSold"],
        "gross_profit": ["GrossProfit"],
        "operating_income": ["OperatingIncomeLoss"],
        "non_current_assets": ["NoncurrentAssets", "AssetsNoncurrent"],
        "total_liabilities": ["Liabilities"],
    }

    for sid, possibleTags in coreGaps.items():
        print(f"\n  {sid}:")
        for tag in possibleTags:
            mapped = EdgarMapper.mapToDart(tag)
            freq = scanResult["tagCounts"].get(tag, 0)
            status = f"→ {mapped}" if mapped else "미매핑"
            print(f"    {tag:<45s} {freq:>5d} CIK  {status}")

    print("\n[4] 학습 영향도 시뮬레이션")
    print("-" * 50)

    currentMapped = mappedTags
    newMappable = autoCount
    projectedRate = (currentMapped + newMappable) / totalTags * 100

    print(f"  현재 매핑률: {currentMapped/totalTags*100:.1f}%")
    print(f"  자동 분류 가능 추가: {newMappable}개")
    print(f"  예상 매핑률: {projectedRate:.1f}%")

    print("\n[5] 10사+ 출현 미매핑 태그 전체")
    print("-" * 50)
    highFreq = [(tag, cnt) for tag, cnt in scanResult["unmappedTagCounts"].most_common()
                if cnt >= scanResult["totalCiks"] * 0.01]
    print(f"  1%+ 출현 미매핑: {len(highFreq)}개")

    for tag, cnt in highFreq[:30]:
        sid = suggestSnakeId(tag)
        sidStr = sid or "?"
        print(f"    {cnt:>4d} CIK | {tag:<55s} → {sidStr}")


if __name__ == "__main__":
    main()
