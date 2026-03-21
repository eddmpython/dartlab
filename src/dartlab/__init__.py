"""DART 공시 데이터 활용 라이브러리."""

import sys
from importlib.metadata import PackageNotFoundError
from importlib.metadata import version as _pkg_version

from dartlab import config, core, engines
from dartlab.company import Company
from dartlab.core.kindList import codeToName, fuzzySearch, getKindList, nameToCode, searchName
from dartlab.engines import ai as llm
from dartlab.engines.dart.company import Company as _DartEngineCompany
from dartlab.engines.dart.openapi.dart import Dart, OpenDart
from dartlab.engines.edgar.openapi.edgar import OpenEdgar

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
            from dartlab.engines.edgar.company import Company as _US

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
            from dartlab.engines.edgar.company import Company as _US

            return _US.listing()
        except (ImportError, AttributeError, NotImplementedError):
            raise NotImplementedError("US listing은 아직 지원되지 않습니다")
    return _DartEngineCompany.listing()


def network():
    """한국 상장사 전체 관계 지도.

    Example::

        import dartlab
        dartlab.network().show()  # 브라우저에서 전체 네트워크
    """
    from dartlab.engines.dart.scan.network import build_graph, export_full
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
    from dartlab.engines.dart.scan.governance import scan_governance

    return scan_governance()


def workforce():
    """한국 상장사 전체 인력/급여 스캔.

    Example::

        import dartlab
        df = dartlab.workforce()
    """
    from dartlab.engines.dart.scan.workforce import scan_workforce

    return scan_workforce()


def capital():
    """한국 상장사 전체 주주환원 스캔.

    Example::

        import dartlab
        df = dartlab.capital()
    """
    from dartlab.engines.dart.scan.capital import scan_capital

    return scan_capital()


def debt():
    """한국 상장사 전체 부채 구조 스캔.

    Example::

        import dartlab
        df = dartlab.debt()
    """
    from dartlab.engines.dart.scan.debt import scan_debt

    return scan_debt()


def screen(preset: str = "가치주"):
    """시장 스크리닝 — 프리셋 기반 종목 필터.

    Args:
        preset: 프리셋 이름 ("가치주", "성장주", "턴어라운드", "현금부자",
                "고위험", "자본잠식", "소형고수익", "대형안정").

    Example::

        import dartlab
        df = dartlab.screen("가치주")    # ROE≥10, 부채≤100 등
        df = dartlab.screen("고위험")    # 부채≥200, ICR<3
    """
    from dartlab.engines.rank.screen import screen as _screen

    return _screen(preset)


def benchmark():
    """섹터별 핵심 비율 벤치마크 (P10, median, P90).

    Example::

        import dartlab
        bm = dartlab.benchmark()   # 섹터 × 비율 정상 범위
    """
    from dartlab.engines.rank.screen import benchmark as _benchmark

    return _benchmark()


def signal(keyword: str | None = None):
    """서술형 공시 시장 시그널 — 키워드 트렌드 탐지.

    Args:
        keyword: 특정 키워드만 필터. None이면 전체 48개 키워드.

    Example::

        import dartlab
        df = dartlab.signal()        # 전체 키워드 트렌드
        df = dartlab.signal("AI")    # AI 키워드 연도별 추이
    """
    from dartlab.engines.dart.scan.signal import scan_signal

    return scan_signal(keyword)


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
        from dartlab.engines.ai.providers.support.oauth_token import is_authenticated

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
        str: 전체 답변 텍스트. (raw=True일 때만 Generator[str])

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
    from dartlab.engines.ai.runtime.standalone import ask as _ask

    # provider 미지정 시 auto-detect
    if provider is None:
        from dartlab.core.ai.detect import auto_detect_provider

        detected = auto_detect_provider()
        if detected is None:
            from dartlab.core.ai.guide import no_provider_message

            msg = no_provider_message()
            print(msg)
            raise RuntimeError("AI provider가 설정되지 않았습니다. dartlab.setup()을 실행하세요.")
        provider = detected

    if len(args) == 2:
        company = Company(args[0])
        question = args[1]
    elif len(args) == 1:
        from dartlab.core.resolve import resolve_from_text

        company, question = resolve_from_text(args[0])
        if company is None:
            raise ValueError(
                f"종목을 찾을 수 없습니다: '{args[0]}'\n"
                "종목명 또는 종목코드를 포함해 주세요.\n"
                "예: dartlab.ask('삼성전자 재무건전성 분석해줘')"
            )
    elif len(args) == 0:
        raise TypeError("질문을 입력해 주세요. 예: dartlab.ask('삼성전자 분석해줘')")
    else:
        raise TypeError(f"인자는 1~2개만 허용됩니다 (받은 수: {len(args)})")

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
    from dartlab.engines.ai.runtime.standalone import chat as _chat

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


def groupHealth():
    """그룹사 건전성 분석 — 네트워크 × 재무비율 교차.

    Returns:
        (summary, weakLinks) 튜플.

    Example::

        import dartlab
        summary, weakLinks = dartlab.groupHealth()
    """
    from dartlab.engines.dart.scan.network.health import groupHealth as _groupHealth

    return _groupHealth()


class _Module(sys.modules[__name__].__class__):
    """dartlab.verbose / dartlab.dataDir / dartlab.chart|table|text 프록시."""

    @property
    def verbose(self):
        return config.verbose

    @verbose.setter
    def verbose(self, value):
        config.verbose = value

    @property
    def dataDir(self):
        return config.dataDir

    @dataDir.setter
    def dataDir(self, value):
        config.dataDir = str(value)

    def __getattr__(self, name):
        if name in ("chart", "table", "text"):
            import importlib

            mod = importlib.import_module(f"dartlab.tools.{name}")
            setattr(self, name, mod)
            return mod
        raise AttributeError(f"module 'dartlab' has no attribute {name!r}")


sys.modules[__name__].__class__ = _Module


__all__ = [
    "Company",
    "Dart",
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
    "network",
    "screen",
    "benchmark",
    "signal",
    "groupHealth",
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
]
