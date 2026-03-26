"""
실험 ID: 005
실험명: 업종별 핵심 계정 보유율 비교 (비교가능성 섹터 차이)

목적:
- 002에서 발견된 약점 계정(inventories 92.2%, cost_of_sales 87.2% 등)이
  특정 업종에서 구조적으로 누락되는 것인지 확인
- 금융업 vs 제조업 vs 서비스업의 계정 보유 패턴 차이 식별
- 업종별로 "비교 가능한 계정 세트"를 정의하기 위한 근거 마련

가설:
1. 금융업(은행/보험/증권)은 revenue, cost_of_sales, inventories 보유율이 현저히 낮음
2. 제조업은 핵심 계정 대부분 95%+ 보유
3. 서비스업은 inventories 보유율이 낮지만 revenue는 높음
4. bonds 보유율은 대기업(금융업) 집중

방법:
1. 전체 finance parquet에서 corp_cls(Y=유가증권, K=코스닥 등) 활용
2. DART industry_code (KSIC) 컬럼이 있으면 업종 대분류
3. 없으면 종목 이름 패턴으로 금융/비금융 최소 구분
4. 업종 그룹별 핵심 계정 보유율 비교

결과 (2026-03-09 실행):

1) 분류 결과: 금융 55개, 비금융(기타) 2,509개
   (corp_cls가 parquet에 없어 유가/코스닥 구분 불가, 키워드 기반 금융 분류만 가능)

2) 금융 vs 비금융 핵심 차이 (20%p+ 차이 계정)
   | 계정 | 금융 | 비금융 | 차이 | 해석 |
   |------|------|--------|------|------|
   | current_assets | 25.5% | 99.5% | -74.0% | 금융업 BS는 유동/비유동 구분 안 함 |
   | non_current_assets | 23.6% | 99.4% | -75.8% | 동일 이유 |
   | current_liabilities | 25.5% | 99.5% | -74.0% | 동일 이유 |
   | non_current_liabilities | 25.5% | 99.4% | -74.0% | 동일 이유 |
   | gross_profit | 20.0% | 93.9% | -73.9% | 금융업은 매출총이익 개념 없음 |
   | cost_of_sales | 21.8% | 94.1% | -72.3% | 금융업은 매출원가 개념 없음 |
   | inventories | 21.8% | 93.7% | -71.9% | 금융업은 재고 없음 |
   | short_term_borrowings | 29.1% | 92.7% | -63.6% | 금융업 차입 구조 상이 |
   | long_term_borrowings | 23.6% | 85.7% | -62.1% | 동일 이유 |
   | revenue | 65.5% | 99.4% | -33.9% | 금융업은 매출 대신 이자수익/수수료수익 |

3) 비금융 기준 약점 계정 (95% 미달)
   cost_of_sales 94.1%, gross_profit 93.9%, inventories 93.7%,
   short_term_borrowings 92.7%, long_term_borrowings 85.7%, bonds 58.7%,
   total_equity 86.5%

4) 양 업종 공통 100% 계정
   operating_income, net_income, total_assets, cash_and_equivalents,
   total_liabilities, equity_including_nci, operating_cashflow,
   investing_cashflow, financing_cashflow

결론:
- 가설1 채택: 금융업은 revenue(-34%), cost_of_sales(-72%), inventories(-72%) 등 대폭 누락
- 가설2 부분채택: 비금융은 대부분 95%+지만 cost_of_sales(94.1%), inventories(93.7%) 소폭 미달
- 가설3 해당없음: 서비스업 별도 분류 불가 (corp_cls 부재)
- 가설4 기각: bonds는 금융(63.6%)과 비금융(58.7%)이 비슷 → 대기업 집중이 아닌 사채 발행 종목 분포

핵심 발견:
- 금융업 55개가 전체 평균을 깎는 주범 (2.1% 비중이지만 약점 계정 대부분 설명)
- 비금융 2,509개 기준으로 보면 대부분의 핵심 계정이 92%+ (실질 비교가능성 높음)
- 금융업은 별도의 계정 세트 필요 (이자수익, 수수료수익, 예수부채, 대출채권 등)
- 비금융 내에서도 total_equity(86.5%)가 약점 → 별도재무제표 종목에서 지배기업 귀속 자본 누락

실험일: 2026-03-09
"""

import sys
import polars as pl
from pathlib import Path
from collections import defaultdict

sys.path.insert(0, str(Path(__file__).resolve().parents[5]))
from dartlab.providers.dart.finance.mapper import AccountMapper
from dartlab.providers.dart.finance.pivot import SNAKE_ALIASES

FINANCE_DIR = Path("C:/Users/MSI/OneDrive/Desktop/sideProject/nicegui/eddmpython/data/dartData/finance")

mapper = AccountMapper.get()

KEY_IDS = [
    "revenue", "cost_of_sales", "gross_profit", "operating_income", "net_income",
    "total_assets", "current_assets", "non_current_assets",
    "cash_and_equivalents", "inventories",
    "total_liabilities", "current_liabilities", "non_current_liabilities",
    "short_term_borrowings", "long_term_borrowings", "bonds",
    "total_equity", "equity_including_nci",
    "operating_cashflow", "investing_cashflow", "financing_cashflow",
]

