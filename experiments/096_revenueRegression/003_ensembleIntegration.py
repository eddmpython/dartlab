"""실험 ID: 096-003
실험명: 9소스 앙상블 통합 테스트 — priceImplied + crossSection 반영 확인

목적:
- forecastRevenue()에 marketCap, crossSectionGrowth 인자를 넘겼을 때
  소스 8(priceImplied)과 소스 9(crossSection)이 실제로 앙상블에 반영되는지 검증
- 기존 7소스만 사용했을 때 대비 예측값 변화 확인
- investmentSignal, marketImpliedGap 필드 정상 출력 확인

가설:
1. marketCap 전달 시 priceImplied 소스가 sourceWeights에 나타남
2. crossSectionGrowth 전달 시 crossSection 소스가 sourceWeights에 나타남
3. 두 소스 추가 시 예측값이 기존 7소스 대비 변화 (±0.1%p 이상)
4. marketImpliedGap과 investmentSignal이 None이 아님

방법:
1. 삼성전자 finance timeseries 로드
2. 3가지 시나리오 비교:
   a. 기존 7소스 (marketCap=None, crossSectionGrowth=None)
   b. +priceImplied (marketCap=시가총액)
   c. +priceImplied+crossSection (marketCap + crossSectionGrowth=5.0)
3. 각 시나리오별 projected, growthRates, sourceWeights, signal 비교

결과:
- 시나리오 A(7소스): 성장률 +23.0%/+3.0%/+3.0%, gap=None, signal=None
- 시나리오 B(+implied): 성장률 +26.4%/+5.7%/+5.7%, gap=-16.7%p, signal=overpriced
  소스: timeseries 0.18, consensus 0.46, roic 0.24, priceImplied 0.12
- 시나리오 C(+implied+cs): 성장률 +27.4%/+6.0%/+6.0%, gap=-16.2%p, signal=overpriced
  소스: timeseries 0.04, consensus 0.46, roic 0.24, priceImplied 0.12, crossSection 0.14
- A→B 변화: +3.4%p, A→C 변화: +4.4%p
- 속도: A 2086ms, B 691ms, C 934ms (B/C가 더 빠른 것은 Company 캐시 효과)

결론:
- 가설1 채택: marketCap 전달 시 priceImplied가 sourceWeights에 정상 출현 (0.12)
- 가설2 채택: crossSectionGrowth 전달 시 crossSection이 sourceWeights에 정상 출현 (0.14)
- 가설3 채택: A→C +4.4%p 변화 (>>0.1%p 기준)
- 가설4 채택: marketImpliedGap=-16.2%p, investmentSignal="overpriced" 정상 출력
- priceImplied 내재 성장률(+43.6%)이 앙상블 예측(+27.4%)보다 높아 overpriced 판정
  → 시장이 더 높은 성장을 가격에 반영 중이라는 합리적 해석
- 9소스 앙상블 통합 검증 완료 — Phase 1 코어 엔진 정상 작동 확인

실험일: 2026-03-25
"""

import time

import dartlab
from dartlab.engines.analysis.analyst.revenueForecast import forecastRevenue
from dartlab.engines.common.finance.extract import getTTM


def run():
    print("=" * 60)
    print("  9소스 앙상블 통합 테스트")
    print("=" * 60)

    t0 = time.time()
    c = dartlab.Company("005930")
    tLoad = time.time() - t0
    print(f"  삼성전자 로드: {tLoad:.1f}s")

    tsRaw = c.finance.timeseries
    series = tsRaw[0] if isinstance(tsRaw, tuple) else tsRaw
    if not series:
        print("  timeseries 없음 — 중단")
        return

    rev = getTTM(series, "IS", "sales")
    print(f"  TTM 매출: {rev/1e12:.1f}조" if rev else "  TTM 매출: None")

    mktCap = 1170e12  # 수동 시가총액 (장 마감 후 null 대비)

    # 시나리오 A: 기존 7소스
    print(f"\n{'─'*60}")
    print("  시나리오 A: 기존 7소스 (priceImplied/crossSection 없음)")
    print(f"{'─'*60}")
    t1 = time.time()
    fA = forecastRevenue(series, stockCode="005930", sectorKey="반도체", horizon=3)
    tA = time.time() - t1
    _printResult(fA, tA)

    # 시나리오 B: +priceImplied
    print(f"\n{'─'*60}")
    print("  시나리오 B: 7소스 + priceImplied (marketCap=1170조)")
    print(f"{'─'*60}")
    t2 = time.time()
    fB = forecastRevenue(
        series, stockCode="005930", sectorKey="반도체", horizon=3,
        marketCap=mktCap,
    )
    tB = time.time() - t2
    _printResult(fB, tB)

    # 시나리오 C: +priceImplied + crossSection
    print(f"\n{'─'*60}")
    print("  시나리오 C: 7소스 + priceImplied + crossSection(5.0%)")
    print(f"{'─'*60}")
    t3 = time.time()
    fC = forecastRevenue(
        series, stockCode="005930", sectorKey="반도체", horizon=3,
        marketCap=mktCap,
        crossSectionGrowth=5.0,
    )
    tC = time.time() - t3
    _printResult(fC, tC)

    # 비교
    print(f"\n{'='*60}")
    print("  시나리오 비교")
    print(f"{'='*60}")
    for label, f in [("A(7소스)", fA), ("B(+implied)", fB), ("C(+implied+cs)", fC)]:
        gr = f.growthRates
        gap = f.marketImpliedGap
        sig = f.investmentSignal
        print(f"  {label:20s}: 성장률 {gr[0]:+.1f}% / {gr[1]:+.1f}% / {gr[2]:+.1f}%  gap={gap}  signal={sig}")

    # 차이 확인
    diffBC = abs(fB.growthRates[0] - fA.growthRates[0])
    diffCC = abs(fC.growthRates[0] - fA.growthRates[0])
    print(f"\n  A→B 1년차 성장률 변화: {diffBC:.2f}%p")
    print(f"  A→C 1년차 성장률 변화: {diffCC:.2f}%p")
    print(f"  가설3 (±0.1%p 이상 변화): {'채택' if diffCC > 0.1 else '기각'}")


def _printResult(f, elapsed):
    print(f"  방법: {f.method}")
    print(f"  소스: {f.sourceWeights}")
    for i, (proj, gr) in enumerate(zip(f.projected, f.growthRates), 1):
        print(f"  +{i}년: {proj/1e12:.1f}조 ({gr:+.1f}%)")
    print(f"  신뢰도: {f.confidence}")
    if f.marketImpliedGap is not None:
        print(f"  시장내재 갭: {f.marketImpliedGap:+.1f}%p")
        print(f"  투자신호: {f.investmentSignal}")
    else:
        print(f"  시장내재 갭: None")
        print(f"  투자신호: None")
    print(f"  시간: {elapsed*1000:.0f}ms")


if __name__ == "__main__":
    run()
    print("\n실험 완료.")
