"""KRX 거래소 수시공시 본문 → 구조화 — *선언 레지스트리* 구동 파서.

KRX 거래소공시(공시유형 "I", 예 단일판매·공급계약체결)는 OpenDART 구조화 엔드포인트가 *없다* —
본문 HTML 만 존재한다. 따라서 ``gather/dart/dart.py::_REPORT_ENDPOINTS`` (구조화 JSON API) 에는
흡수 불가. 대신 KRX 양식은 회사·섹터 불문 *라벨 고정* key-value 표(채워넣기 폼)라, 유형별 파서를
손코딩하지 않고 **라벨패턴 → (필드명, 타입)** 선언 1 엔트리로 끝낸다 (덕지덕지 차단).

선례 = ``sectionTopic.py::_PATTERN_MAPPINGS`` (정규식→topic 레지스트리). 본 모듈은 그 동형의
*수시공시유형* 판. 기계적 HTML 셀 추출은 공통 ``parse.htmlTableParser.flattenTableCells`` (lxml) 에,
값 정규화는 공통 ``_common.tableParser.parseAmount`` 에 위임 — 계약 전용 추출/정규화 코드 0.

확장: 새 수시공시 유형(타법인주식취득결정·유형자산취득 등)은 ``EVENT_SCHEMAS`` 엔트리 1 개. 새 모듈·
imperative 분기 금지. 전 상장사 횡단 소비는 :func:`dartlab.scan.orders.scanOrders`.
"""

from __future__ import annotations

import re

from dartlab.providers._common.tableParser import parseAmount
from dartlab.providers.dart.parse.htmlTableParser import flattenTableCells, parseHtmlTables

# 값 타입: amount(원, parseAmount 위임) / pct(%) / text / date(YYYY-MM-DD) / range(시작·종료 쌍).
EVENT_SCHEMAS: dict[str, dict] = {
    "supplyContract": {
        "label": "단일판매·공급계약",
        "reportMatch": r"단일판매.?공급계약체결",
        "cancelMatch": r"단일판매.?공급계약해지",
        "amendMarker": r"\[기재정정\]",
        "fields": {
            r"계약금액": ("contractAmount", "amount"),
            r"최근\s*매출액": ("recentRevenue", "amount"),
            r"매출액\s*대비": ("revenueRatio", "pct"),
            r"계약상대": ("counterparty", "text"),
            r"판매.?공급지역|공급지역": ("region", "text"),
            r"계약\s*기간": ("contractPeriod", "range"),
            r"계약.?수주.?일|계약일자|체결일": ("orderDate", "date"),
        },
    },
}

_RE_CLEAN_NUM = re.compile(r"^-?[\d,]+(?:\.\d+)?$")
_RE_DATE = re.compile(r"(\d{4})[-./년]\s*(\d{1,2})[-./월]\s*(\d{1,2})")
# 값-정합: contractAmount/recentRevenue*100 이 revenueRatio 와 이 배수 이상 어긋나면 오파싱 의심.
_SANITY_TOLERANCE = 5.0


def eventSchema(eventType: str) -> dict:
    """eventType → 스키마 dict. 미등록 시 KeyError (조용한 폴백 금지).

    Args:
        eventType: ``EVENT_SCHEMAS`` 키 (예 ``"supplyContract"``).

    Returns:
        dict — 해당 유형 스키마 (label/reportMatch/fields 등).

    Raises:
        KeyError: 미등록 유형.

    Example:
        >>> eventSchema("supplyContract")["label"]
        '단일판매·공급계약'
    """
    return EVENT_SCHEMAS[eventType]


def expectedFields(eventType: str) -> list[str]:
    """해당 유형이 추출하는 필드명 목록 (파싱 성공률 분모).

    Args:
        eventType: ``EVENT_SCHEMAS`` 키.

    Returns:
        list[str] — 필드명 (예 ``["contractAmount", "recentRevenue", ...]``).

    Raises:
        KeyError: 미등록 유형.

    Example:
        >>> "contractAmount" in expectedFields("supplyContract")
        True
    """
    return [field for (field, _kind) in EVENT_SCHEMAS[eventType]["fields"].values()]


def _normDate(s: str) -> str | None:
    m = _RE_DATE.search(s or "")
    if not m:
        return None
    y, mo, d = m.groups()
    return f"{int(y):04d}-{int(mo):02d}-{int(d):02d}"


