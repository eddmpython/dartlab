"""전문 리포트 계약 emitter - Story(기존 builders) → ReportModel(contracts/reportModel.ts conform).

사상: story 는 L3 조합기다. 숫자는 전부 L2 엔진(buildStory builders·analysis.valuation calcDFV)이
계산하고, 본 모듈은 결과를 계약 블록으로 *엮기*만 한다(self-calc 0). thesis-led 아크 - 결론(thesis)을
최상단에, 기존 분석 섹션을 본문에, de-gate 밸류에이션(내재가치 bridge·시나리오)을 pro 블록으로.
현재 계약은 ``docs/handbook/architecture/analysisProducts.md``에 정리돼 있다.

L계층: story=L3, valuation=L2 → L2 를 함수 내부 lazy import(import 방향 L2→L3 준수).
"""

from __future__ import annotations

from typing import Any

_PERSPECTIVE_LABELS = {
    "investment": "투자 의사결정",
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
        to_dicts = getattr(df, "to_dicts", None)
        raw_rows = to_dicts() if callable(to_dicts) else []
        rows = raw_rows if isinstance(raw_rows, list) and all(isinstance(row, dict) for row in raw_rows) else []
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
    scenarioMethod = dfv.get("scenarioMethod") or {}
    drivers = scenarioMethod.get("drivers") if isinstance(scenarioMethod.get("drivers"), dict) else {}
    for key, label in (("bear", "약세"), ("base", "기본"), ("bull", "강세")):
        iv = scen.get(key)
        if iv is None:
            continue
        legDrivers = drivers.get(key) if isinstance(drivers.get(key), dict) else {}
        upside = round((iv - current) / current * 100, 1) if current else None
        legs.append(
            {
                "key": key,
                "label": label,
                "growth": legDrivers.get("growthMult"),
                "margin": None,
                "wacc": legDrivers.get("wacc"),
                "intrinsic": iv,
                "upside": upside,
            }
        )
    if not legs:
        return None
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
    raw_product = result.get("product")
    product: dict[str, Any] = raw_product if isinstance(raw_product, dict) else {}
    from dartlab.story.lensProducts import isLensProductPromotable

    if not isLensProductPromotable(product):
        return None
    raw_confidence = product.get("confidence")
    confidence: dict[str, Any] = raw_confidence if isinstance(raw_confidence, dict) else {}
    axes = [
        {"name": str(a.get("name") or a.get("label") or ""), "weight": a.get("weight"), "score": a.get("score")}
        for a in (result.get("axes") or [])
        if isinstance(a, dict)
    ]
    return {
        "status": "usable",
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
    if credit and credit.get("status") == "usable" and credit.get("gradeRaw"):
        kpis.append({"label": "신용등급", "value": str(credit["gradeRaw"])})
    return kpis


def _stockCode(company: Any) -> str:
    """Company 에서 종목코드 추출 (속성명 변종 방어)."""
    for attr in ("stockCode", "code", "corpCode"):
        val = getattr(company, attr, None)
        if val:
            return str(val)
    return ""


def _buildInvestmentReportModel(company: Any, *, basePeriod: str | None = None) -> dict:
    """범용 Story 문서 빌드를 우회하는 결정 중심 투자 브리프."""
    from dartlab.story.investmentMemo import buildInvestmentDecision
    from dartlab.story.lensProducts import (
        collectLensProducts,
        enginesForReportType,
        lensSummary,
        publicLensBundle,
    )
    from dartlab.story.reportTypes import REPORT_TYPES
    from dartlab.story.thesis import buildThesis

    code = _stockCode(company)
    bundle = collectLensProducts(
        company,
        engines=enginesForReportType("investment"),
        basePeriod=basePeriod,
    )
    publicBundle = publicLensBundle(bundle)
    products = publicBundle.get("products") if isinstance(publicBundle, dict) else bundle.get("products", {})
    tensions = publicBundle.get("tensions") if isinstance(publicBundle, dict) else bundle.get("tensions", {})
    lensRows = lensSummary(products)

    dfv = None
    try:
        from dartlab.analysis.valuation.dFV import calcDFV

        dfv = calcDFV(company, basePeriod=basePeriod)
    except Exception:  # noqa: BLE001 - 한 모델 실패를 전체 브리프 실패로 위장하지 않는다.
        pass
    view = _valuationView(dfv) if dfv else None
    scenario = _scenarioSet(dfv) if dfv else None
    thesis = buildThesis(company, None, view, basePeriod=basePeriod)
    decision = buildInvestmentDecision(
        thesis=thesis,
        lensProducts=products,
        lensTensions=tensions,
        valuation=view,
        scenarios=scenario,
        asOf=basePeriod,
        gaps=bundle.get("gaps") or [],
    )

    central = str((thesis or {}).get("central") or "")
    findings: list[dict[str, str]] = []
    if central:
        findings.append({"key": "thesis", "finding": central, "sourceEngine": "story"})
    for row in lensRows:
        finding = row.get("summary") or row.get("label")
        if finding:
            findings.append(
                {
                    "key": f"lens.{row['engine']}",
                    "finding": str(finding),
                    "sourceEngine": str(row["engine"]),
                }
            )

    sections: list[dict[str, Any]] = []
    decisionBlocks = [
        {"type": "text", "text": text} for text in (central, str((thesis or {}).get("bearCase") or "")) if text
    ]
    if decisionBlocks:
        sections.append(
            {
                "key": "investmentDecision",
                "title": "투자 판단과 반대논지",
                "sourceEngine": "story",
                "blocks": decisionBlocks,
                "arcStep": 1,
            }
        )
    proBlocks: list[dict[str, Any]] = []
    if view:
        proBlocks.append({"type": "valuationBridge", "view": view})
    if scenario:
        proBlocks.append({"type": "scenario", "set": scenario})
    if proBlocks:
        sections.append(
            {
                "key": "valuation",
                "title": "가격에 반영된 기대와 시나리오",
                "sourceEngine": "valuation",
                "blocks": proBlocks,
                "arcStep": 2,
            }
        )

    engines = {
        str(engine): {"label": str(engine), "sections": 0, "blocks": 0} for engine in bundle.get("engines") or []
    }
    engines["story"] = {"label": "story", "sections": int(bool(decisionBlocks)), "blocks": len(decisionBlocks)}
    if proBlocks:
        engines["valuation"] = {"label": "valuation", "sections": 1, "blocks": len(proBlocks)}

    model: dict[str, Any] = {
        "stockCode": code,
        "corpName": str(getattr(company, "corpName", "") or ""),
        "asOf": decision.get("asOf") or basePeriod or "",
        "dataBasis": "DART/EDGAR 공시 + dartlab 분석 엔진",
        "perspectiveKey": "investment",
        "perspectiveLabel": _PERSPECTIVE_LABELS["investment"],
        "conclusion": central,
        "headlineKpis": _headlineKpis(None, view, None),
        "narrativeOverview": central,
        "keyFindings": findings,
        "sections": sections,
        "closing": [
            {"label": "판단 상태", "engine": "story", "line": decision["decisionStatus"]},
            {"label": "다음 확인", "engine": "story", "line": decision["summary"]["nextCheck"]},
        ],
        "provenance": {
            "engines": engines,
            "status": decision["decisionStatus"],
            "note": "대표 렌즈와 구조화 가치평가를 한 번씩 조합한 투자 의사결정 브리프입니다.",
        },
        "assumptionsNote": "WACC·성장·시나리오 가정은 valuation 및 scenarios 세부 필드에 공개됩니다.",
        "qualityLabel": decision["evidenceStrength"],
        "focusQuestions": list(REPORT_TYPES["investment"].focusQuestions),
        "schemaVersion": 2,
        "lensSummary": lensRows,
        "gaps": decision["gaps"],
        "thesis": thesis,
        "investmentDecision": decision,
    }
    if publicBundle is not None:
        model["lensProducts"] = publicBundle
    return model


def _storyReportSections(story: Any, view: dict | None, scenario: dict | None, creditView: dict | None) -> list[dict]:
    """Story 블록과 선택적 valuation, credit 제품을 계약 섹션으로 조립한다."""
    sections: list[dict] = []
    for section in story.sections:
        blocks = [block for block in (_mapBlock(item) for item in getattr(section, "blocks", [])) if block]
        if blocks:
            sections.append(
                {
                    "key": getattr(section, "key", ""),
                    "title": getattr(section, "title", ""),
                    "sourceEngine": "story",
                    "blocks": blocks,
                }
            )
    proBlocks = ([{"type": "valuationBridge", "view": view}] if view else []) + (
        [{"type": "scenario", "set": scenario}] if scenario else []
    )
    if proBlocks:
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
    return sections


def _storyReportFindings(card: Any, lensRows: list[dict[str, Any]]) -> tuple[str, list[dict[str, Any]]]:
    """요약 결론과 렌즈별 발견을 동일 공개 구조로 정규화한다."""
    conclusion = getattr(card, "conclusion", "") if card else ""
    findings = [{"key": "thesis", "finding": conclusion, "sourceEngine": "story"}] if conclusion else []
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
    return conclusion, findings


def _storyReportEngines(sections: list[dict], lensProducts: dict[str, Any]) -> dict[str, dict]:
    """섹션과 렌즈 제품에서 provenance 엔진 사용량을 집계한다."""
    engines: dict[str, dict] = {}
    for section in sections:
        engine = section["sourceEngine"]
        slot = engines.setdefault(engine, {"label": engine, "sections": 0, "blocks": 0})
        slot["sections"] += 1
        slot["blocks"] += len(section["blocks"])
    for engine in lensProducts:
        engines.setdefault(engine, {"label": engine, "sections": 0, "blocks": 0})
    return engines


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
    if perspective in {"investment", "invest", "투자", "투자분석"}:
        return _buildInvestmentReportModel(company, basePeriod=basePeriod)
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
    raw_lens_results = bundle.get("results") if isinstance(bundle, dict) else None
    lensResults: dict[str, Any] = raw_lens_results if isinstance(raw_lens_results, dict) else {}

    dfv = None
    try:
        from dartlab.analysis.valuation.dFV import calcDFV

        dfv = calcDFV(company, basePeriod=basePeriod)
    except Exception:  # noqa: BLE001 - 밸류에이션 실패는 리포트 전체 실패 아님(pro 블록만 생략)
        dfv = None
    view = _valuationView(dfv) if dfv else None
    scenario = _scenarioSet(dfv) if dfv else None
    creditView = _creditView(lensResults.get("credit"))
    sections = _storyReportSections(story, view, scenario, creditView)

    from dartlab.story.thesis import buildThesis

    thesis = buildThesis(company, card, view, basePeriod=basePeriod)

    from dartlab.story.lensProducts import lensSummary, publicLensBundle

    lensRows = lensSummary(lensProducts)
    conclusion, findings = _storyReportFindings(card, lensRows)
    engines = _storyReportEngines(sections, lensProducts)

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
            "status": "partial",
            "note": "엔진별 근거는 보존하지만 기존 일반 블록의 값 단위 ref는 아직 완전하지 않습니다.",
        },
        "assumptionsNote": "WACC 는 CAPM 추정(점추정), 성장은 재투자율×ROIC 펀더멘털 path. 가정 명시.",
        "qualityLabel": "partial",
        "focusQuestions": [],
        "schemaVersion": 2,
        "lensSummary": lensRows,
        "gaps": list(getattr(story, "lensGaps", [])),
    }
    publicBundle = publicLensBundle(bundle)
    if publicBundle is not None:
        model["lensProducts"] = publicBundle
    if thesis:
        model["thesis"] = thesis
    return model


__all__ = ["buildReportModel"]
