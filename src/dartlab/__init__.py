"""DART 공시 데이터 활용 라이브러리."""

import sys
from importlib.metadata import PackageNotFoundError
from importlib.metadata import version as _pkg_version

from dartlab import ai as llm
from dartlab import config, core
from dartlab.company import Company
from dartlab.core.env import loadEnv as _loadEnv
from dartlab.core.select import ChartResult, SelectResult
from dartlab.gather.fred import Fred
from dartlab.gather.listing import codeToName, fuzzySearch, getKindList, nameToCode, searchName
from dartlab.providers.dart.company import Company as _DartEngineCompany
from dartlab.providers.dart.openapi.dart import OpenDart
from dartlab.providers.edgar.openapi.edgar import OpenEdgar
from dartlab.review import Review

# .env 자동 로드 — API 키 등 환경변수
_loadEnv()

try:
    __version__ = _pkg_version("dartlab")
except PackageNotFoundError:
    __version__ = "0.0.0"


def search(keyword: str):
    """종목 검색 (KR + US 통합).

    Example::

        import dartlab
        dartlab.search("삼성전자")
        dartlab.search("AAPL")
    """
    if any("\uac00" <= ch <= "\ud7a3" for ch in keyword):
        return _DartEngineCompany.search(keyword)
    if keyword.isascii() and keyword.isalpha():
        try:
            from dartlab.providers.edgar.company import Company as _US

            return _US.search(keyword)
        except (ImportError, AttributeError, NotImplementedError):
            pass
    return _DartEngineCompany.search(keyword)


def listing(market: str | None = None):
    """전체 상장법인 목록.

    Args:
        market: "KR" 또는 "US". None이면 KR 기본.

    Example::

        import dartlab
        dartlab.listing()          # KR 전체
        dartlab.listing("US")      # US 전체 (향후)
    """
    if market and market.upper() == "US":
        try:
            from dartlab.providers.edgar.company import Company as _US

            return _US.listing()
        except (ImportError, AttributeError, NotImplementedError):
            raise NotImplementedError("US listing은 아직 지원되지 않습니다")
    return _DartEngineCompany.listing()


def collect(
    *codes: str,
    categories: list[str] | None = None,
    incremental: bool = True,
) -> dict[str, dict[str, int]]:
    """지정 종목 DART 데이터 수집 (OpenAPI). 멀티키 시 병렬.

    Example::

        import dartlab
        dartlab.collect("005930")                              # 삼성전자 전체
        dartlab.collect("005930", "000660", categories=["finance"])  # 재무만
    """
    from dartlab.providers.dart.openapi.batch import batchCollect

    return batchCollect(list(codes), categories=categories, incremental=incremental)


def collectAll(
    *,
    categories: list[str] | None = None,
    mode: str = "new",
    maxWorkers: int | None = None,
    incremental: bool = True,
) -> dict[str, dict[str, int]]:
    """전체 상장종목 DART 데이터 수집. DART_API_KEY(S) 필요. 멀티키 시 병렬.

    Example::

        import dartlab
        dartlab.collectAll()                          # 전체 미수집 종목
        dartlab.collectAll(categories=["finance"])    # 재무만
        dartlab.collectAll(mode="all")                # 기수집 포함 전체
    """
    from dartlab.providers.dart.openapi.batch import batchCollectAll

    return batchCollectAll(
        categories=categories,
        mode=mode,
        maxWorkers=maxWorkers,
        incremental=incremental,
    )


def downloadAll(category: str = "finance", *, forceUpdate: bool = False) -> None:
    """HuggingFace에서 전체 시장 데이터를 다운로드.

    scanAccount, screen, digest 등 전사(全社) 분석 기능은 로컬에 전체 데이터가 있어야 동작합니다.
    이 함수로 카테고리별 전체 데이터를 사전 다운로드하세요.

    Args:
        category: "finance" (재무 ~600MB), "docs" (공시 ~8GB), "report" (보고서 ~320MB).
        forceUpdate: True면 이미 있는 파일도 최신으로 갱신.

    Examples::

        import dartlab
        dartlab.downloadAll("finance")   # 재무 전체 — scanAccount/scanRatio 등에 필요
        dartlab.downloadAll("report")    # 보고서 전체 — governance/workforce/capital/debt에 필요
        dartlab.downloadAll("docs")      # 공시 전체 — digest에 필요 (대용량 ~8GB)
    """
    from dartlab.core.dataLoader import downloadAll as _downloadAll

    _downloadAll(category, forceUpdate=forceUpdate)


