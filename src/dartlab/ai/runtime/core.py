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
from dartlab.ai.runtime.post_processing import (
    _detect_navigate_action,
    _run_validation,
    autoInjectArtifacts,
    buildCorrectionPrompt,
)

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
            "content": f"코드 실행 결과입니다. 이 결과를 분석하고 해석해주세요:\n\n```\n{result}\n```",
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


# ── 모듈/섹터 감지 ────────────────────────────────────────


def _detectAvailableModules(company: Any) -> list[str]:
    """Company에서 사용 가능한 데이터 모듈 감지."""
    modules: list[str] = []
    for name in ("BS", "IS", "CF", "CIS", "SCE"):
        df = getattr(company, name, None)
        if df is not None and hasattr(df, "__len__") and len(df) > 0:
            modules.append(name)
    if getattr(company, "ratios", None) is not None:
        modules.append("ratios")
    if getattr(company, "sections", None) is not None:
        modules.append("sections")
    if getattr(company, "insights", None) is not None:
        modules.append("insights")
    return modules


def _detectSector(company: Any) -> str | None:
    """Company의 섹터 분류."""
    stockCode = getattr(company, "stockCode", getattr(company, "ticker", None))
    if not stockCode:
        return None
    try:
        from dartlab.core.sector import classify

        info = classify(stockCode)
        if info and hasattr(info, "sectorName"):
            return info.sectorName
        if isinstance(info, dict):
            return info.get("sectorName")
    except (ImportError, AttributeError, KeyError, TypeError, ValueError):
        pass
    return None


# ── 분석 워크플로우 가이드 ────────────────────────────────

