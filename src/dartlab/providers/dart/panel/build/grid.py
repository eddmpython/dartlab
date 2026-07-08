"""DART 표준서식 표(`<TABLE>`) 를 colspan/rowspan 확장 dense 격자로 만드는 범용 primitive.

panel 표 파싱의 공용 기반. 재무 셀은 `<TE ACODE>`(build/cell.py), 서술 표(수주·가동률·생산능력)는
지금까지 raw contentRaw 방치였다. 본 모듈은 그 서술 표를 acode 없이 한글 헤더 앵커로 격자화한다.
정부 표준 서식이라 헤더 라벨(수주잔고·가동률·품목·기간)이 회사간 일관돼 범용 격자화가 성립한다.

핵심: COLSPAN/ROWSPAN 을 실제로 펼쳐(dense) 멀티행 헤더를 컬럼별 합성라벨로 만든다. 이 위에서
소비자(narrativeMetric 등)가 개념 컬럼을 지목한다. titleRows._tableToMarkdown 은 span 을 보존만 하고
펼치지 않으므로(렌더링용) 별개다.

SeeAlso:
    - ``build.titleRows._findDirectTRs`` / ``_elemText`` (TR/셀 순회 재사용).
    - ``providers.dart.panel.narrativeMetric`` (본 격자의 첫 소비자, 헤더 taxonomy + confidence).
    - ``build.cell.cellsFromContent`` (`<TE ACODE>` 재무 셀 경로, 별개 앵커).

Requires:
    lxml. utf-8 decoded XML string.
"""

from __future__ import annotations

import re

from lxml import etree

from dartlab.providers.dart.panel.build.titleRows import _elemText, _findDirectTRs

_CELL_TAGS = ("TD", "TH", "TU", "TE")


def normLabel(s: str) -> str:
    """헤더/셀 라벨 정규화. 공백·별표·괄호 제거 후 소문자 (taxonomy 매칭용).

    Args:
        s: 원본 라벨 문자열.

    Returns:
        정규화 문자열. 예 ``"수주잔고 (*1)"`` 는 ``"수주잔고1"``.
    """
    return re.sub(r"[\s\*]+", "", s or "").replace("(", "").replace(")", "").lower()


def _spanInt(v: str | None) -> int:
    try:
        n = int(str(v or "1").strip() or "1")
        return n if n >= 1 else 1
    except (TypeError, ValueError):
        return 1


def tableToGrid(xml: str, *, maxHeaderRows: int = 3) -> dict | None:
    """`<TABLE>` XML 을 COLSPAN/ROWSPAN 확장한 dense 격자로 파싱한다 (범용, 회사무관).

    멀티행 헤더는 컬럼별 합성라벨(``colLabels``)로 결합해 소비자가 개념 컬럼을 지목할 수 있게 한다.
    nested `<TABLE>` 의 TR/셀은 제외(외곽 표만, ``_findDirectTRs``).

    Args:
        xml: 단일 `<TABLE>...` XML 문자열 (panel narrative table leaf 의 period 셀).
        maxHeaderRows: 헤더로 볼 상단 행 최대 수 (합성라벨 결합 범위).

    Returns:
        dict 또는 None. 키:
            ``dense``: ``list[list[tuple[str, bool]]]`` (셀 텍스트, isHeader). span 확장됨.
            ``headerRows``: 헤더 행 인덱스 리스트.
            ``colLabels``: 컬럼별 합성 헤더라벨(정규화, 멀티행 결합).
            ``nrow`` / ``ncol``: 격자 크기.
        파싱 실패·표 부재는 None.

    Raises:
        없음. XML 파싱 실패는 None.

    Example:
        >>> g = tableToGrid("<TABLE><TR><TH>수주잔고</TH></TR><TR><TD>100</TD></TR></TABLE>")
        >>> g["colLabels"]
        ['수주잔고']

    Capabilities:
        - 임의 DART 표를 span 확장 dense 격자 + 합성 헤더라벨로. 재무·서술 표 공통 기반.

    AIContext:
        narrativeMetric.readMetric 이 본 격자에서 헤더 taxonomy 로 개념 컬럼을 지목해 수주잔고·가동률 추출.

    Requires:
        - lxml. 입력은 `<TABLE>` 포함 XML 문자열.
    """
    if not xml or "<TABLE" not in xml:
        return None
    parser = etree.XMLParser(recover=True, huge_tree=True)
    try:
        root = etree.fromstring(xml.encode("utf-8"), parser)
    except (etree.XMLSyntaxError, ValueError):
        return None
    if root is None:
        return None
    table = root if isinstance(root.tag, str) and root.tag == "TABLE" else root.find(".//TABLE")
    if table is None:
        return None

    rawRows: list[list[tuple[str, int, int, bool]]] = []
    for tr in _findDirectTRs(table):
        cells: list[tuple[str, int, int, bool]] = []
        for cell in tr:
            if not isinstance(cell.tag, str) or cell.tag not in _CELL_TAGS:
                continue
            text = _elemText(cell)
            cs = _spanInt(cell.get("COLSPAN"))
            rs = _spanInt(cell.get("ROWSPAN"))
            cells.append((text, cs, rs, cell.tag in ("TH", "TU")))
        rawRows.append(cells)
    if not any(rawRows):
        return None

    # colspan/rowspan 확장으로 dense 격자 (occupied 셀 skip)
    grid: dict[tuple[int, int], tuple[str, bool]] = {}
    for r, cells in enumerate(rawRows):
        c = 0
        for text, cs, rs, ish in cells:
            while (r, c) in grid:
                c += 1
            for dr in range(rs):
                for dc in range(cs):
                    grid[(r + dr, c + dc)] = (text, ish)
            c += cs
    if not grid:
        return None
    maxr = max(k[0] for k in grid) + 1
    maxc = max(k[1] for k in grid) + 1
    dense = [[grid.get((r, c), ("", False)) for c in range(maxc)] for r in range(maxr)]

    headerRows = [r for r in range(min(maxHeaderRows, maxr)) if any(dense[r][c][1] for c in range(maxc))]
    # 합성 헤더라벨: 멀티행 헤더 결합. rowspan 으로 같은 텍스트가 반복되면 연속 중복 제거.
    colLabels: list[str] = []
    for c in range(maxc):
        parts: list[str] = []
        for r in headerRows:
            t = normLabel(dense[r][c][0])
            if t and (not parts or parts[-1] != t):
                parts.append(t)
        colLabels.append("".join(parts))
    return {"dense": dense, "headerRows": headerRows, "colLabels": colLabels, "nrow": maxr, "ncol": maxc}
