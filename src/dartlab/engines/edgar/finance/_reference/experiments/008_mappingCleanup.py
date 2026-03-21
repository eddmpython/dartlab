"""
실험 ID: 008
실험명: learnedSynonyms 오매핑 제거 + 미매핑 태그 학습

목적:
- 007에서 발견된 합산계정 오매핑(detail → aggregate) 제거
- S&P 100 미매핑 태그 중 빈도 높은 것 학습하여 커버리지 향상
- 매핑 정확도를 올려 derived formula의 실효성 확보

가설:
1. learnedSynonyms에 합산계정(level=1)으로 잘못 매핑된 detail 태그가 상당수 존재
2. 이를 제거하면 007 R1(total_liabilities) 정확도가 유의미하게 개선
3. S&P 100에서 빈도 높은 미매핑 태그를 학습하면 커버리지가 10%+ 상승

방법:
1. Phase 1: 합산계정 오매핑 스캔
   - standardAccounts.json에서 level=1 snakeId 목록 추출
   - learnedSynonyms.json에서 해당 snakeId로 매핑된 태그 전수 스캔
   - commonTags에 이미 있는 태그는 제외 (정당한 매핑)
   - 나머지 = 오매핑 후보 → 리스트 출력
2. Phase 2: 오매핑 제거 실행
3. Phase 3: S&P 100 미매핑 태그 빈도 스캔
4. Phase 4: 빈도 높은 미매핑 태그 학습

결과 (2026-03-10):

Phase 1-2: 합산계정 오매핑 제거
  - level=1 합산계정(24종)에 매핑된 비commonTag = 929개 발견
  - 주요: operating_cash_flow(251), revenue(222), total_other_comprehensive_income(200),
    total_liabilities(46), other_comprehensive_income(39), current_liabilities(39)
  - 전량 제거: 11,660 → 10,731 매핑

Phase 3: 매핑률 변화
  - 제거 직후: 87.2% (기업별 고유 태그 기준, dei 제외)

Phase 4: 미매핑 태그 학습 (008b)
  - 68개 태그 추가, 1개 업데이트 (10,731 → 10,799)
  - 2개 블로킹 (income_before_tax level=1 보호)
  - 학습 후: 92.1% (+4.9%p)

007 재실행 결과 (008 전 → 후):
  D1 (total_liab = assets - equity): 57.8% → 57.3% (변화없음, BS 전기비교값 문제)
  D2 (total_liab = cur + noncur): 34.0% → 98.8% ★ (+64.8%p)
  D3 (gross_profit): 80.7% → 84.5% (+3.8%p)
  D4 (noncur_assets): 29.0% → 40.8% (+11.8%p)
  D5 (noncur_liab): 45.7% → 98.8% ★ (+53.1%p)

  커버리지:
  - 보고 종목수: D1 84→70, D2 18→5, D4 90→81 (거짓양성 제거)
  - D5: 보고 30→17, 파생가능 77→53 (오매핑 제거로 실제 보고 감소)

결론:
- 가설1 채택: 929개 오매핑 존재 확인, 전량 제거
- 가설2 부분 채택: D1은 개선 안됨(전기비교값 문제), D2/D5는 98.8%로 극적 개선
- 가설3 채택: 매핑률 87.2% → 92.1% (+4.9%p)
- 핵심 교훈: level=1 합산계정에는 commonTags만 매핑, learnedSynonyms는 level=2/3만
- 남은 과제: D1/D4의 BS 전기비교값 혼입 문제 (매핑과 무관, pivot.py _selectBS 개선 필요)

실험일: 2026-03-10
"""

from __future__ import annotations

import json
import sys
from collections import Counter, defaultdict
from pathlib import Path

import polars as pl

_PROJECT_ROOT = Path(__file__).resolve().parents[7]
_MAPPER_DATA = Path(__file__).resolve().parents[2] / "mapperData"
_EDGAR_FINANCE = _PROJECT_ROOT / "data" / "edgar" / "finance"
_TICKERS_PATH = _PROJECT_ROOT / "data" / "edgar" / "tickers.parquet"

