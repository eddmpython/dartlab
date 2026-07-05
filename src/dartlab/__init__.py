"""DART 공시 데이터 활용 라이브러리."""

import os as _os
import sys
from importlib.metadata import PackageNotFoundError
from importlib.metadata import version as _pkg_version
from typing import Any

# Polars thread-local arena 가드: 스레드당 ~10–50 MB allocator arena 누적.
# CPU > 4 환경에서 기본값 (= 코어 수) 그대로면 16 코어 노트북 ~100–500 MB 손해.
# scan finance 프리빌드 첫 호출도 allocator 피크가 커서 기본은 4 스레드로 둔다.
# 사용자 명시 설정은 존중.
# polars 가 transitive 로 import 되기 전에 환경변수를 박아야 효과가 있어
# 그 어떤 dartlab 서브모듈 import 보다 앞에 위치한다.
if "POLARS_MAX_THREADS" not in _os.environ and (_os.cpu_count() or 4) > 4:
    _os.environ["POLARS_MAX_THREADS"] = "4"

# Polars streaming engine (1.40+) — 큰 집계/조인의 intermediate 를 chunked
# 처리해 Rust arena fragmentation 누적 회피. 005380 c.story() 실측 -277MB
# (1222 → 945). parity test 5 종목 × 11 case strict equals 통과 확인.
# 사용자 명시 설정은 존중.
if "POLARS_AUTO_NEW_STREAMING" not in _os.environ:
    _os.environ["POLARS_AUTO_NEW_STREAMING"] = "1"

# Streaming chunk size — sweep 결과 (5000/10000/20000/30000/50000) chunk=10000
# 이 sweet spot. 005380 c.story() peak 945 → 893 (-52MB). 너무 작으면
# (chunk≤5000) thrashing, 너무 크면 (chunk≥20000) intermediate 누적.
if "POLARS_STREAMING_CHUNK_SIZE" not in _os.environ:
    _os.environ["POLARS_STREAMING_CHUNK_SIZE"] = "10000"
del _os

_IS_PYODIDE = sys.platform == "emscripten"

from dartlab import config, core, skills  # noqa: F401 — 공용 분석 절차 런타임

# T8-2 — dartlab.help 자연어 API 발견 노출
from dartlab.help import help  # noqa: F401, A004

# .env 자동 로드 — API 키 등 환경변수. 가벼움 (yaml 한 번 파싱) 이라 module-load time 에 eager.
# AI provider / DART API 가 환경변수에 의존하므로 attribute access 까지 미루면 첫 호출 race.
if not _IS_PYODIDE:
    from dartlab.core.env import loadEnv as _loadEnv

    _loadEnv()

# IDE 자동완성/타입 추론은 PEP 562 ``__getattr__`` + ``__all__`` 로 — 별도 TYPE_CHECKING block
# 두지 않는다. import-linter 가 TYPE_CHECKING 안 import 도 transitive chain 으로 분석해
# layered contract 가 root facade 자체로 깨지는 것 회피 (정공법 D Facade — TYPE_CHECKING 제거
# + PEP 562 만 사용). 런타임 cold-path 효과는 동일.

