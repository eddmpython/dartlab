"""SEC submissions.zip 벌크 다운로더·스트리머 — 전 상장사 공시 인덱스(전 form).

URL: https://www.sec.gov/Archives/edgar/daily-index/bulkdata/submissions.zip
주기: 매일 갱신, 크기 ~1.3GB
내용: 회사별 ``CIK{10}.json``(최근 ~1000건) + ``CIK{10}-submissions-NNN.json``(과거 페이지).

companyfacts.zip(``bulk.py``)과 동형 — XBRL facts 대신 *공시 메타*(form·filingDate·accessionNumber)를
담는다. 공시 피드(수시 8-K·DEF 14A 등)의 SSOT 수집원. 피드는 최근분이라 본 모듈은 메인 ``CIK{10}.json``
(recent 블록)만 순회(``recentOnly``) — 과거 페이지 파일은 건너뛴다. 가공(recent.parquet 빌드)은
``.github/scripts/sync/buildEdgarAllFilingsRecent.py`` 가 맡는다(수집·가공 분리).
"""

from __future__ import annotations

import json
import logging
import zipfile
from collections.abc import Iterator
from pathlib import Path

import httpx

from dartlab.core.edgarBulkFreshness import bulkDir, isBulkFresh, touchBulkFreshness
from dartlab.gather.edgar.bulk import _UA

_log = logging.getLogger(__name__)

_SUBMISSIONS_BULK_URL = "https://www.sec.gov/Archives/edgar/daily-index/bulkdata/submissions.zip"
_TIMEOUT = httpx.Timeout(60.0, read=None, write=60.0, connect=30.0)
_TAG = "submissions"


def downloadSubmissionsBulk(*, force: bool = False, ttlHours: int = 24) -> Path:
    """SEC submissions.zip 를 ``data/edgar/_bulk/submissions.zip`` 로 다운로드 (TTL freshness).

    companyfacts ``downloadCompanyfactsBulk`` 동형(TTL 가드 + 스트림). 24h TTL 내면 스킵.

    Args:
        force: True 면 로컬 상태 무관 재다운로드.
        ttlHours: 로컬 freshness TTL (SEC 매일 갱신 → 24h 기본).

    Returns:
        Path — submissions.zip 경로.

    Raises:
        httpx.HTTPError: SEC bulk endpoint 실패.
        OSError: 파일 쓰기 실패.

    Example:
        >>> downloadSubmissionsBulk(force=False)  # doctest: +SKIP

    Capabilities:
        - SEC submissions.zip(~1.3GB) 를 TTL freshness 가드와 함께 스트림 다운로드(메모리 폭증 0).
          24h TTL 내면 재다운로드 스킵, force=True 면 무조건 재수신.

    AIContext:
        공시 피드(수시 8-K·DEF 14A) 수집의 1단계. AI 직접 호출 X — sync 워크플로(buildEdgarAllFilingsRecent)
        가 본 함수로 zip 을 확보한 뒤 ``iterSubmissionsBulk`` 로 순회한다.

    Guide:
        - "전 상장사 공시 메타를 한 번에" → 본 벌크 다운로더. per-ticker submissions API 는 사용자 선택.
        - XET 429·502 회피는 SEC 직접 endpoint 라 무관(HF 아님).

    When:
        edgarFilingsSync cron(주 1회) 첫 단계. 로컬 dev 눈검수 시 1회.

    How:
        ``bulkDir()/submissions.zip`` 대상. ``isBulkFresh`` TTL 통과 시 즉시 반환, 아니면 httpx 스트림
        (1MB 청크)으로 ``.tmp`` 기록 후 atomic replace + ``touchBulkFreshness``.

    Requires:
        - 인터넷 + SEC ``Archives/edgar/daily-index/bulkdata/submissions.zip`` 접근
        - ``_UA``(User-Agent) — SEC 403 회피
        - ``core.edgarBulkFreshness`` (TTL 상태)

    SeeAlso:
        - :func:`iterSubmissionsBulk` — 받은 zip 스트리밍 순회
        - :func:`dartlab.gather.edgar.bulk.downloadCompanyfactsBulk` — companyfacts 동형 벌크
    """
    zipPath = bulkDir() / "submissions.zip"
    if not force and zipPath.exists() and isBulkFresh(_TAG, ttlHours=ttlHours):
        _log.info("submissions.zip fresh (TTL=%dh) — 다운로드 스킵", ttlHours)
        return zipPath

    headers = {"User-Agent": _UA, "Accept-Encoding": "identity"}
    tmpPath = zipPath.with_suffix(".zip.tmp")
    with (
        httpx.Client(timeout=_TIMEOUT, headers=headers) as client,
        client.stream("GET", _SUBMISSIONS_BULK_URL, follow_redirects=True) as resp,
    ):
        resp.raise_for_status()
        with tmpPath.open("wb") as f:
            for data in resp.iter_bytes(chunk_size=1024 * 1024):
                f.write(data)
    tmpPath.replace(zipPath)
    touchBulkFreshness(_TAG, etag="")
    _log.info("submissions.zip 다운로드 완료 — %s (%.1f MB)", zipPath, zipPath.stat().st_size / 1024 / 1024)
    return zipPath


