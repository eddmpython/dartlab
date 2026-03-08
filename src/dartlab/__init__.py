"""DART 공시 데이터 활용 라이브러리."""

import sys

from dartlab import config, core, engines
from dartlab.company import Company
from dartlab.core.kindList import codeToName, getKindList, nameToCode, searchName


class _Module(sys.modules[__name__].__class__):
    """dartlab.verbose 프록시."""

    @property
    def verbose(self):
        return config.verbose

    @verbose.setter
    def verbose(self, value):
        config.verbose = value


sys.modules[__name__].__class__ = _Module


__all__ = [
    "config",
    "core",
    "engines",
    "Company",
    "verbose",
    "getKindList",
    "codeToName",
    "nameToCode",
    "searchName",
]
