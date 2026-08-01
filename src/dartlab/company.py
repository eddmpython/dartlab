"""루트 Company facade — canHandle() 체인 기반 자동 라우팅."""

from __future__ import annotations

from dartlab.core.protocols import CompanyProtocol

# ── provider 레지스트리 ──
_PROVIDERS: list[type] = []
_DISCOVERED = False


def _discover() -> None:
    """내장 provider를 priority 순으로 등록. 최초 1회만 실행."""
    global _DISCOVERED  # noqa: PLW0603
    if _DISCOVERED:
        return
    _DISCOVERED = True

    # 내장 provider lazy import
    from dartlab.providers.dart.company import Company as DartCompany
    from dartlab.providers.edgar.company import Company as EdgarCompany

    _PROVIDERS.clear()
    _PROVIDERS.extend([DartCompany, EdgarCompany])

    # entry_points 기반 외부 플러그인 (향후)
    from dartlab.plugins import discover as _pluginDiscover

    _pluginDiscover()

    # priority 순 정렬 (낮을수록 먼저)
    _PROVIDERS.sort(key=lambda cls: getattr(cls, "priority", lambda: 99)())


def Company(stockCode: str) -> CompanyProtocol:
    """**사람의 최상위 관문** — 종목 하나의 모든 엔진에 접근하는 파사드.

    dartlab 투톱 진입점:
        - `dartlab.ask(question)` — AI 대화 (일회성 질문 → 답)
        - `dartlab.Company(code)` — 사람 파사드 (종목 객체 → 모든 엔진)

    Capabilities:
        - 종목 파사드 하나로 엔진 전수 접근: analysis · credit · quant · macro ·
          industry · gather · panel. 엔진 이름만 기억하면 됨.
        - 종목코드 ("005930"), 회사명 ("삼성전자"), 영문 ticker ("AAPL") 모두 지원
        - canHandle() 체인: provider priority 순 자동 라우팅 (DART → EDGAR)
        - 새 국가 추가 시 이 파일 수정 불필요 — provider 패키지만 추가
        - 핵심 인터페이스: panel(topic) / index / trace(topic) / diff() / select()
        - 모든 데이터 접근은 ``c.panel(topic)`` 으로 통합 — finance topic
          (BS·IS·CF·CIS·SCE·ratios) 도 ``c.panel("BS")`` · ``c.panel("IS", freq="Y")``
          처럼 호출. 별도 namespace property 나 바로가기는 사용하지 않는다
          (``c.docs / c.finance / c.report / c.profile`` · ``c.BS / c.IS / c.CF /
          c.CIS / c.ratios / c.timeseries`` 는 Plan v10 에서 제거).
        - 메타: topics, index, filings(), market, currency

    Requires:
        DART: Company/loadData 단건 자동 다운로드 또는 collect 데이터.
        EDGAR: 인터넷 연결 (On-demand 수집).

    AIContext:
        AI 는 `dartlab.ask()` 로 접근 (Company 를 직접 생성하지 않음).
        사람은 Company 객체 하나로 노트북·스크립트에서 모든 엔진 호출.
        엔진은 사람의 분석엔진이자 AI 의 skill (docstring SSOT) — 한 파일 두 역할.

    Guide:
        - AI 역할: AI는 Company를 단일 종목 분석의 라우터로 보고 대상 식별, 사용 가능한 topic, 하위 엔진 선택을 정한다.
        - 데이터 기본기: Company 경로는 target, provider(DART/EDGAR), topic,
          source, period 를 먼저 고정하고, 이 원자료 ref 를 analysis · credit ·
          story 같은 응용 엔진으로 넘긴다.
        - Handoff: 최신 주가/뉴스/거시 원자료가 필요하면 gather 로 보강하고,
          peer/rank/universe 비교가 필요하면 scan 으로 넘어간다.
        - "삼성전자 재무제표" -> c = Company("005930"); c.panel("IS")
        - "사업 개요 보여줘" -> c.panel("businessOverview")
        - "어떤 데이터 있어?" -> c.index 또는 c.topics
        - "출처 추적" -> c.trace("revenue")
        - "기간 변화" -> c.diff()
        - "종합평가" -> c.analysis("financial", "종합평가")
        - "스토리 보고서" -> c.story()
        - "Apple 분석" -> Company("AAPL") (자동 EDGAR 라우팅)

    SeeAlso:
        - dartlab.ask: AI 대화 (투톱 다른 관문)
        - search: 종목 검색 (종목코드 모를 때)
        - scan: 전종목 횡단분석 (Company-독립)
        - macro: 시장 레벨 거시 (Company-독립)
        - industry: 섹터 밸류체인 (Company-독립)

    Args:
        stockCode: 종목코드, 회사명, 또는 영문 ticker.

    Returns:
        CompanyProtocol — DART 또는 EDGAR Company 인스턴스 (파사드).

    Example::

        import dartlab

        # 사람의 만능 관문 — 한 객체로 전 엔진
        c = dartlab.Company("005930")     # 삼성전자 (DART)
        c.story()                         # 분석 스토리 (보고서)
        c.analysis("financial", "수익성") # 재무 분석
        c.credit()                        # 신용
        c.quant()                         # 주가
        c.panel("businessOverview")        # 원본 사업 개요

        # 글로벌 (EDGAR 자동 라우팅)
        c = dartlab.Company("AAPL")
        c.analysis("financial", "valuation")

        # module-level 엔진도 `stockCode=` 로 호출 가능 (일관성 규약)
        dartlab.analysis.financial("수익성", stockCode="005930")
        dartlab.credit(stockCode="005930")
    """
    _discover()

    normalized = stockCode.strip()
    if not normalized:
        raise ValueError(
            "종목코드 또는 회사명을 입력해 주세요.\n"
            "  예: Company('삼성전자') 또는 Company('005930')\n"
            "  검색: dartlab.searchName('삼성')"
        )

    # canHandle 체인: priority 순으로 시도
    firstError: Exception | None = None
    matchedProvider = False
    for cls in _PROVIDERS:
        if hasattr(cls, "canHandle") and cls.canHandle(normalized):
            matchedProvider = True
            try:
                return cls(normalized)
            except (ValueError, FileNotFoundError) as e:
                firstError = firstError or e
                continue
            except OSError as e:
                firstError = firstError or e
                continue

    # 어떤 provider도 형식을 인식하지 못한 회사명만 fallback 탐색한다. 이미 canHandle=True로
    # 시도한 입력을 전 provider에 다시 보내면 동일 원격 조회가 두 번 실행되고, 숫자 입력은
    # DART와 EDGAR를 각각 중복 호출해 실패 latency가 배가된다.
    if not matchedProvider:
        for cls in _PROVIDERS:
            try:
                return cls(normalized)
            except (ValueError, FileNotFoundError) as e:
                firstError = firstError or e
                continue
            except OSError as e:
                firstError = firstError or e
                continue

    # 유사 종목 top-3 제안 (KRX listing 기반 fuzzy — 초성·편집거리·substring 지원)
    hint = ""
    try:
        from dartlab.gather.krx.listing import fuzzySearch

        suggestions = fuzzySearch(stockCode, maxResults=3)
        if suggestions.height > 0:
            rows = [f"    - {r['회사명']} ({r['종목코드']})" for r in suggestions.iter_rows(named=True)]
            hint = "\n  유사 종목:\n" + "\n".join(rows)
    except (ImportError, OSError, KeyError, ValueError):
        pass

    cause = f" (원인: {firstError})" if firstError else ""
    try:
        from dartlab.core.messaging import format as gfmt

        baseMsg = gfmt("error:no_data", stockCode=stockCode)
        raise ValueError(baseMsg + hint)
    except (ImportError, KeyError):
        raise ValueError(
            f"'{stockCode}'을(를) 찾을 수 없습니다{cause}.\n"
            f"  검색: dartlab.searchName('{stockCode}')\n"
            f"  전체 목록: dartlab.listing(){hint}"
        )


