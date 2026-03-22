"""실험 ID: 081-004
실험명: financing classifier cross validation

목적:
- financing 초안이 기존 capital/debt 축에 비해 추가 설명력을 가지는지 검증
- promotion gate의 cross validation / explainability 조건을 점검
- 10개 수동 sample을 raw column으로 설명 가능한지 확인

가설:
1. capital의 `최근증자=False`만으로는 놓치던 financing evidence가 200사 이상 존재한다
2. capital `중립`과 debt `안전` 내부에서도 financing classifier가 유의미하게 분산된다
3. 분류별 2개씩 총 10개 sample은 raw column으로 100% 설명 가능하다

방법:
1. `001_financingCoverage.py`의 feature/classifier를 생성
2. 기존 `scan_capital(verbose=False)` / `scan_debt(verbose=False)`와 조인
3. capital/debt 교차표와 `최근증자=False + 사용근거=True` 건수를 집계
4. 분류별 2개씩 총 10개 explainable sample을 추출해 raw evidence를 확인

결과 (실험 후 작성):
- financing classifier 1,634사를 capital/debt와 교차 검증
- 추가 설명력:
  - capital의 `최근증자=False`인데 financing `사용근거=True`인 기업 328사
- capital `중립` 내부 분해:
  - 불일치주의형 173 / 희석주의형 111 / 사모집행형 108 / 공모집행형 29 / 혼합집행형 29
- debt `안전` 내부 분해:
  - 희석주의형 114 / 불일치주의형 113 / 공모집행형 38 / 사모집행형 34 / 혼합집행형 10
- debt risk 미결합(null): 85사
- 수동 explainability:
  - 분류별 2개씩 총 10개 sample 모두 `pay_de / se_nm / real_cptal_use_dtls_cn / dffrnc_occrrnc_resn / istc_totqy`로 설명 가능 (10/10)

결론:
- 가설1 채택: capital의 최근증자 flag만으로는 놓치는 financing evidence 328사가 확인됐다
- 가설2 채택: capital `중립`, debt `안전` 내부에서도 financing class가 다섯 갈래로 분산되어 추가 설명력이 존재한다
- 가설3 채택: 수동 sample 10/10 설명 가능으로 explainability gate를 충족했다
- financing 실험 트랙은 coverage, class balance, added value, explainability 네 조건을 모두 충족했다
- 따라서 anomaly 대체 트랙은 이번 배치에서 발동하지 않는다

실험일: 2026-03-20
"""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

import polars as pl

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))

from dartlab.engines.company.dart.scan.capital import scan_capital
from dartlab.engines.company.dart.scan.debt import scan_debt


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
    samples = coverage.buildExplainableSamples(classified, artifacts["evidenceMap"], perClass=2)

    capital = scan_capital(verbose=False)
    debt = scan_debt(verbose=False)

    capital = capital.rename(
        {
            capital.columns[0]: "종목코드",
            capital.columns[6]: "capital_최근증자",
            capital.columns[8]: "capital_분류",
        }
    )
    debt = debt.rename(
        {
            debt.columns[0]: "종목코드",
            debt.columns[7]: "debt_위험등급",
        }
    )

    joined = (
        classified.join(capital.select(["종목코드", "capital_최근증자", "capital_분류"]), on="종목코드", how="left")
        .join(debt.select(["종목코드", "debt_위험등급"]), on="종목코드", how="left")
    )

    capitalNeutral = (
        joined.filter(pl.col("capital_분류") == "중립")
        .group_by("분류초안")
        .agg(pl.len().alias("companies"))
        .sort("companies", descending=True)
    )
    debtSafe = (
        joined.filter(pl.col("debt_위험등급") == "안전")
        .group_by("분류초안")
        .agg(pl.len().alias("companies"))
        .sort("companies", descending=True)
    )

    print("=== financing cross validation ===")
    print(
        "recentFalseButUsageEvidence=",
        joined.filter((~pl.col("capital_최근증자")) & pl.col("사용근거")).height,
    )
    print()
    print("[capital 중립 split]")
    print(capitalNeutral)
    print()
    print("[debt 안전 split]")
    print(debtSafe)
    print()
    print(f"debtRiskNull={joined.filter(pl.col('debt_위험등급').is_null()).height}")
    print()
    print("[manual samples]")
    print(samples)
