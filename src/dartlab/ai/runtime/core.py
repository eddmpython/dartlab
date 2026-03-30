"""AI 분석 통합 오케스트레이터 — CAPABILITIES-Driven 순수 스트리밍.

dartlab.ask(), server UI, CLI가 모두 이 코어를 소비한다.
동기 제너레이터로 AnalysisEvent를 생산하며, 소비자가 형식(SSE/텍스트/제너레이터)을 결정.

새 구조::

    질문 → CAPABILITIES 검색(ms) → 시스템 프롬프트 주입
         → LLM 스트리밍 → 코드블록 감지 → execute_code → 결과 해석 → 스트리밍 답변
"""

from __future__ import annotations

import re
import sqlite3
from typing import Any, Generator

from dartlab.ai.runtime.events import AnalysisEvent

# ── company=None 사전 종목 검색 ───────────────────────────

_COMPARE_SPLIT_RE = re.compile(r"(랑|와|과|이랑|하고|vs\.?|VS\.?|versus)", re.IGNORECASE)


def _detectCompanyNames(question: str) -> list[str]:
    """질문에서 종목명/종목코드 후보를 추출."""
    parts = _COMPARE_SPLIT_RE.split(question)
    candidates: list[str] = []
    for p in parts:
        p = p.strip()
        if not p or _COMPARE_SPLIT_RE.fullmatch(p):
            continue
        cleaned = re.sub(r"\s*(비교|분석|알려|설명|해줘|해주세요|해봐|좀).*$", "", p).strip()
        if cleaned and len(cleaned) >= 2:
            candidates.append(cleaned)
    return candidates[:4]


def _searchCompanyCodes(question: str) -> str:
    """질문에서 종목명을 추출하고 dartlab.search()로 종목코드를 사전 확인."""
    candidates = _detectCompanyNames(question)
    if not candidates:
        return ""

    results: list[str] = []
    try:
        import dartlab

        for name in candidates:
            try:
                df = dartlab.search(name)
                if df is not None and len(df) > 0:
                    row = df.row(0, named=True)
                    corpName = row.get("corp_name", row.get("회사명", name))
                    stockCode = row.get("stock_code", row.get("종목코드", ""))
                    if stockCode:
                        results.append(f"- {corpName}: 종목코드 **{stockCode}**")
            except (FileNotFoundError, OSError, RuntimeError, TypeError, ValueError):
                continue
    except ImportError:
        return ""

    if not results:
        return ""

    header = "## 사전 종목코드 확인 결과\n아래 종목코드가 확인되었습니다. 코드 작성 시 이 코드를 사용하세요:\n"
    return header + "\n".join(results)


# ── 데이터 신선도 추출 ────────────────────────────────────


def _extract_data_date(company: Any) -> str | None:
    """Company에서 최신 데이터 기준일을 추출한다."""
    try:
        filings = company.filings() if callable(getattr(company, "filings", None)) else None
        if filings is not None and hasattr(filings, "columns") and "date" in filings.columns:
            dates = filings["date"].drop_nulls()
            if len(dates) > 0:
                return str(dates.max())
    except (AttributeError, TypeError, KeyError):
        pass
    return None


# ── 에러 분류 ─────────────────────────────────────────────


