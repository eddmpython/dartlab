"""
실험 ID: 002
실험명: 핵심 snakeId 전종목 보유율 측정 (비교가능성 기초)

목적:
- 매핑률 96.49%는 "변환 가능 여부"일 뿐, 종목간 비교가능성은 별도 측정 필요
- 핵심 snakeId N개에 대해 전종목 중 몇 %가 해당 값을 실제 보유하는지 측정
- 비교가능성이 높은/낮은 계정을 식별하여 개선 우선순위 결정

가설:
1. BS 핵심 계정(자산총계, 부채총계, 자본총계)은 99%+ 보유율
2. IS 핵심 계정(매출액, 영업이익, 당기순이익)은 95%+ 보유율
3. CF 핵심 계정(영업/투자/재무활동CF)은 90%+ 보유율
4. 금융업 종목은 제조업 표준 계정(재고자산, 매출원가 등)이 누락될 것

방법:
1. 전체 finance parquet 2,743개 로드
2. 각 파일에서 mapper.map() 후 SNAKE_ALIASES 적용하여 최종 snakeId 집합 추출
3. 핵심 snakeId 30+개에 대해 종목별 존재 여부 집계
4. 재무제표별(BS/IS/CF) 계정 보유율 산출
5. 보유율 하위 계정 → 비교가능성 약점 식별

결과 (2026-03-09 실행):

1) 재무제표별 핵심 계정 보유율 (2,564개 종목)
   BS — 100%: total_assets, total_liabilities, equity_including_nci, retained_earnings
         98%+: cash_and_equivalents(98.9%), ppe(98.8%), current_assets(97.9%), non_current_assets(97.8%)
         WARN: inventories(92.2%), short_term_borrowings(91.3%), long_term_borrowings(84.1%), total_equity(86.0%)
         LOW:  bonds(54.9%), issued_capital(68.0%)
         RARE: trade_and_other_current_receivables(0.4%)
   IS — 100%: net_income
         WARN: revenue(93.0%), operating_income(94.2%), profit_before_tax(94.2%)
         LOW:  cost_of_sales(87.2%), gross_profit(86.8%)
         RARE: sga_expenses(0.0%)
   CF — 99.8%+: operating_cashflow, investing_cashflow, financing_cashflow

2) 동시보유율 (비교가능성 핵심)
   | 그룹 | 보유율 | 판정 |
   |------|--------|------|
   | BS 3대 총계 (자산/부채/자본) | 100.0% | OK |
   | CF 3대 흐름 | 99.8% | OK |
   | 수익성 3종 (매출/영업이익/순이익) | 98.7% | OK |
   | 종합 7종 | 98.5% | OK |
   | 안정성 3종 | 97.9% | OK |
   | 밸류에이션 4종 (매출/순이익/자본/자산) | 85.5% | WARN |

3) 약점 계정 15개 (95% 미달)
   sga_expenses 0.0%, trade_and_other_current_receivables 0.4%,
   bonds 54.9%, issued_capital 68.0%, long_term_borrowings 84.1%,
   total_equity 86.0%, gross_profit 86.8%, cost_of_sales 87.2%,
   short_term_borrowings 91.3%, inventories 92.2%, revenue 93.0%,
   basic_eps 93.8%, operating_income 94.2%, profit_before_tax 94.2%,
   income_tax_expense 94.5%

4) 전체 고유 snakeId: 3,271개

결론:
- 가설1 부분채택: BS 3대 총계는 100%지만, total_equity(지배기업귀속)는 86.0%
  → total_equity vs equity_including_nci 구분이 비교가능성의 큰 약점
- 가설2 기각: revenue 93.0%, operating_income 94.2%로 95% 미달
  → IS는 CIS(포괄손익) 종목에서 매출/영업이익이 누락되는 패턴
- 가설3 채택: CF 3대 흐름 99.8%로 사실상 완벽
- 가설4 확인필요: 금융업 누락이 inventories(92.2%), cost_of_sales(87.2%) 원인인지 별도 검증 필요

핵심 발견:
- sga_expenses(판관비) 0.0% → snakeId 매핑 자체가 누락 (mapper에 없음)
- trade_and_other_current_receivables 0.4% → snakeId 이름이 mapper 출력과 불일치 가능
- revenue가 100%가 아닌 이유 → IS가 아닌 CIS만 있는 종목에서 매출 구조가 다름
- 밸류에이션 4종 85.5% → total_equity(지배기업귀속)가 병목

다음 실험: 003에서 같은 snakeId의 원본 account_nm 의미 일관성 검증 필요

실험일: 2026-03-09
"""

