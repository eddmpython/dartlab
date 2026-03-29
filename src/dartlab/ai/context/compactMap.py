"""compact map — Aider repo-map 스타일 회사 프로필.

~200-400 토큰. 시스템 프롬프트에 항상 포함.
AI가 어떤 도구를 써야 할지 판단하는 근거.
"""

from __future__ import annotations

from typing import Any


def buildCompactMap(company: Any) -> str:
    """회사 프로필 compact map 생성."""
    lines: list[str] = []

    corpName = getattr(company, "corpName", "?")
    stockCode = getattr(company, "stockCode", getattr(company, "ticker", "?"))
    market = getattr(company, "market", "")
    currency = getattr(company, "currency", "KRW")

    # 섹터
    sectorLabel = ""
    try:
        from dartlab.core.sector import classify

        sectorInfo = classify(stockCode)
        if sectorInfo and hasattr(sectorInfo, "sectorName"):
            sectorLabel = sectorInfo.sectorName
        elif isinstance(sectorInfo, dict):
            sectorLabel = sectorInfo.get("sectorName", "")
    except (ImportError, AttributeError, KeyError, TypeError, ValueError):
        pass

    header = f"## {corpName} ({stockCode})"
    if market:
        header += f" — {market}"
    if sectorLabel:
        header += f", {sectorLabel}"
    lines.append(header)

    # 재무제표 사용 가능 목록
    stmts = []
    for name in ("BS", "IS", "CF", "CIS", "SCE"):
        try:
            df = getattr(company, name, None)
            if df is not None and len(df) > 0:
                cols = [c for c in df.columns if c not in ("항목", "snakeId", "account")]
                periods = sorted(cols) if cols else []
                if periods:
                    stmts.append(f"{name}({periods[0]}~{periods[-1]})")
                else:
                    stmts.append(name)
        except (AttributeError, TypeError, ValueError):
            pass
    if stmts:
        lines.append(f"- 재무: {', '.join(stmts)}")

    # 비율 사용 가능 여부 (수치는 코드로 조회하도록 유도)
    try:
        ratios = getattr(company, "ratios", None)
        if callable(ratios):
            r = ratios()
            if r is not None and hasattr(r, "columns"):
                lines.append(f"- 비율: c.ratios()로 조회 가능 ({len(r.columns)}개 지표)")
    except (AttributeError, TypeError, ValueError):
        pass

    # sections 정보
    try:
        sections = getattr(company, "sections", None)
        if sections is not None and hasattr(sections, "height"):
            topics = sections.select("topic").unique().height if "topic" in sections.columns else 0
            lines.append(f"- 공시: {topics}개 topic")
    except (AttributeError, TypeError, ValueError):
        pass

    # changes 건수
    try:
        docsSections = getattr(getattr(company, "docs", None), "sections", None)
        if docsSections is not None and hasattr(docsSections, "changes"):
            changes = docsSections.changes()
            if changes is not None and hasattr(changes, "height"):
                lines.append(f"- 변화: {changes.height}건")
    except (AttributeError, TypeError, ValueError):
        pass

    # report apiType 수
    try:
        report = getattr(company, "report", None)
        if report is not None:
            apiTypes = getattr(report, "availableApiTypes", None)
            if apiTypes:
                lines.append(f"- 보고서: {len(apiTypes)}개 apiType")
    except (AttributeError, TypeError, ValueError):
        pass

    # insight 사용 가능 여부
    try:
        from dartlab.analysis.financial.insight.pipeline import analyze as insightAnalyze

        result = insightAnalyze(stockCode, company=company)
        if result is not None:
            lines.append("- 인사이트: dartlab.analysis(c, axes=['financial']) 또는 c.insights로 조회 가능")
    except (ImportError, AttributeError, KeyError, TypeError, ValueError):
        pass

    return "\n".join(lines) if len(lines) > 1 else ""