def _cleanAmount(raw: str | None) -> float | None:
    """단일 숫자 셀만 → parseAmount(공통). 병합·라벨혼입 셀은 None.

    병합 '계약내역' 셀(``'- X - X - 14.34'``)을 parseAmount 가 숫자 concatenation 해
    천문학적 garbage 로 만드는 회귀 차단 (전수 실측 발견).

    Args:
        raw: cell text.

    Returns:
        float(원) 또는 None.

    Raises:
        없음.

    Example:
        >>> _cleanAmount("1,234")
        1234.0
        >>> _cleanAmount("- 48,427,000,000 - 48,427,000,000 - 14.34") is None
        True
    """
    s = (raw or "").strip()
    return parseAmount(s) if _RE_CLEAN_NUM.match(s) else None


def _cleanPct(raw: str | None) -> float | None:
    s = (raw or "").strip()
    return float(s.replace(",", "")) if _RE_CLEAN_NUM.match(s) else None


def _nextValue(cells: list[str], idx: int, labelPat: re.Pattern[str]) -> str | None:
    for j in range(idx + 1, min(idx + 4, len(cells))):
        cand = cells[j]
        if cand and not labelPat.search(cand):
            return cand
    return None


def _extractField(cells: list[str], labelPatStr: str, kind: str) -> object | None:
    labelPat = re.compile(labelPatStr)
    if kind == "range":
        # 계약기간: 라벨 인접 윈도우(8셀)에서 날짜 수집 → 첫=시작, 끝=종료.
        for i, cell in enumerate(cells):
            if not labelPat.search(cell):
                continue
            dates = [d for d in (_normDate(w) for w in cells[i : i + 8]) if d]
            if dates:
                return {"start": dates[0], "end": dates[-1] if len(dates) > 1 else None}
        return None

    if kind in ("amount", "pct"):
        # 라벨 매칭 셀 순회 — '총액'/'(원)'/'%' canonical 라벨 우선, 깨끗한 단일 숫자만 채택.
        best = None
        for i, cell in enumerate(cells):
            if not labelPat.search(cell):
                continue
            val = (
                _cleanAmount(_nextValue(cells, i, labelPat))
                if kind == "amount"
                else _cleanPct(_nextValue(cells, i, labelPat))
            )
            if val is None:
                continue
            if ("총액" in cell) or ("원" in cell) or ("%" in cell):
                return val
            if best is None:
                best = val
        return best

    for i, cell in enumerate(cells):
        if not labelPat.search(cell):
            continue
        raw = _nextValue(cells, i, labelPat)
        if raw is None:
            continue
        if kind == "date":
            return _normDate(raw)
        return raw  # text
    return None


def _applySanity(row: dict) -> dict:
    """값-정합 가드 — 공시 self-redundancy(계약금액/최근매출 ≈ 매출액대비%) 교차검증.

    contractAmount·recentRevenue·revenueRatio 가 모두 있고 함의 비율이 신고 비율과
    배수(``_SANITY_TOLERANCE``) 이상 어긋나면 contractAmount 오파싱으로 보고 None 처리 +
    ``amountSuspect`` 플래그.
    """
    amt, rev, ratio = row.get("contractAmount"), row.get("recentRevenue"), row.get("revenueRatio")
    if amt and rev and ratio and rev > 0 and ratio > 0:
        implied = amt / rev * 100.0
        rel = implied / ratio
        if rel > _SANITY_TOLERANCE or rel < 1.0 / _SANITY_TOLERANCE:
            row["contractAmount"] = None
            row["amountSuspect"] = True
    return row


