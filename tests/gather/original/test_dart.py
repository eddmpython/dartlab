"""gather.original.dart: archiveDartOriginals unit 테스트 (네트워크 0)."""

from __future__ import annotations

import pytest

pytestmark = pytest.mark.unit

_PERIODIC = {
    "corp_cls": "Y",
    "stock_code": "005930",
    "report_nm": "사업보고서 (2025.12)",
    "rcept_no": "20260601000001",
}
_NONPERIODIC = {
    "corp_cls": "Y",
    "stock_code": "005930",
    "report_nm": "주요사항보고서(유상증자결정)",
    "rcept_no": "20260601000002",
}


class _FakeClient:
    """DartClient 흉내. 한 날짜에 정기 1 + 비정기 1, getBytes 는 유효 zip."""

    def __init__(self, *_, **__):
        self.byteCalls = 0

    def getJson(self, endpoint, params=None, *, emptyOn013=False):
        assert endpoint == "list.json" and emptyOn013
        if params["page_no"] == "1":
            return {"status": "000", "list": [_PERIODIC, _NONPERIODIC], "total_page": 1}
        return {}

    def getBytes(self, endpoint, params=None):
        self.byteCalls += 1
        return b"PK\x03\x04" + b"\x00" * 100


def test_iterDays_and_isPeriodic() -> None:
    """_iterDays 내림차순 + _isPeriodic 정기보고서 판정."""
    from dartlab.gather.original import dart as collect

    assert collect._iterDays("20260601", "20260603") == ["20260603", "20260602", "20260601"]
    assert collect._isPeriodic("반기보고서 (2025.06)") is True
    assert collect._isPeriodic("주요사항보고서") is False


def test_archive_splits_docs_and_allFilings(monkeypatch: pytest.MonkeyPatch, tmp_path) -> None:
    """정기→docs/ · 비정기→allFilings/ 분리 저장 + 유효 zip(PK magic)."""
    import dartlab.config as cfg
    from dartlab.gather.original import dart as collect
    from dartlab.gather.original import paths

    monkeypatch.setattr(cfg, "dataDir", str(tmp_path))
    monkeypatch.setattr(collect, "DartClient", _FakeClient)

    stats = collect.archiveDartOriginals("20260601", "20260601", scope="all", showProgress=False)

    docsZip = paths.dartDocsDir("005930") / "20260601000001.zip"
    miscZip = paths.dartFilingsDir("005930") / "20260601000002.zip"
    assert docsZip.exists() and miscZip.exists()
    assert docsZip.read_bytes()[:4] == b"PK\x03\x04"
    assert stats["ok"] == 2 and stats["error"] == 0


def test_archive_idempotent_skip(monkeypatch: pytest.MonkeyPatch, tmp_path) -> None:
    """재실행 시 기존 zip skip (수집 0)."""
    import dartlab.config as cfg
    from dartlab.gather.original import dart as collect

    monkeypatch.setattr(cfg, "dataDir", str(tmp_path))
    monkeypatch.setattr(collect, "DartClient", _FakeClient)

    collect.archiveDartOriginals("20260601", "20260601", scope="all", showProgress=False)
    stats2 = collect.archiveDartOriginals("20260601", "20260601", scope="all", showProgress=False)
    assert stats2["ok"] == 0 and stats2["skipped"] == 2


class _FakeClientPartialFail:
    """정기(005930)는 본문부재(014), 비정기(000660)는 유효 zip — changed 마킹 분기 검증용."""

    _FAIL_RCEPT = "20260601000001"

    def __init__(self, *_, **__):
        pass

    def getJson(self, endpoint, params=None, *, emptyOn013=False):
        if params["page_no"] == "1":
            rowA = {**_PERIODIC, "stock_code": "005930", "rcept_no": self._FAIL_RCEPT}
            rowB = {**_NONPERIODIC, "stock_code": "000660", "rcept_no": "20260601000002"}
            return {"status": "000", "list": [rowA, rowB], "total_page": 1}
        return {}

    def getBytes(self, endpoint, params=None):
        if (params or {}).get("rcept_no") == self._FAIL_RCEPT:
            return b"<status>014</status>"  # 본문부재 → no_body, zip 미작성
        return b"PK\x03\x04" + b"\x00" * 100


def test_changed_codes_only_on_successful_write(monkeypatch: pytest.MonkeyPatch, tmp_path) -> None:
    """changedCodes 는 zip 이 *실제로 써진* 종목만 — fetch 실패(no_body) 종목 제외.

    회귀 가드: 큐잉 시점 마킹이면 일시 fetch 실패가 panel 재빌드+원본 tar 덮어쓰기를 유발(데이터 손실).
    """
    import dartlab.config as cfg
    from dartlab.gather.original import dart as collect

    monkeypatch.setattr(cfg, "dataDir", str(tmp_path))
    monkeypatch.setattr(collect, "DartClient", _FakeClientPartialFail)

    stats = collect.archiveDartOriginals("20260601", "20260601", scope="all", showProgress=False)

    assert stats["changedCodes"] == ["000660"]  # 005930(no_body)은 제외
    assert stats["ok"] == 1 and stats["noBody"] == 1


def test_scope_nonperiodic_only(monkeypatch: pytest.MonkeyPatch, tmp_path) -> None:
    """scope=nonperiodic 면 비정기만 수집(정기 store 중복 0)."""
    import dartlab.config as cfg
    from dartlab.gather.original import dart as collect
    from dartlab.gather.original import paths

    monkeypatch.setattr(cfg, "dataDir", str(tmp_path))
    monkeypatch.setattr(collect, "DartClient", _FakeClient)

    collect.archiveDartOriginals("20260601", "20260601", scope="nonperiodic", showProgress=False)
    assert not (paths.dartDocsDir("005930") / "20260601000001.zip").exists()
    assert (paths.dartFilingsDir("005930") / "20260601000002.zip").exists()


def test_archive_uses_shared_dart_client() -> None:
    """원본 archive 는 전송·연결 재시도와 XML 상태 해석을 가진 공용 DartClient 를 쓴다.

    복제 client 는 재시도가 없어 응답 없는 끊김 한 번에 archive 가 죽었다(2026-10-02, 10-08, 10-11).
    """
    from dartlab.gather.dart.client import DartClient
    from dartlab.gather.original import dart as collect

    assert collect.DartClient is DartClient


def test_collect_day_rows_pages_filters_and_stops_on_013() -> None:
    """total_page 까지 페이지를 넘기고 corp_cls 로 거르며, 013(결과 없음)은 빈 dict 로 와서 빈 list."""
    from dartlab.gather.original import dart as collect

    class _Pages:
        def __init__(self):
            self.pages = []

        def getJson(self, endpoint, params=None, *, emptyOn013=False):
            self.pages.append(params["page_no"])
            cls = "Y" if params["page_no"] == "1" else "E"
            return {
                "status": "000",
                "list": [{**_PERIODIC, "rcept_no": params["page_no"], "corp_cls": cls}],
                "total_page": 2,
            }

    client = _Pages()
    rows = collect._collectDayRows(client, "20260601", {"Y"})
    assert client.pages == ["1", "2"]
    assert [row["rcept_no"] for row in rows] == ["1"]

    class _Empty:
        def getJson(self, endpoint, params=None, *, emptyOn013=False):
            return {}

    assert collect._collectDayRows(_Empty(), "20260606", {"Y"}) == []
