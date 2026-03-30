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
from dartlab.audit import queryAudit, runAudit
from dartlab.review import Review

# .env 자동 로드 — API 키 등 환경변수
_loadEnv()

try:
    __version__ = _pkg_version("dartlab")
except PackageNotFoundError:
    __version__ = "0.0.0"


def search(keyword: str):
    """종목 검색 (KR + US 통합).

    Capabilities:
        - 한글 입력 시 DART 종목 검색 (종목명, 종목코드)
        - 영문 입력 시 EDGAR 종목 검색 (ticker, 회사명)
        - 부분 일치, 초성 검색 지원 (KR)

    Requires:
        데이터: listing (자동 다운로드)

    AIContext:
        종목코드를 모를 때 사용. 결과에서 종목코드 확인 후 Company 생성.

    Guide:
        - "삼성전자 종목코드 뭐야?" -> search("삼성전자")로 종목코드 확인
        - "애플 티커?" -> search("AAPL")로 EDGAR 종목 검색
        - API 키 불필요. listing 데이터만으로 동작.

    SeeAlso:
        - Company: 종목코드 확인 후 Company 생성하여 상세 분석
        - listing: 전체 상장법인 목록 조회

    Args:
        keyword: 종목명, 종목코드, 또는 ticker. 한글이면 KR, 영문이면 US 자동 감지.

    Returns:
        pl.DataFrame — 검색 결과 (code, name, market 등).

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
        dict — {종목코드: {카테고리: 수집 건수}}.

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
        dict — {종목코드: {카테고리: 수집 건수}}.

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


def network():
    """한국 상장사 전체 관계 지도.

    Capabilities:
        - 상장사 간 지분 관계 네트워크 시각화
        - 브라우저에서 인터랙티브 그래프 표시
        - 노드(기업) + 엣지(지분 관계) 구조

    Requires:
        데이터: docs (자동 다운로드)

    AIContext:
        - 기업 간 지분 관계 파악에 사용
        - 그룹사 구조, 모자회사 관계 시각적 탐색
        - nodes/edges 데이터로 프로그래밍 방식 관계 분석 가능

    Guide:
        - "상장사 관계 보여줘" -> network().show()
        - "기업 간 지분 관계 알려줘" -> network()로 네트워크 데이터 접근
        - "그룹사 구조 시각화" -> network().show()로 브라우저 렌더링

    SeeAlso:
        - governance: 개별 기업 지배구조 상세 (network는 전체 관계 지도)
        - scan: 전종목 횡단 비교 (network는 관계 중심)

    Args:
        없음.

    Returns:
        NetworkResult — .show()로 브라우저 시각화, .nodes/.edges로 데이터 접근.

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

    Capabilities:
        - 전체 상장사 지배구조 횡단 비교
        - 최대주주 지분율, 사외이사 비율, 감사위원회 설치 여부
        - 지분 변동 추이, 특수관계인 거래

    Requires:
        데이터: report (dartlab.downloadAll("report")로 사전 다운로드)

    AIContext:
        - 전체 시장의 지배구조 리스크 스크리닝에 사용
        - 최대주주 지분율 극단값, 사외이사 미선임 기업 탐지
        - governance 점수가 낮은 기업군 필터링 후 심화 분석 연계

    Guide:
        - "지배구조 좋은 기업 찾아줘" -> governance()로 횡단 비교
        - "최대주주 지분율 높은 기업?" -> governance() DataFrame 정렬
        - "사외이사 비율 낮은 곳은?" -> governance() 결과 필터링

    SeeAlso:
        - network: 기업 간 지분 관계 시각화 (governance는 개별 기업 지표)
        - scan: 전종목 횡단 비교 통합 인터페이스
        - workforce: 인력/급여 횡단 비교 (governance와 함께 ESG 분석)

    Args:
        없음.

    Returns:
        pl.DataFrame — 전종목 지배구조 지표 (종목코드, 종목명, 최대주주지분율, ...).

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

    Capabilities:
        - 전체 상장사 임직원 현황 횡단 비교
        - 임직원 수, 평균 근속연수, 평균 급여, 성별 비율
        - 업종별/규모별 비교

    Requires:
        데이터: report (dartlab.downloadAll("report")로 사전 다운로드)

    AIContext:
        - 업종별 인력 효율성 비교에 사용
        - 평균급여 대비 매출/이익 생산성 분석 연계
        - 직원 수 증감 추이로 사업 확장/축소 신호 탐지

    Guide:
        - "평균 급여 높은 기업?" -> workforce() DataFrame 정렬
        - "직원 수 많은 기업 순위" -> workforce() 결과 필터링
        - "인력 현황 비교해줘" -> workforce()로 횡단 비교

    SeeAlso:
        - governance: 지배구조 횡단 비교 (workforce와 함께 ESG 분석)
        - capital: 주주환원 횡단 비교 (인력 투자 vs 주주 환원 비교)
        - scan: 전종목 횡단 비교 통합 인터페이스

    Args:
        없음.

    Returns:
        pl.DataFrame — 전종목 인력 지표 (종목코드, 종목명, 직원수, 평균급여, ...).

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

    Capabilities:
        - 전체 상장사 주주환원 정책 횡단 비교
        - 배당수익률, 배당성향, 자사주 매입/소각 이력
        - 유상증자/무상증자 이력

    Requires:
        데이터: report (dartlab.downloadAll("report")로 사전 다운로드)

    AIContext:
        - 배당주 스크리닝, 주주환원 정책 비교에 사용
        - 배당수익률/배당성향 조합으로 지속가능성 판단
        - 자사주 매입/소각 이력으로 주주 친화도 평가

    Guide:
        - "배당 좋은 기업 찾아줘" -> capital() DataFrame 정렬
        - "자사주 매입한 기업?" -> capital() 결과 필터링
        - "주주환원 비교해줘" -> capital()로 횡단 비교

    SeeAlso:
        - debt: 부채 구조 횡단 비교 (배당 여력과 부채 부담 동시 분석)
        - workforce: 인력/급여 횡단 비교 (인력 투자 vs 주주 환원)
        - insights: 개별 기업 배당 등급 분석 (capital은 전체 시장)

    Args:
        없음.

    Returns:
        pl.DataFrame — 전종목 주주환원 지표 (종목코드, 종목명, 배당수익률, ...).

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

    Capabilities:
        - 전체 상장사 부채 구조 횡단 비교
        - 부채비율, 차입금 의존도, 이자보상배율
        - 단기/장기 차입금 구성, 사채 발행 현황

    Requires:
        데이터: report (dartlab.downloadAll("report")로 사전 다운로드)

    AIContext:
        - 재무 안정성 리스크 스크리닝에 사용
        - 부채비율/이자보상배율 극단값으로 위험 기업 탐지
        - 단기/장기 차입 구조 분석으로 유동성 리스크 평가

    Guide:
        - "부채비율 높은 기업?" -> debt() DataFrame 정렬
        - "재무 안정적인 기업 찾아줘" -> debt() 결과 필터링
        - "부채 구조 비교해줘" -> debt()로 횡단 비교

    SeeAlso:
        - capital: 주주환원 횡단 비교 (부채 vs 배당 균형 분석)
        - insights: 개별 기업 안정성 등급 (debt는 전체 시장)
        - scan: 전종목 횡단 비교 통합 인터페이스

    Args:
        없음.

    Returns:
        pl.DataFrame — 전종목 부채 지표 (종목코드, 종목명, 부채비율, ...).

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
        company = Company(args[0])
        question = args[1]
    elif len(args) == 1:
        from dartlab.core.resolve import resolve_from_text

        company, question = resolve_from_text(args[0])
        if company is None:
            # 종목 없이 AI 진행 (범용 질문: scan, gather, 거시경제 등)
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

    _call_kwargs = dict(
        company=company,
        include=include,
        exclude=exclude,
        provider=provider,
        model=model,
        reflect=reflect,
        pattern=pattern,
        **kwargs,
    )

    if raw:
        return _ask(question, stream=stream, **_call_kwargs)

    if not stream:
        return _ask(question, stream=False, **_call_kwargs)

    gen = _ask(question, stream=True, **_call_kwargs)
    return _auto_stream(gen)


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


