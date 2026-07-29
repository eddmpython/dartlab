"""gather/dart viewer 단위 테스트 — fixture HTML + 형식 검증.

requires_network 통합 테스트는 별도 마커로 표시. 일반 unit run 에서 제외.
"""

from __future__ import annotations

import pytest

pytestmark = pytest.mark.unit


def _nodeRecord(
    *,
    node: str = "node1",
    title: str = "1. 회사의 개요",
    rceptNo: str = "20240315000123",
    dcmNo: str = "9999999",
    eleId: str = "1",
    offset: str = "0",
    length: str = "12345",
    dtd: str = "dart4.xsd",
) -> str:
    return "\n".join(
        [
            f" {node}['text'] = \"{title}\";",
            f" {node}['dtd'] = \"{dtd}\";",
            f" {node}['length'] = \"{length}\";",
            f" {node}['offset'] = \"{offset}\";",
            f" {node}['eleId'] = \"{eleId}\";",
            f" {node}['dcmNo'] = \"{dcmNo}\";",
            f" {node}['rcpNo'] = \"{rceptNo}\";",
        ]
    )


class _Response:
    def __init__(self, text: str) -> None:
        self.text = text
        self.content = text.encode("utf-8")


class _StubClient:
    def __init__(self, responses: list[str | Exception]) -> None:
        self.responses = list(responses)
        self.urls: list[str] = []
        self.closed = False

    async def get(self, url: str):
        self.urls.append(url)
        response = self.responses.pop(0)
        if isinstance(response, Exception):
            raise response
        return _Response(response)

    async def close(self) -> None:
        self.closed = True


# ══════════════════════════════════════
# gather/dart/viewer — 형식 검증
# ══════════════════════════════════════


class TestRceptNoValidation:
    """rcept_no 형식 검증 (14자리 숫자)."""

    def test_valid_14digit(self):
        from dartlab.gather.dart.viewer import _validateRceptNo

        _validateRceptNo("20240315000123")  # 예외 없음

    def test_invalid_short(self):
        from dartlab.gather.dart.types import InvalidRceptNoError
        from dartlab.gather.dart.viewer import _validateRceptNo

        with pytest.raises(InvalidRceptNoError, match="14자리"):
            _validateRceptNo("12345")

    def test_invalid_letters(self):
        from dartlab.gather.dart.types import InvalidRceptNoError
        from dartlab.gather.dart.viewer import _validateRceptNo

        with pytest.raises(InvalidRceptNoError):
            _validateRceptNo("abcdefghijklmn")

    def test_invalid_15digit(self):
        from dartlab.gather.dart.types import InvalidRceptNoError
        from dartlab.gather.dart.viewer import _validateRceptNo

        with pytest.raises(InvalidRceptNoError):
            _validateRceptNo("123456789012345")


