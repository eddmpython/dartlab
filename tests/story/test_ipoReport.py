"""ipoReport — IPO 공모분석 리포트 렌더 회귀(순수, fetch 0).

renderIpoReport 가 파싱 dict → 6 카테고리 섹션 + 검증 배지 + implied 좌표 + 확정가 신호 + 원문근거를
markdown 으로 조립하는지. 합성 parsed dict 입력(parseIpoProspectus 형태).
"""

from __future__ import annotations

import pytest

from dartlab.story.ipoReport import renderIpoReport

pytestmark = [pytest.mark.unit]

_PARSED = {
    "offering": {
        "priceBand": (80000, 90000),
        "offerTotal": 80e9,
        "subscription": "2026.09.01 ~ 09.02",
        "payDate": "2026.09.04",
    },
    "valuation": {"model": "PER", "peerMultiple": 20.0, "perShareValue": 100000, "discount": (10, 20)},
    "financials": {
        "rows": {"매출액": [50e9], "영업이익": [12e9], "당기순이익": [10e9]},
        "periods": ["2025년"],
        "unit": 1.0,
    },
    "float": {
        "freeFloatPct": 30.0,
        "freeFloatShares": 300000,
        "lockedShares": 700000,
        "postOfferingShares": 1000000,
        "lockups": [{"holder": "홍길동", "period": "24개월", "shares": 700000}],
    },
    "multiples": {
        "marketCap": (80e9, 90e9),
        "per": (8.0, 9.0),
        "psr": (1.6, 1.8),
        "pbr": (2.0, 2.25),
        "annualPeriod": "2025년",
        "isLoss": False,
    },
    "identities": {"valuationChain": True, "floatBalance": True, "financialsBalance": True, "sharesRecovered": 1000000},
    "risk": {"count": 3, "sections": ["사업위험", "회사위험", "기타위험"]},
}


def test_render_sections_and_title():
    r = renderIpoReport(_PARSED, corpName="테스트", rcept="20260101000001")
    assert r["title"] == "테스트 공모분석"
    titles = [s["title"] for s in r["sections"]]
    assert titles == ["공모 개요", "공모 일정", "밸류에이션", "유통가능물량 · 보호예수", "재무 (요약)", "투자위험"]


def test_render_markdown_key_facts():
    r = renderIpoReport(_PARSED, corpName="테스트", rcept="20260101000001", confirmation={"confirmedPrice": 90000})
    md = r["markdown"]
    assert "# 테스트 공모분석" in md
    assert "확정 90,000원 (밴드 상단)" in md  # 확정가 vs 밴드 신호
    assert "비교기업 20.0배 대비 저평가 좌표" in md  # implied 8~9 < 비교 20
    assert "유통가능비율: 30.00%" in md
    assert "20260101000001" in md  # 원문근거
    assert "고/저평가 단정 아님" in md  # 단정 회피 면책


def test_render_loss_tag_and_badges():
    parsed = {**_PARSED, "multiples": {**_PARSED["multiples"], "isLoss": True}}
    r = renderIpoReport(parsed, corpName="적자사")
    md = r["markdown"]
    assert "최근 연간 적자" in md
    assert "〔✓ 검증〕" in md  # floatBalance·valuationChain True 배지


def test_render_never_raises_on_empty():
    r = renderIpoReport({}, corpName="빈회사")
    assert r["title"] == "빈회사 공모분석"
    assert isinstance(r["markdown"], str) and "빈회사 공모분석" in r["markdown"]
