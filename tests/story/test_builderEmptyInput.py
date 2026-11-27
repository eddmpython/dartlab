"""story 블록 빌더가 계산 결과가 없을 때 블록 없이 빈 목록을 돌려주는지 본다.

registry 는 계산이 실패하거나 값이 없으면 None 을 넘긴다. 그때 빌더가 예외를 내거나
빈 제목만 남기면 독자에게 내용 없는 절이 보이므로, 빈 입력에는 빈 목록이어야 한다.
"""

from __future__ import annotations

import pytest

from dartlab.story.builders import quality, revenue, valuation

_BUILDERS = [
    quality.calibrationReportBlock,
    quality.cagrComparisonBlock,
    quality.articulationCheckBlock,
    quality.piotroskiFactorBlock,
    quality.accrualsFactorBlock,
    quality.earningsSurpriseBlock,
    revenue.nonOperatingBreakdownBlock,
    valuation.scenarioSensitivityBlock,
    valuation.residualIncomeBlock,
    valuation.dFVBlock,
    valuation.methodFitnessBlock,
    valuation.qualityFactorsBlock,
    valuation.sensitivityBlock,
    valuation.valuationSynthesisBlock,
    valuation.valuationFlagsBlock,
    valuation.companyCyclePositionBlock,
    valuation.valuationBandBlock,
    valuation.lifeCycleStageBlock,
    valuation.valuationSinsBlock,
    valuation.plausibilityBandBlock,
    valuation.macroSensitivityBlock,
]


@pytest.mark.parametrize("empty", [None, {}], ids=["none", "emptyDict"])
@pytest.mark.parametrize("builder", _BUILDERS, ids=lambda fn: fn.__name__)
def testEmptyInputGivesNoBlocks(builder, empty):
    assert builder(empty) == []


def testHistoryBuildersSkipEmptyHistory():
    assert quality.cagrComparisonBlock({"comparisons": []}) == []
    assert quality.articulationCheckBlock({"history": []}) == []
    assert revenue.nonOperatingBreakdownBlock({"history": []}) == []
    assert valuation.lifeCycleStageBlock({"phase": None}) == []
    assert valuation.qualityFactorsBlock({"qualityWACC": {"factors": []}}) == []


def testValuationFlagsKeepSignalMark():
    blocks = valuation.valuationFlagsBlock(
        [
            {"signal": "warning", "label": "부채 부담"},
            {"signal": "opportunity", "label": "현금 여력"},
        ]
    )
    assert blocks
    text = repr(blocks)
    assert "[!] 부채 부담" in text
    assert "[+] 현금 여력" in text