def checkFreshness(stockCode: str, *, forceCheck: bool = False):
    """종목의 로컬 데이터가 최신인지 DART API로 확인.

    Example::

        import dartlab
        result = dartlab.checkFreshness("005930")
        result.isFresh       # True/False
        result.missingCount  # 누락 공시 수
    """
    from dartlab.providers.dart.openapi.freshness import (
        checkFreshness as _check,
    )

    return _check(stockCode, forceCheck=forceCheck)


def network():
    """한국 상장사 전체 관계 지도.

    Example::

        import dartlab
        dartlab.network().show()  # 브라우저에서 전체 네트워크
    """
    from dartlab.scan.network import build_graph, export_full
    from dartlab.tools.network import render_network

    data = build_graph()
    full = export_full(data)
    return render_network(
        full["nodes"],
        full["edges"],
        "한국 상장사 관계 네트워크",
    )


def governance():
    """한국 상장사 전체 지배구조 스캔.

    Example::

        import dartlab
        df = dartlab.governance()
    """
    from dartlab.scan.governance import scan_governance

    result = scan_governance()
    if result is not None and hasattr(result, "is_empty") and result.is_empty():
        print("\n  거버넌스 스캔 결과가 없습니다.")
        print("  전체 시장 데이터가 필요합니다: dartlab.downloadAll('report')\n")
    return result


def workforce():
    """한국 상장사 전체 인력/급여 스캔.

    Example::

        import dartlab
        df = dartlab.workforce()
    """
    from dartlab.scan.workforce import scan_workforce

    result = scan_workforce()
    if result is not None and hasattr(result, "is_empty") and result.is_empty():
        print("\n  인력 스캔 결과가 없습니다.")
        print("  전체 시장 데이터가 필요합니다: dartlab.downloadAll('report')\n")
    return result


def capital():
    """한국 상장사 전체 주주환원 스캔.

    Example::

        import dartlab
        df = dartlab.capital()
    """
    from dartlab.scan.capital import scan_capital

    result = scan_capital()
    if result is not None and hasattr(result, "is_empty") and result.is_empty():
        print("\n  주주환원 스캔 결과가 없습니다.")
        print("  전체 시장 데이터가 필요합니다: dartlab.downloadAll('report')\n")
    return result


def debt():
    """한국 상장사 전체 부채 구조 스캔.

    Example::

        import dartlab
        df = dartlab.debt()
    """
    from dartlab.scan.debt import scan_debt

    result = scan_debt()
    if result is not None and hasattr(result, "is_empty") and result.is_empty():
        print("\n  부채 스캔 결과가 없습니다.")
        print("  전체 시장 데이터가 필요합니다: dartlab.downloadAll('report')\n")
    return result


def news(query: str, *, market: str = "KR", days: int = 30):
    """기업 뉴스 수집.

    Args:
        query: 기업명 또는 티커.
        market: "KR" 또는 "US".
        days: 최근 N일.

    Example::

        import dartlab
        dartlab.news("삼성전자")
        dartlab.news("AAPL", market="US")
    """
    from dartlab.gather import getDefaultGather

    return getDefaultGather().news(query, market=market, days=days)


def price(
    stockCode: str, *, market: str = "KR", start: str | None = None, end: str | None = None, snapshot: bool = False
):
    """주가 시계열 (기본 1년 OHLCV) 또는 스냅샷.

    Example::

        import dartlab
        dartlab.price("005930")                              # 1년 OHLCV 시계열
        dartlab.price("005930", start="2020-01-01")          # 기간 지정
        dartlab.price("005930", snapshot=True)               # 현재가 스냅샷
    """
    from dartlab.gather import getDefaultGather

    return getDefaultGather().price(stockCode, market=market, start=start, end=end, snapshot=snapshot)


def consensus(stockCode: str, *, market: str = "KR"):
    """컨센서스 — 목표가, 투자의견.

    Example::

        import dartlab
        dartlab.consensus("005930")
        dartlab.consensus("AAPL", market="US")
    """
    from dartlab.gather import getDefaultGather

    return getDefaultGather().consensus(stockCode, market=market)


def flow(stockCode: str, *, market: str = "KR"):
    """수급 시계열 — 외국인/기관 매매 동향 (KR 전용).

    Example::

        import dartlab
        dartlab.flow("005930")
        # [{"date": "20260325", "foreignNet": -6165053, "institutionNet": 2908773, ...}, ...]
    """
    from dartlab.gather import getDefaultGather

    return getDefaultGather().flow(stockCode, market=market)


