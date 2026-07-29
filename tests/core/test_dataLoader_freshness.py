"""
dataLoader._checkRemoteFreshness 회귀 테스트.

P0 버그 (2026-04-06): etag 사이드카가 없을 때 현재 HF ETag를 그대로 저장 + fresh
판정 → parquet은 옛날 그대로인데 .etag만 새로 만들어져서 영구 stale 고정.

이 테스트는 그 버그가 다시 들어오는 것을 방지한다.
"""

from __future__ import annotations

import logging
from contextlib import nullcontext
from pathlib import Path
from unittest.mock import patch

import polars as pl
import pytest

from dartlab.core.dataLoader import (
    _checkRemoteFreshness,
    _download,
    _fetchRemoteEtag,
    _fetchRemoteEtagAndSize,
    _refreshFromHf,
)
from dartlab.core.dataLoaderFreshness import downloadWithRetry, saveEtag


def _corruptFirstParquetDataPage(tmp_path: Path) -> bytes:
    """Footer/schema는 유지하고 첫 data-page header만 손상한 payload를 만든다."""
    import pyarrow.parquet as pq

    healthy = tmp_path / "partial-corruption-source.parquet"
    pl.DataFrame(
        {
            "id": range(20_000),
            "text": [f"row-{index}-" + "abcdef0123456789" * 4 for index in range(20_000)],
        }
    ).write_parquet(
        healthy,
        compression="zstd",
        row_group_size=10_000,
    )
    metadata = pq.ParquetFile(healthy).metadata
    pageOffset = metadata.row_group(0).column(1).data_page_offset
    raw = bytearray(healthy.read_bytes())
    raw[pageOffset] ^= 0xFF
    return bytes(raw)


@pytest.mark.unit
def test_download_with_retry_uses_hf_token(monkeypatch, tmp_path):
    """HF_TOKEN 이 있으면 단건 parquet 다운로드에도 Authorization 헤더를 붙인다."""
    seen: dict[str, str | None] = {}

    class _Response:
        def __init__(self):
            self._chunks = [b"abc", b""]

        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc, tb):
            return False

        def read(self, _size: int) -> bytes:
            return self._chunks.pop(0)

    def fakeUrlopen(req):
        seen["authorization"] = req.get_header("Authorization")
        return _Response()

    def failUrlretrieve(_url, _tmp):
        raise AssertionError("HF_TOKEN path should not call urlretrieve")

    monkeypatch.setenv("HF_TOKEN", "token-123")
    monkeypatch.setattr("dartlab.core.dataLoaderFreshness.urlopen", fakeUrlopen)

    dest = tmp_path / "005930.parquet"
    downloadWithRetry(
        "https://huggingface.co/datasets/eddmpython/dartlab-data/resolve/main/dart/panel/005930.parquet",
        dest,
        maxRetries=1,
        socketTimeout=nullcontext,
        urlretrieve=failUrlretrieve,
    )

    assert seen["authorization"] == "Bearer token-123"
    assert dest.read_bytes() == b"abc"


@pytest.mark.unit
def test_saveEtagFailureIsObservable(tmp_path, caplog):
    """best-effort ETag 실패도 원인을 완전히 삼키지 않고 경고로 남긴다."""
    dest = tmp_path / "005930.parquet"

    def failFetch(_url):
        raise OSError("sidecar unavailable")

    with caplog.at_level(logging.WARNING, logger="dartlab.core.dataLoaderFreshness"):
        saveEtag(
            "005930",
            dest,
            "finance",
            hfBaseUrl=lambda _category: "https://example.com",
            fetchRemoteEtag=failFetch,
        )

    assert "ETag" in caplog.text
    assert "OSError" in caplog.text


@pytest.mark.unit
def test_downloadWithRetryRejectsNonHttpsBeforeFilesystem(tmp_path):
    """공개 download helper는 custom/file scheme을 열기 전에 거부한다."""
    dest = tmp_path / "payload.parquet"

    with pytest.raises(ValueError, match="HTTPS"):
        downloadWithRetry(
            "file:///tmp/payload.parquet",
            dest,
            maxRetries=1,
            socketTimeout=nullcontext,
            urlretrieve=lambda *_args: None,
        )

    assert not dest.exists()


def _load_sync_recent_module():
    import importlib.util

    spec = importlib.util.spec_from_file_location(
        "syncRecent",
        Path(__file__).parent.parent.parent / ".github" / "scripts" / "sync" / "syncRecent.py",
    )
    if spec is None or spec.loader is None:
        pytest.skip("syncRecent.py 로드 실패")
    syncRecent = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(syncRecent)
    return syncRecent


