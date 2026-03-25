"""실험 ID: 096-005
실험명: DART 공시 정성 신호 추출 실데이터 검증

목적:
- sections diff에서 키워드 기반 tone 점수가 의미 있는 신호를 생성하는지
- 키워드 매칭 커버리지 확인 (기업당 최소 3개)
- confidence 분포 확인

가설:
1. 5개 종목 중 3개 이상에서 0이 아닌 toneScore 생성
2. 키워드 매칭 기업당 평균 3개 이상
3. impliedGrowthAdj 범위가 ±3%p 이내

방법:
1. 5개 종목 sections 로드
2. extractSignal() 실행 → toneScore, changeIntensity, topicSignals 출력
3. 커버리지 및 신뢰도 확인

결과:
- 삼성전자: tone=+0.043, intensity=0.625, adj=+0.08%p, conf=high
- 현대차: tone=+0.004, intensity=0.488, adj=+0.01%p, conf=high
- SK하이닉스: tone=+0.082, intensity=0.658, adj=+0.16%p (최고), conf=high
- NAVER: tone=-0.026, intensity=0.646, adj=-0.05%p (유일 부정), conf=high
- LG화학: tone=+0.032, intensity=0.644, adj=+0.06%p, conf=high
- 비영 신호: 5/5 (100%), confidence 전원 high
- 추출 시간: 192~339ms (Company 로드 제외)
- NAVER riskDerivative=-0.48 (파생상품 리스크 증가 감지)

결론:
- 가설1 채택: 5/5 종목에서 비영 toneScore 생성 (>3개 기준 충족)
- 가설2 해당없음: 키워드 카운트 직접 미출력이나 confidence=high → 5개+ 매칭 확인
- 가설3 채택: impliedGrowthAdj 범위 [-0.05, +0.16]%p — ±3%p cap 이내
- SK하이닉스 최고 tone(+0.082)은 반도체 호황 문맥과 일치 (합리적)
- NAVER 유일 부정(-0.026)은 riskDerivative -0.48 기여 — 해외 M&A 리스크 노출 반영
- impliedGrowthAdj 최대 +0.16%p는 현실적이나 앙상블 영향이 미미
  → 정성 신호는 방향성 보조 역할에 적합, 주력 소스로는 부족

실험일: 2026-03-25
"""

import time

import dartlab
from dartlab.engines.analysis.analyst.disclosureSignal import extractSignal

STOCKS = [
    ("005930", "삼성전자"),
    ("005380", "현대차"),
    ("000660", "SK하이닉스"),
    ("035420", "NAVER"),
    ("051910", "LG화학"),
]


def run():
    print("=" * 60)
    print("  공시 정성 신호 실데이터 검증")
    print("=" * 60)

    nonZeroCount = 0
    results = []

    for code, name in STOCKS:
        print(f"\n{'─'*60}")
        print(f"  {name} ({code})")
        print(f"{'─'*60}")

        t0 = time.time()
        c = dartlab.Company(code)
        tLoad = time.time() - t0

        sections = c.sections
        if sections is None:
            print(f"  ❌ sections 없음")
            continue

        print(f"  sections: {sections.height}행 × {sections.width}열, 로드 {tLoad:.1f}s")

        # 기간 컬럼 확인
        periodCols = sorted(
            [col for col in sections.columns if _isPeriodLike(col)],
            reverse=True,
        )
        print(f"  기간: {periodCols[:5]}")

        t1 = time.time()
        signal = extractSignal(sections)
        tSignal = time.time() - t1

        if signal is None:
            print(f"  ❌ 신호 추출 실패")
            continue

        print(f"  toneScore: {signal.toneScore:+.3f}")
        print(f"  changeIntensity: {signal.changeIntensity:.3f}")
        print(f"  impliedGrowthAdj: {signal.impliedGrowthAdj:+.2f}%p")
        print(f"  confidence: {signal.confidence}")

        if signal.topicSignals:
            print(f"  topic별 신호:")
            for topic, score in signal.topicSignals.items():
                print(f"    {topic:30s}: {score:+.2f}")

        if signal.keyPhrases:
            print(f"  핵심 구절:")
            for phrase in signal.keyPhrases[:3]:
                print(f"    \"{phrase}\"")

        print(f"  추출 시간: {tSignal*1000:.0f}ms")

        if signal.toneScore != 0.0:
            nonZeroCount += 1

        results.append((name, signal))
        del c

    # 요약
    print(f"\n{'='*60}")
    print(f"  요약")
    print(f"{'='*60}")
    print(f"  비영 신호: {nonZeroCount}/{len(STOCKS)} ({nonZeroCount/len(STOCKS)*100:.0f}%)")

    if results:
        tones = [r[1].toneScore for r in results]
        adjs = [r[1].impliedGrowthAdj for r in results]
        confs = [r[1].confidence for r in results]
        print(f"  toneScore 범위: [{min(tones):+.3f}, {max(tones):+.3f}]")
        print(f"  growthAdj 범위: [{min(adjs):+.2f}, {max(adjs):+.2f}]%p")
        print(f"  confidence 분포: {dict((c, confs.count(c)) for c in set(confs))}")

    for name, sig in results:
        print(f"  {name:12s}: tone={sig.toneScore:+.3f} adj={sig.impliedGrowthAdj:+.2f}%p conf={sig.confidence}")


def _isPeriodLike(name: str) -> bool:
    import re
    return bool(re.fullmatch(r"\d{4}(Q[1-4])?", name))


if __name__ == "__main__":
    run()
    print("\n실험 완료.")
