"""
실험 ID: 007
실험명: CORE_MAP 제거 후 v8 체계 전종목 매핑률 측정 + 미매핑 패턴 분석

목적:
- CORE_MAP/SNAKE_ALIASES 제거하고 accountMappings.json만 사용하는 현재 mapper가
  실제 전종목 데이터에서 어떤 매핑률을 보이는지 측정
- 미매핑 계정을 패턴별로 분류하여 학습 보강 대상 식별
- 핵심 계정(IS/BS/CF 주요 snakeId) 커버리지 확인

가설:
1. 전체 매핑률은 001 실험(96.49%)과 유사하거나 약간 하락 (CORE_MAP 제거 영향)
2. 핵심 21개 계정은 accountMappings.json에 이미 포함되어 99%+ 유지
3. 미매핑은 CF 세부 증감항목, SCE 세부항목에 집중

방법:
1. eddmpython finance parquet 전수 읽기
2. 현재 dartlab mapper.map() 실행
3. 전체/재무제표별/종목별 매핑률 집계
4. 미매핑 계정 빈도순 + 패턴별 분류
5. 핵심 snakeId별 커버리지 (standardAccounts 기준)

결과 (실험 후 작성):

[Phase 1] CORE_MAP 제거 직후 (accountMappings.json만 사용)
- 전체 매핑률: 96.49% (1,163,600/1,205,941) — 001 실험과 동일
- 재무제표별:
  | BS 98.91% | IS 94.16% | CIS 97.31% | CF 95.68% | SCE 91.60% |
- 종목 분포: 100% 172개, 99%+ 496개, 95%+ 2,291개, <80% 0개
- 최하위: 100790(82.7%), 041460(84.1%)

[Phase 2] 수동 학습 보강 후 (78개 매핑 추가, 34,171→34,249)
- 전체 매핑률: 96.87% (1,168,249/1,205,941) → +0.38%p
- 재무제표별:
  | BS 98.94% | IS 98.39% | CIS 97.84% | CF 95.98% | SCE 93.13% |
- 미매핑: 42,341→37,692 (-4,649개)
- SCE: 91.60%→93.13% (+1.53%p) 최대 개선

미매핑 패턴 분류 (Phase 1 기준):
1. CF증감 세부항목 (56종, 2,641발생) — 충당부채/선급/예수금 증감 내역
2. SCE 세부항목 (23종, 624발생) — 합병/전환/자기주식 내역
3. 괄호변형 (11종, 612발생) — 공백 있는 계정명의 괄호 내 변형
4. 기타 (110종, 3,510발생) — 회사 고유 계정

학습 보강 내역:
- 1차(22개): CIS 매출원가 세부, BS 금융기관차입금, SCE 배당/전환사채, CF 고빈도(VAT/법인세)
- 2차(56개): CF 증감 세부(26개), SCE 세부(30개)
- 공백 있는 계정명이 미매핑의 주원인 (공백 없는 버전은 이미 매핑 존재)

결론:
1. 가설 1 채택: CORE_MAP 제거 후에도 매핑률 96.49% 동일 유지 → CORE_MAP은 불필요했음
2. 가설 2 채택: 핵심 계정은 accountMappings.json에 이미 포함 (BS total_assets 100%, CF operating_cashflow 98.4%)
3. 가설 3 채택: 미매핑은 CF 증감 세부/SCE 세부에 집중 (핵심 계정 아님)
4. 수동 학습으로 96.49%→96.87% 개선 가능, 97% 돌파에는 공백 정규화 로직 필요
5. 핵심 발견: CIS(포괄손익)에 대부분의 IS 데이터 포함 (IS sj_div는 K-GAAP만)

실험일: 2026-03-10
"""

import sys
import json
import re
import polars as pl
from pathlib import Path
from collections import Counter, defaultdict

sys.path.insert(0, str(Path(__file__).resolve().parents[4]))
from dartlab.providers.dart.finance.mapper import AccountMapper

FINANCE_DIR = Path("C:/Users/MSI/OneDrive/Desktop/sideProject/nicegui/eddmpython/data/dartData/finance")

mapper = AccountMapper.get()

