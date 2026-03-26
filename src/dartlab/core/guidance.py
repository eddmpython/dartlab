"""사용자 안내 메시지 단일 출처.

모든 user-facing ``[dartlab]`` 메시지(진행, 힌트, 에러 안내)가 이 모듈을 경유한다.

Public API::

    from dartlab.core.guidance import emit, progress, format as fmt

    emit("download:start", stockCode="005930", label="DART 공시 문서 데이터")  # HF 우선 → GH fallback
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
    "download:start": "{stockCode} ({label}) → 첫 사용: 자동 다운로드 중...",
    "download:done": "✓ {label} 다운로드 완료 ({sizeStr})",
    "download:done_short": "✓ 다운로드 완료 ({sizeStr})",
    "download:exists": "✓ {stockCode} ({label}) 이미 존재",
    "download:progress": "{stockCode} ({label}) 다운로드 중...",
    "download:failed_single": "✗ {stockCode} ({label}) 다운로드 실패: {error}",
    "download:failed_item": "✗ {name} 실패: {error}",
    "download:refreshed": "✓ {stockCode} 데이터 갱신 완료",
    # downloadAll (HuggingFace snapshot_download)
    "download_all:hf_start": "{label} — HuggingFace ({repo}/{dir}) 전체 다운로드 시작...",
    "download_all:hf_retry": "⚠ 다운로드 재시도 ({attempt}/{maxRetries})... {error}",
    "download_all:hf_done": "✓ {label} 전체 다운로드 완료 — {count}종목 → {dataDir}",
    # collect (투채널 자동 수집)
    "collect:start": "{stockCode} ({label}) → 로컬에 없음. DART API로 수집 중... ({keyCount}키 {mode})",
    "collect:done": "✓ {label} 수집 완료 ({sizeStr})",
    "collect:skip": "✓ {stockCode} ({label}) 이미 수집됨",
    "collect:no_key": "DART API 키가 있으면 자동 수집 가능합니다: dartlab setup dart-key",
    "collect:batch_start": "{stockCode} → 로컬에 없음. {categories} {keyCount}키 병렬 수집 시작...",
    "collect:batch_done": "✓ {stockCode} 수집 완료 ({summary})",
    "collect:exhausted": "⚠ DART API 일일 한도 도달. 내일 다시 시도하거나 추가 키를 등록하세요.",
    # EDGAR
    "edgar:fallback": "사전 수집 데이터에 없음 → SEC EDGAR API에서 직접 수집 중... (최초 1회, 수 분 소요)",
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
    "edgar:batch_done": "✓ EDGAR 배치 수집 완료 (성공 {success} / 실패 {failed} / 총 {total})",
    "edgar:incremental_start": "{ticker} EDGAR docs 증분 업데이트 ({newCount}건 신규 filing)",
    "edgar:incremental_done": "✓ {ticker} EDGAR docs 증분 완료 ({newRows}행 추가)",
    "edgar:no_new": "✓ {ticker} EDGAR docs 최신 상태",
    # freshness (L3: DART API 직접 조회)
    "freshness:checking": "{stockCode} 최신 공시 확인 중...",
    "freshness:fresh": "✓ {stockCode} 최신 상태",
    "freshness:stale": "⚠ {stockCode} 새 공시 {count}건 발견 ({latestReport})",
    "freshness:noKey": "DART API 키 없음 → 사전 수집 데이터 기준으로만 확인",
    "freshness:scanDone": "✓ {total}종목 스캔: {staleCount}종목에 새 공시",
    # listing
    "listing:download": "KRX KIND 상장법인 목록 다운로드 중...",
    "listing:done": "{count}개 종목 로드 완료",
    # scan
    "scan:signal_start": "서술형 시그널 스캔: {count}사",
    "scan:network_health": "그룹 건전성 분석 중...",
    # 전사 분석 데이터 필요 안내
    "hint:market_data_needed": (
        "⚠ {category} 데이터가 로컬에 없습니다. {fn}은 전체 시장 데이터가 필요합니다.\n"
        "  dartlab.downloadAll('{category}')  # pip install dartlab[hf] 필요"
    ),
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
        template="{stockCode} ({label}) → 사전 수집 데이터에 없습니다.",
        actions_with_key=[
            "DART API 키가 설정되어 있으므로 직접 수집이 가능합니다:\n    dartlab collect {stockCode}",
        ],
        actions_without_key=[
            "DART API 키를 설정하면 직접 수집할 수 있습니다:\n    dartlab setup dart-key\n    dartlab collect {stockCode}",
        ],
    ),
    "hint:missing_other": _StructuredMsg(
        template="{stockCode} ({label}) → 사전 수집 데이터에 없습니다.",
        actions=["해당 종목이 dartlab 데이터셋에 포함되어 있는지 확인하세요."],
        actions_with_key=[
            "DART API 키가 설정되어 있으므로 직접 수집이 가능합니다:\n    dartlab collect {stockCode}\n    dartlab collect --batch {stockCode}  (전 카테고리 병렬)",
        ],
        actions_without_key=[
            "DART API 키를 설정하면 직접 수집할 수 있습니다:\n    dartlab setup dart-key",
        ],
    ),
    "hint:newFilingsAvailable": _StructuredMsg(
        template="{stockCode} — 새 공시 {count}건 발견 ({latestReport})",
        actions_with_key=[
            "증분 수집: dartlab collect --incremental {stockCode}",
            "또는 Python: c.update()",
        ],
        actions_without_key=[
            "DART API 키를 설정하면 자동 수집 가능:\n    dartlab setup dart-key",
        ],
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
                from dartlab.providers.dart.openapi.client import hasDartApiKey

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

    # structured 메시지(hint/error) + collect/download 안내는 항상 출력
    _ALWAYS_SHOW = ("hint:", "error:", "collect:", "download:", "edgar:")
    if key in _STRUCTURED or any(key.startswith(p) for p in _ALWAYS_SHOW):
        print(f"{_PREFIX} {text}")
    else:
        # 그 외 simple 메시지는 verbose일 때만 출력
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
