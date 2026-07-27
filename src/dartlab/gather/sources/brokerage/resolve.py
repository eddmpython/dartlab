"""제목 → 종목코드 해소 — 명시 6자리 코드 우선 + corpCode 상장사명 fallback.

1차: 제목 내 '(005930/매수)' 같은 명시 6자리 코드 정규식 추출 (의존성 0·오탐 0).
2차: corpCode 상장사명 최장 매칭 (DART_API_KEY 필요 — 실패 시 graceful skip).
산업·시황 리포트는 회사 없어 None — 0-fill 금지, None first-class.
"""

from __future__ import annotations

import re
from functools import lru_cache

from dartlab.core.logger import getLogger

_log = getLogger(__name__)

# KRX 단축코드 (6자리 숫자 또는 숫자 선두 영숫자, 예 0008Z0).
_CODE_RE = re.compile(r"\((\d[0-9A-Z]{5})[/)\s]")

# 투자의견 화이트리스트 — '(코드/의견)' 패턴의 의견부만(날짜 '(6/29)' 등 오탐 차단).
_OPINION_RE = re.compile(
    r"\([^()]*/\s*(매수|매도|중립|보유|비중확대|비중축소|적정|"
    r"Not\s*Rated|N\.?R\.?|Buy|Sell|Hold|Outperform|Marketperform|Underperform|Overweight|Underweight)"
    r"\s*\)",
    re.IGNORECASE,
)


@lru_cache(maxsize=1)
def _listedPairs() -> tuple[tuple[str, str], ...]:
    """상장사 (회사명, 종목코드) 튜플 — 이름 길이 내림차순. corpCode 실패 시 빈 튜플(graceful).

    Returns:
        tuple — (corp_name, stock_code) 들, 이름 길이 desc. corpCode 로드 실패 시 ().

    Example::

        _listedPairs()[:1]   # 최장 회사명부터
    """
    try:
        import polars as pl

        from dartlab.gather.dart import corpCode

        client = corpCode.DartClient()
        df = corpCode.loadCorpCodes(client)
        listed = df.filter(pl.col("stock_code").str.strip_chars().str.len_chars() == 6)
        pairs = [
            (r["corp_name"].strip(), r["stock_code"].strip()) for r in listed.iter_rows(named=True) if r["corp_name"]
        ]
        pairs.sort(key=lambda x: len(x[0]), reverse=True)
        return tuple(pairs)
    except Exception as exc:  # noqa: BLE001
        # 키나 네트워크가 없으면 명시코드 경로만 쓴다. 흐름은 그대로 두고 원인만 남긴다.
        _log.warning("상장 종목 쌍 조회 실패로 빈 결과 반환: %s: %s", type(exc).__name__, exc)
        return ()


def _resolveTicker(title: str, *, minLen: int = 3, useNameMatch: bool = True) -> str | None:
    """제목 → 종목코드. 명시 6자리 코드 우선, 없으면 최장 상장사명 매칭(graceful).

    Args:
        title: 리포트 제목.
        minLen: 이름 매칭 최소 회사명 길이 (오탐 억제, 기본 3).
        useNameMatch: False 면 명시 코드만 사용 (corpCode 로드 회피).

    Returns:
        str | None — 6자리 종목코드. 회사 없으면/외국주식이면 None.

    Example::

        _resolveTicker("삼성전자 (005930/매수) ...")   # '005930'
        _resolveTicker("◆ Daily 시황 ◆")               # None
    """
    if not title:
        return None
    m = _CODE_RE.search(title)
    if m:
        return m.group(1)
    if not useNameMatch:
        return None
    for name, code in _listedPairs():
        if len(name) >= minLen and name in title:
            return code
    return None


def _extractOpinion(title: str) -> str | None:
    """제목의 '(코드/의견)' 패턴에서 투자의견만 추출(화이트리스트). 없으면 None.

    Args:
        title: 리포트 제목.

    Returns:
        str | None — '매수'·'Not Rated' 등 정규화 의견. 패턴/화이트리스트 불일치 시 None.

    Example::

        _extractOpinion("삼성전자 (005930/매수) ...")   # '매수'
        _extractOpinion("◆ 시황 (6/29~7/3) ◆")          # None
    """
    if not title:
        return None
    m = _OPINION_RE.search(title)
    return m.group(1).strip() if m else None
