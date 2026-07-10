"""예측신호(6-2) 축 unit 테스트 — 순수 로직, 데이터 로드 없음."""

from __future__ import annotations

import pytest

pytestmark = pytest.mark.unit


# ── import 테스트 ──


def test_predictionSignals_import():
    from dartlab.analysis.financial.predictionSignals import (
        calcAnnouncementTiming,
        calcDisclosureDelta,
        calcEarningsMomentum,
        calcEventImpact,
        calcInventoryDivergence,
        calcMacroRegression,
        calcMacroSensitivity,
        calcPeerPrediction,
        calcPredictionFlags,
        calcPredictionSynthesis,
        calcStructuralBreak,
        calcSupplyChainSignal,
    )

    assert callable(calcEarningsMomentum)
    assert callable(calcPeerPrediction)
    assert callable(calcStructuralBreak)
    assert callable(calcMacroSensitivity)
    assert callable(calcMacroRegression)
    assert callable(calcEventImpact)
    assert callable(calcDisclosureDelta)
    assert callable(calcInventoryDivergence)
    assert callable(calcAnnouncementTiming)
    assert callable(calcSupplyChainSignal)
    assert callable(calcPredictionSynthesis)
    assert callable(calcPredictionFlags)


# ── 레지스트리 등록 확인 ──


def test_axis_registered():
    from dartlab.analysis.financial import _ALIASES, _AXIS_REGISTRY

    assert "예측신호" in _AXIS_REGISTRY
    entry = _AXIS_REGISTRY["예측신호"]
    assert entry.partId == "6-2"
    assert len(entry.calcs) == 15

    # alias
    assert _ALIASES["prediction"] == "예측신호"
    assert _ALIASES["predictionSignals"] == "예측신호"
    assert _ALIASES["전망신호"] == "예측신호"


def test_axis_resolve():
    from dartlab.analysis.financial import _resolveAxis

    assert _resolveAxis("예측신호") == "예측신호"
    assert _resolveAxis("prediction") == "예측신호"
    assert _resolveAxis("전망신호") == "예측신호"


# ── 방향 점수 상수 ──


def test_direction_scores():
    from dartlab.analysis.financial.predictionSignals import _DIRECTION_SCORES

    assert _DIRECTION_SCORES["up"] == 1.0
    assert _DIRECTION_SCORES["down"] == -1.0
    assert _DIRECTION_SCORES["neutral"] == 0.0
    assert _DIRECTION_SCORES["stable"] == 0.0


# ── 매크로 민감도 테이블 ──


def test_sector_macro_map():
    from dartlab.analysis.financial.predictionSignals import _SECTOR_MACRO_MAP

    assert "high" in _SECTOR_MACRO_MAP
    assert "defensive" in _SECTOR_MACRO_MAP
    assert "moderate" in _SECTOR_MACRO_MAP

    # 각 항목에 필수 키가 있는지
    for cyclicality, drivers in _SECTOR_MACRO_MAP.items():
        for d in drivers:
            assert "indicator" in d
            assert "source" in d
            assert "direction" in d


# ── 헬퍼 함수 순수 테스트 ──


def test_avgGrowth():
    from dartlab.analysis.financial._signalsMacro import _avgGrowth

    assert _avgGrowth([100, 110, 121]) == pytest.approx(10.0, abs=0.5)
    assert _avgGrowth([100, 50]) == pytest.approx(-50.0, abs=0.1)
    assert _avgGrowth([100]) is None
    assert _avgGrowth([]) is None


def test_safe():
    from dartlab.core.utils.calc import safeDiv as _safe

    assert _safe(10, 5) == 2.0
    assert _safe(10, 0) is None
    assert _safe(0, 10) == 0.0


# ── forecast/prediction.py 브릿지 ──


def test_collectSignals_accepts_usePredictionAxis():
    """collectSignals가 usePredictionAxis 파라미터를 받는지 확인."""
    import inspect

    from dartlab.analysis.forecast.prediction import collectSignals

    sig = inspect.signature(collectSignals)
    assert "usePredictionAxis" in sig.parameters


def test_contextSignals_fields():
    """ContextSignals에 disclosure 관련 필드가 있는지 확인."""
    from dartlab.analysis.forecast.prediction import ContextSignals

    signals = ContextSignals()
    assert hasattr(signals, "disclosureTone")
    assert hasattr(signals, "disclosureChangeIntensity")
    assert hasattr(signals, "disclosureGrowthAdj")
    assert hasattr(signals, "disclosureConfidence")