def parseEventDisclosure(html: str, eventType: str = "supplyContract") -> dict:
    """KRX 수시공시 본문 HTML → 구조화 필드 dict. 레지스트리 선언만으로 구동.

    계층: 기계적 셀 추출은 ``flattenTableCells`` (lxml, 다중 표), 값 정규화는 공통
    ``parseAmount``. 라벨→값 인접 매핑은 ``EVENT_SCHEMAS`` 선언. 마지막에 self-redundancy
    값-정합 가드 적용.

    Args:
        html: 공시 본문 HTML (``Company.readFiling(rcept)["text"]`` 또는 allFilings
            ``content_raw``).
        eventType: ``EVENT_SCHEMAS`` 키 (기본 ``"supplyContract"``).

    Returns:
        dict — 스키마 필드 + ``amountSuspect`` (값-정합 위반 시 True). 미발견 필드는 None.
        ``contractPeriod`` 는 ``{"start", "end"}`` dict.

    Raises:
        KeyError: 미등록 eventType.

    Example:
        >>> html = '<table><tr><td>계약금액 총액(원)</td><td>100</td></tr></table>'
        >>> parseEventDisclosure(html)["contractAmount"]
        100.0

    Capabilities:
        - 단일 공시 본문 → 계약금액/최근매출/매출대비%/계약상대/지역/계약기간/수주일 추출.
        - 병합 셀 concatenation garbage 차단(깨끗한 단일 숫자만) + 값-정합 교차검증.

    Guide:
        - 전 상장사 횡단은 본 함수 직접 호출 말고 :func:`dartlab.scan.orders.scanOrders` 사용.

    SeeAlso:
        - :func:`classifyEventReport` — report_nm → 체결/해지/정정 분류.
        - :func:`dartlab.scan.orders.scanOrders` — 전수 횡단 (book-to-bill).

    Requires:
        - ``flattenTableCells`` (lxml) · ``parseAmount``.

    AIContext:
        Agent 는 단건 계약 상세가 필요할 때만 본 함수 사용. 후보 발굴·랭킹은 scan("orders").

    LLM Specifications:
        AntiPatterns:
            - 전 상장사 루프에 본 함수 직접 호출 (scan("orders") 가 전수 오케스트레이션).
            - amountSuspect=True row 의 contractAmount 를 신뢰 (값-정합 위반).
        OutputSchema:
            - dict: contractAmount(float|None) / recentRevenue / revenueRatio / counterparty /
              region / contractPeriod(dict) / orderDate(str) / amountSuspect(bool, optional).
        Prerequisites:
            - 본문 HTML (allFilings content_raw 또는 readFiling).
        Freshness:
            - 공시 시점 (수시공시).
        Dataflow:
            - html → flattenTableCells → 라벨→값 매핑 → 값-정합 → dict.
        TargetMarkets:
            - KR (DART/KRX 거래소공시).
    """
    schema = EVENT_SCHEMAS[eventType]
    cells = flattenTableCells(html)
    row: dict[str, object | None] = {}
    for labelPatStr, (field, kind) in schema["fields"].items():
        row[field] = _extractField(cells, labelPatStr, kind)
    return _applySanity(row)


def classifyEventReport(reportName: str, eventType: str = "supplyContract") -> str:
    """공시명(report_nm) → ``'contract'``(체결) / ``'cancel'``(해지) / ``'amend'``(정정) / ``'other'``.

    Args:
        reportName: DART report_nm (예 ``"단일판매ㆍ공급계약체결"``).
        eventType: ``EVENT_SCHEMAS`` 키.

    Returns:
        str — 분류 라벨. 신규수주 inflow 는 ``'contract'``/``'amend'``, ``'cancel'`` 은 차감.

    Raises:
        KeyError: 미등록 eventType.

    Example:
        >>> classifyEventReport("[기재정정]단일판매ㆍ공급계약체결")
        'amend'
        >>> classifyEventReport("단일판매ㆍ공급계약해지")
        'cancel'
    """
    schema = EVENT_SCHEMAS[eventType]
    nm = (reportName or "").strip()
    if re.search(schema.get("amendMarker", r"\[기재정정\]"), nm):
        return "amend"
    if "cancelMatch" in schema and re.search(schema["cancelMatch"], nm):
        return "cancel"
    if re.search(schema["reportMatch"], nm):
        return "contract"
    return "other"


# ── 잠정실적 (영업(잠정)실적 공정공시 + 매출액/손익구조 변동) 실적 행렬표 파서 ──
# eventDisclosure 의 key-value 폼(공급계약 등)과 달리 잠정실적은 계정 x 기간 *행렬표*라
# flattenTableCells(행 경계 소실)로는 못 뽑는다. 공통 parseHtmlTables(행 보존)로 당해실적
# 행을 잡아 current + YoY(영업잠정=전년동기대비, 손익구조=증감비율)를 추출한다. 새 모듈 0.
_FLASH_REPORT_RE = re.compile(r"영업\(잠정\)실적|매출액또는손익구조")
_FLASH_EXCLUDE_RE = re.compile(r"전망|예고|안내|정정신고서제출요구")
# 표 라벨(선행 '-'·공백 제거 후) 을 canonical 계정으로.
_FLASH_ACCOUNTS = {
    "매출액": "revenue",
    "영업이익": "operatingProfit",
    "당기순이익": "netProfit",
    "반기순이익": "netProfit",
    "분기순이익": "netProfit",
    "법인세비용차감전계속사업이익": "pretaxProfit",
}
# 표 헤더 "단위 : 백만원, %" / "단위:천원" 을 원 환산 배수로.
_FLASH_UNIT_WON = {"천원": 1e3, "백만원": 1e6, "십억원": 1e9, "억원": 1e8, "조원": 1e12, "원": 1.0}
_FLASH_UNIT_RE = re.compile(r"단위\s*[:：]\s*([가-힣]+원)")


