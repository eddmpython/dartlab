"""자연어 종목 추출 회귀.

`frame/resolve.py` 는 CLI, Python API, 서버가 공유하는 원소스인데 공개 함수 다섯이 전부
테스트 참조 0 이었다. 여기서 종목을 잘못 집으면 그 뒤 분석 전체가 다른 회사 이야기가
되고, 아무것도 못 집으면 질문이 통째로 회사 없이 흘러간다. 둘 다 조용하다.

조사 제거와 별칭 해석은 순수 함수라 값으로 못 박고, 코드 추출은 형태별 경계를 본다.
"""

from __future__ import annotations

import pytest

from dartlab.frame.resolve import (
    COMMON_ALIASES,
    resolveAlias,
    resolveStockCodeFromText,
    stripParticles,
)


@pytest.mark.parametrize(
    ("text", "expected"),
    [
        ("삼성전자의", "삼성전자"),
        ("삼성전자는", "삼성전자"),
        ("삼성전자가", "삼성전자"),
        ("삼성전자를", "삼성전자"),
        ("삼성전자에서", "삼성전자"),
        ("삼성전자보다", "삼성전자"),
    ],
)
def testParticlesAreStrippedFromTheTail(text: str, expected: str) -> None:
    """조사가 붙은 채로는 어떤 표와도 맞지 않는다."""

    assert stripParticles(text) == expected


def testStrippingOnlyTouchesTheTail() -> None:
    """이름 안쪽 글자가 조사와 같아도 지우면 안 된다."""

    assert stripParticles("이수페타시스") == "이수페타시스"
    assert stripParticles("한국가스공사") == "한국가스공사"


def testNameWithoutAParticleIsUnchanged() -> None:
    """조사가 없으면 그대로 둔다."""

    assert stripParticles("삼성전자") == "삼성전자"
    assert stripParticles("") == ""


def testAliasResolvesToTheFormalName() -> None:
    """약칭은 정식명으로 이어져야 검색이 걸린다."""

    assert resolveAlias("삼전") == "삼성전자"
    assert resolveAlias("하이닉스") == "SK하이닉스"


def testAliasResolvesAfterStrippingAParticle() -> None:
    """말할 때는 조사가 붙는다. '삼전은' 도 같은 회사다."""

    assert resolveAlias("삼전은") == "삼성전자"
    assert resolveAlias("하이닉스의") == "SK하이닉스"


def testUnknownTextHasNoAlias() -> None:
    """모르는 말에 아무 회사나 붙이면 안 된다."""

    assert resolveAlias("삼성전자") is None
    assert resolveAlias("존재하지않는말") is None
    assert resolveAlias("") is None


def testEveryAliasPointsAtANonEmptyDistinctName() -> None:
    """별칭이 자기 자신을 가리키거나 비면 해석이 무의미해진다."""

    for alias, formal in COMMON_ALIASES.items():
        assert alias and formal
        assert alias != formal


def testStockCodeIsExtractedAndRemovedFromTheQuestion() -> None:
    """코드를 뽑았으면 질문에서는 빠져야 뒤 단계가 깔끔하다."""

    code, question = resolveStockCodeFromText("005930 재무 알려줘")

    assert code == "005930"
    assert question == "재무 알려줘"


def testAliasPathReturnsTheFormalNameNotTheCode() -> None:
    """약칭 경로는 이름을 돌려준다. 코드 조회는 그다음 단계 몫이다."""

    resolved, question = resolveStockCodeFromText("삼전 분석")

    assert resolved == "삼성전자"
    assert question == "분석"


def testTextWithoutACompanyResolvesToNothingAndKeepsTheQuestion() -> None:
    """회사가 없으면 없다고 해야 한다. 질문은 손상 없이 남는다."""

    resolved, question = resolveStockCodeFromText("그냥 질문")

    assert resolved is None
    assert question == "그냥 질문"


def testEmptyInputIsHandled() -> None:
    """빈 입력이 예외가 되면 상위 호출부가 통째로 죽는다."""

    resolved, question = resolveStockCodeFromText("")

    assert resolved is None
    assert question == ""