# ── Prediction Space ──


def test_predictionSpace_import():
    from dartlab.analysis.forecast.predictionSpace import (
        getPredictionSpace,
    )

    assert callable(getPredictionSpace)


def test_axisState_dataclass():
    from dartlab.analysis.forecast.predictionSpace import AxisState

    ax = AxisState(name="test", label="테스트", level=0.5, direction="improving", momentum=0.3, confidence="high")
    assert ax.level == 0.5
    assert ax.direction == "improving"


def test_predictionSpace_impactOn():
    from dartlab.analysis.forecast.predictionSpace import AxisState, PredictionSpace

    space = PredictionSpace(
        axes={
            "businessCycle": AxisState("businessCycle", "경기축", 0.5, "improving", 0.3, "high"),
            "fxRate": AxisState("fxRate", "환율축", -0.3, "deteriorating", -0.2, "medium"),
        },
        timestamp="2026-03-30",
        dataFreshness="fresh",
    )
    impact = space.impactOn("반도체")
    assert "businessCycle" in impact
    assert "fxRate" in impact
    # 반도체: revenueToGdp=1.8, level=0.5 → 0.5*1.8*3.0=2.7
    assert impact["businessCycle"] == pytest.approx(2.7, abs=0.1)


def test_predictionSpace_summary():
    from dartlab.analysis.forecast.predictionSpace import AxisState, PredictionSpace

    space = PredictionSpace(
        axes={"businessCycle": AxisState("businessCycle", "경기축", 0.5, "improving", 0.3, "high")},
        timestamp="2026-03-30",
        dataFreshness="fresh",
    )
    s = space.summary()
    assert "axes" in s
    assert s["axes"]["businessCycle"]["state"] == "expansion"
    assert s["axes"]["businessCycle"]["level"] == 0.5


def test_normalize_functions():
    from dartlab.analysis.forecast.predictionSpace import (
        _clamp,
        _normalizeIndex,
        _normalizeZscore,
    )

    assert _clamp(2.0) == 1.0
    assert _clamp(-2.0) == -1.0
    assert _clamp(0.5) == 0.5

    # CLI=110 → (110-100)/20 = 0.5
    assert _normalizeIndex([110]) == pytest.approx(0.5, abs=0.01)
    # CLI=80 → (80-100)/20 = -1.0
    assert _normalizeIndex([80]) == pytest.approx(-1.0, abs=0.01)

    # zscore: 값이 부족하면 0
    assert _normalizeZscore([1, 2, 3]) == 0.0


def test_computeDirection():
    from dartlab.analysis.forecast.predictionSpace import _computeDirection

    # 상승 추세
    direction, momentum = _computeDirection([100, 102, 105])
    assert direction == "improving"
    assert momentum > 0

    # 하락 추세
    direction, momentum = _computeDirection([105, 102, 100])
    assert direction == "deteriorating"
    assert momentum < 0


# ── 관세청 customs 외생후보 연결 (productIndicators → _loadAdaptive greedy 풀) ──


def test_loadAdaptive_selects_customs_when_correlated(monkeypatch):
    """수출업종 회사는 customs HS 가 후보풀에 들어가 corr 최고면 greedy 선택된다.

    강제주입 아닌 corr-greedy 경로 — 합성 데이터로 customs(8542)만 매출과 완전상관,
    나머지 후보는 무상관 → top-3 에 customs 포함 확인. (분산형 자기보호의 이면 검증.)
    """
    import polars as pl

    import dartlab.gather.mapping.exogenousAxes as EA
    import dartlab.gather.mapping.productIndicators as PI
    import dartlab.gather.transforms.macro as MAC
    from dartlab.analysis.financial._signalsMacroSensitivity import _loadAdaptive

    periods = [f"{y}Q{q}" for y in range(2018, 2024) for q in range(1, 5)]  # 24 분기
    # 연도별 레벨(변동 있음) → YoY 가 변동 → 무상관 후보와 구분.
    levels = {2017: 100, 2018: 120, 2019: 110, 2020: 140, 2021: 130, 2022: 150, 2023: 145}
    rev = [(levels[int(c[:4])] - levels[int(c[:4]) - 1]) / abs(levels[int(c[:4]) - 1]) * 100 for c in periods]

    # 무상관 fred/ecos 후보 3 + customs 8542 매핑 (수출업종)
    monkeypatch.setattr(
        EA, "getExogenousSeriesIds", lambda stockCode=None: [("A", "ecos"), ("B", "fred"), ("C", "fred")]
    )
    monkeypatch.setattr(
        PI, "getProductIndicators", lambda code: [{"seriesId": "8542", "source": "customs", "label": "반도체"}]
    )
    monkeypatch.setattr(MAC, "loadMacroParquet", lambda sid, *, source: pl.DataFrame({"_sid": [sid], "value": [0.0]}))

    def fakeAlign(df, cols):
        sid = df["_sid"][0]
        if sid == "8542":  # customs = 연도 레벨 → YoY 가 rev 와 동일(완전상관)
            vals = [float(levels[int(c[:4])]) for c in cols]
        else:  # 무상관: 상수 → YoY 0
            vals = [100.0] * len(cols)
        return pl.DataFrame({"value": vals})

    monkeypatch.setattr(MAC, "alignToFinancialPeriods", fakeAlign)

    result = _loadAdaptive(rev, periods, stockCode="005930")
    assert result is not None
    assert "8542" in result["_usedIndicators"].values()  # customs 가 greedy 선택됨