parquetFiles = sorted(f for f in FINANCE_DIR.glob("*.parquet") if not f.name.startswith("_"))
print(f"총 parquet 파일: {len(parquetFiles)}개")

totalAccounts = 0
mappedAccounts = 0
unmappedCounter = Counter()
unmappedWithId = Counter()
byStatement = defaultdict(lambda: {"total": 0, "mapped": 0})
companyStats = []

CORE_SNAKEIDS = {
    "IS": ["sales", "cost_of_sales", "gross_profit", "operating_profit",
           "net_profit", "profit_before_tax", "income_taxes",
           "selling_and_administrative_expenses", "finance_income", "finance_costs",
           "basic_earnings_per_share", "diluted_earnings_per_share"],
    "BS": ["total_assets", "current_assets", "noncurrent_assets",
           "cash_and_cash_equivalents", "inventories", "trade_and_other_receivables",
           "tangible_assets", "intangible_assets",
           "total_liabilities", "current_liabilities", "noncurrent_liabilities",
           "shortterm_borrowings", "longterm_borrowings", "debentures",
           "owners_of_parent_equity", "total_stockholders_equity",
           "retained_earnings", "paidin_capital"],
    "CF": ["operating_cashflow", "investing_cashflow",
           "cash_flows_from_financing_activities"],
}

coreCoverage = defaultdict(lambda: {"present": 0, "mapped": 0, "total": 0})

for i, fp in enumerate(parquetFiles):
    df = pl.read_parquet(fp)
    if "account_id" not in df.columns or "account_nm" not in df.columns:
        continue

    unique = df.select(["sj_div", "account_id", "account_nm"]).unique()
    compTotal = 0
    compMapped = 0

    compSnakeIds = defaultdict(set)

    for row in unique.iter_rows(named=True):
        sjDiv = row.get("sj_div", "")
        accountId = row.get("account_id", "") or ""
        accountNm = row.get("account_nm", "") or ""
        if not accountNm:
            continue

        totalAccounts += 1
        compTotal += 1
        result = mapper.map(accountId, accountNm)

        byStatement[sjDiv]["total"] += 1

        if result:
            mappedAccounts += 1
            compMapped += 1
            byStatement[sjDiv]["mapped"] += 1
            compSnakeIds[sjDiv].add(result)
        else:
            unmappedCounter[accountNm] += 1
            unmappedWithId[(sjDiv, accountId, accountNm)] += 1

    for sjDiv, sids in CORE_SNAKEIDS.items():
        for sid in sids:
            coreCoverage[sid]["total"] += 1
            if sid in compSnakeIds.get(sjDiv, set()):
                coreCoverage[sid]["present"] += 1
                coreCoverage[sid]["mapped"] += 1

    if compTotal > 0:
        rate = compMapped / compTotal * 100
        companyStats.append((fp.stem, rate, compTotal, compTotal - compMapped))

    if (i + 1) % 500 == 0:
        print(f"  진행: {i + 1}/{len(parquetFiles)}...")

print(f"분석 완료: {len(companyStats)}개 종목")
print()

print("=" * 70)
print("1. 전체 매핑률")
print("=" * 70)
rate = mappedAccounts / totalAccounts * 100 if totalAccounts > 0 else 0
print(f"총 고유 계정: {totalAccounts:,}개")
print(f"매핑 성공: {mappedAccounts:,}개 ({rate:.2f}%)")
print(f"미매핑: {totalAccounts - mappedAccounts:,}개 ({100 - rate:.2f}%)")
print()

print("=" * 70)
print("2. 재무제표별 매핑률")
print("=" * 70)
for stmt in ["BS", "IS", "CIS", "CF", "SCE"]:
    if stmt in byStatement:
        s = byStatement[stmt]
        r = s["mapped"] / s["total"] * 100 if s["total"] > 0 else 0
        print(f"  {stmt:>5}: {s['mapped']:>8,} / {s['total']:>8,}  ({r:.2f}%)")
print()

print("=" * 70)
print("3. 종목별 매핑률 분포")
print("=" * 70)
ranges = {"100%": 0, "99-100%": 0, "95-99%": 0, "90-95%": 0, "80-90%": 0, "<80%": 0}
for _, r, _, _ in companyStats:
    if r == 100:
        ranges["100%"] += 1
    elif r >= 99:
        ranges["99-100%"] += 1
    elif r >= 95:
        ranges["95-99%"] += 1
    elif r >= 90:
        ranges["90-95%"] += 1
    elif r >= 80:
        ranges["80-90%"] += 1
    else:
        ranges["<80%"] += 1

