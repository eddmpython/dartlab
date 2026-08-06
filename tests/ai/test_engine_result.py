"""판정 엔진 결과가 읽을 본문과 인용할 근거로 펴지는지 지키는 계약.

실측(2026-08-06). `Company.panel` 은 본문 1810 자를 건네는데 `Company.analysis` 와
`Company.quant` 와 `Company.credit` 은 본문이 0 자였다. 요약은 "실행 완료" 다섯 글자이고
내용은 9184 자짜리 중첩 dict 였다. 같은 배터리에서 panel 경로 답변은 근거 39 건, analysis
경로 답변은 3226 자를 쓰고도 근거 3 건에 인용 2 건이었다.

여기서 지키는 것은 셋이다. 표로 펼 수 있는 것은 표로 편다. 본문에 그린 표는 반드시
인용할 근거가 함께 나온다. 그리고 지어내지 않는다.
"""

from __future__ import annotations

from typing import Any

import pytest

from dartlab.ai.tools.engineResult import engineResultMarkdown, engineResultRefs, frameMarkdown

pytestmark = pytest.mark.unit


def _historyPayload() -> dict[str, Any]:
    return {
        "accrualAnalysis": {
            "history": [
                {"period": "2025", "netIncome": 45.2e12, "ocfToNi": 188.72},
                {"period": "2024", "netIncome": 34.5e12, "ocfToNi": 211.84},
            ]
        },
        "beneishMScore": {"status": "unavailable", "available": False, "interpretation": "입력 공통 의미 없음"},
        "assessmentStatus": "partial",
    }


def _periodMapPayload() -> dict[str, Any]:
    return {
        "stockCode": "005930",
        "opIncomeHistory": {"2025": 43.6e12, "2024": 32.7e12, "2023": 15.5e12},
        "peadSignal": "none",
        "earningsTrend": "mostly_growing",
    }


def test기간별행목록이표가된다() -> None:
    """블록마다 history 배열을 가진 것이 판정 엔진의 공통 모양이다."""
    body = engineResultMarkdown("Company.analysis", "005930", _historyPayload())

    assert "### accrualAnalysis" in body
    assert "| 지표 | 2025 | 2024 |" in body
    assert "45.2조원" in body


def test기간키맵도표가된다() -> None:
    """엔진마다 시계열을 {기간: 값} 으로도 준다. 한 모양만 받으면 나머지는 dict 로 남는다."""
    body = engineResultMarkdown("Company.quant", "005930", _periodMapPayload())

    assert "### opIncomeHistory" in body
    assert "| 기간 | 2025 | 2024 | 2023 |" in body
    assert "43.6조원" in body


def test최상위스칼라가본문에온다() -> None:
    """판정 엔진은 신호와 강도를 최상위 스칼라로 담아 보낸다. 그게 결론이다."""
    body = engineResultMarkdown("Company.quant", "005930", _periodMapPayload())

    assert "peadSignal none" in body
    assert "earningsTrend mostly_growing" in body


def test못재는것을못잰다고적는다() -> None:
    """빈칸을 지우면 모델이 그 자리를 상상으로 채운다. 없다고 적는 편이 낫다."""
    body = engineResultMarkdown("Company.analysis", "005930", _historyPayload())

    assert "beneishMScore" in body
    assert "unavailable" in body


def test본문에그린표는인용할근거가있다() -> None:
    """본문만 주고 근거를 안 주면 답변은 읽히되 인용되지 않는다."""
    payload = _historyPayload()
    body = engineResultMarkdown("analysis.이익품질", "005930", payload)
    refs = engineResultRefs("analysis.이익품질", "005930", payload)

    drawn = {name for name in payload if f"### {name}" in body}
    cited = {str(ref.payload.get("block")) for ref in refs}
    assert drawn
    assert drawn <= cited


def test근거는회사별로구분된다() -> None:
    """한 세션에서 두 회사를 물으면 같은 id 가 서로를 덮어쓴다."""
    first = engineResultRefs("analysis.이익품질", "005930", _historyPayload())
    second = engineResultRefs("analysis.이익품질", "000660", _historyPayload())

    assert {ref.id for ref in first}.isdisjoint({ref.id for ref in second})


def test표가안되면근거도안만든다() -> None:
    """가리킬 표가 없는 근거는 인용해도 확인할 것이 없다."""
    payload = {"peadSignal": "none", "note": {"status": "ok"}}

    assert engineResultRefs("Company.quant", "005930", payload) == []
    assert "peadSignal none" in engineResultMarkdown("Company.quant", "005930", payload)