def test_loadAdaptive_no_customs_for_nonexport(monkeypatch):
    """비수출업종(productIndicators 빈 list)은 customs 후보가 아예 없다 (자연 스코핑)."""
    import polars as pl

    import dartlab.gather.mapping.exogenousAxes as EA
    import dartlab.gather.mapping.productIndicators as PI
    import dartlab.gather.transforms.macro as MAC
    from dartlab.analysis.financial._signalsMacroSensitivity import _loadAdaptive

    periods = [f"{y}Q{q}" for y in range(2018, 2024) for q in range(1, 5)]
    rev = [float((i % 5) - 2) for i in range(len(periods))]

    monkeypatch.setattr(EA, "getExogenousSeriesIds", lambda stockCode=None: [("A", "ecos")])
    monkeypatch.setattr(PI, "getProductIndicators", lambda code: [])  # 서비스업 → 빈 매핑
    monkeypatch.setattr(MAC, "loadMacroParquet", lambda sid, *, source: pl.DataFrame({"value": [1.0]}))
    monkeypatch.setattr(MAC, "alignToFinancialPeriods", lambda df, cols: pl.DataFrame({"value": [1.0] * len(cols)}))

    result = _loadAdaptive(rev, periods, stockCode="035420")
    # customs 코드(숫자 HS)가 선택지표에 없어야 함
    if result is not None:
        assert not any(str(v).isdigit() and len(str(v)) <= 4 for v in result["_usedIndicators"].values())


# ── 02e Part 2 방법 C: 회귀 불가 시 섹터 prior 위계 폴백 ──


def test_sectorPriorFallback_returns_labeled_prior(monkeypatch):
    from dartlab.analysis.financial import _signalsMacroSensitivity as m

    monkeypatch.setattr(m, "_getSectorKey", lambda c: "IT")
    r = m._sectorPriorFallback(object(), "YoY 관측치 부족 (3 < 6)")
    assert r["evidenceLevel"] == "sectorPrior"
    assert r["fallbackReason"] == "YoY 관측치 부족 (3 < 6)"
    assert r["betas"] is None, "기업 고유 베타 부재 (섹터 평균이 고유 베타로 오독되면 안 됨)"
    assert r["rSquared"] == 0.0 and r["nObs"] == 0
    assert set(r["staticBetas"]) == {"gdp", "rate", "fx"}
    assert r["sectorKey"] == "IT"


def test_sectorPriorFallback_none_without_sector(monkeypatch):
    from dartlab.analysis.financial import _signalsMacroSensitivity as m

    monkeypatch.setattr(m, "_getSectorKey", lambda c: None)
    assert m._sectorPriorFallback(object(), "x") is None, "섹터 미해소면 기본 탄성치 날조 금지"


def test_sectorPriorFallback_fails_existing_numeric_gates(monkeypatch):
    """폴백 dict 는 기존 소비자 게이트(rSquared > 0.1 / > 0.3)를 통과하지 않는다 (회귀 0)."""
    from dartlab.analysis.financial import _signalsMacroSensitivity as m

    monkeypatch.setattr(m, "_getSectorKey", lambda c: "IT")
    r = m._sectorPriorFallback(object(), "x")
    assert not (r.get("rSquared", 0) > 0.1), "_predictionSynthesis:366 게이트"
    assert not (r["rSquared"] > 0.3), "_predictionSynthesis:643 게이트"
    assert r["confidence"] == "low"
