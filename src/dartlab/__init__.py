"""DART 공시 데이터 활용 라이브러리."""

import sys
from importlib.metadata import version as _pkg_version

try:
    __version__ = _pkg_version("dartlab")
except Exception:
    __version__ = "0.0.0"

from dartlab import config, core, engines
from dartlab.company import Company
from dartlab.compare import Compare
from dartlab.core.kindList import codeToName, getKindList, nameToCode, searchName
from dartlab.engines.dart.company import Company as _DartCompany
from dartlab.engines import ai as llm
from dartlab.engines.edgar.company import Company as _EdgarCompany


def search(keyword: str):
    """종목 검색 (KR + US 통합).

    Example::

        import dartlab
        dartlab.search("삼성전자")
        dartlab.search("AAPL")
    """
    if any("\uac00" <= ch <= "\ud7a3" for ch in keyword):
        return _DartCompany.search(keyword)
    if keyword.isascii() and keyword.isalpha():
        try:
            from dartlab.engines.edgar.company import Company as _US
            return _US.search(keyword)
        except (ImportError, AttributeError, NotImplementedError):
            pass
    return _DartCompany.search(keyword)


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
    return _DartCompany.listing()


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
    "Compare",
    "config",
    "core",
    "engines",
    "llm",
    "search",
    "listing",
    "verbose",
    "dataDir",
    "getKindList",
    "codeToName",
    "nameToCode",
    "searchName",
]
