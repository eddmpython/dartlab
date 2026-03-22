"""소스 독립적 재무 유틸리티.

시계열 dict에서 값을 추출하고 비율을 계산한다.
DART, EDGAR 등 어떤 L1 소스의 결과든 동일한 dict 구조면 동작.
"""

from dartlab.engines.common.finance.extract import (
    getAnnualValues,
    getLatest,
    getRevenueGrowth3Y,
    getTTM,
)
from dartlab.engines.common.finance.forecast import (
    ForecastResult,
    ScenarioResult,
    SensitivityResult,
    forecast_all,
    forecast_metric,
    scenario_analysis,
    sensitivity_analysis,
)
from dartlab.engines.common.finance.prediction import (
    ContextSignals,
    adjust_probabilities,
    collect_signals,
    get_noise_sigma,
)
from dartlab.engines.common.finance.pricetarget import (
    PriceTargetResult,
    ScenarioPriceTarget,
    compute_price_target,
)
from dartlab.engines.common.finance.proforma import (
    HistoricalRatios,
    ProFormaResult,
    ProFormaYear,
    build_proforma,
    compute_company_wacc,
    extract_historical_ratios,
)
from dartlab.engines.common.finance.ratios import (
    RATIO_CATEGORIES,
    RatioResult,
    RatioSeriesResult,
    calcRatios,
    calcRatioSeries,
    toSeriesDict,
    yoy_pct,
)
from dartlab.engines.common.finance.simulation import (
    PRESET_SCENARIOS,
    MacroScenario,
    MonteCarloResult,
    SectorElasticity,
    SimulationResult,
    StressTestResult,
    monte_carlo_forecast,
    simulate_all_scenarios,
    simulate_scenario,
    stress_test,
)
from dartlab.engines.common.finance.valuation import (
    DCFResult,
    DDMResult,
    RelativeValuationResult,
    ValuationSummary,
    dcf_valuation,
    ddm_valuation,
    full_valuation,
    relative_valuation,
)

__all__ = [
    "getTTM",
    "getLatest",
    "getAnnualValues",
    "getRevenueGrowth3Y",
    "calcRatios",
    "calcRatioSeries",
    "toSeriesDict",
    "RATIO_CATEGORIES",
    "RatioResult",
    "RatioSeriesResult",
    "yoy_pct",
    # valuation
    "DCFResult",
    "DDMResult",
    "RelativeValuationResult",
    "ValuationSummary",
    "dcf_valuation",
    "ddm_valuation",
    "full_valuation",
    "relative_valuation",
    # forecast
    "ForecastResult",
    "ScenarioResult",
    "SensitivityResult",
    "forecast_all",
    "forecast_metric",
    "scenario_analysis",
    "sensitivity_analysis",
    # simulation
    "MacroScenario",
    "SectorElasticity",
    "SimulationResult",
    "MonteCarloResult",
    "StressTestResult",
    "PRESET_SCENARIOS",
    "simulate_scenario",
    "simulate_all_scenarios",
    "monte_carlo_forecast",
    "stress_test",
    # proforma
    "HistoricalRatios",
    "ProFormaYear",
    "ProFormaResult",
    "extract_historical_ratios",
    "compute_company_wacc",
    "build_proforma",
    # prediction (context signal fusion)
    "ContextSignals",
    "collect_signals",
    "adjust_probabilities",
    "get_noise_sigma",
    # price target
    "ScenarioPriceTarget",
    "PriceTargetResult",
    "compute_price_target",
]
