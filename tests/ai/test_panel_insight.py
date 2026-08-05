"""panel 응답에 실리는 판단 재료의 계약.

중개 제품은 답변을 직접 고쳐 쓸 수 없다. 답변 품질을 올리는 정공법은 건네주는 근거를
판단 가능한 형태로 만드는 것이다. 이 파일은 그 계산이 사실만 말하고 과장하지 않는지 고정한다.
"""

from __future__ import annotations

import pytest

from dartlab.ai.tools.panelInsight import (
    cashFlowPattern,
    contextMarkdown,
    derivedRows,
    insightMarkdown,
    observedRangeAnchors,
    positionNotes,
    profitBridge,
)

pytestmark = pytest.mark.unit


def _summary(**values: dict[str, float]) -> dict[str, object]:
    """기간 내림차순 timeseries summary 를 만든다. 실제 panel 결과와 같은 모양이다."""
    periods = ["2025FY", "2024FY", "2023FY"]
    labels = {
        "sales": "매출액",
        "cost_of_sales": "매출원가",
        "operating_profit": "영업이익",
        "net_income": "당기순이익",
    }
    timeseries = [
        {
            "snakeId": key,
            "item": labels.get(key, key),
            "values": series,
            "formatted": {period: f"{series[period] / 1e12:.1f}조원" for period in series},
        }
        for key, series in values.items()
    ]
    return {"periods": periods, "timeseries": timeseries, "projection": "annual"}


def testGrowthRateIsPercentNotPercentagePoint() -> None:
    """증감률은 부호 붙은 퍼센트다. 퍼센트끼리의 차이가 아니므로 퍼센트포인트가 아니다."""
    summary = _summary(sales={"2025FY": 110e12, "2024FY": 100e12, "2023FY": 50e12})

    rows = derivedRows(summary)
    growth = next(row for row in rows if "증감률" in row["label"])

    assert growth["cells"][0] == "+10.0%"
    assert "%p" not in growth["cells"][0]
    assert growth["cells"][-1] == "-", "가장 오래된 기간은 직전 기간이 없어 증감률을 낼 수 없다"


def testMarginsAreComputedAgainstSales() -> None:
    """매출 대비 비율은 손익계산서에서만 성립하고 매출을 분모로 쓴다."""
    summary = _summary(
        sales={"2025FY": 100e12, "2024FY": 100e12, "2023FY": 100e12},
        operating_profit={"2025FY": 13e12, "2024FY": 11e12, "2023FY": 2e12},
    )

    rows = derivedRows(summary)
    margin = next(row for row in rows if row["label"] == "영업이익률")

    assert margin["cells"] == ["13.0%", "11.0%", "2.0%"]


def testBaseEffectIsFlaggedWhenTroughIsFarBelowPeak() -> None:
    """저점이 기간 최고치에 크게 못 미치면 그 기준 증감률이 부풀려진다고 말한다.

    실측 배경: 영업이익 6.6조원에서 43.6조원으로 간 구간을 "5 배 성장" 으로만 읽으면
    사이클 저점을 구조적 성장으로 오해한다.
    """
    summary = _summary(operating_profit={"2025FY": 43.6e12, "2024FY": 32.7e12, "2023FY": 6.6e12})

    notes = positionNotes(summary)

    assert any("기저효과" in note for note in notes)
    assert any("2023FY" in note for note in notes)


def testSteadySeriesGetsNoBaseEffectWarning() -> None:
    """완만한 시계열에 기저효과 경고를 붙이지 않는다. 없는 문제를 만들면 신뢰를 잃는다."""
    summary = _summary(operating_profit={"2025FY": 11e12, "2024FY": 10e12, "2023FY": 9e12})

    notes = positionNotes(summary)

    assert not any("기저효과" in note for note in notes)


def testLossPeriodIsNotReportedAsMultiple() -> None:
    """적자 기간을 기준으로 한 증감률을 배수로 읽지 말라고 명시한다."""
    summary = _summary(operating_profit={"2025FY": 10e12, "2024FY": 5e12, "2023FY": -3e12})

    notes = positionNotes(summary)

    assert any("적자" in note for note in notes)


def testShortSeriesProducesNothing() -> None:
    """기간이 하나뿐이면 비교할 것이 없으므로 아무 것도 덧붙이지 않는다."""
    summary = {"periods": ["2025FY"], "timeseries": [{"snakeId": "sales", "item": "매출액", "values": {"2025FY": 1.0}}]}

    assert derivedRows(summary) == []
    assert positionNotes(summary) == []
    assert insightMarkdown(summary) == ""


def testMarkdownTableAlignsWithPeriodColumns() -> None:
    """파생 지표 표의 칸 수가 기간 수와 어긋나면 표가 깨진다."""
    summary = _summary(
        sales={"2025FY": 100e12, "2024FY": 90e12, "2023FY": 80e12},
        operating_profit={"2025FY": 13e12, "2024FY": 11e12, "2023FY": 2e12},
    )

    block = insightMarkdown(summary)
    tableLines = [line for line in block.splitlines() if line.startswith("| ")]

    assert tableLines, "파생 지표 표가 있어야 한다"
    widths = {line.count("|") for line in tableLines}
    assert len(widths) == 1, f"칸 수가 어긋난다: {widths}"


