"""DART 공시 데이터 활용 라이브러리."""

import sys
from importlib.metadata import PackageNotFoundError
from importlib.metadata import version as _pkg_version

from dartlab import ai as llm  # noqa: F401 — 하위호환
from dartlab import config, core  # noqa: F401 — 하위호환
from dartlab.audit import queryAudit, runAudit  # noqa: F401 — 하위호환
from dartlab.company import Company
from dartlab.core.env import loadEnv as _loadEnv
from dartlab.core.select import ChartResult, SelectResult
from dartlab.gather.fred import Fred
from dartlab.gather.listing import codeToName, fuzzySearch, getKindList, nameToCode  # noqa: F401
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


def search(
    query: str,
    *,
    corp: str | None = None,
    start: str | None = None,
    end: str | None = None,
    topK: int = 10,
):
    """공시 원문 검색. *(alpha)*

    Ngram+Synonym 기반 검색. 모델 불필요, cold start 0ms.
    DART 공시 뷰어 링크(dartUrl) 포함.

    Capabilities:
        - 전체 공시 원문 검색 (수시공시 포함)
        - 자연어 동의어 확장 ("돈을 빌렸다" → 사채/차입/전환사채)
        - 종목/기간 필터 지원
        - DART 공시 뷰어 링크 포함 (dartUrl 컬럼)

    Requires:
        데이터: allFilings (수집 + buildIndex 필요)

    AIContext:
        공시 내용을 자연어로 찾을 때 사용. 결과의 dartUrl로 원문 확인 가능.
        종목 찾기는 Company("삼성전자")를 사용.

    Guide:
        - "유상증자 한 회사?" -> search("유상증자 결정")
        - "삼성전자 최근 공시?" -> search("공시", corp="005930")

    SeeAlso:
        - Company: 종목코드/회사명으로 Company 생성
        - listing: 전체 상장법인 목록

    Args:
        query: 검색어 (한국어). "유상증자 결정", "대표이사 변경" 등.
        corp: 종목 필터 (종목코드 "005930" 또는 회사명 "삼성전자").
        start: 시작일 (YYYYMMDD).
        end: 종료일 (YYYYMMDD).
        topK: 반환 건수 (기본 10).

    Returns:
        pl.DataFrame — 검색 결과.
        컬럼: score, rcept_no, corp_name, rcept_dt, report_nm,
        section_title, text, dartUrl

    Example::

        import dartlab
        dartlab.search("유상증자 결정")
        dartlab.search("대표이사 변경", corp="005930")
        dartlab.search("전환사채", start="20240101", topK=5)
    """
    from dartlab.core.search import search as _search

    return _search(query, corp=corp, start=start, end=end, topK=topK)