def audit(codeOrName: str):
    """감사 Red Flag 분석.

    Capabilities:
        - 감사의견 추이 (최근 5년, 적정/한정/부적정/의견거절)
        - 감사인 변경 이력 + 변경 사유
        - 계속기업 불확실성 플래그
        - 핵심감사사항 (KAM) 추출
        - 내부회계관리제도 검토의견

    Requires:
        데이터: docs + report (자동 다운로드)

    AIContext:
        - 투자 의사결정 전 감사 리스크 사전 점검에 사용
        - goingConcern 플래그로 계속기업 불확실성 즉시 감지
        - 감사인 변경 + 한정의견 조합으로 회계 신뢰도 평가

    Guide:
        - "이 회사 감사의견 괜찮아?" -> audit("005930")
        - "감사인 바뀐 적 있어?" -> audit()에서 auditorChanges 확인
        - "계속기업 불확실성 있어?" -> audit()에서 goingConcern 확인

    SeeAlso:
        - insights: 7영역 종합 등급 (audit는 감사 특화)
        - research: 종합 리포트 (audit 결과 포함)
        - governance: 지배구조 횡단 비교 (감사위원회 정보)

    Args:
        codeOrName: 종목코드 ("005930") 또는 종목명 ("삼성전자").

    Returns:
        dict — opinion, auditorChanges, goingConcern, kam, internalControl 등.

    Example::

        import dartlab
        dartlab.audit("005930")
    """
    c = Company(codeOrName)
    from dartlab.analysis.financial.insight.pipeline import analyzeAudit

    return analyzeAudit(c)


