"""panel 셀 세분화 파싱 — 재무 5표 표 XML → 셀 dict (lxml, build 서브트리). 별 artifact 0.

``cellsFromContent(contentRaw, ...)`` 가 5표(BS/IS/CIS/CF/SCE) 표 XML 을 셀 dict(CELL_SCHEMA)로 분해.
**read 표면 ``cell._cellsFromPanel`` 이 panel.parquet 의 5표 contentRaw 위에 호출 시 lazy 로 부른다** —
panelCell 별 parquet 파일을 두지 않고 panel.parquet 단일 artifact 에서 그 자리 분해(파생 사슬 0). 두 era:
    - XBRL(2022+): 정부 `<TE ACODE ACONTEXT>` 정밀 셀 (decodeAcontext, 산수 0).
    - 옛(2021 이전, 태그 없음): 표 위치 파싱 (첫 셀=항목명, 이후=당기/전기/전전기 금액, _parseAmount/
      _detectUnit — docs/finance extractAccounts/parseAmount 로직 *참고* 재구현). 과거 ~2011 연장.

build 서브트리(lxml 격리) — read 표면은 이 모듈을 **함수 내 lazy import**(콜드스타트 무영향).

LLM Specifications:
    AntiPatterns:
        - zip 재처리 금지 — panel.parquet contentRaw 만 (R3).
        - valueRaw 숫자화(콤마/괄호 제거) 금지 — 불변 원본, 숫자화는 소비자.
        - 셀을 디스크 parquet 로 영속 금지 — read 가 호출 시 in-memory 분해 (단일 artifact).
    OutputSchema:
        - ``cellsFromContent(contentRaw, *, statement, scope, period, code, rcept) -> Iterator[dict]``.
    Prerequisites:
        - panel.parquet 5표 row contentRaw (read 가 공급). lxml.
    Freshness:
        - 매 호출 (read-time 파생).
    Dataflow:
        - panel.parquet 5표 contentRaw → cellsFromContent(XBRL/옛 분기) → 셀 dict.
    TargetMarkets:
        - KR (DART). XBRL 2025-03+, 옛 표는 전 기간.
"""

from __future__ import annotations

import logging
import re
from collections.abc import Iterator
from pathlib import Path

import lxml.etree as etree
import polars as pl

import dartlab.config as _cfg

from ..cellSchema import CELL_SCHEMA

_log = logging.getLogger(__name__)

# 재무 5표 statement (= panel.parquet disclosureKey). SCE(자본변동표)=EF, CIS(포괄손익)=IS3 (ACLASS 실측).
# IS1=단일 손익계산서, IS2=별도 손익, IS3=포괄손익 — 회사마다 손익 표현이 달라 셋 다 포함.
CELL_STATEMENTS: frozenset[str] = frozenset({"BS", "IS1", "IS2", "IS3", "CF", "EF"})

# statement → 흐름(d=duration)/시점(e=instant). 옛 표(태그 없음)는 statement 로 ctxFlow 도출.
_STMT_FLOW: dict[str, str] = {"BS": "e", "IS1": "d", "IS2": "d", "IS3": "d", "CF": "d", "EF": "e"}

# ACONTEXT period 토큰: prefix(당기/전기/전전기) + FY + 4자리연도 + 흐름/시점(d|e) + marker.
# marker = FY(연간) / FQ?(1분기) / HY?(반기·2분기) / TQ?(3분기), 접미 A(누적)·Q(단독)·∅(시점).
_PERIOD_RE = re.compile(r"^(BP|P|C)FY(\d{4})([de])(FY|FQA|FQQ|FQ|HYA|HYQ|HY|TQA|TQQ|TQ)$")
_AXIS_PREFIXES = ("ifrs-full", "dart")

# marker base(접미 제거) → 분기번호. FY=연간(4분기). FQ=1·HY=2(반기)·TQ=3.
_MARKER_QUARTER = {"FY": 4, "FQ": 1, "HY": 2, "TQ": 3}


def _markerToQuarterMode(marker: str) -> tuple[int, str]:
    """period marker → (ctxQuarter, ctxMode). FY=연간, 접미 A=누적·Q=단독·∅=시점bare.

    Examples:
        >>> _markerToQuarterMode("FY")
        (4, 'Y')
        >>> _markerToQuarterMode("FQA")
        (1, 'A')
        >>> _markerToQuarterMode("TQQ")
        (3, 'Q')
        >>> _markerToQuarterMode("HY")
        (2, 'P')
    """
    if marker == "FY":
        return (4, "Y")
    base = marker[:2]  # FQ/HY/TQ (항상 2글자)
    suffix = marker[2:]  # "", "A"(누적), "Q"(단독)
    mode = suffix if suffix in ("A", "Q") else "P"
    return (_MARKER_QUARTER[base], mode)


