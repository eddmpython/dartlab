"""providers/dart/openapi/allFilingsCollector.py mirror smoke — P6."""

import polars as pl
import pytest

pytestmark = pytest.mark.unit


def test_imports():
    try:
        import dartlab.gather.dart.allFilingsCollector  # noqa: F401
    except ImportError as e:
        pytest.skip(f"module import requires data/env: {e}")


def test_collect_meta_day_callable() -> None:
    """collectMetaDay() callable smoke."""
    from dartlab.gather.dart.allFilingsCollector import collectMetaDay

    assert callable(collectMetaDay)


def test_collect_meta_range_callable() -> None:
    """collectMetaRange() callable smoke."""
    from dartlab.gather.dart.allFilingsCollector import collectMetaRange

    assert callable(collectMetaRange)


def test_collected_dates_callable() -> None:
    """collectedDates() callable smoke."""
    from dartlab.gather.dart.allFilingsCollector import collectedDates

    assert callable(collectedDates)


def test_fill_content_callable() -> None:
    """fillContent() callable smoke."""
    from dartlab.gather.dart.allFilingsCollector import fillContent

    assert callable(fillContent)


def test_fill_content_all_callable() -> None:
    """fillContentAll() callable smoke."""
    from dartlab.gather.dart.allFilingsCollector import fillContentAll

    assert callable(fillContentAll)


def test_fill_content_all_preserves_failure_type_and_date_provenance(monkeypatch) -> None:
    """부분 완료 건수를 반환해 실패를 숨기지 않고 원래 예외와 실패 일자를 전달한다."""
    from dartlab.gather.dart import allFilingsCollector as mod

    monkeypatch.setattr(mod, "pendingDates", lambda: ["20260527", "20260528"])

    def failOnSecondDate(date, **_kwargs):
        if date == "20260528":
            raise OSError("DART disconnected")
        return pl.DataFrame({"rcept_no": ["R1"]})

    monkeypatch.setattr(mod, "fillContent", failOnSecondDate)

    with pytest.raises(OSError, match="DART disconnected") as excInfo:
        mod.fillContentAll(client=object(), showProgress=False)

    assert any("date=20260528, completedDates=1" in note for note in getattr(excInfo.value, "__notes__", []))


def test_load_all_callable() -> None:
    """loadAll() callable smoke."""
    from dartlab.gather.dart.allFilingsCollector import loadAll

    assert callable(loadAll)


def test_load_day_callable() -> None:
    """loadDay() callable smoke."""
    from dartlab.gather.dart.allFilingsCollector import loadDay

    assert callable(loadDay)


def test_pending_dates_callable() -> None:
    """pendingDates() callable smoke."""
    from dartlab.gather.dart.allFilingsCollector import pendingDates

    assert callable(pendingDates)


def test_stats_callable() -> None:
    """stats() callable smoke."""
    from dartlab.gather.dart.allFilingsCollector import stats

    assert callable(stats)


def test_ensure_from_hf_callable() -> None:
    """_ensureFromHf() callable smoke."""
    from dartlab.gather.dart.allFilingsCollector import _ensureFromHf

    assert callable(_ensureFromHf)


def test_ensure_from_hf_env_skip_is_explicit_unavailable(monkeypatch) -> None:
    """의도적으로 끈 remote를 원격 정상 부재와 같은 False로 표현하지 않는다."""
    from dartlab.gather.dart import allFilingsCollector as mod

    monkeypatch.setenv("DARTLAB_NO_HF_DOWNLOAD", "1")
    mod._HF_DOWNLOAD_ATTEMPTED.clear()

    with pytest.raises(mod.AllFilingsHfUnavailableError, match="비활성화") as excInfo:
        mod._ensureFromHf("20990101")

    assert excInfo.value.period == "20990101"


def test_ensure_from_hf_local_exists_short_circuit(monkeypatch, tmp_path) -> None:
    """로컬에 이미 .parquet 있으면 HF 호출 없이 True."""
    import dartlab.config as _cfg
    from dartlab.gather.dart import allFilingsCollector as mod

    monkeypatch.setattr(_cfg, "dataDir", str(tmp_path))
    outDir = mod._allFilingsDir()
    (outDir / "20260527.parquet").write_bytes(b"stub")

    # snapshot_download 가 호출되면 실패 — 호출 없음 검증.
    def shouldNotBeCalled(*args, **kwargs):
        raise AssertionError("snapshot_download 호출됨 — short-circuit 실패")

    import huggingface_hub

    monkeypatch.setattr(huggingface_hub, "snapshot_download", shouldNotBeCalled)
    mod._HF_DOWNLOAD_ATTEMPTED.clear()
    assert mod._ensureFromHf("20260527") is mod.HfFallbackStatus.LOCAL


