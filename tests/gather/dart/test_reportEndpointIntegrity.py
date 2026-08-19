"""report 엔드포인트 매핑 무결성 + 카테고리 격리 회귀 가드.

2026-08 사고 회귀 차단. 정기보고서 수집이 5 일간 진전 0 이었던 원인 둘을 고정한다.

1. `_REPORT_ENDPOINTS` 가 `batch.py` 와 `dart.py` 두 곳에 복제되어 있었고 실제 수집 경로인
   `batch.py` 쪽에서만 철자가 썩었다 (`Scrits` -> `Scrts`). 복제본이 다시 갈라지면 여기서 깨진다.
2. `_collectReport` 가 all-or-nothing 이라 엔드포인트 1 개의 장애가 앞서 모은 카테고리 전체를
   폐기했다. 카테고리 격리가 풀리면 여기서 깨진다.
"""

from __future__ import annotations

import asyncio

import polars as pl
import pytest

from dartlab.core.dartClient import DartApiError

pytestmark = pytest.mark.unit

# 실제 OpenDART 호출에서 [101] 잘못된 URL 로 확인된 이름들 (2026-08-19 실측).
# 되살아나면 그 카테고리 수집이 100% 실패한다.
_KNOWN_INVALID_ENDPOINTS = frozenset(
    {
        "eleStockIstySttus",
        "cndlCaplScrtsNrdmpBlce",
        "newCaplScrtsNrdmpBlce",
    }
)


def _mappings() -> tuple[dict[str, str], list[str], dict[str, str]]:
    from dartlab.gather.dart.batch import _PERIODIC_REPORT_CATEGORIES, _REPORT_ENDPOINTS
    from dartlab.gather.dart.dart import _REPORT_ENDPOINTS as _DART_ENDPOINTS

    return _REPORT_ENDPOINTS, _PERIODIC_REPORT_CATEGORIES, _DART_ENDPOINTS


def test_every_periodic_category_has_endpoint() -> None:
    """수집 대상 카테고리는 전부 엔드포인트 매핑을 가진다 (조용한 skip 차단)."""
    endpoints, categories, _ = _mappings()
    missing = [cat for cat in categories if not endpoints.get(cat)]
    assert missing == [], f"엔드포인트 매핑 누락: {missing}"


def test_no_known_invalid_endpoint_in_use() -> None:
    """실측으로 무효 확인된 엔드포인트가 수집 경로에 없다."""
    endpoints, categories, dartEndpoints = _mappings()
    used = {endpoints[cat] for cat in categories if endpoints.get(cat)}
    revived = sorted(used & _KNOWN_INVALID_ENDPOINTS)
    assert revived == [], f"무효 엔드포인트가 수집 경로에 복귀: {revived}"

    dartRevived = sorted(set(dartEndpoints.values()) & _KNOWN_INVALID_ENDPOINTS)
    assert dartRevived == [], f"무효 엔드포인트가 dart.py 매핑에 복귀: {dartRevived}"


def test_no_dead_label_for_invalid_endpoint() -> None:
    """무효 엔드포인트의 라벨·apiType 매핑도 남기지 않는다.

    `eleStockIstySttus` 는 한 번도 성공한 적이 없어 그 apiType 으로 저장된 데이터가 없다
    (2026-08-19 로컬 report parquet 38 개 표본에서 majorShareholderChange 0 건 확인).
    죽은 매핑을 남기면 다음 사람이 실재하는 수집 항목으로 오독한다.
    """
    from pathlib import Path as _Path

    # tests/gather/dart/<file> 기준 저장소 루트는 parents[3] 이다.
    root = _Path(__file__).resolve().parents[3]
    for rel in ("src/dartlab/core/dartConstants.py", "src/dartlab/providers/dart/build/saver.py"):
        text = (root / rel).read_text(encoding="utf-8")
        assert "eleStockIstySttus" not in text, f"{rel}: 무효 엔드포인트 라벨이 복귀했다"
        assert "majorShareholderChange" not in text, f"{rel}: 죽은 apiType 매핑이 복귀했다"


