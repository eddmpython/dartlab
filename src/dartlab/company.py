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
    from dartlab.core.plugins import discover as _pluginDiscover

    _pluginDiscover()

    # priority 순 정렬 (낮을수록 먼저)
    _PROVIDERS.sort(key=lambda cls: getattr(cls, "priority", lambda: 99)())


def Company(codeOrName: str) -> CompanyProtocol:
    """종목코드/회사명/ticker → 적절한 Company 인스턴스 생성.

    Capabilities:
        - 종목코드 ("005930"), 회사명 ("삼성전자"), 영문 ticker ("AAPL") 모두 지원
        - canHandle() 체인: provider priority 순 자동 라우팅 (DART → EDGAR)
        - 새 국가 추가 시 이 파일 수정 불필요 — provider 패키지만 추가
        - 핵심 인터페이스: show(topic) / index / trace(topic) / diff()
        - namespace: docs (원문) / finance (숫자) / report (정형공시) / profile (merge)
        - 바로가기: BS/IS/CF/CIS, ratios, ratioSeries, timeseries
        - 메타: sections, topics, filings(), insights, market, currency

    Requires:
        DART: 사전 다운로드 데이터 (dartlab.downloadAll() 또는 자동 다운로드).
        EDGAR: 인터넷 연결 (On-demand 수집).

    AIContext:
        개별 종목 분석의 시작점. explore/finance/analysis 수퍼툴이 이 객체를 소비.
        "삼성전자 분석해줘" → Company("005930") 생성 → briefing → LLM 해석.

    Guide:
        - "삼성전자 재무제표" -> c = Company("005930"); c.IS
        - "사업 개요 보여줘" -> c.show("businessOverview")
        - "어떤 데이터 있어?" -> c.index 또는 c.topics
        - "출처 추적" -> c.trace("revenue")
        - "기간 변화" -> c.diff()
        - "인사이트 등급" -> c.insights
        - "리뷰 보고서" -> c.review()
        - "Apple 분석" -> Company("AAPL") (자동 EDGAR 라우팅)

    SeeAlso:
        - search: 종목 검색 (종목코드 모를 때)
        - scan: 전종목 횡단분석 (기업 비교)
        - analysis: 14축 전략분석
        - gather: 주가/수급/거시 데이터

    Args:
        codeOrName: 종목코드, 회사명, 또는 영문 ticker.

    Returns:
        CompanyProtocol — DART 또는 EDGAR Company 인스턴스.

    Example::

        import dartlab
        c = dartlab.Company("005930")     # 삼성전자 (DART)
        c = dartlab.Company("삼성전자")    # 회사명으로도 가능
        c = dartlab.Company("AAPL")       # Apple (EDGAR)

        c.IS                              # 손익계산서
        c.show("businessOverview")        # 사업 개요
        c.insights                        # 7영역 인사이트
        c.review()                        # 분석 보고서
    """
    _discover()

    normalized = codeOrName.strip()
    if not normalized:
        raise ValueError(
            "종목코드 또는 회사명을 입력해 주세요.\n"
            "  예: Company('삼성전자') 또는 Company('005930')\n"
            "  검색: dartlab.search('삼성')"
        )

    # canHandle 체인: priority 순으로 시도
    firstError: Exception | None = None
    for cls in _PROVIDERS:
        if hasattr(cls, "canHandle") and cls.canHandle(normalized):
            try:
                return cls(normalized)
            except (ValueError, FileNotFoundError) as e:
                firstError = firstError or e
                continue
            except OSError as e:
                firstError = firstError or e
                continue

    # fallback: DART (한글도 아니고 ticker도 아닌 회사명 검색 시도)
    for cls in _PROVIDERS:
        try:
            return cls(normalized)
        except (ValueError, FileNotFoundError) as e:
            firstError = firstError or e
            continue
        except OSError as e:
            firstError = firstError or e
            continue

    cause = f" (원인: {firstError})" if firstError else ""
    raise ValueError(
        f"'{codeOrName}'을(를) 찾을 수 없습니다{cause}.\n"
        f"  검색: dartlab.search('{codeOrName}')\n"
        "  전체 목록: dartlab.listing()"
    )
