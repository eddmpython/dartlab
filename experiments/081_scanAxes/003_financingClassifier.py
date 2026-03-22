"""실험 ID: 081-003
실험명: financing classifier draft

목적:
- feature table을 실험용 financing 분류 초안으로 압축
- 단일 class 쏠림 여부를 확인해 promotion gate의 classifier 조건을 점검
- route/usage mismatch/dilution signal을 함께 쓰는 것이 실용적인지 본다

가설:
1. route만 쓰는 것보다 mismatch 우선 분류가 실제 해석에 더 유용하다
2. 단일 class 비중이 85% 미만으로 유지된다
3. 희석주의형이 public/private execution과 분리되어 별도 경고층을 만든다

방법:
1. `001_financingCoverage.py`의 feature table을 불러온다
2. 분류 우선순위:
   - 사용불일치 -> 불일치주의형
   - 혼합 route -> 혼합집행형
   - 공모 route -> 공모집행형
   - 사모 route -> 사모집행형
   - 그 외 희석신호 -> 희석주의형
3. class 분포와 sample row를 점검한다

결과 (실험 후 작성):
- 분류 초안 분포:
  - 불일치주의형 694
  - 희석주의형 371
  - 사모집행형 319
  - 공모집행형 139
  - 혼합집행형 111
- 최다 class 비중: 42.5% (694 / 1,634) -> gate 통과
- sample explainable row:
  - 000670 영풍: 희석주의형, public/private usage 없음, 최근증자=False, 주식수증가율 +937.35%

결론:
- 가설1 채택: mismatch를 최우선으로 올리면 실제 사용불일치 경고층 694사가 별도로 드러난다
- 가설2 채택: 최다 class 42.5%로 단일 class 쏠림 문제가 없다
- 가설3 채택: usage가 없는 희석 후보와 execution형 조달이 분리되어 축 해석이 더 명확해졌다
- classifier draft는 promotion gate의 class balance 조건을 충족한다

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
    classified: pl.DataFrame = coverage.buildFinancingClassifier(artifacts["features"])

    dist = classified.group_by("분류초안").agg(pl.len().alias("companies")).sort("companies", descending=True)
    topCount = dist["companies"][0] if not dist.is_empty() else 0
    share = round(topCount / classified.height * 100, 1) if classified.height else 0.0

    print("=== financing classifier ===")
    print(dist)
    print()
    print(f"topClassShare={share}%")
    print()
    print("sample row")
    print(classified.filter(pl.col("종목코드") == "000670").head(1))