def forecast(codeOrName: str, *, horizon: int = 3):
    """매출 앙상블 예측.

    Capabilities:
        - 매출 시계열 기반 앙상블 예측 (ARIMA + 선형 + 지수평활)
        - 업종 성장률 가중 보정
        - 신뢰구간 (80%, 95%) 제공
        - 최대 N년 전망 (기본 3년)

    Requires:
        데이터: finance (자동 다운로드)

    AIContext:
        - 매출 성장 전망 수치를 DCF/밸류에이션에 입력으로 활용
        - 신뢰구간으로 예측 불확실성 정량화
        - 업종 성장률 반영으로 단순 추세 외삽보다 현실적 전망

    Guide:
        - "매출 전망 보여줘" -> forecast("005930")
        - "5년 뒤 매출 예측" -> forecast("005930", horizon=5)
        - "이 회사 성장할까?" -> forecast()로 매출 추세 확인

    SeeAlso:
        - valuation: 밸류에이션 (forecast 결과를 DCF에 활용)
        - simulation: 시나리오별 재무 영향 (forecast는 기본 전망)
        - insights: 성장성 등급 (forecast는 미래 추정)

    Args:
        codeOrName: 종목코드 ("005930") 또는 종목명.
        horizon: 예측 기간 (년). 기본 3.

    Returns:
        ForecastResult — predicted, confidence80, confidence95, components.

    Example::

        import dartlab
        dartlab.forecast("005930")
        dartlab.forecast("005930", horizon=5)
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

    Capabilities:
        - DCF (잉여현금흐름 할인 모형)
        - DDM (배당할인 모형)
        - 상대가치 (PER/PBR/EV-EBITDA 동종업계 비교)
        - 적정주가 범위 산출

    Requires:
        데이터: finance (자동 다운로드)

    AIContext:
        - 적정주가 범위 산출로 투자 판단 근거 제공
        - DCF/DDM/상대가치 3가지 관점의 교차 검증
        - shares 자동 조회로 주당 가치 즉시 산출

    Guide:
        - "적정 주가 얼마야?" -> valuation("005930")
        - "이 회사 저평가야?" -> valuation()에서 summary 확인
        - "DCF 해줘" -> valuation()에서 dcf 항목 조회

    SeeAlso:
        - forecast: 매출 예측 (valuation의 DCF 입력에 활용)
        - insights: 밸류에이션 등급 (valuation은 절대/상대 가치 상세)
        - research: 종합 리포트 (valuation 결과 포함)

    Args:
        codeOrName: 종목코드 ("005930") 또는 종목명.
        shares: 발행주식수. None이면 프로필에서 자동 조회.

    Returns:
        ValuationResult — dcf, ddm, relative, summary.

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

    Capabilities:
        - 수익성, 성장성, 안정성, 효율성, 현금흐름, 밸류에이션, 배당 — 7영역
        - 각 영역 A~F 등급 부여 + 근거 지표
        - 종합 등급 + 강점/약점 요약
        - 동종업계 백분위 위치

    Requires:
        데이터: finance (자동 다운로드)

    AIContext:
        - 기업의 재무 건전성을 7영역 등급으로 요약
        - 강점/약점 자동 식별로 분석 포커스 결정
        - 동종업계 백분위로 상대적 위치 즉시 파악

    Guide:
        - "이 회사 재무 어때?" -> insights("005930")
        - "수익성 등급 알려줘" -> insights()에서 grades 조회
        - "강점이 뭐야?" -> insights()에서 strengths 확인

    SeeAlso:
        - audit: 감사 Red Flag 분석 (insights는 재무 등급)
        - valuation: 밸류에이션 상세 (insights는 종합 등급)
        - research: 종합 리포트 (insights 결과 포함)

    Args:
        codeOrName: 종목코드 ("005930") 또는 종목명.

    Returns:
        InsightResult — grades (영역별 등급), summary, strengths, weaknesses.

    Example::

        import dartlab
        dartlab.insights("005930")
    """
    c = Company(codeOrName)
    from dartlab.analysis.financial.insight import analyze

    return analyze(c.stockCode, company=c)