@pytest.mark.unit
def test_etag_missing_should_be_stale(tmp_path):
    """P0 회귀: etag 사이드카가 없으면 stale로 판정해야 한다.

    과거 버그: etag 없으면 현재 HF ETag 저장 후 fresh(False) 반환.
    수정 후: etag 없으면 stale(True) 반환 → 다운로드 강제.
    """
    parquet = tmp_path / "test.parquet"
    parquet.write_bytes(b"old data")
    etag_file = parquet.with_suffix(".parquet.etag")
    assert not etag_file.exists()

    # 원격 ETag 정상 조회 가능
    with patch(
        "dartlab.core.dataLoader._fetchRemoteEtagAndSize",
        return_value=("remote-etag-123", 8),  # 8 bytes = 로컬 크기와 같음
    ):
        stale = _checkRemoteFreshness("test", parquet, "finance")

    # 핵심: etag 없으면 무조건 stale (True)
    assert stale is True, "etag 없을 때 fresh로 판정하면 안 됨"

    # 부수: etag 사이드카가 자동 생성되면 안 됨 (다운로드 후에만 _saveEtag로 생성)
    assert not etag_file.exists(), "etag 사이드카는 _checkRemoteFreshness가 만들면 안 됨"


@pytest.mark.unit
def test_etag_match_and_size_match_is_fresh(tmp_path):
    """ETag 같고 Content-Length 같으면 fresh."""
    parquet = tmp_path / "test.parquet"
    parquet.write_bytes(b"matching data")  # 13 bytes
    etag_file = parquet.with_suffix(".parquet.etag")
    etag_file.write_text("matched-etag", encoding="utf-8")

    with patch(
        "dartlab.core.dataLoader._fetchRemoteEtagAndSize",
        return_value=("matched-etag", 13),
    ):
        stale = _checkRemoteFreshness("test", parquet, "finance")

    assert stale is False


@pytest.mark.unit
def test_etag_match_but_size_differs_is_stale(tmp_path):
    """P0 회귀: ETag는 같지만 Content-Length가 다르면 stale (손상 방어).

    HF ETag가 우연히 같지만 로컬 parquet이 손상돼서 크기가 다른 케이스를 잡는다.
    """
    parquet = tmp_path / "test.parquet"
    parquet.write_bytes(b"corrupted")  # 9 bytes
    etag_file = parquet.with_suffix(".parquet.etag")
    etag_file.write_text("matched-etag", encoding="utf-8")

    with patch(
        "dartlab.core.dataLoader._fetchRemoteEtagAndSize",
        return_value=("matched-etag", 100),  # 다름
    ):
        stale = _checkRemoteFreshness("test", parquet, "finance")

    assert stale is True, "Content-Length 차이로 손상 케이스 잡혀야 함"


@pytest.mark.unit
def test_etag_differs_is_stale(tmp_path):
    """ETag가 다르면 stale."""
    parquet = tmp_path / "test.parquet"
    parquet.write_bytes(b"old")
    etag_file = parquet.with_suffix(".parquet.etag")
    etag_file.write_text("old-etag", encoding="utf-8")

    with patch(
        "dartlab.core.dataLoader._fetchRemoteEtagAndSize",
        return_value=("new-etag", 3),
    ):
        stale = _checkRemoteFreshness("test", parquet, "finance")

    assert stale is True


@pytest.mark.unit
def test_remote_etag_unavailable_returns_none(tmp_path):
    """원격 ETag 못 가져오면 None (네트워크 오류)."""
    parquet = tmp_path / "test.parquet"
    parquet.write_bytes(b"x")

    with patch(
        "dartlab.core.dataLoader._fetchRemoteEtagAndSize",
        return_value=("", 0),
    ):
        stale = _checkRemoteFreshness("test", parquet, "finance")

    assert stale is None


@pytest.mark.unit
def test_fetchRemoteEtagAndSize_missingSizeIsUnknown(monkeypatch):
    """size header 부재는 ETag만 유효한 정상 응답으로 처리한다."""

    class Response:
        headers = {"ETag": '"etag-123"'}

        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc, tb):
            return False

    monkeypatch.setattr("dartlab.core.dataLoader.urlopen", lambda _request: Response())

    assert _fetchRemoteEtagAndSize("https://example.invalid/a.parquet") == ("etag-123", 0)


