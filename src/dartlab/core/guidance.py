"""사용자 안내 메시지 단일 출처.

모든 user-facing ``[dartlab]`` 메시지(진행, 힌트, 에러 안내)가 이 모듈을 경유한다.

Public API::

    from dartlab.core.guidance import emit, progress, format as fmt

    emit("download:start", stockCode="005930", label="DART 공시 문서 데이터")
    emit("error:no_data", stockCode="005930", raise_as=ValueError)
    progress("KRX KIND 상장법인 목록 다운로드 중...")
    msg = fmt("hint:stale", stockCode="005930", ageStr="120일")
"""

from __future__ import annotations

from typing import Any

_PREFIX = "[dartlab]"

# ── Simple Messages (template 문자열) ────────────────────────────

_SIMPLE: dict[str, str] = {
    # download (loadData / _ensureData / download)
    "download:start": "{stockCode} ({label}) → 첫 사용: GitHub에서 자동 다운로드 중...",
    "download:done": "✓ {label} 다운로드 완료 ({sizeStr})",
    "download:done_short": "✓ 다운로드 완료 ({sizeStr})",
    "download:exists": "✓ {stockCode} ({label}) 이미 존재",
    "download:progress": "{stockCode} ({label}) 다운로드 중...",
    "download:failed_single": "✗ {stockCode} ({label}) 다운로드 실패: {error}",
    "download:failed_item": "✗ {name} 실패: {error}",
    # downloadAll
    "download_all:query": "{label} — GitHub Release 에셋 목록 조회 중... ({tagCount}개 태그)",
    "download_all:tag_count": "  {tag}: {count}개",
    "download_all:start": "{action} {count}종목 다운로드 시작 (이미 존재: {skipped})",
    "download_all:uptodate": "✓ 전체 {count}종목 이미 최신",
    "download_all:done": "✓ 전체 다운로드 완료 → {dataDir}",
    "download_all:done_with_errors": "✓ 완료 (실패: {failed}건)",
    # EDGAR
    "edgar:fallback": "GitHub에 없음 → SEC EDGAR API에서 직접 수집 중... (최초 1회, 수 분 소요)",
    "edgar:sec_download": "{cik} (SEC EDGAR 재무 데이터) 로컬에 없음 → SEC API에서 다운로드 중...",
    "edgar:empty": "{cik} SEC API 응답이 비어있음 (데이터 없음)",
    "edgar:save_done": "저장 완료: {path}",
    "edgar:download_failed": "{cik} SEC API 다운로드 실패: {error}",
    "edgar:filing_limit": "{ticker} filing 수가 많아 최근 {maxFilings}건만 수집",
    "edgar:docs_start": "{ticker} EDGAR docs 원문 수집 시작 ({count} filings, since {sinceYear})",
    "edgar:docs_skip": "{ticker} filing {count}건 skip",
    "edgar:docs_save": "저장 완료: {path}",
    "edgar:batch_start": "EDGAR docs 배치 수집 시작 ({total} tickers, since {sinceYear})",
    "edgar:batch_progress": "{idx}건 처리 완료 → {cooldown:.1f}초 휴지",
    # listing
    "listing:download": "KRX KIND 상장법인 목록 다운로드 중...",
    "listing:done": "{count}개 종목 로드 완료",
    # scan
    "scan:signal_start": "서술형 시그널 스캔: {count}사",
    "scan:network_health": "그룹 건전성 분석 중...",
    # edgar universe
    "edgar:universe_update": "SEC listed universe 갱신 중...",
    "edgar:universe_save": "저장 완료: {path}",
}


# ── Structured Messages (actions + hasDartApiKey 분기) ───────────

class _StructuredMsg:
    """structured 메시지 정의. actions_with_key / actions_without_key로 분기."""

    __slots__ = ("template", "actions", "actions_with_key", "actions_without_key")

    def __init__(
        self,
        template: str,
        actions: list[str] | None = None,
        actions_with_key: list[str] | None = None,
        actions_without_key: list[str] | None = None,
    ):
        self.template = template
        self.actions = actions or []
        self.actions_with_key = actions_with_key or []
        self.actions_without_key = actions_without_key or []


