"""
실험 ID: 003
실험명: 같은 snakeId로 매핑된 원본 account_nm 의미 일관성 검증

목적:
- 매핑률/보유율과 별개로, 같은 snakeId에 이질적인 계정명이 섞여 있으면 비교 불가
- 예: "매출액"과 "이자수익"이 모두 revenue로 매핑되면 제조업/금융업 비교 시 오류
- 핵심 snakeId에 매핑된 원본 account_nm 목록을 추출하여 이질성 확인

가설:
1. 핵심 20개 snakeId는 의미적으로 동질적 (같은 개념의 변형만 매핑)
2. 일부 snakeId에 업종 특수 계정이 섞여 있을 수 있음 (특히 revenue, operating_income)
3. ACCOUNT_NAME_SYNONYMS의 합산 매핑(예: 이자수익→금융수익)이 정확한지 확인

방법:
1. 전체 finance parquet에서 각 (account_nm, snakeId) 쌍의 빈도 수집
2. 핵심 snakeId별로 매핑된 원본 account_nm TOP 20 출력
3. 의미적으로 이질적인 매핑이 있는지 수동 판단용 데이터 제공

결과 (2026-03-09 실행):

1) 의미 일관성 높은 snakeId (집중도 90%+, 동질적 변형만)
   total_assets 98.4% (12개 변형 — 모두 "자산총계" 변형)
   total_liabilities 98.5% (11개 변형)
   current_assets 96.7%, non_current_assets 96.8%
   current_liabilities 96.6%, non_current_liabilities 96.8%
   → BS 구조 계정은 의미 일관성 우수

2) 의미 일관성 보통 (집중도 50~90%, 같은 개념이지만 표현 다양)
   operating_income 58.4% (71개 — 모두 "영업이익" 변형, 의미 동질)
   gross_profit 90.7% (34개 — "매출총이익" 변형)
   operating_cashflow 67.8% (146개 — "영업활동현금흐름" 변형)
   ppe 80.5% (717개 — 대부분 "유형자산", 일부 하위항목 혼입 주의)
   retained_earnings 51.5% (499개 — "이익잉여금" + "결손금" + SCE항목 혼입)

3) 이질성 의심 snakeId 8개 (집중도 50% 미만)
   | snakeId | 고유명 | 집중도 | 주요 이슈 |
   |---------|--------|--------|-----------|
   | revenue | 350개 | 34.9% | 매출액/수익/영업수익/제품매출/상품매출 혼재 |
   | net_income | 726개 | 37.9% | 당기/반기/분기순이익 + "영업에서창출된현금흐름" 오매핑! |
   | short_term_borrowings | 253개 | 43.6% | 단기차입금 + 유동성장기차입금 + 유동차입금 혼합 |
   | bonds | 1,012개 | 20.1% | 사채/전환사채/신주인수권부사채/교환사채 전부 합산 |
   | total_equity | 335개 | 46.3% | 지배기업 소유주 표현 다양 (의미는 동질) |
   | equity_including_nci | 83개 | 48.1% | 자본총계 + SCE "기말자본" 혼입 |
   | income_tax_expense | 689개 | 48.5% | IS법인세비용 + CF법인세납부 + OCI법인세효과 혼합! |
   | basic_eps | 714개 | 48.0% | 기본/희석 구분 있지만 의미는 동질 |

4) 치명적 오매핑 발견
   - net_income에 "영업에서 창출된 현금흐름"(96건), "소계"(31건) 등 CF항목 혼입
   - income_tax_expense에 "법인세의 납부"(310건, CF항목), "법인세효과"(232건, OCI항목) 혼입
   - bonds에 CF항목("사채발행", "전환사채 보통주 전환" 등) 혼입
   - ppe에 CF항목("시설장치의 처분", "장기투자자산의 취득" 등) 혼입
   - retained_earnings에 "자본잉여금"(12건) 오매핑

5) sga_expenses (판관비) — 매핑 자체가 0건
   accountMappings.json에 sga_expenses로 이어지는 매핑 경로 자체가 없음

결론:
- 가설1 부분기각: BS 구조 계정은 동질적이지만, bonds/short_term_borrowings는 이질적 항목 합산
- 가설2 채택: revenue에 제품매출/상품매출/영업수익이 섞이나, 모두 "매출" 개념이라 의미적으로 동질
- 가설3 관련: net_income, income_tax_expense, ppe, bonds에 CF/OCI 항목이 오매핑되는 심각한 문제 발견

핵심 문제 (우선순위순)
P0: net_income에 CF 항목("영업에서 창출된 현금흐름") 오매핑 → 순이익 수치 오염
P0: income_tax_expense에 CF/OCI 항목 혼입 → IS 법인세와 CF 법인세납부가 합산
P1: bonds에 이질적 사채 종류 전부 합산 → 사채 vs 전환사채 구분 불가
P1: sga_expenses 매핑 경로 없음 → 판관비 분석 불가
P2: retained_earnings에 "자본잉여금" 오매핑
P3: short_term_borrowings에 유동성장기차입금 혼합 (회계상 유동이므로 수용 가능)

실험일: 2026-03-09
"""