@pytest.mark.unit
def test_fetchRemoteEtagAndSize_rejectsNonHttpsBeforeRequest(monkeypatch):
    """원격 metadata reader가 local file이나 평문 HTTP scheme을 열지 않는다."""

    def failUrlopen(_request):
        raise AssertionError("invalid URL must fail before urlopen")

    monkeypatch.setattr("dartlab.core.dataLoader.urlopen", failUrlopen)

    with pytest.raises(ValueError, match="HTTPS"):
        _fetchRemoteEtagAndSize("http://example.invalid/a.parquet")
    with pytest.raises(ValueError, match="HTTPS"):
        _fetchRemoteEtagAndSize("file:///tmp/a.parquet")


@pytest.mark.unit
def test_fetchRemoteEtagAndSize_invalidSizeRaisesAndCloses(monkeypatch):
    """존재하는 malformed size를 0으로 바꾸지 않고 응답도 닫는다."""

    class Response:
        headers = {"ETag": '"etag-123"', "Content-Length": "broken"}
        closed = False

        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc, tb):
            self.closed = True
            return False

    response = Response()
    monkeypatch.setattr("dartlab.core.dataLoader.urlopen", lambda _request: response)

    with pytest.raises(ValueError, match="Content-Length"):
        _fetchRemoteEtagAndSize("https://example.invalid/a.parquet")
    assert response.closed is True


@pytest.mark.unit
def test_fetchRemoteEtag_ignoresUnneededInvalidSize(monkeypatch):
    """ETag projection은 사용하지 않는 size header 오류 때문에 실패하지 않는다."""

    class Response:
        headers = {"ETag": '"etag-123"', "Content-Length": "broken"}

        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc, tb):
            return False

    monkeypatch.setattr("dartlab.core.dataLoader.urlopen", lambda _request: Response())

    assert _fetchRemoteEtag("https://example.invalid/a.parquet") == "etag-123"


@pytest.mark.unit
def test_fetchRemoteEtagAndSize_blankLinkedSizeUsesContentLength(monkeypatch):
    """빈 LFS size가 유효한 Content-Length를 가리지 않는다."""

    class Response:
        headers = {"ETag": '"etag-123"', "X-Linked-Size": "   ", "Content-Length": "123"}

        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc, tb):
            return False

    monkeypatch.setattr("dartlab.core.dataLoader.urlopen", lambda _request: Response())

    assert _fetchRemoteEtagAndSize("https://example.invalid/a.parquet") == ("etag-123", 123)


@pytest.mark.unit
def test_download_keepsPayloadWhenOnlySizeHeaderIsInvalid(tmp_path, monkeypatch):
    """최초 다운로드 성공 payload를 ETag와 무관한 size 오류로 삭제하지 않는다."""
    dest = tmp_path / "005930.parquet"

    def writePayload(_url, path):
        pl.DataFrame({"value": ["downloaded"]}).write_parquet(path)

    monkeypatch.setattr("dartlab.core.dataLoader._downloadWithRetry", writePayload)
    monkeypatch.setattr(
        "dartlab.core.dataLoader._fetchRemoteHeaders",
        lambda _url: ("etag-123", "broken", None),
    )

    _download("005930", dest, "finance")

    assert pl.read_parquet(dest)["value"].to_list() == ["downloaded"]
    assert dest.with_suffix(".parquet.etag").read_text(encoding="utf-8") == "etag-123"


@pytest.mark.unit
def test_refresh_keepsPayloadWhenOnlySizeHeaderIsInvalid(tmp_path, monkeypatch):
    """refresh replace 뒤 ETag 저장도 size 오류와 독립적으로 완료한다."""
    dest = tmp_path / "005930.parquet"
    pl.DataFrame({"value": ["old"]}).write_parquet(dest)

    def writePayload(_url, path):
        pl.DataFrame({"value": ["refreshed"]}).write_parquet(path)

    monkeypatch.setattr("dartlab.core.dataLoader._checkRemoteFreshness", lambda *_args: True)
    monkeypatch.setattr("dartlab.core.dataLoader._downloadWithRetry", writePayload)
    monkeypatch.setattr(
        "dartlab.core.dataLoader._fetchRemoteHeaders",
        lambda _url: ("etag-123", "broken", None),
    )

    _refreshFromHf("005930", dest, "finance")

    assert pl.read_parquet(dest)["value"].to_list() == ["refreshed"]
    assert dest.with_suffix(".parquet.etag").read_text(encoding="utf-8") == "etag-123"


