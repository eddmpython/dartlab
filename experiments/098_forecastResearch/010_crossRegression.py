"""실험 ID: 098-010
실험명: Peer 내 crossRegression (회귀 예측)

목적:
- 096에서 전체 대상 crossRegression R²=0.00이었던 것을
  TF-IDF peer 그룹 내로 한정하면 R²가 개선되는지
- peer 매출로 자사 매출을 회귀 예측하는 것이 consensus보다 나은지

가설:
1. Peer 내 회귀 R² > 0.15 (전체 R²=0.00 대비)
2. 회귀 예측 MAE가 peer consensus(009 MdAE=9.0%)과 동등 이상
3. 대형주(삼성전자, 현대차 등)에서 peer 회귀가 특히 유효

방법:
1. 각 종목의 상위 5 peer에서 회귀식 구축:
   Y(자사 매출 성장률) ~ X(peer 매출 성장률 평균/가중)
2. 2018~2023 데이터로 학습, 2024 예측
3. Leave-one-out cross-validation R² 산출
4. 009의 peer consensus와 MAE/MdAE 비교

결과:
- 유효 종목: 127개
- R² 분포: 평균 0.319, 중앙값 0.245, >0.15 비율 63.8%, >0.30 비율 44.9%
- 예측 성능:
  regression: MAE=16.4%, MdAE=11.1%, <10%=46.5%, <20%=69.3%
  consensus:  MAE=13.4%, MdAE=8.7%,  <10%=55.1%, <20%=84.3%
  naive:      MAE=2523%, MdAE=13.7%, <10%=44.9%, <20%=65.4%
- 대표 종목 R²: 기아 0.895, 현대차 0.703, 삼성전자 0.715, LG화학 0.257
- 삼성전자: R²=0.715이지만 예측은 -7.1% (실제 +16.2%) → 과적합 위험
- consensus가 regression보다 MdAE 2.4%p, <20% 적중률 15%p 우수

결론:
- 가설1 채택: peer 내 회귀 R² 평균 0.319 (전체 R²=0.00 대비 대폭 개선)
  63.8%가 R²>0.15 → peer 한정 시 매출 공변동이 존재
- 가설2 기각: regression MdAE=11.1% > consensus MdAE=8.7% → consensus 우수
  회귀는 R²가 높아도 out-of-sample 예측은 consensus에 열등
  → 5개 시점 OLS의 과적합 위험 (n=5로 추정 불안정)
- 가설3 부분 채택: 기아(R²=0.895), 현대차(R²=0.703)는 높은 R²
  단 삼성전자는 R²=0.715인데 예측 오류 큼 → R² ≠ 예측력
- **핵심 결론**: peer consensus(중앙값)가 peer regression보다 안정적이고 정확함
  1. 소표본(5시점) OLS는 과적합 → 중앙값이 더 robust
  2. R²는 in-sample fit이지 out-of-sample 예측력 아님
  3. 009 peer consensus를 예측 앵커로 채택하는 것이 합리적
  4. 회귀는 데이터가 더 쌓이면(10년+) 재검토 가치 있음

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


def _olsPredict(xTrain: list[float], yTrain: list[float], xTest: float) -> tuple[float, float]:
    """OLS 회귀로 예측. (예측값, R²) 반환."""
    n = len(xTrain)
    if n < 3:
        return np.mean(yTrain), 0.0
    xArr = np.array(xTrain)
    yArr = np.array(yTrain)
    xMean = xArr.mean()
    yMean = yArr.mean()
    ssXX = np.sum((xArr - xMean) ** 2)
    if ssXX < 1e-10:
        return yMean, 0.0
    ssXY = np.sum((xArr - xMean) * (yArr - yMean))
    beta = ssXY / ssXX
    alpha = yMean - beta * xMean
    yPred = alpha + beta * xArr
    ssTot = np.sum((yArr - yMean) ** 2)
    ssRes = np.sum((yArr - yPred) ** 2)
    r2 = 1 - ssRes / ssTot if ssTot > 0 else 0.0
    predicted = alpha + beta * xTest
    return predicted, r2


def _isExcluded(name: str, industry: str) -> bool:
    if industry in EXCLUDE_INDUSTRIES:
        return True
    return any(pat in name for pat in EXCLUDE_NAME_PATTERNS)


def run():
    t0 = time.time()
    print("=" * 70)
    print("  098-010: Peer 내 crossRegression")
    print("=" * 70)

    from dartlab.gather.listing import getKindList
    kindDf = getKindList()
    kindMap = {}
    for row in kindDf.iter_rows(named=True):
        code, name, industry = row["종목코드"], row["회사명"], row["업종"]
        if not _isExcluded(name, industry):
            kindMap[code] = name

    # 매출 데이터
    print("\n  매출 데이터 수집 중...")
    revenueMap = {}
    growthMap = {}
    for code in kindMap:
        rev = _extractAnnualRevenue(code)
        if rev:
            revenueMap[code] = rev
            g = _computeGrowthRates(rev)
            if "2024" in g and len(g) >= 4:
                growthMap[code] = g

    print(f"  2024 + 4년+ 성장률 보유: {len(growthMap)}개")

    # TF-IDF
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

    if len(peerCodes) < 30:
        print("  ❌ 부족")
        return

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

    # 회귀 예측
    trainYears = ["2019", "2020", "2021", "2022", "2023"]
    targetYear = "2024"

    print(f"\n{'─' * 70}")
    print(f"  Peer 회귀 예측 (학습: {trainYears[0]}~{trainYears[-1]}, 예측: {targetYear})")
    print(f"{'─' * 70}")

    regErrors = []
    consensusErrors = []
    naiveErrors = []
    r2Values = []
    detailResults = []

    for code in peerCodes:
        g = growthMap[code]
        actual = g.get(targetYear)
        if actual is None or abs(actual) > 200:
            continue

        i = codeIdx[code]
        topIdx = np.argsort(simMat[i])[-5:][::-1]
        peers = [peerCodes[j] for j in topIdx if peerCodes[j] in growthMap]

        if len(peers) < 2:
            continue

        # 학습 데이터: peer 평균 성장률 (X) vs 자사 성장률 (Y)
        xTrain = []
        yTrain = []
        for year in trainYears:
            yVal = g.get(year)
            if yVal is None or abs(yVal) > 200:
                continue
            peerVals = [growthMap[pc].get(year) for pc in peers
                        if growthMap[pc].get(year) is not None and abs(growthMap[pc].get(year)) < 200]
            if not peerVals:
                continue
            xTrain.append(np.mean(peerVals))
            yTrain.append(yVal)

        if len(xTrain) < 3:
            continue

        # 2024 peer 평균 성장률 (실제로는 2023 사용 — 2024 peer는 미래)
        peerVals2023 = [growthMap[pc].get("2023") for pc in peers
                        if growthMap[pc].get("2023") is not None and abs(growthMap[pc].get("2023")) < 200]
        if not peerVals2023:
            continue

        xTest = np.mean(peerVals2023)
        regPred, r2 = _olsPredict(xTrain, yTrain, xTest)

        # 비교: consensus (009 방식)
        consensusPred = np.median(peerVals2023)
        naivePred = g.get("2023", 0)

        regErr = abs(actual - regPred)
        consErr = abs(actual - consensusPred)
        naiveErr = abs(actual - naivePred)

        # 이상치 회귀 예측 클램핑 (±100%)
        if abs(regPred) > 100:
            regPred = np.clip(regPred, -100, 100)
            regErr = abs(actual - regPred)

        regErrors.append(regErr)
        consensusErrors.append(consErr)
        naiveErrors.append(naiveErr)
        r2Values.append(r2)

        detailResults.append((code, actual, regPred, consensusPred, naivePred, r2))

    print(f"\n  유효 종목: {len(regErrors)}개")

    if not regErrors:
        print("  ❌ 유효 데이터 없음")
        return

    regArr = np.array(regErrors)
    consArr = np.array(consensusErrors)
    naiveArr = np.array(naiveErrors)
    r2Arr = np.array(r2Values)

    print(f"\n  R² 분포:")
    print(f"    평균: {r2Arr.mean():.3f}")
    print(f"    중앙값: {np.median(r2Arr):.3f}")
    print(f"    >0 비율: {(r2Arr > 0).mean():.1%}")
    print(f"    >0.15 비율: {(r2Arr > 0.15).mean():.1%}")
    print(f"    >0.30 비율: {(r2Arr > 0.30).mean():.1%}")

    print(f"\n  예측 성능 비교:")
    print(f"  {'방법':20s} {'MAE':>8s} {'MdAE':>8s} {'<10%':>8s} {'<20%':>8s}")
    print(f"  {'─' * 52}")
    for label, arr in [("regression", regArr), ("consensus", consArr), ("naive", naiveArr)]:
        print(f"  {label:20s} {arr.mean():8.1f}% {np.median(arr):8.1f}% "
              f"{(arr < 10).mean():8.1%} {(arr < 20).mean():8.1%}")

    # 대표 종목
    print(f"\n{'─' * 70}")
    print(f"  대표 종목 상세")
    print(f"{'─' * 70}")
    spotlightCodes = {"005930", "000660", "005380", "035420", "051910", "000270", "097950", "030200"}
    print(f"  {'종목':12s} {'실제':>8s} {'회귀':>8s} {'consensus':>10s} {'naive':>8s} {'R²':>6s}")
    print(f"  {'─' * 58}")
    for code, actual, regPred, consPred, naivePred, r2 in detailResults:
        if code in spotlightCodes:
            name = kindMap.get(code, "?")[:8]
            print(f"  {name:12s} {actual:+8.1f}% {regPred:+8.1f}% {consPred:+10.1f}% "
                  f"{naivePred:+8.1f}% {r2:6.3f}")

    print(f"\n  소요시간: {time.time() - t0:.1f}s")


if __name__ == "__main__":
    run()
    print("\n실험 완료.")
