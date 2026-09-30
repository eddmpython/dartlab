"""테스트 공통 도우미 — logger/stdout 캡처 패턴 + fixture-based Company.

Phase 3 Act4 — 구현 세부 (logger propagate, stdout clean, mockcompany 구조)
를 추상화해 refactor 시 연쇄 깨짐 완화.

사용 예::

    from tests._helpers import assertLogged, assertStdoutClean

    def test_download_message_goes_to_logger(capsys, caplog):
        import logging
        with caplog.at_level(logging.INFO, logger="dartlab.core.messaging"):
            from dartlab.core.messaging import emit
            emit("download:start", stockCode="005930", label="finance")
        assertStdoutClean(capsys)
        assertLogged(caplog, pattern="005930", logger="dartlab.core.messaging")
"""

from __future__ import annotations

import re
from typing import Any


def assertLogged(
    caplog: Any,
    pattern: str,
    *,
    logger: str | None = None,
    level: str | None = None,
) -> None:
    """caplog 에 특정 패턴의 레코드가 있는지 assert.

    Parameters
    ----------
    caplog : pytest.LogCaptureFixture
        ``caplog`` fixture.
    pattern : str
        레코드 메시지에 포함되어야 할 문자열 (regex 미사용, plain substring).
        정규식이 필요하면 ``pattern_re`` 변형을 만들어 사용.
    logger : str | None
        특정 logger 이름 필터 (예: "dartlab.viz"). None 이면 전체 검사.
    level : str | None
        최소 레벨 필터 ("INFO"/"WARNING"/"ERROR"). None 이면 전체.

    Raises
    ------
    AssertionError
        매칭 레코드 없을 때. 실제 캡처된 레코드 요약 포함.
    """
    records = caplog.records
    if logger is not None:
        records = [r for r in records if r.name == logger or r.name.startswith(logger + ".")]
    if level is not None:
        import logging as _logging

        min_level = getattr(_logging, level.upper())
        records = [r for r in records if r.levelno >= min_level]

    for r in records:
        if pattern in r.getMessage():
            return

    # 실패 — 디버그 정보 제공
    summary = [f"  {r.levelname} {r.name}: {r.getMessage()[:120]}" for r in records]
    raise AssertionError(
        f"패턴 '{pattern}' 를 포함하는 레코드 없음 (logger={logger!r}, level={level!r}).\n"
        f"  캡처된 {len(records)}건:\n" + "\n".join(summary[:10])
    )


def assertStdoutClean(capsys: Any) -> None:
    """capsys 의 stdout 이 비어 있음을 assert. 라이브러리 pollution 방어.

    라이브러리 내부 코드는 stdout 에 직접 쓰면 안 되며 logger 를 경유해야
    한다. 본 helper 는 그 계약을 테스트에서 검증.

    Raises
    ------
    AssertionError
        stdout 에 출력이 있을 때. 앞 300자 포함.
    """
    captured = capsys.readouterr()
    if captured.out:
        raise AssertionError(
            f"stdout 오염 감지 (라이브러리는 logger 사용, stdout 쓰기 금지):\n  {captured.out[:300]!r}"
        )


def assertStdoutContains(capsys: Any, pattern: str) -> None:
    """capsys 의 stdout 에 특정 패턴이 있는지 assert. print 기반 출력 검증용.

    사용 케이스: CLI 명령, viz marker (``<!--DARTLAB_VIZ:``), 사용자
    interactive (setup/ask) 등 **의도적** stdout 출력.

    Raises
    ------
    AssertionError
        매칭 실패 시 실제 stdout 앞 300자 포함.
    """
    captured = capsys.readouterr()
    if pattern not in captured.out:
        raise AssertionError(f"stdout 에 '{pattern}' 없음.\n  실제 stdout:\n  {captured.out[:300]!r}")


_VIZ_MARKER_RE = re.compile(r"<!--DARTLAB_VIZ:(.+?):VIZ_END-->", re.DOTALL)


def extractVizMarkers(stdout: str) -> list[dict]:
    """stdout 에서 DARTLAB_VIZ marker JSON 전수 추출.

    Parameters
    ----------
    stdout : str
        ``capsys.readouterr().out`` 원본.

    Returns
    -------
    list[dict]
        각 marker 의 JSON payload (chartType / title / series 등). marker
        없으면 빈 리스트.
    """
    import json

    out: list[dict] = []
    for m in _VIZ_MARKER_RE.finditer(stdout):
        try:
            out.append(json.loads(m.group(1)))
        except json.JSONDecodeError:
            pass
    return out