def test_duplicate_endpoint_tables_agree() -> None:
    """batch.py 와 dart.py 의 중복 매핑은 겹치는 키에서 값이 같아야 한다."""
    endpoints, _, dartEndpoints = _mappings()
    shared = set(endpoints) & set(dartEndpoints)
    assert shared, "두 매핑이 공유하는 키가 없다. 테스트 전제가 깨졌다"
    drift = {key: (endpoints[key], dartEndpoints[key]) for key in shared if endpoints[key] != dartEndpoints[key]}
    assert drift == {}, f"중복 매핑 불일치 (batch.py, dart.py): {drift}"


def _fakeClient(failingEndpoint: str | None, *, status: str = "101"):
    class _Client:
        exhausted = False

        async def getDf(self, path: str, params: dict[str, str]):
            if failingEndpoint and path.startswith(failingEndpoint):
                raise DartApiError(status, f"실패 주입(/api/{path})")
            return pl.DataFrame({"value": [1]})

    return _Client()


def _patchIo(monkeypatch, tmp_path, saved: dict[str, int]):
    monkeypatch.setattr(
        "dartlab.core.dartBuild.enrichReport",
        lambda df, stockCode, corpCode, cat, endpoint: df.with_columns(pl.lit(cat).alias("apiType")),
    )
    monkeypatch.setattr(
        "dartlab.core.dartBuild.saveReplacingByKeys",
        lambda df, path, keys: saved.__setitem__("height", df.height),
    )
    monkeypatch.setattr("dartlab.core.dartBuild.save", lambda df, path: saved.__setitem__("height", df.height))
    monkeypatch.setattr("dartlab.gather.dart.batch._dataPath", lambda category, stockCode: tmp_path / "x.parquet")


def _collect(client, **kwargs):
    from dartlab.gather.dart import batchCollectors

    return asyncio.run(
        batchCollectors._collectReport(
            "005930", "00126380", "삼성전자", client, incremental=False, targetPeriods=[("2024", "11011")], **kwargs
        )
    )


def _healthyCategoryCount() -> int:
    from dartlab.gather.dart.batch import _PERIODIC_REPORT_CATEGORIES, _REPORT_ENDPOINTS

    return len([c for c in _PERIODIC_REPORT_CATEGORIES if _REPORT_ENDPOINTS.get(c)])


def test_one_broken_endpoint_does_not_discard_other_categories(monkeypatch, tmp_path) -> None:
    """카테고리 1 개가 [101] 로 죽어도 나머지 카테고리 수집분은 저장된다."""
    from dartlab.gather.dart import batchCollectors
    from dartlab.gather.dart.batch import _PERIODIC_REPORT_CATEGORIES, _REPORT_ENDPOINTS

    victimEndpoint = _REPORT_ENDPOINTS[_PERIODIC_REPORT_CATEGORIES[0]]
    saved: dict[str, int] = {}
    _patchIo(monkeypatch, tmp_path, saved)

    with pytest.raises(batchCollectors.PartialReportError):
        _collect(_fakeClient(victimEndpoint))

    expected = _healthyCategoryCount() - 1
    assert saved.get("height") == expected, f"깨진 카테고리 1 개 때문에 나머지가 버려졌다 (저장={saved.get('height')})"