def _classify_error(e: Exception) -> dict[str, str]:
    """예외 → {error: str, action: str} 매핑."""
    err_type = type(e).__name__
    err_str = str(e)
    err_low = err_str.lower()

    if isinstance(e, FileNotFoundError):
        return {"error": err_str, "action": "install"}
    if isinstance(e, PermissionError):
        return {"error": err_str, "action": "login"}

    # ChatGPT OAuth
    if err_type == "ChatGPTOAuthError":
        if any(kw in err_low for kw in ("token", "expire", "login")):
            return {"error": "ChatGPT 인증이 만료되었습니다. 다시 로그인해주세요.", "action": "relogin"}
        if any(kw in err_low for kw in ("rate", "limit")):
            return {"error": "ChatGPT 요청 한도에 도달했습니다. 잠시 후 다시 시도해주세요.", "action": "rate_limit"}
        return {"error": f"ChatGPT 연결 오류: {err_str}", "action": "relogin"}

    # OpenAI
    if err_type == "OpenAIError" or "api_key" in err_low:
        return {"error": "AI 설정이 필요합니다. API 키를 확인하거나 다른 provider를 선택해주세요.", "action": "config"}

    # Google Gemini 에러
    if (
        err_type in ("ServerError", "ClientError", "APIError")
        or "google" in err_type.lower()
        or "genai" in err_type.lower()
    ):
        if "503" in err_str or "unavailable" in err_low or "high demand" in err_low:
            return {"error": "Gemini 서버가 일시적으로 혼잡합니다. 잠시 후 다시 시도해주세요.", "action": "retry"}
        if "429" in err_str or "rate" in err_low or "quota" in err_low or "resource_exhausted" in err_low:
            return {"error": "Gemini 요청 한도에 도달했습니다. 잠시 후 다시 시도해주세요.", "action": "rate_limit"}
        if "401" in err_str or "403" in err_str or "unauthenticated" in err_low or "permission" in err_low:
            return {"error": "Gemini API 키가 유효하지 않습니다. 설정에서 확인해주세요.", "action": "config"}
        if "400" in err_str or "invalid" in err_low:
            return {"error": f"Gemini 요청 오류: {err_str}", "action": ""}
        return {"error": f"Gemini 연결 오류: {err_str}", "action": "retry"}

    # Ollama / 로컬 모델
    if "connection" in err_low and ("refused" in err_low or "11434" in err_low):
        return {"error": "Ollama가 실행 중이지 않습니다. ollama serve로 시작해주세요.", "action": "config"}

    # 일반 네트워크/서버 에러
    if isinstance(e, (ConnectionError, TimeoutError)):
        return {
            "error": "AI 서버에 연결할 수 없습니다. 네트워크를 확인하거나 잠시 후 다시 시도해주세요.",
            "action": "retry",
        }

    return {"error": err_str, "action": ""}


def _enrich_with_guide(result: dict[str, str]) -> dict[str, str]:
    """설정 관련 에러에 guide 메시지를 추가."""
    if result.get("action") in ("config", "install", "login", "relogin"):
        try:
            from dartlab.core.ai.guide import no_provider_message

            result["guide"] = no_provider_message()
        except ImportError:
            pass
    return result


# ── Config 해석 ──────────────────────────────────────────


def _resolveAnalysisConfig(
    provider: str | None,
    role: str | None,
    model: str | None,
    api_key: str | None,
    base_url: str | None,
    **kwargs: Any,
) -> Any:
    """Config 해석 — free provider chain, get_config, merge overrides."""
    from dartlab.ai import get_config

    if provider == "free":
        from dartlab.ai.providers.fallback import buildFreeChain

        free_chain = buildFreeChain()
        if free_chain:
            provider = free_chain[0]
        else:
            provider = None

    config_ = get_config(role=role)
    overrides = {
        k: v
        for k, v in {
            "provider": provider,
            "model": model,
            "api_key": api_key,
            "base_url": base_url,
            **kwargs,
        }.items()
        if v is not None
    }
    if overrides:
        config_ = config_.merge(overrides)

    return config_


# ── 코드블록 감지 + 실행 ─────────────────────────────────

_CODE_BLOCK_RE = re.compile(r"```python\s*\n(.*?)```", re.DOTALL)


def _extractCodeBlocks(text: str) -> list[str]:
    """텍스트에서 ```python 코드블록을 추출."""
    return _CODE_BLOCK_RE.findall(text)


def _executeCodeBlock(code: str, stockCode: str | None = None) -> str:
    """DartlabCodeExecutor로 코드를 실행하고 결과를 반환."""
    from dartlab.ai.tools.coding import DartlabCodeExecutor

    executor = DartlabCodeExecutor()
    return executor.execute(code, stockCode=stockCode, timeout=60)


