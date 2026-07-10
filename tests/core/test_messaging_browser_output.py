"""브라우저(pyodide) 셀 출력 오염 가드.

노트북은 stderr 를 그대로 셀 출력에 담는다. 그래서 core.messaging 이 흘리는 것은
전부 학습자 화면에 뜬다. 여기서 세 가지를 못 박는다.

1. 구조화 이벤트(``message_emit``)는 브라우저에서 나가지 않는다. 이벤트 이름을 메시지
   본문으로 찍는 구조라, 소비자도 없는 브라우저에서는 날문자열 노출일 뿐이다.
2. 브라우저 첫 scan 은 "데이터 없음" 이 아니라 "내려받는 중" 이다. 정상 경로다.
3. 사용자에게 보이는 문구에 긴 줄표를 쓰지 않는다.
"""

from __future__ import annotations

import pathlib

from dartlab.core import messaging
from dartlab.core.messagingCatalog import SIMPLE, STRUCTURED

_CATALOG = pathlib.Path(messaging.__file__).parent / "messagingCatalog.py"
_EM_DASH = chr(0x2014)
_EN_DASH = chr(0x2013)
_EM_ESCAPE = chr(92) + "u2014"


def test_structuredEvent_isSilentOnPyodide(monkeypatch) -> None:
    """emscripten 에서는 구조화 이벤트를 내보내지 않는다."""
    called: list[str] = []
    monkeypatch.setattr("dartlab.core.logger.logEvent", lambda *a, **k: called.append(a[1]))

    monkeypatch.setattr(messaging.sys, "platform", "linux")
    messaging._emitStructured("message_emit", key="scan:prebuild_ready")
    assert called == ["message_emit"], "서버에서는 그대로 나가야 한다"

    called.clear()
    monkeypatch.setattr(messaging.sys, "platform", "emscripten")
    messaging._emitStructured("message_emit", key="scan:prebuild_ready")
    assert called == [], "브라우저에서는 한 건도 나가면 안 된다"


def test_browserFirstScan_saysDownloadingNotMissing() -> None:
    """브라우저 첫 scan 문구가 '없음' 이 아니라 '내려받는 중' 이다."""
    text = messaging.formatMessage("scan:prebuild_download_lite")
    assert "없음" not in text
    assert "내려받" in text

    ready = messaging.formatMessage("scan:prebuild_ready_lite", sizeStr="19.3MB")
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