def test_ensure_from_hf_normal_remote_absence_is_not_found(monkeypatch, tmp_path) -> None:
    """원격 호출은 성공했지만 요청 artifact가 없으면 정상 NOT_FOUND다."""
    import dartlab.config as _cfg
    from dartlab.gather.dart import allFilingsCollector as mod

    monkeypatch.setattr(_cfg, "dataDir", str(tmp_path))
    monkeypatch.delenv("DARTLAB_NO_HF_DOWNLOAD", raising=False)
    mod._HF_DOWNLOAD_ATTEMPTED.clear()

    import huggingface_hub

    from dartlab.core import hfRetry

    calls = 0

    def noMatchingArtifact(*_args, **_kwargs):
        nonlocal calls
        calls += 1
        return str(tmp_path)

    monkeypatch.setattr(huggingface_hub, "snapshot_download", noMatchingArtifact)
    monkeypatch.setattr(hfRetry, "retryHfCall", lambda fn, *args, **kwargs: fn(*args, **kwargs))

    assert mod._ensureFromHf("20990101") is mod.HfFallbackStatus.NOT_FOUND
    assert mod._ensureFromHf("20990101") is mod.HfFallbackStatus.NOT_FOUND
    assert calls == 1


def test_ensure_from_hf_download_success_requires_local_artifact(monkeypatch, tmp_path) -> None:
    """snapshot 호출 성공만으로 성공 처리하지 않고 실제 artifact를 검증한다."""
    import dartlab.config as _cfg
    from dartlab.gather.dart import allFilingsCollector as mod

    monkeypatch.setattr(_cfg, "dataDir", str(tmp_path))
    monkeypatch.delenv("DARTLAB_NO_HF_DOWNLOAD", raising=False)
    mod._HF_DOWNLOAD_ATTEMPTED.clear()

    import huggingface_hub

    from dartlab.core import hfRetry

    def writeArtifact(*_args, **_kwargs):
        path = mod._allFilingsDir() / "20260527.parquet"
        pl.DataFrame({"rcept_no": ["R1"]}).write_parquet(path)
        return str(tmp_path)

    monkeypatch.setattr(huggingface_hub, "snapshot_download", writeArtifact)
    monkeypatch.setattr(hfRetry, "retryHfCall", lambda fn, *args, **kwargs: fn(*args, **kwargs))

    assert mod._ensureFromHf("20260527") is mod.HfFallbackStatus.DOWNLOADED


def test_ensure_from_hf_remote_failure_preserves_cause(monkeypatch, tmp_path) -> None:
    """실제 원격 실패는 typed error로 전파하고 원인을 연결한다."""
    import dartlab.config as _cfg
    from dartlab.gather.dart import allFilingsCollector as mod

    monkeypatch.setattr(_cfg, "dataDir", str(tmp_path))
    monkeypatch.delenv("DARTLAB_NO_HF_DOWNLOAD", raising=False)
    mod._HF_DOWNLOAD_ATTEMPTED.clear()

    import huggingface_hub

    from dartlab.core import hfRetry

    def failDownload(*_args, **_kwargs):
        raise OSError("network down")

    monkeypatch.setattr(huggingface_hub, "snapshot_download", failDownload)
    monkeypatch.setattr(hfRetry, "retryHfCall", lambda fn, *args, **kwargs: fn(*args, **kwargs))

    with pytest.raises(mod.AllFilingsHfDownloadError, match="20260527") as excInfo:
        mod._ensureFromHf("20260527")

    assert isinstance(excInfo.value.__cause__, OSError)
    assert excInfo.value.period == "20260527"
    assert "20260527" not in mod._HF_DOWNLOAD_ATTEMPTED


