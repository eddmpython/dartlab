"""업종별 신용등급 기준표.

KIS/KR/NICE + Moody's/S&P 공개 방법론을 종합하여
업종 대분류별 핵심 재무지표의 등급 구간을 정의한다.

등급 구간은 Moody's 선형 보간 방식(linear interpolation)으로
연속적 점수(0-100)를 산출한다. 값이 클수록 위험(100=D, 0=AAA).

각 지표별 방향:
- lower_is_better=True: 값이 낮을수록 좋다 (예: Debt/EBITDA)
- lower_is_better=False: 값이 높을수록 좋다 (예: ICR, 유동비율)
"""

from __future__ import annotations

from dartlab.core.sector.types import IndustryGroup, Sector

# ── 등급 구간 정의 ──
#
# 각 지표는 (breakpoint, grade_score) 리스트.
# breakpoint = 지표값, grade_score = 0-100 위험점수.
# 선형 보간으로 연속 점수 산출.
#
# lower_is_better=True:  작은 값 = 안전 (Debt/EBITDA, 부채비율)
# lower_is_better=False: 큰 값 = 안전 (ICR, 유동비율, FFO/Debt)


def _defaultThresholds() -> dict:
    """기본(제조업) 기준표. 미분류 업종 fallback."""
    return {
        # ── 채무상환능력 ──
        "ebitda_interest_coverage": {
            "lower_is_better": False,
            "breakpoints": [
                (12.0, 0),
                (8.5, 5),
                (6.5, 10),
                (5.0, 18),
                (3.5, 28),
                (2.0, 42),
                (1.0, 62),
                (0.5, 78),
                (0.0, 95),
            ],
        },
        "debt_to_ebitda": {
            "lower_is_better": True,
            "breakpoints": [
                (0.0, 0),
                (0.5, 3),
                (1.0, 8),
                (1.5, 15),
                (2.5, 25),
                (3.5, 38),
                (5.0, 58),
                (7.0, 75),
                (10.0, 90),
            ],
        },
        "ffo_to_debt": {
            "lower_is_better": False,
            "breakpoints": [
                (60.0, 0),
                (45.0, 5),
                (35.0, 12),
                (25.0, 20),
                (15.0, 35),
                (10.0, 50),
                (5.0, 68),
                (0.0, 85),
            ],
        },
        "focf_to_debt": {
            "lower_is_better": False,
            "breakpoints": [
                (40.0, 0),
                (25.0, 8),
                (15.0, 18),
                (10.0, 28),
                (5.0, 42),
                (0.0, 60),
                (-10.0, 80),
                (-20.0, 95),
            ],
        },
        # ── 레버리지 ──
        "debt_ratio": {
            "lower_is_better": True,
            "breakpoints": [
                (0.0, 0),
                (30.0, 2),
                (50.0, 5),
                (80.0, 10),
                (120.0, 18),
                (180.0, 30),
                (250.0, 48),
                (350.0, 68),
                (500.0, 85),
                (800.0, 95),
            ],
        },
        "borrowing_dependency": {
            "lower_is_better": True,
            "breakpoints": [
                (0.0, 0),
                (5.0, 3),
                (10.0, 8),
                (20.0, 18),
                (30.0, 30),
                (40.0, 48),
                (50.0, 65),
                (60.0, 80),
            ],
        },
        "net_debt_to_ebitda": {
            "lower_is_better": True,
            "breakpoints": [
                (-2.0, 0),
                (0.0, 3),
                (1.0, 10),
                (2.0, 18),
                (3.0, 28),
                (4.0, 42),
                (6.0, 60),
                (8.0, 78),
                (10.0, 90),
            ],
        },
        # ── 유동성 ──
        "current_ratio": {
            "lower_is_better": False,
            "breakpoints": [
                (300.0, 0),
                (200.0, 5),
                (150.0, 12),
                (120.0, 20),
                (100.0, 32),
                (80.0, 48),
                (50.0, 68),
                (30.0, 85),
            ],
        },
        "cash_ratio": {
            "lower_is_better": False,
            "breakpoints": [
                (50.0, 0),
                (30.0, 8),
                (20.0, 18),
                (10.0, 32),
                (5.0, 50),
                (2.0, 70),
                (0.0, 88),
            ],
        },
        "short_term_debt_ratio": {
            "lower_is_better": True,
            "breakpoints": [
                (0.0, 0),
                (10.0, 5),
                (20.0, 12),
                (30.0, 22),
                (40.0, 35),
                (50.0, 50),
                (70.0, 72),
                (90.0, 90),
            ],
        },
    }


