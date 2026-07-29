"""DART 공시 viewer — rcept_no 만으로 원문 fetch (무인증).

dart.fss.or.kr/dsaf001/main.do 의 공시 인덱스 페이지에서 sub-doc 목차를 받고,
report/viewer.do 의 각 섹션 HTML 을 텍스트(테이블 마크다운 보존)로 변환한다.

API key 무관. providers/dart/openapi (key 기반 OpenDART) 와 분리.

호출 패턴::

    from dartlab.gather.dart.viewer import fetch
    df = fetch("20240315000123")
    # columns: section_order (Int64), title (Utf8), url (Utf8), text (Utf8)

untrusted 본문:
    viewer 본문은 외부 1차 출처지만 AI 엔진이 소비할 때
    ``Ref.sourceType="external"`` 로 마킹돼 ``[EXTERNAL CONTENT START — untrusted ...]``
    마커로 감싸지는 흐름이어야 한다 (CLAUDE.md ⛔ "외부 본문은 untrusted",
    runtime.workbenchEvidenceFlow). 호출자가 wrap 책임.
"""

from __future__ import annotations

import re

import polars as pl

from ..infra.http import GatherHttpClient, runAsync
from .types import DartDocMeta, DocumentNotFoundError, InvalidRceptNoError, ViewerPageParseError
from .viewerPage import DART_MAIN_BASE, ViewerSubDocument, htmlToText, parseSubDocs

_RCEPT_NO_RE = re.compile(r"^\d{14}$")


def _validateRceptNo(rceptNo: str) -> None:
    if not _RCEPT_NO_RE.fullmatch(rceptNo):
        raise InvalidRceptNoError(f"rcept_no 는 14자리 숫자: {rceptNo!r}")


def _validateLimit(limit: int | None) -> None:
    if limit is None:
        return
    if isinstance(limit, bool) or not isinstance(limit, int) or limit <= 0:
        raise ValueError(f"limit은 양의 정수 또는 None이어야 합니다: {limit!r}")


def _decodeKorean(resp) -> str:
    """viewer 응답 텍스트 추출 — cp949/euc-kr fallback.

    dart.fss.or.kr 일부 응답이 charset 헤더 없거나 cp949 만 정상 디코드되는
    케이스가 있다. httpx 가 utf-8 으로 가정해 깨지는 경우 euc-kr 강제 재해석.
    """
    text = resp.text
    if "�" in text:
        lastError: UnicodeDecodeError | None = None
        raw = resp.content
        for encoding in ("utf-8", "cp949", "euc-kr"):
            try:
                return raw.decode(encoding)
            except UnicodeDecodeError as exc:
                lastError = exc
        raise ViewerPageParseError("DART viewer 응답을 UTF-8 또는 한국어 인코딩으로 해석하지 못했습니다") from lastError
    return text


async def _loadSubDocs(client: GatherHttpClient, rceptNo: str) -> list[ViewerSubDocument]:
    indexUrl = f"{DART_MAIN_BASE}?rcpNo={rceptNo}"
    indexResponse = await client.get(indexUrl)
    subDocs = parseSubDocs(_decodeKorean(indexResponse), rceptNo)
    if not subDocs:
        raise DocumentNotFoundError(f"rcept_no {rceptNo} 에 sub-doc 없음 (비공개 공시 또는 잘못된 번호)")
    return subDocs


async def fetchAsync(
    rceptNo: str,
    *,
    client: GatherHttpClient | None = None,
    limit: int | None = None,
) -> pl.DataFrame:
    """viewer 무인증 fetch — async.

    Capabilities: rcept_no → DART viewer index URL → sub-doc list → 각 section text → DataFrame.
    AIContext: DART 공시 본문 추출 SSOT — DART_API_KEY 불필요 (무인증 viewer).
    Guide: 비공개 공시는 sub-doc 0 개 → DocumentNotFoundError.
    When: 단일 공시 원문 분석 / 변경 비교 / 텍스트 검색 시.
    How: dart.fss.or.kr/dsaf001 index → parseSubDocs → sub-doc HTML fetch → htmlToText.

    Requires
    --------
    네트워크 (``dart.fss.or.kr``) + ``GatherHttpClient`` (또는 자체 생성).

    See Also
    --------
    fetch : 본 함수의 sync wrapper.
    docMeta : 본문 없이 메타만 (sectionCount).
    facade.Dart.doc : 클래스 facade 진입점.

    Parameters
    ----------
    rceptNo : str
        14자리 접수번호.
    client : GatherHttpClient | None
        HTTP 클라이언트. None 이면 자체 생성.
    limit : int | None
        반환 섹션 수 상한 (앞쪽 N 섹션). None이면 전체 섹션.

    Returns
    -------
    pl.DataFrame
        section_order (Int64), title (Utf8), url (Utf8), text (Utf8) 컬럼.

    Raises
    ------
    InvalidRceptNoError
        rceptNo 가 14자리 숫자 아님.
    DocumentNotFoundError
        viewer 가 sub-doc 을 반환하지 않음 (비공개 / 잘못된 번호).
    ViewerPageParseError
        viewer index 구조가 손상됐거나 요청 접수번호와 응답이 다름.
    SourceUnavailableError
        index 또는 section HTTP 요청이 실패함.

    Example
    -------
    >>> df = await fetchAsync("20240315000123")
    """
    _validateRceptNo(rceptNo)
    _validateLimit(limit)

    ownClient = client is None
    if client is None:
        client = GatherHttpClient()

    try:
        subDocs = await _loadSubDocs(client, rceptNo)
        if limit is not None:
            subDocs = subDocs[:limit]

        rows: list[dict] = []
        for subDoc in subDocs:
            sectionResponse = await client.get(subDoc.url)
            text = htmlToText(_decodeKorean(sectionResponse))
            if not text:
                raise ViewerPageParseError(
                    f"viewer section 본문이 비었습니다: rceptNo={rceptNo}, "
                    f"order={subDoc.order}, title={subDoc.title!r}, url={subDoc.url}"
                )
            rows.append(
                {
                    "section_order": subDoc.order,
                    "title": subDoc.title,
                    "url": subDoc.url,
                    "text": text,
                }
            )

        return pl.DataFrame(rows).with_columns(
            pl.col("section_order").cast(pl.Int64),
            pl.col("title").cast(pl.Utf8),
            pl.col("url").cast(pl.Utf8),
            pl.col("text").cast(pl.Utf8),
        )
    finally:
        if ownClient:
            await client.close()