def _axisMembers(segs: list[str]) -> list[str]:
    """ACONTEXT 의 axis 부분 토큰 list → Member 로 끝나는 토큰만 (axis 드롭, 멤버 보존).

    토큰은 ``_`` 로 잘려 들어오므로 ``ifrs-full``/``dart``/``entity`` prefix 로 재조합 후
    ``Member`` 접미만 남긴다 (``...Axis`` 는 멤버에 1:1 종속이라 멤버가 정체성).

    Args:
        segs: ACONTEXT 를 ``_`` split 한 뒤 period 토큰 제외한 나머지 segment list.

    Returns:
        Member 토큰 list (예: ``["ConsolidatedMember", "RetainedEarningsMember"]``).

    표준 ``ifrs-full_``/``dart_`` prefix 는 벗기고(가독), 회사 네임스페이스 ``entity...`` 는 보존.

    Examples:
        >>> _axisMembers(["ifrs-full", "ConsolidatedAndSeparateFinancialStatementsAxis",
        ...               "ifrs-full", "ConsolidatedMember"])
        ['ConsolidatedMember']
    """
    tokens: list[str] = []
    buf: list[str] = []
    for s in segs:
        if s in _AXIS_PREFIXES or s.startswith("entity"):
            if buf:
                tokens.append("_".join(buf))
            buf = [s]
        else:
            buf.append(s)
    if buf:
        tokens.append("_".join(buf))
    members = [t for t in tokens if t.endswith("Member")]
    return [
        m[len("ifrs-full_") :] if m.startswith("ifrs-full_") else m[len("dart_") :] if m.startswith("dart_") else m
        for m in members
    ]


def decodeAcontext(ctx: str) -> tuple[int, str, int, str, str] | None:
    """ACONTEXT attribute → (ctxYear, ctxFlow, ctxQuarter, ctxMode, axisPath) 결정론적 분해.

    period 토큰 ``(C|P|BP)FY{year}{d|e}{marker}`` 를 regex 로 분해하고(marker→분기·모드), 나머지
    axis/member 쌍에서 Member 만 ``|`` join. (``tests/_attempts/panelCellFeasibility.py::_decodeContext``
    의 시도 로직을 정식 본체화 + 전 분기 토큰(FQ/HY/TQ/FY) 포착 — 우회 아님.)

    Args:
        ctx: TE 의 ACONTEXT attribute (예 ``"CFY2025dFY_ifrs-full_...Axis_ifrs-full_ConsolidatedMember"``).

    Returns:
        ``(ctxYear, ctxFlow, ctxQuarter, ctxMode, axisPath)`` — ctxYear=실연도(int), ctxFlow="d"|"e",
        ctxQuarter=1/2/3/4, ctxMode="Y"(연간)|"A"(누적)|"Q"(단독)|"P"(시점bare), axisPath=멤버 ``|``
        join. period 토큰 미매칭 시 None.

    Examples:
        >>> decodeAcontext("CFY2025dFY_ifrs-full_X_ifrs-full_ConsolidatedMember")
        (2025, 'd', 4, 'Y', 'ConsolidatedMember')
        >>> decodeAcontext("BPFY2023eFY_ifrs-full_X_ifrs-full_ConsolidatedMember")
        (2023, 'e', 4, 'Y', 'ConsolidatedMember')
        >>> decodeAcontext("CFY2025dTQA_ifrs-full_X_ifrs-full_ConsolidatedMember")
        (2025, 'd', 3, 'A', 'ConsolidatedMember')
        >>> decodeAcontext("CFY2025dFQQ_ifrs-full_X_ifrs-full_ConsolidatedMember")
        (2025, 'd', 1, 'Q', 'ConsolidatedMember')
        >>> decodeAcontext("garbage") is None
        True

    Raises:
        없음 — 미매칭은 None.

    SeeAlso:
        - ``_xbrlCellsFromContent`` — 본 분해를 TE 마다 호출.
        - ``..cell.readCellWide`` — 분해 결과 컬럼(ctxFlow/ctxQuarter/ctxMode)으로 freq 선택.

    Requires:
        - 없음 (순수 문자열). lxml 무관.

    Capabilities:
        - 정부 기간 문법을 산수 0 으로 (당기/전기/전전기 × 흐름/시점 × 연간/분기 누적·단독·시점).

    Guide:
        - build/cell 내부 호출. read 는 분해 결과 컬럼만 보고 본 함수 미호출(R2).

    AIContext:
        - 결정론 분해 — 005930 전 ACONTEXT 필링(FQ/HY/TQ/FY) 전건 매칭 실측.

    When:
        - TE 셀의 ACONTEXT 를 (연도, 흐름/시점, 분기, 모드, 축경로)로 풀 때.

    How:
        - ``_`` split → period 토큰 regex → marker→(분기,모드) → 나머지 _axisMembers.

    LLM Specifications:
        AntiPatterns:
            - period 토큰 빼기 산수 금지 — 정부가 단독/누적/연간 다 박음, 토큰만 읽음.
            - 분기 토큰 일부(FQ/HY)만 포착 금지 — 전 분기 marker 전수.
        OutputSchema:
            - ``tuple[int, str, int, str, str] | None``.
        Prerequisites:
            - 없음.
        Freshness:
            - 양식 변경 시 _PERIOD_RE/_MARKER_QUARTER 재검증.
        Dataflow:
            - ctx → split → regex → (year, flow, quarter, mode) + members.
        TargetMarkets:
            - KR (DART).
    """
    if not ctx:
        return None
    parts = ctx.split("_")
    m = _PERIOD_RE.match(parts[0])
    if m is None:
        return None
    ctxYear = int(m.group(2))
    ctxFlow = m.group(3)
    ctxQuarter, ctxMode = _markerToQuarterMode(m.group(4))
    axisPath = "|".join(_axisMembers(parts[1:]))
    return (ctxYear, ctxFlow, ctxQuarter, ctxMode, axisPath)


