"""forecastRevenue 앙상블 다년 경로 회귀 (순수 series 주입, network·Company 0).

회귀 앵커: `_revenueForecastCore.py` 앙상블 루프 본문이 for 밖으로 dedent 되어 있던
인덴테이션 버그(다년 예측이 1년차에서 flat, 이후 패딩 복제). 성장 시계열을 넣으면
projected 가 복리로 단조 증가해야 하고, 시나리오 base 경로도 flat 이 아니어야 한다.
"""

from __future__ import annotations

from dartlab.analysis.forecast.revenueForecast import forecastRevenue


def _growingSeries(start: float = 100.0, g: float = 0.10, n: int = 6) -> dict:
    """매출만 있는 최소 finance.timeseries (연 g 성장, 단조)."""
    sales = [round(start * (1 + g) ** i, 4) for i in range(n)]
    return {"IS": {"sales": sales}}


def test_multi_year_path_compounds_not_flat():
    series = _growingSeries(g=0.10, n=6)
    r = forecastRevenue(series, horizon=3)
    assert len(r.projected) == 3
    # 핵심 회귀: 다년 경로가 flat 이 아니라 복리로 단조 증가한다 (버그 시 3개 값이 동일)
    assert r.projected[0] < r.projected[1] < r.projected[2], r.projected
    # 각 스텝 성장률이 살아있다 (0 이 아님)
    assert r.projected[1] / r.projected[0] > 1.01
    assert r.projected[2] / r.projected[1] > 1.01


def test_scenario_base_path_not_flat():
    series = _growingSeries(g=0.12, n=6)
    r = forecastRevenue(series, horizon=3)
    base = (r.scenarios or {}).get("base")
    assert base and len(base) == 3
    # 시나리오 base 경로도 복리 반영 (flat 버그면 3개 동일)
    assert base[0] < base[2], base
    # bull > base > bear 순서 유지 (시나리오 붕괴 아님)
    bull = r.scenarios.get("bull")
    bear = r.scenarios.get("bear")
    if bull and bear:
        assert bear[-1] <= base[-1] <= bull[-1]


def test_override_growth_path_still_respected():
    """override(growthRates) 경로는 앙상블 루프를 건너뛰므로 재인덴트 영향 없음(BC)."""
    series = _growingSeries(g=0.05, n=6)
    r = forecastRevenue(series, horizon=3, overrides={"growthRates": [20.0, 20.0, 20.0]})
    assert len(r.projected) == 3
    assert r.projected[0] < r.projected[1] < r.projected[2]
