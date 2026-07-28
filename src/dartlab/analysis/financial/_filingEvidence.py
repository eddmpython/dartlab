"""공시 근거 정규화 primitive SSOT. 8 자리 날짜 텍스트 검증과 근거 ref 수집.

DART filing feature 어댑터와 EDGAR filing feature 어댑터가 같은 날짜 검증 여덟 줄을,
EDGAR feature 어댑터와 simulate 상태 어댑터가 같은 근거 ref 수집 다섯 줄을 각자 갖고
있었다. 근거 ref 는 feature envelope 의 identity 에 들어가므로, 한쪽만 고치면 같은
공시에서 뽑은 같은 값이 서로 다른 identity 로 굳는다.

날짜 규약: 하이픈을 걷어낸 ``YYYYMMDD`` 8 자리만 통과한다. 자릿수·숫자 여부·실재 날짜
셋을 모두 보고, 하나라도 어긋나면 label 을 붙인 ``ValueError`` 를 던진다. 조용히 None
으로 바꾸지 않는 이유는 이 값이 point-in-time 컷오프라서, 못 읽은 날짜를 넘기면 미래
정보가 과거 관측에 섞이기 때문이다.

``edgarPitState._dateText`` 는 이름만 같은 다른 함수다 (label 인자가 없다). 합치면
오류 메시지가 달라지므로 그대로 둔다.
"""

from __future__ import annotations

from datetime import date
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from dartlab.analysis.financial.edgarPitState import (
        CompiledQuarterlyFinancialState,
        CompiledQuarterlyFlowState,
        CompiledQuarterlyRevenueState,
    )


def _dateText(value: str, label: str) -> str:
    """``YYYYMMDD`` 8 자리로 정규화한다. 형식이나 실재 날짜가 어긋나면 ValueError."""
    text = str(value).replace("-", "")
    if len(text) != 8 or not text.isdigit():
        raise ValueError(f"invalid {label}: {value}")
    try:
        date(int(text[:4]), int(text[4:6]), int(text[6:8]))
    except ValueError as error:
        raise ValueError(f"invalid {label}: {value}") from error
    return text


def _sourceRefs(
    compiled: (CompiledQuarterlyFinancialState | CompiledQuarterlyFlowState | CompiledQuarterlyRevenueState),
) -> tuple[str, ...]:
    """컴파일된 분기 상태의 근거를 정렬된 ref 튜플로 편다. 파생 입력도 함께 담는다."""
    refs = set()
    for item in compiled.evidence:
        refs.add(f"{item.accession}|{item.tag}|{item.fiscalStart}|{item.fiscalEnd}|{item.status}")
        refs.update(item.derivationInputs)
    return tuple(sorted(refs))
