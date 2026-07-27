"""서술 표 단위 해석 회귀.

단위 감지가 "캡션을 찾았는가" 와 "배율을 알아냈는가" 를 구분하지 않았다. 캡션만 찾으면
resolved 로 보고 모르는 단위는 조용히 백만원으로 떨어뜨렸다.

그래서 '(단위: 억원, %)' 처럼 단위와 퍼센트가 함께 적힌 통상 표기가 100 배 낮게,
'조원' 은 100 만 배 낮게 나왔다. 게다가 그 값에 confidence 'high' 까지 붙어서 호출부가
믿을 만한 숫자로 받았다. sanity 상한이 1000 조라 100 배 축소는 걸러지지도 않는다.

배율을 모르면 그 사실을 말해야 한다는 것이 여기서 고정하는 계약이다.
"""

from __future__ import annotations

import pytest

from dartlab.providers.dart.panel.narrativeMetric import _detectUnit


@pytest.mark.parametrize(
    ("caption", "expected"),
    [
        ("(단위 : 억원)", 1e8),
        ("(단위: 억원)", 1e8),
        ("(단위: 백만원)", 1e6),
        ("(단위 : 천원)", 1e3),
        ("(단위: 십억원)", 1e9),
        ("(단위: 조원)", 1e12),
        ("(단위 : 원)", 1.0),
    ],
)
def testKnownUnitsResolveToTheirScale(caption: str, expected: float) -> None:
    """아는 단위는 정확한 배율과 함께 resolved 로 나온다."""

    scale, resolved = _detectUnit(caption)

    assert scale == expected
    assert resolved is True


@pytest.mark.parametrize(
    "caption",
    ["(단위: 억원, %)", "(단위 : 백만원, %)", "(단위: 조원, 배)"],
)
def testUnitSurvivesWhenThePercentSignSharesTheCaption(caption: str) -> None:
    """DART 표는 단위와 퍼센트를 한 괄호에 적는 일이 잦다. 그때도 단위를 읽어야 한다."""

    scale, resolved = _detectUnit(caption)

    assert resolved is True
    assert scale > 1.0


def testMixedCaptionResolvesToTheLeadingUnitNotTheDefault() -> None:
    """가장 비쌌던 사례를 값으로 못 박는다. 예전에는 100 배 낮은 백만원이었다."""

    assert _detectUnit("(단위: 억원, %)") == (1e8, True)


@pytest.mark.parametrize("caption", ["(단위 : 천주)", "(단위: 대)", "(단위 : 알수없음)"])
def testUnknownUnitIsReportedAsUnresolved(caption: str) -> None:
    """모르는 단위를 아는 척하면 안 된다. 배율을 못 알아냈다고 말해야 한다."""

    _scale, resolved = _detectUnit(caption)

    assert resolved is False


def testMissingCaptionIsUnresolved() -> None:
    """캡션이 아예 없으면 당연히 모른다."""

    assert _detectUnit("<TABLE><TR><TD>수주잔고</TD></TR></TABLE>") == (1e6, False)


def testUnitIsFoundInsideSurroundingTableMarkup() -> None:
    """실제 입력은 표 XML 통째다. 캡션만 오는 것이 아니다."""

    xml = "<TABLE><P>수주 현황 (단위 : 억원)</P><TR><TD>합계</TD><TD>1,000</TD></TR></TABLE>"

    assert _detectUnit(xml) == (1e8, True)
