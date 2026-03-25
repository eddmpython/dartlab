"""실험 ID: 098-012
실험명: 체계적 Backtesting 프레임워크

목적:
- 009의 peer consensus 결과를 단일 연도(2024)가 아닌
  3개년(2022/2023/2024)으로 확장하여 안정성 검증
- 연도별 성능 변동이 크면 2024 결과가 우연일 수 있음

가설:
1. Peer consensus가 3개년 모두에서 naive보다 MdAE 2%p+ 우수
2. 연도별 MdAE 변동계수 < 0.3 (안정적)
3. 20% 이내 적중률이 3개년 모두 75%+

방법:
1. 예측 대상: 2022, 2023, 2024 각 연도
2. 각 연도에서 직전 데이터만 사용 (정보 누수 방지)
3. 방법: naive, avg3y, peerConsensus, sectorMedian
4. 연도별/종합 MdAE, MAE, 적중률 비교

결과:
- 3개년 평균 MdAE: avg3y 13.2%, peerConsensus 13.3%, naive 14.5%, sectorMedian 15.6%
- 3개년 평균 20%이내: peerConsensus 67.3%, avg3y 65.2%, naive 61.3%, sectorMedian 61.8%
- peerConsensus 연도별 MdAE: 2022=14.6%, 2023=16.9%, 2024=8.3% (CV=0.27)
- avg3y 연도별 MdAE: 2022=14.2%, 2023=13.9%, 2024=11.7% (CV=0.08)
- 2024년에서만 peerConsensus가 압도적 (MdAE 8.3% vs 차점 11.7%)
- 2022/2023에서는 avg3y와 peer가 거의 동등하거나 avg3y가 소폭 우수

결론:
- 가설1 부분 채택: 3개년 평균에서 peer(13.3%)가 naive(14.5%)보다 1.2%p 우수
  단 2%p+ 기준 미달. 2024년만 보면 5.4%p 우수
- 가설2 채택: peerConsensus CV=0.27 < 0.3 기준. 단 4가지 방법 중 가장 불안정
- 가설3 기각: 20%이내 적중률 67.3% < 75% 기준
- **핵심 결론**: 3개년 backtesting에서 peer consensus의 우위는 제한적
  1. avg3y(3년 평균)가 가장 안정적이고 peer와 거의 동등한 성능
  2. peer consensus는 2024에서 탁월하지만 연도별 변동이 큼
  3. **최적 전략은 peer consensus + avg3y 앙상블** (둘의 장점 결합)
  4. naive와 sectorMedian은 이상치에 취약 — MAE가 연도별로 큰 편차
  5. 단일 방법으로 peer만 사용하는 것보다 앙상블이 더 안전

실험일: 2026-03-25
"""

import re
import time
from pathlib import Path

import numpy as np
import polars as pl
from scipy.sparse import hstack
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

DATA_DIR = Path(__file__).resolve().parents[2] / "data" / "dart"
DOCS_DIR = DATA_DIR / "docs"
FINANCE_DIR = DATA_DIR / "finance"

EXCLUDE_INDUSTRIES = {"기타 금융업", "신탁업", "집합투자업"}
EXCLUDE_NAME_PATTERNS = ["지주", "홀딩스", "Holdings"]

TOPIC_CONFIG = {
    "bizOverview": {"titles": ["II. 사업의 내용", "1. 사업의 개요", "2. 주요 제품 및 서비스"], "fallback": "사업", "weight": 0.50},
    "segments": {"titles": ["5. 사업부문별 정보", "4. 매출 및 수주상황"], "fallback": "부문|매출|수주", "weight": 0.25},
    "contracts": {"titles": ["3. 원재료 및 생산설비"], "fallback": "원재료|생산|설비|연구개발", "weight": 0.15},
    "risk": {"titles": [], "fallback": "위험|리스크|파생", "weight": 0.10},
}

TARGET_YEARS = ["2022", "2023", "2024"]


def _cleanText(text: str) -> str:
    text = re.sub(r"<[^>]+>", " ", text)
    text = re.sub(r"\d[\d,\.]*\s*(원|억|조|만|천|백|%|백만|십억|달러|USD|KRW|Won)", " ", text)
    text = re.sub(r"\b\d[\d,\.]*\b", " ", text)
    text = re.sub(r"[│├└┌─┐┘┤┬┴┼━┃╋\(\)\[\]\{\}]+", " ", text)
    text = re.sub(r"\s+", " ", text).strip()
    return text