def testProfitBridgeSplitsChangeIntoVolumeAndMargin() -> None:
    """이익 변동을 매출 효과와 마진 효과로 쪼개고 둘의 합이 실제 변동과 정확히 맞는다.

    항등식이라 어긋나면 계산이 틀린 것이다. 근거 제품에서 합이 안 맞는 분해는 내보내면 안 된다.
    """
    summary = _summary(
        sales={"2025FY": 333.6e12, "2024FY": 300.9e12, "2023FY": 258.9e12},
        operating_profit={"2025FY": 43.6e12, "2024FY": 32.7e12, "2023FY": 6.6e12},
    )

    notes = profitBridge(summary)

    assert notes, "매출과 영업이익이 다 있으면 분해할 수 있어야 한다"
    salesNow, salesPrev = 333.6e12, 300.9e12
    profitNow, profitPrev = 43.6e12, 32.7e12
    volume = (salesNow - salesPrev) * (profitPrev / salesPrev)
    margin = (profitNow / salesNow - profitPrev / salesPrev) * salesNow
    assert abs((volume + margin) - (profitNow - profitPrev)) < 1e6, "두 기여분의 합이 실제 변동과 같아야 한다"
    assert any("몸통은" in note for note in notes)


def testProfitBridgeNeedsBothSalesAndProfit() -> None:
    """재무상태표처럼 매출이 없는 표에서는 분해를 시도하지 않는다."""
    summary = _summary(operating_profit={"2025FY": 10e12, "2024FY": 8e12, "2023FY": 6e12})

    assert profitBridge(summary) == []


def _statement(**values: dict[str, float]) -> dict[str, object]:
    """손익 외 표에도 쓰는 일반 summary. 라벨은 재무제표 매핑의 정본 이름을 따른다."""
    periods = ["2025FY", "2024FY", "2023FY"]
    labels = {
        "total_liabilities": "부채총계",
        "total_stockholders_equity": "자본총계",
        "total_assets": "자산총계",
        "current_assets": "유동자산",
        "current_liabilities": "유동부채",
        "cash_and_cash_equivalents": "현금및현금성자산",
        "cash_flows_from_operating_activities": "영업활동현금흐름",
        "cash_flows_from_investing_activities": "투자활동현금흐름",
        "cash_flows_from_financing_activities": "재무활동현금흐름",
        "purchase_of_property_plant_and_equipment": "유형자산의취득",
    }
    timeseries = [
        {
            "snakeId": key,
            "item": labels.get(key, key),
            "values": series,
            "formatted": {period: f"{series[period] / 1e12:.1f}조원" for period in series},
        }
        for key, series in values.items()
    ]
    return {"periods": periods, "timeseries": timeseries, "projection": "annual"}


def testBalanceSheetRatiosUseTheirOwnDenominators() -> None:
    """부채비율은 자본이, 자기자본비율은 자산이 분모다. 매출로 나누면 안 된다."""
    summary = _statement(
        total_liabilities={"2025FY": 50e12, "2024FY": 60e12, "2023FY": 70e12},
        total_stockholders_equity={"2025FY": 100e12, "2024FY": 100e12, "2023FY": 100e12},
        total_assets={"2025FY": 150e12, "2024FY": 160e12, "2023FY": 170e12},
    )

    rows = derivedRows(summary)
    debt = next(row for row in rows if row["label"] == "부채비율")

    assert debt["cells"] == ["50.0%", "60.0%", "70.0%"]


def testFreeCashFlowSubtractsCapexAsMagnitude() -> None:
    """설비투자 취득액은 양수로 보고되므로 절대값을 뺀다. 부호를 그대로 더하면 두 배가 된다."""
    summary = _statement(
        cash_flows_from_operating_activities={"2025FY": 60e12, "2024FY": 50e12, "2023FY": 40e12},
        purchase_of_property_plant_and_equipment={"2025FY": 45e12, "2024FY": 50e12, "2023FY": 55e12},
    )

    rows = derivedRows(summary)
    fcf = next(row for row in rows if "잉여현금흐름" in row["label"])

    assert fcf["cells"][0].startswith("+15.0")
    assert fcf["cells"][2].startswith("-15.0"), "영업 현금이 설비투자를 못 덮으면 음수여야 한다"


def testCashFlowSignPatternIsRead() -> None:
    """영업 양수, 투자 음수, 재무 음수는 성숙한 현금 창출 구조에서 흔한 조합이다."""
    summary = _statement(
        cash_flows_from_operating_activities={"2025FY": 60e12, "2024FY": 50e12, "2023FY": 40e12},
        cash_flows_from_investing_activities={"2025FY": -40e12, "2024FY": -35e12, "2023FY": -30e12},
        cash_flows_from_financing_activities={"2025FY": -15e12, "2024FY": -10e12, "2023FY": -5e12},
    )

    notes = cashFlowPattern(summary)

    assert notes, "세 흐름이 다 있으면 부호 조합을 읽어야 한다"
    assert any("성숙" in note for note in notes)


