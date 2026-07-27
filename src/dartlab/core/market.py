"""시장 자동 감지. 종목코드/티커/회사명으로 KR/US 판별.

모든 엔진이 이 모듈을 SSOT로 사용한다.
market 파라미터 기본값이 "KR"인 곳에서 resolveMarket을 호출하면
알파벳 종목코드는 자동으로 US로 분기된다.

Usage::

    from dartlab.core.market import detectMarket, resolveMarket

    detectMarket("005930")   # "KR"
    detectMarket("0008Z0")   # "KR"  (KRX 영숫자 단축코드)
    detectMarket("INTC")     # "US"
    detectMarket("삼성전자")  # "KR"

    resolveMarket("INTC", "KR")    # "US" (알파벳 → 자동 감지)
    resolveMarket("005930", "KR")  # "KR" (KRX 단축코드 → 그대로)
    resolveMarket("0008Z0", "KR")  # "KR" (영숫자 코드도 KR)
    resolveMarket("INTC", "US")    # "US" (명시 → 그대로)
"""

from __future__ import annotations

import re

_HANGUL_RE = re.compile(r"[가-힣]")

# KRX 단축코드 6자리. 첫 자리는 항상 숫자, 나머지는 영숫자다.
# 순수 6자리 숫자(005930)가 다수지만 신형 발행분은 영문을 섞는다
# (에스엔시스 0008Z0 · 삼성에피스홀딩스 0126Z0 · SK우 03473K).
# 2026-07 기준 상장 2,873 종목 중 79 종목이 영숫자다.
# "알파벳 포함이면 US" 규칙만 있으면 이들이 전부 US 로 새므로 그 앞에서 걸러야 한다.
# US 티커는 숫자로 시작하지 않아 이 규칙과 충돌하지 않는다.
_KR_STOCK_CODE_RE = re.compile(r"^\d[0-9A-Z]{5}$")

# 자유 텍스트에서 종목코드를 뽑는 패턴 (사용자 질문·세션 기록 스캔용).
# 위 _KR_STOCK_CODE_RE 를 그대로 텍스트에 풀면 기간 문자열 "2026Q1" 이 6자 영숫자라
# 종목코드로 잡힌다. 그래서 기간 모양을 앞에서 배제하고, 양옆이 영숫자면(긴 토큰 일부,
# 예 날짜 "20260101") 매칭하지 않는다. 영문부는 KRX 표기대로 대문자만 인정한다.
KR_STOCK_CODE_TEXT_RE = re.compile(r"(?<![0-9A-Za-z])(?!\d{4}Q[1-4](?![0-9A-Za-z]))(\d[0-9A-Z]{5})(?![0-9A-Za-z])")


def normalizeKrCode(code: str) -> str:
    """KR 종목코드 표기 정규화. 공백 제거 + 대문자.

    Capabilities:
        KRX 영숫자 코드의 영문을 항상 대문자로 맞춰 조회 키를 일치시킨다.
    AIContext:
        panel/finance 파일명과 조인 키가 대문자 코드라 사용자 입력 "0008z0" 을 그대로
        쓰면 미스가 난다. 판정과 조회 직전에 통과시키는 L0 정규화다.
    Guide:
        isKrStockCode 로 판정하기 전, 그리고 코드로 파일이나 행을 찾기 전에 호출한다.
    When:
        사용자 입력이나 외부 텍스트에서 뽑은 코드를 내부 키로 바꿀 때.
    How:
        strip 후 upper 한다. 숫자만인 코드는 무변이라 기존 6자리 경로에 영향이 없다.

    Parameters
    ----------
    code : str
        종목코드 후보.

    Returns
    -------
    str
        정규화된 코드. None 이나 빈 값은 빈 문자열.
    Requires:
        code는 문자열 또는 None 호환 값이어야 한다.
    Raises:
        없음.
    Example:
        >>> normalizeKrCode(" 0008z0 ")
        '0008Z0'
        >>> normalizeKrCode("005930")
        '005930'
    SeeAlso:
        isKrStockCode: 정규화 후 모양 판정.
    """
    return str(code or "").strip().upper()


def isKrStockCode(code: str) -> bool:
    """KRX 단축코드 모양인지 판정. 숫자 선두 6자 영숫자.

    Capabilities:
        005930 같은 순수 숫자 코드와 0008Z0 같은 신형 영숫자 코드를 모두 KR 로 인정한다.
    AIContext:
        옛 6자리 숫자 전용 가정이 영숫자 코드를 US 티커로 흘려 보내 EDGAR 경로 404 를
        냈다. 코드 모양 판정이 필요한 자리는 정규식을 손수 쓰지 말고 이 함수를 부른다.
    Guide:
        "이 문자열이 KR 종목코드냐" 물음의 정본. 시장 분기는 detectMarket 을 쓴다.
    When:
        입력 검증, 필터, 조회 가드에서 코드 모양만 확인할 때.
    How:
        normalizeKrCode 로 맞춘 뒤 첫 자리 숫자 + 영숫자 6자 패턴에 맞춘다.

    Parameters
    ----------
    code : str
        종목코드 후보.

    Returns
    -------
    bool
        KRX 단축코드 모양이면 True.
    Requires:
        code는 문자열 또는 None 호환 값이어야 한다.
    Raises:
        없음.
    Example:
        >>> isKrStockCode("005930")
        True
        >>> isKrStockCode("0008Z0")
        True
        >>> isKrStockCode("AAPL")
        False
    SeeAlso:
        detectMarket: 코드나 회사명을 KR 또는 US 시장으로 분기.
    """
    return bool(_KR_STOCK_CODE_RE.match(normalizeKrCode(code)))