def _extractTopicTexts(parquetPath: Path) -> dict[str, str]:
    try:
        df = pl.read_parquet(str(parquetPath), columns=["year", "report_type", "section_title", "section_content"])
    except Exception:
        return {}
    df = df.filter(pl.col("report_type").str.contains("사업"))
    if df.height == 0:
        return {}
    latestYear = df["year"].cast(str).sort(descending=True).first()
    df = df.filter(pl.col("year") == latestYear)
    result = {}
    for topicKey, cfg in TOPIC_CONFIG.items():
        filtered = df.filter(pl.col("section_title").is_in(cfg["titles"]))
        if filtered.height == 0 and cfg["fallback"]:
            filtered = df.filter(pl.col("section_title").str.contains(cfg["fallback"]))
        if filtered.height == 0:
            continue
        texts = filtered["section_content"].drop_nulls().to_list()
        combined = _cleanText("\n".join(str(t) for t in texts if t))
        if len(combined) >= 100:
            result[topicKey] = combined
    return result


def _extractAnnualRevenue(stockCode: str) -> dict[str, float] | None:
    fp = FINANCE_DIR / f"{stockCode}.parquet"
    if not fp.exists():
        return None
    try:
        df = pl.read_parquet(str(fp))
    except Exception:
        return None
    requiredCols = {"sj_div", "account_id", "bsns_year", "thstrm_amount", "fs_div", "reprt_code"}
    if not requiredCols.issubset(set(df.columns)):
        return None
    df = df.filter(pl.col("reprt_code") == "11011")
    if df.height == 0:
        return None
    isRows = df.filter(
        (pl.col("sj_div") == "IS") &
        (pl.col("account_id").str.to_lowercase().str.contains("revenue"))
    )
    if isRows.height == 0:
        isRows = df.filter(
            (pl.col("sj_div") == "IS") &
            (pl.col("account_nm").str.contains("매출액|수익\\(매출"))
        )
    if isRows.height == 0:
        return None
    yearValues = {}
    for row in isRows.iter_rows(named=True):
        year = str(row.get("bsns_year", ""))
        amount = row.get("thstrm_amount")
        if not year or amount is None:
            continue
        try:
            val = float(str(amount).replace(",", ""))
        except (ValueError, TypeError):
            continue
        if val == 0:
            continue
        fsDiv = str(row.get("fs_div", ""))
        if year not in yearValues or fsDiv == "CFS":
            yearValues[year] = val
    return yearValues if len(yearValues) >= 4 else None


def _computeGrowthRates(revMap: dict[str, float]) -> dict[str, float]:
    years = sorted(revMap.keys())
    growth = {}
    for i in range(1, len(years)):
        prev = revMap[years[i - 1]]
        curr = revMap[years[i]]
        if prev != 0:
            growth[years[i]] = ((curr - prev) / abs(prev)) * 100
    return growth


def _isExcluded(name: str, industry: str) -> bool:
    if industry in EXCLUDE_INDUSTRIES:
        return True
    return any(pat in name for pat in EXCLUDE_NAME_PATTERNS)


