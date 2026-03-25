"""실험 ID: 096-004
실험명: priceImplied TV 공식 수정 후 WACC/terminalGrowth 센시티비티

목적:
- TV 이중 성장 적용 버그 수정 후 내재성장률이 합리적 범위로 내려오는지 확인
- WACC × terminalGrowth 센시티비티 매트릭스 (6×3 = 18셀)
- ±50% cap 적용 전후 비교

가설:
1. TV 수정 후 삼성전자 내재성장률이 +29.3% → 5~20% 범위로 하락
2. WACC 1%p 변화당 내재성장률 변동 10%p 이내
3. cap(±50%)에 걸리는 경우가 전체의 20% 이하

방법:
1. 삼성전자/현대차/SK하이닉스 timeseries 로드
2. WACC 7~12% × terminalGrowth 1~3% 센시티비티
3. 각 셀에서 reverseImpliedGrowth 호출 → 내재성장률 기록

결과:
- 삼성전자 (시총 1170조, 매출 334조, P/S=3.5x):
  WACC 7%/tG=1%: +25.0%, WACC 10%/tG=2%: +39.6%, WACC 12%/tG=3%: +46.6%
  TV 수정 전 +29.3% → 수정 후 +39.6% (WACC10/tG2) — 오히려 상승
  cap(±50%) 적용: 3/18셀(17%)
- 현대차 (시총 46조, 매출 186조, P/S=0.25x):
  전 구간 음수 (-7.2% ~ -33.9%), WACC 10%/tG=2%: -16.7%
- SK하이닉스 (시총 120조, 매출 97조, 마진 48.6%):
  전 구간 음수 (-21.9% ~ -44.0%), WACC 10%/tG=2%: -29.7%
- WACC 1%p당 최대 변동: 삼성전자 7.9%p, 현대차 4.6%p, SK하이닉스 3.8%p

결론:
- 가설1 기각: TV 수정 후 삼성전자 내재성장률이 5~20% 범위가 아님 (+39.6%)
  근본 원인: P/S 3.5x 기업에서 FCF margin 8.7%로는 DCF 역산 자체가 고성장 요구
  이는 버그가 아닌 모델 한계 — 삼성전자 시총이 미래 매출이 아닌 기술/특허 프리미엄 포함
- 가설2 채택: WACC 1%p당 변동 7.9%p 이내 (10%p 기준 충족)
- 가설3 채택 경계: cap 17%로 20% 이하이나, 삼성전자에 집중
- 대응: cap을 ±30%로 강화, 앙상블 가중치를 0.08로 축소하여 비현실적 값의 영향 제한

실험일: 2026-03-25
"""

import time

import dartlab
from dartlab.engines.analysis.analyst.priceImplied import reverseImpliedGrowth
from dartlab.engines.common.finance.extract import getTTM

STOCKS = [
    ("005930", "삼성전자", 1170e12),   # 시가총액 수동 (장 마감 후 null 대비)
    ("005380", "현대차", 46e12),
    ("000660", "SK하이닉스", 120e12),
]

WACC_RANGE = [7.0, 8.0, 9.0, 10.0, 11.0, 12.0]
TG_RANGE = [1.0, 2.0, 3.0]


def run():
    print("=" * 70)
    print("  priceImplied 센시티비티 (TV 수정 후)")
    print("=" * 70)

    for code, name, mktCap in STOCKS:
        print(f"\n{'─'*70}")
        print(f"  {name} ({code}) — 시가총액 {mktCap/1e12:.0f}조")
        print(f"{'─'*70}")

        t0 = time.time()
        c = dartlab.Company(code)
        tsRaw = c.finance.timeseries
        series = tsRaw[0] if isinstance(tsRaw, tuple) else tsRaw
        if not series:
            print(f"  ❌ timeseries 없음")
            continue

        rev = getTTM(series, "IS", "sales")
        opInc = getTTM(series, "IS", "operating_profit")
        margin = opInc / rev * 100 if opInc and rev and rev > 0 else 0
        print(f"  TTM 매출: {rev/1e12:.1f}조, 영업이익률: {margin:.1f}%")
        print(f"  로드: {time.time()-t0:.1f}s")

        # 센시티비티 테이블
        header = f"  {'WACC':>6s}"
        for tg in TG_RANGE:
            header += f"  tG={tg:.0f}%"
        print(f"\n{header}")
        print(f"  {'─'*40}")

        capCount = 0
        totalCells = 0

        for wacc in WACC_RANGE:
            row = f"  {wacc:5.0f}%"
            for tg in TG_RANGE:
                result = reverseImpliedGrowth(
                    series, mktCap, wacc=wacc, terminalGrowth=tg, horizon=3,
                )
                totalCells += 1
                if result and result.impliedGrowthRate != 0.0:
                    g = result.impliedGrowthRate
                    capHit = "!" if result.warnings and "cap" in str(result.warnings) else " "
                    if capHit == "!":
                        capCount += 1
                    row += f"  {g:+5.1f}%{capHit}"
                else:
                    row += f"   FAIL "
            print(row)

        print(f"\n  cap 적용: {capCount}/{totalCells}셀 ({capCount/totalCells*100:.0f}%)")

        # WACC 1%p 변화당 변동 확인 (tG=2% 기준)
        gList = []
        for wacc in WACC_RANGE:
            r = reverseImpliedGrowth(series, mktCap, wacc=wacc, terminalGrowth=2.0, horizon=3)
            if r and r.impliedGrowthRate != 0.0:
                gList.append(r.impliedGrowthRate)
        if len(gList) >= 2:
            maxDelta = max(abs(gList[i+1] - gList[i]) for i in range(len(gList)-1))
            print(f"  WACC 1%p당 최대 변동 (tG=2%): {maxDelta:.1f}%p")

        del c  # 메모리 해제


if __name__ == "__main__":
    run()
    print("\n실험 완료.")