def macro(market: str = "KR", indicator: str | None = None, *, start: str | None = None, end: str | None = None):
    """거시 지표 시계열 — ECOS(KR) / FRED(US).

    인자 없으면 카탈로그 전체 지표를 wide DataFrame으로 반환.

    Example::

        import dartlab
        dartlab.macro()                    # KR 전체 지표 wide DF (22개)
        dartlab.macro("US")                # US 전체 지표 wide DF (50개)
        dartlab.macro("CPI")               # CPI (자동 KR 감지)
        dartlab.macro("FEDFUNDS")          # 연방기금금리 (자동 US 감지)
        dartlab.macro("KR", "CPI")         # 명시적 KR + CPI
        dartlab.macro("US", "SP500")       # 명시적 US + S&P500
    """
    from dartlab.gather import getDefaultGather

    return getDefaultGather().macro(market, indicator, start=start, end=end)


def setup(provider: str | None = None):
    """AI provider 설정 안내 + 인터랙티브 설정.

    Args:
        provider: 특정 provider 설정. None이면 전체 현황.

    Example::

        import dartlab
        dartlab.setup()              # 전체 provider 현황
        dartlab.setup("chatgpt")     # ChatGPT OAuth 브라우저 로그인
        dartlab.setup("openai")      # OpenAI API 키 설정
        dartlab.setup("ollama")      # Ollama 설치 안내
    """
    from dartlab.core.ai.guide import (
        provider_guide,
        providers_status,
        resolve_alias,
    )

    if provider is None:
        print(providers_status())
        return

    provider = resolve_alias(provider)

    if provider == "oauth-codex":
        _setup_oauth_interactive()
    elif provider == "openai":
        _setup_openai_interactive()
    else:
        print(provider_guide(provider))


def _setup_oauth_interactive():
    """노트북/CLI에서 ChatGPT OAuth 브라우저 로그인."""
    try:
        from dartlab.ai.providers.support.oauth_token import is_authenticated

        if is_authenticated():
            print("\n  ✓ ChatGPT OAuth 이미 인증되어 있습니다.")
            print('  재인증: dartlab.setup("chatgpt")  # 재실행하면 갱신\n')
            return
    except ImportError:
        pass

    try:
        from dartlab.cli.commands.setup import _do_oauth_login

        _do_oauth_login()
    except ImportError:
        print("\n  ChatGPT OAuth 브라우저 로그인:")
        print("  CLI에서 실행: dartlab setup oauth-codex\n")


def _setup_openai_interactive():
    """노트북에서 OpenAI API 키 인라인 설정."""
    import os

    from dartlab.core.ai.guide import provider_guide

    existing_key = os.environ.get("OPENAI_API_KEY")
    if existing_key:
        print(f"\n  ✓ OPENAI_API_KEY 환경변수가 설정되어 있습니다. (sk-...{existing_key[-4:]})\n")
        return

    print(provider_guide("openai"))
    print()

    try:
        from getpass import getpass

        key = getpass("  API 키 입력 (Enter로 건너뛰기): ").strip()
        if key:
            llm.configure(provider="openai", api_key=key)
            print("\n  ✓ OpenAI API 키가 설정되었습니다.\n")
        else:
            print("\n  건너뛰었습니다.\n")
    except (EOFError, KeyboardInterrupt):
        print("\n  건너뛰었습니다.\n")


def _auto_stream(gen) -> str:
    """Generator를 소비하면서 stdout에 스트리밍 출력, 전체 텍스트 반환."""
    import sys

    chunks: list[str] = []
    for chunk in gen:
        chunks.append(chunk)
        sys.stdout.write(chunk)
        sys.stdout.flush()
    sys.stdout.write("\n")
    sys.stdout.flush()
    return "".join(chunks)


