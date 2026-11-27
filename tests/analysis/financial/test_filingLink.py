"""사업보고서 문장과 재무 숫자 연결(calcFilingLinks)과 새 문장(calcNewFilingSentences)을 본다.

금액 읽기는 원화만 받고 달러·대수·법 조항은 버려야 한다. 이유 문장은 계정 이름 뒤에 조사가 붙은
문장만 받는다(SK하이닉스 외환위험 문장이 '부채' 이유로 붙던 잡음). 새 문장은 숫자만 바뀐 문장을
같은 문장으로 본다.
"""

from __future__ import annotations

from types import SimpleNamespace

import polars as pl
import pytest

from dartlab.analysis.financial import filingLink
from dartlab.story.blocks import HeadingBlock, MetricBlock, TextBlock

pytestmark = pytest.mark.unit

_IV = "IV. 이사의 경영진단 및 분석의견"
_II = "II. 사업의 내용"


def _amounts(sentence: str) -> list[tuple[str, float]]:
    """문장에서 읽은 (금액 글, 값) 목록."""
    return [(text, value) for text, value, _ in filingLink._readAmounts(sentence)]


@pytest.mark.parametrize(
    ("sentence", "expected"),
    [
        ("매출은 52조 4,102억원입니다.", [("52조 4,102억원", 52.4102e12)]),
        ("영업이익 4,128억원을 냈습니다.", [("4,128억원", 4128e8)]),
        ("매출 334조원을 기록하였습니다.", [("334조원", 334e12)]),
        ("매출 897,514백만원입니다.", [("897,514백만원", 897514e6)]),
        ("전년 대비 23조 7,390억 증가하였습니다.", [("23조 7,390억", 23.739e12)]),
    ],
)
def testReadsWonAmounts(sentence, expected):
    """조·억·백만 원화 금액과 '원'을 빠뜨린 조+억 금액을 읽는다."""
    got = _amounts(sentence)
    assert [text for text, _ in got] == [text for text, _ in expected]
    for (_, value), (_, want) in zip(got, expected):
        assert value == pytest.approx(want)


@pytest.mark.parametrize(
    "sentence",
    [
        "시장 규모는 905억달러입니다.",
        "출하량은 2.1억대입니다.",
        "상법 제159조에 따라 공시합니다.",
        "백만 명이 이용합니다.",
    ],
)
def testSkipsNonWonAmounts(sentence):
    """달러·대수·법 조항·사람 수는 금액으로 읽지 않는다."""
    assert _amounts(sentence) == []


def testSplitsSentencesWithoutSpaceAndUnescapes():
    """띄어쓰기 없이 붙은 문장을 나누고 원문 꺾쇠 글자를 되살린다."""
    text = "매출은 늘었습니다.부채는 줄었습니다. &lt;IB 부문&gt; 설명입니다."
    assert filingLink._splitSentences(text) == ["매출은 늘었습니다.", "부채는 줄었습니다.", "<IB 부문> 설명입니다."]


@pytest.mark.parametrize(
    ("sentence", "account", "mentioned", "expected"),
    [
        ("매출액은 메모리 판가 상승에 따른 영향으로 늘었습니다.", "매출액", False, True),
        ("매출액은 늘었습니다.", "매출액", False, False),
        ("매출원가율 개선 영향으로 이익이 늘었습니다.", "매출액", False, False),
        ("매출원가율 개선 영향으로 매출 10조원이 늘었습니다.", "매출액", True, True),
        ("환율 변동 영향 외환위험은 외화 자산과 부채 모두에서 생깁니다.", "부채총계", False, False),
    ],
)
def testReasonNeedsAccountWithParticle(sentence, account, mentioned, expected):
    """이유 표시어가 있고 계정 이름 뒤에 조사가 붙은 문장만 이유로 받는다."""
    key = filingLink._nameKey(sentence)
    assert filingLink._isReason(key, sentence, account, mentioned) is expected


class _Result:
    """select 결과 흉내. df 만 가진다."""

    def __init__(self, df):
        self.df = df