def searchName(keyword: str):
    """종목명/코드로 종목 찾기 (KR + US).

    Args:
        keyword: 종목명, 종목코드, 또는 ticker.

    Returns:
        pl.DataFrame — 종목 검색 결과.

    Example::

        dartlab.searchName("삼성전자")
        dartlab.searchName("AAPL")
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

    Capabilities:
        - KR 전체 상장법인 목록 (KOSPI + KOSDAQ)
        - 종목코드, 종목명, 시장구분, 업종 포함
        - US listing은 향후 지원 예정

    Requires:
        데이터: listing (자동 다운로드)

    AIContext:
        전종목 대상 필터링/통계에 사용. scan()과 조합하여 시장 전체 분석.

    Guide:
        - "상장된 회사 몇 개야?" -> listing()으로 전체 목록 조회 후 개수
        - "코스닥 회사 목록?" -> listing()에서 market 필터
        - API 키 불필요.

    SeeAlso:
        - search: 키워드로 특정 종목 검색
        - scan: 전종목 횡단 비교 분석

    Args:
        market: "KR" 또는 "US". None이면 KR 기본.

    Returns:
        pl.DataFrame — 전체 상장법인 (code, name, market, sector 등).

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
    """지정 종목 DART 데이터 수집 (OpenAPI).

    Capabilities:
        - 종목별 DART 공시 데이터 직접 수집 (finance, docs, report)
        - 멀티키 병렬 수집 (DART_API_KEYS 쉼표 구분)
        - 증분 수집 — 이미 있는 데이터는 건너뜀
        - 카테고리별 선택 수집

    Requires:
        API 키: DART_API_KEY

    AIContext:
        사용자가 특정 종목의 최신 데이터를 직접 수집할 때 사용.

    Guide:
        - "데이터 수집해줘" -> DART_API_KEY 필요. dartlab.setup("dart-key", "YOUR_KEY")로 설정 안내
        - "삼성전자 재무 데이터 수집" -> collect("005930", categories=["finance"])
        - 보안: 키는 로컬 .env에만 저장, 외부 전송 절대 없음

    SeeAlso:
        - Company: 수집된 데이터로 Company 생성하여 분석
        - search: 종목코드 모를 때 먼저 검색

    Args:
        *codes: 종목코드 1개 이상 ("005930", "000660").
        categories: 수집 카테고리 ["finance", "docs", "report"]. None이면 전체.
        incremental: True면 증분 수집 (기본). False면 전체 재수집.

    Returns:
        dict — 종목코드별 카테고리별 수집 건수.

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
    """전체 상장종목 DART 데이터 일괄 수집.

    Capabilities:
        - 전체 상장종목 DART 공시 데이터 일괄 수집
        - 미수집 종목만 선별 수집 (mode="new") 또는 전체 재수집 (mode="all")
        - 멀티키 병렬 수집 (DART_API_KEYS 쉼표 구분)
        - 카테고리별 선택 (finance, docs, report)

    Requires:
        API 키: DART_API_KEY

    Guide:
        - "전종목 데이터 수집" -> collectAll() 안내. DART_API_KEY 필요
        - "재무 데이터만 수집" -> collectAll(categories=["finance"])
        - 보안: 키는 로컬 .env에만 저장, 외부 전송 절대 없음

    SeeAlso:
        - collect: 특정 종목만 수집
        - downloadAll: HuggingFace 사전구축 데이터 (API 키 불필요, 더 빠름)

    Args:
        categories: 수집 카테고리 ["finance", "docs", "report"]. None이면 전체.
        mode: "new" (미수집만, 기본) 또는 "all" (전체 재수집).
        maxWorkers: 병렬 워커 수. None이면 키 수에 따라 자동.
        incremental: True면 증분 수집. False면 전체 재수집.

    Returns:
        dict — 종목코드별 카테고리별 수집 건수.

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
    """HuggingFace에서 전체 시장 데이터 다운로드.

    Capabilities:
        - HuggingFace 사전 구축 데이터 일괄 다운로드
        - finance (~600MB, 2700+종목), docs (~8GB, 2500+종목), report (~320MB, 2700+종목)
        - 이어받기/병렬 다운로드 지원 (huggingface_hub)
        - 전사 분석(scanAccount, governance, digest 등)에 필요한 데이터 사전 준비

    Requires:
        없음 (HuggingFace 공개 데이터셋)

    Guide:
        - "데이터 어떻게 받아?" -> downloadAll("finance") 안내. API 키 불필요
        - "scan 쓰려면?" -> downloadAll("finance") + downloadAll("report") 필요
        - finance 먼저 (600MB), report 다음 (320MB), docs는 대용량 주의 (8GB)

    SeeAlso:
        - scan: 다운로드된 데이터로 전종목 비교
        - collect: DART API로 직접 수집 (최신 데이터, API 키 필요)

    Args:
        category: "finance" (재무 ~600MB), "docs" (공시 ~8GB), "report" (보고서 ~320MB).
        forceUpdate: True면 이미 있는 파일도 최신으로 갱신.

    Returns:
        None.

    Example::

        import dartlab
        dartlab.downloadAll("finance")   # 재무 전체 — scanAccount/scanRatio 등에 필요
        dartlab.downloadAll("report")    # 보고서 전체 — governance/workforce/capital/debt에 필요
        dartlab.downloadAll("docs")      # 공시 전체 — digest에 필요 (대용량 ~8GB)
    """
    from dartlab.core.dataLoader import downloadAll as _downloadAll

    _downloadAll(category, forceUpdate=forceUpdate)


def checkFreshness(stockCode: str, *, forceCheck: bool = False):
    """종목의 로컬 데이터가 최신인지 DART API로 확인.

    Capabilities:
        - 로컬 데이터와 DART 서버의 최신 공시 비교
        - 누락 공시 수 + 최신 여부 판정
        - 캐시된 결과 재사용 (forceCheck=False)

    Requires:
        API 키: DART_API_KEY

    AIContext:
        - 분석 전 데이터 최신성 확인에 사용
        - isFresh=False이면 collect()로 갱신 권장
        - missingCount로 누락 규모 파악 후 수집 우선순위 판단

    Guide:
        - "내 데이터 최신이야?" -> checkFreshness("005930")
        - "공시 누락 있어?" -> checkFreshness로 missingCount 확인
        - "데이터 업데이트 필요해?" -> checkFreshness 후 collect 안내

    SeeAlso:
        - collect: 누락 공시 실제 수집 (checkFreshness에서 발견한 gap 채우기)
        - Company: 종목 데이터 접근 (최신 데이터 기반 분석)

    Args:
        stockCode: 종목코드 ("005930").
        forceCheck: True면 캐시 무시, DART API 강제 조회.

    Returns:
        FreshnessResult — isFresh (bool), missingCount (int), lastLocalDate, lastRemoteDate.

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


