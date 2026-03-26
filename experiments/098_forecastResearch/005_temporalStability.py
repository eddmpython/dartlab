"""실험 ID: 098-005
실험명: TF-IDF peer 그룹 시간 안정성

목적:
- 연도별 사업보고서 TF-IDF peer가 시간적으로 안정적인지 확인
- peer 그룹 갱신 주기 결정 근거

가설:
1. 상위 10 peer의 연도간 Jaccard similarity > 0.5 (절반 이상 유지)
2. 상위 3 peer는 연도간 80%+ 유지
3. 대형주(시총 상위)가 소형주보다 안정적

방법:
1. 2021~2024 각 연도별 사업보고서 텍스트로 TF-IDF peer 산출
2. 연도간 상위 10 peer의 Jaccard similarity 측정
3. 대표 5종목 심층 분석

결과:
- 공통 종목: 200개 (docs 파일 크기 상위)
- 연도간 Jaccard (상위 10 peer):
  2021→2022: 0.676, 2022→2023: 0.669, 2023→2024: 0.687
  전체 평균: 0.678, ≥0.5 비율: 89.2%
- 상위 3 peer 유지율: 평균 74~75%, ≥67% 비율 33~38%
- 대표 종목 안정성:
  삼성전자: LG전자/SK하이닉스/삼성전기/LG디스플레이 — 4년간 상위 4 유지
  현대차: 기아 4년 연속 1위, 현대모비스/현대로템도 안정
  NAVER: 카카오/KT/NHN 4년간 꾸준
  LG화학: 롯데케미칼/SK이노베이션/LG전자/한화솔루션 안정

결론:
- 가설1 채택: Jaccard 0.678 (0.5 초과). 상위 10 peer의 67%가 다음 해에도 유지
- 가설2 부분 채택: 상위 3 peer 유지율 75% (80% 미달이나 충분히 안정)
- 가설3 미검증: 대형주/소형주 비교는 200개 대형주만 사용하여 확인 불가
- **TF-IDF peer는 시간적으로 안정적** — 연간 갱신이면 충분
- 핵심 peer(상위 3-4)는 매우 안정적, 5위 이하에서 소폭 변동
- 사업 구조의 점진적 변화를 자연스럽게 반영 (급변 없음)

실험일: 2026-03-25
"""

import re
import time
from pathlib import Path

import numpy as np
import polars as pl
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

DATA_DIR = Path(__file__).resolve().parents[2] / "data" / "dart" / "docs"
EXCLUDE_INDUSTRIES = {"기타 금융업", "신탁업", "집합투자업"}
EXCLUDE_NAME_PATTERNS = ["지주", "홀딩스", "Holdings"]
YEARS = ["2021", "2022", "2023", "2024"]
MIN_TEXT_LEN = 200

# 분석 대상: 데이터가 충분한 대형주 200개로 제한 (메모리+속도)
MAX_COMPANIES = 200


def _cleanText(text: str) -> str:
    text = re.sub(r"<[^>]+>", " ", text)
    text = re.sub(r"\d[\d,\.]*\s*(원|억|조|만|천|백|%|백만|십억|달러|USD|KRW|Won)", " ", text)
    text = re.sub(r"\b\d[\d,\.]*\b", " ", text)
    text = re.sub(r"[│├└┌─┐┘┤┬┴┼━┃╋\(\)\[\]\{\}]+", " ", text)
    text = re.sub(r"\s+", " ", text).strip()
    return text


def _extractBizTextByYear(parquetPath: Path, year: str) -> str | None:
    """특정 연도 사업보고서의 사업 설명 텍스트."""
    try:
        df = pl.read_parquet(str(parquetPath), columns=["year", "report_type", "section_title", "section_content"])
    except Exception:
        return None
    df = df.filter(
        (pl.col("report_type").str.contains("사업")) &
        (pl.col("year") == year)
    )
    if df.height == 0:
        return None
    bizDf = df.filter(pl.col("section_title").str.contains("사업의 내용|사업의 개요|주요 제품"))
    if bizDf.height == 0:
        bizDf = df.filter(pl.col("section_title").str.contains("사업"))
    if bizDf.height == 0:
        return None
    texts = bizDf["section_content"].drop_nulls().to_list()
    combined = _cleanText("\n".join(str(t) for t in texts if t))
    return combined if len(combined) >= MIN_TEXT_LEN else None


def _isExcluded(name: str, industry: str) -> bool:
    if industry in EXCLUDE_INDUSTRIES:
        return True
    return any(pat in name for pat in EXCLUDE_NAME_PATTERNS)


def _jaccard(set1: set, set2: set) -> float:
    if not set1 and not set2:
        return 1.0
    inter = len(set1 & set2)
    union = len(set1 | set2)
    return inter / union if union > 0 else 0.0