_STRUCTURED: dict[str, _StructuredMsg] = {
    "hint:missing_docs": _StructuredMsg(
        template="{stockCode} ({label}) → GitHub Release에 없습니다.",
        actions_with_key=[
            "DART API 키가 설정되어 있으므로 직접 수집이 가능합니다:\n    dartlab collect {stockCode}",
        ],
        actions_without_key=[
            "DART API 키를 설정하면 직접 수집할 수 있습니다:\n    dartlab setup dart-key\n    dartlab collect {stockCode}",
        ],
    ),
    "hint:missing_other": _StructuredMsg(
        template="{stockCode} ({label}) → GitHub Release에 없습니다.",
        actions=["해당 종목이 dartlab 데이터셋에 포함되어 있는지 확인하세요."],
    ),
    "hint:stale": _StructuredMsg(
        template="{stockCode} docs 데이터가 {ageStr} 전 기준입니다.",
        actions_with_key=["최신 공시 반영: dartlab collect {stockCode}"],
        actions_without_key=[
            "갱신하려면 DART API 키 설정이 필요합니다:\n    dartlab setup dart-key",
        ],
    ),
    "error:download_failed": _StructuredMsg(
        template="데이터 다운로드 실패 ({stockCode}, {label}): {error}",
        actions=[
            "인터넷 연결을 확인하세요",
            "해당 종목이 dartlab 데이터셋에 포함되어 있는지 확인하세요\n  → DART: 한국 상장기업 ~2,700개 / EDGAR: 미국 상장기업 ~970개",
        ],
        actions_with_key=[
            "DART 공시 문서는 직접 수집 가능합니다:\n  dartlab collect {stockCode}",
        ],
        actions_without_key=[
            "DART API 키를 설정하면 직접 수집할 수 있습니다:\n  dartlab setup dart-key\n  dartlab collect {stockCode}",
        ],
    ),
    "error:no_data": _StructuredMsg(
        template="'{stockCode}' 데이터를 찾을 수 없습니다.",
        actions=[
            "종목코드가 올바른지 확인하세요 (6자리, 예: '005930')",
            "비상장 또는 dartlab 데이터셋에 미포함 종목일 수 있습니다",
            "인터넷 연결을 확인하세요 (첫 사용 시 자동 다운로드 필요)",
        ],
        actions_with_key=[
            "DART API 키가 설정되어 있으므로 직접 수집이 가능합니다:\n  dartlab collect {stockCode}",
            "종목 검색: dartlab.search('삼성') 또는 dartlab.listing()",
        ],
        actions_without_key=[
            "DART API 키를 설정하면 직접 수집할 수 있습니다:\n  dartlab setup dart-key\n  dartlab collect {stockCode}",
            "종목 검색: dartlab.search('삼성') 또는 dartlab.listing()",
        ],
    ),
}


# ── Lazy Context ─────────────────────────────────────────────────

class _Context:
    """hasDartApiKey, verbose 캐시 — lazy import으로 circular dependency 방지."""

    def __init__(self) -> None:
        self._dart_key: bool | None = None
        self._verbose: bool | None = None

    @property
    def has_dart_key(self) -> bool:
        if self._dart_key is None:
            try:
                from dartlab.engines.company.dart.openapi.client import hasDartApiKey
                self._dart_key = hasDartApiKey()
            except ImportError:
                self._dart_key = False
        return self._dart_key

    @property
    def verbose(self) -> bool:
        if self._verbose is None:
            from dartlab import config
            self._verbose = config.verbose
        return self._verbose

    def reset(self) -> None:
        """테스트나 config 변경 후 캐시 초기화."""
        self._dart_key = None
        self._verbose = None


_ctx = _Context()


# ── Internal Formatting ──────────────────────────────────────────

def _format_simple(key: str, **kwargs: Any) -> str:
    return _SIMPLE[key].format(**kwargs)


def _format_structured(msg: _StructuredMsg, **kwargs: Any) -> str:
    lines = [msg.template.format(**kwargs)]

    actions: list[str] = list(msg.actions)
    if msg.actions_with_key or msg.actions_without_key:
        if _ctx.has_dart_key:
            actions.extend(msg.actions_with_key)
        else:
            actions.extend(msg.actions_without_key)

    if actions:
        lines.append("")
        for action in actions:
            lines.append(f"  • {action.format(**kwargs)}")

    return "\n".join(lines)


# ── Public API ───────────────────────────────────────────────────

def emit(key: str, *, raise_as: type | None = None, **kwargs: Any) -> str:
    """메시지 조립 + 출력 (또는 예외).

    Parameters
    ----------
    key : str
        메시지 키. ``_SIMPLE`` 또는 ``_STRUCTURED``에 정의.
    raise_as : type | None
        ``ValueError`` / ``RuntimeError`` 등을 넘기면 print 대신 raise.
    **kwargs
        template 변수 (stockCode, label, sizeStr 등).

    Returns
    -------
    str
        조립된 메시지 문자열.
    """
    text = format(key, **kwargs)

    if raise_as is not None:
        raise raise_as(text)

    # structured 메시지(hint/error)는 verbose 무관하게 항상 출력
    if key in _STRUCTURED:
        if _ctx.verbose:
            print(f"{_PREFIX} {text}")
    else:
        # simple 메시지는 verbose일 때만 출력
        if _ctx.verbose:
            print(f"{_PREFIX} {text}")

    return text


def format(key: str, **kwargs: Any) -> str:
    """메시지만 조립하고 출력하지 않음. Server SSE, RuntimeError 등에서 사용."""
    if key in _STRUCTURED:
        return _format_structured(_STRUCTURED[key], **kwargs)
    return _format_simple(key, **kwargs)


def progress(text: str) -> None:
    """verbose-aware 한 줄 진행 메시지. ``config.verbose=False``이면 무시."""
    if _ctx.verbose:
        print(f"{_PREFIX} {text}")
