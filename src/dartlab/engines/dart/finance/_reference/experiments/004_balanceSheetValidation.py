"""
실험 ID: 004
실험명: BS 회계 항등식 검증 (자산 = 부채 + 자본) 전종목 통과율

목적:
- 매핑이 정확하다면 BS 항등식 (자산총계 = 부채총계 + 자본총계)이 성립해야 함
- 전종목의 최신 BS 데이터에 대해 항등식 통과율 측정
- 오차가 큰 종목을 식별하여 매핑 오류 또는 데이터 품질 문제 파악
- 추가로 유동/비유동 분해 검증 (유동자산+비유동자산 ≈ 자산총계)

가설:
1. 자산=부채+자본 항등식은 95%+ 종목에서 오차 1% 이내로 성립
2. 유동+비유동 분해도 90%+ 종목에서 성립
3. 오차가 큰 종목은 매핑 오류(특히 003에서 발견된 오매핑)가 원인

방법:
1. 전체 finance parquet에서 BS 데이터만 추출
2. mapper.map() + SNAKE_ALIASES 적용하여 snakeId 변환
3. 최신 분기의 total_assets, total_liabilities, equity_including_nci 값 추출
4. |자산 - (부채+자본)| / 자산 으로 오차율 계산
5. 유동자산+비유동자산 vs 자산총계도 검증

결과 (2026-03-09 실행):

1) 자산 = 부채 + 자본 항등식 (2,563개 종목)
   | 오차 구간 | 종목수 | 비율 |
   |-----------|--------|------|
   | 정확(0%) | 2,556 | 99.7% |
   | 0~0.01% | 3 | 0.1% |
   | 0.01~0.1% | 1 | 0.0% |
   | 0.1~1% | 1 | 0.0% |
   | 1~5% | 1 | 0.0% |
   | 5%+ | 1 | 0.0% |
   → 오차 1% 이내: 99.9% (2,561/2,563)
   → 정확 일치: 99.7% (2,556/2,563)

2) 유동 + 비유동 = 자산총계 (2,506개 종목)
   → 오차 1% 이내: 99.1% (2,484/2,506)
   → 정확 일치: 98.3% (2,463/2,506)
   → 10%+ 오차: 12개 (0.5%)

3) 오차 종목
   053620: 10.3% 오차 (자산 2,439억, 부채+자본 합계 2,189억)
   032830: 3.0% 오차 (자산 319조, 부채+자본 합계 328조) → 금융업 추정

결론:
- 가설1 채택: 자산=부채+자본 항등식 99.9% 통과 (1% 이내 기준) → 사실상 완벽
- 가설2 채택: 유동+비유동 분해도 99.1% 통과
- 가설3 미확인: 오차 종목이 2개뿐이라 패턴 분석 불가. 금융업 특수 구조 가능성

핵심 발견
- BS 3대 총계(자산/부채/자본) 매핑은 사실상 완벽 → 신뢰 가능
- 003에서 발견된 오매핑은 BS가 아닌 IS/CF 쪽 문제 (BS에는 영향 없음)
- 유동+비유동 분해에서 10%+ 오차 12개 → 금융업 or 비표준 BS 구조 종목

실험일: 2026-03-09
"""

import sys
import polars as pl
from pathlib import Path
from collections import defaultdict

sys.path.insert(0, str(Path(__file__).resolve().parents[5]))
from dartlab.engines.dart.finance.mapper import AccountMapper
from dartlab.engines.dart.finance.pivot import SNAKE_ALIASES

FINANCE_DIR = Path("C:/Users/MSI/OneDrive/Desktop/sideProject/nicegui/eddmpython/data/dartData/finance")

mapper = AccountMapper.get()

parquetFiles = sorted(f for f in FINANCE_DIR.glob("*.parquet") if not f.name.startswith("_"))
print(f"총 parquet 파일: {len(parquetFiles)}개")

results = []
detailErrors = []

