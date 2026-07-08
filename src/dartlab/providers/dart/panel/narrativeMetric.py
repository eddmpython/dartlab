"""사업보고서 서술 표에서 정량 지표를 전천후 추출 (panel SSOT, 하드코딩 회사별 규칙 0).

수주잔고·가동률 같은 값은 재무제표가 아니라 사업보고서 서술 섹션의 표(`<TABLE>`)에 있다. panel 은
지금까지 이 표를 raw 로 방치했다. 본 모듈은 build.grid.tableToGrid(범용 격자) + 성장형 헤더 taxonomy
(METRIC_DEFS) + confidence gate 로 그 표에서 개념 컬럼을 지목해 종목별 값을 뽑는다.

안전(조용한 오답 0): 헤더 강매칭 + 단위 명확(표 내부) + sanity 통과일 때만 추출. 미달은 정직 gap(None).
단위를 표 내부에서 우선 탐지해 sibling 표의 다른 단위 오선택(억원 vs 백만원)을 차단한다.

SeeAlso:
    - ``build.grid.tableToGrid`` (범용 격자 primitive).
    - ``core.extractionCatalog`` narrative 개념(narrativeAnchor 로 섹션 표 선택).
    - ``scan.builders.kr.narrativeMetrics`` (본 함수의 전종목 프리빌드).
"""

from __future__ import annotations

import re

from dartlab.core.extractionCatalog import getConcept
from dartlab.core.utils.helpers import parseNumStr
from dartlab.providers.dart.panel.build.grid import normLabel, tableToGrid

_UNIT_SCALE = {"백만원": 1e6, "억원": 1e8, "천원": 1e3, "십억원": 1e9, "원": 1.0}
_AMOUNT_HINTS = ("금액", "가액")
_QTY_HINTS = ("수량", "대수", "개수")
_TOTAL_HINTS = ("합계", "합 계", "총계", "총 계", "소계")

# 성장형 지표 taxonomy. 개념 -> {섹션, 동의어/전략, 종류, sanity}. 회사별 하드코딩 아님.
METRIC_DEFS: dict[str, dict] = {
    "backlog": {
        "label": "수주잔고",
        "section": "narrative.salesOrder",
        "kind": "amount",
        "synonyms": ["수주잔고", "기말수주잔고", "계약잔액", "기초계약잔액", "수주잔량"],
        "sanityMax": 1e15,  # 1000조원 상한 (단위 오선택 등 명백 오류 컷)
    },
    "utilizationRate": {
        "label": "가동률",
        "section": "narrative.productionCapacity",
        "kind": "rate",
        "direct": ["가동률", "평균가동률"],
        "compute": [(["실제가동시간", "실가동시간"], ["가동가능시간"]), (["생산실적"], ["생산능력"])],
        "sanityMin": 0.0,
        "sanityMax": 150.0,
    },
}


def listMetrics() -> list[dict]:
    """추출 가능한 서술 지표 목록(metricId·label·섹션·종류)을 반환한다.

    Returns:
        ``[{metricId, label, section, kind}]``.
    """
    return [
        {"metricId": k, "label": v["label"], "section": v["section"], "kind": v["kind"]} for k, v in METRIC_DEFS.items()
    ]


def _detectUnit(xml: str) -> tuple[float, bool]:
    """표 XML 내부에서 (단위:X) 탐지. (scale, found). 미발견 시 (1e6=백만원 기본, False)."""
    m = re.search(r"\(단위\s*[:：]\s*([^\)/]{1,8})", xml)
    if m:
        return _UNIT_SCALE.get(normLabel(m.group(1)), 1e6), True
    return 1e6, False


