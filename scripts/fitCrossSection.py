"""횡단면/패널 회귀 모델 적합 — scan 데이터 → 모델 캐시.

calcPeerPrediction이 실작동하려면 이 스크립트로 모델을 적합해야 한다.
적합된 모델은 ~/.dartlab/models/ 에 JSON으로 저장된다.

사용법::

    uv run python scripts/fitCrossSection.py              # 최신 연도 적합
    uv run python scripts/fitCrossSection.py --year 2024  # 특정 연도
    uv run python scripts/fitCrossSection.py --panel      # 패널 모델도 적합
"""

from __future__ import annotations

import argparse
import gc
import math
import sys
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

import dartlab
from dartlab.analysis.valuation.crossRegression import (
    CompanyFeatures,
    fitCrossSection,
    fitPanel,
    saveModel,
    savePanelModel,
)


def _collectFeatures(year: int) -> list[CompanyFeatures]:
    """scan 데이터에서 전종목 피처를 수집한다."""
    from dartlab.scan import Scan

    scan = Scan()
    features: list[CompanyFeatures] = []

    # scan ratio에서 핵심 비율 수집
    ratioNames = [
        "per", "pbr", "operatingMargin", "debtRatio",
        "revenueGrowth", "roe", "totalAssetTurnover",
    ]

    # 각 ratio를 DataFrame으로 로드
    ratioData: dict[str, dict[str, float]] = {}
    for name in ratioNames:
        try:
            result = scan("ratio", name)
            if result is not None and hasattr(result, "df"):
                df = result.df
                codeCol = "stockCode" if "stockCode" in df.columns else df.columns[0]
                # 최신 값 추출
                periodCols = [c for c in df.columns if c not in (codeCol, "companyName", "종목코드", "회사명")]
                if not periodCols:
                    continue
                latestCol = periodCols[0]  # 최신 먼저 정렬 가정
                for row in df.iter_rows(named=True):
                    code = str(row.get(codeCol, ""))
                    val = row.get(latestCol)
                    if code and val is not None:
                        ratioData.setdefault(code, {})[name] = float(val)
        except (ValueError, TypeError, AttributeError) as e:
            print(f"  [WARN] ratio '{name}' 로드 실패: {e}")

    # sector 정보 수집
    sectorData: dict[str, str] = {}
    try:
        listing = dartlab.listing()
        if listing is not None:
            for row in listing.iter_rows(named=True):
                code = str(row.get("stockCode", ""))
                sector = row.get("sector", "") or row.get("industryGroup", "") or ""
                if code and sector:
                    sectorData[code] = sector
    except (AttributeError, TypeError):
        pass

    # CompanyFeatures 조립
    for code, ratios in ratioData.items():
        revGrowth = ratios.get("revenueGrowth")
        per = ratios.get("per")
        pbr = ratios.get("pbr")
        opMargin = ratios.get("operatingMargin")
        debtRatio = ratios.get("debtRatio")

        # 필수 필드 체크
        if revGrowth is None or per is None or pbr is None:
            continue
        if opMargin is None or debtRatio is None:
            continue

        # 이상치 필터 (극단적 값 제거)
        if abs(revGrowth) > 200 or abs(per) > 500 or pbr < 0 or pbr > 50:
            continue

        # lnMarketCap — 없으면 skip
        # 간단히 PBR * 자본총계로 추정하거나, 0으로 대체
        lnMc = math.log(max(abs(pbr) * 1e9, 1))  # 대략적 추정

        features.append(CompanyFeatures(
            stockCode=code,
            year=year,
            sector=sectorData.get(code, ""),
            revenueGrowth=revGrowth,
            per=per,
            pbr=pbr,
            lnMarketCap=lnMc,
            operatingMargin=opMargin or 0,
            capexRatio=0,  # scan에서 직접 제공하지 않으면 0
            debtRatio=debtRatio or 0,
            foreignHoldingRatio=0,  # scan에서 직접 제공하지 않으면 0
            revenueGrowthLag=0,  # 전년 데이터 없으면 0
        ))

    return features


def main():
    parser = argparse.ArgumentParser(description="횡단면/패널 회귀 모델 적합")
    parser.add_argument("--year", type=int, default=datetime.now().year - 1, help="적합 연도 (기본: 전년)")
    parser.add_argument("--panel", action="store_true", help="패널 모델도 적합")
    args = parser.parse_args()

    year = args.year
    print(f"[1/3] {year}년 피처 수집 중...")
    features = _collectFeatures(year)
    print(f"       {len(features)}개 기업 피처 수집 완료")

    if len(features) < 30:
        print(f"[ERROR] 관측치 {len(features)}개 — 최소 30개 필요. scan 데이터를 먼저 다운로드하세요.")
        sys.exit(1)

    # 횡단면 모델 적합
    print(f"[2/3] 횡단면 회귀 적합 중 ({len(features)} obs)...")
    csModel = fitCrossSection(features)
    if csModel is None:
        print("[ERROR] 횡단면 모델 적합 실패")
        sys.exit(1)

    path = saveModel(csModel)
    print(f"       R² = {csModel.rSquared:.4f}, adj R² = {csModel.adjRSquared:.4f}")
    print(f"       저장: {path}")

    # 패널 모델 (선택적)
    if args.panel:
        print(f"[3/3] 패널 회귀 적합 중...")
        # 패널은 여러 연도 데이터 필요 — 현재는 단일 연도로 시도
        panelModel = fitPanel(features, minObs=30, minYears=1)
        if panelModel:
            panelPath = savePanelModel(panelModel)
            print(f"       Panel R² = {panelModel.rSquared:.4f}, {panelModel.nFirms} firms")
            print(f"       저장: {panelPath}")
        else:
            print("       [WARN] 패널 모델 적합 실패 (데이터 부족)")
    else:
        print("[3/3] 패널 모델 생략 (--panel 옵션으로 활성화)")

    gc.collect()
    print("\n완료.")


if __name__ == "__main__":
    main()