def ask(
    *args: str,
    include: list[str] | None = None,
    exclude: list[str] | None = None,
    provider: str | None = None,
    model: str | None = None,
    stream: bool = True,
    raw: bool = False,
    reflect: bool = False,
    pattern: str | None = None,
    **kwargs,
):
    """LLM에게 기업에 대해 질문.

    Args:
        *args: 자연어 질문 (1개) 또는 (종목, 질문) 2개.
        provider: LLM provider ("openai", "codex", "oauth-codex", "ollama").
        model: 모델 override.
        stream: True면 스트리밍 출력 (기본값). False면 조용히 전체 텍스트 반환.
        raw: True면 Generator를 직접 반환 (커스텀 UI용).
        include: 포함할 데이터 모듈.
        exclude: 제외할 데이터 모듈.
        reflect: True면 답변 자체 검증 (1회 reflection).

    Returns:
        str | None: 전체 답변 텍스트. 설정 오류 시 None. (raw=True일 때만 Generator[str])

    Example::

        import dartlab
        dartlab.llm.configure(provider="openai", api_key="sk-...")

        # 호출하면 스트리밍 출력 + 전체 텍스트 반환
        answer = dartlab.ask("삼성전자 재무건전성 분석해줘")

        # provider + model 지정
        answer = dartlab.ask("삼성전자 분석", provider="openai", model="gpt-4o")

        # (종목, 질문) 분리
        answer = dartlab.ask("005930", "영업이익률 추세는?")

        # 조용히 전체 텍스트만 (배치용)
        answer = dartlab.ask("삼성전자 분석", stream=False)

        # Generator 직접 제어 (커스텀 UI용)
        for chunk in dartlab.ask("삼성전자 분석", raw=True):
            custom_process(chunk)
    """
    from dartlab.ai.runtime.standalone import ask as _ask

    # provider 미지정 시 auto-detect
    if provider is None:
        from dartlab.core.ai.detect import auto_detect_provider

        detected = auto_detect_provider()
        if detected is None:
            from dartlab.core.ai.guide import no_provider_message

            print(no_provider_message())
            return None
        provider = detected

    if len(args) == 2:
        company = Company(args[0])
        question = args[1]
    elif len(args) == 1:
        from dartlab.core.resolve import resolve_from_text

        company, question = resolve_from_text(args[0])
        if company is None:
            print(f"\n  종목을 찾을 수 없습니다: '{args[0]}'")
            print("  종목명 또는 종목코드를 포함해 주세요.")
            print("  예: dartlab.ask('삼성전자 재무건전성 분석해줘')")
            print(f"  검색: dartlab.search('{args[0]}')\n")
            return None
    elif len(args) == 0:
        print("\n  질문을 입력해 주세요.")
        print("  예: dartlab.ask('삼성전자 재무건전성 분석해줘')")
        print("  예: dartlab.ask('005930', '영업이익률 추세는?')\n")
        return None
    else:
        print(f"\n  인자는 1~2개만 허용됩니다 (받은 수: {len(args)})")
        print("  예: dartlab.ask('삼성전자 분석해줘')")
        print("  예: dartlab.ask('005930', '영업이익률 추세는?')\n")
        return None

    if raw:
        return _ask(
            company,
            question,
            include=include,
            exclude=exclude,
            provider=provider,
            model=model,
            stream=stream,
            reflect=reflect,
            pattern=pattern,
            **kwargs,
        )

    if not stream:
        return _ask(
            company,
            question,
            include=include,
            exclude=exclude,
            provider=provider,
            model=model,
            stream=False,
            reflect=reflect,
            pattern=pattern,
            **kwargs,
        )

    gen = _ask(
        company,
        question,
        include=include,
        exclude=exclude,
        provider=provider,
        model=model,
        stream=True,
        reflect=reflect,
        pattern=pattern,
        **kwargs,
    )
    return _auto_stream(gen)


def chat(
    codeOrName: str,
    question: str,
    *,
    provider: str | None = None,
    model: str | None = None,
    max_turns: int = 5,
    on_tool_call=None,
    on_tool_result=None,
    **kwargs,
) -> str:
    """에이전트 모드: LLM이 도구를 선택하여 심화 분석.

    Args:
        codeOrName: 종목코드, 회사명, 또는 US ticker.
        question: 질문 텍스트.
        provider: LLM provider.
        model: 모델 override.
        max_turns: 최대 도구 호출 반복 횟수.

    Example::

        import dartlab
        dartlab.chat("005930", "배당 추세를 분석하고 이상 징후를 찾아줘")
    """
    from dartlab.ai.runtime.standalone import chat as _chat

    company = Company(codeOrName)
    return _chat(
        company,
        question,
        provider=provider,
        model=model,
        max_turns=max_turns,
        on_tool_call=on_tool_call,
        on_tool_result=on_tool_result,
        **kwargs,
    )


def plugins():
    """로드된 플러그인 목록 반환.

    Example::

        import dartlab
        dartlab.plugins()  # [PluginMeta(name="esg-scores", ...)]
    """
    from dartlab.core.plugins import discover, get_loaded_plugins

    discover()
    return get_loaded_plugins()


