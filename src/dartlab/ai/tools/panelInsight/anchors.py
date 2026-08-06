"""수치를 판단으로 바꾸는 기준선.

"영업이익률 13.1%" 도 "부채비율 29.9%" 도 그 자체로 좋고 나쁨을 말하지 않는다. 같은
업종 회사들이 어디에 있는지, 그리고 이 판단이 뒤집히려면 무엇이 얼마나 움직여야 하는지를
알아야 판단이 된다. 둘 다 모델이 손으로 하기에는 비싼 계산이라 우리가 해서 건넨다.
"""

from __future__ import annotations

from typing import Any

from .values import _formatAmount, _numeric, _pick, _seriesByKey, _withDerivedEquity


def _paceNote(distance: float, step: float, direction: str, unit: str) -> str:
    """남은 거리를 최근 한 기 변화폭으로 나눈다. 산술이지 전망이 아니라고 못 박는다.

    방향을 문장에 적는다. 내려가는 지표에 "+" 를 붙이면 정확히 반대로 읽힌다.
    """
    if step <= 0 or distance <= 0:
        return ""
    return (
        f" 최근 한 기 {direction} 폭 {step:.1f}%p가 이어지면 {distance / step:.0f} {unit} 뒤입니다"
        f"(산술이며 전망이 아닙니다)."
    )


def _debtTripwire(
    indexed: dict[str, dict[str, Any]], periods: list[str], position: dict[str, Any] | None, unit: str
) -> list[str]:
    """부채비율이 업종 중앙값에 닿으려면 부채가 얼마나 늘어야 하는지 적는다."""
    liabilities = indexed.get("total_liabilities")
    equity = _pick(indexed, ("total_stockholders_equity", "total_equity"))
    distribution = (position or {}).get("debtRatioDistribution")
    if liabilities is None or equity is None or not isinstance(distribution, dict):
        return []
    median = distribution.get("median")
    if not isinstance(median, (int, float)):
        return []
    latest = periods[0]
    debtNow = _numeric(liabilities.get("values"), latest)
    equityNow = _numeric(equity.get("values"), latest)
    if debtNow is None or not equityNow:
        return []
    ratioNow = debtNow / equityNow * 100
    target = float(median)
    gap = (target / 100) * equityNow - debtNow
    if gap <= 0:
        return [
            f"부채비율 {ratioNow:.1f}%는 이미 업종 중앙값 {target:.1f}% 위입니다. "
            f"중앙값으로 돌아가려면 자본이 그대로일 때 부채가 {_formatAmount(-gap).lstrip('+')} 줄어야 합니다."
        ]
    note = (
        f"부채비율이 업종 중앙값 {target:.1f}%에 닿으려면 자본이 그대로일 때 부채가 지금보다 "
        f"{_formatAmount(gap).lstrip('+')} 늘어야 합니다(현재 {ratioNow:.1f}%)."
    )
    if len(periods) >= 2:
        debtPrior = _numeric(liabilities.get("values"), periods[1])
        equityPrior = _numeric(equity.get("values"), periods[1])
        if debtPrior is not None and equityPrior:
            note += _paceNote(target - ratioNow, ratioNow - debtPrior / equityPrior * 100, "상승", unit)
    return [note]


def _liquidityTripwire(indexed: dict[str, dict[str, Any]], periods: list[str], unit: str) -> list[str]:
    """유동부채가 얼마나 더 늘면 유동자산으로 못 덮는지 적는다. 100%는 정의상 경계다."""
    assets = indexed.get("current_assets")
    liabilities = indexed.get("current_liabilities")
    if assets is None or liabilities is None:
        return []
    latest = periods[0]
    assetsNow = _numeric(assets.get("values"), latest)
    liabilitiesNow = _numeric(liabilities.get("values"), latest)
    if assetsNow is None or not liabilitiesNow:
        return []
    ratioNow = assetsNow / liabilitiesNow * 100
    if ratioNow <= 100:
        return [f"유동비율 {ratioNow:.1f}%로 유동자산이 이미 유동부채에 못 미칩니다."]
    note = (
        f"유동부채가 지금보다 {_formatAmount(assetsNow - liabilitiesNow).lstrip('+')} 늘면 "
        f"유동자산으로 덮지 못합니다(유동비율 100%). 현재 {ratioNow:.1f}%입니다."
    )
    if len(periods) >= 2:
        assetsPrior = _numeric(assets.get("values"), periods[1])
        liabilitiesPrior = _numeric(liabilities.get("values"), periods[1])
        if assetsPrior is not None and liabilitiesPrior:
            note += _paceNote(ratioNow - 100, assetsPrior / liabilitiesPrior * 100 - ratioNow, "하락", unit)
    return [note]