def test_load_day_returns_none_only_for_normal_remote_absence(monkeypatch, tmp_path) -> None:
    """loadDay의 None은 정상적인 artifact 부재만 뜻한다."""
    import dartlab.config as _cfg
    from dartlab.gather.dart import allFilingsCollector as mod

    monkeypatch.setattr(_cfg, "dataDir", str(tmp_path))
    monkeypatch.setattr(mod, "_ensureFromHf", lambda _period: mod.HfFallbackStatus.NOT_FOUND)

    assert mod.loadDay("20990101") is None


def test_load_all_returns_empty_only_for_normal_remote_absence(monkeypatch, tmp_path) -> None:
    """loadAll의 빈 frame은 정상적인 원격 artifact 부재만 뜻한다."""
    import dartlab.config as _cfg
    from dartlab.gather.dart import allFilingsCollector as mod

    monkeypatch.setattr(_cfg, "dataDir", str(tmp_path))
    monkeypatch.setattr(mod, "_ensureFromHf", lambda: mod.HfFallbackStatus.NOT_FOUND)

    assert mod.loadAll().is_empty()


@pytest.mark.parametrize("loaderArgs", [("day", "20990101"), ("all", None)])
def test_loaders_propagate_typed_hf_failure(monkeypatch, tmp_path, loaderArgs) -> None:
    """사용자-facing loader가 typed remote 실패를 빈 결과로 다시 삼키지 않는다."""
    import dartlab.config as _cfg
    from dartlab.gather.dart import allFilingsCollector as mod

    monkeypatch.setattr(_cfg, "dataDir", str(tmp_path))
    kind, period = loaderArgs

    def failEnsure(_period=None):
        raise mod.AllFilingsHfDownloadError("remote failed", period=_period)

    monkeypatch.setattr(mod, "_ensureFromHf", failEnsure)

    with pytest.raises(mod.AllFilingsHfDownloadError, match="remote failed"):
        if kind == "day":
            mod.loadDay(period)
        else:
            mod.loadAll()


_STUB_DART_014 = (
    b'<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
    b"<result><status>014</status><message>\xed\x8c\x8c\xec\x9d\xbc\xec\x9d\xb4 "
    b"\xec\xa1\xb4\xec\x9e\xac\xed\x95\x98\xec\xa7\x80 \xec\x95\x8a\xec\x8a\xb5\xeb\x8b\x88\xeb\x8b\xa4."
    b"</message></result>"
)
_STUB_DART_013 = (
    b'<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
    b"<result><status>013</status><message>\xec\xa0\x91\xec\x88\x98\xeb\xb2\x88\xed\x98\xb8 "
    b"\xec\x98\xa4\xeb\xa5\x98</message></result>"
)


def _stubMeta(rceptNo: str, reportNm: str = "주요사항보고서(자기주식취득결정)"):
    """단일 row meta DataFrame 반환."""
    return pl.DataFrame(
        [
            {
                "corp_code": "00126380",
                "corp_name": "삼성전자",
                "stock_code": "005930",
                "corp_cls": "Y",
                "rcept_dt": "20260527",
                "rcept_no": rceptNo,
                "report_nm": reportNm,
                "flr_nm": "삼성전자",
            }
        ]
    )


def _assertSchema(df) -> None:
    """공통 schema 회귀 가드 — content_raw + fetch_status, section_* 부재."""
    cols = set(df.columns)
    assert "content_raw" in cols, f"content_raw 컬럼 없음: {cols}"
    assert "fetch_status" in cols, f"fetch_status 컬럼 없음: {cols}"
    assert "section_content" not in cols, f"옛 section_content 컬럼 잔존: {cols}"
    assert "section_title" not in cols, f"옛 section_title 컬럼 잔존: {cols}"
    assert "section_order" not in cols, f"옛 section_order 컬럼 잔존: {cols}"


class _StubClient:
    pass


def _patchListFilings(monkeypatch, mod, metaDf):
    """fillContent → collectMetaDay → listFilings 경로 stub."""
    monkeypatch.setattr(mod, "listFilings", lambda *a, **kw: metaDf)