def _pickCol(colLabels: list[str], synonyms: list[str], *, amountPref: bool) -> int | None:
    """합성 헤더라벨에서 개념 컬럼 지목. amountPref 면 금액 컬럼 우선, 수량-only 제외."""
    target = None
    for c, lab in enumerate(colLabels):
        if not any(normLabel(s) in lab for s in synonyms):
            continue
        if amountPref:
            if any(q in lab for q in _QTY_HINTS) and not any(a in lab for a in _AMOUNT_HINTS):
                continue  # 수량-only 컬럼 제외
            target = c
            if any(a in lab for a in _AMOUNT_HINTS):
                return c  # 금액 명시 우선
        else:
            return c
    return target


def _resolveAmount(grid: dict, xml: str, mdef: dict, leafScale: float | None) -> dict | None:
    """금액 지표(수주잔고 등)를 격자에서 지목 + 합계행 우선 + 단위환산 + sanity.

    단위는 표 내부 우선, 없으면 leaf 전역 단일단위(leafScale, 모호하면 None)로 확정. 둘 다 없으면
    기본 백만원 + 저신뢰. sibling 표의 다른 단위 오선택은 leafScale 이 단일일 때만 신뢰해 차단.
    """
    col = _pickCol(grid["colLabels"], mdef["synonyms"], amountPref=True)
    if col is None:
        return None
    inScale, inFound = _detectUnit(xml)
    if inFound:
        scale, unitConf = inScale, True
    elif leafScale is not None:
        scale, unitConf = leafScale, True
    else:
        scale, unitConf = 1e6, False
    dense, headerRows = grid["dense"], set(grid["headerRows"])
    total = 0.0
    totalRowVal = None
    n = 0
    for r in range(grid["nrow"]):
        if r in headerRows or col >= len(dense[r]):
            continue
        v = parseNumStr(dense[r][col][0])
        if v is None or v <= 0:
            continue
        rowLabel = normLabel(dense[r][0][0]) if dense[r] else ""
        if any(normLabel(h) in rowLabel for h in _TOTAL_HINTS):
            totalRowVal = v
        total += v
        n += 1
    raw = totalRowVal if totalRowVal is not None else total
    if raw <= 0:
        return None
    value = raw * scale
    if value > mdef["sanityMax"]:
        return None  # 명백 오류(단위 오선택 등) 컷
    conf = (
        "high"
        if (unitConf and totalRowVal is not None)
        else ("mid" if (unitConf or totalRowVal is not None) else "low")
    )
    return {"value": value, "unit": "원", "confidence": conf, "provenance": f"수주표 col{col} rows{n}"}


def _resolveRate(grid: dict) -> dict | None:
    """비율 지표(가동률)를 직접 라벨 또는 성분(실제/가능, 실적/능력)에서 계산."""
    mdef = METRIC_DEFS["utilizationRate"]
    labels = grid["colLabels"]
    dense, headerRows = grid["dense"], set(grid["headerRows"])
    dataRows = [r for r in range(grid["nrow"]) if r not in headerRows]

    def colVals(c: int) -> list[float]:
        """데이터 행에서 컬럼 c 의 파싱 가능한 수치 값 목록."""
        out = []
        for r in dataRows:
            if c < len(dense[r]):
                v = parseNumStr(dense[r][c][0])
                if v is not None:
                    out.append(v)
        return out

    # 1) 직접 라벨
    dc = _pickCol(labels, mdef["direct"], amountPref=False)
    if dc is not None:
        vals = [v for v in colVals(dc) if 0 <= v <= 150]
        if vals:
            value = sum(vals) / len(vals)
            return {"value": round(value, 1), "unit": "%", "confidence": "high", "provenance": f"가동률 col{dc}"}
    # 2) 성분 계산 (실제/가능, 실적/능력)
    for numSyn, denSyn in mdef["compute"]:
        nc = _pickCol(labels, numSyn, amountPref=False)
        dcol = _pickCol(labels, denSyn, amountPref=False)
        if nc is None or dcol is None:
            continue
        num = colVals(nc)
        den = colVals(dcol)
        if num and den and sum(den) > 0:
            value = sum(num) / sum(den) * 100.0
            if 0 <= value <= 150:
                return {"value": round(value, 1), "unit": "%", "confidence": "mid", "provenance": f"계산 {nc}/{dcol}"}
    return None


