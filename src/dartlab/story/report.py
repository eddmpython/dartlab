"""전문 리포트 계약 emitter - Story(기존 builders) → ReportModel(contracts/reportModel.ts conform).

사상: story 는 L3 조합기다. 숫자는 전부 L2 엔진(buildStory builders·analysis.valuation calcDFV)이
계산하고, 본 모듈은 결과를 계약 블록으로 *엮기*만 한다(self-calc 0). thesis-led 아크 - 결론(thesis)을
최상단에, 기존 분석 섹션을 본문에, de-gate 밸류에이션(내재가치 bridge·시나리오)을 pro 블록으로.
SSOT: mainPlan/professional-report-engine/03-report-engine-architecture.md §2.3.

L계층: story=L3, valuation=L2 → L2 를 함수 내부 lazy import(import 방향 L2→L3 준수).
"""

from __future__ import annotations

from typing import Any

_PERSPECTIVE_LABELS = {
    "full": "종합",
    "valuation": "밸류에이션",
    "earnings": "수익체력",
    "credit": "신용",
    "growth": "성장",
    "crisis": "위기",
    "thesis": "투자논거",
    "executive": "경영진 요약",
    "governance": "지배구조",
    "macro": "거시",
    "dividend": "배당",
}

_MODEL_MAP = {
    "dcf2stage": "DCF",
    "dcf": "DCF",
    "ddm": "DDM",
    "rim": "RIM",
    "relative": "relative",
    "relativeSurvival": "relative",
    "liquidation": "liquidation",
    "bankExcessReturn": "excessReturn",
    "sotp": "SOTP",
}


def _fmtCell(value: Any) -> str:
    """표 셀 값을 문자열로 - None=빈칸, 그 외 str()."""
    if value is None:
        return ""
    return str(value)


def _mapBlock(block: Any) -> dict | None:
    """Story 블록 dataclass → 계약 ReportBlock dict (legacy 6→8). 미지원=None(graceful)."""
    cls = type(block).__name__
    if cls == "HeadingBlock":
        return {"type": "heading", "title": getattr(block, "title", "")}
    if cls == "TextBlock":
        text = getattr(block, "text", "")
        return {"type": "text", "text": text} if text else None
    if cls == "MetricBlock":
        metrics = [{"label": str(lbl), "value": str(val)} for lbl, val in getattr(block, "metrics", [])]
        return {"type": "metrics", "metrics": metrics} if metrics else None
    if cls == "FlagBlock":
        flags = list(getattr(block, "flags", []))
        if not flags:
            return None
        kind = "opportunity" if getattr(block, "kind", "warning") == "opportunity" else "warning"
        return {"type": "flags", "kind": kind, "flags": flags}
    if cls == "TableBlock":
        df = getattr(block, "df", None)
        rows = df.to_dicts() if hasattr(df, "to_dicts") else []
        data = [{str(k): _fmtCell(v) for k, v in row.items()} for row in rows]
        return {"type": "table", "label": getattr(block, "label", "") or None, "data": data}
    if cls == "ChartBlock":
        # 차트는 P3 랜딩에서 MiniFinChart SSOT 로 재구성 - 여기선 캡션만 text 로 graceful 보존.
        caption = getattr(block, "caption", "")
        return {"type": "text", "text": caption} if caption else None
    return None


def _valuationView(dfv: dict) -> dict | None:
    """calcDFV 출력 → 계약 ValuationView(내재가치·WACC·재투자묶인 g·reverse-DCF)."""
    intrinsic = dfv.get("dFV")
    if intrinsic is None or intrinsic <= 0:
        return None
    rc = dfv.get("reinvestmentCheck") or {}
    rd = dfv.get("reverseDcf")
    current = dfv.get("currentPrice")
    bridge: list[dict] = []
    if current is not None:
        bridge.append({"label": "현재가", "value": current})
    if intrinsic is not None:
        bridge.append({"label": "내재가치", "value": intrinsic})
    reverse = None
    if rd:
        reverse = {
            "impliedGrowth": rd.get("impliedGrowth"),
            "supportedGrowth": rd.get("supportedGrowth", rc.get("fundamentalGrowth")),
            "verdict": rd.get("verdict", ""),
        }
    return {
        "model": _MODEL_MAP.get(dfv.get("primaryModel", ""), dfv.get("primaryModel") or "unknown"),
        "intrinsic": intrinsic,
        "current": current,
        "wacc": (dfv.get("qualityWACC") or {}).get("adjustedWACC"),
        "waccBreakdown": {"rf": None, "erp": None, "beta": None, "costDebt": None, "taxRate": None, "weightE": None},
        "g": rc.get("fundamentalGrowth"),
        "reinvestRate": rc.get("reinvestRate"),
        "roic": rc.get("roic0"),
        "fadeYears": 8,
        "bridge": bridge,
        "reverseDcf": reverse,
    }