def test_partial_failure_stays_in_retry_ledger(monkeypatch, tmp_path) -> None:
    """부분 실패는 저장 후에도 예외로 알려 failures 원장에 남는다.

    조용히 성공으로 끝내면 이 종목의 rcept_no 가 심어져 누락 검사에서 빠지고, 죽은
    카테고리가 재수집 트리거 없이 영구 구멍이 된다. 상위 batchWorker 가 잡을 수 있도록
    RuntimeError 계열이어야 한다.
    """
    from dartlab.gather.dart import batchCollectors
    from dartlab.gather.dart.batch import _PERIODIC_REPORT_CATEGORIES, _REPORT_ENDPOINTS

    assert issubclass(batchCollectors.PartialReportError, RuntimeError)

    victimEndpoint = _REPORT_ENDPOINTS[_PERIODIC_REPORT_CATEGORIES[0]]
    saved: dict[str, int] = {}
    _patchIo(monkeypatch, tmp_path, saved)

    with pytest.raises(batchCollectors.PartialReportError) as excinfo:
        _collect(_fakeClient(victimEndpoint))
    assert _PERIODIC_REPORT_CATEGORIES[0] in str(excinfo.value)


def test_all_categories_healthy_does_not_raise(monkeypatch, tmp_path) -> None:
    """실패가 없으면 예외 없이 저장 행수를 반환한다 (정상 경로 오탐 차단)."""
    saved: dict[str, int] = {}
    _patchIo(monkeypatch, tmp_path, saved)

    rows = _collect(_fakeClient(None))
    assert rows == _healthyCategoryCount()
    assert saved.get("height") == rows


def test_json_decode_failure_is_isolated_not_total_loss(monkeypatch, tmp_path) -> None:
    """DART 가 HTTP 200 으로 HTML 을 주는 경우(JSONDecodeError)도 카테고리 단위로 격리된다."""
    import json

    from dartlab.gather.dart import batchCollectors
    from dartlab.gather.dart.batch import _PERIODIC_REPORT_CATEGORIES, _REPORT_ENDPOINTS

    victimEndpoint = _REPORT_ENDPOINTS[_PERIODIC_REPORT_CATEGORIES[0]]
    saved: dict[str, int] = {}
    _patchIo(monkeypatch, tmp_path, saved)

    class _HtmlClient:
        exhausted = False

        async def getDf(self, path: str, params: dict[str, str]):
            if path.startswith(victimEndpoint):
                raise json.JSONDecodeError("Expecting value", "<html>점검중</html>", 0)
            return pl.DataFrame({"value": [1]})

    with pytest.raises(batchCollectors.PartialReportError):
        _collect(_HtmlClient())
    assert saved.get("height") == _healthyCategoryCount() - 1


@pytest.mark.parametrize("status", ["010", "011", "012", "020", "021"])
def test_account_level_dart_errors_propagate(monkeypatch, tmp_path, status: str) -> None:
    """키·IP·한도 사유는 카테고리 문제가 아니므로 격리하지 않고 즉시 전파한다."""
    from dartlab.gather.dart.batch import _PERIODIC_REPORT_CATEGORIES, _REPORT_ENDPOINTS

    victimEndpoint = _REPORT_ENDPOINTS[_PERIODIC_REPORT_CATEGORIES[0]]
    saved: dict[str, int] = {}
    _patchIo(monkeypatch, tmp_path, saved)

    with pytest.raises(DartApiError) as excinfo:
        _collect(_fakeClient(victimEndpoint, status=status))
    assert excinfo.value.status == status


def test_quota_exhaustion_still_propagates(monkeypatch, tmp_path) -> None:
    """API 한도 초과([020])는 격리하지 않고 그대로 전파한다 (다음 실행 재개 신호)."""
    from dartlab.gather.dart import batchCollectors

    class _Exhausted:
        exhausted = True

        async def getDf(self, path: str, params: dict[str, str]):  # pragma: no cover
            raise AssertionError("한도 초과 상태에서는 호출되지 않아야 한다")

    monkeypatch.setattr("dartlab.gather.dart.batch._dataPath", lambda category, stockCode: tmp_path / "x.parquet")

    with pytest.raises(DartApiError) as excinfo:
        asyncio.run(
            batchCollectors._collectReport(
                "005930",
                "00126380",
                "삼성전자",
                _Exhausted(),
                incremental=False,
                targetPeriods=[("2024", "11011")],
            )
        )
    assert excinfo.value.status == "020"
