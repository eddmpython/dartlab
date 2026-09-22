"""DART allFilings 단일 원문 응답 parser와 fetch 경계를 검증한다."""

import io
import zipfile

import pytest

from dartlab.gather.dart.allFilingsDocument import collectOneRaw, parseDocumentResponse

pytestmark = pytest.mark.unit


def _zipBytes(files: dict[str, bytes]) -> bytes:
    """테스트용 ZIP 응답을 메모리에서 만든다."""
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w") as archive:
        for name, content in files.items():
            archive.writestr(name, content)
    return buffer.getvalue()


def test_parse_document_response_preserves_largest_raw_document() -> None:
    """ZIP 안 가장 큰 공시 원문을 태그 변형 없이 보존한다."""
    expected = '<DOCUMENT ATOCID="1"><TITLE ATOC="Y">원문</TITLE></DOCUMENT>'
    raw = _zipBytes(
        {
            "small.xml": b"<x/>",
            "report.xml": expected.encode(),
        }
    )

    content, status = parseDocumentResponse(raw)

    assert status == "ok"
    assert content == expected


@pytest.mark.parametrize("statusCode", ["013", "014"])
def test_parse_document_response_distinguishes_declared_no_body(statusCode: str) -> None:
    """DART가 명시한 접수번호 오류와 파일 부재만 최종 no_body로 분류한다."""
    raw = f"<result><status>{statusCode}</status></result>".encode()

    assert parseDocumentResponse(raw) == (None, "no_body")


@pytest.mark.parametrize(
    "raw",
    [
        None,
        b"",
        b"PK\x03\x04broken",
        b"<result><status>020</status></result>",
    ],
)
def test_parse_document_response_marks_retryable_failures(raw: bytes | None) -> None:
    """응답 부재, 손상 ZIP, API 한도 응답은 재시도 가능한 error다."""
    assert parseDocumentResponse(raw) == (None, "error")


def test_collect_one_raw_converts_client_failure_to_retryable_error() -> None:
    """client 실행 실패가 수집 파이프라인을 깨지 않고 error 상태로 전달된다."""

    class FailingClient:
        def getBytes(self, endpoint, params):
            raise OSError("network down")

    assert collectOneRaw(FailingClient(), "20260527000001") == (None, "error")


def _patchedZip(
    *,
    flagBits: int = 0,
    compressType: int | None = None,
    dataPatch: dict[int, int] | None = None,
    compression: int = zipfile.ZIP_DEFLATED,
    badUtf8Name: bool = False,
) -> bytes:
    """멤버를 읽을 때 BadZipFile 이 아닌 예외를 내는 ZIP 을 만든다(헤더 필드 직접 수정).

    ``dataPatch`` 는 압축 데이터 시작 기준 오프셋의 바이트를 덮어쓴다.
    """
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w", compression=compression) as archive:
        archive.writestr("report.xml", b"<DOCUMENT>" + b"x" * 400 + b"</DOCUMENT>")
    raw = bytearray(buffer.getvalue())
    local = raw.find(b"PK\x03\x04")
    central = raw.find(b"PK\x01\x02")
    if flagBits:
        raw[local + 6] |= flagBits
        raw[central + 8] |= flagBits
    if compressType is not None:
        raw[local + 8 : local + 10] = compressType.to_bytes(2, "little")
        raw[central + 10 : central + 12] = compressType.to_bytes(2, "little")
    if dataPatch:
        nameLen = int.from_bytes(raw[local + 26 : local + 28], "little")
        extraLen = int.from_bytes(raw[local + 28 : local + 30], "little")
        start = local + 30 + nameLen + extraLen
        for offset, value in dataPatch.items():
            raw[start + offset] = value
    if badUtf8Name:  # UTF-8 파일명 플래그 + 디코딩 불가 바이트: ZipFile 을 여는 순간 UnicodeDecodeError
        raw[central + 9] |= 0x08
        nameLen = int.from_bytes(raw[central + 28 : central + 30], "little")
        raw[central + 46 : central + 46 + nameLen] = b"\xff" * nameLen
    return bytes(raw)


@pytest.mark.parametrize(
    "raw",
    [
        _patchedZip(flagBits=0x1),  # 암호화 플래그: zipfile 이 RuntimeError
        _patchedZip(compressType=99),  # 미지원 압축 방식: NotImplementedError
        _patchedZip(dataPatch=dict.fromkeys(range(8), 0xFF)),  # 깨진 deflate 스트림: zlib.error
        _patchedZip(dataPatch=dict.fromkeys(range(8), 0xFF), compression=zipfile.ZIP_BZIP2),  # 깨진 bzip2: OSError
        _patchedZip(dataPatch={4: 0xFF}, compression=zipfile.ZIP_LZMA),  # lzma 속성 바이트 이상: LZMAError
        _patchedZip(badUtf8Name=True),  # 파일명 디코딩 실패: UnicodeDecodeError
    ],
    ids=["encrypted", "unsupportedCompression", "brokenDeflate", "brokenBzip2", "brokenLzma", "badUtf8Name"],
)
def test_parse_document_response_unreadable_zip_member_is_retryable_error(raw: bytes) -> None:
    """멤버를 못 읽는 ZIP 도 예외 대신 error 다. 호출측 수집 루프(reconcile·fillContent)가 죽지 않는다."""
    assert parseDocumentResponse(raw) == (None, "error")