def _teText(te) -> str:
    """TE element 의 inner text (태그 제거) — valueRaw/label 용. 콤마·괄호 보존.

    Args:
        te: TE lxml element.

    Returns:
        itertext concat strip (예 ``"333,605,938"``, ``"(1,234)"``, ``"매출액 (주30)"``).
    """
    return "".join(te.itertext()).strip()  # noqa: E501  # element.itertext OK


def _rowLabel(tes: list) -> str:
    """같은 TR 의 첫 ACODE-없는 TE 한글 라벨 (value 셀과 100% 동거 실측).

    Args:
        tes: 한 TR 의 TE element list.

    Returns:
        첫 ACODE-없는 TE 의 text. 없으면 "".
    """
    for te in tes:
        if not (te.get("ACODE", "") or "").strip():
            txt = _teText(te)
            if txt:
                return txt
    return ""


def _parseAmount(text: str) -> float | None:
    """금액 텍스트 → float (△/▲/괄호 음수, 콤마 strip). 주석번호/비숫자는 None.

    (docs/finance ``tableParser.parseAmount`` 로직 참고 재구현 — panel 자급, cross-import 0.)

    Examples:
        >>> _parseAmount("200,653,482")
        200653482.0
        >>> _parseAmount("△500")
        -500.0
        >>> _parseAmount("(1,234)")
        -1234.0
        >>> _parseAmount("(주30)") is None
        True
        >>> _parseAmount("매출액") is None
        True
    """
    from dartlab.providers.dart.parse.amount import parseAmount

    return parseAmount(text)


def _detectUnit(text: str) -> int:
    """본문에서 ``단위 : 백만원|천원|원`` → 원 기준 배율. 미발견 시 백만원(기본 1_000_000)."""
    from dartlab.providers.dart.parse.amount import detectUnitScale

    return detectUnitScale(text, defaultUnit="백만원") or 1_000_000


def _parseFragment(contentRaw: str, *, provenance: str | None = None):
    """panel.parquet contentRaw를 파싱하고 복구·실패를 provenance와 함께 기록한다."""
    if not contentRaw:
        if provenance is not None:
            _log.warning("panel cell XML empty: %s", provenance)
        return None
    parser = etree.XMLParser(recover=True, huge_tree=True)
    try:
        root = etree.fromstring(f"<root>{contentRaw}</root>".encode(), parser)
    except (etree.XMLSyntaxError, ValueError) as exc:
        _log.warning(
            "panel cell XML parse failed: %s error=%s: %s",
            provenance or "unknown",
            type(exc).__name__,
            exc,
        )
        return None
    if parser.error_log:
        first = parser.error_log[0]
        _log.warning(
            "panel cell XML recovered: %s errors=%d first=%s",
            provenance or "unknown",
            len(parser.error_log),
            first.message,
        )
    return root


