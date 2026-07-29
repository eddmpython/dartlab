"""DART 대문자 공시 XML → 표준 소문자 HTML 정규화 + 셀 값 정합 정규화 (lxml 0, 순수).

DART raw 공시 XML 은 정부 대문자 태그 (``<TABLE><TR><TE>``, ``<TU>``=헤더) 를 쓴다. 브라우저
공시뷰어는 ``ui/packages/surfaces/src/viewer/lib/cell.ts::normalizeDartXml`` + ``DART_TAG_MAP``
으로 표준 소문자 HTML 로 재작성한 뒤 렌더한다. 본 모듈은 그 **표(table) 관련 부분집합의 Python
포팅** 이라, 엔진이 같은 표준 HTML 을 기존 격자기 ``cellGrid()``
(``providers/dart/parse/htmlTableParser.py``) 에 그대로 먹여 병합 보존 격자를 얻는다.

세 함수 모두 순수(no I/O, no dartlab import) — table-export 엔진·브라우저가 **동일 규칙**을
구현하고 같은 골든 픽스처(``tests/fixtures/xmlTables/*.grid.json``)로 양쪽 검증한다:

- ``normalizeDartXml(value)`` — 대문자 DART XML → 소문자 표준 HTML. ``colspan``/``rowspan``/
  ``align`` 속성 유지, ``ACODE``/``ACONTEXT`` 등 정부 메타 제거.
- ``coerceCell(text)`` — 셀 텍스트 → 타입값(int/float/str/None). 숫자/한국식 음수(괄호·삼각형)/
  결손(honest-gap, 0 금지) 규칙.
- ``detectUnit(caption)`` — "(단위: 백만원)" 형 캡션 → 단위 토큰 (스케일 환산 0 — xml-native-truth,
  미지 단위 → "").

LLM Specifications:
    AntiPatterns:
        - 단위 스케일로 값 환산 금지 — detectUnit 은 라벨만, coerceCell 은 원본 스케일 유지
          (feedback_xml_native_truth).
        - 결손 셀을 0 으로 치환 금지 — coerceCell("") is None (honest-gap).
        - lxml/zipfile/network import 금지 — 순수 정규식(콜드 0, 브라우저 패리티).
        - dartlab 패키지 import 금지 — 본 모듈은 엔진/브라우저 공유 leaf (역의존 0).
    OutputSchema:
        - ``normalizeDartXml(value: str) -> str`` (표준 소문자 HTML).
        - ``coerceCell(text: str) -> int | float | str | None``.
        - ``detectUnit(caption: str) -> str`` (단위 토큰 또는 "").
    Prerequisites:
        - re (표준 라이브러리). dartlab artifact 의존 0.
    Freshness:
        - 순수 변환 — 캐시 0, 부작용 0.
    Dataflow:
        - contentRaw(대문자 XML) → normalizeDartXml → cellGrid → coerceCell(셀별) → 타입값.
    TargetMarkets:
        - KR (DART 공시 XML). EDGAR 는 별도 경로(셀 분해 native).
"""

from __future__ import annotations

import re

# ── DART 대문자 XML → 표준 소문자 HTML 태그 맵 (DART_TAG_MAP 의 table 부분집합) ──
# cell.ts DART_TAG_MAP 미러. TU(헤더 셀) → th, TE(데이터 셀) → td. block/inline 태그
# (P/SPAN/TITLE/TABLE-GROUP) 는 div/span/br 로 — cellGrid 는 td/th/tr/table 구조만 읽으므로
# 무해, 단 임베디드 마크업이 raw 대문자로 새지 않도록 유지.
DART_TAG_MAP: dict[str, str] = {
    "TABLE-GROUP": "div",
    "TABLE": "table",
    "THEAD": "thead",
    "TBODY": "tbody",
    "TR": "tr",
    "TH": "th",
    "TU": "th",
    "TE": "td",
    "TD": "td",
    "P": "div",
    "SPAN": "span",
    "TITLE": "div",
    "BR": "br",
}

# 한 태그 매칭: 선행 슬래시(닫는태그), 태그명, 속성, self-close.
_TAG_RE = re.compile(r"<(/?)([A-Za-z][\w-]*)((?:\s[^>]*)?)\s*/?>")
# opening 태그에서 KEEP 할 구조 속성 (ACODE/ACONTEXT/USERMARK 등 제거).
_KEEP_ATTR_RE = re.compile(r"""\b(colspan|rowspan|align)\s*=\s*("[^"]*"|'[^']*'|\S+)""", re.IGNORECASE)


