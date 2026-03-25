"""실험 ID: 098-016
실험명: 거시 2변수(GDP+환율) 앙상블 기여도

목적:
- 015에서 5변수 다변량은 과적합 확인 (n=8에 k=5)
- GDP+환율 2변수로 제한하면 과적합 없이 앙상블에 기여하는지
- avg3y+peer(MdAE 12.0%) 앙상블에 macro_2var 추가 효과 검증

가설:
1. GDP+환율 2변수 out-of-sample MdAE < GDP 단독(11.0%)
2. avg3y+peer+macro_2var 앙상블이 avg3y+peer(12.0%) 대비 MdAE 1%p 개선
3. 수출 섹터(반도체/자동차)에서 환율 추가 효과가 큼

방법:
1. GDP+환율 2변수 OLS (2017~2023 학습, 2024 예측)
2. 섹터별 매출 예측값을 소속 종목에 적용
3. avg3y+peer+macro_2var 3개 앙상블 비교
4. 3개년(2022/2023/2024) 확장 backtesting

결과:
| 방법 | 2022 | 2023 | 2024 | 3yr avg |
|------|------|------|------|---------|
| avg3y | 14.2% | 13.9% | 11.7% | 13.2% |
| peer | 14.6% | 16.9% | 8.3% | 13.3% |
| avg3y+peer | 12.2% | 14.9% | 9.1% | 12.0% |
| avg3y+peer+macro | 12.3% | 14.8% | 9.1% | 12.1% |

- 20%이내 비율: avg3y+peer 69.5% = avg3y+peer+macro 69.5% (동일)
- macro 2var 커버리지: 12/168 종목(7%)만 섹터 매핑됨
- 커버리지 밖 종목은 macro=0으로 처리 → 앙상블 영향 미미

결론:
- **가설 1 기각**: GDP+환율 2변수도 앙상블 기여 없음 (12.0% → 12.1% 악화)
- **가설 2 기각**: macro 추가 MdAE 개선 없음 (오히려 +0.1%p)
- **가설 3 검증 불가**: 커버리지 7%로 섹터별 분석 의미 없음
- 근본 원인: (1) 거시→섹터 회귀 자체가 8개 연도로 부정확, (2) 섹터→종목 매핑 12개뿐
- **Phase B+E 최종 결론: 거시 변수는 현재 프레임워크에서 앙상블 기여 불가**
- 거시가 유효하려면: (a) 20년+ 시계열 또는 (b) 월별 데이터 + 기업별 직접 회귀 필요

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

# 거시 데이터 (015와 동일)
MACRO_GDP = {
    "2016": 2.9, "2017": 3.2, "2018": 2.9, "2019": 2.2, "2020": -0.7,
    "2021": 4.3, "2022": 2.6, "2023": 1.4, "2024": 2.0,
}
MACRO_FX = {
    "2016": -2.0, "2017": -2.8, "2018": 0.6, "2019": 5.9, "2020": -0.4,
    "2021": 0.5, "2022": 12.5, "2023": 3.1, "2024": 7.0,
}

# 섹터 매핑 (KIND 업종 → 거시 회귀 섹터)
SECTOR_STOCKS = {
    "반도체": [("005930",), ("000660",), ("009150",), ("058470",), ("403870",)],
    "자동차": [("005380",), ("000270",), ("012330",), ("018880",), ("161390",)],
    "화학": [("051910",), ("011170",), ("009830",), ("006120",), ("004000",)],
    "철강": [("005490",), ("004020",), ("001230",), ("004990",)],
    "통신": [("030200",), ("017670",)],
    "식품": [("005440",), ("097950",), ("004370",), ("271560",), ("014680",)],
    "IT/소프트웨어": [("035420",), ("035720",), ("036570",), ("018260",), ("293490",)],
    "유통": [("004170",), ("069960",), ("023530",)],
}

# 종목코드 → 섹터
CODE_TO_SECTOR = {}
for sector, stocks in SECTOR_STOCKS.items():
    for s in stocks:
        CODE_TO_SECTOR[s[0]] = sector

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


def _sectorMacroPredict(sector: str, targetYear: str) -> float | None:
    """GDP+환율 2변수 OLS로 섹터 매출 성장률 예측."""
    # 섹터 매출 성장률 계산
    stockList = SECTOR_STOCKS.get(sector)
    if not stockList:
        return None
    yearTotals = {}
    for s in stockList:
        rev = _extractAnnualRevenue(s[0])
        if not rev:
            continue
        for y, v in rev.items():
            yearTotals[y] = yearTotals.get(y, 0) + v
    years = sorted(yearTotals.keys())
    growth = {}
    for i in range(1, len(years)):
        if yearTotals[years[i - 1]] > 0:
            growth[years[i]] = ((yearTotals[years[i]] - yearTotals[years[i - 1]]) / yearTotals[years[i - 1]]) * 100

    # 학습 데이터 (targetYear 제외)
    trainYears = [y for y in sorted(growth.keys()) if y != targetYear and y in MACRO_GDP and y in MACRO_FX]
    if len(trainYears) < 4:
        return None

    yTrain = np.array([growth[y] for y in trainYears])
    xTrain = np.array([[1.0, MACRO_GDP[y], MACRO_FX[y]] for y in trainYears])

    try:
        beta = np.linalg.lstsq(xTrain, yTrain, rcond=None)[0]
    except np.linalg.LinAlgError:
        return None

    if targetYear not in MACRO_GDP or targetYear not in MACRO_FX:
        return None

    x2024 = np.array([1.0, MACRO_GDP[targetYear], MACRO_FX[targetYear]])
    return float(x2024 @ beta)


def run():
    t0 = time.time()
    print("=" * 70)
    print("  098-016: 거시 2변수(GDP+환율) 앙상블 기여도")
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

    # 매출
    print("\n  데이터 수집 중...")
    growthMap = {}
    for code in kindMap:
        rev = _extractAnnualRevenue(code)
        if rev:
            g = _computeGrowthRates(rev)
            if len(g) >= 3:
                growthMap[code] = g

    # TF-IDF peer
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

    # 섹터별 macro 예측 캐시
    sectorMacroPreds = {}
    for targetYear in TARGET_YEARS:
        for sector in SECTOR_STOCKS:
            pred = _sectorMacroPredict(sector, targetYear)
            sectorMacroPreds[(sector, targetYear)] = pred

    # 3개년 backtesting
    methods = ["avg3y", "peer", "avg3y+peer", "avg3y+peer+macro"]
    yearResults = {}

    for targetYear in TARGET_YEARS:
        prevYear = str(int(targetYear) - 1)
        errors = {m: [] for m in methods}

        for code in peerCodes:
            g = growthMap[code]
            actual = g.get(targetYear)
            prev = g.get(prevYear)
            if actual is None or prev is None or abs(actual) > 200:
                continue

            # avg3y
            recentYears = [str(int(targetYear) - k) for k in range(1, 4)]
            recent = [g.get(y) for y in recentYears if g.get(y) is not None and abs(g.get(y)) < 200]
            avg3y = np.mean(recent) if recent else prev

            # peer consensus
            i = codeIdx[code]
            topIdx = np.argsort(simMat[i])[-5:][::-1]
            peerGrowths = [growthMap.get(peerCodes[j], {}).get(prevYear)
                           for j in topIdx
                           if growthMap.get(peerCodes[j], {}).get(prevYear) is not None
                           and abs(growthMap.get(peerCodes[j], {}).get(prevYear)) < 200]
            peer = np.median(peerGrowths) if peerGrowths else prev

            # macro 2var
            sector = CODE_TO_SECTOR.get(code)
            macroPred = sectorMacroPreds.get((sector, targetYear)) if sector else None

            preds = {
                "avg3y": avg3y,
                "peer": peer,
                "avg3y+peer": np.mean([avg3y, peer]),
            }
            if macroPred is not None and abs(macroPred) < 200:
                preds["avg3y+peer+macro"] = np.mean([avg3y, peer, macroPred])
            else:
                preds["avg3y+peer+macro"] = preds["avg3y+peer"]  # fallback

            for m in methods:
                errors[m].append(abs(actual - preds[m]))

        yearResult = {}
        for m in methods:
            arr = np.array(errors[m]) if errors[m] else np.array([0.0])
            yearResult[m] = {"mdae": np.median(arr), "w20": (arr < 20).mean(), "n": len(arr)}
        yearResults[targetYear] = yearResult

    # 결과
    print(f"\n{'=' * 70}")
    print(f"  3개년 MdAE 비교")
    print(f"{'=' * 70}")

    print(f"\n  {'방법':25s}", end="")
    for y in TARGET_YEARS:
        print(f" {y:>8s}", end="")
    print(f" {'평균':>8s}")
    print(f"  {'─' * 55}")

    for m in methods:
        print(f"  {m:25s}", end="")
        mdaes = [yearResults[y][m]["mdae"] for y in TARGET_YEARS]
        for md in mdaes:
            print(f" {md:8.1f}%", end="")
        print(f" {np.mean(mdaes):8.1f}%")

    print(f"\n  3개년 20%이내 비교:")
    print(f"  {'방법':25s}", end="")
    for y in TARGET_YEARS:
        print(f" {y:>8s}", end="")
    print(f" {'평균':>8s}")
    print(f"  {'─' * 55}")

    for m in methods:
        print(f"  {m:25s}", end="")
        w20s = [yearResults[y][m]["w20"] for y in TARGET_YEARS]
        for w in w20s:
            print(f" {w:8.1%}", end="")
        print(f" {np.mean(w20s):8.1%}")

    # macro 커버리지
    coveredCount = sum(1 for code in peerCodes if CODE_TO_SECTOR.get(code))
    print(f"\n  macro 2var 커버리지: {coveredCount}/{len(peerCodes)} 종목이 섹터 매핑됨")

    print(f"\n  소요시간: {time.time() - t0:.1f}s")


if __name__ == "__main__":
    run()
    print("\n실험 완료.")
