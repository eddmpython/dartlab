"""실험 ID: 098-013
실험명: Ablation study — 예측 소스 누적 기여도

목적:
- 다양한 예측 소스(naive, avg3y, peer, sector, macro)를
  하나씩 추가할 때 앙상블 성능이 어떻게 변하는지 측정
- 각 소스의 한계 기여(marginal contribution) 확인

가설:
1. 앙상블(avg3y + peer)이 단독보다 MdAE 1%p+ 개선
2. macro(GDP beta) 추가 시 거의 개선 없음 (Phase B 결론 반영)
3. 소스 3개 이상에서 수확 체감 (diminishing returns)

방법:
1. 기본 소스들의 예측값 산출 (2024 대상)
2. 누적 앙상블: 단순 평균으로 결합
   S1: naive only
   S2: + avg3y
   S3: + peerConsensus
   S4: + sectorMedian
   S5: + macro(GDP beta 예측)
3. 각 단계별 MdAE, 20% 적중률 측정
4. Leave-one-out: 각 소스 제거 시 성능 변화

결과:
- 누적 앙상블 MdAE: S1(naive)13.7% → S2(+avg3y)10.8% → S3(+peer)9.1% → S4(+sector)9.0% → S5(+macro)9.6%
- peer 추가 시 MdAE -1.7%p (가장 큰 단일 기여), 20%이내 +5.4%p
- macro 추가 시 MdAE +0.6%p (악화!)
- Leave-one-out: peer 제거 시 +1.2%p 악화 (가장 중요), avg3y 제거 +0.7%p
  naive 제거 시 -0.7%p 개선, macro 제거 시 -0.6%p 개선
- 최적 2개 조합: avg3y+peer = MdAE 8.9%, <20% 79.4%
- 최적 3개 조합: avg3y+peer+sector = MdAE 8.2%, <20% 80.2%
- peer+sector = MdAE 9.4%, <20% 80.9% (적중률 최고)

결론:
- 가설1 채택: avg3y+peer 앙상블(8.9%) > avg3y 단독(11.7%) = 2.8%p 개선
  avg3y+peer+sector(8.2%)는 3.5%p 개선
- 가설2 채택: macro 추가 시 MdAE 악화 (+0.6%p), 제거해도 개선
  → GDP beta 예측은 앙상블에 기여하지 못함 (Phase B 결론 재확인)
- 가설3 채택: S3(+peer)에서 대부분 성능 달성, S4(+sector)는 미미한 추가 개선
  → 3개 이상에서 수확 체감
- **최종 권장 앙상블**: avg3y + peer consensus + sector median (3개)
  MdAE=8.2%, 20%이내=80.2%
  단 peer만으로 79.4% 도달 → 2개(avg3y+peer)도 실용적
- naive와 macro는 앙상블에서 제외하는 것이 최적
  (naive: 이상치 취약, macro: GDP 단일변수 한계)

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

# GDP beta (007 하드코딩)
GDP_GROWTH_2023 = 1.4  # %
SECTOR_GDP_BETA = {
    "반도체": 1.8, "자동차": 1.3, "화학": 1.2, "철강": 1.4,
    "통신": 0.4, "식품": 0.3, "IT/소프트웨어": 1.0, "유통": 0.8,
}

# KIND 업종 → 섹터 매핑 (간이)
INDUSTRY_TO_SECTOR = {
    "반도체 제조업": "반도체", "전자부품 제조업": "반도체",
    "자동차 제조업": "자동차", "자동차 부품 제조업": "자동차",
    "기초 화학물질 제조업": "화학", "합성고무 및 플라스틱 물질 제조업": "화학",
    "1차 철강 제조업": "철강", "철강 제조업": "철강",
    "유선 통신업": "통신", "무선 통신업": "통신",
    "식료품 제조업": "식품", "음료 제조업": "식품",
    "소프트웨어 개발 및 공급업": "IT/소프트웨어", "컴퓨터 프로그래밍": "IT/소프트웨어",
    "종합 소매업": "유통", "대형마트": "유통",
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


def _isExcluded(name: str, industry: str) -> bool:
    if industry in EXCLUDE_INDUSTRIES:
        return True
    return any(pat in name for pat in EXCLUDE_NAME_PATTERNS)


def run():
    t0 = time.time()
    print("=" * 70)
    print("  098-013: Ablation study — 예측 소스 기여도")
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
            if "2024" in g and "2023" in g:
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
    print(f"  유효 종목: {len(peerCodes)}개")

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

    # 각 종목별 5가지 소스 예측값 산출
    predictions = {}  # code -> {"naive": x, "avg3y": x, "peer": x, "sector": x, "macro": x}
    actuals = {}

    for code in peerCodes:
        g = growthMap[code]
        actual = g.get("2024")
        if actual is None or abs(actual) > 200:
            continue

        naive = g.get("2023", 0)
        recent = [g.get(y) for y in ["2021", "2022", "2023"] if g.get(y) is not None and abs(g.get(y)) < 200]
        avg3y = np.mean(recent) if recent else naive

        i = codeIdx[code]
        topIdx = np.argsort(simMat[i])[-5:][::-1]
        peerGrowths = [growthMap.get(peerCodes[j], {}).get("2023")
                       for j in topIdx
                       if growthMap.get(peerCodes[j], {}).get("2023") is not None
                       and abs(growthMap.get(peerCodes[j], {}).get("2023")) < 200]
        peer = np.median(peerGrowths) if peerGrowths else naive

        ind = industryMap.get(code, "기타")
        sectorGrowths = [growthMap.get(c, {}).get("2023", 0)
                         for c in industryGroups.get(ind, [])
                         if c != code and abs(growthMap.get(c, {}).get("2023", 0)) < 200]
        sector = np.median(sectorGrowths) if sectorGrowths else naive

        # Macro: GDP beta 기반
        sectorKey = INDUSTRY_TO_SECTOR.get(ind)
        gdpBeta = SECTOR_GDP_BETA.get(sectorKey, 0.8)
        gdpChange = 2.0 - 1.4  # 2024(예측 2.0%) - 2023(1.4%) = +0.6%p
        macro = naive + gdpBeta * gdpChange

        predictions[code] = {"naive": naive, "avg3y": avg3y, "peer": peer, "sector": sector, "macro": macro}
        actuals[code] = actual

    validCodes = sorted(predictions.keys())
    print(f"  예측 대상: {len(validCodes)}개")

    # 누적 앙상블
    print(f"\n{'─' * 70}")
    print(f"  누적 앙상블 (단순 평균)")
    print(f"{'─' * 70}")

    sourceOrder = ["naive", "avg3y", "peer", "sector", "macro"]
    sourceLabels = ["S1: naive", "S2: +avg3y", "S3: +peer", "S4: +sector", "S5: +macro"]

    print(f"\n  {'단계':20s} {'MAE':>8s} {'MdAE':>8s} {'<10%':>8s} {'<20%':>8s}")
    print(f"  {'─' * 52}")

    for step in range(1, len(sourceOrder) + 1):
        sources = sourceOrder[:step]
        errors = []
        for code in validCodes:
            preds = [predictions[code][s] for s in sources]
            ensemble = np.mean(preds)
            errors.append(abs(actuals[code] - ensemble))
        arr = np.array(errors)
        print(f"  {sourceLabels[step - 1]:20s} {arr.mean():8.1f}% {np.median(arr):8.1f}% "
              f"{(arr < 10).mean():8.1%} {(arr < 20).mean():8.1%}")

    # Leave-one-out
    print(f"\n{'─' * 70}")
    print(f"  Leave-one-out (하나 제거 시 성능)")
    print(f"{'─' * 70}")

    allSources = set(sourceOrder)
    print(f"\n  {'제거 소스':20s} {'MAE':>8s} {'MdAE':>8s} {'<20%':>8s} {'MdAE변화':>10s}")
    print(f"  {'─' * 54}")

    # 전체 앙상블 기준
    fullErrors = []
    for code in validCodes:
        preds = [predictions[code][s] for s in sourceOrder]
        fullErrors.append(abs(actuals[code] - np.mean(preds)))
    fullMdAE = np.median(fullErrors)

    print(f"  {'(전체)':20s} {np.mean(fullErrors):8.1f}% {fullMdAE:8.1f}% "
          f"{(np.array(fullErrors) < 20).mean():8.1%}       —")

    for removeSource in sourceOrder:
        remaining = [s for s in sourceOrder if s != removeSource]
        errors = []
        for code in validCodes:
            preds = [predictions[code][s] for s in remaining]
            ensemble = np.mean(preds)
            errors.append(abs(actuals[code] - ensemble))
        arr = np.array(errors)
        mdae = np.median(arr)
        delta = mdae - fullMdAE
        print(f"  -{removeSource:19s} {arr.mean():8.1f}% {mdae:8.1f}% "
              f"{(arr < 20).mean():8.1%} {delta:+10.1f}%p")

    # 최적 조합 탐색 (2~3개)
    print(f"\n{'─' * 70}")
    print(f"  최적 2~3개 소스 조합")
    print(f"{'─' * 70}")

    from itertools import combinations
    bestCombos = []
    for size in [2, 3]:
        for combo in combinations(sourceOrder, size):
            errors = []
            for code in validCodes:
                preds = [predictions[code][s] for s in combo]
                ensemble = np.mean(preds)
                errors.append(abs(actuals[code] - ensemble))
            arr = np.array(errors)
            bestCombos.append((combo, np.median(arr), (arr < 20).mean()))

    bestCombos.sort(key=lambda x: x[1])
    print(f"\n  {'조합':35s} {'MdAE':>8s} {'<20%':>8s}")
    print(f"  {'─' * 53}")
    for combo, mdae, w20 in bestCombos[:10]:
        label = "+".join(combo)
        print(f"  {label:35s} {mdae:8.1f}% {w20:8.1%}")

    print(f"\n  소요시간: {time.time() - t0:.1f}s")


if __name__ == "__main__":
    run()
    print("\n실험 완료.")
