"""루트 Company facade."""

from __future__ import annotations

import re

from dartlab.engines.dart.company import Company as _DartCompany
from dartlab.engines.edgar.company import Company as _EdgarCompany


def _isUSTicker(s: str) -> bool:
    """미국 ticker 형식 판별 (영문 대문자 1~5자리)."""
    return bool(re.match(r"^[A-Za-z]{1,5}$", s))


def Company(codeOrName: str):
    """종목코드/회사명/ticker → 적절한 Company 인스턴스 생성."""
    if re.match(r"^\d{6}$", codeOrName):
        return _DartCompany(codeOrName)

    if any("\uac00" <= ch <= "\ud7a3" for ch in codeOrName):
        return _DartCompany(codeOrName)

    if _isUSTicker(codeOrName):
        return _EdgarCompany(codeOrName)

    return _DartCompany(codeOrName)