def _utilitiesThresholds() -> dict:
    """유틸리티 업종 — 높은 부채 허용, 안정 현금흐름, 공기업 특성.

    한전: 유동비율 ~60%, 부채비율 300%+는 공기업 구조상 정상.
    """
    base = _defaultThresholds()
    # 부채비율 기준 완화
    base["debt_ratio"]["breakpoints"] = [
        (0.0, 0),
        (50.0, 2),
        (100.0, 5),
        (150.0, 10),
        (200.0, 18),
        (300.0, 30),
        (400.0, 48),
        (600.0, 68),
        (800.0, 85),
    ]
    # 유동비율 완화 (공기업/전력은 설비 자산 비중 높아 유동비율 낮음)
    base["current_ratio"]["breakpoints"] = [
        (200.0, 0), (150.0, 5), (120.0, 10), (100.0, 18),
        (80.0, 25), (60.0, 35), (40.0, 52), (20.0, 72),
    ]
    base["debt_to_ebitda"]["breakpoints"] = [
        (0.0, 0),
        (1.0, 3),
        (2.0, 8),
        (3.0, 15),
        (4.0, 25),
        (5.0, 38),
        (7.0, 58),
        (10.0, 75),
        (15.0, 90),
    ]
    base["net_debt_to_ebitda"]["breakpoints"] = [
        (-2.0, 0),
        (0.0, 3),
        (2.0, 10),
        (3.0, 18),
        (4.0, 28),
        (6.0, 42),
        (8.0, 60),
        (10.0, 78),
        (15.0, 90),
    ]
    return base


def _financialsThresholds() -> dict:
    """금융업 — 레버리지 구조 다름, 자본 적정성 중심."""
    base = _defaultThresholds()
    base["debt_ratio"]["breakpoints"] = [
        (0.0, 0),
        (100.0, 2),
        (200.0, 5),
        (400.0, 10),
        (600.0, 20),
        (800.0, 35),
        (1000.0, 55),
        (1500.0, 75),
        (2000.0, 90),
    ]
    # Debt/EBITDA는 금융업에서 의미 제한적 — 가중치 감소로 처리
    base["borrowing_dependency"]["breakpoints"] = [
        (0.0, 0),
        (20.0, 3),
        (40.0, 8),
        (60.0, 18),
        (70.0, 30),
        (80.0, 48),
        (90.0, 65),
        (95.0, 80),
    ]
    return base


def _constructionThresholds() -> dict:
    """건설업 — 프로젝트 기반, 현금흐름 불규칙."""
    base = _defaultThresholds()
    # 유동비율 기준 강화 (선수금/미청구공사 구조)
    base["current_ratio"]["breakpoints"] = [
        (350.0, 0),
        (250.0, 5),
        (180.0, 12),
        (150.0, 20),
        (120.0, 32),
        (100.0, 48),
        (70.0, 68),
        (40.0, 85),
    ]
    return base


def _itThresholds() -> dict:
    """IT — 무형자산 비중 높음, 현금 보유 중시."""
    base = _defaultThresholds()
    # 부채비율 기준 강화 (유형자산 적어 담보력 약함)
    base["debt_ratio"]["breakpoints"] = [
        (0.0, 0),
        (20.0, 2),
        (40.0, 5),
        (60.0, 10),
        (100.0, 20),
        (150.0, 35),
        (200.0, 52),
        (300.0, 72),
        (500.0, 90),
    ]
    return base


