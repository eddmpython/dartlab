"""DART allFilings 원문 응답을 보존형 본문과 수집 상태로 변환한다.

``allFilingsCollector`` 는 날짜별 수집과 parquet 병합을 맡고, 이 모듈은 단일
``document.xml`` 응답의 fetch와 해석만 맡는다. 정상 ZIP에서는 가장 큰 원문 파일을
후처리 없이 디코딩하고, DART가 명시한 본문 부재와 재시도 가능한 실패를 구분한다.
"""

from __future__ import annotations

import io
import zipfile
from typing import TYPE_CHECKING, Literal, TypeAlias

if TYPE_CHECKING:
    from dartlab.gather.dart.client import DartClient

FetchStatus: TypeAlias = Literal["ok", "no_body", "error"]
DocumentResult: TypeAlias = tuple[str | None, FetchStatus]

_NO_BODY_STATUSES = ("<status>014", "<status>013")
_DOCUMENT_ENCODINGS = ("utf-8", "euc-kr", "cp949")


def parseDocumentResponse(raw: bytes | None) -> DocumentResult:
    """DART ``document.xml`` 응답을 raw 본문과 상태로 변환한다.

    Args:
        raw: DART 응답 bytes. 응답 부재는 ``None``.

    Returns:
        ``(contentRaw, fetchStatus)``. 정상 ZIP은 ``ok``, DART의 013/014 상태는
        ``no_body``, 손상 또는 알 수 없는 응답은 ``error``.

    Raises:
        없음. 원격 응답의 손상과 디코딩 실패는 재시도 가능한 ``error`` 상태다.

    Example:
        >>> parseDocumentResponse(b"<result><status>014</status></result>")
        (None, 'no_body')

    Capabilities:
        - DART ZIP 원문을 가장 큰 파일 기준으로 선택하고 태그를 변형 없이 보존한다.
        - 명시적 본문 부재와 재시도 가능한 응답 실패를 구분한다.

    AIContext:
        allFilings 수집기가 저장 여부와 재시도를 결정할 때 쓰는 내부 응답 해석기다.

    Guide:
        네트워크 호출은 ``collectOneRaw``에 맡기고, 이미 받은 bytes의 상태 판정이나
        parser 단위 검증에만 이 함수를 사용한다.

    When:
        DART ``document.xml`` 응답을 parquet row로 옮기기 전에 원문과 상태가 필요할 때.

    How:
        응답 종류 판정, ZIP 원문 선택, 문자셋 디코딩, 상태 분류 순서로 처리한다.

    Requires:
        - DART ``document.xml`` 응답 형식.
        - Python 표준 라이브러리 ``zipfile``.

    SeeAlso:
        - ``collectOneRaw``: DART client fetch를 포함한 단일 공시 수집 경계.
        - ``allFilingsCollector.fillContent``: 날짜별 수집과 parquet 병합 파이프라인.

    LLM Specifications:
        AntiPatterns:
            - 013/014 외 상태를 영구적인 본문 부재로 분류하지 않는다.
            - raw XML/HTML을 정규화하거나 태그를 제거하지 않는다.
        Prerequisites:
            - DART ``document.xml`` 원응답 bytes.
        Freshness:
            - 호출 시점의 DART 원응답을 그대로 판정한다.
        Dataflow:
            - document.xml bytes -> 응답 판정 -> raw 본문과 fetch status.
        TargetMarkets:
            - KR (DART).
    """
    if not raw:
        return (None, "error")

    if raw[:4] == b"PK\x03\x04":
        try:
            with zipfile.ZipFile(io.BytesIO(raw)) as archive:
                names = archive.namelist()
                if not names:
                    return (None, "error")
                largest = max(names, key=lambda name: archive.getinfo(name).file_size)
                content = archive.read(largest)
        except zipfile.BadZipFile:
            return (None, "error")

        rawContent: str | None = None
        for encoding in _DOCUMENT_ENCODINGS:
            try:
                rawContent = content.decode(encoding)
                break
            except (UnicodeDecodeError, LookupError):
                continue
        if rawContent is None:
            rawContent = content.decode("utf-8", errors="replace")
        if not rawContent.strip():
            return (None, "error")
        return (rawContent, "ok")

    statusText = raw[:300].decode("utf-8", errors="replace")
    if any(status in statusText for status in _NO_BODY_STATUSES):
        return (None, "no_body")
    return (None, "error")


def collectOneRaw(client: DartClient, rceptNo: str) -> DocumentResult:
    """단일 공시 원문을 fetch해 보존형 raw 본문과 수집 상태를 반환한다.

    Args:
        client: DART ``document.xml`` 호출 client.
        rceptNo: 공시 접수번호.

    Returns:
        ``(contentRaw, fetchStatus)``. ``error``만 재시도 대상이다.

    Raises:
        없음. 네트워크와 API 실행 오류는 재시도 가능한 ``error`` 상태로 반환한다.

    Requires:
        - 인터넷 연결과 유효한 DART API 자격증명을 가진 client.

    Example:
        >>> collectOneRaw(client, "20260527000001")  # doctest: +SKIP
    """
    try:
        raw = client.getBytes("document.xml", {"rcept_no": rceptNo})
    except (RuntimeError, OSError):
        return (None, "error")
    return parseDocumentResponse(raw)