for i, fp in enumerate(parquetFiles):
    df = pl.read_parquet(fp)
    required = {"sj_div", "account_id", "account_nm", "thstrm_amount", "bsns_year", "reprt_code"}
    if not required.issubset(set(df.columns)):
        continue

    bsDf = df.filter(pl.col("sj_div") == "BS")
    if bsDf.is_empty():
        continue

    cfs = bsDf.filter(pl.col("fs_div") == "CFS") if "fs_div" in bsDf.columns else pl.DataFrame()
    if cfs.is_empty():
        cfs = bsDf.filter(pl.col("fs_div") == "OFS") if "fs_div" in bsDf.columns else bsDf

    if cfs.is_empty():
        cfs = bsDf

    latestYear = cfs["bsns_year"].max()
    latest = cfs.filter(pl.col("bsns_year") == latestYear)

    latestReprt = latest["reprt_code"].max()
    latest = latest.filter(pl.col("reprt_code") == latestReprt)

    snakeValues = {}
    for row in latest.iter_rows(named=True):
        accountId = row.get("account_id", "") or ""
        accountNm = row.get("account_nm", "") or ""
        rawAmount = row.get("thstrm_amount")
        if not accountNm or rawAmount is None:
            continue

        if isinstance(rawAmount, str):
            rawAmount = rawAmount.replace(",", "").strip()
            if not rawAmount or rawAmount == "-":
                continue
            rawAmount = float(rawAmount)

        result = mapper.map(accountId, accountNm)
        if result:
            finalId = SNAKE_ALIASES.get(result, result)
            if finalId not in snakeValues:
                snakeValues[finalId] = rawAmount

    totalAssets = snakeValues.get("total_assets")
    totalLiabilities = snakeValues.get("total_liabilities")
    equityNci = snakeValues.get("equity_including_nci")
    currentAssets = snakeValues.get("current_assets")
    nonCurrentAssets = snakeValues.get("non_current_assets")

    if totalAssets and totalLiabilities and equityNci and totalAssets != 0:
        rhs = totalLiabilities + equityNci
        diff = abs(totalAssets - rhs)
        errorRate = diff / abs(totalAssets) * 100

        hasSubBreakdown = currentAssets is not None and nonCurrentAssets is not None
        subError = None
        if hasSubBreakdown and totalAssets != 0:
            subSum = currentAssets + nonCurrentAssets
            subError = abs(totalAssets - subSum) / abs(totalAssets) * 100

        results.append({
            "code": fp.stem,
            "year": latestYear,
            "reprt": latestReprt,
            "assets": totalAssets,
            "liabilities": totalLiabilities,
            "equity": equityNci,
            "rhs": rhs,
            "diff": diff,
            "errorRate": errorRate,
            "subError": subError,
        })

        if errorRate > 1:
            detailErrors.append({
                "code": fp.stem,
                "errorRate": errorRate,
                "assets": totalAssets,
                "liabilities": totalLiabilities,
                "equity": equityNci,
                "diff": diff,
            })

    if (i + 1) % 500 == 0:
        print(f"  진행: {i + 1}/{len(parquetFiles)}...")

print(f"검증 대상: {len(results)}개 종목")
print()

print("=" * 80)
print("1. 자산 = 부채 + 자본 항등식 검증")
print("=" * 80)

ranges = {"정확 (0%)": 0, "0~0.01%": 0, "0.01~0.1%": 0, "0.1~1%": 0, "1~5%": 0, "5%+": 0}
for r in results:
    e = r["errorRate"]
    if e == 0:
        ranges["정확 (0%)"] += 1
    elif e <= 0.01:
        ranges["0~0.01%"] += 1
    elif e <= 0.1:
        ranges["0.01~0.1%"] += 1
    elif e <= 1:
        ranges["0.1~1%"] += 1
    elif e <= 5:
        ranges["1~5%"] += 1
    else:
        ranges["5%+"] += 1

total = len(results)
for label, cnt in ranges.items():
    pct = cnt / total * 100
    bar = "#" * int(pct / 2)
    print(f"  {label:>15}: {cnt:>5}개 ({pct:>5.1f}%) {bar}")

within1 = sum(1 for r in results if r["errorRate"] <= 1)
within01 = sum(1 for r in results if r["errorRate"] <= 0.1)
exact = sum(1 for r in results if r["errorRate"] == 0)
print(f"\n  정확 일치: {exact:,}개 ({exact/total*100:.1f}%)")
print(f"  오차 0.1% 이내: {within01:,}개 ({within01/total*100:.1f}%)")
print(f"  오차 1% 이내: {within1:,}개 ({within1/total*100:.1f}%)")

print()
print("=" * 80)
print("2. 유동 + 비유동 = 자산총계 검증")
print("=" * 80)

subResults = [r for r in results if r["subError"] is not None]
if subResults:
    subRanges = {"정확 (0%)": 0, "0~1%": 0, "1~5%": 0, "5~10%": 0, "10%+": 0}
    for r in subResults:
        e = r["subError"]
        if e == 0:
            subRanges["정확 (0%)"] += 1
        elif e <= 1:
            subRanges["0~1%"] += 1
        elif e <= 5:
            subRanges["1~5%"] += 1
        elif e <= 10:
            subRanges["5~10%"] += 1
        else:
            subRanges["10%+"] += 1

    subTotal = len(subResults)
    for label, cnt in subRanges.items():
        pct = cnt / subTotal * 100
        print(f"  {label:>15}: {cnt:>5}개 ({pct:>5.1f}%)")

    subWithin1 = sum(1 for r in subResults if r["subError"] <= 1)
    print(f"\n  검증 대상: {subTotal:,}개 (유동/비유동 모두 보유)")
    print(f"  오차 1% 이내: {subWithin1:,}개 ({subWithin1/subTotal*100:.1f}%)")

print()
print("=" * 80)
print("3. 오차 1% 초과 종목 (상위 20개)")
print("=" * 80)

detailErrors.sort(key=lambda x: -x["errorRate"])
if detailErrors:
    print(f"  총 {len(detailErrors)}개 종목이 오차 1% 초과")
    print(f"  {'종목':>10} {'오차율':>8} {'자산':>15} {'부채':>15} {'자본':>15} {'차이':>15}")
    print(f"  {'-'*80}")
    for r in detailErrors[:20]:
        print(f"  {r['code']:>10} {r['errorRate']:>7.1f}% {r['assets']:>15,.0f} {r['liabilities']:>15,.0f} {r['equity']:>15,.0f} {r['diff']:>15,.0f}")
else:
    print("  오차 1% 초과 종목 없음")

print()
print("=" * 80)
print("4. 종합 평가")
print("=" * 80)
grade = "우수" if within1 / total >= 0.95 else "양호" if within1 / total >= 0.90 else "보통"
print(f"  항등식 통과율 (1% 이내): {within1/total*100:.1f}% → {grade}")
print(f"  정확 일치율: {exact/total*100:.1f}%")