# ── 업종 매핑 ──

_SECTOR_THRESHOLDS: dict[Sector, dict] = {
    Sector.ENERGY: _defaultThresholds(),
    Sector.MATERIALS: _defaultThresholds(),
    Sector.INDUSTRIALS: _defaultThresholds(),
    Sector.CONSUMER_DISC: _defaultThresholds(),
    Sector.CONSUMER_STAPLES: _defaultThresholds(),
    Sector.HEALTHCARE: _defaultThresholds(),
    Sector.FINANCIALS: _financialsThresholds(),
    Sector.IT: _itThresholds(),
    Sector.COMMUNICATION: _itThresholds(),
    Sector.UTILITIES: _utilitiesThresholds(),
    Sector.REAL_ESTATE: _utilitiesThresholds(),
    Sector.UNKNOWN: _defaultThresholds(),
}


def _energyThresholds() -> dict:
    """에너지 — 사이클 업종, 높은 부채/CAPEX 허용."""
    base = _defaultThresholds()
    base["debt_ratio"]["breakpoints"] = [
        (0.0, 0),
        (40.0, 2),
        (80.0, 5),
        (120.0, 10),
        (180.0, 18),
        (250.0, 30),
        (350.0, 48),
        (500.0, 68),
        (700.0, 85),
    ]
    base["debt_to_ebitda"]["breakpoints"] = [
        (0.0, 0),
        (0.5, 3),
        (1.5, 8),
        (2.5, 15),
        (3.5, 25),
        (5.0, 38),
        (7.0, 55),
        (10.0, 75),
        (15.0, 90),
    ]
    return base


def _shipbuildingThresholds() -> dict:
    """조선 — 극심한 사이클, 선수금 구조, 장기 프로젝트."""
    base = _constructionThresholds()
    # 부채비율 완화 (수주산업 특성)
    base["debt_ratio"]["breakpoints"] = [
        (0.0, 0),
        (50.0, 2),
        (100.0, 5),
        (200.0, 12),
        (300.0, 22),
        (400.0, 38),
        (600.0, 58),
        (800.0, 78),
        (1000.0, 90),
    ]
    return base


def _semiconductorThresholds() -> dict:
    """반도체 — 극심한 사이클, 대규모 CAPEX, 현금흐름 변동.

    삼성SDI D/EBITDA ~15x, SK하이닉스 CAPEX 사이클 ~5-10x.
    """
    base = _itThresholds()
    # D/EBITDA: 반도체 CAPEX 사이클 감안. 15x까지도 투자적격.
    base["debt_to_ebitda"]["breakpoints"] = [
        (0.0, 0),
        (1.0, 3),
        (2.0, 8),
        (4.0, 15),
        (6.0, 22),
        (10.0, 32),
        (15.0, 45),
        (20.0, 62),
        (30.0, 82),
    ]
    base["net_debt_to_ebitda"]["breakpoints"] = [
        (-5.0, 0),
        (0.0, 3),
        (2.0, 10),
        (4.0, 18),
        (6.0, 25),
        (10.0, 35),
        (15.0, 48),
        (20.0, 65),
        (30.0, 85),
    ]
    return base


def _autoThresholds() -> dict:
    """자동차 — 캡티브 금융 연결, 높은 부채비율 정상."""
    base = _defaultThresholds()
    base["debt_ratio"]["breakpoints"] = [
        (0.0, 0),
        (50.0, 2),
        (100.0, 5),
        (150.0, 10),
        (200.0, 18),
        (300.0, 28),
        (400.0, 42),
        (600.0, 62),
        (800.0, 82),
    ]
    base["debt_to_ebitda"]["breakpoints"] = [
        (0.0, 0),
        (1.0, 3),
        (2.0, 8),
        (3.0, 15),
        (5.0, 25),
        (8.0, 40),
        (12.0, 58),
        (20.0, 78),
        (30.0, 90),
    ]
    base["borrowing_dependency"]["breakpoints"] = [
        (0.0, 0),
        (10.0, 3),
        (20.0, 8),
        (30.0, 15),
        (40.0, 25),
        (50.0, 38),
        (60.0, 52),
        (70.0, 68),
        (80.0, 82),
    ]
    return base


