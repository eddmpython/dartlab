"""DART 공시 데이터 활용 라이브러리."""

import sys

from dartlab import config, core, engines
from dartlab.company import Company
from dartlab.core.kindList import codeToName, getKindList, nameToCode, searchName
from dartlab.engines import llmAnalyzer as llm


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
    "verbose",
    "dataDir",
    "getKindList",
    "codeToName",
    "nameToCode",
    "searchName",
]
