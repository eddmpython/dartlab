"""
실험 ID: 053-002
실험명: 삼성전자 docs vs finance 심층 비교

목적:
- 단일 종목(005930)으로 docs/finance 값 차이의 원인 정밀 분석
- 단위(원/백만원/억원) 확인
- 연도 매핑 정확도 확인
- 핵심 계정별 비교 테이블 생성

방법:
1. finance buildAnnual → 연도별 핵심 계정 값
2. docs fsSummary → 연도별 계정 값
3. 동일 연도·계정 값을 나란히 출력하여 육안 비교
4. 비율(finance/docs) 계산으로 단위 추정

결과 (실험 후 작성):
- docs year N의 자산총계 값 = finance year N-1의 자산총계 값 (×1,000,000)
  docs 2025: 514,531,948 × 1M = finance 2024: 514,531,948,000,000
  docs 2024: 455,905,980 × 1M = finance 2023: 455,905,980,000,000
- docs fsSummary는 보고서 제출 연도를 year로 사용하고 전기(N-1) 값이 idx=0
- docs에 "당기순이익" 없음 → "연결총당기순이익"으로 표시 (매핑 미지원)

결론:
- docs year N = finance year N-1 (1년 시차 확인)
- 단위 × 1,000,000 확인 (삼성전자 기준)
- BS 계정은 정밀 일치, IS/CF는 docs에 항목이 적어 비교 제한적

실험일: 2026-03-10
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "src"))

CODE = "005930"

KEY_ACCOUNTS = [
    ("자산총계", "total_assets", "BS"),
    ("부채총계", "total_liabilities", "BS"),
    ("자본총계", "total_stockholders_equity", "BS"),
    ("유동자산", "current_assets", "BS"),
    ("비유동자산", "noncurrent_assets", "BS"),
    ("현금및현금성자산", "cash_and_cash_equivalents", "BS"),
    ("매출액", "sales", "IS"),
    ("영업이익", "operating_profit", "IS"),
    ("당기순이익", "net_profit", "IS"),
    ("매출원가", "cost_of_sales", "IS"),
    ("영업활동현금흐름", "operating_cashflow", "CF"),
]


def main():
    from dartlab.engines.dart.finance.pivot import buildAnnual
    from dartlab.engines.dart.finance.mapper import AccountMapper
    from dartlab.engines.dart.docs.finance.summary.pipeline import fsSummary

    mapper = AccountMapper.get()

    annual = buildAnnual(CODE)
    if annual is None:
        print("finance 데이터 없음")
        return

    aSeries, aYears = annual
    print(f"finance 연도: {aYears}")

    docResult = fsSummary(CODE, ifrsOnly=True, period="y")
    if docResult is None:
        print("docs 데이터 없음")
        return

    docsYears = sorted(docResult.yearAccounts.keys())
    print(f"docs 연도: {docsYears}")
    print()

    commonYears = [y for y in docsYears if y in aYears]
    print(f"공통 연도: {commonYears}")
    print()

    print("docs 단위 추정 (docs 자산총계 값):")
    for year in docsYears:
        ya = docResult.yearAccounts[year]
        for nm in ["자산총계", "자산 총계"]:
            if nm in ya.accounts:
                val = ya.accounts[nm][0] if ya.accounts[nm] else None
                print(f"  {year}: {nm} = {val:,.0f}" if val else f"  {year}: {nm} = None")
    print()

    print("finance 자산총계 값:")
    taVals = aSeries.get("BS", {}).get("total_assets", [])
    for i, year in enumerate(aYears):
        val = taVals[i] if i < len(taVals) else None
        print(f"  {year}: {val:,.0f}" if val else f"  {year}: None")
    print()

    print("=" * 100)
    print(f"{'계정명':<25} {'연도':>6} {'docs':>20} {'finance':>20} {'비율(f/d)':>12} {'판정':>8}")
    print("-" * 100)

    for year in commonYears[-5:]:
        ya = docResult.yearAccounts[year]
        yIdx = aYears.index(year)

        for docsNm, snakeId, sjDiv in KEY_ACCOUNTS:
            docsVal = None
            for candidate in [docsNm]:
                if candidate in ya.accounts:
                    vals = ya.accounts[candidate]
                    if vals:
                        docsVal = vals[0]
                    break

            if docsVal is None:
                snakeIdFromMapper = mapper.map("", docsNm)
                if snakeIdFromMapper:
                    for nm, amts in ya.accounts.items():
                        mapped = mapper.map("", nm)
                        if mapped == snakeId and amts:
                            docsVal = amts[0]
                            docsNm = nm
                            break

            finVals = aSeries.get(sjDiv, {}).get(snakeId, [])
            finVal = finVals[yIdx] if yIdx < len(finVals) and finVals[yIdx] is not None else None

            if docsVal is not None and finVal is not None and docsVal != 0:
                ratio = finVal / docsVal
                if abs(ratio - 1) < 0.05:
                    verdict = "일치"
                elif abs(ratio - 1e3) / 1e3 < 0.1:
                    verdict = "×1000"
                elif abs(ratio - 1e6) / 1e6 < 0.1:
                    verdict = "×1M"
                elif abs(ratio - 1e9) / 1e9 < 0.1:
                    verdict = "×1B"
                else:
                    verdict = f"×{ratio:.0f}"
                ratioStr = f"{ratio:,.1f}"
            else:
                ratioStr = "-"
                verdict = "N/A"

            dStr = f"{docsVal:,.0f}" if docsVal is not None else "None"
            fStr = f"{finVal:,.0f}" if finVal is not None else "None"
            print(f"{docsNm:<25} {year:>6} {dStr:>20} {fStr:>20} {ratioStr:>12} {verdict:>8}")
        print()

    print("\n[ docs 계정 목록 (2024년) ]")
    if "2024" in docResult.yearAccounts:
        ya = docResult.yearAccounts["2024"]
        for nm in ya.order[:30]:
            vals = ya.accounts[nm]
            v = vals[0] if vals else None
            mapped = mapper.map("", nm)
            vStr = f"{v:>18,.0f}" if v is not None else f"{'None':>18}"
            mStr = f"→ {mapped}" if mapped else "→ ?"
            print(f"  {nm:<35} {vStr}  {mStr}")


if __name__ == "__main__":
    main()