# ── facade resolveFromText (정공법 D — Facade re-export) ─────────────
# core/resolve.py 가 stockCode/ticker 추출까지 담당하고, Company 인스턴스 생성은
# 본 facade 가 책임. core 가 dartlab/Company 직접 import 하지 않게 layer 분리.


_RESOLVE_ERRORS = (AttributeError, KeyError, OSError, RuntimeError, TypeError, ValueError)


def resolveFromText(text: str) -> tuple[CompanyProtocol | None, str]:
    """자연어 텍스트에서 Company 인스턴스와 남은 질문을 분리한다.

    core/resolve.resolveStockCodeFromText 가 stockCode 추출까지 담당.
    본 함수는 stockCode → Company 인스턴스 생성을 책임 (facade 역할).

    Examples
    --------
        resolveFromText("삼성전자 재무건전성 분석해줘")
        # → (Company("삼성전자"), "재무건전성 분석해줘")

        resolveFromText("005930 영업이익률 추세는?")
        # → (Company("005930"), "영업이익률 추세는?")

        resolveFromText("오늘 날씨 어때")
        # → (None, "오늘 날씨 어때")
    """
    from dartlab.frame.resolve import resolveStockCodeFromText

    stockCode, remaining = resolveStockCodeFromText(text)
    if stockCode is None:
        return None, remaining
    try:
        return Company(stockCode), remaining
    except _RESOLVE_ERRORS:
        return None, text