def _airlineThresholds() -> dict:
    """항공/해운 — IFRS16 리스 부채, 높은 감가상각, 탑승률 민감."""
    base = _defaultThresholds()
    base["debt_ratio"]["breakpoints"] = [
        (0.0, 0), (50.0, 2), (100.0, 5), (150.0, 10),
        (200.0, 15), (300.0, 25), (400.0, 38),
        (500.0, 55), (700.0, 75),
    ]
    base["debt_to_ebitda"]["breakpoints"] = [
        (0.0, 0), (1.0, 3), (2.0, 8), (3.0, 15),
        (4.0, 22), (5.0, 32), (7.0, 48),
        (10.0, 65), (15.0, 85),
    ]
    base["net_debt_to_ebitda"]["breakpoints"] = [
        (0.0, 0), (1.0, 5), (2.0, 10), (3.0, 18),
        (5.0, 30), (7.0, 48), (10.0, 68), (15.0, 88),
    ]
    base["borrowing_dependency"]["breakpoints"] = [
        (0.0, 0), (10.0, 3), (20.0, 8), (30.0, 15),
        (40.0, 28), (50.0, 42), (60.0, 62), (70.0, 80),
    ]
    return base


def _holdingThresholds() -> dict:
    """지주사 — 지분법 자산/손익, 연결 부채 과대. 비영업자산 비중 높음."""
    base = _defaultThresholds()
    base["debt_ratio"]["breakpoints"] = [
        (0.0, 0), (50.0, 2), (100.0, 5), (150.0, 10),
        (200.0, 18), (300.0, 28), (400.0, 42),
        (600.0, 62), (800.0, 80),
    ]
    base["debt_to_ebitda"]["breakpoints"] = [
        (0.0, 0), (1.0, 3), (2.0, 8), (3.0, 15),
        (5.0, 25), (8.0, 40), (12.0, 58),
        (18.0, 75), (25.0, 90),
    ]
    base["net_debt_to_ebitda"]["breakpoints"] = [
        (0.0, 0), (1.0, 5), (3.0, 12), (5.0, 22),
        (8.0, 35), (12.0, 52), (18.0, 72), (25.0, 88),
    ]
    return base


def _metalsThresholds() -> dict:
    """비철금속/광업 — CAPEX 사이클, 원자재 가격 민감.

    고려아연 D/EBITDA ~8x, 현대제철 ~10x. 광업/철강 CAPEX 정상 범위.
    """
    base = _energyThresholds()
    base["debt_to_ebitda"]["breakpoints"] = [
        (0.0, 0), (1.0, 3), (2.0, 8), (3.0, 15),
        (5.0, 22), (8.0, 32), (12.0, 48),
        (18.0, 68), (25.0, 85),
    ]
    # 유동비율도 광업 특성 반영 (설비 자산 비중 높음)
    base["current_ratio"]["breakpoints"] = [
        (200.0, 0), (150.0, 5), (120.0, 12), (100.0, 20),
        (80.0, 30), (60.0, 42), (40.0, 62), (20.0, 82),
    ]
    return base