def detectMarket(code: str) -> str:
    """종목코드/티커/회사명 → "KR" | "US" 자동 감지.

    Capabilities:
        KRX 단축코드, 한글 회사명, 영문 티커를 구분해 KR/US 시장 코드를 반환한다.
    AIContext:
        Company, gather, scan 진입점이 사용자의 코드 문자열만 보고 provider를 고를 때
        참조하는 L0 시장 판별 함수다.
    Guide:
        명시 market 값이 있는 경우에는 resolveMarket을 쓰고, 순수 문자열 판별만 필요할
        때 이 함수를 직접 쓴다.
    When:
        public API가 "005930", "0008Z0", "INTC", "삼성전자" 같은 입력을 받았을 때.
    How:
        공백 제거 후 KRX 단축코드와 한글을 KR로, 그 밖의 알파벳 포함 문자열을 US로 분류한다.

    Parameters
    ----------
    code : str
        종목코드 ("005930"), 티커 ("INTC"), 또는 회사명 ("삼성전자").

    Returns
    -------
    str
        "KR" : KRX 단축코드(영숫자 포함) 또는 한글 포함.
        "US" : 그 밖의 알파벳 포함 (영문 티커).
    Requires:
        code는 문자열이어야 한다. 빈 문자열은 KR fallback으로 처리한다.
    Raises:
        AttributeError: code가 strip 메서드를 제공하지 않는 비문자 객체일 때.
    Example:
        >>> detectMarket("005930")
        'KR'
        >>> detectMarket("0008Z0")
        'KR'
        >>> detectMarket("INTC")
        'US'
    SeeAlso:
        resolveMarket: 명시 market 파라미터와 자동 감지를 함께 처리한다.
    """
    if not code:
        return "KR"
    stripped = code.strip()
    # KRX 단축코드 (6자리 숫자 또는 숫자 선두 영숫자) → KR.
    # 영숫자 코드(0008Z0)는 아래 "알파벳 포함 → US" 보다 반드시 먼저 걸러야 한다.
    if isKrStockCode(stripped):
        return "KR"
    # 한글 포함 → KR (회사명)
    if _HANGUL_RE.search(stripped):
        return "KR"
    # 알파벳 포함 → US
    if any(c.isalpha() for c in stripped):
        return "US"
    # 숫자만 (6자리 아닌) → KR fallback
    return "KR"


def resolveMarket(code: str, market: str = "auto") -> str:
    """market 파라미터 해석. 명시 값 우선, 아니면 자동 감지.

    Capabilities:
        사용자 market 인자와 code 기반 자동 감지를 합쳐 최종 KR/US 시장 코드를 정한다.
    AIContext:
        public surface가 기본 market을 KR처럼 보존하면서도 영문 티커를 US provider로
        보내기 위한 L0 routing guard다.
    Guide:
        provider 선택 직전에 호출한다. market="US"는 강제값이고, "auto" 또는 "KR"은
        code 형태를 다시 본다.
    When:
        Company, gather, scan, quant 계열 진입점에서 market 기본값을 해석할 때.
    How:
        market을 대문자로 정규화하고, US는 그대로 반환하며 AUTO/KR은 detectMarket으로
        위임한다.

    market="KR"(기본값)이어도 code가 알파벳이면 US로 자동 변경.
    market을 "US"로 명시했으면 그대로 유지.

    Parameters
    ----------
    code : str
        종목코드/티커/회사명.
    market : str
        "KR" | "US" | "auto". 기본 "auto".

    Returns
    -------
    str
        "KR" 또는 "US".
    Requires:
        code와 market은 문자열 또는 None 호환 값이어야 한다.
    Raises:
        AttributeError: code가 비어 있지 않지만 strip 메서드가 없는 객체일 때.
    Example:
        >>> resolveMarket("INTC", "KR")
        'US'
        >>> resolveMarket("005930", "KR")
        'KR'
    SeeAlso:
        detectMarket: code 단독 자동 감지.
    """
    if not code:
        return market.upper() if market and market.lower() != "auto" else "KR"

    upper = market.upper() if market else "KR"

    # 명시적으로 US를 지정했으면 그대로
    if upper == "US":
        return "US"

    # "auto" 또는 "KR"(기본값)인데 코드가 알파벳이면 자동 감지
    if upper in ("AUTO", "KR"):
        return detectMarket(code)

    return upper