def _scenarioSet(dfv: dict) -> dict | None:
    """calcDFV 출력 → 계약 ScenarioSet(bear/base/bull 내재가치 + 현재가 대비 upside)."""
    scen = dfv.get("scenarios") or {}
    current = dfv.get("currentPrice")
    if not scen.get("base"):
        return None
    legs: list[dict] = []
    for key, label in (("bear", "약세"), ("base", "기본"), ("bull", "강세")):
        iv = scen.get(key)
        if iv is None:
            continue
        upside = round((iv - current) / current * 100, 1) if current else None
        legs.append(
            {
                "key": key,
                "label": label,
                "growth": None,
                "margin": None,
                "wacc": None,
                "intrinsic": iv,
                "upside": upside,
            }
        )
    if not legs:
        return None
    scenarioMethod = dfv.get("scenarioMethod") or {}
    method = scenarioMethod.get("method")
    if method == "driverSensitivity":
        note = "성장률·WACC 드라이버 민감도 기반 3개 시나리오."
    elif method == "arithmeticPercentBand":
        pct = scenarioMethod.get("percent")
        pctText = f"±{pct:g}%" if isinstance(pct, int | float) else "고정 비율"
        note = f"모델 드라이버 시나리오가 없어 base 가치에 {pctText} 산술 밴드를 적용한 근사치."
    else:
        note = "시나리오 생성 방법 메타데이터가 없어 성장·마진·WACC 교란으로 해석할 수 없음."
    return {
        "current": current,
        "legs": legs,
        "note": note,
    }


def _creditView(result: dict[str, Any] | None) -> dict | None:
    """이미 수집된 신용 대표 결과를 계약 CreditView 로 매핑한다.

    P1e 신용 라이브배선(02e): 구조화 신용 패킷(등급·축·PD·전망)을 valuationBridge 동형 pro 블록으로
    노출한다. 금융사·데이터부족은 None (graceful skip). 여기서는 엔진을 다시 호출하지 않고
    Story가 보관한 같은 세션 원본의 필드만 투영한다.
    """
    if not isinstance(result, dict) or not result.get("grade"):
        return None
    product = result.get("product") if isinstance(result.get("product"), dict) else {}
    confidence = product.get("confidence") if isinstance(product.get("confidence"), dict) else {}
    axes = [
        {"name": str(a.get("name") or a.get("label") or ""), "weight": a.get("weight"), "score": a.get("score")}
        for a in (result.get("axes") or [])
        if isinstance(a, dict)
    ]
    return {
        "grade": result.get("grade"),
        "gradeRaw": result.get("gradeRaw"),
        "score": result.get("score"),
        "healthScore": result.get("healthScore"),
        "pdEstimate": result.get("pdEstimate"),
        "outlook": result.get("outlook"),
        "investmentGrade": result.get("investmentGrade"),
        "axes": axes,
        "confidence": confidence.get("score"),
        "confidenceMethod": confidence.get("method") or "creditProduct",
    }


def _headlineKpis(card: Any, view: dict | None, credit: dict | None = None) -> list[dict]:
    """헤드라인 KPI: SummaryCard grades + 밸류에이션 콜 + 신용 등급."""
    kpis: list[dict] = []
    grades = getattr(card, "grades", {}) if card else {}
    for label, value in list(grades.items())[:4]:
        kpis.append({"label": str(label), "value": str(value)})
    if view and view.get("intrinsic"):
        kpis.append({"label": "내재가치", "value": f"{view['intrinsic']:,}원"})
    if credit and credit.get("gradeRaw"):
        kpis.append({"label": "신용등급", "value": str(credit["gradeRaw"])})
    return kpis


def _stockCode(company: Any) -> str:
    """Company 에서 종목코드 추출 (속성명 변종 방어)."""
    for attr in ("stockCode", "code", "corpCode"):
        val = getattr(company, attr, None)
        if val:
            return str(val)
    return ""


