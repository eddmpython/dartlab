"""이야기 본문 숫자와 문장이 입력을 그대로 말하는지 본다(2026-11-27 삼성전자 실측 회귀).

삼성전자 이야기에서 나온 결함들이다. 막 결론이 '+10' 에서 잘렸고(소수점을 문장 끝으로 봄),
부문 매출이 '187967346.0조' 로 찍혔고(원 단위 값을 백만원으로 봄), 표의 비중·이익률 열이
사라졌고, 적정가 판정이 verdict 와 어긋났고, 궤적 하나뿐인 storyTree 가 "서사와 무관하게
안정" 이라고 말했다.
"""

from __future__ import annotations

from types import SimpleNamespace

import polars as pl

from dartlab.story.summary import _firstSentence, buildSectionSummary


def test_first_sentence_keeps_decimal_point():
    assert _firstSentence("매출 성장률 +10.9%. 다음 문장") == "매출 성장률 +10.9%"
    assert _firstSentence("영업이익률 46.1%") == "영업이익률 46.1%"


def test_section_summary_text_block_not_cut_at_decimal():
    from dartlab.story.blocks import TextBlock

    sec = SimpleNamespace(blocks=[TextBlock("매출 성장률 +10.9%. 이어지는 설명.")], threads=[])
    assert buildSectionSummary(sec) == "매출 성장률 +10.9%"


def test_unify_table_scale_won_and_keeps_other_columns():
    from dartlab.story.utils import unifyTableScale

    rows = [
        {
            "부문": "DX",
            "매출": 187_967_346_000_000.0,
            "비중": "52%",
            "영업이익": 12_852_650_000_000.0,
            "이익률": "6.8%",
        },
        {"부문": "DS", "매출": 130_128_162_000_000.0, "비중": "36%", "영업이익": None, "이익률": "-"},
    ]
    out = unifyTableScale(rows, "부문", ["매출", "영업이익"], unit="won")
    assert out[0]["매출"] == "188.0조"
    assert out[0]["영업이익"] == "12.9조"
    assert out[0]["비중"] == "52%" and out[0]["이익률"] == "6.8%"
    assert out[1]["영업이익"] == "-"
    assert list(out[0]) == ["부문", "매출", "비중", "영업이익", "이익률"]


def test_segment_composition_block_reads_won():
    from dartlab.story.blocks import TableBlock
    from dartlab.story.builders.revenue import segmentCompositionBlock

    data = {
        "totalRevenue": 363_720_494_000_000.0,
        "hasOpIncome": True,
        "segments": [
            {"name": "DX", "revenue": 187_967_346_000_000.0, "opIncome": 12_852_650_000_000.0, "opMargin": 6.8},
        ],
    }
    table = next(b for b in segmentCompositionBlock(data) if isinstance(b, TableBlock))
    row = table.df.row(0, named=True)
    assert row["매출"] == "188.0조"
    assert row["비중"] == "52%"


def test_richardson_accrual_is_percent_not_amount():
    from dartlab.story.blocks import TableBlock
    from dartlab.story.builders.quality import richardsonAccrualBlock

    data = {"history": [{"period": "2026", "wcacc": 14.36, "ltoacc": 5.65, "finacc": -6.02, "totalAccrual": 13.98}]}
    table = next(b for b in richardsonAccrualBlock(data) if isinstance(b, TableBlock))
    row = table.df.row(0, named=True)
    assert row["WCACC"] == "+14.4%"
    assert row["FINACC"] == "-6.0%"
    assert "억" not in str(row) and "조" not in str(row)


def test_valuation_text_follows_verdict():
    from dartlab.story.narrate import narrateValuation

    text = narrateValuation({"verdict": "적정", "fairValueRange": [60_000, 200_000], "currentPrice": 100_000})
    assert text.startswith("종합 판정: 적정.")
    assert "범위 안이다" in text
    assert "안전마진" not in text and "저평가" not in text
    assert "범위가 넓다" in text


def test_dfv_text_has_no_investment_opinion():
    from dartlab.story.narrate import narrateDFV

    text = narrateDFV({"dFV": 90_000, "currentPrice": 100_000, "upside": -10.0, "opinion": "매수"}) or ""
    assert "투자 의견" not in text and "매수" not in text


def test_peer_year_skips_thin_latest_year():
    from dartlab.analysis.financial.storyValidation import _peerYear

    snap = pl.DataFrame(
        {
            "bsns_year": ["2026"] * 5 + ["2025"] * 20 + ["2024"] * 19,
            "stockCode": [f"{i:06d}" for i in range(5)]
            + [f"{i:06d}" for i in range(20)]
            + [f"{i:06d}" for i in range(19)],
        }
    )
    assert _peerYear(snap) == "2025"


def test_story_tree_single_trajectory_claims_no_stability():
    from dartlab.story.storyTree import narrateStoryTree

    tree = {
        "probable": {"dFV": 100_000, "label": "기본"},
        "summary": {"min": 100_000, "max": 100_000, "spread": 0, "spreadPct": None, "mean": 100_000, "count": 1},
    }
    assert "안정" not in narrateStoryTree(tree)


def test_industry_gap_reason_when_detail_not_computed():
    from dartlab.industry.product import buildIndustryProduct

    company = SimpleNamespace(stockCode="005930", market="KR")
    result = {
        "industry": "semiconductor",
        "stage": "midstream",
        "detailComputed": False,
        "sectorMetrics": None,
        "sectorCycle": None,
        "profitPool": None,
        "relationships": None,
        "concentration": None,
    }
    product = buildIndustryProduct(company, result)
    reasons = {g["id"]: g["reason"] for g in product["gaps"]}
    assert "기본 조회에서 계산하지 않았습니다" in reasons["industry.sectorMetrics"]
    assert "확보하지 못했습니다" not in reasons["industry.sectorMetrics"]