def buildVcr(
    cassette_dir: str,
    *,
    record_mode: str = "once",
    filter_query: list[str] | None = None,
    filter_headers: list[str] | None = None,
):
    """providers/* 외부 HTTP 호출 record-replay 카세트 생성기 — Track 7.

    Capabilities:
        vcrpy 의 VCR 인스턴스를 dartlab 표준 설정 (sanitize + match 룰)
        으로 생성. DART/EDGAR API 키 같은 민감 정보를 카세트에서 자동 제거.
    Args:
        cassette_dir: 카세트 저장 경로. 보통 tests/_cassettes/{provider}.
        record_mode: vcrpy 모드. "once" (없으면 record, 있으면 replay),
            "none" (replay only, 카세트 없으면 fail), "new_episodes" (추가만).
            CI 기본은 "none".
        filter_query: 쿼리 파라미터 sanitize 목록 (기본: crtfc_key, api_key).
        filter_headers: 헤더 sanitize 목록 (기본: Authorization, Cookie).
    Returns:
        vcr.VCR 인스턴스. .use_cassette('name.yaml') 컨텍스트 매니저 / 데코레이터.
    Example:
        >>> _vcr = buildVcr('tests/_cassettes/dart')
        >>> @_vcr.use_cassette('corpCode.yaml')
        ... def test_corpCode_replay():
        ...     from dartlab.gather.dart.corpCode import fetchCorpCode
        ...     df = fetchCorpCode()
        ...     assert df.height > 0
    Guide:
        첫 record 는 운영자 트리거 (API key 필요). 카세트 commit 후
        CI 에서 record_mode="none" 으로 replay 만.
    SeeAlso:
        tests/_cassettes/README.md (절차) · vcrpy 공식 문서.
    Requires:
        vcrpy>=6.0 (pyproject [dependency-groups].dev). httpx wrapping 지원.
    AIContext:
        DART/EDGAR API 응답 포맷 변경 시 fixture parquet 만으론 못 잡음.
        카세트는 raw HTTP body 까지 동결해 silent drift 차단.
    Raises:
        ImportError: vcrpy 미설치 시 (production install 에는 없는 dev dep).
    """
    try:
        import vcr
    except ImportError as e:  # pragma: no cover
        raise ImportError("vcrpy 미설치 — uv sync --group dev 후 재실행. tests/_cassettes/README.md 참조.") from e

    return vcr.VCR(
        cassette_library_dir=cassette_dir,
        record_mode=record_mode,
        filter_query_parameters=filter_query or ["crtfc_key", "api_key", "apikey"],
        filter_headers=filter_headers or ["Authorization", "Cookie", "X-Api-Key"],
        match_on=["method", "scheme", "host", "port", "path", "query"],
    )


def captureRichOutput(fn, *, width: int = 120, color: bool = False) -> str:
    """fn 호출 동안 dartlab Console 출력을 텍스트로 캡처 — syrupy snapshot 호환.

    Capabilities:
        dartlab.core.logger 의 공용 Console 을 임시 record-mode 로 교체해 rich
        Progress · Live · Console.print · RichHandler 로그를 한 문자열로 모은다.
        snapshot 동결로 CLI 시각 회귀를 자동 차단한다.
    Args:
        fn: 인자 없는 callable. 본 함수 안에서 호출되며 그 동안의 출력만 캡처.
        width: 터미널 폭 고정 (환경 독립성 — Windows / Linux ANSI 차이 제거).
        color: True 면 ANSI escape 포함, False 면 plain text.
    Returns:
        str. console.export_text(clear=False, styles=color) 결과.
    Example:
        >>> from tests._helpers import captureRichOutput
        >>> def emit_hf_marker():
        ...     from dartlab.core.logger import getLogger
        ...     getLogger(__name__).info("[cyan]⬇ HF[/] dartList.parquet")
        >>> text = captureRichOutput(emit_hf_marker)
        >>> "⬇ HF" in text
        True
    Guide:
        installRichHandler 가 호출됐을 때만 logger → Console 라우팅 동작.
        본 헬퍼가 자동으로 idempotent 호출.
    SeeAlso:
        dartlab.core.logger.installRichHandler · getConsole.
    Requires:
        rich Console.record=True 지원 (rich >= 12).
    AIContext:
        본 SSOT 통합 PR (commit ad520727b) 의 화면 일관성 acceptance test.
    Raises:
        없음. fn 내부 예외는 그대로 전파.
    """
    import io

    from rich.console import Console

    from dartlab.core import logger as _loggerMod

    _loggerMod.installRichHandler()
    buf = io.StringIO()
    # 실제 터미널의 TERM=dumb 또는 Windows legacy 탐지가 snapshot 폭과
    # 진행률 프레임을 바꾸지 않도록 캡처용 터미널만 같은 조건으로 고정한다.
    newConsole = Console(
        file=buf,
        record=True,
        force_terminal=True,
        force_interactive=True,
        force_jupyter=False,
        legacy_windows=False,
        width=width,
        color_system="truecolor",
        _environ={"TERM": "xterm-256color"},
    )
    savedConsole = _loggerMod._console
    savedProgress = _loggerMod._progress
    _loggerMod._console = newConsole
    # Progress singleton 도 reset — 이전 호출이 만든 Progress 가 이전 console 에
    # 묶여있으면 newConsole 로 redirect 안 됨. None 으로 비우면 다음 getProgress()
    # 가 newConsole 로 재생성.
    _loggerMod._progress = None
    try:
        savedRichHandler = None
        for h in _loggerMod.logging.getLogger(_loggerMod._ROOT_NAME).handlers:
            if hasattr(h, "console"):
                savedRichHandler = h
                h.console = newConsole
        fn()
        out = newConsole.export_text(clear=False, styles=color)
        # rich Progress BarColumn 은 환경 따라 character 가 다름 (Linux=`━` unicode
        # block, Windows cp949 fallback=`-` ASCII dash). snapshot 환경 독립성 위해
        # 두 형태를 한 ASCII dash 로 normalize.
        out = out.replace("━", "-")
        return out
    finally:
        _loggerMod._console = savedConsole
        _loggerMod._progress = savedProgress
        if savedRichHandler is not None:
            savedRichHandler.console = savedConsole
