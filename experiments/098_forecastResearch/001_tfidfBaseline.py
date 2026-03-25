"""실험 ID: 098-001
실험명: TF-IDF 기반 사업보고서 텍스트 유사도 peer 발견

목적:
- DART 사업보고서의 "사업의 내용" 텍스트를 TF-IDF 벡터화하여
  기업간 cosine similarity를 산출하고, 기존 KIND 업종분류와 비교
- Hoberg-Phillips(2016) 방법론의 한국 DART 버전 기초 실험

가설:
1. TF-IDF cosine similarity로 산출한 상위 10 peer가
   KIND 업종 같은 기업과 높은 일치율 보임 (ARI > 0.3)
2. 같은 업종 내 평균 유사도 > 다른 업종 간 평균 유사도 (비율 > 2.0)
3. 200개 이상 종목에서 유효한 텍스트 추출 가능

방법:
1. docs parquet에서 "사업의 내용" 또는 "사업의 개요" 텍스트 직접 추출
   (Company 객체 생성 없이 parquet 직접 읽기 — 메모리 안전)
2. KIND listing에서 업종 정보 조인
3. scikit-learn TfidfVectorizer (unigram+bigram, 띄어쓰기 기반)
4. cosine_similarity 매트릭스 산출
5. 종목별 상위 10 peer 추출
6. KIND 업종과의 ARI(Adjusted Rand Index) 비교
7. 업종 내/외 유사도 비율 산출

결과:
- 유효 종목: 2546/2663개 (95.6%) — 가설3 채택
- TF-IDF features: 10000개, matrix: 2546×10000
- ARI (k-means 50 클러스터 vs KIND 162 업종): 0.1373 — 가설1 기각 (0.3 미달)
- 업종 내 평균 유사도: 0.2369 (81,709쌍)
- 업종 외 평균 유사도: 0.1856 (3,158,076쌍)
- 업종 내/외 비율: 1.28x — 가설2 기각 (2.0 미달)
- peer 업종 일치율: 평균 23.3%, 중앙값 10.0%, 0%인 종목 35.0%
- 대표 종목: NAVER→카카오(✅), LG화학→LG에너지솔루션(sim=0.689)는 올바른 매칭
- 문제점: SK, LG, HD현대 등 **지주회사가 모든 종목 상위 peer에 편재**
  → 다각화된 사업보고서가 모든 업종과 높은 유사도를 보이는 노이즈

결론:
- 가설1 기각: ARI=0.14로 TF-IDF 클러스터와 KIND 업종은 약한 일치
- 가설2 기각: 내/외 비율 1.28x — 업종 내 유사도가 약간만 높음
- 가설3 채택: 2546개 종목에서 유효 텍스트 추출 (95.6%)
- **지주회사 노이즈가 핵심 문제**: "기타 금융업"으로 분류된 지주회사들이
  광범위한 사업 서술로 인해 모든 기업과 높은 유사도 → peer 품질 저하
- 다음 실험에서 지주회사 제거 + 업종 대분류 비교 + 텍스트 전처리 개선 필요
- 긍정 신호: NAVER-카카오, LG화학-LG에너지솔루션 등 의미적으로 올바른 매칭 존재

실험일: 2026-03-25
"""

import time
from pathlib import Path

import polars as pl
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from sklearn.metrics import adjusted_rand_score
import numpy as np

# ── 설정 ──
DATA_DIR = Path(__file__).resolve().parents[2] / "data" / "dart" / "docs"
# 사업의 내용/개요 section_title 패턴
BIZ_TITLES = ["II. 사업의 내용", "1. 사업의 개요", "2. 주요 제품 및 서비스"]
MIN_TEXT_LEN = 200  # 최소 텍스트 길이 (너무 짧은 건 제외)


