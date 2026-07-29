"""브라우저(pyodide) 셀 출력 오염 가드.

노트북은 stderr 를 그대로 셀 출력에 담는다. 그래서 core.messaging 이 흘리는 것은
전부 학습자 화면에 뜬다. 여기서 세 가지를 못 박는다.

1. native 구조화 메타데이터는 사용자 메시지와 같은 레코드에 붙고 브라우저에서는 빠진다.
2. 브라우저 첫 scan 은 "데이터 없음" 이 아니라 "내려받는 중" 이다. 정상 경로다.
3. 사용자에게 보이는 문구에 긴 줄표를 쓰지 않는다.
"""

from __future__ import annotations

import logging
import pathlib

import pytest

from dartlab.core import messaging
from dartlab.core.messagingCatalog import SIMPLE, STRUCTURED
from dartlab.core.messagingFormatting import formatMessage

_CATALOG = pathlib.Path(messaging.__file__).parent / "messagingCatalog.py"
_EM_DASH = chr(0x2014)
_EN_DASH = chr(0x2013)
_EM_ESCAPE = chr(92) + "u2014"


def test_publicFacade_exportsOnlyEmissionPrimitives() -> None:
    """L0 facade는 상위 안내 정책을 재수출하지 않는다."""
    assert messaging.__all__ == ["emit", "format", "progress"]


@pytest.mark.parametrize(("platform", "hasEvent"), [("linux", True), ("emscripten", False)])
def test_structuredMetadata_staysOnSingleUserRecord(caplog, monkeypatch, platform: str, hasEvent: bool) -> None:
    """메시지 한 건은 로그 한 건이며 native에서만 같은 레코드에 메타데이터가 붙는다."""
    monkeypatch.setattr(messaging.sys, "platform", platform)

    with caplog.at_level(logging.INFO, logger="dartlab"):
        messaging.emit("download:done_short", sizeStr="1MB")

    records = [record for record in caplog.records if record.name.startswith("dartlab")]
    assert [record.getMessage() for record in records] == ["[dartlab] ✓ 다운로드 완료 (1MB)"]
    assert hasattr(records[0], "event") is hasEvent
    if hasEvent:
        assert records[0].event == "message_emit"
        assert records[0].fields == {
            "key": "download:done_short",
            "kind": "structured",
        }


def test_emit_doesNotSwallowLoggerFailure(monkeypatch) -> None:
    """메시지 전송 실패를 성공으로 숨기지 않는다."""

    def _fail(*args, **kwargs) -> None:
        raise RuntimeError("message sink failed")

    monkeypatch.setattr(messaging._log, "info", _fail)

    with pytest.raises(RuntimeError, match="message sink failed"):
        messaging.emit("download:done_short", sizeStr="1MB")


def test_emit_addsPrefixExactlyOnce(caplog, monkeypatch) -> None:
    """catalog 본문과 logger가 [dartlab] prefix를 중복하지 않는다."""
    monkeypatch.setattr(messaging.sys, "platform", "linux")

    with caplog.at_level(logging.INFO, logger="dartlab"):
        messaging.emit("edgar:bulk_download_start")

    messages = [record.getMessage() for record in caplog.records if record.name.startswith("dartlab")]
    assert messages == ["[dartlab] SEC EDGAR 재무 데이터 전체 다운로드 중 (~1.37GB, 최초 1회 5~15분). companyfacts.zip"]


def test_browserFirstScan_saysDownloadingNotMissing() -> None:
    """브라우저 첫 scan 문구가 '없음' 이 아니라 '내려받는 중' 이다."""
    text = formatMessage("scan:prebuild_download_lite")
    assert "없음" not in text
    assert "내려받" in text

    ready = formatMessage("scan:prebuild_ready_lite", sizeStr="19.3MB")
    assert "19.3MB" in ready
    assert "개 파일" not in ready, "용량을 파일 수 자리에 넣던 옛 버그"


def test_userFacingCopy_hasNoLongDash() -> None:
    """카탈로그 문구에 긴 줄표도, 그 유니코드 이스케이프도 없다."""
    raw = _CATALOG.read_text(encoding="utf-8")
    assert _EM_DASH not in raw, "긴 줄표 문자"
    assert _EM_ESCAPE not in raw, "긴 줄표 이스케이프"

    rendered = list(SIMPLE.values()) + [m.template for m in STRUCTURED.values()]
    offenders = [t for t in rendered if _EM_DASH in t or _EN_DASH in t]
    assert not offenders, f"사용자 노출 문구에 긴 줄표: {offenders[:3]}"
