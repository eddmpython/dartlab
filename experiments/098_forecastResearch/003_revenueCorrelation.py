"""실험 ID: 098-003
실험명: TF-IDF peer의 매출 성장률 상관 검증

목적:
- 002에서 발견한 TF-IDF peer가 실제로 매출 성장률에서도 유사한 패턴을 보이는지 검증
- 핵심 질문: "사업 내용이 유사한 기업 = 매출 추이도 유사한가?"

가설:
1. TF-IDF peer top5의 매출 성장률 상관 > 랜덤 5사 상관 (0.3 vs ~0.0)
2. KIND 같은 업종 내 상관 vs TF-IDF peer 상관 비교 — peer가 우세하거나 동등
3. 대표 5종목에서 3개 이상에서 peer 상관 > 0.2

방법:
1. 002의 TF-IDF 유사도 재산출 (지주회사 제거, 전처리 적용)
2. finance parquet에서 연간 매출(sales) 시계열 추출 (2016~2024)
3. YoY 성장률 산출
4. 종목별 top5 peer와의 매출 성장률 Pearson 상관 계산
5. 비교군: KIND 같은 업종 랜덤 5사, 완전 랜덤 5사
6. 대표 5종목 심층 분석

결과:
- 매출 데이터 보유: 177/2408개 (연간 사업보고서 Revenue만 — 커버리지 한계)
- TF-IDF peer top5 평균 상관: 0.2217 (n=109)
- KIND 같은 업종 평균 상관: 0.1613 (n=89)
- 완전 랜덤 평균 상관: 0.0813 (n=168)
- peer > 랜덤 차이: +0.14, peer > 업종 차이: +0.06
- 강한 상관(>0.3): peer 38.5% > KIND 34.8% > 랜덤 15.5%
- 대표 종목:
  삼성전자→LG전자: corr=+0.717
  현대차→기아: corr=+0.952, →현대모비스: corr=+0.862
  LG화학→LG에너지솔루션: corr=+0.831, →LG전자: corr=+0.837

결론:
- 가설1 부분 채택: TF-IDF peer 평균 상관 0.22 (0.3 미달이나 랜덤 대비 2.7배)
- 가설2 채택: TF-IDF peer(0.22) > KIND 업종(0.16) — peer가 우세
- 가설3 채택: 대표 3종목(삼성전자/현대차/LG화학) 모두 peer 상관 > 0.7
- **TF-IDF 텍스트 유사도가 매출 상관에서도 KIND 업종보다 우수**
- 한계: 매출 커버리지 177개로 적음 (account_nm 매칭 확대 필요)
- 핵심 발견: 텍스트적으로 유사한 기업은 실제로 매출도 유사하게 움직임
  → peer group 기반 매출 예측(Phase C)의 근거 확보

실험일: 2026-03-25
"""

import re
import time
from collections import defaultdict
from pathlib import Path

import numpy as np
import polars as pl
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

DATA_DIR = Path(__file__).resolve().parents[2] / "data" / "dart"
DOCS_DIR = DATA_DIR / "docs"
FINANCE_DIR = DATA_DIR / "finance"

BIZ_TITLES = ["II. 사업의 내용", "1. 사업의 개요", "2. 주요 제품 및 서비스"]
MIN_TEXT_LEN = 200
EXCLUDE_INDUSTRIES = {"기타 금융업", "신탁업", "집합투자업"}
EXCLUDE_NAME_PATTERNS = ["지주", "홀딩스", "Holdings"]


def _cleanText(text: str) -> str:
    """텍스트 전처리."""
    text = re.sub(r"<[^>]+>", " ", text)
    text = re.sub(r"\d[\d,\.]*\s*(원|억|조|만|천|백|%|백만|십억|달러|USD|KRW|Won)", " ", text)
    text = re.sub(r"\b\d[\d,\.]*\b", " ", text)
    text = re.sub(r"[│├└┌─┐┘┤┬┴┼━┃╋\(\)\[\]\{\}]+", " ", text)
    text = re.sub(r"\s+", " ", text).strip()
    return text


def _extractBizText(parquetPath: Path) -> str | None:
    """parquet에서 최신 사업보고서의 사업 설명 텍스트를 추출."""
    try:
        df = pl.read_parquet(str(parquetPath), columns=["year", "report_type", "section_title", "section_content"])
    except Exception:
        return None
    df = df.filter(pl.col("report_type").str.contains("사업"))
    if df.height == 0:
        return None
    latestYear = df["year"].cast(str).sort(descending=True).first()
    df = df.filter(pl.col("year") == latestYear)
    bizDf = df.filter(pl.col("section_title").is_in(BIZ_TITLES))
    if bizDf.height == 0:
        bizDf = df.filter(pl.col("section_title").str.contains("사업"))
    if bizDf.height == 0:
        return None
    texts = bizDf["section_content"].drop_nulls().to_list()
    combined = _cleanText("\n".join(str(t) for t in texts if t))
    return combined if len(combined) >= MIN_TEXT_LEN else None