def setup(provider: str | None = None):
    """AI provider 설정 안내 + 인터랙티브 설정.

    Capabilities:
        - 전체 AI provider 설정 현황 테이블 표시
        - provider별 대화형 설정 (키 입력 → .env 저장)
        - ChatGPT OAuth 브라우저 로그인
        - OpenAI/Gemini/Groq/Cerebras/Mistral API 키 설정
        - Ollama 로컬 LLM 설치 안내

    Requires:
        없음

    AIContext:
        - AI 분석 기능 사용 전 provider 설정 상태 확인
        - 미설정 provider 감지 시 setup() 안내로 연결
        - 설정 완료 여부를 프로그래밍 방식으로 체크 가능

    Guide:
        - "AI 설정 어떻게 해?" -> setup()으로 전체 현황 확인
        - "ChatGPT 연결하고 싶어" -> setup("chatgpt")
        - "OpenAI 키 등록" -> setup("openai")
        - "Ollama 어떻게 써?" -> setup("ollama")

    SeeAlso:
        - ask: AI 질문 (setup 완료 후 사용)
        - chat: AI 대화 (setup 완료 후 사용)
        - llm.configure: 프로그래밍 방식 provider 설정

    Args:
        provider: provider명 또는 alias. None이면 전체 현황 표시.
            지원: "chatgpt", "openai", "gemini", "groq", "cerebras",
            "mistral", "ollama", "codex", "custom".

    Returns:
        None (터미널/노트북에 안내 출력).

    Example::

        import dartlab
        dartlab.setup()              # 전체 provider 현황
        dartlab.setup("chatgpt")     # ChatGPT OAuth 브라우저 로그인
        dartlab.setup("openai")      # OpenAI API 키 설정
        dartlab.setup("ollama")      # Ollama 설치 안내
    """
    from dartlab.core.ai.guide import (
        providers_status,
        resolve_alias,
    )

    if provider is None:
        print(providers_status())
        return

    provider = resolve_alias(provider)

    if provider == "oauth-codex":
        _setup_oauth_interactive()
    else:
        _setup_apikey_interactive(provider)


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