def _company(statements: dict[str, pl.DataFrame]):
    """연간 재무제표만 가진 작은 DART 회사."""

    def _select(statement, freq="Y"):
        return _Result(statements.get(statement))

    return SimpleNamespace(stockCode="999990", select=_select)


@pytest.fixture
def smallCompany():
    """매출액·영업이익·부채총계 두 해 숫자."""
    return _company(
        {
            "IS": pl.DataFrame(
                {
                    "항목": ["매출액", "영업이익"],
                    "2025": [333_605_938_000_000.0, 43_601_100_000_000.0],
                    "2024": [300_870_903_000_000.0, 32_726_000_000_000.0],
                }
            ),
            "BS": pl.DataFrame({"항목": ["부채총계"], "2025": [100_000_000_000_000.0], "2024": [90_000_000_000_000.0]}),
        }
    )


def testLinksAmountSentenceAndReason(monkeypatch, smallCompany):
    """금액 문장을 매출액에 맞추고 같은 글의 이유 문장을 붙인다. 달러 금액은 세지 않는다."""
    leaves = pl.DataFrame(
        [
            {
                "chapter": _IV,
                "sectionLeaf": "2. 개요",
                "2025Q4": (
                    "당사 매출액은 전년 대비 32조 7,350억원 증가한 333조 6,059억원을 기록하였습니다. "
                    "매출액은 메모리 판가 상승에 따른 영향으로 늘었습니다. "
                    "회사는 2,000억달러 규모 시장을 봅니다."
                ),
            }
        ]
    )
    monkeypatch.setattr(filingLink, "_textLeaves", lambda code, periods: leaves)
    monkeypatch.setattr(filingLink, "_segmentCandidates", lambda company, year, basePeriod: [])

    result = filingLink.calcFilingLinks(smallCompany)

    assert result["year"] == "2025"
    assert result["amountCount"] == 2
    assert result["matchedCount"] == 2
    assert [a["account"] for a in result["accounts"]] == ["매출액"]
    sales = result["accounts"][0]
    assert len(sales["mentions"]) == 1
    assert sales["mentions"][0]["amount"] == "32조 7,350억원"
    assert sales["mentions"][0]["kind"] == "증감"
    assert [r["sentence"] for r in sales["reasons"]] == ["매출액은 메모리 판가 상승에 따른 영향으로 늘었습니다."]
    assert "_order" not in sales["mentions"][0]


def testNoTextMeansNone(monkeypatch, smallCompany):
    """공시 글이 없거나 DART 회사가 아니면 None 이다."""
    monkeypatch.setattr(filingLink, "_textLeaves", lambda code, periods: None)
    assert filingLink.calcFilingLinks(smallCompany) is None
    assert filingLink.calcFilingLinks(SimpleNamespace(stockCode="AAPL")) is None


def testNewSentencesSkipNumberOnlyChanges(monkeypatch, smallCompany):
    """숫자만 바뀐 문장과 I장 문장은 빼고, 경영진단의 위험 문장을 앞에 둔다."""
    leaves = pl.DataFrame(
        [
            {
                "chapter": _II,
                "sectionLeaf": "1. 사업의 개요",
                "2025Q4": (
                    "당사는 2025년에 매출 10조원을 기록하였습니다. "
                    "당사는 내년 미국 시장 진출을 계획하고 있으며 관세 부담이 커질 것으로 예상됩니다."
                ),
                "2024Q4": "당사는 2024년에 매출 9조원을 기록하였습니다.",
            },
            {
                "chapter": "I. 회사의 개요",
                "sectionLeaf": "1. 회사의 개요",
                "2025Q4": "회사 개요 장에 새로 들어간 문장이지만 사업 설명이 아니라서 고르지 않습니다.",
                "2024Q4": None,
            },
            {
                "chapter": _IV,
                "sectionLeaf": "3. 재무상태 및 영업실적",
                "2025Q4": "반도체 수요 둔화에 따른 재고 부담으로 하반기 실적이 악화될 위험이 있습니다.",
                "2024Q4": None,
            },
        ]
    )
    monkeypatch.setattr(filingLink, "_textLeaves", lambda code, periods: leaves)

    result = filingLink.calcNewFilingSentences(smallCompany)

    assert result["period"] == "2025Q4"
    assert result["previousPeriod"] == "2024Q4"
    assert result["newSentenceCount"] == 2
    assert [s["chapter"] for s in result["sentences"]] == [_IV, _II]