class TestViewerFetchBoundary:
    """index parse와 section fetch의 요청 수 및 오류 투명성."""

    def test_decodeKorean_uses_strict_cp949_fallback(self):
        from dartlab.gather.dart.viewer import _decodeKorean

        response = _Response("")
        response.text = "�"
        response.content = "본문".encode("cp949")
        assert _decodeKorean(response) == "본문"

    def test_decodeKorean_rejects_undecodable_bytes(self):
        from dartlab.gather.dart.types import ViewerPageParseError
        from dartlab.gather.dart.viewer import _decodeKorean

        response = _Response("")
        response.text = "�"
        response.content = b"\xff"
        with pytest.raises(ViewerPageParseError, match="인코딩"):
            _decodeKorean(response)

    @pytest.mark.asyncio
    async def test_limit_slices_before_section_fetch(self):
        from dartlab.gather.dart.viewer import fetchAsync

        client = _StubClient(
            [
                _nodeRecord(title="첫째", eleId="1")
                + "\n"
                + _nodeRecord(
                    node="node2",
                    title="둘째",
                    eleId="2",
                ),
                "<p>짧음</p>",
            ]
        )

        frame = await fetchAsync("20240315000123", client=client, limit=1)

        assert frame.height == 1
        assert frame["text"].to_list() == ["짧음"]
        assert len(client.urls) == 2
        assert "dsaf001/main.do" in client.urls[0]
        assert "eleId=1" in client.urls[1]

    @pytest.mark.asyncio
    async def test_limit_none_fetches_all_sections(self):
        from dartlab.gather.dart.viewer import fetchAsync

        client = _StubClient(
            [
                _nodeRecord(title="첫째", eleId="1")
                + "\n"
                + _nodeRecord(
                    node="node2",
                    title="둘째",
                    eleId="2",
                ),
                "<p>첫째</p>",
                "<p>둘째</p>",
            ]
        )

        frame = await fetchAsync("20240315000123", client=client)

        assert frame.height == 2
        assert frame["text"].to_list() == ["첫째", "둘째"]
        assert len(client.urls) == 3

    @pytest.mark.asyncio
    @pytest.mark.parametrize("limit", [0, -1, True, 1.5])
    async def test_invalid_limit_fails_before_http(self, limit):
        from dartlab.gather.dart.viewer import fetchAsync

        client = _StubClient([])
        with pytest.raises(ValueError, match="limit"):
            await fetchAsync("20240315000123", client=client, limit=limit)
        assert client.urls == []

    @pytest.mark.asyncio
    @pytest.mark.parametrize("failureAt", ["index", "section"])
    async def test_source_error_propagates_without_partial_frame(self, failureAt: str):
        from dartlab.gather.dart.viewer import fetchAsync
        from dartlab.gather.types import SourceUnavailableError

        failure = SourceUnavailableError(f"{failureAt} unavailable")
        responses: list[str | Exception]
        if failureAt == "index":
            responses = [failure]
        else:
            responses = [
                _nodeRecord(title="첫째", eleId="1") + "\n" + _nodeRecord(node="node2", title="둘째", eleId="2"),
                "<p>첫째</p>",
                failure,
            ]
        client = _StubClient(responses)

        with pytest.raises(SourceUnavailableError, match=failureAt):
            await fetchAsync("20240315000123", client=client)

    @pytest.mark.asyncio
    async def test_empty_section_is_typed_parse_error(self):
        from dartlab.gather.dart.types import ViewerPageParseError
        from dartlab.gather.dart.viewer import fetchAsync

        client = _StubClient([_nodeRecord(title="빈 본문"), "<html><body></body></html>"])
        with pytest.raises(ViewerPageParseError, match="빈 본문"):
            await fetchAsync("20240315000123", client=client)

    @pytest.mark.asyncio
    async def test_owned_client_closes_on_failure(self, monkeypatch: pytest.MonkeyPatch):
        from dartlab.gather.dart import viewer
        from dartlab.gather.types import SourceUnavailableError

        client = _StubClient([SourceUnavailableError("index unavailable")])
        monkeypatch.setattr(viewer, "GatherHttpClient", lambda: client)

        with pytest.raises(SourceUnavailableError):
            await viewer.fetchAsync("20240315000123")
        assert client.closed is True

    def test_docMeta_fetches_only_index(self):
        from dartlab.gather.dart.viewer import docMeta

        client = _StubClient(
            [
                _nodeRecord(title="첫째", eleId="1")
                + "\n"
                + _nodeRecord(
                    node="node2",
                    title="둘째",
                    eleId="2",
                )
            ]
        )

        meta = docMeta("20240315000123", client=client)

        assert meta.sectionCount == 2
        assert len(client.urls) == 1
        assert "dsaf001/main.do" in client.urls[0]

    @pytest.mark.asyncio
    async def test_docMeta_owned_client_closes(self, monkeypatch: pytest.MonkeyPatch):
        from dartlab.gather.dart import viewer

        client = _StubClient([_nodeRecord()])
        monkeypatch.setattr(viewer, "GatherHttpClient", lambda: client)

        meta = await viewer._docMetaAsync("20240315000123")

        assert meta.sectionCount == 1
        assert client.closed is True


# ══════════════════════════════════════
# gather/dart/__init__ + GatherEntry 통합
# ══════════════════════════════════════


class TestPublicSurface:
    """Dart facade, GatherEntry 축 등록 확인."""

    def test_dart_class_available(self):
        from dartlab.gather.dart import Dart

        d = Dart()
        assert callable(d.doc)
        assert callable(d.meta)

    def test_viewer_parse_error_is_public(self):
        from dartlab.gather.dart import DartDocError, ViewerPageParseError

        assert issubclass(ViewerPageParseError, DartDocError)

    def test_gather_entry_axis_registered(self):
        from dartlab.gather.entry import API_KEY_INFO, AXIS_REGISTRY

        assert "dartDoc" in AXIS_REGISTRY
        assert "dartDoc" in API_KEY_INFO
        assert API_KEY_INFO["dartDoc"].startswith("불필요")
        entry = AXIS_REGISTRY["dartDoc"]
        assert entry.targetType == "rceptNo"

    def test_gather_class_has_dartDoc_method(self):
        from dartlab.gather import Gather

        assert callable(getattr(Gather, "dartDoc", None))

    def test_domain_policy_registered(self):
        from dartlab.gather.infra.http import DOMAIN_POLICY

        assert "dart.fss.or.kr" in DOMAIN_POLICY