for label, cnt in ranges.items():
    pct = cnt / len(companyStats) * 100
    bar = "#" * int(pct / 2)
    print(f"  {label:>10}: {cnt:>5}개 ({pct:>5.1f}%) {bar}")
print()

print("=" * 70)
print("4. 핵심 snakeId 커버리지")
print("=" * 70)
nCompanies = len(companyStats)
for sjDiv, sids in CORE_SNAKEIDS.items():
    print(f"  [{sjDiv}]")
    for sid in sids:
        c = coreCoverage[sid]
        pRate = c["present"] / nCompanies * 100 if nCompanies > 0 else 0
        status = "OK" if pRate >= 90 else "WARN" if pRate >= 70 else "LOW"
        print(f"    [{status:>4}] {sid:45s} {c['present']:>5}/{nCompanies} ({pRate:.1f}%)")
    print()

print("=" * 70)
print("5. 미매핑 계정 상위 50개 (빈도순)")
print("=" * 70)
for i, (nm, cnt) in enumerate(unmappedCounter.most_common(50), 1):
    print(f"  {i:>3}. [{cnt:>4}] {nm}")
print()

print("=" * 70)
print("6. 미매핑 계정 패턴 분류")
print("=" * 70)

patterns = {
    "CF증감": [],
    "SCE세부": [],
    "괄호변형": [],
    "회사고유": [],
    "기타": [],
}

for nm, cnt in unmappedCounter.most_common(200):
    if any(kw in nm for kw in ["증가", "감소", "증감", "의증가", "의감소"]):
        patterns["CF증감"].append((nm, cnt))
    elif any(kw in nm for kw in ["총포괄", "이익잉여금", "자본금", "기타포괄", "자기주식", "주식선택권"]):
        patterns["SCE세부"].append((nm, cnt))
    elif "(" in nm or ")" in nm:
        patterns["괄호변형"].append((nm, cnt))
    elif cnt <= 5:
        patterns["회사고유"].append((nm, cnt))
    else:
        patterns["기타"].append((nm, cnt))

for pName, items in patterns.items():
    totalCnt = sum(c for _, c in items)
    print(f"  {pName}: {len(items)}개 고유 계정, {totalCnt:,} 발생")
    for nm, cnt in items[:5]:
        print(f"    [{cnt:>4}] {nm}")
    if len(items) > 5:
        print(f"    ... +{len(items) - 5}개")
    print()

print("=" * 70)
print("7. 미매핑 중 학습 가능한 후보 (빈도 10+ 계정)")
print("=" * 70)
print("  다음 계정들은 적절한 snakeId에 매핑하면 매핑률 개선 가능:")
print()

candidates = [(nm, cnt) for nm, cnt in unmappedCounter.most_common() if cnt >= 10]
print(f"  총 {len(candidates)}개 (빈도 10+)")
for nm, cnt in candidates[:30]:
    print(f"  [{cnt:>4}] {nm}")
print()

print("=" * 70)
print("8. 매핑률 최하위 종목 10개")
print("=" * 70)
companyStats.sort(key=lambda x: x[1])
for code, r, total, unmapped in companyStats[:10]:
    print(f"  {code}: {r:.1f}% ({unmapped}/{total} unmapped)")
print()

print("=" * 70)
print("9. 종합 평가")
print("=" * 70)
if rate >= 95:
    grade = "우수"
elif rate >= 90:
    grade = "양호"
elif rate >= 80:
    grade = "보통"
else:
    grade = "개선 필요"
print(f"전체 매핑률: {rate:.2f}% → {grade}")
pct100 = ranges["100%"] / len(companyStats) * 100
pct99 = (ranges["100%"] + ranges["99-100%"]) / len(companyStats) * 100
print(f"100% 매핑 종목: {ranges['100%']}개 ({pct100:.1f}%)")
print(f"99%+ 매핑 종목: {ranges['100%'] + ranges['99-100%']}개 ({pct99:.1f}%)")