def financialTrackBThresholds() -> dict:
    """금융업 Track B 전용 기준표.

    D/EBITDA, FFO/Debt를 사용하지 않음.
    자기자본비율, ROA, NIM, 충당금 비율이 핵심.
    은행: 자기자본비율 7~15%, ROA 0.3~1.5%, NIM 1~3%.
    """
    return {
        "equity_ratio": {  # 금융지주 자기자본비율: 7~15% 정상, BIS 최저 8%
            "lower_is_better": False,
            "breakpoints": [
                (15.0, 0), (12.0, 3), (10.0, 8), (8.0, 15),
                (7.0, 25), (6.0, 38), (5.0, 55), (4.0, 75), (3.0, 90),
            ],
        },
        "roa": {  # 금융지주 ROA: 0.3~1.0%가 정상 범위
            "lower_is_better": False,
            "breakpoints": [
                (1.2, 0), (0.8, 5), (0.6, 12), (0.4, 22),
                (0.3, 32), (0.2, 45), (0.1, 62), (0.0, 80), (-0.3, 95),
            ],
        },
        "nim_proxy": {  # 이자수익/자산 (NIM 대리, 순마진 아닌 총이자수익 비율)
            "lower_is_better": False,
            "breakpoints": [
                (4.0, 0), (3.0, 5), (2.0, 12), (1.5, 22),
                (1.0, 35), (0.5, 52), (0.2, 72), (0.0, 90),
            ],
        },
        "provision_ratio": {
            "lower_is_better": True,
            "breakpoints": [
                (0.0, 0), (0.1, 5), (0.3, 12), (0.5, 25),
                (1.0, 42), (2.0, 65), (3.0, 85),
            ],
        },
        "cash_to_asset": {
            "lower_is_better": False,
            "breakpoints": [
                (20.0, 0), (15.0, 8), (10.0, 18), (5.0, 35),
                (3.0, 52), (1.0, 72), (0.0, 90),
            ],
        },
        "current_ratio": {
            "lower_is_better": False,
            "breakpoints": [
                (200.0, 0), (150.0, 10), (120.0, 20), (100.0, 35),
                (80.0, 52), (60.0, 68), (40.0, 85),
            ],
        },
    }


def _telecomThresholds() -> dict:
    """통신 — 높은 설비투자, 안정 현금흐름, 규제 산업."""
    base = _utilitiesThresholds()
    base["debt_to_ebitda"]["breakpoints"] = [
        (0.0, 0), (0.5, 2), (1.0, 5), (1.5, 10),
        (2.0, 15), (3.0, 25), (4.0, 38),
        (6.0, 55), (8.0, 75),
    ]
    return base


# ── IndustryGroup별 override ──

_INDUSTRY_THRESHOLDS: dict[IndustryGroup, dict] = {
    IndustryGroup.CONSTRUCTION: _constructionThresholds(),
    IndustryGroup.SHIPBUILDING: _shipbuildingThresholds(),
    IndustryGroup.SEMICONDUCTOR: _semiconductorThresholds(),
    IndustryGroup.AUTO: _autoThresholds(),
    IndustryGroup.BANK: _financialsThresholds(),
    IndustryGroup.INSURANCE: _financialsThresholds(),
    IndustryGroup.DIVERSIFIED_FINANCIALS: _financialsThresholds(),
    IndustryGroup.OIL_GAS: _energyThresholds(),
    IndustryGroup.CHEMICAL: _semiconductorThresholds(),  # 화학/배터리 = 반도체급 CAPEX 사이클
    IndustryGroup.ELECTRIC: _utilitiesThresholds(),
    IndustryGroup.GAS_UTILITY: _utilitiesThresholds(),
    IndustryGroup.AEROSPACE_DEFENSE: _airlineThresholds(),
    IndustryGroup.METALS: _metalsThresholds(),
    IndustryGroup.TELECOM: _telecomThresholds(),
}

_SECTOR_THRESHOLDS[Sector.ENERGY] = _energyThresholds()


def getThresholds(sector: Sector | None, industryGroup: IndustryGroup | None = None) -> dict:
    """업종별 기준표 반환.

    IndustryGroup override가 있으면 우선, 없으면 Sector 대분류 사용.
    """
    if industryGroup is not None and industryGroup in _INDUSTRY_THRESHOLDS:
        return _INDUSTRY_THRESHOLDS[industryGroup]
    if sector is None:
        return _defaultThresholds()
    return _SECTOR_THRESHOLDS.get(sector, _defaultThresholds())


def getSectorLabel(sector: Sector | None) -> str:
    """업종 라벨 반환."""
    if sector is None:
        return "일반"
    return sector.value
