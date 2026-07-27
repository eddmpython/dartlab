"""결과 봉투 안에서 증적끼리 말이 어긋나던 것에 대한 회귀.

부분 결과를 안 받겠다는 요청(`requireComplete`)에서 행은 버리면서 개수와 영수증은 남겨
뒀다. 그래서 partitions 가 비었는데 succeededPartitions 는 1 이고 실행 영수증도 한 장
붙은 결과가 나갔다. 같은 봉투 안에서 lineageRefs 와 qualityAssertions 는 비어 있고
성적표만 성공을 말하니 세 증적이 서로 다른 말을 했다. 그 옵션은 부분 답을 거절하려고
고르는 자리라 하필 거기서 어긋났다.

universe resolver 가 망가졌을 때는 systemic 표시가 빠져 있었다. 시장 전체가 안 나오는
사건인데 다른 asset 하나가 성공했다는 이유로 partial 로 내려갔다. 형제 실패 경로는 전부
systemic 을 다는데 그 한 줄만 빠졌다.

resolver 예외는 문구 전체를 code 로 썼다. code 공간이 무한해지고 로컬 경로 같은 내부
사정이 공개 결과에 실려 나갔다.
"""

from __future__ import annotations

import polars as pl
import pytest

from dartlab.dataHub.catalog import universe as universeModule
from dartlab.dataHub.contracts import DataQuery, DataRequest, UniverseSelection
from dartlab.dataHub.execution import executeDataQuery

pytestmark = [pytest.mark.unit]


def _query(completeness: str = "allowPartial") -> DataQuery:
    return DataQuery(
        requests=(
            DataRequest("scan.ratio", "good", measures=("roe",)),
            DataRequest("does.notexist", "bad"),
        ),
        completeness=completeness,
    )


def _run(completeness: str):
    return executeDataQuery(["scan.ratio", "does.notexist"], _query(completeness))


@pytest.mark.parametrize("completeness", ["requireComplete", "allowPartial"])
def testCoverageMatchesTheRowsActuallyReturned(completeness: str) -> None:
    """성적표는 돌려준 행을 세야 한다. 버린 행을 세면 안 된다."""

    result = _run(completeness)

    assert result.coverage.succeededPartitions == len(result.partitions)


def testDiscardedPartitionsLeaveNoReceipt() -> None:
    """행을 버렸으면 그 행에서 나온 영수증도 같이 버린다."""

    result = _run("requireComplete")

    assert result.status == "failed"
    assert result.partitions == ()
    assert result.executionReceipts == ()


def testAllProvenanceChannelsAgree() -> None:
    """성적표, 영수증, lineage, 품질단언이 한 봉투 안에서 같은 말을 해야 한다."""

    result = _run("requireComplete")

    assert result.coverage.succeededPartitions == 0
    assert result.executionReceipts == ()
    assert result.lineageRefs == ()
    assert result.qualityAssertions == ()


def testPartialRunStillReturnsItsRowsAndReceipts() -> None:
    """완전성을 요구하지 않은 요청까지 비우면 안 된다."""

    result = _run("allowPartial")

    assert result.status == "partial"
    assert len(result.partitions) > 0
    assert len(result.executionReceipts) > 0


def testBrokenResolverIsSystemic(monkeypatch: pytest.MonkeyPatch) -> None:
    """시장 전체가 안 나오는 사건은 한 종목의 결손과 등급이 다르다."""

    def _badSchema(**kwargs):
        return pl.DataFrame({"wrongColumn": ["005930"]})

    monkeypatch.setattr(universeModule, "_resolverSpec", lambda *a, **k: {"module": "x", "attribute": "y"})
    monkeypatch.setattr(universeModule.importlib, "import_module", lambda name: type("M", (), {"y": _badSchema}))

    _resolved, gap = universeModule._loadMembership(UniverseSelection(markets=("KR",)), "KR")

    assert gap is not None
    assert gap.systemic is True


def testResolverExceptionTextDoesNotBecomeTheCode(monkeypatch: pytest.MonkeyPatch) -> None:
    """code 는 기계가 읽는 자리다. 경로도 문장도 거기 실리면 안 된다."""

    def _boom(**kwargs):
        raise ValueError("UNIVERSE_MARKET_UNSUPPORTED: C:/some/local/path.parquet 가 없습니다")

    monkeypatch.setattr(universeModule, "_resolverSpec", lambda *a, **k: {"module": "x", "attribute": "y"})
    monkeypatch.setattr(universeModule.importlib, "import_module", lambda name: type("M", (), {"y": _boom}))

    _resolved, gap = universeModule._loadMembership(UniverseSelection(markets=("KR",)), "KR")

    assert gap is not None
    assert gap.code == "UNIVERSE_MARKET_UNSUPPORTED"
    assert ":" not in gap.code
    assert "path.parquet" in gap.message


def testUnknownResolverFailureFallsBackToTheFixedCode(monkeypatch: pytest.MonkeyPatch) -> None:
    """정해진 code 가 아니면 하나로 모은다. code 공간이 무한해지면 안 된다."""

    def _boom(**kwargs):
        raise RuntimeError("무슨 일인지 모를 실패: 자세한 사정")

    monkeypatch.setattr(universeModule, "_resolverSpec", lambda *a, **k: {"module": "x", "attribute": "y"})
    monkeypatch.setattr(universeModule.importlib, "import_module", lambda name: type("M", (), {"y": _boom}))

    _resolved, gap = universeModule._loadMembership(UniverseSelection(markets=("KR",)), "KR")

    assert gap is not None
    assert gap.code == "UNIVERSE_RESOLUTION_FAILED"