def _streamWithCodeExecution(
    llm: Any,
    messages: list[dict],
    stockCode: str | None,
    *,
    maxRounds: int = 5,
) -> Generator[str, None, None]:
    """LLM 스트리밍 + 코드블록 자동 감지/실행 루프.

    LLM이 ```python 블록을 생성하면 자동 실행하고
    결과를 LLM에 피드백하여 해석을 이어간다.
    """
    for _round in range(maxRounds):
        buffer = ""
        for chunk in llm.stream(messages):
            buffer += chunk
            yield chunk

        # 코드블록 감지
        codeBlocks = _extractCodeBlocks(buffer)
        if not codeBlocks:
            return  # 코드 없음 → 스트리밍 완료

        # 마지막 코드블록 실행
        code = codeBlocks[-1]
        try:
            result = _executeCodeBlock(code, stockCode=stockCode)
        except (OSError, RuntimeError, TimeoutError, ValueError) as exc:
            result = f"실행 오류: {exc}"

        # 실행 결과 알림
        yield f"\n\n```\n[실행 결과]\n{result}\n```\n\n"

        # 결과를 대화에 추가하여 LLM이 해석하도록 재요청
        messages.append({"role": "assistant", "content": buffer})
        messages.append({
            "role": "user",
            "content": (
                "코드 실행 결과:\n\n"
                f"```\n{result}\n```\n\n"
                "이 결과를 바탕으로 해석하세요. "
                "오류가 있으면 수정 코드를 짜서 재실행하세요. "
                "결과가 잘렸으면 .head()/.filter()로 범위를 좁혀 재실행하세요."
            ),
        })

    # maxRounds 도달 — 마지막 스트리밍으로 종합
    yield from llm.stream(messages)


# ── 대화 상태 빌드 (history만 유지) ─────────────────────────


def _buildHistoryMessages(
    history: list | None,
    history_messages: list[dict] | None,
) -> list[dict] | None:
    """히스토리 messages 자동 빌드."""
    if history_messages is not None:
        return history_messages

    if history is None:
        return None

    from dartlab.ai.conversation.history import build_history_messages, compress_history
    from dartlab.ai.types import history_from_dicts

    light_history = history_from_dicts(history)
    compressed = compress_history(light_history)
    return build_history_messages(compressed)


# ── 시스템 프롬프트 ───────────────────────────────────────

_SYSTEM_PROMPT = """\
당신은 dartlab 재무분석 플랫폼의 AI입니다.
```python 코드블록을 작성하면 자동 실행되고 결과가 피드백됩니다.

## 사용법
- `import dartlab` 하나로 시작. 종목코드 하나면 모든 분석 가능.
- API를 모르면 `dartlab.capabilities(search='키워드')`로 검색.
- 결과는 `print()`로 출력. 실행 실패 시 에러를 읽고 수정 코드 재생성.

## 도구 우선순위 — 1차부터 쓰고, 깊이가 필요하면 2차로
**1차 (여기서 시작):**
- 기업 분석 → `c.review("섹션명")` — 구조화된 보고서 (수익구조, 안정성, 성장성, 종합진단 등)
- 기업간 비교 → `dartlab.scan("축", "종목코드")` — 동종업계 순위
- 외부 데이터 → `dartlab.gather("종류", "종목코드")` — 주가, 컨센서스, 수급

**2차 (깊이가 필요할 때):**
- `c.analysis("축")` — 14축 상세 (waterfall, 듀퐁, Sloan 등)
- `c.ratios`, `c.BS`, `c.IS`, `c.CF` — 원본 재무제표/비율
- `c.sections`, `c.show("토픽")` — 공시 원문

## 규칙
- 되묻지 말고 즉시 코드를 실행하라. 합리적 기본값 사용.
- 숫자 나열이 아니라 원인/추세/시사점을 해석하라.
- 한국어 질문에는 한국어로 답변.
- 코드로 확인되지 않은 수치를 인용하지 마라.
"""

_EDGAR_SUPPLEMENT = """
## EDGAR (미국 기업)
- US GAAP 적용. 통화 USD. report 네임스페이스 없음 (sections으로 접근).
- topic 형식: `10-K::item1Business`, `10-K::item7MdnA`, `10-Q::partIItem2Mdna`
"""


# ── 프롬프트 조립 ─────────────────────────────────────────


def _buildSystemPrompt(config_: Any, *, market: str = "KR") -> str:
    """시스템 프롬프트 조립 — CAPABILITIES + 사용설명서."""
    custom = getattr(config_, "system_prompt", None)
    if custom:
        return custom

    parts = [_SYSTEM_PROMPT]
    if market == "US":
        parts.append(_EDGAR_SUPPLEMENT)
    return "\n".join(parts)


# ── 통합 오케스트레이터 ──────────────────────────────────