def classifyEarningsFlash(reportName: str) -> dict:
    """공시명(report_nm) 을 잠정실적 판별 + 유형/기준으로. 숫자 없는 전망/예고/안내는 제외.

    Args:
        reportName: DART report_nm.

    Returns:
        dict. ``{"isFlash": bool, "type": str|None, "basis": str|None}``. type 은
        ``"영업잠정실적"`` 또는 ``"손익구조변동"``, basis 는 ``"연결"``/``"별도"``.

    Raises:
        없음.

    Example:
        >>> classifyEarningsFlash("연결재무제표기준영업(잠정)실적(공정공시)")
        {'isFlash': True, 'type': '영업잠정실적', 'basis': '연결'}
        >>> classifyEarningsFlash("영업(잠정)실적등에대한전망(공정공시)")["isFlash"]
        False
    """
    nm = (reportName or "").strip()
    if not _FLASH_REPORT_RE.search(nm) or _FLASH_EXCLUDE_RE.search(nm):
        return {"isFlash": False, "type": None, "basis": None}
    typ = "손익구조변동" if "매출액또는손익구조" in nm else "영업잠정실적"
    basis = "연결" if "연결" in nm else "별도"
    return {"isFlash": True, "type": typ, "basis": basis}


def _flashLabel(cell: str) -> str:
    return re.sub(r"^[-\s]+", "", cell or "").strip()


def _flashNum(cell: str) -> float | None:
    """실적 셀 을 부호 보존 float 로. 대시/빈칸은 None, 괄호는 음수(회계 관행).

    ``parseAmount`` 는 계약금액(항상 양수)용이라 선행 ``-`` 부호를 버린다. 잠정실적은
    영업손실 등 음수가 있어 손실을 이익으로 뒤집으면 안 되므로 별도 파서를 쓴다.
    """
    s = (cell or "").strip()
    if s in ("", "-"):
        return None
    paren = s.startswith("(") and s.endswith(")")
    body = s.strip("()")
    if not _RE_CLEAN_NUM.match(body):
        return None
    v = float(body.replace(",", ""))
    return -v if paren else v


def _flashUnitWon(text: str) -> tuple[str, float]:
    m = _FLASH_UNIT_RE.search(text or "")
    unit = m.group(1) if m else "원"
    return unit, _FLASH_UNIT_WON.get(unit, 1.0)