def testNewSentencesNeedPreviousYear(monkeypatch, smallCompany):
    """전년 글이 없으면 새 문장을 가를 수 없어 None 이다."""
    leaves = pl.DataFrame([{"chapter": _II, "sectionLeaf": "1. 사업의 개요", "2025Q4": "올해 글만 있는 회사입니다."}])
    monkeypatch.setattr(filingLink, "_textLeaves", lambda code, periods: leaves)
    assert filingLink.calcNewFilingSentences(smallCompany) is None


_LINKS = {
    "year": "2025",
    "period": "2025Q4",
    "sentenceCount": 1032,
    "amountCount": 105,
    "matchedCount": 47,
    "accountCount": 2,
    "accounts": [
        {
            "account": "자산총계",
            "statement": "BS",
            "current": 566e12,
            "previous": 514e12,
            "change": 52e12,
            "mentions": [
                {
                    "chapter": _IV,
                    "section": "3. 재무상태",
                    "sentence": "자산은 566조원입니다.",
                    "amount": "566조원",
                    "kind": "당기",
                }
            ],
            "reasons": [],
        },
        {
            "account": "매출액",
            "statement": "IS",
            "current": 333.6e12,
            "previous": 300.9e12,
            "change": 32.7e12,
            "mentions": [
                {
                    "chapter": _IV,
                    "section": "2. 개요",
                    "sentence": "매출 334조원입니다.",
                    "amount": "334조원",
                    "kind": "당기",
                }
            ],
            "reasons": [
                {"chapter": _IV, "section": "2. 개요", "sentence": "매출액은 판가 상승에 따른 영향으로 늘었습니다."}
            ],
        },
    ],
    "segments": [
        {
            "chapter": _IV,
            "section": "4. 부문별",
            "sentence": "DS 부문 매출은 130조원입니다.",
            "segments": ["DS 매출"],
            "following": ["AI 수요 강세는 지속될 것으로 전망합니다."],
        }
    ],
}


def testStoryBlocksQuoteCompanySentences():
    """스토리 블록은 이유가 있는 계정을 앞에 두고 회사 문장을 위치와 함께 인용한다."""
    from dartlab.story.builders import (
        filingAccountStoryBlock,
        filingCoverageBlock,
        filingSegmentStoryBlock,
        newFilingSentencesBlock,
    )

    coverage = filingCoverageBlock(_LINKS)
    assert isinstance(coverage[0], HeadingBlock) and isinstance(coverage[1], MetricBlock)
    assert coverage[1].metrics[:2] == [
        ("재무 숫자와 맞은 금액", "105개 가운데 47개"),
        ("회사가 이유를 붙인 계정", "2개 가운데 1개"),
    ]

    accounts = filingAccountStoryBlock(_LINKS)
    texts = [b.text for b in accounts if isinstance(b, TextBlock)]
    assert texts[0].startswith("**매출액** 333.6조원 (전년 300.9조원)")
    assert f"> 매출액은 판가 상승에 따른 영향으로 늘었습니다. ({_IV} > 2. 개요)" in texts[0]
    assert texts[1].endswith("이 금액을 적은 절에서는 회사가 이유를 밝히지 않았다.")

    segment = filingSegmentStoryBlock(_LINKS)
    assert segment[1].text.startswith("**DS 매출**")
    assert "- AI 수요 강세는 지속될 것으로 전망합니다." in segment[1].text

    fresh = newFilingSentencesBlock(
        {
            "year": "2025",
            "period": "2025Q4",
            "previousPeriod": "2024Q4",
            "newSentenceCount": 163,
            "sentences": [{"chapter": _IV, "section": "", "sentence": "수요 둔화 위험이 있습니다."}],
        }
    )
    assert "2024년 보고서에 없던 문장 163개" in fresh[0].helper
    assert fresh[1].text == f"> 수요 둔화 위험이 있습니다. ({_IV})"

    for block in (filingCoverageBlock, filingAccountStoryBlock, filingSegmentStoryBlock, newFilingSentencesBlock):
        assert block(None) == []