def test_fill_content_schema_raw_xml(monkeypatch, tmp_path) -> None:
    """raw XML (dart4.xsd) 태그·attribute 보존 + fetch_status="ok" 회귀 가드."""
    import dartlab.config as _cfg
    from dartlab.gather.dart import allFilingsCollector as mod

    monkeypatch.setattr(_cfg, "dataDir", str(tmp_path))
    _patchListFilings(monkeypatch, mod, _stubMeta("20260527000001"))

    stubXml = (
        '<?xml version="1.0" encoding="utf-8"?>'
        '<DOCUMENT xsi:noNamespaceSchemaLocation="dart4.xsd">'
        '<DOCUMENT-NAME ACODE="10136">주요사항보고서</DOCUMENT-NAME>'
        '<BODY ATOCID="32">'
        '<TITLE ATOC="Y" AASSOCNOTE="COVER" ATOCID="1">개요</TITLE>'
        "<P>본문 시작</P>"
        '<TABLE BORDER="1"><TR><TD>항목</TD><TD>값</TD></TR></TABLE>'
        "<P>본문 끝</P>"
        "</BODY></DOCUMENT>"
    )
    monkeypatch.setattr(mod, "_collectOneRaw", lambda client, rceptNo: (stubXml, "ok"))

    df = mod.fillContent("20260527", client=_StubClient(), showProgress=False)
    assert df is not None
    _assertSchema(df)

    raw = df["content_raw"][0]
    assert "<DOCUMENT" in raw
    assert "<TITLE" in raw
    assert "<TABLE" in raw
    assert 'ATOC="Y"' in raw
    assert 'AASSOCNOTE="COVER"' in raw
    assert df["fetch_status"][0] == "ok"

    outDir = mod._allFilingsDir()
    assert not (outDir / "20260527_meta.parquet").exists()
    assert (outDir / "20260527.parquet").exists()


def test_fill_content_schema_raw_html(monkeypatch, tmp_path) -> None:
    """raw HTML (xforms) 태그·attribute 보존 + fetch_status="ok" 회귀 가드."""
    import dartlab.config as _cfg
    from dartlab.gather.dart import allFilingsCollector as mod

    monkeypatch.setattr(_cfg, "dataDir", str(tmp_path))
    _patchListFilings(monkeypatch, mod, _stubMeta("20260528000002"))

    stubHtml = (
        "<html><head>"
        '<meta content="text/html; charset=euc-kr" http-equiv="Content-Type">'
        "<STYLE>.xforms * { font-family: 돋움체; } .xforms_title * { font-size: 13pt; }</STYLE>"
        '</head><body class="xforms">'
        '<table><tr><td class="xforms_title">최대주주변동</td></tr></table>'
        "</body></html>"
    )
    monkeypatch.setattr(mod, "_collectOneRaw", lambda client, rceptNo: (stubHtml, "ok"))

    df = mod.fillContent("20260528", client=_StubClient(), showProgress=False)
    assert df is not None
    _assertSchema(df)

    raw = df["content_raw"][0]
    assert "<html>" in raw
    assert "<STYLE>" in raw
    assert "xforms" in raw
    assert "charset=euc-kr" in raw
    assert df["fetch_status"][0] == "ok"

    outDir = mod._allFilingsDir()
    assert (outDir / "20260528.parquet").exists()


def test_collect_one_raw_no_body_014(monkeypatch) -> None:
    """DART status=014 (파일 부재) → (None, "no_body") — 영원히 retry 불가."""
    from dartlab.gather.dart import allFilingsCollector as mod

    class _C:
        def getBytes(self, endpoint, params):
            return _STUB_DART_014

    content, status = mod._collectOneRaw(_C(), "20260527100051")
    assert content is None
    assert status == "no_body"


def test_collect_one_raw_no_body_013(monkeypatch) -> None:
    """DART status=013 (잘못된 rcept_no) → (None, "no_body")."""
    from dartlab.gather.dart import allFilingsCollector as mod

    class _C:
        def getBytes(self, endpoint, params):
            return _STUB_DART_013

    content, status = mod._collectOneRaw(_C(), "99999999999999")
    assert content is None
    assert status == "no_body"


def test_collect_one_raw_error_exception(monkeypatch) -> None:
    """client.getBytes 가 RuntimeError raise → (None, "error") — retry 대상."""
    from dartlab.gather.dart import allFilingsCollector as mod

    class _C:
        def getBytes(self, endpoint, params):
            raise RuntimeError("api rate limit")

    content, status = mod._collectOneRaw(_C(), "20260527000001")
    assert content is None
    assert status == "error"


