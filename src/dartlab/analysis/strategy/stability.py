"""2-3 안정성 분석 -- 레버리지, 이자보상, 부실 판별."""

from __future__ import annotations

_MAX_YEARS = 5


def _getRatioSeries(company) -> tuple[dict, list[str]] | None:
    """ratioSeries를 안전하게 가져온다."""
    try:
        result = company.finance.ratioSeries
        if result is None:
            return None
        return result
    except (ValueError, KeyError, AttributeError):
        return None


def _buildTimeline(data: dict, field: str, years: list[str]) -> list[dict]:
    """시계열 데이터를 [{period, value}, ...] 형태로 변환."""
    vals = data.get("RATIO", {}).get(field, [])
    n = min(len(vals), len(years), _MAX_YEARS)
    if n == 0:
        return []
    return [
        {"period": years[i], "value": vals[i]}
        for i in range(len(years) - n, len(years))
    ]


def calcLeverageTrend(company) -> dict | None:
    """부채비율, 차입금의존도 시계열."""
    result = _getRatioSeries(company)
    if result is None:
        return None

    data, years = result
    debtRatio = _buildTimeline(data, "debtRatio", years)
    netDebtRatio = _buildTimeline(data, "netDebtRatio", years)
    equityRatio = _buildTimeline(data, "equityRatio", years)

    if not debtRatio:
        return None

    return {
        "debtRatio": debtRatio,
        "netDebtRatio": netDebtRatio,
        "equityRatio": equityRatio,
    }


def calcCoverageTrend(company) -> dict | None:
    """이자보상배율 시계열."""
    result = _getRatioSeries(company)
    if result is None:
        return None

    data, years = result
    coverage = _buildTimeline(data, "interestCoverage", years)

    if not coverage:
        return None

    return {"interestCoverage": coverage}


def calcDistressScore(company) -> dict | None:
    """Altman Z-Score 시계열 + 종합 등급."""
    result = _getRatioSeries(company)
    if result is None:
        return None

    data, years = result
    zScore = _buildTimeline(data, "altmanZScore", years)

    if not zScore:
        return None

    # 최신 Z-Score 기반 등급
    latest = next((v["value"] for v in reversed(zScore) if v["value"] is not None), None)
    if latest is None:
        zone = "판별 불가"
    elif latest > 2.99:
        zone = "안전 구간"
    elif latest > 1.81:
        zone = "회색 구간"
    else:
        zone = "위험 구간"

    return {"altmanZScore": zScore, "latestScore": latest, "zone": zone}


def calcStabilityFlags(company) -> list[str]:
    """안정성 경고/기회 플래그."""
    flags: list[str] = []
    result = _getRatioSeries(company)
    if result is None:
        return flags

    data, _years = result

    # 부채비율
    dr = data.get("RATIO", {}).get("debtRatio", [])
    latestDr = next((v for v in reversed(dr) if v is not None), None)
    if latestDr is not None:
        if latestDr > 200:
            flags.append(f"부채비율 {latestDr:.0f}% -- 재무 위험")
        elif latestDr < 50:
            flags.append(f"부채비율 {latestDr:.0f}% -- 매우 안정")

    # 이자보상배율
    ic = data.get("RATIO", {}).get("interestCoverage", [])
    latestIc = next((v for v in reversed(ic) if v is not None), None)
    if latestIc is not None:
        if latestIc < 1:
            flags.append(f"이자보상배율 {latestIc:.1f}배 -- 이자 지급 불능 위험")
        elif latestIc < 3:
            flags.append(f"이자보상배율 {latestIc:.1f}배 -- 이자 부담 과다")

    # Altman Z-Score
    z = data.get("RATIO", {}).get("altmanZScore", [])
    latestZ = next((v for v in reversed(z) if v is not None), None)
    if latestZ is not None and latestZ < 1.81:
        flags.append(f"Altman Z-Score {latestZ:.2f} -- 부실 위험 구간")

    return flags