@pytest.mark.unit
def test_downloadRejectsInvalidParquetWithoutPublishingIt(tmp_path, monkeypatch):
    """신규 payload가 parquet이 아니면 canonical 경로에 확정하지 않는다."""
    dest = tmp_path / "005930.parquet"

    monkeypatch.setattr(
        "dartlab.core.dataLoader._downloadWithRetry",
        lambda _url, path: path.write_bytes(b"invalid parquet"),
    )

    with pytest.raises(OSError, match="parquet"):
        _download("005930", dest, "finance")

    assert not dest.exists()


@pytest.mark.unit
def test_downloadInvalidReplacementPreservesExistingParquet(tmp_path, monkeypatch):
    """footer가 유효한 부분 손상 payload도 기존 정상 canonical을 덮지 않는다."""
    dest = tmp_path / "005930.parquet"
    pl.DataFrame({"value": ["old"]}).write_parquet(dest)
    corruptPayload = _corruptFirstParquetDataPage(tmp_path)

    monkeypatch.setattr(
        "dartlab.core.dataLoader._downloadWithRetry",
        lambda _url, path: path.write_bytes(corruptPayload),
    )

    with pytest.raises(OSError, match="parquet"):
        _download("005930", dest, "finance")

    assert pl.read_parquet(dest)["value"].to_list() == ["old"]


@pytest.mark.unit
def test_refreshInvalidReplacementPreservesExistingParquet(tmp_path, monkeypatch):
    """자동 refresh도 부분 손상을 끝까지 decode하고 기존 canonical을 유지한다."""
    dest = tmp_path / "005930.parquet"
    pl.DataFrame({"value": ["old"]}).write_parquet(dest)
    corruptPayload = _corruptFirstParquetDataPage(tmp_path)

    monkeypatch.setattr("dartlab.core.dataLoader._checkRemoteFreshness", lambda *_args: True)
    monkeypatch.setattr(
        "dartlab.core.dataLoader._downloadWithRetry",
        lambda _url, path: path.write_bytes(corruptPayload),
    )

    refreshed = _refreshFromHf("005930", dest, "finance")

    assert refreshed is False
    assert pl.read_parquet(dest)["value"].to_list() == ["old"]


@pytest.mark.unit
def test_remote_invalidSizeIsUnavailable(tmp_path):
    """malformed remote metadata는 fresh가 아니라 판단 불가로 올라간다."""
    parquet = tmp_path / "test.parquet"
    parquet.write_bytes(b"x")
    parquet.with_suffix(".parquet.etag").write_text("etag-123", encoding="utf-8")

    with patch(
        "dartlab.core.dataLoader._fetchRemoteEtagAndSize",
        side_effect=ValueError("invalid Content-Length"),
    ):
        stale = _checkRemoteFreshness("test", parquet, "finance")

    assert stale is None


@pytest.mark.unit
def test_reportNm_to_finance_key():
    """syncRecent의 _reportNmToFinanceKey: 보고서명 → (year, reprt_code) 매핑."""
    syncRecent = _load_sync_recent_module()

    fn = syncRecent._reportNmToFinanceKey

    # 사업보고서
    assert fn("사업보고서 (2025.12)") == ("2025", "11011")
    # 반기보고서
    assert fn("반기보고서 (2025.06)") == ("2025", "11012")
    # 분기보고서 Q1
    assert fn("분기보고서 (2025.03)") == ("2025", "11013")
    # 분기보고서 Q3
    assert fn("분기보고서 (2025.09)") == ("2025", "11014")
    # 정정류 prefix는 같은 정기보고서 기간으로 매핑해야 한다.
    assert fn("[기재정정]사업보고서 (2025.12)") == ("2025", "11011")
    assert fn("[첨부정정]반기보고서 (2025.06)") == ("2025", "11012")
    assert fn("[첨부추가]분기보고서 (2025.03)") == ("2025", "11013")
    # 매칭 안 됨
    assert fn("기타 공시") is None
    assert fn("사업보고서") is None  # 연도 없음
    assert fn("사업보고서제출기한연장신고서 (2025.12)") is None