def parseEarningsFlash(html: str, reportName: str) -> dict:
    """잠정실적 본문 을 계정별 당기 실적 + 전년동기(또는 직전연도) 증감율로.

    영업(잠정)실적 공정공시와 매출액/손익구조 변동 공시 두 유형 모두 처리한다. 계정 x
    기간 행렬표라 공통 ``parseHtmlTables`` (행 보존, lxml) 로 실적표(매출액+영업이익 포함
    표)를 찾아, 유형별 컬럼 매핑으로 값을 뽑는다. 숫자를 대시(``-``)로만 낸 공시는 해당
    계정을 건너뛴다(조용한 오파싱 대신 부재 노출).

    유형별 컬럼(빈 셀 제거 후):
        - 영업잠정실적: ``[매출액, 당해실적, 당기, 전기, 전기대비%, 흑자적자, 전년동기,
          전년동기대비%, ...]`` 로 current=idx2, yoyPct(전년동기대비)=idx7.
        - 손익구조변동: ``[- 매출액, 당해연도, 직전연도, 증감금액, 증감비율%, ...]`` 로
          current=idx1, yoyPct(증감비율)=idx4.

    Args:
        html: 공시 본문 HTML/XML (allFilings ``content_raw`` 또는 ``document.xml``).
        reportName: DART report_nm (유형 분기용).

    Returns:
        dict. ``{"type", "basis", "unit", "unitWon", "accounts"}``. accounts 는
        ``{canonical: {"current": float, "yoyPct": float|None}}`` (canonical =
        revenue/operatingProfit/netProfit/pretaxProfit). current 는 표 단위 그대로이고
        원 환산은 ``current * unitWon``. 실적표 부재/전부 대시면 accounts 는 빈 dict.

    Raises:
        없음. parse 실패는 빈 accounts 로 흡수.

    Example:
        >>> html = ('<table><tr><td>구분</td></tr>'
        ...   '<tr><td>매출액</td><td>당해실적</td><td>50,902</td><td>83,014</td>'
        ...   '<td>-38.7</td><td>-</td><td>147,392</td><td>-65.5</td><td>-</td></tr>'
        ...   '<tr><td>영업이익</td><td>당해실적</td><td>8,456</td><td>1</td><td>2</td>'
        ...   '<td>-</td><td>3</td><td>-87.9</td><td>-</td></tr>'
        ...   '<td>단위 : 백만원</td></table>')
        >>> r = parseEarningsFlash(html, "연결재무제표기준영업(잠정)실적(공정공시)")
        >>> r["accounts"]["revenue"]
        {'current': 50902.0, 'yoyPct': -65.5}

    Capabilities:
        - 두 잠정실적 유형 실적표 를 매출·영업이익·순이익·세전이익 당기값 + 증감율로.
        - 표 헤더 단위(백만원/억원/천원) 파싱 후 원 환산 배수 동반 반환.

    Guide:
        - 전 상장사 횡단·원 환산·알림은 :func:`dartlab.scan.earningsFlash.scanEarningsFlash`.

    SeeAlso:
        - :func:`classifyEarningsFlash`. report_nm 판별.
        - :func:`parseEventDisclosure`. 동 모듈 key-value 수시공시 파서.
        - :func:`dartlab.scan.earningsFlash.scanEarningsFlash`. 전수 횡단 소비.

    Requires:
        - ``parseHtmlTables`` (lxml) · ``parseAmount``.

    AIContext:
        Agent 는 단건 잠정실적 상세가 필요할 때만 본 함수. 후보 발굴·랭킹은 scan("earningsFlash").

    When:
        잠정실적 공시 본문에서 구조화 실적을 뽑을 때 (왓처 알림·단건 조회).

    How:
        ``parseHtmlTables`` 로 매출액+영업이익 표 선택 후 당해실적 행 컬럼 매핑 후
        ``parseAmount``/pct 로 계정 dict.

    LLM Specifications:
        AntiPatterns:
            - 대시(``-``)만 낸 공시의 값을 0 으로 오해 (accounts 에서 아예 빠짐).
            - unit 무시하고 current 를 원으로 취급 (unitWon 곱셈 필수).
        OutputSchema:
            - dict: type/basis/unit/unitWon/accounts{canonical:{current,yoyPct}}.
        Prerequisites:
            - 본문 HTML (거래소공시 I 잠정실적).
        Freshness:
            - 공시 시점 (잠정치, 확정치와 다를 수 있음).
        Dataflow:
            - html 을 parseHtmlTables 후 컬럼 매핑 후 accounts.
        TargetMarkets:
            - KR (DART/KRX 거래소공시 I).
    """
    cls = classifyEarningsFlash(reportName)
    isStruct = cls["type"] == "손익구조변동"
    empty = {"type": cls["type"], "basis": cls["basis"], "unit": "원", "unitWon": 1.0, "accounts": {}}
    for tbl in parseHtmlTables(html):
        rows = [[c.text.strip() for c in r.cells] for r in tbl.rows]
        joined = " ".join(cell for row in rows for cell in row)
        if "매출액" not in joined or "영업이익" not in joined:
            continue
        unit, unitWon = _flashUnitWon(joined)
        accounts: dict[str, dict] = {}
        for raw in rows:
            cells = [c for c in raw if c]
            if not cells:
                continue
            canon = _FLASH_ACCOUNTS.get(_flashLabel(cells[0]))
            if not canon or canon in accounts:
                continue
            if isStruct:
                current = _flashNum(cells[1]) if len(cells) > 1 else None
                yoy = _cleanPct(cells[4]) if len(cells) > 4 else None
            else:
                if len(cells) < 8 or "당해실적" not in cells[1]:
                    continue  # 누계실적/변형 행 스킵 (당해실적 본행만)
                current = _flashNum(cells[2])
                yoy = _cleanPct(cells[7])
            if current is not None:
                accounts[canon] = {"current": current, "yoyPct": yoy}
        if accounts:
            return {"type": cls["type"], "basis": cls["basis"], "unit": unit, "unitWon": unitWon, "accounts": accounts}
    return empty


__all__ = [
    "EVENT_SCHEMAS",
    "classifyEarningsFlash",
    "classifyEventReport",
    "eventSchema",
    "expectedFields",
    "parseEarningsFlash",
    "parseEventDisclosure",
]