def testCashFlowPatternNeedsAllThreeFlows() -> None:
    """셋 중 하나라도 없으면 국면을 단정하지 않는다."""
    summary = _statement(cash_flows_from_operating_activities={"2025FY": 60e12, "2024FY": 50e12, "2023FY": 40e12})

    assert cashFlowPattern(summary) == []


def testUnknownSignPatternGetsFactsWithoutVerdict() -> None:
    """조합표에 없는 모양이면 수치만 적고 해석을 지어내지 않는다."""
    summary = _statement(
        cash_flows_from_operating_activities={"2025FY": 60e12, "2024FY": 1e12, "2023FY": 1e12},
        cash_flows_from_investing_activities={"2025FY": 10e12, "2024FY": 1e12, "2023FY": 1e12},
        cash_flows_from_financing_activities={"2025FY": 10e12, "2024FY": 1e12, "2023FY": 1e12},
    )

    notes = cashFlowPattern(summary)

    assert len(notes) == 1, "사실 한 줄만 남고 해석은 붙지 않아야 한다"


def testDownsideAnchorUsesObservedMarginNotInventedOne() -> None:
    """판단이 바뀌는 지점을 지어낸 가정이 아니라 실제 겪은 마진으로 만든다.

    답변에서 가장 자주 빠지는 것이 "이 판단이 틀리려면 무엇이 일어나야 하나" 다.
    임의 시나리오를 만들면 근거 제품이 아니게 되므로 관측된 값만 쓴다.
    """
    summary = _summary(
        sales={"2025FY": 333.6e12, "2024FY": 300.9e12, "2023FY": 258.9e12},
        operating_profit={"2025FY": 43.6e12, "2024FY": 32.7e12, "2023FY": 6.6e12},
    )

    notes = observedRangeAnchors(summary)

    assert notes, "3 개 기간이 있으면 하방 앵커를 낼 수 있어야 한다"
    assert "2023FY" in notes[0], "실제 최저를 겪은 기간을 지목해야 한다"
    assert "2.5%" in notes[0]
    assert "전망이 아닙니다" in notes[0], "산술임을 명시하지 않으면 예측으로 읽힌다"


def testDownsideAnchorIsSkippedWhenAlreadyAtTheLow() -> None:
    """지금이 이미 기간 최저면 더 낮은 관측치가 없으므로 하방 앵커를 만들지 않는다."""
    summary = _summary(
        sales={"2025FY": 100e12, "2024FY": 100e12, "2023FY": 100e12},
        operating_profit={"2025FY": 2e12, "2024FY": 11e12, "2023FY": 13e12},
    )

    notes = observedRangeAnchors(summary)

    assert not any("최저" in note for note in notes)


def testDownsideAnchorNeedsSalesAndProfit() -> None:
    """매출이 없는 표에서는 마진을 만들 수 없으므로 시도하지 않는다."""
    summary = _summary(operating_profit={"2025FY": 10e12, "2024FY": 8e12, "2023FY": 6e12})

    assert observedRangeAnchors(summary) == []


def testContextBlockSurfacesCreditAndIndustry() -> None:
    """이미 계산된 신용 등급과 산업 국면을 본문으로 끌어올린다.

    두 뱃지는 오래전부터 payload 에 있었지만 본문에 없어 답변에 한 번도 쓰이지 않았다.
    수치 하나가 좋은지 나쁜지 말하려면 기준이 필요하다.
    """
    block = contextMarkdown(
        {"grade": "dCR-AA", "outlook": "안정적", "pdEstimate": 0.02, "investmentGrade": True},
        {
            "industryName": "반도체",
            "stageName": "전공정(FAB)",
            "phase": "재도약",
            "peers": [{"stockCode": "000660", "corpName": "SK하이닉스"}],
        },
    )

    assert "dCR-AA" in block
    assert "투자등급" in block
    assert "재도약" in block
    assert "SK하이닉스(000660)" in block


def testContextBlockIsEmptyWithoutBadges() -> None:
    """뱃지가 없으면 아무 것도 덧붙이지 않는다. 빈 제목만 남기면 소음이다."""
    assert contextMarkdown(None, None) == ""
    assert contextMarkdown({}, {}) == ""


def testUnknownIndustryPhaseIsOmitted() -> None:
    """분류에 실패한 국면을 unknown 이라고 화면에 적지 않는다."""
    block = contextMarkdown(None, {"industryName": "반도체", "phase": "unknown"})

    assert "unknown" not in block
    assert "반도체" in block


def testMissingValuesDoNotCrash() -> None:
    """일부 기간 값이 비어도 하이픈으로 채우고 계속 진행한다."""
    summary = _summary(
        sales={"2025FY": 100e12, "2023FY": 80e12},
        operating_profit={"2025FY": 13e12},
    )

    block = insightMarkdown(summary)

    assert "-" in block