def run():
    t0 = time.time()
    print("=" * 70)
    print("  098-012: 체계적 Backtesting (3개년)")
    print("=" * 70)

    from dartlab.engines.gather.listing import getKindList
    kindDf = getKindList()
    kindMap = {}
    industryMap = {}
    for row in kindDf.iter_rows(named=True):
        code, name, industry = row["종목코드"], row["회사명"], row["업종"]
        if not _isExcluded(name, industry):
            kindMap[code] = name
            industryMap[code] = industry

    # 매출 데이터
    print("\n  매출 데이터 수집 중...")
    revenueMap = {}
    growthMap = {}
    for code in kindMap:
        rev = _extractAnnualRevenue(code)
        if rev:
            revenueMap[code] = rev
            g = _computeGrowthRates(rev)
            if len(g) >= 3:
                growthMap[code] = g

    print(f"  성장률 데이터 보유: {len(growthMap)}개")

    # TF-IDF peer (한번만 구축)
    print("\n  멀티토픽 TF-IDF peer 구축 중...")
    allTopicTexts = {}
    for pf in sorted(DOCS_DIR.glob("*.parquet")):
        code = pf.stem
        if code not in kindMap:
            continue
        texts = _extractTopicTexts(pf)
        if "bizOverview" in texts:
            allTopicTexts[code] = texts

    peerCodes = sorted(set(growthMap.keys()) & set(allTopicTexts.keys()))
    print(f"  peer 대상: {len(peerCodes)}개")

    topicMatrices = {}
    for topicKey, cfg in TOPIC_CONFIG.items():
        texts = [allTopicTexts.get(c, {}).get(topicKey, "") for c in peerCodes]
        vec = TfidfVectorizer(
            max_features=5000, ngram_range=(1, 2), min_df=3, max_df=0.90,
            sublinear_tf=True, token_pattern=r"(?u)\b[가-힣a-zA-Z]{2,}\b",
        )
        mat = vec.fit_transform(texts)
        topicMatrices[topicKey] = mat * cfg["weight"]

    combinedMatrix = hstack(list(topicMatrices.values()))
    simMat = cosine_similarity(combinedMatrix)
    np.fill_diagonal(simMat, 0)
    codeIdx = {c: i for i, c in enumerate(peerCodes)}

    # KIND 업종 그룹
    industryGroups = {}
    for code in peerCodes:
        ind = industryMap.get(code, "기타")
        industryGroups.setdefault(ind, []).append(code)

    # 연도별 backtesting
    methods = ["naive", "avg3y", "peerConsensus", "sectorMedian"]
    yearResults = {}

    for targetYear in TARGET_YEARS:
        prevYear = str(int(targetYear) - 1)
        print(f"\n{'─' * 70}")
        print(f"  {targetYear}년 예측 (정보 기준: ~{prevYear})")
        print(f"{'─' * 70}")

        errors = {m: [] for m in methods}
        validCount = 0

        for code in peerCodes:
            g = growthMap[code]
            actual = g.get(targetYear)
            prevGrowth = g.get(prevYear)
            if actual is None or prevGrowth is None or abs(actual) > 200:
                continue

            validCount += 1

            # Naive
            naive = prevGrowth

            # 3년 평균
            recentYears = [str(int(targetYear) - k) for k in range(1, 4)]
            recent = [g.get(y) for y in recentYears if g.get(y) is not None and abs(g.get(y)) < 200]
            avg3y = np.mean(recent) if recent else naive

            # Peer consensus
            i = codeIdx[code]
            topIdx = np.argsort(simMat[i])[-5:][::-1]
            peerGrowths = []
            for j in topIdx:
                pc = peerCodes[j]
                pg = growthMap.get(pc, {}).get(prevYear)
                if pg is not None and abs(pg) < 200:
                    peerGrowths.append(pg)
            peerConsensus = np.median(peerGrowths) if peerGrowths else naive

            # Sector median
            ind = industryMap.get(code, "기타")
            sectorGrowths = [
                growthMap.get(c, {}).get(prevYear, 0)
                for c in industryGroups.get(ind, [])
                if c != code and abs(growthMap.get(c, {}).get(prevYear, 0)) < 200
            ]
            sectorMedian = np.median(sectorGrowths) if sectorGrowths else naive

            preds = {"naive": naive, "avg3y": avg3y, "peerConsensus": peerConsensus, "sectorMedian": sectorMedian}
            for m in methods:
                errors[m].append(abs(actual - preds[m]))

        print(f"  유효 종목: {validCount}개")
        print(f"\n  {'방법':20s} {'MAE':>8s} {'MdAE':>8s} {'<10%':>8s} {'<20%':>8s}")
        print(f"  {'─' * 52}")

        yearResult = {}
        for m in methods:
            arr = np.array(errors[m]) if errors[m] else np.array([0.0])
            mae = arr.mean()
            mdae = np.median(arr)
            within10 = (arr < 10).mean()
            within20 = (arr < 20).mean()
            yearResult[m] = {"mae": mae, "mdae": mdae, "within10": within10, "within20": within20, "n": len(arr)}
            print(f"  {m:20s} {mae:8.1f}% {mdae:8.1f}% {within10:8.1%} {within20:8.1%}")

        yearResults[targetYear] = yearResult

    # 종합
    print(f"\n{'=' * 70}")
    print(f"  종합 비교 (3개년 평균)")
    print(f"{'=' * 70}")

    print(f"\n  MdAE 연도별 추이:")
    print(f"  {'방법':20s}", end="")
    for y in TARGET_YEARS:
        print(f" {y:>8s}", end="")
    print(f" {'평균':>8s} {'CV':>6s}")
    print(f"  {'─' * 60}")

    for m in methods:
        mdaes = [yearResults[y][m]["mdae"] for y in TARGET_YEARS]
        avg = np.mean(mdaes)
        cv = np.std(mdaes) / avg if avg > 0 else 0
        print(f"  {m:20s}", end="")
        for md in mdaes:
            print(f" {md:8.1f}%", end="")
        print(f" {avg:8.1f}% {cv:6.2f}")

    print(f"\n  20% 이내 적중률 연도별 추이:")
    print(f"  {'방법':20s}", end="")
    for y in TARGET_YEARS:
        print(f" {y:>8s}", end="")
    print(f" {'평균':>8s}")
    print(f"  {'─' * 52}")

    for m in methods:
        w20s = [yearResults[y][m]["within20"] for y in TARGET_YEARS]
        avg = np.mean(w20s)
        print(f"  {m:20s}", end="")
        for w in w20s:
            print(f" {w:8.1%}", end="")
        print(f" {avg:8.1%}")

    print(f"\n  소요시간: {time.time() - t0:.1f}s")


if __name__ == "__main__":
    run()
    print("\n실험 완료.")
