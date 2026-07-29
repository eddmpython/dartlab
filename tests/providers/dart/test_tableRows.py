"""DART 표 셀 파서 회귀.

`tableRows` 는 산업 그래프 빌드(`industry/build/table_parser.py`, `edges.py`)와 건설
섹터 KPI 가 top-level 로 끌어다 쓰는데 테스트가 하나도 없었다. 여기 고정하는 것은
파서가 "값 없음" 과 "잘못된 값" 을 어떻게 가르는지다. 이 경계가 흔들리면 숫자가 조용히
0 이나 빈 문자열로 바뀌어 그래프에 그대로 실린다.
"""

from __future__ import annotations

import pytest

from dartlab.providers.dart.tableRows import (
    extractCorpNames,
    extractTables,
    findTableByHeaders,
    normalizeCorpName,
    parseAmount,
    parsePercent,
    tableToRowDicts,
)


@pytest.mark.parametrize(
    ("cell", "expected"),
    [
        ("138,272", 138272.0),
        ("1 234", 1234.0),
        ("-1,500", -1500.0),
        ("0", 0.0),
        ("3.14", 3.14),
    ],
)
def testParseAmountReadsThousandSeparatorsAndSigns(cell: str, expected: float) -> None:
    """DART 표는 천 단위 쉼표와 공백을 섞어 쓴다. 둘 다 같은 값으로 읽어야 한다."""

    assert parseAmount(cell) == expected


@pytest.mark.parametrize("cell", ["", "-", "   ", "해당사항 없음", "N/A"])
def testParseAmountReturnsNoneRatherThanZeroForAbsentValues(cell: str) -> None:
    """값 없음을 0 으로 돌려주면 안 된다. 0 원 매입과 미기재가 구분되지 않는다."""

    assert parseAmount(cell) is None


def testParseAmountKeepsZeroDistinctFromAbsent() -> None:
    """0 은 값이고 빈 셀은 값이 아니다. 둘이 같은 결과가 되면 안 된다."""

    assert parseAmount("0") == 0.0
    assert parseAmount("") is None


def testExtractTablesSeparatesBlocksAndDropsSeparatorRows() -> None:
    """서로 떨어진 표는 분리하고 마크다운 구분선은 데이터로 내보내지 않는다."""
    content = "|회사|금액|\n|---|---|\n|삼성전자|100|\n\n본문\n|회사|금액|\n|---|---|\n|LG전자|80|"

    assert extractTables(content) == [
        [["회사", "금액"], ["삼성전자", "100"]],
        [["회사", "금액"], ["LG전자", "80"]],
    ]


def testTableToRowDictsInheritsMergedCellsWithoutInventingColumns() -> None:
    """빈 병합 셀은 직전 값을 상속하고 짧은 행은 헤더 길이에 맞춘다."""
    table = [["사업", "회사", "금액"], ["반도체", "삼성전자", "100"], ["", "SK하이닉스"]]

    assert tableToRowDicts(table) == [
        {"사업": "반도체", "회사": "삼성전자", "금액": "100"},
        {"사업": "반도체", "회사": "SK하이닉스", "금액": "100"},
    ]


@pytest.mark.parametrize(
    ("cell", "expected"),
    [
        ("18.5%", 18.5),
        ("100%", 100.0),
        ("0.0%", 0.0),
        ("1,234.5%", 1234.5),
    ],
)
def testParsePercentReturnsHundredScaleNotFraction(cell: str, expected: float) -> None:
    """0~100 스케일이다. 0~1 로 바뀌면 호출자 계산이 100 배 틀어진다."""

    assert parsePercent(cell) == expected


@pytest.mark.parametrize("cell", ["", "-", "   "])
def testParsePercentReturnsNoneForAbsentValues(cell: str) -> None:
    """비중 미기재도 0% 가 아니라 값 없음이다."""

    assert parsePercent(cell) is None


def testExtractCorpNamesSplitsOnCommaAndConjunction() -> None:
    """한 셀에 여러 거래처가 들어온다. 쉼표와 접속어 둘 다 구분자다."""

    assert extractCorpNames("삼성전자, LG전자") == ["삼성전자", "LG전자"]
    assert extractCorpNames("삼성전자 및 LG전자") == ["삼성전자", "LG전자"]


def testExtractCorpNamesDropsTrailingEtcAndParenthetical() -> None:
    """`등` 과 끝 괄호 주석은 회사 이름이 아니다."""

    assert extractCorpNames("삼성전자 등") == ["삼성전자"]
    assert extractCorpNames("삼성전자(주요 매입처)") == ["삼성전자"]


def testExtractCorpNamesDropsSingleCharacterFragments() -> None:
    """한 글자짜리 조각은 회사 이름으로 세지 않는다."""

    assert extractCorpNames("A, 삼성전자") == ["삼성전자"]


def testExtractCorpNamesReturnsEmptyForBlankCell() -> None:
    """빈 셀은 빈 목록이다. 빈 이름 하나를 만들어내면 안 된다."""

    assert extractCorpNames("") == []
    assert extractCorpNames("   ") == []


@pytest.mark.parametrize(
    ("raw", "expected"),
    [
        ("㈜삼성전자", "삼성전자"),
        ("(주)삼성전자", "삼성전자"),
        ("주식회사 삼성전자", "삼성전자"),
        ("삼성전자", "삼성전자"),
        ("  삼성전자  ", "삼성전자"),
    ],
)
def testNormalizeCorpNameStripsLegalFormForMatching(raw: str, expected: str) -> None:
    """법인 표기가 달라도 같은 회사로 이어져야 그래프 간선이 끊기지 않는다."""

    assert normalizeCorpName(raw) == expected


def testNormalizeCorpNameReturnsEmptyStringForBlank() -> None:
    """빈 입력은 빈 문자열이다. 호출자가 None 처리를 따로 하지 않아도 된다."""

    assert normalizeCorpName("") == ""


def testFindTableByHeadersMatchesPartialKeywords() -> None:
    """헤더는 부분 일치다. 표기가 조금 달라도 같은 표를 찾아야 한다."""

    table = [["매입처명", "매입비중(%)"], ["삼성전자", "18.5"]]
    found = findTableByHeaders([table], ["매입처", "비중"])

    assert found is not None
    assert found[0] is table
    assert found[1] == 0


def testFindTableByHeadersSkipsUnitMetaRowAboveTheHeader() -> None:
    """DART 표는 첫 줄에 단위 안내가 오는 일이 잦다. 그 아래를 헤더로 봐야 한다."""

    table = [["(단위: 억원)"], ["매입처명", "매입비중(%)"], ["삼성전자", "18.5"]]
    found = findTableByHeaders([table], ["매입처", "비중"])

    assert found is not None
    assert found[1] == 1


def testFindTableByHeadersReturnsNoneWhenAnyKeywordIsMissing() -> None:
    """키워드 하나라도 없으면 다른 표다. 부분 일치로 엉뚱한 표를 집으면 안 된다."""

    table = [["매입처명", "금액"], ["삼성전자", "138,272"]]

    assert findTableByHeaders([table], ["매입처", "비중"]) is None


def testFindTableByHeadersReturnsNoneForEmptyInput() -> None:
    """표가 없으면 없음이다."""

    assert findTableByHeaders([], ["매입처"]) is None
