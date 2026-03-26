"""실험 ID: 098-009
실험명: Peer consensus 매출 예측

목적:
- TF-IDF peer 그룹의 매출 성장률 중앙값을 "앵커"로 사용했을 때
  단순 자기회귀(naive) 대비 예측력이 개선되는지 확인
- Phase A에서 검증된 peer 품질(상관 0.27)이 실제 예측에 전이되는지

가설:
1. Peer consensus(peer 매출 중앙값)가 naive(전년 성장률 유지)보다 MAE 2%p+ 개선
2. Peer consensus가 sector median(KIND 업종 중앙값)보다 우수
3. 매출 상관이 높은 peer일수록 consensus 예측력이 좋음

방법:
1. 2024년 매출 예측 (2023년까지 데이터로 예측, 2024 실제와 비교)
2. 예측 방법 4가지 비교:
   a) Naive: 2023년 성장률 그대로 반복
   b) 3년 평균: 최근 3년 성장률 평균
   c) Peer consensus: 상위 5 peer의 2023년 성장률 중앙값
   d) Peer-weighted: peer 유사도 가중 성장률
3. 멀티토픽 TF-IDF(004 방법) peer 사용
4. 매출 데이터 보유 종목만 대상

결과:
- 평가 대상: 131개 종목 (매출+텍스트 보유, ±200% 이상치 제외)
- MdAE (중앙값 절대오차) 기준:
  peerConsensus: 9.0% (최저) → naive 13.7%, avg3y 11.8%, sectorMedian 12.3%
- 10% 이내 적중: peerConsensus 53.4% > naive 44.3% > avg3y 42.7% > sectorMedian 41.2%
- 20% 이내 적중: peerConsensus 84.7% > peerWeighted 77.1% > sectorMedian 71.8% > avg3y 67.2%
- MAE는 이상치 1개가 naive/sectorMedian을 2000%대로 왜곡 → MdAE가 더 신뢰 지표
- peerConsensus vs peerWeighted: 중앙값(13.5%)이 가중(14.8%)보다 소폭 우수
- 대표 종목: 삼성전자(실제+16.2%, peer+5.2%), 기아(+7.7%, peer+14.1%),
  LG화학(-11.5%, peer+0.9%), KT(+0.2%, peer+2.0%)
- peer 유사도 구간별 차이: 높은sim MAE=13.8% vs 낮은sim MAE=13.2% → 유의차 없음

결론:
- 가설1 채택: peerConsensus MdAE=9.0%로 naive(13.7%) 대비 4.7%p 개선
  20% 이내 적중률 84.7% vs 64.9% → 19.8%p 개선
- 가설2 채택: peerConsensus(9.0%) > sectorMedian(12.3%) → 3.3%p 우수
- 가설3 기각: 높은/낮은 유사도 peer 간 성능 차이 미미 (-0.6%p)
  → peer 존재 자체가 중요하지, 유사도 수준은 덜 중요
- **핵심 발견**: TF-IDF peer consensus는 2024 매출 예측에서 가장 강력한 앵커
  1. 중앙값 기반이 가중 기반보다 안정적 (이상치 방어)
  2. 84.7%가 20% 이내 오차 → 실용적 정확도
  3. KIND 업종 대비 우위 → 텍스트 기반 peer가 정형 분류보다 유용
  4. naive/avg3y의 이상치 취약성(MAE 2000%+) vs peer의 안정성(13.5%)
- 한계: 매출 데이터 커버리지 132/2400+ (5.5%) — account_nm 매칭 확대 필요

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
    "bizOverview": {
        "titles": ["II. 사업의 내용", "1. 사업의 개요", "2. 주요 제품 및 서비스"],
        "fallback": "사업",
        "weight": 0.50,
    },
    "segments": {
        "titles": ["5. 사업부문별 정보", "4. 매출 및 수주상황"],
        "fallback": "부문|매출|수주",
        "weight": 0.25,
    },
    "contracts": {
        "titles": ["3. 원재료 및 생산설비"],
        "fallback": "원재료|생산|설비|연구개발",
        "weight": 0.15,
    },
    "risk": {
        "titles": [],
        "fallback": "위험|리스크|파생",
        "weight": 0.10,
    },
}

TARGET_YEAR = "2024"  # 예측 대상
TRAIN_YEARS = ["2018", "2019", "2020", "2021", "2022", "2023"]


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
    print("  098-009: Peer consensus 매출 예측")
    print("=" * 70)

    from dartlab.gather.listing import getKindList
    kindDf = getKindList()
    kindMap = {}
    industryMap = {}
    for row in kindDf.iter_rows(named=True):
        code, name, industry = row["종목코드"], row["회사명"], row["업종"]
        if not _isExcluded(name, industry):
            kindMap[code] = name
            industryMap[code] = industry

    # 매출 데이터 수집
    print("\n  매출 데이터 수집 중...")
    revenueMap = {}  # code -> {year -> revenue}
    growthMap = {}   # code -> {year -> growth%}
    for code in kindMap:
        rev = _extractAnnualRevenue(code)
        if rev and TARGET_YEAR in rev:
            revenueMap[code] = rev
            g = _computeGrowthRates(rev)
            if TARGET_YEAR in g and "2023" in g:
                growthMap[code] = g

    print(f"  2024 매출 + 2023/2024 성장률 보유: {len(growthMap)}개")

    if len(growthMap) < 30:
        print("  ❌ 데이터 부족 — 실험 중단")
        return

    validCodes = sorted(growthMap.keys())

    # TF-IDF peer 구축 (멀티토픽)
    print("\n  멀티토픽 TF-IDF peer 구축 중...")
    allTopicTexts = {}
    for pf in sorted(DOCS_DIR.glob("*.parquet")):
        code = pf.stem
        if code not in kindMap:
            continue
        texts = _extractTopicTexts(pf)
        if "bizOverview" in texts:
            allTopicTexts[code] = texts

    # peer 대상: 텍스트 + 매출 모두 있는 종목
    peerCodes = sorted(set(validCodes) & set(allTopicTexts.keys()))
    print(f"  peer 대상 (텍스트+매출): {len(peerCodes)}개")

    if len(peerCodes) < 30:
        print("  ❌ peer 대상 부족 — 실험 중단")
        return

    # TF-IDF 벡터화
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

    # 예측 비교
    print("\n" + "─" * 70)
    print("  2024년 매출 성장률 예측 비교")
    print("─" * 70)

    methods = ["naive", "avg3y", "peerConsensus", "peerWeighted", "sectorMedian"]
    errors = {m: [] for m in methods}
    predResults = []

    for code in peerCodes:
        g = growthMap[code]
        actual2024 = g[TARGET_YEAR]

        # 이상치 필터 (±200% 초과 제외)
        if abs(actual2024) > 200:
            continue

        # Naive: 2023 성장률 반복
        naive = g.get("2023", 0)

        # 3년 평균
        recent = [g.get(y, 0) for y in ["2021", "2022", "2023"] if y in g]
        avg3y = np.mean(recent) if recent else 0

        # Peer consensus: 상위 5 peer의 2023 성장률 중앙값
        i = codeIdx[code]
        topIdx = np.argsort(simMat[i])[-5:][::-1]
        peerGrowths2023 = []
        peerSims = []
        for j in topIdx:
            peerCode = peerCodes[j]
            pg = growthMap.get(peerCode, {}).get("2023")
            if pg is not None and abs(pg) < 200:
                peerGrowths2023.append(pg)
                peerSims.append(simMat[i][j])

        peerConsensus = np.median(peerGrowths2023) if peerGrowths2023 else naive

        # Peer-weighted: 유사도 가중
        if peerGrowths2023 and sum(peerSims) > 0:
            weights = np.array(peerSims[:len(peerGrowths2023)])
            weights = weights / weights.sum()
            peerWeighted = np.dot(weights, peerGrowths2023)
        else:
            peerWeighted = naive

        # Sector median: KIND 업종 내 2023 성장률 중앙값
        ind = industryMap.get(code, "기타")
        sectorGrowths = [
            growthMap.get(c, {}).get("2023", 0)
            for c in industryGroups.get(ind, [])
            if c != code and abs(growthMap.get(c, {}).get("2023", 0)) < 200
        ]
        sectorMedian = np.median(sectorGrowths) if sectorGrowths else naive

        preds = {
            "naive": naive, "avg3y": avg3y,
            "peerConsensus": peerConsensus, "peerWeighted": peerWeighted,
            "sectorMedian": sectorMedian,
        }
        for m in methods:
            errors[m].append(abs(actual2024 - preds[m]))

        predResults.append((code, actual2024, preds))

    # 결과 요약
    print(f"\n  평가 대상: {len(predResults)}개 종목 (이상치 ±200% 제외)")
    print(f"\n  {'방법':20s} {'MAE':>8s} {'MdAE':>8s} {'<10%':>8s} {'<20%':>8s}")
    print(f"  {'─' * 52}")

    for m in methods:
        arr = np.array(errors[m])
        mae = arr.mean()
        mdae = np.median(arr)
        within10 = (arr < 10).mean()
        within20 = (arr < 20).mean()
        print(f"  {m:20s} {mae:8.1f}% {mdae:8.1f}% {within10:8.1%} {within20:8.1%}")

    # 대표 종목 상세
    print(f"\n{'─' * 70}")
    print(f"  대표 종목 상세 (상위 10)")
    print(f"{'─' * 70}")
    spotlightCodes = ["005930", "000660", "005380", "035420", "051910",
                      "000270", "097950", "004170", "030200", "035720"]
    print(f"  {'종목':12s} {'실제':>8s} {'naive':>8s} {'avg3y':>8s} {'peer':>8s} {'pWgt':>8s} {'sector':>8s}")
    print(f"  {'─' * 60}")
    for code, actual, preds in predResults:
        if code in spotlightCodes:
            name = kindMap.get(code, "?")[:8]
            print(f"  {name:12s} {actual:+8.1f}% {preds['naive']:+8.1f}% "
                  f"{preds['avg3y']:+8.1f}% {preds['peerConsensus']:+8.1f}% "
                  f"{preds['peerWeighted']:+8.1f}% {preds['sectorMedian']:+8.1f}%")

    # 가설3: 상관이 높은 peer의 consensus 성능
    print(f"\n{'─' * 70}")
    print(f"  peer 유사도 구간별 consensus 성능")
    print(f"{'─' * 70}")
    highSimErrors = []
    lowSimErrors = []
    for code in peerCodes:
        if code not in codeIdx or abs(growthMap[code].get(TARGET_YEAR, 999)) > 200:
            continue
        i = codeIdx[code]
        topSim = np.sort(simMat[i])[-5:][::-1]
        avgSim = topSim.mean()
        actual = growthMap[code][TARGET_YEAR]

        topIdx = np.argsort(simMat[i])[-5:][::-1]
        pg = [growthMap.get(peerCodes[j], {}).get("2023", 0) for j in topIdx
              if abs(growthMap.get(peerCodes[j], {}).get("2023", 0)) < 200]
        if pg:
            pred = np.median(pg)
            err = abs(actual - pred)
            if avgSim > np.median([np.sort(simMat[k])[-5:][::-1].mean() for k in range(len(peerCodes))]):
                highSimErrors.append(err)
            else:
                lowSimErrors.append(err)

    if highSimErrors and lowSimErrors:
        print(f"  높은 유사도 peer: MAE={np.mean(highSimErrors):.1f}% (n={len(highSimErrors)})")
        print(f"  낮은 유사도 peer: MAE={np.mean(lowSimErrors):.1f}% (n={len(lowSimErrors)})")
        print(f"  차이: {np.mean(lowSimErrors) - np.mean(highSimErrors):+.1f}%p")

    print(f"\n  소요시간: {time.time() - t0:.1f}s")


if __name__ == "__main__":
    run()
    print("\n실험 완료.")