def balanceTripwires(summary: dict[str, Any], position: dict[str, Any] | None) -> list[str]:
    """재무 건전성 판단이 뒤집히는 지점을 산술로 적는다.

    실측(2026-08-06): 업종 기준을 붙여 주니 답변이 "29.9%는 업종 하위 28%라 낮은 편" 까지
    갔는데, 정작 "이 판단이 틀리려면 무엇이 일어나야 하나" 는 사라졌다. 재료가 늘면서
    마무리 규율이 밀려난 것이다. 반증 조건이 비싼 이유는 모델이 그 산술을 손으로 해야
    하기 때문이다. 현금흐름에서 통한 방법을 그대로 쓴다. 산술을 우리가 해서 건넨다.

    가정을 지어내지 않는다. 쓰는 것은 당기 재무상태표 수치와 이미 계산된 업종 중앙값,
    그리고 유동비율 100%라는 정의상 경계뿐이다.

    Args:
        summary: `Company.panel` tool 결과의 summary. 재무상태표가 아니면 빈 목록이다.
        position: `getSectorPosition` 결과. 없으면 유동성 임계만 적는다.

    Returns:
        list[str]: 사람이 읽는 한 줄 노트 목록.

    Example:
        `notes = balanceTripwires(summary, position)`
    """
    periods = [str(p) for p in (summary.get("periods") or [])]
    timeseries = [row for row in (summary.get("timeseries") or []) if isinstance(row, dict)]
    if not periods or not timeseries:
        return []
    indexed = _withDerivedEquity(_seriesByKey(timeseries), periods)
    unit = "년" if summary.get("projection") == "annual" else "분기"
    return _debtTripwire(indexed, periods, position, unit) + _liquidityTripwire(indexed, periods, unit)


# (표시 이름, 백분위 키, 분포 키, 높을수록 좋은가).
# 방향을 표에 박아 둔다. 부채비율은 낮을수록 안전한데 "상위 몇 %" 로 적으면 정반대로 읽힌다.
_SECTOR_AXES: tuple[tuple[str, str, str, bool], ...] = (
    ("영업이익률", "myOpmPercentile", "opmDistribution", True),
    ("ROE", "myRoePercentile", "roeDistribution", True),
    ("매출 성장률", "myCagrPercentile", "cagrDistribution", True),
    ("부채비율", "myDebtRatioPercentile", "debtRatioDistribution", False),
    ("유동비율", "myCurrentRatioPercentile", "currentRatioDistribution", True),
)


