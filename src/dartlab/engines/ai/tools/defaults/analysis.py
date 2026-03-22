"""분석 도구 — insight/sector/rank + Excel export."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any


def register_analysis_tools(company: Any, register_tool) -> None:
    """분석 엔진 + Excel export 도구를 등록한다."""

    # ── get_insight ──

    def get_insight() -> str:
        stockCode = getattr(company, "stockCode", None)
        if not stockCode:
            return "종목코드가 없어 인사이트 분석을 실행할 수 없습니다."
        try:
            from dartlab.engines.analysis.insight import analyze

            result = analyze(stockCode, company=company)
            if result is None:
                return "재무 데이터 부족으로 인사이트 분석을 수행할 수 없습니다."
            grades = result.grades()
            lines = [f"프로파일: {result.profile}", ""]
            lines.append("| 영역 | 등급 | 요약 |")
            lines.append("| --- | --- | --- |")
            areaMap = {
                "performance": "실적",
                "profitability": "수익성",
                "health": "건전성",
                "cashflow": "현금흐름",
                "governance": "지배구조",
                "risk": "리스크",
                "opportunity": "기회",
            }
            for key, label in areaMap.items():
                ir = getattr(result, key, None)
                grade = grades.get(key, "N")
                summary = ir.summary if ir else "-"
                lines.append(f"| {label} | {grade} | {summary} |")
            if result.anomalies:
                lines.append("")
                for a in result.anomalies[:5]:
                    lines.append(f"- [{a.severity}] {a.text}")
            if result.summary:
                lines.append(f"\n{result.summary}")
            return "\n".join(lines)
        except ImportError:
            return "insight 엔진을 불러올 수 없습니다."

    register_tool(
        "get_insight",
        get_insight,
        "기업의 7영역 인사이트 종합 분석을 실행합니다. "
        "영역: 실적, 수익성, 재무건전성, 현금흐름, 지배구조, 리스크, 기회 (각각 A~F 등급). "
        "프로파일: premium/growth/stable/caution/distress 분류. 이상치 자동 탐지 포함. "
        "사용 시점: 종합 분석, '이 회사 어때?', 투자 판단 근거가 필요할 때. "
        "사용하지 말 것: 특정 재무 수치만 필요하면 get_data/compute_ratios가 빠릅니다.",
        {"type": "object", "properties": {}},
    )

    # ── get_sector_info ──

    def get_sector_info() -> str:
        try:
            from dartlab.engines.analysis.sector import classify, getParams

            corpName = getattr(company, "corpName", "")
            overview = company.show("companyOverview") if hasattr(company, "show") else None
            kindIndustry = None
            if isinstance(overview, dict):
                kindIndustry = overview.get("indutyName")
            detail = company.show("companyOverviewDetail") if hasattr(company, "show") else None
            mainProducts = None
            if isinstance(detail, dict):
                mainProducts = detail.get("mainBusiness")
            info = classify(corpName, kindIndustry=kindIndustry, mainProducts=mainProducts)
            params = getParams(info)
            lines = [
                f"대분류: {info.sector.value}",
                f"중분류: {info.industryGroup.value}",
                f"분류근거: {info.source} (신뢰도 {info.confidence:.0%})",
            ]
            if params:
                lines.append(f"섹터 기준 PER: {params.perMultiple}배")
                lines.append(f"섹터 기준 PBR: {params.pbrMultiple}배")
                lines.append(f"할인율: {params.discountRate}%")
                lines.append(f"성장률: {params.growthRate}%")
            return "\n".join(lines)
        except ImportError:
            return "sector 엔진을 불러올 수 없습니다."

    register_tool(
        "get_sector_info",
        get_sector_info,
        "기업의 WICS 섹터 분류(대/중분류)와 섹터 기준 밸류에이션(PER, PBR, 할인율)을 조회합니다. "
        "사용 시점: 업종 비교, 밸류에이션 판단, '동종업계 대비 어때?' 질문. "
        "사용하지 말 것: 기업 자체 재무비율은 compute_ratios를 사용하세요.",
        {"type": "object", "properties": {}},
    )

    # ── get_rank ──

    def get_rank_info() -> str:
        stockCode = getattr(company, "stockCode", None)
        if not stockCode:
            return "종목코드가 없습니다."
        try:
            from dartlab.engines.analysis.rank import getRank

            rank = getRank(stockCode)
            if rank is None:
                return "순위 데이터가 없습니다. (rank snapshot 미생성)"
            lines = []
            if rank.revenueRank is not None:
                lines.append(f"매출 순위(전체): {rank.revenueRank}/{rank.revenueTotal}")
            if rank.assetRank is not None:
                lines.append(f"자산 순위(전체): {rank.assetRank}/{rank.assetTotal}")
            if rank.growthRank is not None:
                lines.append(f"성장률 순위(전체): {rank.growthRank}/{rank.growthTotal}")
            if rank.revenueRankInSector is not None:
                lines.append(f"매출 순위({rank.sector}): {rank.revenueRankInSector}/{rank.revenueSectorTotal}")
            if rank.sizeClass:
                lines.append(f"규모 분류: {rank.sizeClass}")
            return "\n".join(lines) if lines else "순위 데이터가 비어있습니다."
        except ImportError:
            return "rank 엔진을 불러올 수 없습니다."

    register_tool(
        "get_rank",
        get_rank_info,
        "기업의 전체 시장 및 섹터 내 규모 순위를 조회합니다. "
        "매출/자산/성장률 순위와 상위 %를 반환. 규모 분류(대형/중형/소형) 포함. "
        "사용 시점: 시장 내 위치 파악, '이 회사 규모가 어느 정도야?' 질문. "
        "사용하지 말 것: 재무 수치 자체가 필요하면 get_data를 사용하세요.",
        {"type": "object", "properties": {}},
    )

    # ── Excel export ──

    def export_to_excel(modules: str = "") -> str:
        import tempfile

        from dartlab.export.excel import exportToExcel, listAvailableModules

        modList = [m.strip() for m in modules.split(",") if m.strip()] or None
        safeName = company.corpName.replace("/", "_").replace("\\", "_")
        outPath = Path(tempfile.gettempdir()) / f"{company.stockCode}_{safeName}.xlsx"

        exportToExcel(company, outputPath=outPath, modules=modList)
        available = listAvailableModules(company)
        modDesc = ", ".join(m["label"] for m in available) if not modList else ", ".join(modList)
        return f"Excel 파일 생성 완료: {outPath}\n포함 시트: {modDesc}"

    register_tool(
        "export_to_excel",
        export_to_excel,
        "기업 데이터를 Excel(.xlsx) 파일로 내보냅니다. "
        "modules: 쉼표 구분 시트 선택 (IS,BS,CF,ratios,dividend,audit,employee,executive 등 Company의 모든 property). "
        "비워두면 데이터가 있는 모든 모듈 자동 포함.",
        {
            "type": "object",
            "properties": {
                "modules": {
                    "type": "string",
                    "description": "포함할 시트 (쉼표 구분, 예: 'IS,BS,ratios,dividend'). 비워두면 전체.",
                    "default": "",
                },
            },
        },
    )

    def create_template(name: str, sheets_json: str) -> str:
        from dartlab.export.store import TemplateStore
        from dartlab.export.template import ExcelTemplate, SheetSpec

        try:
            sheets_data = json.loads(sheets_json)
        except json.JSONDecodeError:
            return 'sheets_json 파싱 오류. JSON 배열 형태로 입력하세요. 예: [{"source":"IS","label":"손익"}]'
        sheets = [SheetSpec(**s) for s in sheets_data]
        tmpl = ExcelTemplate(name=name, sheets=sheets)
        store = TemplateStore()
        tid = store.save(tmpl)
        sheetNames = ", ".join(s.label for s in sheets)
        return f"템플릿 '{name}' 생성 완료 (ID: {tid})\n시트: {sheetNames}"

    register_tool(
        "create_template",
        create_template,
        "Excel 내보내기 템플릿을 생성합니다. "
        "시트 구성을 JSON으로 정의하면 저장되어 다음에도 재사용 가능합니다. "
        "프리셋: preset_full(전체), preset_summary(요약), preset_governance(지배구조).",
        {
            "type": "object",
            "properties": {
                "name": {
                    "type": "string",
                    "description": "템플릿 이름 (예: '내 분석 양식')",
                },
                "sheets_json": {
                    "type": "string",
                    "description": '시트 목록 JSON. 예: [{"source":"IS","label":"손익계산서"},{"source":"BS"},{"source":"dividend"}]',
                },
            },
            "required": ["name", "sheets_json"],
        },
    )

    def export_with_template(template_id: str) -> str:
        import tempfile

        from dartlab.export.excel import exportWithTemplate
        from dartlab.export.store import TemplateStore

        store = TemplateStore()
        tmpl = store.get(template_id)
        if tmpl is None:
            available = store.list()
            avail_str = ", ".join(f"{t.templateId}({t.name})" for t in available)
            return f"템플릿 '{template_id}'을 찾을 수 없습니다. 사용 가능: {avail_str}"

        safeName = company.corpName.replace("/", "_").replace("\\", "_")
        templateSafe = tmpl.name.replace("/", "_").replace("\\", "_")
        outPath = Path(tempfile.gettempdir()) / f"{company.stockCode}_{safeName}_{templateSafe}.xlsx"

        exportWithTemplate(company, tmpl, outPath)
        return f"Excel 파일 생성 완료: {outPath}\n템플릿: {tmpl.name} ({len(tmpl.sheets)}개 시트)"

    register_tool(
        "export_with_template",
        export_with_template,
        "저장된 템플릿으로 Excel 파일을 생성합니다. "
        "템플릿 ID 예시: preset_full(전체), preset_summary(요약), preset_governance(지배구조). "
        "사용자가 만든 커스텀 템플릿도 ID로 사용 가능합니다.",
        {
            "type": "object",
            "properties": {
                "template_id": {
                    "type": "string",
                    "description": "사용할 템플릿 ID (예: preset_full, preset_summary, t_1234567890)",
                },
            },
            "required": ["template_id"],
        },
    )

    def list_templates() -> str:
        from dartlab.export.store import TemplateStore

        store = TemplateStore()
        templates = store.list()
        if not templates:
            return "저장된 템플릿이 없습니다."
        lines = ["| ID | 이름 | 시트 수 | 설명 |", "| --- | --- | --- | --- |"]
        for t in templates:
            lines.append(f"| `{t.templateId}` | {t.name} | {len(t.sheets)} | {t.description or '-'} |")
        return "\n".join(lines)

    register_tool(
        "list_templates",
        list_templates,
        "저장된 Excel 내보내기 템플릿 목록을 조회합니다. 프리셋과 사용자 커스텀 템플릿을 모두 포함합니다.",
        {"type": "object", "properties": {}},
    )
