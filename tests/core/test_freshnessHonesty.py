"""원격 신선도 확인 실패의 기록 계약 회귀.

`.etag` 파일의 mtime 이 곧 "마지막으로 확인한 시각" 이다. 확인이 실패했을 때도 그 파일을
touch 하고 있어서, 실패가 "확인했고 최신" 으로 기록됐다. 오프라인이나 프록시 차단이
이어지면 TTL 동안 갱신 시도조차 하지 않고, 실패할 때마다 그 침묵이 다시 연장된다.
자료는 오래될수록 더 최신처럼 보인다.
"""

from __future__ import annotations

import time
from pathlib import Path

from dartlab.core.dataLoaderFreshness import refreshFromHf

_RELEASES = {"dartFinance": {"label": "재무"}}


def _prepare(tmpPath: Path) -> tuple[Path, Path, float]:
    """로컬 parquet 과 확인 시각 사이드카를 오래된 상태로 만든다."""

    parquet = tmpPath / "005930.parquet"
    parquet.write_bytes(b"local")
    etag = parquet.with_suffix(".parquet.etag")
    etag.write_text("etag-old", encoding="utf-8")
    old = time.time() - 86400
    import os

    os.utime(etag, (old, old))
    return parquet, etag, etag.stat().st_mtime


def _refresh(parquet: Path, *, stale: bool | None, downloaded: list[str]) -> None:
    refreshFromHf(
        "005930",
        parquet,
        "dartFinance",
        dataReleases=_RELEASES,
        hfBaseUrl=lambda _category: "https://example.invalid",
        checkRemoteFreshness=lambda *_args: stale,
        downloadWithRetry=lambda url, _dest: downloaded.append(url),
        saveEtag=lambda *_args: None,
    )


def testFailedCheckDoesNotAdvanceTheLastVerifiedClock(tmp_path: Path) -> None:
    """확인 실패는 확인이 아니다. 시각을 밀면 다음 시도까지 막힌다."""

    parquet, etag, before = _prepare(tmp_path)
    downloaded: list[str] = []

    _refresh(parquet, stale=None, downloaded=downloaded)

    assert etag.stat().st_mtime == before
    assert downloaded == []


def testSuccessfulCheckThatFindsNothingNewDoesAdvanceTheClock(tmp_path: Path) -> None:
    """실제로 확인해서 최신이면 그 시각을 기록하는 것이 맞다."""

    parquet, etag, before = _prepare(tmp_path)
    downloaded: list[str] = []

    _refresh(parquet, stale=False, downloaded=downloaded)

    assert etag.stat().st_mtime > before
    assert downloaded == []


def testStaleRemoteTriggersDownload(tmp_path: Path) -> None:
    """원격이 더 새로우면 받아온다. 이 길이 막히면 갱신 자체가 없어진다."""

    parquet, _etag, _before = _prepare(tmp_path)
    downloaded: list[str] = []

    _refresh(parquet, stale=True, downloaded=downloaded)

    assert downloaded == ["https://example.invalid/005930.parquet"]


def testLocalFileSurvivesAFailedCheck(tmp_path: Path) -> None:
    """확인이 실패해도 갖고 있던 자료는 그대로 쓴다."""

    parquet, _etag, _before = _prepare(tmp_path)

    _refresh(parquet, stale=None, downloaded=[])

    assert parquet.read_bytes() == b"local"