def normalizeDartXml(value: str) -> str:
    """대문자 DART 공시 XML → 표준 소문자 HTML (table 구조 부분집합).

    Capabilities:
        - 정부 대문자 태그(``<TABLE><TE><TU>``)를 ``cellGrid`` 가 읽는 표준 소문자
          HTML(``<table><td><th>``)로 변환 — colspan/rowspan/align 보존, 정부 메타 제거.

    cell.ts ``normalizeDartXml`` 포팅에서 브라우저 전용 USERMARK/class 렌더 부분만 뺀 것
    (cellGrid 는 ``table/tr/td/th`` + colspan/rowspan/align 만 필요). 각 태그명을
    ``DART_TAG_MAP`` (fallback = raw 태그 소문자)으로 재작성하고 opening 태그에서
    ``colspan``/``rowspan``/``align`` 만 유지. 그 외 정부 메타(ACODE, ACONTEXT, USERMARK,
    ADIM, ...)는 모두 제거.

    Args:
        value: raw DART XML 문자열 (``<TABLE>...</TABLE>`` 블록 포함 가능).

    Returns:
        ``cellGrid()`` 가 먹을 수 있는 표준 HTML 문자열. ``<`` 없는 문자열은 그대로 통과.

    Example:
        >>> normalizeDartXml('<TABLE><TR><TU COLSPAN="2" ACODE="x">H</TU></TR></TABLE>')
        '<table><tr><th colspan="2">H</th></tr></table>'

    Raises:
        없음 — 순수 정규식 치환. ``<`` 없는 입력은 즉시 원본 반환.

    Guide:
        - ``viz/export/excel.py::_writeGridSheet`` 가 wide 셀 raw XML 에 적용 후 cellGrid 호출.

    SeeAlso:
        - ``htmlTableParser.cellGrid`` — 정규화 결과를 병합 보존 격자로.
        - ``coerceCell`` — 격자 셀 텍스트를 타입값으로.

    Requires:
        - re (표준 라이브러리).

    AIContext:
        - 브라우저 cell.ts 와 1:1 패리티 — 같은 골든 픽스처(*.xml)로 양쪽 CI 검증.

    LLM Specifications:
        AntiPatterns:
            - lxml 파싱 금지 — 정규식 태그 치환(브라우저 패리티·콜드 0).
            - colspan/rowspan/align 외 속성 유지 금지 — 정부 메타 누출 차단.
        OutputSchema:
            - ``str`` (표준 소문자 HTML).
        Prerequisites:
            - re.
        Freshness:
            - 순수 변환.
        Dataflow:
            - raw XML → 태그별 DART_TAG_MAP 재작성 + KEEP 속성만 → 표준 HTML.
        TargetMarkets:
            - KR (DART).
    """
    if not value or "<" not in value:
        return value

    def _sub(m: "re.Match[str]") -> str:
        slash, tag, attrs = m.group(1), m.group(2), m.group(3)
        upper = tag.upper()
        name = DART_TAG_MAP.get(upper, tag.lower())
        keep = ""
        if not slash and attrs:
            am = _KEEP_ATTR_RE.findall(attrs)
            if am:
                # findall 은 (attr, value) 튜플 — 소문자 정규화해 재조립.
                keep = "".join(f" {a.lower()}={v}" for a, v in am)
        return f"<{slash}{name}{keep}>"

    return _TAG_RE.sub(_sub, value)


def detectUnit(caption: str) -> str:
    """단위 캡션("(단위: 백만원)") 감지 → 단위 토큰 반환, 환산 0.

    Capabilities:
        - 표 인접 캡션 텍스트의 "(단위: …)" 조각을 알아내 단위 문자열만 반환 — 값 스케일은
          건드리지 않는다(시트 상단 라벨용).

    PRD §5 + xml-native-truth: 엔진은 값을 단위 스케일로 곱하지 않는다. 단위 문자열만 표면화해
    export 시트가 라벨할 수 있게 한다. 미지/부재 단위 → 빈 문자열(honest-gap, 스케일 추측 0).

    Args:
        caption: "(단위: …)" 조각을 포함할 수 있는 임의 텍스트.

    Returns:
        canonical 단위 토큰(예 "백만원", "원", "%") 또는 인식 실패 시 "".

    Example:
        >>> detectUnit("(단위: 백만원)")
        '백만원'
        >>> detectUnit("매출액 추이")
        ''

    Raises:
        없음 — 순수 정규식 검색. 부재/미지 단위는 "" 로 흡수.

    Guide:
        - ``_writeGridSheet`` 가 표 캡션/선행 문단에서 단위를 뽑아 시트 1행 라벨로.

    SeeAlso:
        - ``coerceCell`` — 값은 원본 스케일 유지(단위로 환산 금지).

    Requires:
        - re.

    AIContext:
        - 단위는 셀 안이 아니라 표 인접 캡션 텍스트에 산다(브라우저 absorbCaptionUnitFromText 대응).

    LLM Specifications:
        AntiPatterns:
            - 단위 스케일로 값 환산 금지 — 라벨만(feedback_xml_native_truth).
            - 미지 단위 추측 금지 — "" 반환(honest-gap).
        OutputSchema:
            - ``str`` (단위 토큰 또는 "").
        Prerequisites:
            - re.
        Freshness:
            - 순수 변환.
        Dataflow:
            - caption → 단위 정규식 → KNOWN_UNITS 검증 → 토큰 또는 "".
        TargetMarkets:
            - KR (한국 회계 단위).
    """
    from dartlab.providers.dart.parse.amount import detectUnitLabel

    return detectUnitLabel(caption) or ""


