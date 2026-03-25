"""실험 ID: 098-014
실험명: 최종 모델 비교 — dartlab 앙상블 vs 기준선

목적:
- 098 전체 실험의 최종 결론 도출
- dartlab이 구축할 수 있는 최적 매출 예측 앙상블의 성능을 체계적으로 정리
- 외부 벤치마크(학술/산업) 대비 위치 확인

가설:
1. dartlab 최적 앙상블(avg3y+peer+sector)이 모든 단일 기준선을 능가
2. 3개년 평균 기준에서도 최적 앙상블이 안정적 우위 유지
3. 커버리지 확대 없이도 현재 데이터로 실용적 예측 가능

방법:
1. 2022/2023/2024 3개년 backtesting
2. 비교 대상:
   a) Naive (전년 반복)
   b) 3년 이동평균 (avg3y)
   c) Peer consensus (TF-IDF peer 중앙값)
   d) Sector median (KIND 업종 중앙값)
   e) dartlab 앙상블 (avg3y + peer + sector 단순 평균)
   f) dartlab 2소스 (avg3y + peer)
3. 지표: MdAE, MAE(trimmed), 20%이내 적중률, 방향 적중률

결과:
- 3개년 평균 성능 (MdAE / <20% / 방향):
  ensemble2(avg3y+peer):    12.0% / 69.5% / 66.3% ★
  ensemble3(+sector):       12.1% / 68.5% / 63.4% ★
  avg3y:                    13.2% / 65.2% / 61.3%
  peerConsensus:            13.3% / 67.3% / 64.2%
  naive:                    14.5% / 61.3% / 63.1%
  sectorMedian:             15.6% / 61.8% / 59.4%
- 연도별 앙상블 MdAE: 2022=12.2%, 2023=14.9%, 2024=9.1%
- 방향 적중률: ensemble2 66.3%로 최고

결론:
- 가설1 채택: ensemble3(12.1%) < 모든 단일 기준선 (13.2%~15.6%)
  ensemble2(12.0%)가 사실상 최적 — sector 추가 효과 미미
- 가설2 채택: 3개년 모두 앙상블이 naive보다 우수
  (2022: 12.2 vs 13.2, 2023: 14.9 vs 16.6, 2024: 9.1 vs 13.7)
- 가설3 부분 채택: 현재 132개 커버리지로 실용적 예측 가능
  단 전체 상장사(2400+) 대비 5.5%만 커버 → 확대 필요

- **098 실험 시리즈 최종 결론**:
  1. TF-IDF peer consensus + 3년 이동평균 앙상블 = MdAE 12.0%
  2. 애널리스트(5-8%)와 ML(10-15%) 사이, 순수 통계 기반으로 competitive
  3. 핵심 병목: 매출 데이터 커버리지 (account_nm 매칭 확대 필요)
  4. GDP 거시 beta는 예측에 기여하지 못함 → 제외
  5. 텍스트 peer는 KIND 업종보다 예측력 우수 (12.0% vs 15.6%)

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
    print("  098-014: 최종 모델 비교")
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

    # 데이터
    print("\n  데이터 준비 중...")
    growthMap = {}
    for code in kindMap:
        rev = _extractAnnualRevenue(code)
        if rev:
            g = _computeGrowthRates(rev)
            if len(g) >= 3:
                growthMap[code] = g

    # TF-IDF
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

    industryGroups = {}
    for code in peerCodes:
        ind = industryMap.get(code, "기타")
        industryGroups.setdefault(ind, []).append(code)

    # 모델 정의
    models = {
        "naive": lambda code, g, prevYear, **kw: g.get(prevYear, 0),
        "avg3y": lambda code, g, prevYear, **kw: _avg3y(g, prevYear),
        "peerConsensus": lambda code, g, prevYear, **kw: _peerConsensus(code, g, prevYear, peerCodes, simMat, codeIdx, growthMap),
        "sectorMedian": lambda code, g, prevYear, **kw: _sectorMedian(code, g, prevYear, industryMap, industryGroups, growthMap),
        "ensemble3": lambda code, g, prevYear, **kw: np.mean([
            _avg3y(g, prevYear),
            _peerConsensus(code, g, prevYear, peerCodes, simMat, codeIdx, growthMap),
            _sectorMedian(code, g, prevYear, industryMap, industryGroups, growthMap),
        ]),
        "ensemble2": lambda code, g, prevYear, **kw: np.mean([
            _avg3y(g, prevYear),
            _peerConsensus(code, g, prevYear, peerCodes, simMat, codeIdx, growthMap),
        ]),
    }

    # 3개년 backtesting
    yearMetrics = {m: {"mdae": [], "w20": [], "direction": []} for m in models}

    for targetYear in TARGET_YEARS:
        prevYear = str(int(targetYear) - 1)

        for modelName in models:
            errors = []
            directionHits = []
            for code in peerCodes:
                g = growthMap[code]
                actual = g.get(targetYear)
                prev = g.get(prevYear)
                if actual is None or prev is None or abs(actual) > 200:
                    continue

                pred = models[modelName](code, g, prevYear)
                errors.append(abs(actual - pred))
                # 방향 적중: 둘 다 양수 or 둘 다 음수
                if (pred >= 0 and actual >= 0) or (pred < 0 and actual < 0):
                    directionHits.append(1)
                else:
                    directionHits.append(0)

            if errors:
                arr = np.array(errors)
                yearMetrics[modelName]["mdae"].append(np.median(arr))
                yearMetrics[modelName]["w20"].append((arr < 20).mean())
                yearMetrics[modelName]["direction"].append(np.mean(directionHits))

    # 결과 테이블
    print(f"\n{'=' * 70}")
    print(f"  3개년 평균 성능 비교 (2022/2023/2024)")
    print(f"{'=' * 70}")

    print(f"\n  {'모델':20s} {'MdAE':>8s} {'<20%':>8s} {'방향':>8s}")
    print(f"  {'─' * 44}")

    for modelName in models:
        m = yearMetrics[modelName]
        avgMdAE = np.mean(m["mdae"]) if m["mdae"] else 0
        avgW20 = np.mean(m["w20"]) if m["w20"] else 0
        avgDir = np.mean(m["direction"]) if m["direction"] else 0
        marker = " ★" if modelName in ("ensemble3", "ensemble2") else ""
        print(f"  {modelName:20s} {avgMdAE:8.1f}% {avgW20:8.1%} {avgDir:8.1%}{marker}")

    # 연도별 상세
    for targetYear in TARGET_YEARS:
        idx = TARGET_YEARS.index(targetYear)
        print(f"\n  [{targetYear}]", end="")
        for modelName in models:
            m = yearMetrics[modelName]
            if idx < len(m["mdae"]):
                print(f"  {modelName}={m['mdae'][idx]:.1f}%", end="")
        print()

    # 외부 벤치마크 대비
    print(f"\n{'=' * 70}")
    print(f"  외부 벤치마크 대비 위치")
    print(f"{'=' * 70}")
    bestMdAE = np.mean(yearMetrics["ensemble3"]["mdae"])
    bestW20 = np.mean(yearMetrics["ensemble3"]["w20"])
    print(f"""
  dartlab 최적 앙상블 (avg3y + peer + sector):
    3개년 평균 MdAE = {bestMdAE:.1f}%
    3개년 평균 <20% = {bestW20:.1%}

  참고 벤치마크 (학술/산업):
    - 애널리스트 consensus: MdAE ~5-8% (정보 우위, 질적 판단 포함)
    - LSTM/CNN-LSTM: MAE ~10-15% (충분한 시계열 필요, 100+ 분기)
    - Random Forest ensemble: MAE ~12-18% (다수 재무비율 feature)
    - Naive (전년 반복): MdAE ~15% (우리 결과와 일치)
    - Sector median: MdAE ~15-16% (우리 결과와 일치)

  위치: 애널리스트와 ML 모델 사이
    - 순수 통계 기반으로 MdAE {bestMdAE:.0f}%는 competitive
    - 애널리스트(5-8%)에는 미달이나, 질적 판단 없이 달성
    - ML(10-15%)과 동등하나, 학습 데이터가 5-7년분으로 제한적
    - 커버리지 확대(132→2000+) + 분기 데이터 추가 시 개선 여지 큼
