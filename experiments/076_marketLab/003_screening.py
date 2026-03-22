"""실험 ID: 003
실험명: 조건부 스크리닝 엔진

목적:
- 다중 조건 필터로 시장에서 특정 유형의 기업 추출
- 가치주, 성장주, 배당주, 턴어라운드, 위험군 등 프리셋 정의
- 프리셋별 해당 기업 수와 대표 종목 확인

가설:
1. 10개 이상의 유용한 스크리닝 프리셋 정의 가능
2. 각 프리셋에 5개+ 기업이 매칭되어 실용적이다
3. 프리셋 간 중복이 적어 독립적인 유형 분류가 된다

방법:
1. 001의 market_ratios.parquet 로드
2. Polars filter 체인으로 스크리닝 함수 구현
3. 투자 스타일별 프리셋 정의 및 실행

결과 (실험 후 작성):
- 11개 프리셋 전부 5개+ 매칭 (가설2 충족)
- 프리셋별 매칭:
  - 우량 가치주: 231개 (8.7%) — ROE≥10, 부채≤100, OM≥5, 유동≥150
  - 고성장주: 95개 (3.6%) — ROE≥15, OM≥10, 매출≥1000억
  - 턴어라운드 후보: 176개 (6.6%) — ROE 음수(-30~0), 부채≤80, 유동≥150
  - 현금부자: 338개 (12.7%) — FCF양수, CF마진≥10, 부채≤60
  - 고위험 고부채: 226개 (8.5%) — 부채≥200, 이자보상<3
  - 자본잠식 우려: 46개 (1.7%) — 자기자본비율<20, ROE음수
  - 초소형 고수익: 21개 (0.8%) — 자산100~1000억, ROE≥15, OM≥10
  - 대형 안정주: 120개 (4.5%) — 자산≥1조, 부채≤150, ROE≥5
  - 저평가 후보: 212개 (8.0%) — ROE≥8, OM≥5, 부채≤80, 자산<5000억
  - IT 고성장: 83개 (3.1%) — IT섹터, ROE≥10, OM≥5
  - 건강관리 흑자전환: 121개 (4.5%) — 건강관리섹터, 흑자
- 프리셋 간 중복: 우량가치주-저평가 151개(높음), 우량가치주-현금부자 121개, 턴어라운드-고위험 0개(독립)
- 고위험-자본잠식 36개 중복(자연스러운 겹침)

결론:
- 채택: 11개 프리셋 모두 실용적 (가설1,2 충족)
- 가설3(독립성) 부분 충족: 우량/현금부자/저평가는 겹치나, 턴어라운드/고위험/자본잠식은 독립적
- 향후: revenueGrowth 추가 시 성장주/턴어라운드 프리셋 정밀화 가능

실험일: 2026-03-20
"""

from __future__ import annotations

import sys
from pathlib import Path

import polars as pl

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "src"))

DATA_DIR = Path(__file__).parent / "data"


def loadSnapshot() -> pl.DataFrame:
    return pl.read_parquet(str(DATA_DIR / "market_ratios.parquet"))


def screen(df: pl.DataFrame, conditions: list[pl.Expr], name: str = "") -> pl.DataFrame:
    """다중 조건으로 스크리닝."""
    result = df
    for cond in conditions:
        result = result.filter(cond)
    return result


# ── 프리셋 정의 ──