def testAccountsSharingOneSentenceAreShownOnce():
    """같은 이유 문장을 가진 계정은 한 번에 묶어 그 문장을 한 번만 인용한다(삼성전자 자산 문장)."""
    from dartlab.story.builders import filingAccountStoryBlock

    reason = {"chapter": _IV, "section": "3. 재무상태", "sentence": "자산의 주요 증가 원인은 시설투자입니다."}
    accounts = [
        {"account": name, "current": value, "previous": None, "mentions": [reason], "reasons": [reason]}
        for name, value in (("자산총계", 566.9e12), ("유형자산", 215.3e12))
    ]

    texts = [b.text for b in filingAccountStoryBlock({"accounts": accounts}) if isinstance(b, TextBlock)]

    assert len(texts) == 1
    assert texts[0].count("> 자산의 주요 증가 원인은 시설투자입니다.") == 1
    assert "**자산총계** 566.9조원" in texts[0] and "**유형자산** 215.3조원" in texts[0]


@pytest.mark.parametrize(
    ("names", "expected"),
    [
        (["DxDivision 매출", "DxDivision 영업이익"], "DX 매출·영업이익"),
        (["Sdc 매출", "Harman 매출"], "SDC 매출, Harman 매출"),
        (["LgEnergySolutionLtd 매출"], "LG Energy Solution 매출"),
    ],
)
def testSegmentHeadUsesReadableNames(names, expected):
    """XBRL 부문 이름(DxDivision)을 글에 쓰는 이름(DX)으로 바꿔 부문마다 묶는다."""
    from dartlab.story.builders.filing import _segmentHead

    assert _segmentHead(names) == expected


def testRepeatedSegmentSentenceKeptOnce(monkeypatch, smallCompany):
    """다른 절에 제목만 붙여 다시 실은 부문 금액 문장은 한 번만 둔다."""
    sentence = "2025년 매출은 DS 부문이 130조 1,282억원입니다."
    leaves = pl.DataFrame(
        [
            {"chapter": _II, "sectionLeaf": "2. 주요 제품", "2025Q4": sentence},
            {"chapter": _II, "sectionLeaf": "7. 기타", "2025Q4": f"라. 사업부문별 요약 {sentence}"},
        ]
    )
    monkeypatch.setattr(filingLink, "_textLeaves", lambda code, periods: leaves)
    monkeypatch.setattr(
        filingLink,
        "_segmentCandidates",
        lambda company, year, basePeriod: [("", 130.1282e12, "당기", "segment", "DsDivision 매출", 3)],
    )

    result = filingLink.calcFilingLinks(smallCompany)

    assert [s["section"] for s in result["segments"]] == ["2. 주요 제품"]


def testRegistryBuildsFilingBlocks(monkeypatch):
    """buildBlocks 가 사업보고서 블록 3개와 공시변화의 새 문장 블록을 만든다."""
    from dartlab.story.registry import buildBlocks

    monkeypatch.setattr(filingLink, "calcFilingLinks", lambda company, basePeriod=None: _LINKS)
    monkeypatch.setattr(filingLink, "calcNewFilingSentences", lambda company, basePeriod=None: None)
    keys = {"filingCoverage", "filingAccountStory", "filingSegmentStory", "newFilingSentences"}

    blocks = buildBlocks(SimpleNamespace(stockCode="999990", currency="KRW"), keys)

    assert blocks["filingCoverage"]
    assert blocks["filingAccountStory"]
    assert blocks["filingSegmentStory"]
    assert blocks["newFilingSentences"] == []
