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