SP100_TICKERS = [
    "AAPL", "ABBV", "ABT", "ACN", "ADBE", "AIG", "AMD", "AMGN", "AMT", "AMZN",
    "AXP", "BA", "BAC", "BK", "BKNG", "BLK", "BMY", "BRK-B", "C", "CAT",
    "CHTR", "CL", "CMCSA", "COF", "COP", "COST", "CRM", "CSCO", "CVS", "CVX",
    "DE", "DHR", "DIS", "DOW", "DUK", "EMR", "EXC", "F", "FDX", "GD",
    "GE", "GILD", "GM", "GOOG", "GOOGL", "GS", "HD", "HON", "IBM", "INTC",
    "INTU", "JNJ", "JPM", "KHC", "KO", "LIN", "LLY", "LMT", "LOW", "MA",
    "MCD", "MDLZ", "MDT", "MET", "META", "MMM", "MO", "MRK", "MS", "MSFT",
    "NEE", "NFLX", "NKE", "NOW", "NVDA", "ORCL", "PEP", "PFE", "PG", "PM",
    "PYPL", "QCOM", "RTX", "SBUX", "SCHW", "SO", "SPG", "T", "TGT", "TMO",
    "TMUS", "TSLA", "TXN", "UNH", "UNP", "UPS", "USB", "V", "VZ", "WFC",
    "WMT", "XOM",
]


def loadStandardAccounts():
    path = _MAPPER_DATA / "standardAccounts.json"
    with open(path, encoding="utf-8") as f:
        data = json.load(f)
    return data["accounts"]


def loadLearnedSynonyms():
    path = _MAPPER_DATA / "learnedSynonyms.json"
    with open(path, encoding="utf-8") as f:
        data = json.load(f)
    return data


def saveLearnedSynonyms(data):
    path = _MAPPER_DATA / "learnedSynonyms.json"
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    print(f"  saved: {path}")


def getTickerCikMap():
    if not _TICKERS_PATH.exists():
        print(f"  tickers.parquet not found: {_TICKERS_PATH}")
        return {}
    df = pl.read_parquet(_TICKERS_PATH)
    result = {}
    for row in df.iter_rows(named=True):
        ticker = row.get("ticker", "")
        cik = row.get("cik", "")
        if ticker and cik:
            result[ticker] = str(cik)
    return result


def loadParquet(cik: str):
    path = _EDGAR_FINANCE / f"{cik}.parquet"
    if not path.exists():
        return None
    return pl.read_parquet(path)


def phase1_scanMismappings():
    """합산계정(level=1) snakeId에 매핑된 detail 태그를 스캔"""
    print("=" * 70)
    print("Phase 1: 합산계정 오매핑 스캔")
    print("=" * 70)

    accounts = loadStandardAccounts()
    learned = loadLearnedSynonyms()
    tagMappings = learned["tagMappings"]

    aggregateSnakeIds = set()
    commonTagsSet = set()
    for acct in accounts:
        if acct["level"] == 1:
            aggregateSnakeIds.add(acct["snakeId"])
        for tag in acct.get("commonTags", []):
            commonTagsSet.add(tag.lower())

    print(f"\n  aggregate snakeIds (level=1): {len(aggregateSnakeIds)}")
    print(f"  {sorted(aggregateSnakeIds)}")
    print(f"  commonTags count: {len(commonTagsSet)}")

    mismapped = defaultdict(list)
    for tag, sid in tagMappings.items():
        if sid in aggregateSnakeIds:
            if tag not in commonTagsSet:
                mismapped[sid].append(tag)

    totalMismapped = sum(len(v) for v in mismapped.values())
    print(f"\n  총 오매핑 후보: {totalMismapped}개")
    print()

    for sid in sorted(mismapped.keys()):
        tags = sorted(mismapped[sid])
        print(f"  [{sid}] ({len(tags)}개)")
        for t in tags[:15]:
            print(f"    - {t}")
        if len(tags) > 15:
            print(f"    ... +{len(tags) - 15}개 더")
        print()

    return mismapped