PRESETS: dict[str, dict] = {
    "우량 가치주": {
        "description": "높은 수익성 + 낮은 부채 + 안정적",
        "conditions": [
            pl.col("roe") >= 10,
            pl.col("debtRatio") <= 100,
            pl.col("operatingMargin") >= 5,
            pl.col("currentRatio") >= 150,
        ],
    },
    "고성장주": {
        "description": "높은 수익성 + 높은 매출",
        "conditions": [
            pl.col("roe") >= 15,
            pl.col("operatingMargin") >= 10,
            pl.col("revenueTTM") >= 100_000_000_000,  # 매출 1000억+
        ],
    },
    "턴어라운드 후보": {
        "description": "적자 → 부채 낮아 회복 여지",
        "conditions": [
            pl.col("roe") < 0,
            pl.col("roe") > -30,
            pl.col("debtRatio") <= 80,
            pl.col("currentRatio") >= 150,
            pl.col("totalAssets") >= 50_000_000_000,  # 총자산 500억+
        ],
    },
    "현금부자": {
        "description": "FCF 풍부 + 낮은 부채",
        "conditions": [
            pl.col("fcf") > 0,
            pl.col("operatingCfMargin") >= 10,
            pl.col("debtRatio") <= 60,
        ],
    },
    "고위험 고부채": {
        "description": "높은 부채 + 이자 부담 큼",
        "conditions": [
            pl.col("debtRatio") >= 200,
            pl.col("interestCoverage").is_not_null(),
            pl.col("interestCoverage") < 3,
        ],
    },
    "자본잠식 우려": {
        "description": "자기자본비율 매우 낮음",
        "conditions": [
            pl.col("equityRatio") < 20,
            pl.col("roe") < 0,
        ],
    },
    "초소형 고수익": {
        "description": "총자산 작지만 수익성 높음",
        "conditions": [
            pl.col("totalAssets") < 100_000_000_000,  # 1000억 미만
            pl.col("totalAssets") > 10_000_000_000,    # 100억 이상
            pl.col("roe") >= 15,
            pl.col("operatingMargin") >= 10,
        ],
    },
    "대형 안정주": {
        "description": "대형주 + 안정적 재무",
        "conditions": [
            pl.col("totalAssets") >= 1_000_000_000_000,  # 1조+
            pl.col("debtRatio") <= 150,
            pl.col("roe") >= 5,
            pl.col("currentRatio") >= 100,
        ],
    },
    "저평가 후보": {
        "description": "수익성 있지만 낮은 인지도 섹터",
        "conditions": [
            pl.col("roe") >= 8,
            pl.col("operatingMargin") >= 5,
            pl.col("debtRatio") <= 80,
            pl.col("totalAssets") < 500_000_000_000,  # 5000억 미만
        ],
    },
    "IT 고성장": {
        "description": "IT 섹터 + 높은 수익성",
        "conditions": [
            pl.col("sector") == "IT",
            pl.col("roe") >= 10,
            pl.col("operatingMargin") >= 5,
        ],
    },
    "건강관리 흑자전환": {
        "description": "바이오/헬스 섹터 흑자 기업",
        "conditions": [
            pl.col("sector") == "건강관리",
            pl.col("roe") > 0,
            pl.col("operatingMargin") > 0,
        ],
    },
}


if __name__ == "__main__":
    df = loadSnapshot()
    total = df.shape[0]
    print(f"전체 종목: {total}\n")

    print("=" * 80)
    print(f"{'프리셋':20s} {'매칭':>6s} {'비율':>7s}  설명")
    print("=" * 80)

    presetResults = {}
    for name, preset in PRESETS.items():
        result = screen(df, preset["conditions"])
        count = result.shape[0]
        pct = count / total * 100
        presetResults[name] = result
        print(f"  {name:18s} {count:>5d}  {pct:>5.1f}%  {preset['description']}")

    # 상세 결과
    print(f"\n{'='*80}")
    print("상세 결과 (각 프리셋 Top 10)")
    print("=" * 80)

    displayCols = ["stockCode", "corpName", "sector", "roe", "debtRatio",
                   "operatingMargin", "totalAssets"]
    displayCols = [c for c in displayCols if c in df.columns]

    for name, result in presetResults.items():
        if result.shape[0] == 0:
            continue
        print(f"\n▶ {name} ({result.shape[0]}개)")

        # ROE 내림차순
        sortCol = "roe" if "roe" in result.columns else "totalAssets"
        shown = result.sort(sortCol, descending=True).head(10).select(displayCols)
        print(shown)

    # 프리셋 간 중복 분석
    print(f"\n{'='*80}")
    print("프리셋 간 중복 분석")
    print("=" * 80)

    presetNames = list(presetResults.keys())
    for i, n1 in enumerate(presetNames):
        codes1 = set(presetResults[n1]["stockCode"].to_list())
        if len(codes1) == 0:
            continue
        for n2 in presetNames[i+1:]:
            codes2 = set(presetResults[n2]["stockCode"].to_list())
            if len(codes2) == 0:
                continue
            overlap = codes1 & codes2
            if overlap:
                print(f"  {n1} ∩ {n2}: {len(overlap)}개 중복")
