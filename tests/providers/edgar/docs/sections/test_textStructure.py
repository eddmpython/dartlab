"""providers/edgar/docs/sections/textStructure.py mirror smoke — P6."""

import time

import pytest

pytestmark = pytest.mark.unit

# 예전 Title Case 패턴이면 "A" + " a" * 24 + " !" 한 줄에 수 초가 걸린다(2 회 늘 때마다 약 4 배).
_FAST_SECONDS = 0.5


def test_imports():
    try:
        import dartlab.providers.edgar.docs.sections.textStructure  # noqa: F401
    except ImportError as e:
        pytest.skip(f"module import requires data/env: {e}")


def test_parse_text_structure_callable() -> None:
    """parseTextStructure() callable smoke."""
    from dartlab.providers.edgar.docs.sections.textStructure import parseTextStructure

    assert callable(parseTextStructure)


@pytest.mark.parametrize(
    "line",
    [
        "Risk Factors",
        "Wearables, Home and Accessories",
        "Research and Development",
        "Selling, General and Administrative",
        "Products and Services Performance",
        "Management's Discussion and Analysis of Financial Condition",
        "Property, Plant and Equipment",
        "Americas/Europe & Rest of Asia Pacific",
        "Home & Accessories - Other",
        "iPhone",
        "AppleCare®",
        "Products and",
    ],
)
def test_title_case_accepts_representative_headings(line: str) -> None:
    """접속사·전치사가 섞인 실제 heading 형태는 예전처럼 Title Case 로 잡힌다."""
    from dartlab.providers.edgar.docs.sections.textStructure import _RE_TITLE_CASE

    assert _RE_TITLE_CASE.fullmatch(line) is not None


@pytest.mark.parametrize(
    "line",
    [
        "Item 1A. Risk Factors",
        "Net sales 2024",
        "Q3 Results",
        "Total (in millions)",
        "Revenue: Americas",
        "- Leading dash",
        "Growth 5%",
        "A and and and !",
    ],
)
def test_title_case_rejects_non_headings(line: str) -> None:
    """숫자/괄호/콜론 등이 섞인 줄은 예전처럼 Title Case 가 아니다."""
    from dartlab.providers.edgar.docs.sections.textStructure import _RE_TITLE_CASE

    assert _RE_TITLE_CASE.fullmatch(line) is None


@pytest.mark.parametrize(
    "line",
    [
        "A" + " a" * 24 + " !",
        "A" + " and" * 22 + " !",
        "Apple" + " of the" * 11 + " 1",
    ],
)
def test_title_case_is_linear_on_pathological_input(line: str) -> None:
    """접속사가 반복된 뒤 실패하는 줄도 즉시 끝난다 (예전 패턴은 지수 backtracking)."""
    from dartlab.providers.edgar.docs.sections.textStructure import _RE_TITLE_CASE

    started = time.perf_counter()
    assert _RE_TITLE_CASE.fullmatch(line) is None
    assert time.perf_counter() - started < _FAST_SECONDS


def test_is_heading_levels_and_pathological_line() -> None:
    """heading 판정 결과는 그대로이고, 65 자 한도 안의 병적인 줄도 빨리 body 로 끝난다."""
    from dartlab.providers.edgar.docs.sections.textStructure import _isHeading

    assert _isHeading("RISK FACTORS", prevBlank=True, nextBlank=True) == (True, 1)
    assert _isHeading("Wearables, Home and Accessories", prevBlank=True, nextBlank=True) == (True, 2)
    assert _isHeading("The Company designs and markets smartphones", prevBlank=True, nextBlank=True) == (False, 0)

    line = "A" + " a" * 24 + " !"
    assert len(line) <= 65
    started = time.perf_counter()
    assert _isHeading(line, prevBlank=True, nextBlank=False) == (False, 0)
    assert time.perf_counter() - started < _FAST_SECONDS