@pytest.mark.unit
def test_sync_recent_verifies_expected_rcept_after_collection(tmp_path):
    """수집 대상 rcept_no가 parquet에 없으면 업로드 전 실패로 잡아야 한다."""
    import polars as pl

    syncRecent = _load_sync_recent_module()

    dataDir = tmp_path / "data"
    financeDir = dataDir / "dart" / "finance"
    financeDir.mkdir(parents=True)
    pl.DataFrame(
        {
            "stock_code": ["005930"],
            "bsns_year": ["2025"],
            "reprt_code": ["11013"],
            "rcept_no": ["new-rcept"],
        }
    ).write_parquet(financeDir / "005930.parquet")

    targetFilings = {
        "005930": {
            "finance": [
                {
                    "rcept_no": "new-rcept",
                    "report_nm": "[기재정정]분기보고서 (2025.03)",
                    "rcept_dt": "20260514",
                }
            ]
        }
    }
    assert syncRecent._verifyCollectedRcepts(targetFilings, str(dataDir), ["finance"]) == []

    targetFilings["005930"]["finance"][0]["rcept_no"] = "missing-rcept"
    failures = syncRecent._verifyCollectedRcepts(targetFilings, str(dataDir), ["finance"])
    assert failures == [
        {
            "category": "finance",
            "stockCode": "005930",
            "rceptNo": "missing-rcept",
            "reportNm": "[기재정정]분기보고서 (2025.03)",
            "rceptDt": "20260514",
        }
    ]


@pytest.mark.unit
def test_collectFinance_targetPeriods_skips_88_diff():
    """_collectFinance가 targetPeriods를 받으면 _buildAllPeriods 88분기 차집합을 안 돌아야 한다.

    P0 회귀 (Phase 5): list.json 기반 가벼운 경로가 무거운 경로로 회귀하는 것을 방지.
    """
    import inspect

    from dartlab.gather.dart.batch import _collectFinance, _collectReport, _workerLoop, batchCollect

    # 새 인자 등록 검증
    sig_finance = inspect.signature(_collectFinance)
    assert "targetPeriods" in sig_finance.parameters, "_collectFinance에 targetPeriods 누락"

    sig_report = inspect.signature(_collectReport)
    assert "targetPeriods" in sig_report.parameters, "_collectReport에 targetPeriods 누락"

    sig_batch = inspect.signature(batchCollect)
    assert "targetPeriodsByCode" in sig_batch.parameters, "batchCollect에 targetPeriodsByCode 누락"

    sig_worker = inspect.signature(_workerLoop)
    assert "targetPeriodsByCode" in sig_worker.parameters, "_workerLoop에 targetPeriodsByCode 누락"


@pytest.mark.unit
def test_syncRecent_recent_mode_caps_max_workers(monkeypatch):
    """recent 동기화는 기본적으로 DART report API 동시성을 제한한다."""
    syncRecent = _load_sync_recent_module()

    monkeypatch.delenv("SYNC_MAX_WORKERS", raising=False)
    assert syncRecent._syncMaxWorkers() == 4

    monkeypatch.setenv("SYNC_MAX_WORKERS", "2")
    assert syncRecent._syncMaxWorkers() == 2

    monkeypatch.setenv("SYNC_MAX_WORKERS", "all")
    assert syncRecent._syncMaxWorkers() is None


@pytest.mark.unit
def test_buildAllPeriods_newest_first():
    """_buildAllPeriods는 최신 분기부터 반환해야 한다.

    P0 회귀: 옛날 분기부터 처리하면 API 한도 도달 시 매번 최신 분기가 잘려서
    신규 데이터가 영구 누락된다 (2026-04-06 388개 종목 누락 사례).
    """
    from datetime import datetime

    from dartlab.gather.dart.batch import _buildAllPeriods

    periods = _buildAllPeriods()
    currentYear = datetime.now().year

    # 첫 번째는 현재 연도 Q4 (사업보고서, 11011)
    assert periods[0][0] == str(currentYear), "첫 번째는 최신 연도여야 함"
    assert periods[0][1] == "11011", "현재 연도 첫 번째는 Q4(사업보고서)여야 함"

    # 한 연도 안에서도 Q4 → Q3 → Q2 → Q1 순서
    yearGroups: dict[str, list[str]] = {}
    for y, c in periods:
        yearGroups.setdefault(y, []).append(c)
    expected_order = ["11011", "11014", "11012", "11013"]  # Q4 Q3 Q2 Q1
    for y, codes in yearGroups.items():
        assert codes == expected_order, f"{y}년 분기 순서가 Q4→Q1이 아님: {codes}"
