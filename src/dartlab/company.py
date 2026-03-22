"""루트 Company facade."""

from __future__ import annotations

import re

from dartlab.engines.common.protocols import CompanyProtocol
from dartlab.engines.company.dart.company import Company as _DartEngineCompany
from dartlab.engines.company.edgar.company import Company as _EdgarEngineCompany


def _isUSTicker(s: str) -> bool:
    """미국 ticker 형식 판별 (영문 대문자 1~5자리)."""
    return bool(re.match(r"^[A-Za-z]{1,5}$", s))


def _isDartCode(s: str) -> bool:
    """DART 종목코드 형식 판별 (숫자/영문 포함 6자리)."""
    return bool(re.match(r"^[0-9A-Za-z]{6}$", s))


def Company(codeOrName: str) -> CompanyProtocol:
    """종목코드/회사명/ticker → 적절한 Company 인스턴스 생성."""
    from dartlab.core.plugins import discover

    discover()  # 최초 1회만 실행, 이후 즉시 반환

    normalized = codeOrName.strip()
    if not normalized:
        raise ValueError("종목코드 또는 회사명을 입력해 주세요.")

    try:
        if _isDartCode(normalized):
            return _DartEngineCompany(normalized.upper())

        if any("\uac00" <= ch <= "\ud7a3" for ch in normalized):
            return _DartEngineCompany(normalized)

        if _isUSTicker(normalized):
            return _EdgarEngineCompany(normalized)

        return _DartEngineCompany(normalized)
    except (ValueError, FileNotFoundError, OSError) as exc:
        raise ValueError(
            f"'{codeOrName}'을(를) 찾을 수 없습니다. dartlab.search('{codeOrName}')로 검색해 보세요."
        ) from exc
