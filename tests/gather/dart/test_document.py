"""gather/dart/document.py — DART document.xml 원본 zip 병렬 fetch 단위 (무네트워크).

옛 위치: providers/dart/openapi/bulkZipFetcher.py (수집 일원화 — fetch 는 gather 전담).
streamZipBytes/fetchZipsParallel 는 DartClient + 네트워크가 필요하므로 import + 순수
헬퍼(FetchStats·safeWriteBytes·buildTargetsFromFilingList)만 검증한다.
"""

from __future__ import annotations

from pathlib import Path

import pytest

pytestmark = pytest.mark.unit


def test_imports() -> None:
    """공개 fetch 표면 import smoke (실 네트워크 0)."""
    from dartlab.gather.dart.document import (  # noqa: F401
        FetchStats,
        buildTargetsFromFilingList,
        collectAllOriginalZips,
        fetchZipsParallel,
        safeWriteBytes,
        streamZipBytes,
    )


def test_fetch_stats_accumulate() -> None:
    """FetchStats — 스레드 안전 누적 + asDict 직렬화."""
    from dartlab.gather.dart.document import FetchStats

    stats = FetchStats()
    stats.add(saved=2, skipped=1, failed=0, bytesTotal=2048)
    stats.add(saved=1, skipped=0, failed=1, bytesTotal=512)
    d = stats.asDict()
    assert d["saved"] == 3
    assert d["skipped"] == 1
    assert d["failed"] == 1
    assert d["bytesTotal"] == 2560


def test_safe_write_bytes_atomic(tmp_path: Path) -> None:
    """safeWriteBytes — atomic write (.tmp → rename), 디렉터리 자동 생성."""
    from dartlab.gather.dart.document import safeWriteBytes

    dest = tmp_path / "nested" / "005930" / "rcept.zip"
    safeWriteBytes(dest, b"PK\x03\x04payload")
    assert dest.exists()
    assert dest.read_bytes() == b"PK\x03\x04payload"
    assert not (dest.parent / "rcept.zip.tmp").exists()


def test_build_targets_empty_codes_no_network() -> None:
    """buildTargetsFromFilingList — 빈 codes 면 빈 list (listFilings 미호출, 네트워크 0)."""
    from dartlab.gather.dart.document import buildTargetsFromFilingList

    # client=None 이어도 빈 codes 는 루프 0 회 → listFilings 호출 없이 빈 list.
    out = buildTargetsFromFilingList(None, [])  # type: ignore[arg-type]
    assert out == []


class _FakeDocClient:
    """document.xml 응답을 rcept 별로 돌려주는 무네트워크 client. 값이 예외면 그대로 던진다."""

    _slots = [object()]

    def __init__(self, responses: dict[str, object]) -> None:
        self._responses = responses

    def getBytes(self, endpoint: str, params: dict[str, str]) -> bytes:
        value = self._responses[params["rcept_no"]]
        if isinstance(value, BaseException):
            raise value
        return value  # type: ignore[return-value]


def test_iter_zips_separates_final_no_body_from_retryable_errors(tmp_path: Path) -> None:
    """DART 014/013 XML 본문은 no_body, 나머지 실패는 error 로 갈라야 reconcile 이 재시도 실패만 센다.

    2026-09-15~21 Original SSOT Sync dart-reconcile 은 남은 누락 rcept 가 전부 014(정정 공시 등)라
    매일 zip fetch 0/N 으로 실패했다. 이 테스트는 그 판정 경계를 잠근다.
    """
    from dartlab.core.dartClient import DartApiError
    from dartlab.gather.dart.document import iterZipsParallel

    xml014 = (
        b'<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
        b"<result><status>014</status><message>file missing</message></result>"
    )
    xml013 = b"<result><status>013</status><message>bad rcept</message></result>"
    zipBody = b"PK\x03\x04" + b"z" * 2000
    client = _FakeDocClient(
        {
            "r014": xml014,
            "r013": xml013,
            "rOther": b"<result><status>800</status></result>",
            "rBigHtml": b"<html>" + b"x" * 2000,
            "rKeys": DartApiError("020", "all keys cooling down"),
            "rOk": zipBody,
        }
    )
    targets = [("000001", rc) for rc in ("r014", "r013", "rOther", "rBigHtml", "rKeys", "rOk")]

    out = {rc: (status, n) for _sc, rc, status, n in iterZipsParallel(client, targets, outDir=tmp_path, workers=2)}

    assert out == {
        "r014": ("no_body", 0),
        "r013": ("no_body", 0),
        "rOther": ("error", 0),
        "rBigHtml": ("error", 0),
        "rKeys": ("error", 0),
        "rOk": ("ok", len(zipBody)),
    }
    assert sorted(path.name for path in (tmp_path / "000001").iterdir()) == ["rOk.zip"]