def test_fill_content_diff_retry(monkeypatch, tmp_path) -> None:
    """기존 .parquet 의 error row 만 retry, no_body/ok 는 skip, 신규 row 추가."""
    import dartlab.config as _cfg
    from dartlab.gather.dart import allFilingsCollector as mod

    monkeypatch.setattr(_cfg, "dataDir", str(tmp_path))
    outDir = mod._allFilingsDir()

    # 기존 .parquet: ok / error / no_body 각 1
    existingRows = [
        {
            "corp_code": "001",
            "corp_name": "A",
            "stock_code": "001",
            "corp_cls": "Y",
            "rcept_dt": "20260527",
            "rcept_no": "R_OK",
            "report_nm": "공시1",
            "flr_nm": "A",
            "content_raw": "<DOC>기존 ok</DOC>",
            "fetch_status": "ok",
        },
        {
            "corp_code": "002",
            "corp_name": "B",
            "stock_code": "002",
            "corp_cls": "Y",
            "rcept_dt": "20260527",
            "rcept_no": "R_ERR",
            "report_nm": "공시2",
            "flr_nm": "B",
            "content_raw": None,
            "fetch_status": "error",
        },
        {
            "corp_code": "003",
            "corp_name": "C",
            "stock_code": "003",
            "corp_cls": "Y",
            "rcept_dt": "20260527",
            "rcept_no": "R_NB",
            "report_nm": "공시3",
            "flr_nm": "C",
            "content_raw": None,
            "fetch_status": "no_body",
        },
    ]
    pl.DataFrame(existingRows).write_parquet(outDir / "20260527.parquet")

    # listFilings 가 기존 3 + 신규 1 = 4 건 반환
    metaRows = [
        {
            "corp_code": r["corp_code"],
            "corp_name": r["corp_name"],
            "stock_code": r["stock_code"],
            "corp_cls": r["corp_cls"],
            "rcept_dt": r["rcept_dt"],
            "rcept_no": r["rcept_no"],
            "report_nm": r["report_nm"],
            "flr_nm": r["flr_nm"],
        }
        for r in existingRows
    ]
    metaRows.append(
        {
            "corp_code": "004",
            "corp_name": "D",
            "stock_code": "004",
            "corp_cls": "Y",
            "rcept_dt": "20260527",
            "rcept_no": "R_NEW",
            "report_nm": "공시4",
            "flr_nm": "D",
        }
    )
    _patchListFilings(monkeypatch, mod, pl.DataFrame(metaRows))

    # _collectOneRaw — error retry / 신규는 모두 ok 반환
    collectCalls: list[str] = []

    def stubCollect(client, rceptNo):
        collectCalls.append(rceptNo)
        return (f"<DOC>{rceptNo} 신규 ok</DOC>", "ok")

    monkeypatch.setattr(mod, "_collectOneRaw", stubCollect)

    df = mod.fillContent("20260527", client=_StubClient(), showProgress=False)
    assert df is not None

    # 처리 대상은 신규 + retry 만 (ok / no_body 는 skip)
    assert set(collectCalls) == {"R_ERR", "R_NEW"}

    rowsByRcept = {r["rcept_no"]: r for r in df.iter_rows(named=True)}
    assert len(rowsByRcept) == 4

    # ok / no_body 는 그대로 보존
    assert rowsByRcept["R_OK"]["fetch_status"] == "ok"
    assert rowsByRcept["R_OK"]["content_raw"] == "<DOC>기존 ok</DOC>"
    assert rowsByRcept["R_NB"]["fetch_status"] == "no_body"
    assert rowsByRcept["R_NB"]["content_raw"] is None

    # error 는 retry 결과로 업데이트
    assert rowsByRcept["R_ERR"]["fetch_status"] == "ok"
    assert "R_ERR 신규 ok" in rowsByRcept["R_ERR"]["content_raw"]

    # 신규 추가
    assert rowsByRcept["R_NEW"]["fetch_status"] == "ok"