def _extractBizText(parquetPath: Path) -> str | None:
    """parquet에서 최신 사업보고서의 사업 설명 텍스트를 추출."""
    try:
        df = pl.read_parquet(
            str(parquetPath),
            columns=["year", "report_type", "section_title", "section_content"],
        )
    except Exception:
        return None

    # 사업보고서만 (분기/반기 제외)
    df = df.filter(pl.col("report_type").str.contains("사업"))
    if df.height == 0:
        return None

    # 최신 연도
    latestYear = df["year"].cast(str).sort(descending=True).first()
    df = df.filter(pl.col("year") == latestYear)

    # 사업 관련 section 필터
    bizDf = df.filter(pl.col("section_title").is_in(BIZ_TITLES))
    if bizDf.height == 0:
        # fallback: "사업" 포함 title
        bizDf = df.filter(pl.col("section_title").str.contains("사업"))
    if bizDf.height == 0:
        return None

    # 텍스트 concat
    texts = bizDf["section_content"].drop_nulls().to_list()
    combined = "\n".join(str(t) for t in texts if t)
    return combined if len(combined) >= MIN_TEXT_LEN else None


def run():
    t0 = time.time()
    print("=" * 70)
    print("  098-001: TF-IDF 기반 peer 발견 기초 실험")
    print("=" * 70)

    # 1. KIND listing 로드
    from dartlab.engines.gather.listing import getKindList

    kindDf = getKindList()
    kindMap = {}  # stockCode -> (companyName, industry)
    for row in kindDf.iter_rows(named=True):
        code = row["종목코드"]
        kindMap[code] = (row["회사명"], row["업종"])

    print(f"\n  KIND 상장사: {len(kindMap)}개")

    # 2. docs parquet에서 텍스트 추출
    print("\n  텍스트 추출 중...")
    corpus = {}  # stockCode -> text
    parquetFiles = sorted(DATA_DIR.glob("*.parquet"))
    print(f"  docs parquet 파일: {len(parquetFiles)}개")

    for pf in parquetFiles:
        code = pf.stem
        if code not in kindMap:
            continue
        text = _extractBizText(pf)
        if text:
            corpus[code] = text

    print(f"  유효 텍스트 추출: {corpus and len(corpus)}개 / {len(kindMap)}개")
    tExtract = time.time() - t0
    print(f"  추출 시간: {tExtract:.1f}s")

    if len(corpus) < 50:
        print("  ❌ 유효 텍스트 부족 — 실험 중단")
        return

    # 3. TF-IDF 벡터화
    print("\n  TF-IDF 벡터화 중...")
    codes = sorted(corpus.keys())
    texts = [corpus[c] for c in codes]

    vectorizer = TfidfVectorizer(
        max_features=10000,
        ngram_range=(1, 2),
        min_df=3,
        max_df=0.95,
        sublinear_tf=True,
    )
    tfidfMatrix = vectorizer.fit_transform(texts)
    print(f"  TF-IDF matrix: {tfidfMatrix.shape}")
    print(f"  feature 수: {len(vectorizer.get_feature_names_out())}")

    # 4. cosine similarity
    print("\n  cosine similarity 산출 중...")
    simMatrix = cosine_similarity(tfidfMatrix)
    np.fill_diagonal(simMatrix, 0)  # 자기 자신 제외

    # 5. 종목별 상위 10 peer
    print("\n  상위 peer 추출 중...")
    peerMap = {}  # code -> [(peerCode, similarity), ...]
    for i, code in enumerate(codes):
        topIdx = np.argsort(simMatrix[i])[-10:][::-1]
        peers = [(codes[j], float(simMatrix[i][j])) for j in topIdx]
        peerMap[code] = peers

    # 6. 업종 일치 분석
    print("\n" + "─" * 70)
    print("  업종 일치 분석")
    print("─" * 70)

    # 업종 label 준비
    industryLabels = []
    for code in codes:
        _, industry = kindMap.get(code, ("", ""))
        industryLabels.append(industry)

    # 클러스터 기반 분석: k-means로 TF-IDF 클러스터링 vs KIND 업종
    from sklearn.cluster import KMeans

    nIndustries = len(set(industryLabels))
    nClusters = min(nIndustries, 50)  # 업종 수가 너무 많으면 50으로 제한
    print(f"  KIND 업종 고유값: {nIndustries}개")
    print(f"  k-means 클러스터 수: {nClusters}개")

    km = KMeans(n_clusters=nClusters, random_state=42, n_init=10, max_iter=300)
    clusterLabels = km.fit_predict(tfidfMatrix.toarray())

    ari = adjusted_rand_score(industryLabels, clusterLabels)
    print(f"\n  ARI (TF-IDF 클러스터 vs KIND 업종): {ari:.4f}")

    # 7. 업종 내/외 유사도 비율
    print("\n" + "─" * 70)
    print("  업종 내/외 유사도 비율")
    print("─" * 70)

    intraSims = []
    interSims = []
    for i in range(len(codes)):
        for j in range(i + 1, len(codes)):
            sim = simMatrix[i][j]
            if industryLabels[i] == industryLabels[j]:
                intraSims.append(sim)
            else:
                interSims.append(sim)

    avgIntra = np.mean(intraSims) if intraSims else 0.0
    avgInter = np.mean(interSims) if interSims else 0.0
    ratio = avgIntra / avgInter if avgInter > 0 else float("inf")

    print(f"  같은 업종 내 평균 유사도: {avgIntra:.4f} ({len(intraSims):,}쌍)")
    print(f"  다른 업종 간 평균 유사도: {avgInter:.4f} ({len(interSims):,}쌍)")
    print(f"  비율 (내/외): {ratio:.2f}x")

    # 8. 대표 종목 peer 확인
    print("\n" + "─" * 70)
    print("  대표 종목 peer (상위 5)")
    print("─" * 70)

    spotlightCodes = ["005930", "005380", "000660", "035420", "051910"]
    for code in spotlightCodes:
        if code not in peerMap:
            continue
        name, industry = kindMap.get(code, ("?", "?"))
        print(f"\n  {name} ({code}) — 업종: {industry}")
        for peerCode, sim in peerMap[code][:5]:
            peerName, peerIndustry = kindMap.get(peerCode, ("?", "?"))
            sameTag = "✅" if peerIndustry == industry else "  "
            print(f"    {sameTag} {peerName:20s} ({peerCode}) sim={sim:.3f} [{peerIndustry}]")

    # 9. peer 업종 일치율 (상위 10 중 같은 업종 비율)
    print("\n" + "─" * 70)
    print("  Peer 업종 일치율 분포")
    print("─" * 70)

    matchRates = []
    for code in codes:
        _, myIndustry = kindMap.get(code, ("", ""))
        if not myIndustry:
            continue
        peers = peerMap[code]
        matches = sum(1 for pc, _ in peers if kindMap.get(pc, ("", ""))[1] == myIndustry)
        matchRates.append(matches / len(peers))

    if matchRates:
        arr = np.array(matchRates)
        print(f"  평균 일치율: {arr.mean():.1%}")
        print(f"  중앙값: {np.median(arr):.1%}")
        print(f"  표준편차: {arr.std():.1%}")
        print(f"  0% 일치: {(arr == 0).sum()}개 ({(arr == 0).mean():.1%})")
        print(f"  50%+ 일치: {(arr >= 0.5).sum()}개 ({(arr >= 0.5).mean():.1%})")
        print(f"  100% 일치: {(arr == 1.0).sum()}개 ({(arr == 1.0).mean():.1%})")

    # 10. 요약
    tTotal = time.time() - t0
    print(f"\n{'=' * 70}")
    print(f"  요약")
    print(f"{'=' * 70}")
    print(f"  유효 종목: {len(corpus)}개")
    print(f"  TF-IDF features: {tfidfMatrix.shape[1]}개")
    print(f"  ARI: {ari:.4f}")
    print(f"  업종 내/외 유사도 비율: {ratio:.2f}x")
    print(f"  peer 업종 일치율 평균: {np.mean(matchRates):.1%}" if matchRates else "")
    print(f"  총 소요시간: {tTotal:.1f}s")


if __name__ == "__main__":
    run()
    print("\n실험 완료.")