_ANALYSIS_WORKFLOW_GUIDE = """\
## dartlab — 기업 분석 플랫폼

`import dartlab` 하나로 모든 기능 접근. ```python 코드블록은 자동 실행되고 결과가 피드백됩니다.

### 분석 도구 — 무엇이 나오는지 알고 써라

**c.insights** (가장 먼저 확인 — 전체 그림을 잡는다)
→ 10개 영역 등급(A~F): performance, profitability, health, cashflow, governance, risk, opportunity 등
→ anomalies: 이상치 11개 룰 (영업이익 증가인데 CF 감소, 매출채권/재고 급증, 감사의견 변화 등)
→ distress: 5축 부실 스코어카드 (Ohlson O-Score + Altman Z/Z'' + Beneish M + Merton PD + 감사위험)
→ distress.level: safe/watch/warning/danger/critical, creditGrade: AAA~D
→ distress.cashRunwayMonths, riskFactors[]
→ profile: premium/growth/stable/caution/distress/mixed

**dartlab.analysis(c)** (14축 재무 분석 — 깊이를 더한다)
→ Part 1 사업구조: 수익구조(segmentComposition, concentration, revenueQuality), 자금조달, 자산구조, 현금흐름
→ Part 2 핵심비율: 수익성, 성장성, 안정성(leverageTrend, distressScore, debtMaturity), 효율성, 종합평가
→ Part 3 심화: 이익품질(Beneish M-Score, Sloan Accrual, OCF/NI), 비용구조, 자본배분, 투자효율, 재무정합성
→ 각 축마다 flags(적색신호/기회신호)가 포함됨

**dartlab.valuation(c)** (적정가치 — 투자 판단의 핵심)
→ dcf: FCF 시계열 + WACC + 터미널밸류 → 주당가치 + marginOfSafety
→ ddm: 배당할인모형 (Gordon Growth / Two-Stage)
→ relative: 피어 멀티플(PER/PBR/EV-EBITDA) 대비 프리미엄/디스카운트 + 합의가치
→ fairValueRange: (low, high)

**dartlab.forecast(c)** (미래 추정 — 시나리오별 확률 가중)
→ predicted/upper/lower: 3~5년 매출 예측 + 신뢰구간
→ signals: insight 등급 반영 확률 조정 (performance=F → bull 하향), 섹터 사이클리컬리티, 공시 톤 변화
→ scenario별 확률 가중 (bull/base/bear)

**dartlab.review(c)** (14섹션 종합 보고서 — 한번에 전체를 본다)
→ 각 섹션: TextBlock(서술) + MetricBlock(KPI) + TableBlock(다년비교) + FlagBlock(적색/기회 신호)
→ DuPont 5-factor ROE 분해, Beneish M-Score, 운전자본 사이클, 부채만기구조, 피어 벤치마크 포함

### 분석 워크플로우 — 빠른 것부터 쓰고, 필요하면 깊이를 더한다

**기업 종합 분석** (c.ratios만 보지 마라):
1단계 (1-3초): `c.insights` → 등급/이상치/부실점수. 여기서 전체 그림이 잡힌다.
2단계 (5초): 약한 축을 골라서 `dartlab.analysis("해당축", c)` → 단일 축 상세
3단계 (필요시): `dartlab.valuation(c)` → 적정가치, `dartlab.forecast(c)` → 미래 시나리오
4단계 (필요시): `c.review("섹션명")` → 특정 섹션만 구조화 보고서

주의: `c.review()` (파라미터 없음)는 14섹션 전부 계산하므로 느리다 (30초+).
      특정 섹션이 필요하면 `c.review("안정성")` 같이 섹션명을 지정하라.
      `dartlab.analysis("축", c)`가 `review()`보다 빠르다 — 축별로 호출하라.

**기업 비교 분석**:
1. `dartlab.scan('peer', stockCode)` → 동종 기업 자동 선별
2. `dartlab.scan('screen', metric='roe', n=20)` → 조건부 스크리닝
3. `dartlab.governance()` / `dartlab.capital()` / `dartlab.debt()` → 시장 횡단

**사업/전략 분석**:
1. `c.show(topic)` → 공시 원문 (사업모델, 경쟁우위, 리스크)
2. `c.sections` → 사용 가능한 topic 지도
3. `dartlab.analysis(c, axes=['strategy','accounting'])` → 회계정책, 사업전략

**리스크/부실 심화**:
1. `c.insights.distress` → 5축 스코어카드 개별 확인 (Beneish 높은데 Ohlson 낮으면 다른 이야기)
2. `c.insights.anomalies` → 이상치 패턴 (OP 증가인데 CF 감소 = 이익품질 적색신호)
3. `dartlab.audit(c)` → 감사인 변경, 계속기업 의심, 핵심감사사항

### 기업 데이터
- `c = dartlab.Company('종목코드')` — 기업 데이터의 뿌리
- `c.ratios` 비율 (property), `c.BS`/`c.IS`/`c.CF` 재무제표 (property)
- `c.show(topic)` 공시 원문, `c.sections` 토픽 지도

### API 탐색
- `dartlab.capabilities(search='키워드')` → 어떤 API가 있는지 검색
- `dartlab.capabilities()` → 전체 목록

### 규칙
- **즉시 실행 원칙**: 데이터 요청이 오면 범위/조건을 되묻지 말고 즉시 코드를 짜서 실행하라. "어떤 기간?" "어떤 지표?" 같은 질문 금지. 합리적 기본값으로 먼저 보여주고, 사용자가 조정하면 그때 바꿔라.
- **모르면 capabilities 검색**: API가 뭔지 모르겠으면 `dartlab.capabilities(search='키워드')`로 찾아서 실행하라. 사용자에게 "이런 기능이 있습니다" 안내만 하고 끝내지 마라.
- 결과는 `print()`로 출력. 실행 실패 시 에러를 읽고 수정 코드 재생성.
- **c.ratios만 보고 끝내지 마라.** insights → analysis → valuation 순서로 깊이를 더해라.
- **이상치(anomalies)를 먼저 확인하라.** OP 증가 + CF 감소, 매출채권 급증, 감사의견 변화는 분석 방향을 바꾸는 신호다.
- 비율만 나열하지 말고, 추세/원인/시사점/비교 관점으로 해석하라.
- 한 축만 보지 말고 복수 축을 교차 검증하라 (건전성 + 수익성 + 이익품질 + 캐시플로우).
"""


# ── 프롬프트 조립 ─────────────────────────────────────────