def phase2_removeMismappings(mismapped: dict[str, list[str]]):
    """확인된 오매핑을 learnedSynonyms.json에서 삭제"""
    print("=" * 70)
    print("Phase 2: 오매핑 제거")
    print("=" * 70)

    learned = loadLearnedSynonyms()
    tagMappings = learned["tagMappings"]
    before = len(tagMappings)

    removedCount = 0
    for sid, tags in mismapped.items():
        for tag in tags:
            if tag in tagMappings:
                del tagMappings[tag]
                removedCount += 1

    after = len(tagMappings)
    print(f"\n  before: {before}")
    print(f"  removed: {removedCount}")
    print(f"  after: {after}")

    learned["tagMappings"] = tagMappings
    learned["_metadata"]["totalMappings"] = after
    saveLearnedSynonyms(learned)


def phase3_scanUnmappedTags():
    """S&P 100 파켓에서 미매핑 태그 빈도 스캔"""
    print("=" * 70)
    print("Phase 3: S&P 100 미매핑 태그 빈도 스캔")
    print("=" * 70)

    edgarFinancePath = str(Path(__file__).resolve().parents[2].parent.parent)
    if edgarFinancePath not in sys.path:
        sys.path.insert(0, edgarFinancePath)
    from edgar.finance.mapper import EdgarMapper

    EdgarMapper._tagMap = None

    tickerCik = getTickerCikMap()
    unmappedCounter = Counter()
    unmappedExamples = defaultdict(set)
    totalUniquePerCompany = 0
    mappedUniquePerCompany = 0
    companyCount = 0

    for ticker in SP100_TICKERS:
        cik = tickerCik.get(ticker)
        if not cik:
            continue
        df = loadParquet(cik)
        if df is None:
            continue

        companyCount += 1
        tags = df.filter(pl.col("namespace") != "dei")["tag"].unique().to_list()

        for tag in tags:
            totalUniquePerCompany += 1
            sid = EdgarMapper.map(tag)
            if sid is None:
                unmappedCounter[tag] += 1
                unmappedExamples[tag].add(ticker)
            else:
                mappedUniquePerCompany += 1

    mappingRate = mappedUniquePerCompany / totalUniquePerCompany * 100 if totalUniquePerCompany > 0 else 0
    print(f"\n  기업 수: {companyCount}")
    print(f"  총 태그 (기업별 고유, dei 제외): {totalUniquePerCompany}")
    print(f"  매핑됨: {mappedUniquePerCompany} ({mappingRate:.1f}%)")
    print(f"  미매핑: {totalUniquePerCompany - mappedUniquePerCompany}")
    print(f"  고유 미매핑 태그 종류: {len(unmappedCounter)}")

    print(f"\n  상위 80개 미매핑 태그 (빈도순):")
    for tag, count in unmappedCounter.most_common(80):
        tickers = sorted(unmappedExamples[tag])[:5]
        tickerStr = ", ".join(tickers)
        print(f"    {count:3d}사 | {tag} [{tickerStr}]")

    return unmappedCounter, unmappedExamples


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument("--phase", type=int, default=0,
                        help="0=all, 1=scan, 2=remove, 3=unmapped")
    args = parser.parse_args()

    if args.phase == 0 or args.phase == 1:
        mismapped = phase1_scanMismappings()

    if args.phase == 0 or args.phase == 2:
        if args.phase == 2:
            mismapped = phase1_scanMismappings()
        if mismapped:
            total = sum(len(v) for v in mismapped.values())
            print(f"\n  >>> Phase 2: {total}개 오매핑 제거 진행")
            phase2_removeMismappings(mismapped)

    if args.phase == 0 or args.phase == 3:
        phase3_scanUnmappedTags()

    print("\n" + "=" * 70)
    print("완료.")
    print("=" * 70)
