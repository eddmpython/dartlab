"""전종목 스캔의 행 순서 결정성에 대한 회귀.

`dartlab.scan("ratio", "roe")` 를 두 번 부르면 같은 2,812 행이 매번 다른 순서로 나왔다.
정렬하면 완전히 같으므로 내용은 같고 순서만 흔들린 것이다. 원인은 `scanAccount` 의
group_by 와 pivot, 그리고 비율 계산의 join 이다. polars 는 이 셋을 병렬로 처리하며 행
순서를 보장하지 않는다.

두 가지가 걸린다. 첫째, 사용자가 보는 전종목 표가 실행마다 섞인다. 둘째, 그 위에 얹힌
content seal 이 같은 내용에 매번 다른 식별자를 붙인다. 내용이 같으면 같은 식별자라는 것이
seal 의 존재 이유이고, dataHub 는 그 식별자로 세대 재사용과 replay 검증을 한다. 봉인이
매번 바뀌면 재사용은 영영 성립하지 않고, 검증은 항상 불일치를 보고한다.

종목코드 오름차순은 정본 순서다. 문서의 예제들이 전부 `.sort("2025", descending=True)` 처럼
호출자 쪽에서 다시 정렬하므로, 원본 순서에 의미가 실려 있지 않다.
"""

from __future__ import annotations

import pytest

import dartlab

pytestmark = [pytest.mark.realData]

_AXES = [("ratio", "roe"), ("ratio", "revenueGrowth"), ("ratio", "debtRatio"), ("account", "sales")]


@pytest.mark.parametrize(("axis", "target"), _AXES)
def testRowOrderIsStableAcrossRuns(axis: str, target: str) -> None:
    """결함의 핵심이다. 같은 질의는 같은 순서로 나와야 한다."""

    first = dartlab.scan(axis, target)
    second = dartlab.scan(axis, target)
    key = first.columns[0]

    assert first[key].to_list() == second[key].to_list()


@pytest.mark.parametrize(("axis", "target"), _AXES)
def testRowsAreSortedByStockCode(axis: str, target: str) -> None:
    """정본 순서를 못 박는다. 안 그러면 안정적이지만 임의인 순서가 굳는다."""

    frame = dartlab.scan(axis, target)
    codes = frame[frame.columns[0]].to_list()

    assert codes == sorted(codes)


def testContentIsUnchangedByTheOrdering() -> None:
    """정렬을 넣느라 행을 잃거나 더하면 안 된다."""

    frame = dartlab.scan("ratio", "roe")

    assert frame.height > 1000
    assert frame[frame.columns[0]].n_unique() == frame.height


def testContentSealIsStableForIdenticalContent() -> None:
    """봉인은 같은 내용에 같은 식별자를 붙여야 한다. 그것이 존재 이유다."""

    from dartlab.dataHub.contracts import DataQuery, DataRequest
    from dartlab.dataHub.execution import executeDataQuery

    query = DataQuery(requests=(DataRequest("scan.ratio", "s", measures=("roe",)),))
    first = executeDataQuery(["scan.ratio"], query)
    second = executeDataQuery(["scan.ratio"], query)

    assert first.partitions and second.partitions
    assert first.partitions[0].contentHash == second.partitions[0].contentHash
    assert first.dataSnapshotId == second.dataSnapshotId
    assert first.dataSnapshotId is not None