def _buildSystemPrompt(
    config_: Any,
    company: Any | None,
    question: str,
    *,
    report_mode: bool,
    market: str,
) -> str:
    """시스템 프롬프트 조립 — 동적 모듈/섹터/질문유형 감지 + 분석 워크플로우."""
    from dartlab.ai.conversation.prompts import _classify_question, build_system_prompt_parts

    q_type = _classify_question(question)
    included_modules = _detectAvailableModules(company) if company else []
    sector = _detectSector(company) if company else None

    static_part, dynamic_part = build_system_prompt_parts(
        config_.system_prompt,
        included_modules=included_modules,
        sector=sector,
        question_type=q_type,
        compact=True,
        report_mode=report_mode,
        market=market,
        allow_tools=True,
        hasCompany=(company is not None),
    )

    parts = [static_part, _ANALYSIS_WORKFLOW_GUIDE]
    if dynamic_part:
        parts.append(dynamic_part)

    return "\n\n".join(parts)


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
                report_mode=report_mode,
                history=history,
                history_messages=history_messages,
                conversation_meta=conversation_meta,
                validate=validate,
                emit_system_prompt=emit_system_prompt,
                _full_response_parts=full_response_parts,
                _done_payload=done_payload,
                **kwargs,
            ):
                yield _emit(ev)
        except Exception as e:
            yield _emit(AnalysisEvent("error", _enrich_with_guide(_classify_error(e))))

        # ── 후처리: navigate ui_action ──
        if detect_navigate and company is not None:
            nav_event = _detect_navigate_action(company, question)
            if nav_event:
                yield _emit(nav_event)

        # ── 후처리: validation ──
        if validate and company is not None and full_response_parts:
            val_event = _run_validation(company, full_response_parts)
            if val_event:
                yield _emit(val_event)

        # ── 후처리: auto-artifact injection ──
        if company is not None:
            _q_type = done_payload.get("_q_type")
            _tc_names = done_payload.pop("_tool_call_names", [])
            done_payload.pop("_q_type", None)
            for art_event in autoInjectArtifacts(company, _q_type, _tc_names):
                yield _emit(art_event)

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
    report_mode: bool,
    history: list | None,
    history_messages: list[dict] | None,
    conversation_meta: dict | None,
    validate: bool,
    emit_system_prompt: bool,
    _full_response_parts: list[str],
    _done_payload: dict[str, Any],
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

    # ── 2. 시스템 프롬프트 조립 (CAPABILITIES 검색 기반) ──
    company_market = getattr(company, "market", "KR") if company else "KR"
    system_prompt = _buildSystemPrompt(
        config_,
        company,
        question,
        report_mode=report_mode,
        market=company_market,
    )

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

    from dartlab.ai.conversation.prompts import _classify_question

    q_type = _classify_question(question)
    _done_payload["_q_type"] = q_type
    _done_payload["_tool_call_names"] = []

    for chunk in _streamWithCodeExecution(llm, messages, stockCode=stock_id):
        _full_response_parts.append(chunk)
        yield AnalysisEvent("chunk", {"text": chunk})

    # ── Self-Verification (correction) ──
    if validate and company is not None and _full_response_parts:
        correction_prompt = buildCorrectionPrompt(company, _full_response_parts)
        if correction_prompt:
            _done_payload["selfVerification"] = True
            yield AnalysisEvent("correction", {"message": correction_prompt})

            correction_messages = [
                *messages,
                {"role": "assistant", "content": "".join(_full_response_parts)},
                {"role": "user", "content": correction_prompt},
            ]
            _full_response_parts.clear()
            yield AnalysisEvent("chunk", {"text": "\n\n---\n*[수치 검증 후 수정된 답변]*\n\n"})
            _full_response_parts.append("\n\n---\n*[수치 검증 후 수정된 답변]*\n\n")
            for chunk in llm.stream(correction_messages):
                _full_response_parts.append(chunk)
                yield AnalysisEvent("chunk", {"text": chunk})

    # ── Response meta 추출 ──
    if company and _full_response_parts and "responseMeta" not in _done_payload:
        from dartlab.ai.conversation.prompts import extract_response_meta

        full_text = "".join(_full_response_parts)
        response_meta = extract_response_meta(full_text)
        if response_meta.get("grade") or response_meta.get("has_conclusion"):
            _done_payload["responseMeta"] = response_meta

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
                questionType=q_type or "",
                resultSummary=summarizeResponse(_fullText),
                grade=extractGrade(_fullText),
            )
        except (ImportError, OSError, sqlite3.Error):
            pass