def cellsFromContent(
    contentRaw: str, *, statement: str, scope: str, period: str, code: str, rcept: str
) -> Iterator[dict]:
    """panel.parquet 한 5표 row 의 contentRaw → 셀 행 iter (XBRL/옛 분기).

    contentRaw 에 ACONTEXT TE 가 있으면 XBRL 정밀 경로(decodeAcontext), 없으면 옛 표 위치 파싱
    (`_parseOldStatementTable`). panel 은 자기 artifact(panel.parquet) contentRaw 만 본다.

    Args:
        contentRaw: 5표 row 의 표 XML (panel.parquet contentRaw).
        statement: disclosureKey (BS/IS2/IS3/CF/EF).
        scope: consolidated/standalone.
        period: 보고서 period (YYYYQn).
        code: 종목코드.
        rcept: 접수번호.

    Yields:
        CELL_SCHEMA 14-col dict.

    Raises:
        없음 — 파싱 실패 시 0 행.

    Example:
        >>> list(cellsFromContent("<TABLE>...</TABLE>", statement="IS2", scope="consolidated",
        ...                       period="2025Q4", code="005930", rcept="R1"))  # doctest: +SKIP
    """
    provenance = f"code={code} period={period} statement={statement} rcept={rcept or '-'}"
    root = _parseFragment(contentRaw, provenance=provenance)
    if root is None:
        return
    if root.find(".//TE[@ACONTEXT]") is not None:
        yield from _xbrlCellsFromContent(root, statement=statement, scope=scope, period=period, code=code, rcept=rcept)
    else:
        yield from _parseOldStatementTable(
            root, statement=statement, scope=scope, period=period, code=code, rcept=rcept
        )


def _xbrlCellsFromContent(root, *, statement: str, scope: str, period: str, code: str, rcept: str) -> Iterator[dict]:
    """XBRL era(ACONTEXT 박힘) — TR 별 첫 ACODE-없는 TE=label, ACONTEXT TE=value 정밀 셀.

    Args:
        root: contentRaw 파싱 root.
        statement/scope/period/code/rcept: 셀 메타.

    Yields:
        CELL_SCHEMA dict (acode 정밀, axisPath 차원).
    """
    order = 0
    for tr in root.iter("TR"):
        tes = list(tr.iter("TE"))
        if not tes:
            continue
        label = _rowLabel(tes)
        for te in tes:
            actx = (te.get("ACONTEXT", "") or "").strip()
            acode = (te.get("ACODE", "") or "").strip()
            if not actx or not acode:
                continue
            decoded = decodeAcontext(actx)
            if decoded is None:
                continue
            ctxYear, ctxFlow, ctxQuarter, ctxMode, axisPath = decoded
            yield {
                "corp": code,
                "rceptNo": rcept,
                "filingPeriod": period,
                "statement": statement,
                "scope": scope,
                "acode": acode,
                "label": label,
                "ctxYear": ctxYear,
                "ctxFlow": ctxFlow,
                "ctxQuarter": ctxQuarter,
                "ctxMode": ctxMode,
                "axisPath": axisPath,
                "valueRaw": _teText(te),
                "cellOrder": order,
            }
            order += 1


def _parseOldStatementTable(root, *, statement: str, scope: str, period: str, code: str, rcept: str) -> Iterator[dict]:
    """옛 era(ACONTEXT 없음) — 표 위치 파싱: TR 첫 셀=항목명, 이후 셀=당기/전기/전전기 금액.

    한 보고서가 당기/전기/전전기를 운반 → 컬럼 i = ctxYear(period연도 −i). acode=None(태그 없음),
    label=항목명, axisPath=ConsolidatedMember(top-level), ctxFlow=statement 파생. (docs/finance
    ``extractAccounts``/``parseAmount`` 로직 참고 — panel 자급, contentRaw 만.)

    Args:
        root: contentRaw 파싱 root.
        statement/scope/period/code/rcept: 셀 메타. period 연도 = 당기.

    Yields:
        CELL_SCHEMA dict (acode=None, label=항목명).
    """
    periodYear = int(period[:4])
    isAnnual = period.endswith("Q4")
    quarter = 4 if isAnnual else (int(period[5]) if len(period) > 5 and period[5].isdigit() else 4)
    mode = "Y" if isAnnual else "A"  # 옛 분기는 누적(A) — 단독(Q)은 태그 없어 불가
    flow = _STMT_FLOW.get(statement, "d")
    order = 0
    for tr in root.iter("TR"):
        cells = [c for c in tr if c.tag in ("TD", "TE")]
        if len(cells) < 2:
            continue
        label = _teText(cells[0])
        if not label or _parseAmount(label) is not None:
            continue  # 첫 셀은 비숫자 항목명
        amounts = [_teText(c) for c in cells[1:]]
        parsed = [_parseAmount(a) for a in amounts]
        if not any(p is not None for p in parsed):
            continue  # 데이터 행만 (헤더/단위 행 제외)
        for col, (rawV, num) in enumerate(zip(amounts, parsed)):
            if num is None:
                continue
            yield {
                "corp": code,
                "rceptNo": rcept,
                "filingPeriod": period,
                "statement": statement,
                "scope": scope,
                "acode": None,
                "label": label,
                "ctxYear": periodYear - col,
                "ctxFlow": flow,
                "ctxQuarter": quarter,
                "ctxMode": mode,
                "axisPath": "ConsolidatedMember",
                "valueRaw": rawV,
                "cellOrder": order,
            }
            order += 1