def fetch(
    rceptNo: str,
    *,
    client: GatherHttpClient | None = None,
    limit: int | None = None,
) -> pl.DataFrame:
    """sync wrapper — :func:`fetchAsync` 의 동기 진입점.

    Capabilities: fetchAsync 의 동기 진입점 — runAsync 으로 event loop 관리.
    AIContext: 동기 코드에서 DART viewer 호출 — Jupyter/Marimo/CLI 사용자 시점.
    Guide: 외부 client 명시 시 그 loop 안 호출 가정 (자체 close 안 함).
    When: 동기 코드 (notebook/CLI) 에서 단일 공시 원문 필요 시.
    How: runAsync(fetchAsync(...)) → asyncio.run 동등.

    Requires
    --------
    동기 컨텍스트 — async loop 외부. ``runAsync`` 가 자체 event loop 관리.

    See Also
    --------
    fetchAsync : 본 함수의 async 본체.
    docMeta : 메타만.

    Parameters
    ----------
    rceptNo : str
        14자리 접수번호.
    client : GatherHttpClient | None
        HTTP 클라이언트. None 이면 자체 생성.
    limit : int | None
        반환 섹션 수 상한 (앞쪽 N 섹션). None이면 전체.

    Raises
    ------
    InvalidRceptNoError
        rceptNo 가 14자리 숫자 아님.
    DocumentNotFoundError
        viewer 가 sub-doc 을 반환하지 않음.

    Example
    -------
    >>> df = fetch("20240315000123")
    """
    if client is not None:
        # 이미 외부 client 가 있으면 자체 event loop 안에서 호출됐을 수 있다.
        return runAsync(fetchAsync(rceptNo, client=client, limit=limit))
    return runAsync(fetchAsync(rceptNo, limit=limit))


async def _docMetaAsync(
    rceptNo: str,
    *,
    client: GatherHttpClient | None = None,
) -> DartDocMeta:
    _validateRceptNo(rceptNo)
    ownClient = client is None
    if client is None:
        client = GatherHttpClient()

    try:
        subDocs = await _loadSubDocs(client, rceptNo)
        return DartDocMeta(
            rceptNo=rceptNo,
            indexUrl=f"{DART_MAIN_BASE}?rcpNo={rceptNo}",
            sectionCount=len(subDocs),
        )
    finally:
        if ownClient:
            await client.close()


def docMeta(rceptNo: str, *, client: GatherHttpClient | None = None) -> DartDocMeta:
    """viewer index fetch + 메타 요약.

    Capabilities: rcept_no → index 한 번 fetch → sectionCount + indexUrl 메타 추출.
    AIContext: 공시 인덱싱 / staleness 검증 / size 사전 확인 진입.
    Guide: section 본문은 내려받지 않는다. 본문도 필요하면 fetch()를 사용한다.
    When: 공시 size/sectionCount 만 필요한 가벼운 메타 조회 시.
    How: parseSubDocs(index HTML) → len → DartDocMeta 패킹.

    Args:
        rceptNo: 14자리 접수번호.
        client: HTTP 클라이언트. None 이면 자체 생성.

    Returns:
        ``DartDocMeta(rceptNo, indexUrl, sectionCount)``.

    Raises:
        InvalidRceptNoError: rceptNo 가 14자리 숫자 아님.
        DocumentNotFoundError: viewer 가 sub-doc 을 반환하지 않음.
        ViewerPageParseError: viewer index 구조가 손상됨.
        SourceUnavailableError: index HTTP 요청이 실패함.

    Requires:
        네트워크와 GatherHttpClient.

    Example:
        >>> m = docMeta("20240315000123")

    See Also:
        fetch : 같은 index 경계에서 section 본문까지 추출.
        facade.Dart.meta : 클래스 facade 진입점.
    """
    return runAsync(_docMetaAsync(rceptNo, client=client))