# ── 셀 값 정합 정규화 (PRD §5) ──
_NUMERIC_RE = re.compile(r"^-?[\d,]+(\.\d+)?$")
# 한국식 음수 래퍼: (1,234) 괄호음수 ; △ / ▲ 삼각형 접두.
_PAREN_NEG_RE = re.compile(r"^\(\s*([\d,]+(?:\.\d+)?)\s*\)$")
_TRIANGLE_NEG_RE = re.compile(r"^[△▲]\s*([\d,]+(?:\.\d+)?)$")


def _toNumber(digits: str) -> int | float:
    """콤마 제거 숫자 토큰을 int(점 없음) 또는 float(점 있음)로 파싱."""
    cleaned = digits.replace(",", "")
    if "." in cleaned:
        return float(cleaned)
    return int(cleaned)


def coerceCell(text: str) -> int | float | str | None:
    """표 셀 문자열을 타입값으로 정합 정규화 (PRD §5).

    Capabilities:
        - 콤마 그룹 숫자·한국식 음수(괄호·삼각형)를 Number 로, 결손을 None(0 아님)으로,
          그 외는 원본 문자열로 — "바로 엑셀 계산 가능" 임계 충족.

    규칙 (정확):
      - ``-?[\\d,]+(\\.\\d+)?`` (콤마 제거 후) → int / float. "1,234" → 1234(int), 문자열 아님.
        콤마는 표시용일 뿐 값에 안 넣는다.
      - 한국식 음수: "(1,234)" → -1234 ; "△1,234" 또는 "▲1234" → -1234.
      - 빈/공백뿐 → None (honest-gap — 결손을 **절대 0 으로** 안 만든다).
      - 그 외(한글 텍스트·혼합) → 원본 문자열(trim).

    Args:
        text: raw 셀 텍스트.

    Returns:
        int | float | str | None.

    Example:
        >>> coerceCell("1,234")
        1234
        >>> coerceCell("(1,234)")
        -1234
        >>> coerceCell("△1,234.5")
        -1234.5
        >>> coerceCell("") is None
        True
        >>> coerceCell("삼성전자")
        '삼성전자'

    Raises:
        없음 — None/빈 입력은 None, 비숫자는 문자열로 흡수.

    Guide:
        - ``_writeGridSheet`` 가 각 격자 셀에 적용 — Number 면 openpyxl 숫자 셀, 그 외 문자열.

    SeeAlso:
        - ``detectUnit`` — 단위는 별도(값 환산 금지).
        - ``normalizeDartXml`` — 셀 텍스트의 출처 격자.

    Requires:
        - re.

    AIContext:
        - 줄바꿈 낀 삼각형 음수("△\\n1,202,857")도 ``\\s*`` 로 흡수 — 실데이터 존재.

    LLM Specifications:
        AntiPatterns:
            - 결손을 0 으로 치환 금지 — None(honest-gap).
            - 단위 접미 숫자("5,000원")를 1234 로 벗기기 금지 — 문자열 유지(의도적 정직).
        OutputSchema:
            - ``int | float | str | None``.
        Prerequisites:
            - re.
        Freshness:
            - 순수 변환.
        Dataflow:
            - text → 괄호/삼각형 음수 → 평문 숫자 → 그 외 문자열/None.
        TargetMarkets:
            - KR (한국 공시 음수·콤마 규약).
    """
    if text is None:
        return None
    s = text.strip()
    if not s:
        return None

    # 한국식 괄호음수: (1,234) → -1234
    pm = _PAREN_NEG_RE.match(s)
    if pm:
        return -_toNumber(pm.group(1))

    # 한국식 삼각형음수: △1,234 / ▲1234 → -1234
    tm = _TRIANGLE_NEG_RE.match(s)
    if tm:
        return -_toNumber(tm.group(1))

    # 평문 숫자 (선행 "-" 포함).
    if _NUMERIC_RE.match(s):
        # 가드: 단독 "-" 또는 "," 는 숫자 아님.
        if s.strip("-,. ") == "":
            return s
        return _toNumber(s)

    # 비숫자 텍스트 → 문자열 유지.
    return s
