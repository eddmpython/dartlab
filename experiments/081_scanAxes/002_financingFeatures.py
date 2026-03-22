"""실험 ID: 081-002
실험명: financing feature extraction

목적:
- financing 축에 필요한 company-level feature를 설명 가능한 형태로 추출
- 최근 조달 여부, 조달 경로, 자금사용 근거/계획/불일치, 희석 신호를 하나의 테이블로 정리
- market-wide feature table과 company explainable row가 실제로 동시에 만들어지는지 검증

가설:
1. public/private usage만으로도 조달 경로를 실용적으로 분리할 수 있다
2. usage detail / plan / mismatch 플래그는 최근 조달 기업을 의미 있게 세분화한다
3. stockTotal 주식수 증가율을 결합하면 희석 신호가 더 설명 가능해진다

방법:
1. `001_financingCoverage.py`의 buildFinancingArtifacts()를 호출
2. company-level feature table에서 route, usageEvidence, planPresent, mismatch, dilutionSignal을 집계
3. 대표 경로(`대표경로`) 상위 분포와 sample row를 확인

결과 (실험 후 작성):
- 1,634사 feature table 구축
- feature flag 분포:
  - 사용근거 1,159사
  - 사용계획 634사
  - 사용불일치 694사
  - 희석신호 1,291사
  - 주식수증가만으로 추가 포착 52사
- 조달 경로 분포:
  - 사모 628 / 혼합 340 / 증자전용 338 / 공모 295 / 주식수증가전용 33
- 대표 경로 Top5:
  - 회사채 146 / 유상증자 126 / 전환사채 119 / 교환사채 42 / 제3자배정 유상증자 30
- sample explainable row:
  - 000040 KR모터스: 혼합, 사용근거=True, 사용불일치=True, 희석신호=True, 주식수증가율 -10.16%

결론:
- 가설1 채택: route가 공모/사모/혼합/증자전용/주식수증가전용으로 분리되어 시장 표가 바로 나온다
- 가설2 채택: usage detail / mismatch 플래그만으로도 1,159사 / 694사를 구분할 수 있어 해석층이 생긴다
- 가설3 채택: capitalChange만으로 설명되지 않는 +5% 주식수 증가 후보 52사가 추가된다
- feature extraction 단계는 financing 축 후보의 핵심 설명변수를 안정적으로 제공한다

실험일: 2026-03-20
"""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

import polars as pl

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))


def _loadCoverageModule():
    path = Path(__file__).with_name("001_financingCoverage.py")
    spec = importlib.util.spec_from_file_location("scan_axes_financing_coverage", path)
    if spec is None or spec.loader is None:
        raise RuntimeError("001_financingCoverage.py 로드 실패")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


if __name__ == "__main__":
    coverage = _loadCoverageModule()
    artifacts = coverage.buildFinancingArtifacts()
    features: pl.DataFrame = artifacts["features"]

    routeSummary = (
        features.group_by("조달경로")
        .agg(pl.len().alias("companies"))
        .sort("companies", descending=True)
    )
    routeHints = (
        features.filter(pl.col("대표경로") != "")
        .group_by("대표경로")
        .agg(pl.len().alias("companies"))
        .sort("companies", descending=True)
        .head(10)
    )

    print("=== financing features ===")
    print(routeSummary)
    print()
    print(
        f"usageEvidence={features.filter(pl.col('사용근거')).height} "
        f"planPresent={features.filter(pl.col('사용계획')).height} "
        f"mismatch={features.filter(pl.col('사용불일치')).height} "
        f"dilution={features.filter(pl.col('희석신호')).height}"
    )
    print()
    print(routeHints)
    print()
    print("sample row")
    print(features.filter(pl.col("종목코드") == "000040").head(1))