def reload_plugins():
    """플러그인 재스캔 — pip install 후 재시작 없이 즉시 인식.

    Example::

        # 1. 새 플러그인 설치
        # !uv pip install dartlab-plugin-esg

        # 2. 재스캔
        dartlab.reload_plugins()

        # 3. 즉시 사용
        dartlab.Company("005930").show("esgScore")
    """
    from dartlab.core.plugins import rediscover

    return rediscover()


def audit(codeOrName: str):
    """감사 Red Flag 분석.

    Example::

        import dartlab
        dartlab.audit("005930")
    """
    c = Company(codeOrName)
    from dartlab.analysis.financial.insight.pipeline import analyzeAudit

    return analyzeAudit(c)


def forecast(codeOrName: str, *, horizon: int = 3):
    """매출 앙상블 예측.

    Example::

        import dartlab
        dartlab.forecast("005930")
    """
    c = Company(codeOrName)
    from dartlab.analysis.forecast.revenueForecast import forecastRevenue

    ts = c.finance.timeseries
    if ts is None:
        return None
    series = ts[0] if isinstance(ts, tuple) else ts
    currency = getattr(c, "currency", "KRW")
    return forecastRevenue(
        series,
        stockCode=getattr(c, "stockCode", None),
        sectorKey=getattr(c, "sectorKey", None),
        market=getattr(c, "market", "KR"),
        horizon=horizon,
        currency=currency,
    )


def valuation(codeOrName: str, *, shares: int | None = None):
    """종합 밸류에이션 (DCF + DDM + 상대가치).

    Example::

        import dartlab
        dartlab.valuation("005930")
    """
    c = Company(codeOrName)
    from dartlab.analysis.valuation.valuation import fullValuation

    ts = c.finance.timeseries
    if ts is None:
        return None
    series = ts[0] if isinstance(ts, tuple) else ts
    currency = getattr(c, "currency", "KRW")
    if shares is None:
        profile = getattr(c, "profile", None)
        if profile:
            shares = getattr(profile, "sharesOutstanding", None)
            if shares:
                shares = int(shares)
    return fullValuation(series, shares=shares, currency=currency)


def insights(codeOrName: str):
    """7영역 등급 분석.

    Example::

        import dartlab
        dartlab.insights("005930")
    """
    c = Company(codeOrName)
    from dartlab.analysis.financial.insight import analyze

    return analyze(c.stockCode, company=c)


def simulation(codeOrName: str, *, scenarios: list[str] | None = None):
    """경제 시나리오 시뮬레이션.

    Example::

        import dartlab
        dartlab.simulation("005930")
    """
    c = Company(codeOrName)
    from dartlab.analysis.forecast.simulation import simulateAllScenarios

    ts = c.finance.timeseries
    if ts is None:
        return None
    series = ts[0] if isinstance(ts, tuple) else ts
    return simulateAllScenarios(
        series,
        sectorKey=getattr(c, "sectorKey", None),
        scenarios=scenarios,
    )


def research(codeOrName: str, *, sections: list[str] | None = None, includeMarket: bool = True):
    """종합 기업분석 리포트.

    Example::

        import dartlab
        dartlab.research("005930")
    """
    c = Company(codeOrName)
    from dartlab.analysis.financial.research import generateResearch

    return generateResearch(c, sections=sections, includeMarket=includeMarket)


def scanAccount(
    snakeId: str,
    *,
    market: str = "dart",
    sjDiv: str | None = None,
    fsPref: str = "CFS",
    annual: bool = False,
):
    """전종목 단일 계정 시계열.

    Args:
        snakeId: 계정 식별자. 영문("sales") 또는 한글("매출액") 모두 가능.
        market: "dart" (한국, 기본) 또는 "edgar" (미국).
        sjDiv: 재무제표 구분 ("IS", "BS", "CF"). None이면 자동 결정. (dart만)
        fsPref: 연결/별도 우선순위 ("CFS"=연결 우선, "OFS"=별도 우선). (dart만)
        annual: True면 연간 (기본 False=분기별 standalone).

    Example::

        import dartlab
        dartlab.scan("account", "매출액")                      # DART 분기별
        dartlab.scan("account", "매출액", annual=True)          # DART 연간
        dartlab.scan("account", "sales", market="edgar")        # EDGAR 분기별
        dartlab.scan("account", "total_assets", market="edgar", annual=True)
    """
    if market == "edgar":
        from dartlab.providers.edgar.finance.scanAccount import scanAccount as _edgarScan

        return _edgarScan(snakeId, annual=annual)

    from dartlab.providers.dart.finance.scanAccount import scanAccount as _scan

    return _scan(snakeId, sjDiv=sjDiv, fsPref=fsPref, annual=annual)


