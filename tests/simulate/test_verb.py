"""Callable `simulate` preview: top-level `dartlab.simulate` + `Company.simulate` (L2.5).

Unit smoke (no Company load): the preview is importable from the Python package:
- `dartlab.simulate` resolves through the lazy `__getattr__` map and is callable.
- `simulate` is in `dartlab.__all__`. Skill OS / apiContract registration is a separate gate.
- `Company.simulate` exists on the DART Company class.

One realData test (serial) — `dartlab.simulate("005930", scenario="baseline")` returns a
SimulationResult with a populated revenuePath + dcfPerShare, and `Company("005930").simulate(
scenario="adverse")` yields a lower terminal revenue than baseline. The Company is released
with `del`.
"""

from __future__ import annotations

import pytest


# ──────────────────────────────────────────────────────────────────────
# unit — verb importable + registered in the lazy map / __all__
# ──────────────────────────────────────────────────────────────────────
@pytest.mark.unit
def test_simulate_verb_registered() -> None:
    import dartlab

    # Python export surface only. This does not prove Skill OS / apiContract registration.
    assert "simulate" in dartlab.__all__
    # `dartlab.simulate` is callable as the top-level verb even though `simulate` is also a
    # subpackage name — the callable-module patch (mirror of scan/macro) delegates to the verb.
    assert callable(dartlab.simulate)
    # registered in the lazy attr map pointing at the thin entry wrapper (the pre-load path).
    assert dartlab._LAZY_ATTRS["simulate"] == ("dartlab.simulate.entry", "simulate")
    # the thin entry wrapper is directly importable (the function the verb dispatches to).
    from dartlab.simulate.entry import simulate as _entryVerb

    assert callable(_entryVerb)


@pytest.mark.unit
def test_company_simulate_method_exists() -> None:
    from dartlab.providers.dart.company import Company

    assert callable(getattr(Company, "simulate", None))


@pytest.mark.unit
def test_company_simulate_rejects_invalid_scenario_before_lens_fanout(monkeypatch) -> None:
    from types import SimpleNamespace

    from dartlab.providers.dart.company import Company

    def unexpectedFanout(*args, **kwargs):
        raise AssertionError("lens fanout ran before scenario validation")

    monkeypatch.setattr("dartlab.story.lensProducts.collectLensProducts", unexpectedFanout)

    with pytest.raises(ValueError, match="scenario"):
        Company.simulate(SimpleNamespace(), scenario="unknown", horizon=3)


@pytest.mark.unit
def test_company_simulate_rejects_bad_user_assumptions_before_lens_fanout(monkeypatch) -> None:
    """잘못된 사용자 시나리오와 override 는 렌즈 수집 전에 실패하고, strategies 축은 override 를 거부한다."""
    from types import SimpleNamespace

    from dartlab.providers.dart.company import Company
    from dartlab.simulate.assumptions import AssumptionInputError

    def unexpectedFanout(*args, **kwargs):
        raise AssertionError("lens fanout ran before assumption validation")

    monkeypatch.setattr("dartlab.story.lensProducts.collectLensProducts", unexpectedFanout)

    with pytest.raises(AssumptionInputError, match="허용 범위"):
        Company.simulate(SimpleNamespace(), scenario={"name": "typo", "rate": [45.0, 5.0, 5.0]})
    with pytest.raises(AssumptionInputError, match="모르는"):
        Company.simulate(SimpleNamespace(), overrides={"wacc": 9.0})
    with pytest.raises(ValueError, match="override"):
        Company.simulate(SimpleNamespace(), "strategies", overrides={"baseWacc": 9.0})


@pytest.mark.unit
def test_simulate_guards_non_kr(monkeypatch: pytest.MonkeyPatch) -> None:
    """KR 외 시장(US → EDGAR)은 매크로 프리셋 부재로 ValueError (네트워크 없이 fake company)."""
    import dartlab
    from dartlab.simulate import entry as _entry

    class _FakeUsCompany:
        market = "US"
        stockCode = "AAPL"  # EDGAR mirrors ticker into stockCode — market is the discriminator.

    monkeypatch.setattr(dartlab, "Company", lambda code: _FakeUsCompany())
    with pytest.raises(ValueError, match="KR"):
        _entry.simulate("AAPL", scenario="baseline")


# ──────────────────────────────────────────────────────────────────────
# realData — top-level verb + Company method on one company (serial, del after)
# ──────────────────────────────────────────────────────────────────────
@pytest.mark.realData
@pytest.mark.serial
def test_realData_simulate_verb_005930() -> None:
    """005930: dartlab.simulate(baseline) populates paths/dcf; c.simulate(adverse) < baseline."""
    import dartlab
    from dartlab.simulate.run import SimulationResult

    baseline = dartlab.simulate("005930", scenario="baseline")
    if baseline.revenuePath is None or baseline.proformaYears == 0:
        pytest.skip("005930 finance series unavailable — realData skip environment")

    assert isinstance(baseline, SimulationResult)
    assert baseline.scenarioName == "baseline"
    assert len(baseline.revenuePath) == 3
    assert baseline.dcfPerShare is not None

    # Company.simulate mirrors the top-level verb; adverse terminal revenue < baseline.
    c = dartlab.Company("005930")
    try:
        adverse = c.simulate(scenario="adverse", horizon=3)
        assert isinstance(adverse, SimulationResult)
        assert adverse.revenuePath is not None
        assert adverse.revenuePath[-1] < baseline.revenuePath[-1]

        # 사용자 금리 충격은 매출을 그대로 두고 WACC 경로를 올려 주당 DCF 를 낮춘다.
        shock = c.simulate(scenario={"name": "rateShock", "rate": [5.0, 5.5, 5.5]}, horizon=3)
        assert (shock.scenarioKind, shock.scenarioBase) == ("user", "baseline")
        assert shock.macroPaths["rate"] == (5.0, 5.5, 5.5)
        assert shock.revenuePath == baseline.revenuePath
        assert all(user > base for user, base in zip(shock.waccPath, baseline.waccPath))
        assert shock.dcfPerShare < baseline.dcfPerShare
        overridden = c.simulate(overrides={"baseWacc": 12.0}, horizon=3)
        assert overridden.waccPath[0] == pytest.approx(12.0)
        # 렌즈 맥락 행은 id 가 없다. 사용자 행만 골라 본다.
        userRows = [(row["kind"], row["id"]) for row in overridden.assumptionLedger if row["source"] == "user"]
        assert userRows == [("driverOverride", "baseWacc")]
    finally:
        del c
