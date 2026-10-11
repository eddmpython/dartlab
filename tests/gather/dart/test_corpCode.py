"""providers/dart/openapi/corpCode.py mirror smoke — P6."""

import pytest

pytestmark = pytest.mark.unit


def test_imports():
    try:
        import dartlab.gather.dart.corpCode  # noqa: F401
    except ImportError as e:
        pytest.skip(f"module import requires data/env: {e}")


def test_find_corp_code_callable() -> None:
    """findCorpCode() callable smoke."""
    from dartlab.gather.dart.corpCode import findCorpCode

    assert callable(findCorpCode)


def test_iter_companies_callable() -> None:
    """iterCompanies() callable smoke."""
    from dartlab.gather.dart.corpCode import iterCompanies

    assert callable(iterCompanies)


def test_load_corp_codes_callable() -> None:
    """loadCorpCodes() callable smoke."""
    from dartlab.gather.dart.corpCode import loadCorpCodes

    assert callable(loadCorpCodes)


def test_search_companies_callable() -> None:
    """searchCompanies() callable smoke."""
    from dartlab.gather.dart.corpCode import searchCompanies

    assert callable(searchCompanies)


class _StatusClient:
    """corpCode.xml 에 OpenDART 상태 본문을 돌려주는 가짜 client. 호출 수를 센다."""

    def __init__(self, status: str = "800") -> None:
        self.calls = 0
        self.body = f"<result><status>{status}</status><message>점검</message></result>".encode()

    def getBytes(self, endpoint, params=None):
        self.calls += 1
        return self.body


def _freshModule(monkeypatch):
    from dartlab.gather.dart import corpCode

    monkeypatch.setattr(corpCode, "_memCache", None)
    monkeypatch.setattr(corpCode, "_lastFailure", None)
    monkeypatch.setattr(corpCode, "_isCacheFresh", lambda: False)
    return corpCode


def test_download_surfaces_dart_status_instead_of_zip_error(monkeypatch) -> None:
    """ZIP 대신 온 상태 본문은 'ZIP 손상' 이 아니라 그 상태(800 점검 등)의 DartApiError 다."""
    from dartlab.core.dartClient import DartApiError

    corpCode = _freshModule(monkeypatch)
    with pytest.raises(DartApiError) as excInfo:
        corpCode.loadCorpCodes(_StatusClient("800"))
    assert excInfo.value.status == "800"
    assert "corpCode.xml 다운로드 실패" in str(excInfo.value)


def test_load_corp_codes_memoizes_recent_failure(monkeypatch) -> None:
    """실패 직후 다시 불러도 다시 받지 않는다(점검 중 run 하나에서 112 회 요청하던 경로)."""
    from dartlab.core.dartClient import DartApiError

    corpCode = _freshModule(monkeypatch)
    client = _StatusClient("020")
    for _ in range(5):
        with pytest.raises(DartApiError):
            corpCode.loadCorpCodes(client)
    assert client.calls == 1


def test_load_corp_codes_retries_after_failure_memo_expires(monkeypatch) -> None:
    from dartlab.core.dartClient import DartApiError

    corpCode = _freshModule(monkeypatch)
    client = _StatusClient("800")
    with pytest.raises(DartApiError):
        corpCode.loadCorpCodes(client)
    monkeypatch.setattr(corpCode, "_lastFailure", (corpCode._lastFailure[0] - corpCode._FAILURE_MEMO_SEC - 1, None))
    with pytest.raises(DartApiError):
        corpCode.loadCorpCodes(client)
    assert client.calls == 2