def run():
    t0 = time.time()
    print("=" * 70)
    print("  098-005: TF-IDF peer 시간 안정성")
    print("=" * 70)

    from dartlab.gather.listing import getKindList
    kindDf = getKindList()
    kindMap = {}
    for row in kindDf.iter_rows(named=True):
        code, name, industry = row["종목코드"], row["회사명"], row["업종"]
        if not _isExcluded(name, industry):
            kindMap[code] = (name, industry)

    # 대상 종목 선정 (docs 파일 크기 기준 상위 200 = 대형주 경향)
    parquetFiles = sorted(DATA_DIR.glob("*.parquet"))
    candidates = [(pf, pf.stat().st_size) for pf in parquetFiles if pf.stem in kindMap]
    candidates.sort(key=lambda x: x[1], reverse=True)
    targetFiles = [pf for pf, _ in candidates[:MAX_COMPANIES]]
    targetCodes = [pf.stem for pf in targetFiles]
    print(f"\n  대상 종목: {len(targetCodes)}개 (docs 파일 크기 상위)")

    # 연도별 텍스트 추출
    yearCorpus = {}  # year -> {code -> text}
    for year in YEARS:
        corpus = {}
        for pf in targetFiles:
            code = pf.stem
            text = _extractBizTextByYear(pf, year)
            if text:
                corpus[code] = text
        yearCorpus[year] = corpus
        print(f"  {year}: {len(corpus)}개 종목 텍스트 추출")

    # 공통 종목만 사용
    commonCodes = set(targetCodes)
    for year in YEARS:
        commonCodes &= set(yearCorpus[year].keys())
    commonCodes = sorted(commonCodes)
    print(f"\n  전 연도 공통 종목: {len(commonCodes)}개")

    if len(commonCodes) < 30:
        print("  ❌ 공통 종목 부족 — 실험 중단")
        return

    # 연도별 TF-IDF → peer 산출
    yearPeers = {}  # year -> {code -> [peerCode, ...]}
    for year in YEARS:
        texts = [yearCorpus[year][c] for c in commonCodes]
        vec = TfidfVectorizer(
            max_features=10000, ngram_range=(1, 2), min_df=3, max_df=0.90,
            sublinear_tf=True, token_pattern=r"(?u)\b[가-힣a-zA-Z]{2,}\b",
        )
        mat = vec.fit_transform(texts)
        sim = cosine_similarity(mat)
        np.fill_diagonal(sim, 0)

        peers = {}
        for i, code in enumerate(commonCodes):
            topIdx = np.argsort(sim[i])[-10:][::-1]
            peers[code] = [commonCodes[j] for j in topIdx]
        yearPeers[year] = peers

    # Jaccard similarity 연도간
    print("\n" + "─" * 70)
    print("  연도간 Jaccard similarity (상위 10 peer)")
    print("─" * 70)

    pairJaccards = {}
    for i in range(len(YEARS) - 1):
        y1, y2 = YEARS[i], YEARS[i + 1]
        jaccards = []
        for code in commonCodes:
            set1 = set(yearPeers[y1][code])
            set2 = set(yearPeers[y2][code])
            jaccards.append(_jaccard(set1, set2))
        arr = np.array(jaccards)
        pairJaccards[(y1, y2)] = arr
        print(f"  {y1}→{y2}: 평균={arr.mean():.3f}, 중앙값={np.median(arr):.3f}, "
              f"≥0.5: {(arr >= 0.5).mean():.1%}, ≥0.7: {(arr >= 0.7).mean():.1%}")

    # 상위 3 peer 안정성
    print("\n" + "─" * 70)
    print("  연도간 상위 3 peer 유지율")
    print("─" * 70)

    for i in range(len(YEARS) - 1):
        y1, y2 = YEARS[i], YEARS[i + 1]
        retainRates = []
        for code in commonCodes:
            top3_y1 = set(yearPeers[y1][code][:3])
            top3_y2 = set(yearPeers[y2][code][:3])
            retain = len(top3_y1 & top3_y2) / 3
            retainRates.append(retain)
        arr = np.array(retainRates)
        print(f"  {y1}→{y2}: 유지율 평균={arr.mean():.1%}, ≥67%: {(arr >= 0.67).mean():.1%}")

    # 대표 종목 peer 변화
    print("\n" + "─" * 70)
    print("  대표 종목 peer 변화 (상위 5)")
    print("─" * 70)

    for code in ["005930", "005380", "000660", "035420", "051910"]:
        if code not in commonCodes:
            continue
        name = kindMap.get(code, ("?",))[0]
        print(f"\n  {name} ({code})")
        for year in YEARS:
            peers = yearPeers[year][code][:5]
            peerNames = [kindMap.get(pc, ("?",))[0][:8] for pc in peers]
            print(f"    {year}: {', '.join(peerNames)}")

    # 요약
    tTotal = time.time() - t0
    allJaccards = np.concatenate(list(pairJaccards.values()))
    print(f"\n{'=' * 70}")
    print(f"  요약")
    print(f"{'=' * 70}")
    print(f"  공통 종목: {len(commonCodes)}개")
    print(f"  전체 Jaccard 평균: {allJaccards.mean():.3f}")
    print(f"  Jaccard ≥ 0.5 비율: {(allJaccards >= 0.5).mean():.1%}")
    print(f"  총 소요시간: {tTotal:.1f}s")


if __name__ == "__main__":
    run()
    print("\n실험 완료.")