def sectorPositionLines(position: dict[str, Any] | None) -> list[str]:
    """수치를 판단으로 바꾸는 업종 내 위치를 문장으로 만든다.

    "영업이익률 13.1%" 는 그 자체로 좋고 나쁨을 말하지 않는다. 같은 업종 회사들이 어디에
    있는지를 알아야 판단이 된다. 분포와 백분위는 오래전부터 계산되고 있었지만 답변 표면에
    오지 않아 한 번도 쓰이지 않았다.

    표본이 작으면 백분위가 흔들린다. 몇 개 회사로 잰 값인지 함께 적어 과신을 막는다.

    Args:
        position: `getSectorPosition` 결과. 없으면 빈 목록이다.

    Returns:
        list[str]: 사람이 읽는 한 줄 노트 목록.

    Example:
        `lines = sectorPositionLines(position)`
    """
    if not isinstance(position, dict) or not position.get("peerCount"):
        return []
    industry = str(position.get("industryName") or position.get("industryId") or "동종 업종")
    peerCount = position.get("peerCount")
    lines: list[str] = []
    for label, percentileKey, distributionKey, higherIsBetter in _SECTOR_AXES:
        percentile = position.get(percentileKey)
        distribution = position.get(distributionKey)
        if not isinstance(percentile, (int, float)) or not isinstance(distribution, dict):
            continue
        median = distribution.get("median")
        sampled = distribution.get("n") or peerCount
        if higherIsBetter:
            parts = [f"{label} 업종 상위 {100 - float(percentile):.0f}%"]
            boundary, boundaryLabel = distribution.get("p90"), "상위 10% 경계"
        else:
            # 낮은 쪽에 있을수록 안전하다는 뜻을 문장 안에 넣는다. 숫자만 주면 뒤집혀 읽힌다.
            parts = [f"{label} 업종 하위 {float(percentile):.0f}% (낮을수록 안전)"]
            boundary, boundaryLabel = distribution.get("p10"), "가장 낮은 10% 경계"
        if isinstance(median, (int, float)):
            parts.append(f"중앙값 {float(median):.1f}%")
        if isinstance(boundary, (int, float)):
            parts.append(f"{boundaryLabel} {float(boundary):.1f}%")
        lines.append(f"- {', '.join(parts)} ({industry} {sampled}사 기준).")
    return lines


def contextMarkdown(
    dcrBadge: dict[str, Any] | None,
    industryBadge: dict[str, Any] | None,
    sectorPosition: dict[str, Any] | None = None,
    summary: dict[str, Any] | None = None,
) -> str:
    """이미 계산돼 붙어 있는 신용 등급과 산업 위치를 답변 표면으로 끌어올린다.

    두 뱃지는 오래전부터 tool 결과에 실려 있었지만 payload 안에만 있어서 실제 답변에는
    한 번도 쓰이지 않았다. 모델이 읽고 재사용하는 것은 markdown 본문이다. 계산이 이미
    끝난 것을 옮겨 적기만 하므로 비용이 없고, 수치 하나에 판단 기준이 생긴다.

    Args:
        dcrBadge: 신용 스코어카드 요약. 없으면 건너뛴다.
        industryBadge: 산업 분류와 국면과 동종 후보. 없으면 건너뛴다.

    Returns:
        str: 붙일 것이 없으면 빈 문자열이다.

    Example:
        `block = contextMarkdown(data.get("dcrBadge"), data.get("industryBadge"))`
    """
    lines: list[str] = []
    if isinstance(dcrBadge, dict) and dcrBadge.get("grade"):
        parts = [f"신용 {dcrBadge.get('grade')}"]
        if dcrBadge.get("outlook"):
            parts.append(f"전망 {dcrBadge['outlook']}")
        pd = dcrBadge.get("pdEstimate")
        if isinstance(pd, (int, float)):
            parts.append(f"1년 부도확률 {float(pd):.2f}%")
        if dcrBadge.get("investmentGrade") is not None:
            parts.append("투자등급" if dcrBadge["investmentGrade"] else "투기등급")
        lines.append(f"- {', '.join(parts)}.")
    if isinstance(industryBadge, dict) and industryBadge.get("industryName"):
        parts = [str(industryBadge["industryName"])]
        if industryBadge.get("stageName"):
            parts.append(str(industryBadge["stageName"]))
        if industryBadge.get("phase") and industryBadge["phase"] != "unknown":
            parts.append(f"국면 {industryBadge['phase']}")
        peers = [
            f"{peer.get('corpName')}({peer.get('stockCode')})"
            for peer in (industryBadge.get("peers") or [])
            if isinstance(peer, dict) and peer.get("corpName")
        ][:3]
        line = f"- 산업 {', '.join(parts)}."
        if peers:
            line += f" 같은 산업 비교 후보: {', '.join(peers)}."
        lines.append(line)
    lines.extend(sectorPositionLines(sectorPosition))
    tripwires = balanceTripwires(summary or {}, sectorPosition)
    if not lines and not tripwires:
        return ""
    block = "## 회사 위치\n" + "\n".join(lines) + "\n" if lines else ""
    if tripwires:
        block += "\n## 판단이 뒤집히는 지점\n" + "\n".join(f"- {note}" for note in tripwires) + "\n"
    return block