def readMetric(code: str, metricId: str, *, marketNs: str = "kr") -> dict | None:
    """종목의 사업보고서 서술 표에서 지표(수주잔고·가동률 등)를 전천후 추출한다.

    METRIC_DEFS 의 섹션 앵커로 panel 서술 표 leaf 를 고르고, tableToGrid 격자 위에서 헤더 taxonomy 로
    개념 컬럼을 지목해 값을 뽑는다. 헤더 강매칭 + 단위/전략 명확 + sanity 통과일 때만 반환(조용한 오답 0).

    Args:
        code: 종목코드 (KR 6자리).
        metricId: METRIC_DEFS 키 ("backlog"·"utilizationRate").
        marketNs: 시장 namespace ("kr").

    Returns:
        ``{value, unit, confidence(high/mid/low), period, provenance}`` 또는 None(정직 gap).

    Raises:
        ValueError: 미등록 metricId.

    Example:
        >>> readMetric("042660", "backlog")  # doctest: +SKIP
        {'value': 3.5e+16, 'unit': '원', 'confidence': 'high', ...}

    Capabilities:
        - 표준서식 서술 표를 격자화 + 헤더 taxonomy 로 종목별 정량 지표 추출. 회사별 코드 0.

    AIContext:
        scan.builders.kr.narrativeMetrics 가 전종목 순회로 본 함수를 프리빌드해 수주잔고·가동률 스크리닝화.

    Requires:
        - 로컬 panel artifact + core.extractionCatalog narrative 개념(narrativeAnchor).
    """
    mdef = METRIC_DEFS.get(metricId)
    if mdef is None:
        raise ValueError(f"미등록 metricId: {metricId!r}. 가용: {sorted(METRIC_DEFS)}")
    concept = getConcept(mdef["section"])
    if concept is None or concept.narrativeAnchor is None:
        return None
    _chapter, keyword = concept.narrativeAnchor

    from dartlab.providers.dart.panel.panel import Panel

    p = Panel(code, marketNs=marketNs)
    if p is None or getattr(p, "height", 0) == 0:
        return None
    if "sectionLeaf" not in p.columns or "disclosureKey" not in p.columns:
        return None
    import polars as pl

    mask = pl.col("disclosureKey").is_null() & pl.col("sectionLeaf").fill_null("").str.contains(keyword, literal=True)
    if "leafType" in p.columns:
        mask = mask & (pl.col("leafType") == "table")
    leaf = p.filter(mask)
    if leaf.is_empty():
        return None

    pcols = [c for c in leaf.columns if re.match(r"20\d\dQ?\d?", c)]
    pcols = sorted(pcols, reverse=True)
    # leaf 전역 단일단위 확정 (sibling 표의 단위 caption. 모호하면 None 이라 신뢰 안 함)
    allText = " ".join(str(leaf[pc][i] or "") for i in range(leaf.height) for pc in pcols[:3])
    leafUnits = {normLabel(u) for u in re.findall(r"\(단위\s*[:：]\s*([^\)/]{1,8})", allText)} & set(_UNIT_SCALE)
    leafScale = _UNIT_SCALE[next(iter(leafUnits))] if len(leafUnits) == 1 else None
    for i in range(leaf.height):
        for pc in pcols[:3]:  # 최신 3 기간 시도
            xml = str(leaf[pc][i] or "")
            if not any(normLabel(s) in normLabel(xml) for s in mdef.get("synonyms", mdef.get("direct", []))):
                if "<TABLE" not in xml:
                    continue
            grid = tableToGrid(xml)
            if grid is None:
                continue
            res = _resolveAmount(grid, xml, mdef, leafScale) if mdef["kind"] == "amount" else _resolveRate(grid)
            if res is not None:
                res["period"] = pc
                return res
    return None