import sys
import polars as pl
from pathlib import Path
from collections import defaultdict

sys.path.insert(0, str(Path(__file__).resolve().parents[5]))
from dartlab.engines.company.dart.finance.mapper import AccountMapper
from dartlab.engines.company.dart.finance.pivot import SNAKE_ALIASES

FINANCE_DIR = Path("C:/Users/MSI/OneDrive/Desktop/sideProject/nicegui/eddmpython/data/dartData/finance")

mapper = AccountMapper.get()

KEY_ACCOUNTS = {
    "BS": [
        "total_assets", "current_assets", "non_current_assets",
        "cash_and_equivalents", "inventories", "ppe",
        "trade_and_other_current_receivables",
        "total_liabilities", "current_liabilities", "non_current_liabilities",
        "short_term_borrowings", "long_term_borrowings", "bonds",
        "total_equity", "equity_including_nci",
        "issued_capital", "retained_earnings",
    ],
    "IS": [
        "revenue", "cost_of_sales", "gross_profit",
        "operating_income", "net_income",
        "sga_expenses", "profit_before_tax",
        "income_tax_expense", "basic_eps",
    ],
    "CF": [
        "operating_cashflow", "investing_cashflow", "financing_cashflow",
    ],
}

ALL_KEY_IDS = set()
for ids in KEY_ACCOUNTS.values():
    ALL_KEY_IDS.update(ids)

parquetFiles = sorted(f for f in FINANCE_DIR.glob("*.parquet") if not f.name.startswith("_"))
print(f"총 parquet 파일: {len(parquetFiles)}개")

coverage = defaultdict(lambda: defaultdict(int))
totalByStmt = defaultdict(int)
companyAccounts = {}

for i, fp in enumerate(parquetFiles):
    df = pl.read_parquet(fp)
    if "account_id" not in df.columns or "account_nm" not in df.columns:
        continue

    unique = df.select(["sj_div", "account_id", "account_nm"]).unique()

    snakeIdsByStmt = defaultdict(set)

    for row in unique.iter_rows(named=True):
        sjDiv = row.get("sj_div", "")
        accountId = row.get("account_id", "") or ""
        accountNm = row.get("account_nm", "") or ""
        if not accountNm:
            continue

        result = mapper.map(accountId, accountNm)
        if result:
            finalId = SNAKE_ALIASES.get(result, result)
            snakeIdsByStmt[sjDiv].add(finalId)

    for sjDiv in ["BS", "IS", "CIS", "CF"]:
        if sjDiv in snakeIdsByStmt:
            stmtKey = "IS" if sjDiv == "CIS" else sjDiv
            totalByStmt[stmtKey] += 1
            for snakeId in snakeIdsByStmt[sjDiv]:
                coverage[stmtKey][snakeId] += 1

    allIds = set()
    for ids in snakeIdsByStmt.values():
        allIds.update(ids)
    companyAccounts[fp.stem] = allIds

    if (i + 1) % 500 == 0:
        print(f"  진행: {i + 1}/{len(parquetFiles)}...")

totalCompanies = len(companyAccounts)
print(f"분석 완료: {totalCompanies}개 종목")
print()

print("=" * 80)
print("1. 핵심 계정 보유율 — 재무제표별")
print("=" * 80)

for stmt in ["BS", "IS", "CF"]:
    stmtTotal = totalByStmt.get(stmt, 0)
    print(f"\n  [{stmt}] (해당 재무제표 보유 종목: {stmtTotal:,}개)")
    print(f"  {'snakeId':<45} {'보유':<8} {'보유율':<8} {'판정'}")
    print(f"  {'-'*75}")

    for snakeId in KEY_ACCOUNTS[stmt]:
        cnt = coverage[stmt].get(snakeId, 0)
        rate = cnt / stmtTotal * 100 if stmtTotal > 0 else 0
        grade = "OK" if rate >= 95 else "WARN" if rate >= 80 else "LOW" if rate >= 50 else "RARE"
        print(f"  {snakeId:<45} {cnt:>6,} {rate:>6.1f}%  {grade}")

print()
print("=" * 80)
print("2. 전체 snakeId 보유율 TOP/BOTTOM (모든 재무제표 통합)")
print("=" * 80)