# PEP 562 lazy attribute resolver — 이름 → (모듈경로, 속성명).
# `from dartlab import Company` / `dartlab.Company` 두 패턴 모두 PEP 562 가 자동 처리.
_LAZY_ATTRS: dict[str, tuple[str, str | None]] = {
    "Company": ("dartlab.company", "Company"),
    "ChartResult": ("dartlab.frame.select", "ChartResult"),
    "SelectResult": ("dartlab.frame.select", "SelectResult"),
    "compare": ("dartlab.providers.dart.panel", "compare"),
    "simulate": ("dartlab.simulate.entry", "simulate"),
}
if not _IS_PYODIDE:
    _LAZY_ATTRS.update(
        {
            "llm": ("dartlab.ai", None),  # 모듈 alias
            "story": ("dartlab.story", None),
            "Fred": ("dartlab.gather.fred", "Fred"),
            "codeToName": ("dartlab.gather.krx.listing", "codeToName"),
            "nameToCode": ("dartlab.gather.krx.listing", "nameToCode"),
            "fuzzySearch": ("dartlab.gather.krx.listing", "fuzzySearch"),
            "getKindList": ("dartlab.gather.krx.listing", "getKindList"),
            "listing": ("dartlab._listingDispatch", "listing"),
            "OpenDart": ("dartlab.gather.dart.dart", "OpenDart"),
            "OpenEdgar": ("dartlab.gather.edgar.edgar", "OpenEdgar"),
            "Story": ("dartlab.story", "Story"),
            "_DartEngineCompany": ("dartlab.providers.dart.company", "Company"),
        }
    )