def _parseOldNoteTable(root, *, statement: str, scope: str, period: str, code: str, rcept: str) -> Iterator[dict]:
    """옛(ACONTEXT 없음) **주석** 표 — 우측정렬 가드 위치파싱 (병합행 phantom 차단). 5표 파서는 무수정.

    5표 ``_parseOldStatementTable`` 은 TR 첫 셀=항목명 가정이나, 주석 총계행은 rowspan 으로 ``합계|라벨|값``
    3셀 병합이라 첫 셀('합계')을 라벨로 쓰면 값열이 한 칸 밀려 ctxYear 오배정(prior-year phantom, 표본 77.5%).
    본 파서는 **값=후행 contiguous 숫자런, 라벨=값런 직전 텍스트셀**(우측정렬)이라 병합행도 정확. 단일축 lineitem
    주석(비용성격별·판관비·법인세 등)을 5표처럼 당기/전기 비교열로 과거 연장(~2013).

    Args:
        root: contentRaw 파싱 root.
        statement: 노트 코드(NT_D######) — 셀 statement 필드.
        scope: consolidated / standalone.
        period: 보고서 period(YYYYQn). 연도=당기, 컬럼 i=ctxYear(연도−i).
        code: 종목코드.
        rcept: 접수번호.

    Yields:
        CELL_SCHEMA dict (acode=None, label=항목명, axisPath=ConsolidatedMember).
    """
    periodYear = int(period[:4])
    isAnnual = period.endswith("Q4")
    quarter = 4 if isAnnual else (int(period[5]) if len(period) > 5 and period[5].isdigit() else 4)
    mode = "Y" if isAnnual else "A"  # 옛 분기는 누적(A) — 단독(Q)은 태그 없어 불가
    flow = _STMT_FLOW.get(statement, "d")
    order = 0
    for tr in root.iter("TR"):
        cells = [c for c in tr if c.tag in ("TD", "TE")]
        if len(cells) < 2:
            continue
        texts = [_teText(c) for c in cells]
        amts = [_parseAmount(t) for t in texts]
        # 후행 숫자런(오른쪽부터, 빈셀 건너뜀, 텍스트 만나면 정지) = 당기/전기/… 값열.
        valIdx: list[int] = []
        for i in range(len(cells) - 1, -1, -1):
            if amts[i] is not None:
                valIdx.append(i)
            elif texts[i].strip():
                break  # 라벨 경계
        valIdx.reverse()
        if not valIdx:
            continue
        firstVal = valIdx[0]
        # 라벨 = 값런 직전 마지막 텍스트셀(병합행 `합계|라벨|값` 도 중간 라벨 정확).
        labelCells = [texts[j] for j in range(firstVal) if texts[j].strip() and amts[j] is None]
        label = labelCells[-1] if labelCells else (texts[0] if texts else "")
        if not label or _parseAmount(label) is not None:
            continue
        for col, idx in enumerate(valIdx):  # 좌=당기, 우로 갈수록 과거
            yield {
                "corp": code,
                "rceptNo": rcept,
                "filingPeriod": period,
                "statement": statement,
                "scope": scope,
                "acode": None,
                "label": label,
                "ctxYear": periodYear - col,
                "ctxFlow": flow,
                "ctxQuarter": quarter,
                "ctxMode": mode,
                "axisPath": "ConsolidatedMember",
                "valueRaw": texts[idx],
                "cellOrder": order,
            }
            order += 1