def test펼것이없으면빈문자열이다() -> None:
    """빈 제목만 남기면 소음이고 payload 예산만 먹는다."""
    assert engineResultMarkdown("Company.quant", "005930", {}) == ""
    assert engineResultMarkdown("Company.quant", "005930", None) == ""
    assert engineResultRefs("Company.quant", "005930", None) == []


def test본문에상한이있다() -> None:
    """소비하는 CLI 상한을 넘기면 잘리는 게 아니라 결과 전체가 버려진다."""
    huge = {
        f"block{index}": {"history": [{"period": str(2000 + step), "value": step * 1.5} for step in range(30)]}
        for index in range(60)
    }
    body = engineResultMarkdown("Company.analysis", "005930", huge)

    assert len(body) <= 6200
    assert "여기서 끊었습니다" in body


def test표제목에인용할이름이적힌다() -> None:
    """가리킬 이름을 눈앞에 두지 않으면 인용은 비싼 일이 된다. 실측에서 표 이름만 쓰고
    인용은 못 했다."""
    payload = _historyPayload()
    body = engineResultMarkdown("analysis.이익품질", "005930", payload)
    refs = engineResultRefs("analysis.이익품질", "005930", payload)

    assert refs
    for ref in refs:
        assert ref.id in body


def _framePayload() -> dict[str, Any]:
    return {
        "_type": "DataFrame",
        "rowCount": 40,
        "columns": ["axis", "label", "example"],
        "rows": [
            {"axis": "grade", "label": "등급", "example": 'c.credit("등급")'},
            {"axis": "liquidity", "label": "유동성", "example": 'c.credit("유동성")'},
        ],
    }


def test격자결과가표가된다() -> None:
    """옛 계약은 행 수와 열 이름만 줘서 값이 하나도 보이지 않았다. 축 목록조차 못 봤다."""
    body = frameMarkdown("Company.credit", "005930", _framePayload())

    assert "| axis | label | example |" in body
    assert "유동성" in body


def test보인행수를밝힌다() -> None:
    """일부만 보여 주고 전부인 척하면 모델이 없는 종목을 없다고 단정한다."""
    body = frameMarkdown("Company.credit", "005930", _framePayload())

    assert "전체 40행 중 2행만" in body


def test행이없으면빈문자열이다() -> None:
    """빈 표를 그리면 소음이고 payload 예산만 먹는다."""
    assert frameMarkdown("Company.credit", "005930", {"columns": ["a"], "rows": []}) == ""
    assert frameMarkdown("Company.credit", "005930", None) == ""


def test잘라낸기간을밝힌다() -> None:
    """조용히 자르면 모델이 보인 것을 전부로 읽고 없는 것을 없다고 단정한다."""
    payload = {
        "block": {"history": [{"period": str(2016 + step), "value": float(step)} for step in range(10)]},
    }

    body = engineResultMarkdown("Company.analysis", "005930", payload)

    assert "기간 10 개 중 8 개만 보였습니다" in body


def test잘라낸지표를밝힌다() -> None:
    """지표 스무 개 중 여덟 개만 보이면 나머지가 없는 것으로 읽힌다."""
    payload = {
        "block": {"history": [{"period": "2025", **{f"m{index}": float(index) for index in range(20)}}]},
    }

    body = engineResultMarkdown("Company.analysis", "005930", payload)

    assert "지표 20 개 중 8 개만 보였습니다" in body


def test잘라낸스칼라를밝힌다() -> None:
    """판정 엔진은 결론을 최상위 스칼라에 담는다. 말없이 버리면 결론이 사라진다."""
    payload = {f"signal{index}": f"value{index}" for index in range(25)}

    body = engineResultMarkdown("Company.quant", "005930", payload)

    assert "값 25 개 중 16 개만 보였습니다" in body


def test잘라낸열을밝힌다() -> None:
    """열이 잘리면 그 열의 종목이 조건을 안 만족한 것으로 읽힌다."""
    columns = [f"c{index}" for index in range(15)]
    payload = {"rowCount": 2, "columns": columns, "rows": [dict.fromkeys(columns, 1), dict.fromkeys(columns, 2)]}

    body = frameMarkdown("scan.growth", "", payload)

    assert "열 15 개 중 8 개만 보였습니다" in body