globalCoverage = defaultdict(int)
for comp, ids in companyAccounts.items():
    for sid in ids:
        globalCoverage[sid] += 1

sortedAll = sorted(globalCoverage.items(), key=lambda x: -x[1])

print(f"\n  전체 종목: {totalCompanies:,}개")
print(f"  전체 고유 snakeId: {len(sortedAll)}개")
print()

print(f"  --- TOP 30 (보유율 높은 순) ---")
print(f"  {'snakeId':<50} {'보유':<8} {'보유율'}")
for sid, cnt in sortedAll[:30]:
    rate = cnt / totalCompanies * 100
    print(f"  {sid:<50} {cnt:>6,} {rate:>6.1f}%")

print()
print(f"  --- BOTTOM 30 (보유율 낮은 순, 10건 이상만) ---")
bottomFiltered = [(sid, cnt) for sid, cnt in sortedAll if cnt >= 10]
for sid, cnt in bottomFiltered[-30:]:
    rate = cnt / totalCompanies * 100
    print(f"  {sid:<50} {cnt:>6,} {rate:>6.1f}%")

print()
print("=" * 80)
print("3. 핵심 계정 전종목 동시보유율 (비교가능성 핵심)")
print("=" * 80)

coreGroups = {
    "수익성 3종 (revenue + operating_income + net_income)": ["revenue", "operating_income", "net_income"],
    "BS 3대 총계 (total_assets + total_liabilities + equity_including_nci)": ["total_assets", "total_liabilities", "equity_including_nci"],
    "CF 3대 흐름 (operating + investing + financing)": ["operating_cashflow", "investing_cashflow", "financing_cashflow"],
    "밸류에이션 4종 (revenue + net_income + total_equity + total_assets)": ["revenue", "net_income", "total_equity", "total_assets"],
    "안정성 3종 (total_liabilities + current_liabilities + non_current_liabilities)": ["total_liabilities", "current_liabilities", "non_current_liabilities"],
    "종합 7종 (매출+영업이익+순이익+자산+부채+자본+영업CF)": ["revenue", "operating_income", "net_income", "total_assets", "total_liabilities", "equity_including_nci", "operating_cashflow"],
}

for label, ids in coreGroups.items():
    cnt = sum(1 for comp, allIds in companyAccounts.items() if all(sid in allIds for sid in ids))
    rate = cnt / totalCompanies * 100
    grade = "OK" if rate >= 90 else "WARN" if rate >= 70 else "LOW"
    print(f"  [{grade:>4}] {label}")
    print(f"         {cnt:>5,} / {totalCompanies:,} ({rate:.1f}%)")
    print()

print("=" * 80)
print("4. 비교가능성 약점 계정 (핵심인데 보유율 낮은 것)")
print("=" * 80)

weakAccounts = []
for stmt, ids in KEY_ACCOUNTS.items():
    stmtTotal = totalByStmt.get(stmt, 0)
    for snakeId in ids:
        cnt = coverage[stmt].get(snakeId, 0)
        rate = cnt / stmtTotal * 100 if stmtTotal > 0 else 0
        if rate < 95:
            weakAccounts.append((stmt, snakeId, cnt, stmtTotal, rate))

weakAccounts.sort(key=lambda x: x[4])
if weakAccounts:
    print(f"  {'제표':<5} {'snakeId':<45} {'보유율':<10} {'누락종목'}")
    print(f"  {'-'*75}")
    for stmt, sid, cnt, total, rate in weakAccounts:
        missing = total - cnt
        print(f"  {stmt:<5} {sid:<45} {rate:>6.1f}%   {missing:>5,}개 누락")
else:
    print("  모든 핵심 계정이 95% 이상 보유 — 약점 없음")

print()
print("=" * 80)
print("5. 종합 평가")
print("=" * 80)

allKeyTotal = len(ALL_KEY_IDS)
okCount = sum(1 for stmt, ids in KEY_ACCOUNTS.items()
              for sid in ids
              if coverage[stmt].get(sid, 0) / max(totalByStmt.get(stmt, 0), 1) * 100 >= 95)
print(f"  핵심 계정 {allKeyTotal}개 중 95%+ 보유율: {okCount}개 ({okCount/allKeyTotal*100:.1f}%)")
print(f"  약점 계정 수: {len(weakAccounts)}개")