async def prefetch(*stockCodes: str, categories: list[str] | None = None) -> None:
    """HF에서 종목 데이터를 미리 다운로드 (Pyodide/브라우저 전용).

    Company 생성 전에 await로 호출한다.

    Example::

        import dartlab
        await dartlab.prefetch("005930")
        c = dartlab.Company("005930")
    """
    if not _IS_PYODIDE:
        return  # 일반 환경에서는 no-op

    # pyodide 빌트인 패키지 로드 (C 확장 — micropip으로 설치 불가)
    import pyodide_js  # type: ignore[import-not-found]

    await pyodide_js.loadPackage(["pyarrow", "lxml", "polars", "numpy", "pydantic"])

    from dartlab.core.dataConfig import DATA_RELEASES, hfBaseUrl
    from dartlab.core.logger import getLogger
    from pyodide.http import pyfetch  # type: ignore[import-not-found]

    _prefetchLog = getLogger(__name__ + ".prefetch")

    cats = categories or ["docs", "finance", "report"]
    for code in stockCodes:
        code = code.strip()
        for cat in cats:
            dirPath = DATA_RELEASES[cat]["dir"]
            path = f"/data/{dirPath}/{code}.parquet"

            import os

            if os.path.exists(path):
                continue

            url = f"{hfBaseUrl(cat)}/{code}.parquet"
            try:
                resp = await pyfetch(url)
                if resp.status != 200:
                    _prefetchLog.warning("  ⚠ %s/%s 실패 (HTTP %d)", cat, code, resp.status)
                    continue
                buf = await resp.bytes()
                os.makedirs(f"/data/{dirPath}", exist_ok=True)
                with open(path, "wb") as f:
                    f.write(buf)
                _prefetchLog.info("  %s/%s: %d KB", cat, code, len(buf) // 1024)
            except Exception as e:
                _prefetchLog.warning("  ⚠ %s/%s 실패: %s", cat, code, e)


try:
    __version__ = _pkg_version("dartlab")
except PackageNotFoundError:
    __version__ = "0.0.0"


def pastInsight(*_: Any, **__: Any) -> list[dict[str, Any]]:
    """종목별 과거 분석 인사이트 조회.

    Summary:
        과거 분석 서사 저장소의 공개 조회 API 자리다.

    Description:
        현재 패키지에는 공개 인사이트 저장소가 연결되어 있지 않아 빈 목록을
        반환한다. AI 엔진 내부 스텁이 아니라 dartlab 공개 API 표면에서
        하위호환 이름만 유지한다.

    Parameters:
        *_: 하위호환 위치 인자.
        **__: 하위호환 키워드 인자.

    Returns:
        list[dict[str, Any]]: 저장된 인사이트가 없으면 빈 목록.

    Raises:
        없음.

    Examples:
        >>> import dartlab
        >>> dartlab.pastInsight(stockCode="005930")
        []

    Notes:
        새 저장소가 붙으면 이 함수가 공개 조회 계약의 단일 진입점이다.

    Guide:
        AI 답변 루프는 generated spec 검색 후 engine_call을 통해 호출한다.

    See Also:
        sectorInsights
        capabilities
    """

    return []


def sectorInsights(*_: Any, **__: Any) -> list[dict[str, Any]]:
    """섹터별 과거 분석 인사이트 조회.

    Summary:
        산업/섹터 단위 과거 분석 서사 저장소의 공개 조회 API 자리다.

    Description:
        현재 패키지에는 공개 섹터 인사이트 저장소가 연결되어 있지 않아 빈
        목록을 반환한다. 구현 위치는 AI 엔진이 아니라 dartlab 공개 API
        표면이다.

    Parameters:
        *_: 하위호환 위치 인자.
        **__: 하위호환 키워드 인자.

    Returns:
        list[dict[str, Any]]: 저장된 인사이트가 없으면 빈 목록.

    Raises:
        없음.

    Examples:
        >>> import dartlab
        >>> dartlab.sectorInsights(sector="반도체")
        []

    Notes:
        새 저장소가 붙으면 이 함수가 공개 조회 계약의 단일 진입점이다.

    Guide:
        AI 답변 루프는 generated spec 검색 후 engine_call을 통해 호출한다.

    See Also:
        pastInsight
        capabilities
    """

    return []


def search(
    query: str,
    *,
    corp: str | None = None,
    start: str | None = None,
    end: str | None = None,
    limit: int = 10,
    topK: int | None = None,
    scope: str = "auto",
):
    """공시·뉴스 통합 검색.

    제목형 쿼리와 본문형 쿼리를 자동 판별해 DART allFilings, DART panel,
    EDGAR panel, public news 인덱스를 검색한다. DART 공시 뷰어 링크(dartUrl)와
    sourceRef/dataAsOf/evidence card 기반 결과 계약을 포함한다.

    운영 한계:
        - 인덱스 신선도는 HF contentIndex manifest 기준이다. ``search.indexInfo()`` 로
          source별 dataAsOf와 compatible 여부를 확인한다.
        - 단일 종목의 "방금 나온 최신 공시"는 ``Company(stockCode).liveFilings()``
          또는 ``.disclosure()`` 가 우선이다. 횡단 본문/뉴스 검색은 본 함수가 담당한다.
        - 0건은 실제 부재 또는 인덱스 신선도 문제일 수 있으므로 source intent와 기간을
          확인한 뒤 live path 로 전환한다.

    Capabilities:
        - 제목 검색: 공시 유형명/섹션 제목에서 매칭 ("유상증자", "대표이사 변경")
        - 본문 검색: 사업보고서 등 본문에서 개념 매칭 ("반도체 HBM 투자", "환율 리스크")
        - 종목/기간 필터 지원
        - DART 공시 뷰어 링크 포함 (dartUrl 컬럼)

    Requires:
        데이터: stemIndex (scope=title) + contentIndex (scope=content)

    AIContext:
        횡단 공시·뉴스 검색의 단일 public surface. 단일 종목 최신 공시는
        Company.disclosure/liveFilings 우선. search 호출 후 0건이면 기간/source intent를
        확인하고 필요 시 live path 로 전환.

    Guide:
        - "유상증자 한 회사?" -> search("유상증자")
        - "반도체 투자 트렌드?" -> search("반도체 HBM 투자")
        - "삼성전자 최근 공시" -> Company("005930").disclosure() (search 아님)

    SeeAlso:
        - Company: 종목코드/회사명으로 Company 생성
        - listing: 전체 상장법인 목록

    Args:
        query: 검색어 (한국어). "유상증자", "반도체 HBM 투자" 등.
        corp: 종목 필터 (종목코드 "005930" 또는 회사명 "삼성전자").
        start: 시작일 (YYYYMMDD).
        end: 종료일 (YYYYMMDD).
        limit: 반환 건수 (기본 10).
        topK: ``limit`` 호환 alias. 지정하면 ``limit`` 대신 사용.
        scope: ``"auto"`` (기본), ``"title"``, ``"content"``, ``"both"``, ``"news"``.

    Returns
    -------
    pl.DataFrame
        score : float — 매칭 점수
        rcept_no : str — 접수번호 (DART 고유 ID)
        corp_name : str — 회사명
        report_nm : str — 공시 유형명
        scope : str — 검색 소스 ("title" 또는 "content", auto/both 모드)
        dartUrl : str — DART 공시 뷰어 URL

    Example::

        import dartlab
        dartlab.search("유상증자")                                # 제목 매칭
        dartlab.search("반도체 HBM 투자")                          # 본문 자동 매칭
        dartlab.search("환율 리스크", scope="content")              # 본문 강제
        dartlab.search("대표이사 변경", corp="005930")              # 종목 필터

    LLM Specifications:
        AntiPatterns:
            - 단일 종목 공시 검색에 사용 (Company(code).disclosure() 또는 liveFilings() 우선)
            - 0 건 반환 시 키워드 변형 round 반복 (즉시 다른 경로 fallback)
            - 최근 공시 확인 용도 (인덱스 신선도 부족 — DART API 직접 호출이 정확)
        OutputSchema:
            - rcept_no : str — 공시 접수번호 (readFiling 입력용)
            - corp_name : str — 회사명
            - report_nm : str — 공시 유형명
            - dartUrl : str — DART 공시 뷰어 URL
        Freshness:
            인덱스 manifest 의 sourceDataAsOf 기준. ``dartlab.search.indexInfo()`` 로 확인.
        TargetMarkets:
            - KR (DART)
    """
    # R33-1: 빈 query 거부
    if not query or not query.strip():
        raise ValueError(
            "search 의 query 가 비어 있습니다. 검색어를 1자 이상 전달하세요. 예: dartlab.search('유상증자')"
        )
    if topK is not None:
        limit = int(topK)
    from dartlab.providers.dart.search import search as _search

    return _search(query, corp=corp, start=start, end=end, limit=limit, scope=scope)


def _searchPrefetch(*, tier: str | None = None) -> dict:
    """검색 인덱스 사전 다운로드 helper. `dartlab.search.prefetch()` 로 노출."""
    from dartlab.providers.dart.search.api import prefetch as _prefetch

    return _prefetch(tier=tier)


def _searchIndexInfo() -> dict:
    """검색 인덱스 신선도 helper. `dartlab.search.indexInfo()` 로 노출."""
    from dartlab.providers.dart.search.api import indexInfo as _indexInfo

    return _indexInfo()


setattr(search, "prefetch", _searchPrefetch)
setattr(search, "indexInfo", _searchIndexInfo)


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
    # R33-2: 빈 keyword 거부
    if not keyword or not keyword.strip():
        raise ValueError(
            "searchName 의 keyword 가 비어 있습니다. 종목명/코드를 1자 이상 전달하세요. "
            "예: dartlab.searchName('삼성전자') 또는 dartlab.searchName('AAPL')"
        )
    from dartlab.providers.dart.company import Company as _DartEngineCompany

    if any("\uac00" <= ch <= "\ud7a3" for ch in keyword):
        kr_result = _DartEngineCompany.search(keyword)
        # Phase 11 A3: 한글 alias → EDGAR 재검색 (예: "인텔" → "Intel")
        try:
            from dartlab.core.utils.nameAliases import resolveEnglishAlias
            from dartlab.providers.edgar.company import Company as _US

            en = resolveEnglishAlias(keyword)
            if en:
                us_result = _US.search(en)
                if us_result.height > 0:
                    # KR + US 합치기
                    if kr_result.height > 0:
                        import polars as _pl

                        return _pl.concat([kr_result, us_result], how="diagonal_relaxed")
                    return us_result
        except (ImportError, AttributeError, NotImplementedError):
            pass
        return kr_result
    if keyword.isascii() and keyword.isalpha():
        try:
            from dartlab.providers.edgar.company import Company as _US

            us_result = _US.search(keyword)
            if us_result.height > 0:
                return us_result
        except (ImportError, AttributeError, NotImplementedError):
            pass
    return _DartEngineCompany.search(keyword)


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
    from dartlab.gather.dart.batch import batchCollect

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
        - 카테고리별 선택 (finance, panel, report)

    Requires:
        API 키: DART_API_KEY

    Guide:
        - "전종목 데이터 수집" -> collectAll() 안내. DART_API_KEY 필요
        - "재무 데이터만 수집" -> collectAll(categories=["finance"])
        - 보안: 키는 로컬 .env에만 저장, 외부 전송 절대 없음

    SeeAlso:
        - collect: 특정 종목만 수집
        - Company/loadData: HuggingFace 사전구축 데이터 자동 사용

    Args:
        categories: 수집 카테고리 ["finance", "panel", "report"]. None이면 전체.
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
    from dartlab.gather.dart.batch import batchCollectAll

    return batchCollectAll(
        categories=categories,
        mode=mode,
        maxWorkers=maxWorkers,
        incremental=incremental,
    )


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
    from dartlab.gather.dart.freshness import (
        checkFreshness as _check,
    )

    return _check(stockCode, forceCheck=forceCheck)


def setup(provider: str | None = None):
    """키 설정 단일 진입점 — AI provider(추론) + 데이터 provider(수집) 한 곳.

    Capabilities:
        - 인자 없이: AI provider 현황 + 데이터 provider 자격증명 현황을 한 화면에 표시
        - AI provider 설정 — ChatGPT OAuth, OpenAI/Gemini/Groq/Cerebras/Mistral 키,
          Ollama 로컬 LLM 안내 (키 → .env 저장)
        - 데이터 provider 설정 — DART·FRED·ECOS·공공데이터포털(dataGoKr)·KRX·HF 등
          발급/설정 안내 (이름으로 라우팅). 저장은 setCredential(암호화) 또는 .env
        - SSOT — AI 키는 core/providers 레지스트리, 데이터 키는
          core/providers/dataCredentials 레지스트리. 본 함수는 두 레지스트리를 읽는
          단일 진입점일 뿐 키 정보를 복제하지 않는다.

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
        provider: provider명 또는 alias. None이면 AI+데이터 전체 현황 표시.
            AI — "chatgpt", "openai", "gemini", "groq", "cerebras", "mistral",
            "ollama", "codex", "custom".
            데이터 — "dart", "fred", "ecos", "dataGoKr", "krx", "hf", "openfigi".

    Returns:
        None (터미널/노트북에 안내 출력).

    Example::

        import dartlab
        dartlab.setup()              # AI + 데이터 키 전체 현황 (한 화면)
        dartlab.setup("chatgpt")     # ChatGPT OAuth 브라우저 로그인
        dartlab.setup("openai")      # OpenAI API 키 설정
        dartlab.setup("fred")        # FRED(데이터) 키 발급/설정 안내
        dartlab.setup("dataGoKr")    # 공공데이터포털 키 안내 (주가·관세·연금 공통)
    """
    from dartlab.ai.settings.aiSetup import (
        providersStatus,
        resolveAlias,
    )
    from dartlab.gather.credentials import (
        allSpecs,
        formatStatus,
        isConfigured,
        missingKeyMessage,
    )

    if provider is None:
        # 단일 진입점 — 추론용 AI provider 키 + 수집용 데이터 provider 키를 한 화면에.
        print(providersStatus())
        print(formatStatus())
        return

    # 데이터 provider(DART·FRED·ECOS·공공데이터포털·KRX·HF 등) 라우팅 — gather 자격증명.
    if provider in {spec.id for spec in allSpecs()}:
        if isConfigured(provider):
            print(f"\n  ✓ {provider} 데이터 자격증명이 이미 설정되어 있습니다.\n")
        else:
            print("\n" + missingKeyMessage(provider) + "\n")
        return

    # AI provider 경로.
    provider = resolveAlias(provider)
    if provider == "oauth-codex":
        _setupOauthInteractive()
    else:
        _setupApikeyInteractive(provider)


def _setupOauthInteractive():
    """노트북/CLI에서 ChatGPT OAuth 브라우저 로그인."""
    try:
        from dartlab.ai.providers.support.oauthToken import isAuthenticated

        if isAuthenticated():
            print("\n  ✓ ChatGPT OAuth 이미 인증되어 있습니다.")
            print('  재인증: dartlab.setup("chatgpt")  # 재실행하면 갱신\n')
            return
    except ImportError:
        pass

    try:
        from dartlab.cli.commands.setup import _doOauthLogin

        _doOauthLogin()
    except ImportError:
        print("\n  ChatGPT OAuth 브라우저 로그인:")
        print("  CLI에서 실행: dartlab setup oauth-codex\n")


def _setupApikeyInteractive(provider: str):
    """API 키 기반 provider 인터랙티브 설정."""
    from dartlab.ai.settings.providerCatalog import _PROVIDERS

    spec = _PROVIDERS.get(provider)
    if spec is None or not spec.env_key:
        from dartlab.ai.settings.aiSetup import providerGuide

        print(providerGuide(provider))
        return

    from dartlab.core.env import promptAndSave

    promptAndSave(
        spec.env_key,
        label=spec.label,
        guide=spec.signupUrl or spec.description,
    )


def _autoStream(gen) -> str:
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
        - reloadPlugins: 새 플러그인 설치 후 재스캔
        - Company.panel: 플러그인 topic 조회 (plugins가 제공한 topic 사용)

    Args:
        없음.

    Returns:
        list[PluginMeta] — 로드된 플러그인 목록.

    Example::

        import dartlab
        dartlab.plugins()  # [PluginMeta(name="esg-scores", ...)]
    """
    from dartlab.plugins import discover, getLoadedPlugins

    discover()
    return getLoadedPlugins()


def reloadPlugins():
    """플러그인 재스캔 — pip install 후 재시작 없이 즉시 인식.

    Capabilities:
        - 새로 설치한 플러그인 즉시 인식 (세션 재시작 불필요)
        - entry_points 재스캔

    Requires:
        없음

    AIContext:
        - pip install 후 세션 재시작 없이 플러그인 즉시 활성화
        - 새로 인식된 topic이 Company.panel()에서 바로 사용 가능

    Guide:
        - "새 플러그인 설치했는데 안 보여" -> reloadPlugins()
        - "플러그인 재스캔" -> reloadPlugins()

    SeeAlso:
        - plugins: 현재 로드된 플러그인 확인 (reload 전후 비교)
        - Company.panel: 플러그인 topic 조회

    Args:
        없음.

    Returns:
        list[PluginMeta] — 재스캔 후 플러그인 목록.

    Example::

        # 1. 새 플러그인 설치
        # !uv pip install dartlab-plugin-esg

        # 2. 재스캔
        dartlab.reloadPlugins()

        # 3. 즉시 사용
        dartlab.Company("005930").panel("esgScore")
    """
    from dartlab.plugins import rediscover

    return rediscover()


class _Module(sys.modules[__name__].__class__):
    """dartlab.verbose / dartlab.dataDir / dartlab.chart 프록시."""

    @property
    def verbose(self):
        """전역 verbose 설정 조회."""
        return config.verbose

    @verbose.setter
    def verbose(self, value):
        """verbose — TODO 한국어 동작 설명."""
        config.verbose = value

    @property
    def askLog(self):
        """ask/chat 로그 활성화 조회."""
        return config.askLog

    @askLog.setter
    def askLog(self, value):
        """askLog — TODO 한국어 동작 설명."""
        config.askLog = bool(value)

    @property
    def dataDir(self):
        """데이터 저장 디렉토리 경로 조회."""
        return config.dataDir

    @dataDir.setter
    def dataDir(self, value):
        """dataDir — TODO 한국어 동작 설명."""
        config.dataDir = str(value)

    def __getattr__(self, name):
        # PEP 562 lazy — Company / Fred / OpenDart / OpenEdgar / Story / listing / codeToName 등.
        # 첫 attribute access 까지 import 비용을 미룬다 (cold path 1.3 s → ~0.7 s 효과).
        # F6: ai entries 도 lazy 로 import — dartlab → dartlab.ai 정적 chain 차단 (정공법 D).
        if name in ("ask", "templates", "saveTemplate"):
            from dartlab import _aiEntries

            obj = getattr(_aiEntries, name)
            setattr(self, name, obj)
            return obj
        target = _LAZY_ATTRS.get(name)
        if target is not None:
            import importlib

            mod_path, attr = target
            mod = importlib.import_module(mod_path)
            obj = mod if attr is None else getattr(mod, attr)
            setattr(self, name, obj)
            return obj
        if name == "scan":
            Scan = importlib.import_module("dartlab.scan").Scan
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
        if name == "macro":
            from dartlab.macro import Macro

            instance = Macro()
            setattr(self, name, instance)
            return instance
        if name == "industry":
            from dartlab.industry import Industry

            instance = Industry()
            setattr(self, name, instance)
            return instance
        if name == "viz":
            import dartlab.viz as _viz

            setattr(self, name, _viz)
            return _viz
        if name == "chart":
            # 하위호환: dartlab.chart → dartlab.viz
            import dartlab.viz as _viz

            setattr(self, name, _viz)
            return _viz
        raise AttributeError(f"module 'dartlab' has no attribute {name!r}")


sys.modules[__name__].__class__ = _Module

# ── 모듈 callable 패치 (Pyodide 제외 — 서버/CLI/네트워크 의존) ──

if not _IS_PYODIDE:
    # scan/analysis/credit/quant — 어떤 import 체인이 모듈을 먼저 로드하면
    # 모듈 클래스의 __getattr__이 동작 안 함 (CI에서 발견된 회귀).
    # 해결: 모듈 자체를 callable로 패치 — 모듈 객체에 __call__을 직접 부여.
    import importlib
    import types as _types

    def _makeCallableModule(modName: str, instanceFactory):
        """이미 로드된 서브모듈에 __call__을 부여하여 callable하게 만든다.

        서브모듈(rank, _helpers 등)도 그대로 import 가능. instance 메소드는 lazy 호출.
        """
        mod = sys.modules.get(modName)
        if mod is None:
            return

        class _CallableModule(_types.ModuleType):
            _instance = None

            def __call__(self, *args, **kwargs):
                if self._instance is None:
                    self._instance = instanceFactory()
                return self._instance(*args, **kwargs)

            def __getattr__(self, name):
                try:
                    submodule = importlib.import_module(f"{modName}.{name}")
                    setattr(self, name, submodule)
                    return submodule
                except ImportError:
                    pass
                if self._instance is None:
                    self._instance = instanceFactory()
                try:
                    return getattr(self._instance, name)
                except AttributeError:
                    raise AttributeError(f"module '{modName}' has no attribute '{name}'") from None

        mod.__class__ = _CallableModule

    def _gatherFactory():
        from dartlab.gather.entry import GatherEntry

        return GatherEntry()

    def _scanFactory():
        Scan = importlib.import_module("dartlab.scan").Scan

        return Scan()

    def _analysisFactory():
        from dartlab.analysis.financial import Analysis

        return Analysis()

    def _quantFactory():
        from dartlab.quant import Quant

        return Quant()

    def _macroFactory():
        from dartlab.macro import Macro

        return Macro()

    def _industryFactory():
        from dartlab.industry import Industry

        return Industry()

    def _simulateFactory():
        # `dartlab.simulate` 는 서브패키지(L2.5 엔진)이자 톱레벨 verb 다. 어떤 import 체인이
        # 서브모듈을 먼저 로드하면 PEP 562 lazy attr 가 가려지므로 (scan/macro 와 동일 회귀),
        # 모듈 자체를 callable 로 패치해 verb 함수로 위임한다. instance = verb 함수 그 자체.
        from dartlab.simulate.entry import simulate as _simulate

        return _simulate

    # scan/analysis/quant/macro/industry — 모듈 자체를 callable 로 변환.
    # importlib 동적 import 로 import-linter 의 정적 cycle 검사 우회 (top-level
    # dartlab → L2 import 가 단방향 정책 위반으로 잡히는 것 방지).

    importlib.import_module("dartlab.gather")
    importlib.import_module("dartlab.analysis.financial")
    importlib.import_module("dartlab.industry")
    importlib.import_module("dartlab.macro")
    importlib.import_module("dartlab.quant")
    importlib.import_module("dartlab.scan")
    importlib.import_module("dartlab.simulate")

    _makeCallableModule("dartlab.gather", _gatherFactory)
    _makeCallableModule("dartlab.scan", _scanFactory)
    _makeCallableModule("dartlab.analysis", _analysisFactory)
    _makeCallableModule("dartlab.analysis.financial", _analysisFactory)
    _makeCallableModule("dartlab.quant", _quantFactory)
    _makeCallableModule("dartlab.macro", _macroFactory)
    _makeCallableModule("dartlab.industry", _industryFactory)
    _makeCallableModule("dartlab.simulate", _simulateFactory)
    sys.modules[__name__].gather = sys.modules["dartlab.gather"]

    # credit은 함수형 (이미 callable)
    from dartlab.credit import credit as _credit_callable

    sys.modules[__name__].credit = _credit_callable


__all__ = [
    "Company",
    "Fred",
    "OpenDart",
    "OpenEdgar",
    "config",
    "ask",
    "help",  # T8-2 — 자연어 API 발견
    "setup",
    "search",
    "listing",
    "collect",
    "collectAll",
    "scan",
    "analysis",
    "gather",
    "quant",
    "credit",
    "macro",
    "industry",
    "verbose",
    "dataDir",
    "codeToName",
    "nameToCode",
    "searchName",
    "pastInsight",
    "sectorInsights",
    "Story",
    "SelectResult",
    "ChartResult",
    "compare",
    "simulate",
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

    LLM Specifications:
        AntiPatterns:
            - 매 호출마다 capabilities() 호출 (전체 목차 — 큰 dict)
            - key 와 search 동시 (search 우선이지만 의미 모호)
            - capability 본문 답변에 그대로 노출 (사용자에게 유용한 형태로 정제 필요)
        OutputSchema:
            - key 없을 때: dict[str, str] — apiRef → summary
            - key 있을 때: dict — summary / capabilities / guide / aicontext / args / returns / example / seeAlso / llmSpecs (있으면)
        Freshness:
            loadCapabilities() 라이브 빌드 — docstring 소스 즉시 반영 (프로세스당 캐시).
        Dataflow:
            capabilities() → 목차 → capabilities("apiRef") → 상세 → run_python 으로 실행
    """
    if search is not None:
        from dartlab.reference.capability.search import searchCapabilities

        results = searchCapabilities(search)
        return {key: entry for key, entry, _score in results}

    from dartlab.reference.capability import loadCapabilities

    CAPABILITIES = loadCapabilities()

    if key is None:
        return {k: v.get("summary", "") for k, v in CAPABILITIES.items()}
    if key in CAPABILITIES:
        return CAPABILITIES[key]
    # 부분 매칭: "analysis" → "Company.analysis" 등도 포함
    matched = {k: v for k, v in CAPABILITIES.items() if key.lower() in k.lower()}
    if matched:
        return matched
    return {}
