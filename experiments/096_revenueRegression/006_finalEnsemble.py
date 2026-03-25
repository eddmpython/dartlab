"""실험 ID: 096-006
실험명: 최종 통합 — TV 수정 + disclosure + 가중치 재설계 10소스 앙상블

목적:
- Phase 1 수정(TV 버그, ±30% cap, crossSection 비활성, 시계열 최소 보장) +
  Phase 2(disclosureSignal) 전체 통합 후 예측 품질 확인
- 기존 7소스 대비 개선/악화 여부

가설:
1. TV 수정 + cap 후 priceImplied 기여가 ±5%p 이내
2. disclosureSignal이 최소 3개 종목에서 0이 아닌 가중치 생성
3. 시계열 가중치가 최소 0.10 보장
4. 가중치 합이 1.00

방법:
1. 삼성전자/현대차/SK하이닉스 3사
2. 시나리오 비교: (A) 기존 7소스, (B) 8소스(+priceImplied), (C) full 통합
3. sourceWeights 확인

결과:
- 삼성전자(005930):
  A(7소스): +23.0% / B(+implied): +25.8% / C(full): +26.0%
  A→C: +3.00%p, ts=0.14, gap=-18.0%p overpriced
  disclosure: tone=+0.043, adj=+0.08%p
- 현대차(005380):
  A(7소스): +3.2% / B(+implied): +1.6% / C(full): +1.4%
  A→C: -1.80%p, ts=0.14, gap=+17.2%p underpriced
  disclosure: tone=+0.004, adj=+0.01%p
- SK하이닉스(000660):
  A(7소스): +79.0% / B(+implied): +78.1% / C(full): +78.7%
  A→C: -0.30%p, ts=0.12, gap=+50.5%p underpriced
  disclosure: tone=+0.082, adj=+0.16%p
- 전 종목 가중치합 1.000, timeseries ≥ 0.12 (floor 0.10 보장)

결론:
- 가설1 채택: priceImplied 기여 +3.0%p/-1.8%p/-0.3%p — 전부 ±5%p 이내
- 가설2 채택: 3/3 종목에서 disclosure 가중치 0.02~0.06 생성 (비영)
- 가설3 채택: timeseries 최소 0.12 (floor 0.10 이상 보장)
- 가설4 채택: 전 시나리오 가중치합 1.000
- priceImplied ±30% cap + 가중치 0.08~0.09로 앙상블 왜곡 제한적
- disclosure adj 최대 +0.16%p — 방향성 보조 역할, 앙상블 영향 미미
- gap 신호: 삼성전자 overpriced(-18%p), 현대차/SK하이닉스 underpriced(+17/+50%p)
- Phase 1+2 전체 통합 후 앙상블 안정성 확인 — 흡수 기준 충족

실험일: 2026-03-25
"""

import time

import dartlab
from dartlab.engines.analysis.analyst.disclosureSignal import extractSignal
from dartlab.engines.analysis.analyst.revenueForecast import forecastRevenue
from dartlab.engines.common.finance.extract import getTTM

STOCKS = [
    ("005930", "삼성전자", 1170e12),
    ("005380", "현대차", 46e12),
    ("000660", "SK하이닉스", 120e12),
]


def run():
    print("=" * 70)
    print("  최종 10소스 앙상블 통합 테스트")
    print("=" * 70)

    for code, name, mktCap in STOCKS:
        print(f"\n{'━'*70}")
        print(f"  {name} ({code})")
        print(f"{'━'*70}")

        c = dartlab.Company(code)
        tsRaw = c.finance.timeseries
        series = tsRaw[0] if isinstance(tsRaw, tuple) else tsRaw
        if not series:
            print("  ❌ timeseries 없음")
            continue

        # disclosure 신호 추출
        dsAdj = None
        sections = c.sections
        if sections is not None:
            ds = extractSignal(sections)
            if ds and ds.impliedGrowthAdj != 0.0:
                dsAdj = ds.impliedGrowthAdj
                print(f"  disclosure: tone={ds.toneScore:+.3f}, adj={ds.impliedGrowthAdj:+.2f}%p")
            else:
                print(f"  disclosure: tone={ds.toneScore if ds else 'None'}, adj=0")

        # (A) 기존 7소스
        fA = forecastRevenue(series, stockCode=code, sectorKey="", horizon=3)

        # (B) +priceImplied (TV 수정 + ±30% cap)
        fB = forecastRevenue(series, stockCode=code, sectorKey="", horizon=3, marketCap=mktCap)

        # (C) full 통합 (+priceImplied + disclosure)
        fC = forecastRevenue(
            series, stockCode=code, sectorKey="", horizon=3,
            marketCap=mktCap,
            disclosureGrowthAdj=dsAdj,
        )

        for label, f in [("A(7소스)", fA), ("B(+implied)", fB), ("C(full)", fC)]:
            gr = f.growthRates
            sw = f.sourceWeights
            gap = f.marketImpliedGap
            sig = f.investmentSignal
            wSum = sum(sw.values())
            tsW = sw.get("timeseries", 0)
            print(f"\n  [{label}]")
            print(f"    성장률: {gr[0]:+.1f}% / {gr[1]:+.1f}% / {gr[2]:+.1f}%")
            print(f"    소스: {sw}")
            print(f"    가중치합: {wSum:.3f}, ts={tsW:.3f}")
            if gap is not None:
                print(f"    gap={gap:+.1f}%p, signal={sig}")

        # 비교
        diffAB = fB.growthRates[0] - fA.growthRates[0]
        diffAC = fC.growthRates[0] - fA.growthRates[0]
        print(f"\n  A→B: {diffAB:+.2f}%p, A→C: {diffAC:+.2f}%p")

        del c


if __name__ == "__main__":
    run()
    print("\n\n실험 완료.")