def simulation(codeOrName: str, *, scenarios: list[str] | None = None):
    """경제 시나리오 시뮬레이션.

    Capabilities:
        - 거시경제 시나리오별 재무 영향 시뮬레이션
        - 기본 시나리오: 금리 인상, 경기 침체, 원자재 급등, 환율 변동
        - 매출/영업이익/순이익 변동 추정
        - 업종별 민감도 차등 적용

    Requires:
        데이터: finance (자동 다운로드)

    AIContext:
        - 거시 변수 변동이 개별 기업 재무에 미치는 영향 정량화
        - 업종별 민감도 차등으로 현실적 스트레스 테스트
        - 복수 시나리오 동시 비교로 리스크 범위 파악

    Guide:
        - "금리 오르면 이 회사 어떻게 돼?" -> simulation("005930")
        - "경기 침체 시나리오" -> simulation()에서 해당 시나리오 확인
        - "환율 영향 분석" -> simulation()으로 환율 변동 시나리오 조회

    SeeAlso:
        - forecast: 매출 예측 (simulation은 시나리오별 변동)
        - valuation: 밸류에이션 (시나리오별 적정가치 비교에 활용)
        - research: 종합 리포트 (simulation 결과 포함)

    Args:
        codeOrName: 종목코드 ("005930") 또는 종목명.
        scenarios: 시나리오명 목록. None이면 전체 기본 시나리오.

    Returns:
        SimulationResult — scenarios별 재무 영향 추정.

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

    Capabilities:
        - 재무분석 + 시장분석 통합 리포트
        - 섹션별 선택 생성 가능
        - 재무비율 추세, 동종업계 비교, 시장 포지션
        - 구조화된 마크다운 출력

    Requires:
        데이터: finance + docs (자동 다운로드)

    AIContext:
        - 재무 + 시장 + 공시 통합 리포트 자동 생성
        - 마크다운 구조로 LLM이 섹션별 참조 가능
        - 섹션 선택으로 특정 관점만 추출 가능

    Guide:
        - "기업 분석 리포트 만들어줘" -> research("005930")
        - "재무분석만 보고 싶어" -> research("005930", includeMarket=False)
        - "종합 분석해줘" -> research()로 전체 리포트 생성

    SeeAlso:
        - insights: 7영역 등급 (research는 서술형 리포트)
        - ask: AI가 해석하는 분석 (research는 엔진 기반 구조화)
        - forecast: 매출 예측 (research 리포트에 포함)

    Args:
        codeOrName: 종목코드 ("005930") 또는 종목명.
        sections: 포함할 섹션명 목록. None이면 전체.
        includeMarket: True면 시장 분석 포함 (기본).

    Returns:
        ResearchResult — 구조화된 분석 리포트.

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

    Capabilities:
        - 전체 상장종목의 특정 계정 시계열 횡단 비교
        - 한글/영문 계정명 모두 지원 ("매출액" = "sales")
        - DART(KR) + EDGAR(US) 양쪽 지원
        - 분기별/연간 선택, 연결/별도 선택

    Requires:
        데이터: finance (dartlab.downloadAll("finance")로 사전 다운로드)

    AIContext:
        - 전종목 동일 계정을 한 번에 비교하여 이상치/트렌드 탐지
        - 피벗 테이블 형태로 시계열 분석 즉시 가능
        - KR/US 양쪽 시장 동일 인터페이스로 글로벌 비교

    Guide:
        - "전종목 매출 비교" -> scan("account", "매출액")
        - "전체 기업 자산 순위" -> scan("account", "total_assets") 후 정렬
        - "미국 기업 매출 비교" -> scan("account", "sales", market="edgar")

    SeeAlso:
        - scanRatio: 전종목 재무비율 횡단 비교 (scanAccount는 원시 계정)
        - scan: 전종목 횡단 비교 통합 인터페이스
        - Company.finance: 개별 기업 재무 상세

    Args:
        snakeId: 계정 식별자. 영문("sales") 또는 한글("매출액") 모두 가능.
        market: "dart" (한국, 기본) 또는 "edgar" (미국).
        sjDiv: 재무제표 구분 ("IS", "BS", "CF"). None이면 자동 결정. (dart만)
        fsPref: 연결/별도 우선순위 ("CFS"=연결 우선, "OFS"=별도 우선). (dart만)
        annual: True면 연간 (기본 False=분기별 standalone).

    Returns:
        pl.DataFrame — 종목코드 × 기간 피벗 테이블.

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

    Capabilities:
        - 전체 상장종목의 특정 재무비율 시계열 횡단 비교
        - ROE, 영업이익률, 부채비율 등 주요 비율 지원
        - DART(KR) + EDGAR(US) 양쪽 지원
        - 분기별/연간 선택

    Requires:
        데이터: finance (dartlab.downloadAll("finance")로 사전 다운로드)

    AIContext:
        - 전종목 동일 비율을 한 번에 비교하여 업종별 분포 파악
        - ROE/영업이익률 등 핵심 비율의 시장 전체 추이 분석
        - 이상치 기업 탐지 및 피어 그룹 벤치마킹에 활용

    Guide:
        - "전종목 ROE 비교" -> scan("ratio", "roe")
        - "영업이익률 높은 기업 순위" -> scan("ratio", "operatingMargin") 후 정렬
        - "미국 기업 ROE 비교" -> scan("ratio", "roe", market="edgar")

    SeeAlso:
        - scanAccount: 전종목 원시 계정 횡단 비교 (scanRatio는 가공된 비율)
        - scan: 전종목 횡단 비교 통합 인터페이스
        - insights: 개별 기업 등급 (scanRatio는 시장 전체)

    Args:
        ratioName: 비율 식별자 ("roe", "operatingMargin", "debtRatio" 등).
        market: "dart" (한국, 기본) 또는 "edgar" (미국).
        fsPref: 연결/별도 우선순위. (dart만)
        annual: True면 연간 (기본 False=분기별).

    Returns:
        pl.DataFrame — 종목코드 × 기간 피벗 테이블.

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

    Capabilities:
        - 전체 상장사 공시 변화 중요도 순위
        - 섹터별 필터링
        - 텍스트 변화량 + 재무 변화 통합 스코어링
        - DataFrame/마크다운/JSON 출력

    Requires:
        데이터: docs (dartlab.downloadAll("docs")로 사전 다운로드)

    AIContext:
        - 시장 전체에서 공시 변화가 큰 기업을 중요도 순으로 제공
        - 섹터별 필터링으로 관심 업종의 변화 포착
        - 마크다운/JSON 출력으로 LLM 컨텍스트에 직접 주입 가능

    Guide:
        - "최근 공시 변화 큰 기업?" -> digest()
        - "반도체 섹터 공시 변화" -> digest(sector="반도체")
        - "시장 동향 요약해줘" -> digest(format="markdown")

    SeeAlso:
        - scan: 전종목 횡단 비교 통합 (digest는 공시 변화 특화)
        - Company.diff: 개별 기업 기간간 변화 (digest는 시장 전체)
        - checkFreshness: 데이터 최신성 확인 (digest 전 갱신 여부 판단)

    Args:
        sector: 섹터 필터 (예: "반도체"). None이면 전체.
        top_n: 상위 N개.
        format: "dataframe", "markdown", "json".
        stock_codes: 직접 종목코드 목록 지정.
        verbose: 진행 상황 출력.

    Returns:
        pl.DataFrame | str — format에 따라 DataFrame 또는 마크다운/JSON 문자열.

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
    "gather",
    "network",
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