def buildReportModel(company: Any, perspective: str = "full", *, basePeriod: str | None = None) -> dict:
    """계약 ReportModel emitter - Story builders + de-gate 밸류에이션을 thesis-led 리포트로 조립.

    동작: buildStory 로 기존 분석 섹션/블록을 얻어 계약 블록으로 매핑(self-calc 0) → calcDFV
    de-gate 결과를 valuationBridge·scenario pro 블록 + 구조화 thesis 로 합성 → ReportModel
    dict(schemaVersion=2, camelCase) 반환. 모든 숫자는 L2 엔진 산출, story 는 엮기만.

    Args:
        company: dartlab Company 인스턴스 (dart/edgar).
        perspective: 리포트 관점 (full/valuation/credit/earnings/growth/... 기본 full).
        basePeriod: 재무기간 cutoff (None=최신). 공시 가용일·시장데이터 vintage까지
            고정하는 point-in-time 계약은 아니며, 해당 근거가 필요한 평가는 차단된다.

    Returns:
        dict: contracts/reportModel.ts ReportModel conform (schemaVersion=2). 데이터 부족 시
        {"skipped": True, "stockCode": ..., "reason": ...} (억지 채움 0).

    Example:
        >>> buildReportModel(dartlab.Company("005930"), "valuation")
        {"stockCode": "005930", "schemaVersion": 2, "thesis": {...}, "sections": [...]}

    Raises:
        없음 - 데이터 부족·빌드 실패는 skipped dict 로 반환.
    """
    code = _stockCode(company)
    try:
        from dartlab.story.registry import buildStory

        story = buildStory(company, type=perspective, basePeriod=basePeriod)
    except Exception as exc:  # noqa: BLE001 - emitter 는 never-raise, skip dict 반환
        return {"skipped": True, "stockCode": code, "reason": f"buildStory 실패: {str(exc)[:160]}"}
    if not story or not getattr(story, "sections", None):
        return {"skipped": True, "stockCode": code, "reason": "섹션 없음"}

    card = getattr(story, "summaryCard", None)
    bundle = getattr(story, "_lensBundle", {})
    lensProducts = getattr(story, "lensProducts", {})
    lensResults = bundle.get("results") if isinstance(bundle, dict) and isinstance(bundle.get("results"), dict) else {}

    dfv = None
    try:
        from dartlab.analysis.valuation.dFV import calcDFV

        dfv = calcDFV(company, basePeriod=basePeriod)
    except Exception:  # noqa: BLE001 - 밸류에이션 실패는 리포트 전체 실패 아님(pro 블록만 생략)
        dfv = None
    view = _valuationView(dfv) if dfv else None
    scenario = _scenarioSet(dfv) if dfv else None
    creditView = _creditView(lensResults.get("credit"))

    sections: list[dict] = []
    for sec in story.sections:
        blocks = [b for b in (_mapBlock(x) for x in getattr(sec, "blocks", [])) if b]
        if not blocks:
            continue
        sections.append(
            {
                "key": getattr(sec, "key", ""),
                "title": getattr(sec, "title", ""),
                "sourceEngine": "story",
                "blocks": blocks,
            }
        )

    if view or scenario:
        proBlocks: list[dict] = []
        if view:
            proBlocks.append({"type": "valuationBridge", "view": view})
        if scenario:
            proBlocks.append({"type": "scenario", "set": scenario})
        sections.append(
            {
                "key": "valuation",
                "title": "밸류에이션 - 내재가치와 시나리오",
                "sourceEngine": "valuation",
                "blocks": proBlocks,
                "arcStep": 7,
            }
        )

    if creditView:
        sections.append(
            {
                "key": "credit",
                "title": "신용: dCR 등급과 부도확률",
                "sourceEngine": "credit",
                "blocks": [{"type": "creditPanel", "view": creditView}],
                "arcStep": 8,
            }
        )

    from dartlab.story.thesis import buildThesis

    thesis = buildThesis(company, card, view, basePeriod=basePeriod)
    conclusion = getattr(card, "conclusion", "") if card else ""
    findings = [{"key": "thesis", "finding": conclusion, "sourceEngine": "story"}] if conclusion else []

    from dartlab.story.lensProducts import lensSummary, publicLensBundle

    lensRows = lensSummary(lensProducts)
    for row in lensRows:
        finding = row.get("summary") or row.get("label")
        if finding:
            findings.append(
                {
                    "key": f"lens.{row['engine']}",
                    "finding": str(finding),
                    "sourceEngine": row["engine"],
                }
            )

    engines: dict[str, dict] = {}
    for sec in sections:
        eng = sec["sourceEngine"]
        slot = engines.setdefault(eng, {"label": eng, "sections": 0, "blocks": 0})
        slot["sections"] += 1
        slot["blocks"] += len(sec["blocks"])
    for engine in lensProducts:
        engines.setdefault(engine, {"label": engine, "sections": 0, "blocks": 0})

    model: dict = {
        "stockCode": story.stockCode or code,
        "corpName": getattr(story, "corpName", ""),
        "asOf": basePeriod or "",
        "dataBasis": "DART/EDGAR 공시 + dartlab 분석 엔진",
        "perspectiveKey": perspective,
        "perspectiveLabel": _PERSPECTIVE_LABELS.get(perspective, perspective),
        "conclusion": conclusion,
        "headlineKpis": _headlineKpis(card, view, creditView),
        "narrativeOverview": conclusion,
        "keyFindings": findings,
        "sections": sections,
        "closing": [],
        "provenance": {
            "engines": engines,
            "note": "self-calc 0. 숫자와 렌즈 결론은 각 엔진 산출이며 Story는 엮기만 합니다.",
        },
        "assumptionsNote": "WACC 는 CAPM 추정(점추정), 성장은 재투자율×ROIC 펀더멘털 path. 가정 명시.",
        "qualityLabel": "conditional",
        "focusQuestions": [],
        "schemaVersion": 2,
        "lensSummary": lensRows,
    }
    publicBundle = publicLensBundle(bundle)
    if publicBundle is not None:
        model["lensProducts"] = publicBundle
    if thesis:
        model["thesis"] = thesis
    return model


__all__ = ["buildReportModel"]