""")

    print(f"  소요시간: {time.time() - t0:.1f}s")


def _avg3y(g: dict, prevYear: str) -> float:
    years = [str(int(prevYear) - k) for k in range(0, 3)]
    vals = [g.get(y) for y in years if g.get(y) is not None and abs(g.get(y)) < 200]
    return np.mean(vals) if vals else 0


def _peerConsensus(code, g, prevYear, peerCodes, simMat, codeIdx, growthMap):
    if code not in codeIdx:
        return g.get(prevYear, 0)
    i = codeIdx[code]
    topIdx = np.argsort(simMat[i])[-5:][::-1]
    peerGrowths = [growthMap.get(peerCodes[j], {}).get(prevYear)
                   for j in topIdx
                   if growthMap.get(peerCodes[j], {}).get(prevYear) is not None
                   and abs(growthMap.get(peerCodes[j], {}).get(prevYear)) < 200]
    return np.median(peerGrowths) if peerGrowths else g.get(prevYear, 0)


def _sectorMedian(code, g, prevYear, industryMap, industryGroups, growthMap):
    ind = industryMap.get(code, "기타")
    vals = [growthMap.get(c, {}).get(prevYear, 0)
            for c in industryGroups.get(ind, [])
            if c != code and abs(growthMap.get(c, {}).get(prevYear, 0)) < 200]
    return np.median(vals) if vals else g.get(prevYear, 0)


if __name__ == "__main__":
    run()
    print("\n실험 완료.")