FINANCE_KEYWORDS = [
    "은행", "금융", "캐피탈", "증권", "보험", "투자", "저축", "신용",
    "카드", "리스", "자산운용", "파이낸스", "파이낸셜",
]

parquetFiles = sorted(f for f in FINANCE_DIR.glob("*.parquet") if not f.name.startswith("_"))
print(f"총 parquet 파일: {len(parquetFiles)}개")

sectorAccounts = defaultdict(lambda: defaultdict(int))
sectorTotal = defaultdict(int)
sectorCompanies = defaultdict(list)

for i, fp in enumerate(parquetFiles):
    df = pl.read_parquet(fp)
    if "account_id" not in df.columns or "account_nm" not in df.columns:
        continue

    corpName = ""
    corpCls = ""

    if "corp_name" in df.columns:
        names = df["corp_name"].drop_nulls()
        if len(names) > 0:
            corpName = str(names[0])

    if "corp_cls" in df.columns:
        classes = df["corp_cls"].drop_nulls()
        if len(classes) > 0:
            corpCls = str(classes[0])

    isFinance = any(kw in corpName for kw in FINANCE_KEYWORDS)

    if isFinance:
        sector = "금융"
    elif corpCls == "Y":
        sector = "유가증권(비금융)"
    elif corpCls == "K":
        sector = "코스닥"
    elif corpCls == "N":
        sector = "코넥스"
    else:
        sector = "기타"

    unique = df.select(["sj_div", "account_id", "account_nm"]).unique()
    compSnakeIds = set()

    for row in unique.iter_rows(named=True):
        accountId = row.get("account_id", "") or ""
        accountNm = row.get("account_nm", "") or ""
        if not accountNm:
            continue

        result = mapper.map(accountId, accountNm)
        if result:
            finalId = SNAKE_ALIASES.get(result, result)
            compSnakeIds.add(finalId)

    sectorTotal[sector] += 1
    sectorCompanies[sector].append(fp.stem)
    for sid in KEY_IDS:
        if sid in compSnakeIds:
            sectorAccounts[sector][sid] += 1

    if (i + 1) % 500 == 0:
        print(f"  진행: {i + 1}/{len(parquetFiles)}...")

print(f"분석 완료")
print()

print("=" * 100)
print("1. 업종 그룹별 종목 수")
print("=" * 100)
for sector in sorted(sectorTotal, key=lambda x: -sectorTotal[x]):
    print(f"  {sector:<20}: {sectorTotal[sector]:>5}개")

print()
print("=" * 100)
print("2. 업종 그룹별 핵심 계정 보유율")
print("=" * 100)

header = f"  {'계정':<35}"
sectors = sorted(sectorTotal, key=lambda x: -sectorTotal[x])
for s in sectors:
    header += f" {s[:6]:>8}"
print(header)
print(f"  {'-'*35}" + " --------" * len(sectors))

for sid in KEY_IDS:
    line = f"  {sid:<35}"
    for s in sectors:
        total = sectorTotal[s]
        cnt = sectorAccounts[s].get(sid, 0)
        rate = cnt / total * 100 if total > 0 else 0
        line += f" {rate:>7.1f}%"
    print(line)

print()
print("=" * 100)
print("3. 금융 vs 비금융 핵심 차이")
print("=" * 100)

finTotal = sectorTotal.get("금융", 0)
nonFinTotal = sum(v for k, v in sectorTotal.items() if k != "금융")

print(f"  금융: {finTotal}개, 비금융: {nonFinTotal}개")
print()
print(f"  {'계정':<35} {'금융':>8} {'비금융':>8} {'차이':>8}")
print(f"  {'-'*65}")

for sid in KEY_IDS:
    finCnt = sectorAccounts.get("금융", {}).get(sid, 0)
    finRate = finCnt / finTotal * 100 if finTotal > 0 else 0

    nonFinCnt = sum(sectorAccounts.get(s, {}).get(sid, 0) for s in sectorTotal if s != "금융")
    nonFinRate = nonFinCnt / nonFinTotal * 100 if nonFinTotal > 0 else 0

    diff = finRate - nonFinRate
    marker = " <<<" if abs(diff) > 20 else ""
    print(f"  {sid:<35} {finRate:>7.1f}% {nonFinRate:>7.1f}% {diff:>+7.1f}%{marker}")

print()
print("=" * 100)
print("4. 종합 평가")
print("=" * 100)

finWeakAccounts = []
for sid in KEY_IDS:
    finCnt = sectorAccounts.get("금융", {}).get(sid, 0)
    finRate = finCnt / finTotal * 100 if finTotal > 0 else 0
    nonFinCnt = sum(sectorAccounts.get(s, {}).get(sid, 0) for s in sectorTotal if s != "금융")
    nonFinRate = nonFinCnt / nonFinTotal * 100 if nonFinTotal > 0 else 0
    if finRate < nonFinRate - 20:
        finWeakAccounts.append((sid, finRate, nonFinRate))

if finWeakAccounts:
    print("  금융업에서 현저히 낮은 계정 (비금융 대비 -20%p 이상):")
    for sid, fr, nfr in finWeakAccounts:
        print(f"    {sid}: 금융 {fr:.1f}% vs 비금융 {nfr:.1f}%")
