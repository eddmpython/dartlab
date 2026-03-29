"""매크로 시나리오 타입, 업종 감응도, 노이즈 설정.

순수 데이터 + 룩업 함수. 외부 의존성 없음.
analysis/ 계층이 아닌 core/ 계층 소속.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional


# ======================================================
# Layer 1: 거시경제 시나리오
# ======================================================


@dataclass
class MacroScenario:
    """거시경제 시나리오 정의."""

    name: str
    label: str
    gdpGrowth: list[float]  # 3년 GDP 성장률 (%)
    interestRate: list[float]  # 3년 기준금리 (%)
    krwUsd: list[float]  # 3년 환율
    cpi: list[float]  # 3년 CPI (%)
    description: str = ""

    def __repr__(self) -> str:
        lines = [f"[{self.label}]"]
        lines.append(f"  GDP: {' -> '.join(f'{g:+.1f}%' for g in self.gdpGrowth)}")
        lines.append(f"  금리: {' -> '.join(f'{r:.1f}%' for r in self.interestRate)}")
        lines.append(f"  환율: {' -> '.join(f'{x:,.0f}' for x in self.krwUsd)}")
        if self.description:
            lines.append(f"  설명: {self.description}")
        return "\n".join(lines)


# -- 한국 기준 사전 정의 시나리오 --

BASELINE_RATE = 2.5  # 현재 BOK 기준금리
BASELINE_FX = 1470  # 현재 KRW/USD

PRESET_SCENARIOS_KR: dict[str, MacroScenario] = {
    "baseline": MacroScenario(
        "baseline",
        "기준 시나리오",
        gdpGrowth=[1.5, 2.0, 2.2],
        interestRate=[2.5, 2.5, 2.5],
        krwUsd=[1470, 1470, 1470],
        cpi=[2.2, 2.1, 2.0],
        description="현재 추세 유지",
    ),
    "adverse": MacroScenario(
        "adverse",
        "경기침체",
        gdpGrowth=[-3.0, -1.0, 0.5],
        interestRate=[1.0, 1.5, 2.0],
        krwUsd=[1600, 1580, 1550],
        cpi=[1.2, 1.5, 2.0],
        description="CCAR 스타일 심각한 경기침체 + 원화 약세",
    ),
    "china_slowdown": MacroScenario(
        "china_slowdown",
        "중국 경기둔화",
        gdpGrowth=[-1.5, -0.5, 1.0],
        interestRate=[1.5, 1.5, 2.0],
        krwUsd=[1550, 1520, 1480],
        cpi=[1.8, 1.9, 2.0],
        description="중국 수요 감소 -> 한국 수출 타격",
    ),
    "rate_hike": MacroScenario(
        "rate_hike",
        "금리 인상",
        gdpGrowth=[1.0, 1.5, 2.0],
        interestRate=[3.5, 4.0, 4.0],
        krwUsd=[1400, 1380, 1400],
        cpi=[3.0, 2.8, 2.5],
        description="인플레이션 대응 긴축 + 원화 강세",
    ),
    "semiconductor_down": MacroScenario(
        "semiconductor_down",
        "반도체 불황",
        gdpGrowth=[-2.0, -0.5, 1.5],
        interestRate=[2.0, 2.0, 2.5],
        krwUsd=[1550, 1520, 1500],
        cpi=[1.5, 1.8, 2.0],
        description="DRAM/NAND 가격 급락 + 글로벌 수요 감소",
    ),
}

# -- US 기준 사전 정의 시나리오 --

PRESET_SCENARIOS_US: dict[str, MacroScenario] = {
    "baseline": MacroScenario(
        "baseline",
        "Baseline",
        gdpGrowth=[2.0, 2.2, 2.3],
        interestRate=[5.0, 4.5, 4.0],
        krwUsd=[1.0, 1.0, 1.0],  # USD/USD = 1 (placeholder)
        cpi=[2.5, 2.3, 2.0],
        description="Current trend maintained",
    ),
    "adverse": MacroScenario(
        "adverse",
        "Recession",
        gdpGrowth=[-2.5, -0.5, 1.0],
        interestRate=[3.0, 2.5, 3.0],
        krwUsd=[1.0, 1.0, 1.0],
        cpi=[1.0, 1.5, 2.0],
        description="CCAR-style severe recession",
    ),
    "rate_hike": MacroScenario(
        "rate_hike",
        "Fed Tightening",
        gdpGrowth=[1.0, 1.5, 2.0],
        interestRate=[6.0, 6.5, 6.0],
        krwUsd=[1.0, 1.0, 1.0],
        cpi=[3.5, 3.0, 2.5],
        description="Persistent inflation -> aggressive Fed tightening",
    ),
    "rate_cut": MacroScenario(
        "rate_cut",
        "Fed Easing",
        gdpGrowth=[2.5, 3.0, 2.8],
        interestRate=[4.0, 3.5, 3.0],
        krwUsd=[1.0, 1.0, 1.0],
        cpi=[2.0, 2.0, 2.0],
        description="Soft landing -> aggressive rate cuts",
    ),
    "tech_downturn": MacroScenario(
        "tech_downturn",
        "Tech Downturn",
        gdpGrowth=[-1.0, 0.5, 2.0],
        interestRate=[4.5, 4.0, 4.0],
        krwUsd=[1.0, 1.0, 1.0],
        cpi=[2.0, 2.0, 2.0],
        description="Tech sector correction + AI capex pullback",
    ),
}

# 시장별 시나리오 선택
PRESET_SCENARIOS = PRESET_SCENARIOS_KR  # 기본값 (하위호환)


def getPresetScenarios(market: str = "KR") -> dict[str, MacroScenario]:
    """시장별 사전 정의 시나리오 반환."""
    if market == "US":
        return PRESET_SCENARIOS_US
    return PRESET_SCENARIOS_KR


# ======================================================
# Layer 2: 업종별 거시경제 감응도
# ======================================================


@dataclass
class SectorElasticity:
    """업종별 거시경제 감응도."""

    revenueToGdp: float  # GDP 1%p 변화 -> 매출 변화 (배수, beta)
    revenueToFx: float  # 환율 10% 약세 -> 매출 변화 (%)
    marginToGdp: float  # GDP 1%p 변화 -> 마진 변화 (bps)
    nimToRate: float  # 금리 100bps 변화 -> NIM 변화 (bps, 금융업만)
    cyclicality: str  # "high" | "moderate" | "low" | "defensive"

    def __repr__(self) -> str:
        return f"b(GDP)={self.revenueToGdp:.1f}, b(FX)={self.revenueToFx:.1f}, {self.cyclicality}"


SECTOR_ELASTICITY: dict[str, SectorElasticity] = {
    # 한국 (WICS 분류)
    "반도체": SectorElasticity(1.8, 0.8, 50, 0, "high"),
    "자동차": SectorElasticity(1.3, 0.6, 30, 0, "high"),
    "화학": SectorElasticity(1.2, 0.4, 25, 0, "high"),
    "철강": SectorElasticity(1.4, 0.3, 30, 0, "high"),
    "건설": SectorElasticity(1.5, 0.1, 40, 0, "high"),
    "금융/은행": SectorElasticity(1.0, 0.1, 20, 15, "moderate"),
    "금융/보험": SectorElasticity(0.8, 0.1, 15, 10, "moderate"),
    "금융/증권": SectorElasticity(1.5, 0.2, 40, 5, "high"),
    "IT/소프트웨어": SectorElasticity(1.0, 0.3, 20, 0, "moderate"),
    "통신": SectorElasticity(0.4, 0.05, 10, 0, "defensive"),
    "유통": SectorElasticity(0.8, 0.1, 15, 0, "moderate"),
    "식품": SectorElasticity(0.3, 0.05, 5, 0, "defensive"),
    "제약/바이오": SectorElasticity(0.5, 0.2, 10, 0, "low"),
    "전력/에너지": SectorElasticity(0.3, 0.15, 10, 0, "defensive"),
    "섬유/의류": SectorElasticity(0.9, 0.3, 20, 0, "moderate"),
    "전자/하드웨어": SectorElasticity(1.3, 0.5, 30, 0, "high"),
    "디스플레이": SectorElasticity(1.5, 0.6, 40, 0, "high"),
    "에너지/자원": SectorElasticity(1.0, 0.3, 25, 0, "high"),
    "산업재": SectorElasticity(1.2, 0.2, 25, 0, "moderate"),
    "조선": SectorElasticity(1.5, 0.3, 35, 0, "high"),
    "미디어/엔터": SectorElasticity(0.8, 0.1, 20, 0, "moderate"),
    "게임": SectorElasticity(0.6, 0.2, 15, 0, "moderate"),
    "부동산": SectorElasticity(1.0, 0.1, 20, 10, "moderate"),
    # US (GICS-like 분류)
    "Technology": SectorElasticity(1.5, 0.3, 40, 0, "high"),
    "Semiconductors": SectorElasticity(1.8, 0.5, 50, 0, "high"),
    "Healthcare": SectorElasticity(0.4, 0.1, 10, 0, "defensive"),
    "Financials": SectorElasticity(1.2, 0.1, 25, 12, "moderate"),
    "Consumer Discretionary": SectorElasticity(1.3, 0.2, 30, 0, "high"),
    "Consumer Staples": SectorElasticity(0.3, 0.05, 5, 0, "defensive"),
    "Energy": SectorElasticity(1.0, 0.3, 25, 0, "high"),
    "Industrials": SectorElasticity(1.2, 0.2, 25, 0, "moderate"),
    "Materials": SectorElasticity(1.3, 0.3, 30, 0, "high"),
    "Utilities": SectorElasticity(0.2, 0.05, 5, 0, "defensive"),
    "Communication Services": SectorElasticity(0.8, 0.1, 20, 0, "moderate"),
    "Real Estate": SectorElasticity(1.0, 0.1, 20, 10, "moderate"),
}

DEFAULT_ELASTICITY = SectorElasticity(0.8, 0.2, 15, 0, "moderate")


def getElasticity(sectorKey: Optional[str]) -> SectorElasticity:
    """업종 키로 감응도 조회."""
    if sectorKey is None:
        return DEFAULT_ELASTICITY
    return SECTOR_ELASTICITY.get(sectorKey, DEFAULT_ELASTICITY)


# ======================================================
# MC 노이즈 설정 -- 기업 규모별 sigma 차등
# ======================================================


NOISE_CONFIG: dict[str, dict[str, float]] = {
    "growth": {"baseSigma": 1.5, "Small": 1.5, "Mid": 1.0, "Large": 0.8},
    "margin": {"baseSigma": 2.5, "Small": 1.3, "Mid": 1.0, "Large": 0.9},
    "wacc": {"baseSigma": 0.8, "Small": 1.5, "Mid": 1.0, "Large": 0.7},
    "capex": {"baseSigma": 1.0, "Small": 1.2, "Mid": 1.0, "Large": 0.9},
    "tax": {"baseSigma": 1.0, "Small": 1.0, "Mid": 1.0, "Large": 1.0},
}


def getNoiseSigma(variable: str, sizeClass: str = "Mid") -> float:
    """변수별 x 규모별 noise sigma 반환."""
    cfg = NOISE_CONFIG.get(variable, {"baseSigma": 1.0})
    base = cfg["baseSigma"]
    mult = cfg.get(sizeClass, 1.0)
    return base * mult