import sys
import polars as pl
from pathlib import Path
from collections import defaultdict, Counter

sys.path.insert(0, str(Path(__file__).resolve().parents[5]))
from dartlab.engines.company.dart.finance.mapper import AccountMapper
from dartlab.engines.company.dart.finance.pivot import SNAKE_ALIASES

FINANCE_DIR = Path("C:/Users/MSI/OneDrive/Desktop/sideProject/nicegui/eddmpython/data/dartData/finance")

mapper = AccountMapper.get()

TARGET_SNAKE_IDS = [
    "revenue", "cost_of_sales", "gross_profit",
    "operating_income", "net_income",
    "total_assets", "current_assets", "non_current_assets",
    "cash_and_equivalents", "inventories",
    "total_liabilities", "current_liabilities", "non_current_liabilities",
    "short_term_borrowings", "long_term_borrowings", "bonds",
    "total_equity", "equity_including_nci",
    "operating_cashflow", "investing_cashflow", "financing_cashflow",
    "sga_expenses", "profit_before_tax", "income_tax_expense",
    "basic_eps", "retained_earnings", "ppe",
]

snakeToNames = defaultdict(Counter)

parquetFiles = sorted(f for f in FINANCE_DIR.glob("*.parquet") if not f.name.startswith("_"))
print(f"총 parquet 파일: {len(parquetFiles)}개")

for i, fp in enumerate(parquetFiles):
    df = pl.read_parquet(fp)
    if "account_id" not in df.columns or "account_nm" not in df.columns:
        continue

    unique = df.select(["account_id", "account_nm"]).unique()

    for row in unique.iter_rows(named=True):
        accountId = row.get("account_id", "") or ""
        accountNm = row.get("account_nm", "") or ""
        if not accountNm:
            continue

        result = mapper.map(accountId, accountNm)
        if result:
            finalId = SNAKE_ALIASES.get(result, result)
            if finalId in TARGET_SNAKE_IDS:
                snakeToNames[finalId][accountNm] += 1

    if (i + 1) % 500 == 0:
        print(f"  진행: {i + 1}/{len(parquetFiles)}...")

print(f"분석 완료")
print()

print("=" * 90)
print("핵심 snakeId별 원본 account_nm 목록 (빈도순 TOP 20)")
print("=" * 90)

for snakeId in TARGET_SNAKE_IDS:
    names = snakeToNames.get(snakeId)
    if not names:
        print(f"\n  [{snakeId}] — 매핑된 account_nm 없음 (0건)")
        continue

    totalMappings = sum(names.values())
    uniqueNames = len(names)
    topName, topCount = names.most_common(1)[0]
    concentration = topCount / totalMappings * 100

    print(f"\n  [{snakeId}] 총 {totalMappings:,}건, 고유 {uniqueNames}개, 집중도 {concentration:.1f}% (1위: '{topName}')")
    for rank, (nm, cnt) in enumerate(names.most_common(20), 1):
        pct = cnt / totalMappings * 100
        print(f"    {rank:>3}. [{cnt:>5,}] ({pct:>5.1f}%) {nm}")

print()
print("=" * 90)
print("이질성 의심 snakeId (고유 계정명 10개 이상 + 집중도 50% 미만)")
print("=" * 90)

suspectCount = 0
for snakeId in TARGET_SNAKE_IDS:
    names = snakeToNames.get(snakeId)
    if not names:
        continue
    totalMappings = sum(names.values())
    uniqueNames = len(names)
    topName, topCount = names.most_common(1)[0]
    concentration = topCount / totalMappings * 100

    if uniqueNames >= 10 and concentration < 50:
        suspectCount += 1
        print(f"\n  [{snakeId}] 고유 {uniqueNames}개, 집중도 {concentration:.1f}%")
        for rank, (nm, cnt) in enumerate(names.most_common(10), 1):
            pct = cnt / totalMappings * 100
            print(f"    {rank:>3}. [{cnt:>5,}] ({pct:>5.1f}%) {nm}")

if suspectCount == 0:
    print("  이질성 의심 snakeId 없음")

print()
print("=" * 90)
print("종합 통계")
print("=" * 90)
print(f"  분석 snakeId: {len(TARGET_SNAKE_IDS)}개")
print(f"  매핑 존재: {len(snakeToNames)}개")
print(f"  매핑 부재: {len(TARGET_SNAKE_IDS) - len(snakeToNames)}개")
for sid in TARGET_SNAKE_IDS:
    if sid not in snakeToNames:
        print(f"    - {sid}")