def analyze(
    company: Any | None,
    question: str,
    *,
    # LLM 설정
    provider: str | None = None,
    role: str | None = None,
    model: str | None = None,
    api_key: str | None = None,
    base_url: str | None = None,
    include: list[str] | None = None,
    exclude: list[str] | None = None,
    # 멀티컴퍼니 비교 지원
    companies: list[Any] | None = None,
    # 모드 (하위호환 — 내부적으로 무시)
    use_tools: bool = True,
    max_turns: int = 5,
    max_tools: int | None = None,
    reflect: bool = False,
    report_mode: bool = False,
    # 하위호환 파라미터 (내부적으로 무시)
    snapshot: dict | None = None,
    auto_snapshot: bool = True,
    focus_context: str | None = None,
    diff_context: str | None = None,
    auto_diff: bool = True,
    history: list | None = None,
    history_messages: list[dict] | None = None,
    view_context: dict | None = None,
    dialogue_policy: str | None = None,
    conversation_meta: dict | None = None,
    question_types: tuple[str, ...] = (),
    # 기능 플래그
    validate: bool = True,
    detect_navigate: bool = True,
    emit_system_prompt: bool = True,
    # 단축 경로
    not_found_msg: str | None = None,
    # 추가 LLMConfig overrides
    **kwargs: Any,
) -> Generator[AnalysisEvent, None, None]:
    """AI 분석 이벤트 스트림 생산.

    3단계 구조:
        1. Config 해석 + Meta 이벤트
        2. CAPABILITIES 검색 → 시스템 프롬프트 조립
        3. LLM 스트리밍 + 코드블록 자동 실행 → chunk 이벤트

    로그: ``dartlab.askLog = True``로 설정하면 data/ask_logs/에 세션별 JSONL 저장.
    """
    # ── ask 로그 초기화 ──
    _logFile = None
    try:
        from dartlab import config as _cfg

        if getattr(_cfg, "askLog", False):
            import datetime
            import json
            from pathlib import Path

            logDir = Path(_cfg.dataDir) / "ask_logs"
            logDir.mkdir(parents=True, exist_ok=True)
            ts = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            _stock = getattr(company, "stockCode", getattr(company, "ticker", "unknown")) if company else "none"
            _logPath = logDir / f"{ts}_{_stock}.jsonl"
            _logFile = open(_logPath, "w", encoding="utf-8")  # noqa: SIM115
            # 첫 줄: 질문
            _logFile.write(json.dumps({"kind": "question", "data": {"question": question}}, ensure_ascii=False) + "\n")
    except (ImportError, OSError):
        _logFile = None

    def _emit(event: AnalysisEvent) -> AnalysisEvent:
        if _logFile is not None:
            import json

            try:
                _logFile.write(json.dumps({"kind": event.kind, "data": event.data}, ensure_ascii=False, default=str) + "\n")
                _logFile.flush()
            except (OSError, TypeError):
                pass
        return event

    try:
        # ── not_found 단축 경로 ──
        if not_found_msg:
            meta = conversation_meta or {}
            corp_name = getattr(company, "corpName", None) if company else None
            stock_id = getattr(company, "stockCode", getattr(company, "ticker", "")) if company else None
            if corp_name:
                meta.setdefault("company", corp_name)
            if stock_id:
                meta.setdefault("stockCode", stock_id)
            yield _emit(AnalysisEvent("meta", meta))
            yield _emit(AnalysisEvent("chunk", {"text": not_found_msg}))
            yield _emit(AnalysisEvent("done", {}))
            return

        full_response_parts: list[str] = []
        done_payload: dict[str, Any] = {}

        try:
            for ev in _analyze_inner(
                company,
                question,
                provider=provider,
                role=role,
                model=model,
                api_key=api_key,
                base_url=base_url,
                history=history,
                history_messages=history_messages,
                conversation_meta=conversation_meta,
                emit_system_prompt=emit_system_prompt,
                _full_response_parts=full_response_parts,
                **kwargs,
            ):
                yield _emit(ev)
        except Exception as e:
            yield _emit(AnalysisEvent("error", _enrich_with_guide(_classify_error(e))))

        # ── 후처리: plugin hints ──
        if question:
            from dartlab.ai.runtime.plugin_hints import (
                detect_plugin_hints,
                format_plugin_hints,
            )
            from dartlab.core.plugins import get_loaded_plugins

            loaded_names = [p.name for p in get_loaded_plugins()]
            hints = detect_plugin_hints(question, loaded_names)
            if hints:
                done_payload["pluginHints"] = hints
                hint_text = format_plugin_hints(hints)
                if hint_text:
                    done_payload["pluginHintsText"] = hint_text

        # ── Done 이벤트 ──
        yield _emit(AnalysisEvent("done", done_payload))
    finally:
        if _logFile is not None:
            _logFile.close()