def test_fill_content_parallel_workers_env(monkeypatch, tmp_path) -> None:
    """DART_ALLFILINGS_WORKERS>1 이면 document.xml fetch 병렬 경로도 parquet 로 merge."""
    import dartlab.config as _cfg
    from dartlab.gather.dart import allFilingsCollector as mod

    monkeypatch.setattr(_cfg, "dataDir", str(tmp_path))
    monkeypatch.setenv("DART_ALLFILINGS_WORKERS", "2")
    meta = pl.DataFrame(
        [
            {
                "corp_code": f"00{i}",
                "corp_name": f"C{i}",
                "stock_code": f"00000{i}",
                "corp_cls": "Y",
                "rcept_dt": "20260529",
                "rcept_no": f"R{i}",
                "report_nm": "주요사항보고서",
                "flr_nm": f"C{i}",
            }
            for i in range(3)
        ]
    )
    _patchListFilings(monkeypatch, mod, meta)
    calls: list[str] = []

    def stubCollect(client, rceptNo):
        calls.append(rceptNo)
        return (f"<DOC>{rceptNo}</DOC>", "ok")

    monkeypatch.setattr(mod, "_collectOneRaw", stubCollect)

    df = mod.fillContent("20260529", client=_StubClient(), showProgress=False)
    assert df is not None
    rowsByRcept = {r["rcept_no"]: r for r in df.iter_rows(named=True)}

    assert set(calls) == {"R0", "R1", "R2"}
    assert set(rowsByRcept) == {"R0", "R1", "R2"}
    assert {r["fetch_status"] for r in rowsByRcept.values()} == {"ok"}


def test_collect_meta_day_always_calls_list_filings(monkeypatch, tmp_path) -> None:
    """기존 .parquet 존재 여부와 무관하게 listFilings 가 항상 호출됨 — idempotent diff 전제."""
    import dartlab.config as _cfg
    from dartlab.gather.dart import allFilingsCollector as mod

    monkeypatch.setattr(_cfg, "dataDir", str(tmp_path))
    outDir = mod._allFilingsDir()
    # 옛 .parquet + _meta.parquet 둘 다 미리 작성 (옛 skip 가드라면 둘 다 차단)
    pl.DataFrame(
        [
            {
                "corp_code": "001",
                "corp_name": "A",
                "stock_code": "001",
                "corp_cls": "Y",
                "rcept_dt": "20260527",
                "rcept_no": "R_OLD",
                "report_nm": "옛 공시",
                "flr_nm": "A",
            }
        ]
    ).write_parquet(outDir / "20260527_meta.parquet")

    callCount = {"n": 0}

    def stubList(*args, **kwargs):
        callCount["n"] += 1
        return _stubMeta("R_NEW", reportNm="신규 공시")

    monkeypatch.setattr(mod, "listFilings", stubList)
    mod.collectMetaDay("20260527", client=_StubClient(), showProgress=False)
    assert callCount["n"] == 1, f"listFilings 호출 0 — skip 가드 잔존: {callCount}"


# ---------------------------------------------------------------------------
# freshness 재동기화 (TTL + 마커) — HF 일일 갱신 catch-up 배선
# ---------------------------------------------------------------------------


def test_ensure_from_hf_refresh_bypasses_local_short_circuit(monkeypatch, tmp_path) -> None:
    """refresh=True 는 로컬 존재여도 원격 재동기화를 수행하고 attempted 마킹은 안 한다."""
    import huggingface_hub

    import dartlab.config as _cfg
    from dartlab.core import hfRetry
    from dartlab.gather.dart import allFilingsCollector as mod

    monkeypatch.setattr(_cfg, "dataDir", str(tmp_path))
    monkeypatch.delenv("DARTLAB_NO_HF_DOWNLOAD", raising=False)
    mod._HF_DOWNLOAD_ATTEMPTED.clear()
    outDir = mod._allFilingsDir()
    (outDir / "20260527.parquet").write_bytes(b"stub")

    calls = 0

    def countDownload(*_args, **_kwargs):
        nonlocal calls
        calls += 1
        return str(tmp_path)

    monkeypatch.setattr(huggingface_hub, "snapshot_download", countDownload)
    monkeypatch.setattr(hfRetry, "retryHfCall", lambda fn, *args, **kwargs: fn(*args, **kwargs))

    assert mod._ensureFromHf("20260527", refresh=True) is mod.HfFallbackStatus.DOWNLOADED
    assert calls == 1
    assert "20260527" not in mod._HF_DOWNLOAD_ATTEMPTED