def cikFromStem(stem: str) -> str:
    """zip 엔트리 stem에서 CIK(0-padded 10자리) 추출. 메인·과거 페이지 공통.

    메인은 ``CIK0000104169``, 과거 페이지는 ``CIK0000104169-submissions-001``. 후자에서 CIK만
    떼려면 ``-`` 앞부분만 취해야 한다(옛 lstrip 방식은 과거 페이지 stem을 ``104169-submissions-001``로
    깨뜨려 cik→ticker 매핑 실패 = 과거 페이지 전량 누락 버그).

    Args:
        stem: zip 엔트리 파일명 stem (``CIK{10}`` 또는 ``CIK{10}-submissions-NNN``).

    Returns:
        str. 0-padded 10자리 CIK.

    Raises:
        없음. 순수 문자열 변환.

    Example:
        >>> cikFromStem("CIK0000104169-submissions-001")
        '0000104169'

    Requires:
        - 표준 라이브러리만.
    """
    core = stem.replace("CIK", "").split("-")[0]
    return (core.lstrip("0") or "0").zfill(10)


def iterSubmissionsBulk(zipPath: Path, *, recentOnly: bool = True) -> Iterator[tuple[str, dict]]:
    """submissions.zip 스트리밍 → (cik, submissions_json) yield (메인 회사 JSON만).

    zip 안에는 메인 ``CIK{10}.json``(recent 블록 + files 포인터) 과 과거 페이지
    ``CIK{10}-submissions-NNN.json`` 이 섞여 있다. recentOnly=True 면 과거 페이지를 건너뛰고 메인만 —
    공시 피드는 최근분이라 recent 블록(~1000건, 수년치)이면 충분하다.

    Args:
        zipPath: submissions.zip 경로.
        recentOnly: True 면 메인 ``CIK{10}.json`` 만 (과거 페이지 제외).

    Yields:
        ``(cik, payload)`` — cik 0-padded 10자리, payload = 회사 submissions JSON dict.

    Raises:
        zipfile.BadZipFile: zip 손상.

    Example:
        >>> for cik, js in iterSubmissionsBulk(Path("submissions.zip")):  # doctest: +SKIP
        ...     pass

    Requires:
        - ``downloadSubmissionsBulk`` 가 받아둔 로컬 ``submissions.zip``
        - 표준 라이브러리 ``zipfile`` / ``json`` (외부 의존 0 — 스트리밍 추출)
    """
    with zipfile.ZipFile(zipPath, "r") as zf:
        for info in zf.infolist():
            name = info.filename
            if not name.endswith(".json"):
                continue
            stem = Path(name).stem
            if not stem.startswith("CIK"):
                continue
            if recentOnly and "-submissions-" in stem:
                continue  # 과거 페이지(recent 블록만)
            cik = cikFromStem(stem)
            try:
                with zf.open(info) as f:
                    payload = json.load(f)
            except (json.JSONDecodeError, zipfile.BadZipFile, OSError) as exc:
                _log.warning("submissions zip entry %s 파싱 실패: %s", name, exc)
                continue
            yield cik, payload


__all__ = ["cikFromStem", "downloadSubmissionsBulk", "iterSubmissionsBulk"]