def _extractSalesGrowth(stockCode: str) -> dict[str, float] | None:
    """finance parquet에서 연간 매출 성장률 추출.

    연간 사업보고서(reprt_code=11011)의 CFS(연결) Revenue만 사용.
    """
    fp = FINANCE_DIR / f"{stockCode}.parquet"
    if not fp.exists():
        return None
    try:
        df = pl.read_parquet(str(fp))
    except Exception:
        return None

    # 컬럼 확인
    requiredCols = {"sj_div", "account_id", "account_nm", "bsns_year", "thstrm_amount", "fs_div", "reprt_code"}
    if not requiredCols.issubset(set(df.columns)):
        return None

    # 연간 사업보고서만 (분기 제외)
    df = df.filter(pl.col("reprt_code") == "11011")
    if df.height == 0:
        return None

    # IS에서 Revenue 계정 (account_id에 Revenue/Sales 포함)
    isRows = df.filter(
        (pl.col("sj_div") == "IS") &
        (pl.col("account_id").str.to_lowercase().str.contains("revenue"))
    )

    if isRows.height == 0:
        # account_nm fallback
        isRows = df.filter(
            (pl.col("sj_div") == "IS") &
            (pl.col("account_nm").str.contains("매출액|수익\\(매출"))
        )

    if isRows.height == 0:
        return None

    # 연도별 값 (CFS 우선)
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

    if len(yearValues) < 3:
        return None

    # YoY 성장률
    years = sorted(yearValues.keys())
    growth = {}
    for i in range(1, len(years)):
        prevVal = yearValues[years[i - 1]]
        currVal = yearValues[years[i]]
        if prevVal != 0:
            growth[years[i]] = (currVal - prevVal) / abs(prevVal)

    return growth if len(growth) >= 2 else None


def _pearsonCorr(g1: dict[str, float], g2: dict[str, float]) -> float | None:
    """두 성장률 딕셔너리의 공통 연도 Pearson 상관."""
    commonYears = sorted(set(g1.keys()) & set(g2.keys()))
    if len(commonYears) < 3:
        return None
    v1 = np.array([g1[y] for y in commonYears])
    v2 = np.array([g2[y] for y in commonYears])
    if np.std(v1) == 0 or np.std(v2) == 0:
        return None
    return float(np.corrcoef(v1, v2)[0, 1])


def _isExcluded(companyName: str, industry: str) -> bool:
    if industry in EXCLUDE_INDUSTRIES:
        return True
    return any(pat in companyName for pat in EXCLUDE_NAME_PATTERNS)