def test_maybe_resync_ttl_marker_and_memo(monkeypatch, tmp_path) -> None:
    """마커 부재 시 1회 재동기화 + 마커 생성. memo·마커 TTL 이 반복 호출을 차단한다."""
    import dartlab.config as _cfg
    from dartlab.gather.dart import allFilingsCollector as mod

    monkeypatch.setattr(_cfg, "dataDir", str(tmp_path))
    monkeypatch.delenv("DARTLAB_NO_HF_DOWNLOAD", raising=False)
    monkeypatch.delenv("DARTLAB_NO_REFRESH", raising=False)
    monkeypatch.setattr(mod, "_allFilingsResyncCheckedAt", {}, raising=False)
    outDir = mod._allFilingsDir()
    (outDir / "20260527.parquet").write_bytes(b"stub")

    calls: list[str | None] = []

    def fakeEnsure(period=None, *, refresh=False):
        assert refresh is True
        calls.append(period)
        return mod.HfFallbackStatus.DOWNLOADED

    monkeypatch.setattr(mod, "_ensureFromHf", fakeEnsure)

    mod._maybeResyncFromHf("20260527")
    assert calls == ["20260527"]
    assert (outDir / ".hfSynced_20260527").exists()

    # 마커가 신선하므로 재호출 차단 (memo 를 비워도 TTL 게이트가 막는다)
    monkeypatch.setattr(mod, "_allFilingsResyncCheckedAt", {}, raising=False)
    mod._maybeResyncFromHf("20260527")
    assert calls == ["20260527"]


def test_maybe_resync_respects_no_download_env(monkeypatch, tmp_path) -> None:
    """DARTLAB_NO_HF_DOWNLOAD=1 이면 재동기화 자체를 하지 않는다."""
    import dartlab.config as _cfg
    from dartlab.gather.dart import allFilingsCollector as mod

    monkeypatch.setattr(_cfg, "dataDir", str(tmp_path))
    monkeypatch.setenv("DARTLAB_NO_HF_DOWNLOAD", "1")
    monkeypatch.setattr(mod, "_allFilingsResyncCheckedAt", {}, raising=False)

    def trap(*_a, **_k):
        raise AssertionError("resync must be disabled by DARTLAB_NO_HF_DOWNLOAD")

    monkeypatch.setattr(mod, "_ensureFromHf", trap)
    mod._maybeResyncFromHf(None)


def test_loadDay_local_exists_triggers_resync(monkeypatch, tmp_path) -> None:
    """loadDay 는 로컬 존재 시에도 TTL 재동기화 경로를 태운다."""
    import dartlab.config as _cfg
    from dartlab.gather.dart import allFilingsCollector as mod

    monkeypatch.setattr(_cfg, "dataDir", str(tmp_path))
    outDir = mod._allFilingsDir()
    pl.DataFrame({"rcept_no": ["R1"]}).write_parquet(outDir / "20260527.parquet")

    resynced: list[str | None] = []
    monkeypatch.setattr(mod, "_maybeResyncFromHf", lambda period: resynced.append(period))

    frame = mod.loadDay("20260527")
    assert frame is not None and frame.height == 1
    assert resynced == ["20260527"]


def test_loadAll_local_files_trigger_resync(monkeypatch, tmp_path) -> None:
    """loadAll 은 로컬 파일이 있어도 재동기화로 신규 일자를 catch-up 한다."""
    import dartlab.config as _cfg
    from dartlab.gather.dart import allFilingsCollector as mod

    monkeypatch.setattr(_cfg, "dataDir", str(tmp_path))
    outDir = mod._allFilingsDir()
    pl.DataFrame({"rcept_no": ["R1"]}).write_parquet(outDir / "20260526.parquet")

    resynced: list[str | None] = []

    def fakeResync(period):
        resynced.append(period)
        # 재동기화가 신규 일자를 내려받은 상황 재현
        pl.DataFrame({"rcept_no": ["R2"]}).write_parquet(outDir / "20260527.parquet")

    monkeypatch.setattr(mod, "_maybeResyncFromHf", fakeResync)

    frame = mod.loadAll()
    assert resynced == [None]
    assert frame.height == 2, "재동기화로 받은 신규 일자가 결과에 포함되어야 함"