def _analyze_inner(
    company: Any | None,
    question: str,
    *,
    provider: str | None,
    role: str | None,
    model: str | None,
    api_key: str | None,
    base_url: str | None,
    history: list | None,
    history_messages: list[dict] | None,
    conversation_meta: dict | None,
    emit_system_prompt: bool,
    _full_response_parts: list[str],
    **kwargs: Any,
) -> Generator[AnalysisEvent, None, None]:
    """analyze() 본체 — 3단계 순수 스트리밍."""

    # ── 1. Config 해석 + Meta 이벤트 ──
    config_ = _resolveAnalysisConfig(provider, role, model, api_key, base_url, **kwargs)

    corp_name = getattr(company, "corpName", "Unknown") if company else None
    stock_id = getattr(company, "stockCode", getattr(company, "ticker", "")) if company else None

    meta = conversation_meta or {}
    if corp_name:
        meta.setdefault("company", corp_name)
    if stock_id:
        meta.setdefault("stockCode", stock_id)
    if company is not None:
        _dataDate = _extract_data_date(company)
        if _dataDate:
            meta.setdefault("dataDate", _dataDate)
    yield AnalysisEvent("meta", meta)

    # ── 2. 시스템 프롬프트 조립 ──
    company_market = getattr(company, "market", "KR") if company else "KR"
    system_prompt = _buildSystemPrompt(config_, market=company_market)

    # company=None이면 종목명 사전 검색
    prefetchText = ""
    if company is None:
        prefetchText = _searchCompanyCodes(question)

    if emit_system_prompt:
        yield AnalysisEvent("system_prompt", {"text": system_prompt})

    # ── Messages 조립 ──
    messages: list[dict] = [{"role": "system", "content": system_prompt}]

    # 히스토리 주입
    effective_history = _buildHistoryMessages(history, history_messages)
    if effective_history:
        messages.extend(effective_history)

    # 메모리 (세션 간) — 질문 이력만 참조, 수치/요약은 제외 (코드 실행 유도)
    memoryHints = ""
    if stock_id:
        try:
            from dartlab.ai.memory.store import getMemory

            records = getMemory().recallForStock(stock_id, limit=3)
            if records:
                import datetime

                hints = []
                for r in records:
                    dt = datetime.datetime.fromtimestamp(r.timestamp).strftime("%Y-%m-%d")
                    hints.append(f"- {dt}: {r.question} ({r.questionType})")
                memoryHints = "## 이전 질문 이력\n" + "\n".join(hints)
        except (ImportError, OSError, sqlite3.Error):
            pass

    # user 메시지 조립
    userParts: list[str] = []
    if corp_name and stock_id:
        userParts.append(f"분석 대상: {corp_name} (종목코드: {stock_id})")
    if prefetchText:
        userParts.append(prefetchText)
    if memoryHints:
        userParts.append(memoryHints)
    userParts.append(f"질문: {question}")
    userContent = "\n\n---\n\n".join(userParts)
    messages.append({"role": "user", "content": userContent})

    # ── 3. LLM 스트리밍 + 코드블록 자동 실행 ──
    from dartlab.ai.providers import create_provider

    llm = create_provider(config_)

    for chunk in _streamWithCodeExecution(llm, messages, stockCode=stock_id):
        _full_response_parts.append(chunk)
        yield AnalysisEvent("chunk", {"text": chunk})

    # ── 분석 메모리 저장 ──
    if stock_id and _full_response_parts:
        try:
            from dartlab.ai.memory.store import getMemory
            from dartlab.ai.memory.summarizer import extractGrade, summarizeResponse

            _fullText = "".join(_full_response_parts)
            _mem = getMemory()
            _mem.saveAnalysis(
                stockCode=stock_id,
                question=question[:200],
                questionType="",
                resultSummary=summarizeResponse(_fullText),
                grade=extractGrade(_fullText),
            )
        except (ImportError, OSError, sqlite3.Error):
            pass