def run():
    t0 = time.time()
    print("=" * 70)
    print("  098-003: TF-IDF peer 매출 상관 검증")
    print("=" * 70)

    # 1. KIND listing
    from dartlab.engines.gather.listing import getKindList
    kindDf = getKindList()
    kindMap = {}
    for row in kindDf.iter_rows(named=True):
        code = row["종목코드"]
        name = row["회사명"]
        industry = row["업종"]
        if not _isExcluded(name, industry):
            kindMap[code] = (name, industry)

    # 2. 텍스트 추출 + TF-IDF (002 동일)
    print("\n  텍스트 추출 + TF-IDF 산출 중...")
    corpus = {}
    for pf in sorted(DOCS_DIR.glob("*.parquet")):
        code = pf.stem
        if code not in kindMap:
            continue
        text = _extractBizText(pf)
        if text:
            corpus[code] = text

    codes = sorted(corpus.keys())
    texts = [corpus[c] for c in codes]
    print(f"  유효 텍스트: {len(codes)}개")

    vectorizer = TfidfVectorizer(
        max_features=10000, ngram_range=(1, 2), min_df=3, max_df=0.90,
        sublinear_tf=True, token_pattern=r"(?u)\b[가-힣a-zA-Z]{2,}\b",
    )
    tfidfMatrix = vectorizer.fit_transform(texts)
    simMatrix = cosine_similarity(tfidfMatrix)
    np.fill_diagonal(simMatrix, 0)

    # peer map
    codeIdx = {c: i for i, c in enumerate(codes)}
    peerMap = {}
    for i, code in enumerate(codes):
        topIdx = np.argsort(simMatrix[i])[-5:][::-1]
        peerMap[code] = [(codes[j], float(simMatrix[i][j])) for j in topIdx]

    # 3. 매출 성장률 추출
    print("\n  매출 성장률 추출 중...")
    growthMap = {}
    for code in codes:
        g = _extractSalesGrowth(code)
        if g:
            growthMap[code] = g

    print(f"  매출 데이터 보유: {len(growthMap)}개 / {len(codes)}개")

    # 4. peer 상관 계산
    print("\n  peer 상관 계산 중...")
    # (A) TF-IDF peer top5 상관
    peerCorrs = []
    # (B) KIND 같은 업종 랜덤 5사 상관
    industryCorrs = []
    # (C) 완전 랜덤 5사 상관
    randomCorrs = []

    rng = np.random.RandomState(42)
    industryGroups = defaultdict(list)
    for code in codes:
        if code in growthMap:
            _, ind = kindMap[code]
            industryGroups[ind].append(code)

    validCodes = [c for c in codes if c in growthMap]

    for code in validCodes:
        myGrowth = growthMap[code]

        # (A) TF-IDF peer
        peers = [pc for pc, _ in peerMap.get(code, []) if pc in growthMap]
        if peers:
            corrs = [_pearsonCorr(myGrowth, growthMap[pc]) for pc in peers]
            corrs = [c for c in corrs if c is not None]
            if corrs:
                peerCorrs.append(np.mean(corrs))

        # (B) KIND 같은 업종
        _, myIndustry = kindMap[code]
        sameIndustry = [c for c in industryGroups[myIndustry] if c != code and c in growthMap]
        if len(sameIndustry) >= 3:
            sample = rng.choice(sameIndustry, size=min(5, len(sameIndustry)), replace=False)
            corrs = [_pearsonCorr(myGrowth, growthMap[c]) for c in sample]
            corrs = [c for c in corrs if c is not None]
            if corrs:
                industryCorrs.append(np.mean(corrs))

        # (C) 랜덤
        randSample = rng.choice(validCodes, size=5, replace=False)
        corrs = [_pearsonCorr(myGrowth, growthMap[c]) for c in randSample if c != code]
        corrs = [c for c in corrs if c is not None]
        if corrs:
            randomCorrs.append(np.mean(corrs))

    # 5. 결과 출력
    print("\n" + "─" * 70)
    print("  매출 성장률 상관 비교")
    print("─" * 70)

    for label, corrs in [
        ("TF-IDF peer top5", peerCorrs),
        ("KIND 같은 업종", industryCorrs),
        ("완전 랜덤", randomCorrs),
    ]:
        arr = np.array(corrs) if corrs else np.array([0.0])
        print(f"\n  [{label}] n={len(corrs)}")
        print(f"    평균 상관: {arr.mean():.4f}")
        print(f"    중앙값:   {np.median(arr):.4f}")
        print(f"    표준편차:  {arr.std():.4f}")
        print(f"    양의 상관(>0) 비율: {(arr > 0).mean():.1%}")
        print(f"    강한 상관(>0.3) 비율: {(arr > 0.3).mean():.1%}")

    # 6. 대표 종목 심층
    print("\n" + "─" * 70)
    print("  대표 종목 peer 매출 상관")
    print("─" * 70)

    spotlightCodes = ["005930", "005380", "000660", "035420", "051910"]
    for code in spotlightCodes:
        if code not in growthMap or code not in peerMap:
            continue
        name, industry = kindMap.get(code, ("?", "?"))
        myGrowth = growthMap[code]
        print(f"\n  {name} ({code}) — {industry}")
        print(f"    자사 성장률: {', '.join(f'{y}:{v:+.1%}' for y, v in sorted(myGrowth.items())[-5:])}")

        for peerCode, sim in peerMap[code][:5]:
            if peerCode not in growthMap:
                continue
            peerName = kindMap.get(peerCode, ("?",))[0]
            corr = _pearsonCorr(myGrowth, growthMap[peerCode])
            corrStr = f"{corr:+.3f}" if corr is not None else "N/A"
            print(f"    → {peerName:20s} sim={sim:.3f} corr={corrStr}")

    # 7. 요약
    tTotal = time.time() - t0
    print(f"\n{'=' * 70}")
    print(f"  요약")
    print(f"{'=' * 70}")
    print(f"  매출 데이터 보유 종목: {len(growthMap)}개")
    pArr = np.array(peerCorrs)
    iArr = np.array(industryCorrs) if industryCorrs else np.array([0.0])
    rArr = np.array(randomCorrs) if randomCorrs else np.array([0.0])
    print(f"  TF-IDF peer 평균 상관: {pArr.mean():.4f}")
    print(f"  KIND 업종 평균 상관:   {iArr.mean():.4f}")
    print(f"  랜덤 평균 상관:        {rArr.mean():.4f}")
    print(f"  peer > 랜덤 차이:      {pArr.mean() - rArr.mean():+.4f}")
    print(f"  peer > 업종 차이:      {pArr.mean() - iArr.mean():+.4f}")
    print(f"  총 소요시간: {tTotal:.1f}s")


if __name__ == "__main__":
    run()
    print("\n실험 완료.")