def scanRatio(
    ratioName: str,
    *,
    market: str = "dart",
    fsPref: str = "CFS",
    annual: bool = False,
):
    """전종목 단일 재무비율 시계열.

    Args:
        ratioName: 비율 식별자 ("roe", "operatingMargin", "debtRatio" 등).
        market: "dart" (한국, 기본) 또는 "edgar" (미국).
        fsPref: 연결/별도 우선순위. (dart만)
        annual: True면 연간 (기본 False=분기별).

    Example::

        import dartlab
        dartlab.scan("ratio", "roe")                           # DART 분기별
        dartlab.scan("ratio", "operatingMargin", annual=True)  # DART 연간
        dartlab.scan("ratio", "roe", market="edgar", annual=True)  # EDGAR 연간
    """
    if market == "edgar":
        from dartlab.providers.edgar.finance.scanAccount import scanRatio as _edgarRatio

        return _edgarRatio(ratioName, annual=annual)

    from dartlab.providers.dart.finance.scanAccount import scanRatio as _ratio

    return _ratio(ratioName, fsPref=fsPref, annual=annual)





def digest(
    *,
    sector: str | None = None,
    top_n: int = 20,
    format: str = "dataframe",
    stock_codes: list[str] | None = None,
    verbose: bool = False,
):
    """시장 전체 공시 변화 다이제스트.

    로컬에 다운로드된 docs 데이터를 순회하며 중요도 높은 변화를 집계한다.

    Args:
        sector: 섹터 필터 (예: "반도체"). None이면 전체.
        top_n: 상위 N개.
        format: "dataframe", "markdown", "json".
        stock_codes: 직접 종목코드 목록 지정.
        verbose: 진행 상황 출력.

    Example::

        import dartlab
        dartlab.digest()                          # 전체 시장
        dartlab.digest(sector="반도체")             # 섹터별
        dartlab.digest(format="markdown")          # 마크다운 출력
    """
    from dartlab.scan.watch.digest import build_digest
    from dartlab.scan.watch.scanner import scan_market

    scan_df = scan_market(
        sector=sector,
        top_n=top_n,
        stock_codes=stock_codes,
        verbose=verbose,
    )

    if format == "dataframe":
        return scan_df

    title = f"{sector} 섹터 변화 다이제스트" if sector else None
    return build_digest(scan_df, format=format, title=title, top_n=top_n)


class _Module(sys.modules[__name__].__class__):
    """dartlab.verbose / dartlab.dataDir / dartlab.chart|table|text 프록시."""

    @property
    def verbose(self):
        """전역 verbose 설정 조회."""
        return config.verbose

    @verbose.setter
    def verbose(self, value):
        config.verbose = value

    @property
    def dataDir(self):
        """데이터 저장 디렉토리 경로 조회."""
        return config.dataDir

    @dataDir.setter
    def dataDir(self, value):
        config.dataDir = str(value)

    def __getattr__(self, name):
        if name == "scan":
            from dartlab.scan import Scan

            instance = Scan()
            setattr(self, name, instance)
            return instance
        if name == "analysis":
            from dartlab.analysis.strategy import Analysis

            instance = Analysis()
            setattr(self, name, instance)
            return instance
        if name in ("chart", "table", "text"):
            import importlib

            mod = importlib.import_module(f"dartlab.tools.{name}")
            setattr(self, name, mod)
            return mod
        raise AttributeError(f"module 'dartlab' has no attribute {name!r}")


sys.modules[__name__].__class__ = _Module


__all__ = [
    "Company",
    "Fred",
    "OpenDart",
    "OpenEdgar",
    "config",
    "core",
    "engines",
    "llm",
    "ask",
    "chat",
    "setup",
    "search",
    "listing",
    "collect",
    "collectAll",
    "downloadAll",
    "scan",
    "analysis",
    "network",
    "news",
    "audit",
    "forecast",
    "valuation",
    "insights",
    "simulation",
    "governance",
    "workforce",
    "capital",
    "debt",
    "research",
    "digest",
    "scanAccount",
    "scanRatio",
    "plugins",
    "reload_plugins",
    "verbose",
    "dataDir",
    "getKindList",
    "codeToName",
    "nameToCode",
    "searchName",
    "fuzzySearch",
    "chart",
    "table",
    "text",
    "Review",
    "SelectResult",
    "ChartResult",
]
