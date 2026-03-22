"""실험 ID: 009
실험명: 텍스트 감성 분석 — 사업보고서 부정적 어조 추이

목적:
- Loughran-McDonald(2011) 부정어 분석을 한국 DART 공시에 적용
- sections 텍스트에서 위험/부정 키워드 빈도 추이를 기간별로 분석
- 텍스트 신호가 정량 부실 지표와 상관관계를 보이는지 확인

가설:
1. 부정 키워드 빈도가 높은 기업일수록 정량 부실 점수도 높을 것
2. "위험", "손실", "불확실성" 등의 빈도 추이가 악화 선행지표로 작동
3. 업종별로 부정어 기저 수준이 다를 것 (금융업 > 제조업)

방법:
1. 한국어 부정/위험 키워드 사전 정의 (Loughran-McDonald 한국어 적응)
2. sections에서 주요 topic 텍스트 추출
3. 기간별 부정어 빈도(부정어 수 / 전체 어절 수 × 1000) 계산
4. 20개 종목 비교

결과 (실험 후 작성):
- 16/16 종목 분석 (삼성전기 sections 텍스트 부족으로 0 반환)
- 부정어 밀도 상위 5:
  1. 삼성생명: 15.65/1k (금융업, 부정비율 87.7%)
  2. S-Oil: 13.84/1k (정유업, 위험/변동성 키워드 빈출)
  3. KB금융: 12.85/1k (금융업)
  4. 신한지주: 12.47/1k (금융업)
  5. 한화: 11.41/1k (방산/화학)
- 부정어 밀도 하위: SK 0.87/1k, NAVER 2.99/1k, LG 4.01/1k
- **금융업 평균 11.29/1k vs 비금융업 6.92/1k** — 1.63배 차이
- 부정비율(부정/(부정+긍정)): 삼성증권 88.6% > 삼성생명 87.7% > 셀트리온 84.3%
- 기간별 추이:
  - KB금융: 11.5→12.9→13.1→13.1→13.9 (5기 연속 상승 — 악화 신호)
  - 신한지주: 12.4→11.2→12.6→13.6→13.8 (최근 3기 상승)
  - 삼성생명: 15.9→14.6→14.5→15.3→16.2 (최근 2기 반등)
  - S-Oil: 13.2→14.4 (상승)
  - 삼성전자: 8.3→7.9→7.6→7.7→1.9 (2025 급감 — 최신 보고서 부분공시 가능성)
- 2025년 급감 종목 다수 — 최신 사업보고서 아직 부분 공시로 텍스트 불완전 가능성

결론:
- **가설 1 부분 채택**: 금융업은 부정어 밀도 높고 정량 부실 점수도 높은 편 (004 앙상블 금융 0.54).
  그러나 비금융 대형주(삼성전자, 현대차)는 부정어 낮고 정량도 안전 — 방향 일치.
  SK는 부정어 0.87로 극단적 저밀도이나 ICR<1 7기 연속(006) — 텍스트 밀도가 낮은 이유는
  지주회사 sections 구조 차이(텍스트 양 자체 극단적 많음 24M 어절)
- **가설 2 부분 채택**: KB금융 5기 연속 부정어 밀도 상승은 시계열 악화 신호로 해석 가능.
  그러나 2025년 텍스트 불완전으로 추이 해석에 주의 필요
- **가설 3 채택**: 금융업 11.29 vs 비금융업 6.92 — 업종별 기저 수준 유의미 차이 확인.
  금융업은 규제/리스크 서술 의무로 부정어 구조적 고밀도
- **한계**: 어절 기반 밀도는 텍스트 양 극단값(SK 24M, 삼성증권 12M)에 왜곡.
  업종별 정규화 또는 핵심 section만 분석하는 방식이 더 정확할 것
- **엔진 흡수 방향**: Optional. 텍스트 감성은 보조지표로만 활용.
  sections 기반 keyword scan을 insight/textual.py로 분리 가능하나 우선순위 낮음

실험일: 2026-03-22
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "src"))

import polars as pl
from dartlab import Company


# ── 한국어 부정/위험 키워드 사전 (Loughran-McDonald 한국어 적응) ──
NEGATIVE_KEYWORDS = {
    # 재무 위험
    "손실", "적자", "감소", "하락", "악화", "부진", "축소", "저하",
    "감손", "손상", "상각", "충당", "대손", "부실", "미수", "연체",
    # 운영 위험
    "중단", "폐쇄", "폐지", "철수", "구조조정", "정리", "해고",
    "파산", "부도", "회생", "청산", "도산",
    # 법적 위험
    "소송", "분쟁", "제재", "과징금", "벌금", "위반", "처분", "시정",
    # 불확실성
    "불확실", "위험", "리스크", "우려", "변동성", "취약", "불안정",
    # 계속기업
    "계속기업", "존속", "의문", "불투명",
}

POSITIVE_KEYWORDS = {
    "성장", "증가", "개선", "확대", "호조", "흑자", "회복",
    "강화", "안정", "우수", "양호", "견조",
}


def _count_keywords(text: str, keywords: set) -> int:
    """텍스트에서 키워드 빈도 카운트."""
    count = 0
    for kw in keywords:
        # 어절 단위가 아니라 부분 문자열 매칭 (한국어 교착어 특성)
        count += text.count(kw)
    return count


def analyze_text_sentiment(c: Company) -> dict | None:
    """sections 텍스트에서 감성 분석.

    sections는 기간 컬럼(2016, 2017, ..., 2025, 2016Q1 등)에 텍스트가 들어있는 구조.
    """
    try:
        sections = c.docs.sections
    except Exception:
        return None

    if sections is None or len(sections) == 0:
        return None

    # 기간 컬럼 식별 (연도/분기 패턴)
    import re
    period_cols = [col for col in sections.columns if re.match(r"^\d{4}(Q[1-4])?$", col)]
    # 연간만 사용 (분기 제외하여 비교 단순화)
    annual_cols = [col for col in period_cols if re.match(r"^\d{4}$", col)]

    if not annual_cols:
        return None

    trends = {}
    total_words = 0
    total_neg = 0
    total_pos = 0

    for period in sorted(annual_cols):
        if period not in sections.columns:
            continue
        col_data = sections[period].drop_nulls().to_list()
        all_text = " ".join(str(v) for v in col_data if v)
        if len(all_text) < 50:
            continue

        words = len(all_text.split())
        neg = _count_keywords(all_text, NEGATIVE_KEYWORDS)
        pos = _count_keywords(all_text, POSITIVE_KEYWORDS)

        total_words += words
        total_neg += neg
        total_pos += pos

        trends[period] = {
            "words": words,
            "neg": neg,
            "pos": pos,
            "neg_per_1k": round(neg / words * 1000, 2) if words > 0 else 0,
        }

    return {
        "total_words": total_words,
        "neg_count": total_neg,
        "pos_count": total_pos,
        "neg_per_1k": round(total_neg / total_words * 1000, 2) if total_words > 0 else 0,
        "pos_per_1k": round(total_pos / total_words * 1000, 2) if total_words > 0 else 0,
        "sentiment_ratio": round(total_neg / (total_neg + total_pos) * 100, 1) if (total_neg + total_pos) > 0 else 50,
        "period_trends": trends,
    }


TEST_STOCKS = [
    ("005930", "삼성전자"), ("000660", "SK하이닉스"), ("035420", "NAVER"),
    ("068270", "셀트리온"), ("003550", "LG"), ("005380", "현대차"),
    ("105560", "KB금융"), ("055550", "신한지주"),
    ("003490", "대한항공"), ("000880", "한화"),
    ("016360", "삼성증권"), ("010950", "S-Oil"),
    ("009150", "삼성전기"), ("066570", "LG전자"),
    ("034730", "SK"), ("032830", "삼성생명"),
]

FIN_NAMES = {"KB금융", "신한지주", "삼성증권", "삼성생명"}


if __name__ == "__main__":
    print("=" * 110)
    print("실험 009: 텍스트 감성 분석 — 사업보고서 부정적 어조")
    print("=" * 110)

    results = []
    for code, name in TEST_STOCKS:
        try:
            c = Company(code)
            sentiment = analyze_text_sentiment(c)
            if sentiment:
                results.append({"name": name, "is_fin": name in FIN_NAMES, **sentiment})
            else:
                print(f"  {name}: sections 없음")
            del c
        except Exception as e:
            print(f"  {name}: {e}")

    # ── 결과 ──
    print(f"\n{'종목':>12} {'어절수':>8} {'부정어':>6} {'긍정어':>6} {'부정/1k':>8} {'긍정/1k':>8} {'부정비율':>8} {'금융':>4}")
    print("-" * 110)

    for r in sorted(results, key=lambda x: x["neg_per_1k"], reverse=True):
        fin = "Y" if r["is_fin"] else ""
        print(f"  {r['name']:>10} {r['total_words']:>8} {r['neg_count']:>6} {r['pos_count']:>6} "
              f"{r['neg_per_1k']:>8.2f} {r['pos_per_1k']:>8.2f} {r['sentiment_ratio']:>7.1f}% {fin:>4}")

    # ── 금융업 vs 비금융업 ──
    print("\n" + "=" * 110)
    fin_r = [r for r in results if r["is_fin"]]
    nfin_r = [r for r in results if not r["is_fin"]]
    if fin_r:
        avg_fin = sum(r["neg_per_1k"] for r in fin_r) / len(fin_r)
        avg_nfin = sum(r["neg_per_1k"] for r in nfin_r) / len(nfin_r) if nfin_r else 0
        print(f"  금융업 부정어 밀도: {avg_fin:.2f}/1000어절")
        print(f"  비금융업 부정어 밀도: {avg_nfin:.2f}/1000어절")

    # ── 기간별 추이 (최신 3기간) ──
    print("\n" + "=" * 110)
    print("기간별 부정어 밀도 추이 (최근)")
    print("-" * 110)
    for r in results:
        if r["period_trends"]:
            periods = sorted(r["period_trends"].keys())[-5:]
            trend_str = " → ".join(f"{p}:{r['period_trends'][p]['neg_per_1k']:.1f}" for p in periods)
            print(f"  {r['name']:>10}: {trend_str}")

    print(f"\n총 {len(results)}개 종목 텍스트 감성 분석 완료")
