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
    """dartlab.verbose / dartlab.dataDir 프록시."""

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
    "search",
    "listing",
    "network",
    "screen",
    "benchmark",
    "signal",
    "groupHealth",
    "verbose",
    "dataDir",
    "getKindList",
    "codeToName",
    "nameToCode",
    "searchName",
    "fuzzySearch",
]