def _setup_apikey_interactive(provider: str):
    """API 키 기반 provider 인터랙티브 설정."""
    from dartlab.guide.providers import _PROVIDERS

    spec = _PROVIDERS.get(provider)
    if spec is None or not spec.env_key:
        from dartlab.core.ai.guide import provider_guide

        print(provider_guide(provider))
        return

    from dartlab.guide.env import promptAndSave

    promptAndSave(
        spec.env_key,
        label=spec.label,
        guide=spec.signupUrl or spec.description,
    )


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
    template: str | None = None,
    modules: list[str] | None = None,
    **kwargs,
):
    """LLM에게 기업에 대해 질문.

    Capabilities:
        - 자연어로 기업 분석 질문 (종목 자동 감지)
        - 스트리밍 출력 (기본) / 배치 반환 / Generator 직접 제어
        - 엔진 자동 계산 → LLM 해석 (Engine-First)
        - 데이터 모듈 include/exclude로 분석 범위 제어
        - 자체 검증 (reflect=True)

    Requires:
        AI: provider 설정 (dartlab.setup() 참조)

    AIContext:
        - 재무비율, 추세, 동종업계 비교를 자동 계산하여 LLM에 제공
        - sections 서술형 데이터 + finance 숫자 데이터 동시 주입
        - tool calling provider에서는 LLM이 추가 데이터 자율 탐색

    Guide:
        - "삼성전자 분석해줘" -> ask("삼성전자 재무건전성 분석해줘")
        - "이 회사 괜찮아?" -> ask("종목코드", "이 회사 투자해도 괜찮아?")
        - "AI 설정 어떻게 해?" -> dartlab.setup()으로 provider/키 설정 안내
        - provider 미설정 시 자동 감지. 설정 방법: dartlab.llm.configure(provider="openai", api_key="sk-...")
        - 보안: API 키는 로컬 .env에만 저장, 외부 전송 절대 없음

    SeeAlso:
        - chat: 대화형 연속 분석 (멀티턴)
        - Company: 프로그래밍 방식 데이터 접근
        - scan: 전종목 비교 (ask보다 직접적)

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
        import warnings

        warnings.warn(
            "dartlab.ask(stock, question) is deprecated. Use dartlab.ask('삼성전자 분석해줘') instead.",
            DeprecationWarning,
            stacklevel=2,
        )
        company = Company(args[0])
        question = args[1]
    elif len(args) == 1:
        company = None
        question = args[0]
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

    # kwargs에서 company 제거 (내부에서 직접 전달)
    kwargs.pop("company", None)
    _call_kwargs = dict(
        company=company,
        include=include,
        exclude=exclude,
        provider=provider,
        model=model,
        reflect=reflect,
        pattern=pattern,
        template=template,
        modules=modules,
        **kwargs,
    )

    if raw:
        return _ask(question, stream=stream, **_call_kwargs)

    if not stream:
        return _ask(question, stream=False, **_call_kwargs)

    gen = _ask(question, stream=True, **_call_kwargs)
    return _auto_stream(gen)


def templates(name: str | None = None):
    """분석 템플릿 목록 또는 특정 템플릿 내용.

    Example::

        dartlab.templates()          # 전체 목록
        dartlab.templates("가치투자") # 특정 템플릿 내용
    """
    from dartlab.ai import templates as _templates

    return _templates(name)


def saveTemplate(name: str, *, content: str | None = None, file: str | None = None):
    """사용자 분석 템플릿 저장. ~/.dartlab/templates/{name}.md

    Example::

        dartlab.saveTemplate("my_style", content="## 내 기준\\n- ROE > 15%")
    """
    from dartlab.ai import saveTemplate as _save

    return _save(name, content=content, file=file)


def chat(
    *args: str,
    provider: str | None = None,
    model: str | None = None,
    max_turns: int = 5,
    on_tool_call=None,
    on_tool_result=None,
    **kwargs,
) -> str:
    """에이전트 모드: LLM이 도구를 선택하여 심화 분석.

    Capabilities:
        - LLM이 dartlab 도구를 자율적으로 선택/실행
        - 원본 공시 탐색, 계정 시계열 비교, 섹터 통계 등 심화 분석
        - 최대 N회 도구 호출 반복 (multi-turn)
        - 도구 호출/결과 콜백으로 UI 연동
        - 종목 없이도 동작 (시장 전체 질문, 메타 질문 등)

    Requires:
        AI: provider 설정 (tool calling 지원 provider 권장)

    AIContext:
        - ask()와 동일한 기본 컨텍스트 + 저수준 도구 접근
        - LLM이 부족하다 판단하면 추가 데이터 자율 수집
        - company=None이면 scan/gather/system 도구만 활성화

    Guide:
        - "깊게 분석해줘" -> chat("005930", "배당 추세를 분석하고 이상 징후를 찾아줘")
        - "시장 전체 거버넌스 비교" -> chat("코스피 거버넌스 좋은 회사 찾아줘")
        - "dartlab 뭐 할 수 있어?" -> chat("dartlab 기능 알려줘")
        - ask()보다 심화 분석이 필요할 때 사용. LLM이 자율적으로 도구 호출

    SeeAlso:
        - ask: 단일 질문 (간단한 분석)
        - Company: 프로그래밍 방식 직접 접근
        - scan: 전종목 횡단분석

    Args:
        *args: (종목, 질문) 2개 또는 질문만 1개.
        provider: LLM provider.
        model: 모델 override.
        max_turns: 최대 도구 호출 반복 횟수.

    Returns:
        str: 최종 답변 텍스트.

    Example::

        import dartlab
        dartlab.chat("005930", "배당 추세를 분석하고 이상 징후를 찾아줘")
        dartlab.chat("코스피 ROE 높은 회사 알려줘")  # 종목 없이 시장 질문
    """
    from dartlab.ai.runtime.standalone import chat as _chat

    if len(args) == 2:
        company = Company(args[0])
        question = args[1]
    elif len(args) == 1:
        from dartlab.core.resolve import resolve_from_text

        company, question = resolve_from_text(args[0])
        if company is None:
            question = args[0]
    elif len(args) == 0:
        print("\n  질문을 입력해 주세요.")
        print("  예: dartlab.chat('005930', '배당 추세 분석해줘')")
        print("  예: dartlab.chat('코스피 ROE 높은 회사 알려줘')\n")
        return ""
    else:
        print(f"\n  인자는 1~2개만 허용됩니다 (받은 수: {len(args)})")
        return ""

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

    Capabilities:
        - 설치된 dartlab 플러그인 자동 탐색
        - 플러그인 메타데이터 (이름, 버전, 제공 topic) 조회

    Requires:
        없음

    AIContext:
        - 확장 기능 탐색 시 설치된 플러그인 목록 확인
        - 플러그인이 제공하는 topic을 show()에서 사용 가능
        - 플러그인 유무에 따라 분석 범위 동적 결정

    Guide:
        - "플러그인 뭐 있어?" -> plugins()
        - "확장 기능 목록" -> plugins()로 설치된 플러그인 확인
        - "ESG 플러그인 있어?" -> plugins()에서 검색

    SeeAlso:
        - reload_plugins: 새 플러그인 설치 후 재스캔
        - Company.show: 플러그인 topic 조회 (plugins가 제공한 topic 사용)

    Args:
        없음.

    Returns:
        list[PluginMeta] — 로드된 플러그인 목록.

    Example::

        import dartlab
        dartlab.plugins()  # [PluginMeta(name="esg-scores", ...)]
    """
    from dartlab.core.plugins import discover, get_loaded_plugins

    discover()
    return get_loaded_plugins()


def reload_plugins():
    """플러그인 재스캔 — pip install 후 재시작 없이 즉시 인식.

    Capabilities:
        - 새로 설치한 플러그인 즉시 인식 (세션 재시작 불필요)
        - entry_points 재스캔

    Requires:
        없음

    AIContext:
        - pip install 후 세션 재시작 없이 플러그인 즉시 활성화
        - 새로 인식된 topic이 Company.show()에서 바로 사용 가능

    Guide:
        - "새 플러그인 설치했는데 안 보여" -> reload_plugins()
        - "플러그인 재스캔" -> reload_plugins()

    SeeAlso:
        - plugins: 현재 로드된 플러그인 확인 (reload 전후 비교)
        - Company.show: 플러그인 topic 조회

    Args:
        없음.

    Returns:
        list[PluginMeta] — 재스캔 후 플러그인 목록.

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
    def askLog(self):
        """ask/chat 로그 활성화 조회."""
        return config.askLog

    @askLog.setter
    def askLog(self, value):
        config.askLog = bool(value)

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
            from dartlab.analysis.financial import Analysis

            instance = Analysis()
            setattr(self, name, instance)
            return instance
        if name == "credit":
            from dartlab.credit import credit

            setattr(self, name, credit)
            return credit
        if name == "quant":
            from dartlab.quant import Quant

            instance = Quant()
            setattr(self, name, instance)
            return instance
        if name == "chart":
            from dartlab.chart import Chart

            instance = Chart()
            setattr(self, name, instance)
            return instance
        if name == "table":
            from dartlab.table import Table

            instance = Table()
            setattr(self, name, instance)
            return instance
        if name == "text":
            import importlib

            mod = importlib.import_module("dartlab.tools.text")
            setattr(self, name, mod)
            return mod
        raise AttributeError(f"module 'dartlab' has no attribute {name!r}")


sys.modules[__name__].__class__ = _Module

# gather 모듈을 GatherEntry callable로 덮어쓰기
# (gather 서브모듈이 top-level import로 이미 로드되므로 __getattr__ lazy 불가)
from dartlab.gather.entry import GatherEntry as _GatherEntry

sys.modules[__name__].gather = _GatherEntry()


__all__ = [
    "Company",
    "Fred",
    "OpenDart",
    "OpenEdgar",
    "config",
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
    "gather",
    "credit",
    "quant",
    "verbose",
    "dataDir",
    "codeToName",
    "nameToCode",
    "searchName",
    "Review",
    "SelectResult",
    "ChartResult",
    "capabilities",
]


def capabilities(key: str | None = None, *, search: str | None = None) -> dict | list[str]:
    """dartlab 전체 기능 카탈로그 조회.

    Capabilities:
        CAPABILITIES dict에서 부분 조회 가능.
        key 없이 호출 시 전체 키 목록(summary 포함) 반환.
        key 지정 시 해당 항목의 상세(guide, capabilities, seeAlso 등) 반환.
        search 지정 시 자연어 질문 기반 관련 API 검색 (상위 10개).

    Requires:
        없음

    AIContext:
        AI가 "dartlab에 뭐가 있는지" 모를 때 탐색용.
        capabilities() → 목차 확인 → capabilities("analysis") → 상세 확인 → execute_code.
        capabilities(search="재무건전성") → 질문 관련 API 검색 → 코드 생성.

    Guide:
        - "dartlab 뭐 할 수 있어?" -> capabilities()
        - "분석 기능 뭐 있어?" -> capabilities("analysis")
        - "scan 어떻게 써?" -> capabilities("scan")
        - "재무건전성 관련 API?" -> capabilities(search="재무건전성")

    SeeAlso:
        - ask: AI 질문 (capabilities로 기능 파악 후 ask로 분석)
        - setup: AI provider 설정 (capabilities 확인 후 설정)

    Args:
        key: 조회할 기능 키. None이면 전체 목차.
        search: 자연어 질문 기반 검색. key와 동시 사용 불가.

    Returns:
        dict | list[str] — key 있으면 해당 항목 dict, 없으면 키+summary 목록.

    Example::

        dartlab.capabilities()                       # 전체 목차
        dartlab.capabilities("analysis")             # analysis 상세 (guide, capabilities)
        dartlab.capabilities("Company.analysis")     # Company.analysis 상세
        dartlab.capabilities("scan")                 # scan 상세
        dartlab.capabilities(search="재무건전성")     # 질문 기반 검색 → 상위 10개
    """
    if search is not None:
        from dartlab.core._capabilitySearch import searchCapabilities

        results = searchCapabilities(search)
        return {key: entry for key, entry, _score in results}

    from dartlab.core._generatedCapabilities import CAPABILITIES

    if key is None:
        return {k: v.get("summary", "") for k, v in CAPABILITIES.items()}
    if key in CAPABILITIES:
        return CAPABILITIES[key]
    # 부분 매칭: "analysis" → "Company.analysis" 등도 포함
    matched = {k: v for k, v in CAPABILITIES.items() if key.lower() in k.lower()}
    if matched:
        return matched
    return {}
