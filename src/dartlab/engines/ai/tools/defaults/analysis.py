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
        category="analysis",
        questionTypes=("건전성", "수익성", "리스크", "종합"),
        priority=85,
    )

    # ── run_audit ──

    def run_audit() -> str:
        """감사 Red Flag 분석."""
        stockCode = getattr(company, "stockCode", None)
        if not stockCode:
            return "종목코드가 없어 감사 분석을 실행할 수 없습니다."
        try:
            import dartlab as _dl

            result = _dl.audit(stockCode)
            if result is None:
                return "감사 분석 데이터가 부족합니다."
            if hasattr(result, "height"):  # DataFrame
                from .helpers import df_to_md

                return df_to_md(result, max_rows=30)
            return str(result)[:4000]
        except (ImportError, KeyError, OSError, RuntimeError, TypeError, ValueError) as e:
            return f"감사 분석 실패: {e}"

    register_tool(
        "run_audit",
        run_audit,
        "감사 Red Flag 분석을 실행합니다. "
        "감사의견, 내부통제, 계속기업 가정, 우발채무, 관련 당사자 거래 등을 종합 점검합니다. "
        "사용 시점: '감사 이슈', '리스크 총점검', '내부통제 문제', '부실 징후' 질문. "
        "사용하지 말 것: 일반적인 재무비율 분석에는 compute_ratios가 적절합니다.",
        {"type": "object", "properties": {}},
        category="analysis",
        questionTypes=("리스크", "종합"),
        priority=75,
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
        category="analysis",
        questionTypes=("투자", "종합"),
        priority=70,
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
        category="analysis",
        questionTypes=("종합",),
        priority=60,
    )

    # ── get_esg ──

    def get_esg() -> str:
        """ESG 3축 분석."""
        try:
            from dartlab.engines.analysis.esg.extractor import analyze_esg

            result = analyze_esg(company)
            if result is None:
                return "ESG 분석에 필요한 공시 데이터가 부족합니다."
            lines = [
                f"종합: {result.totalGrade} ({result.totalScore:.0f}점)",
                "",
                "| 축 | 등급 | 점수 | 상세 |",
                "| --- | --- | --- | --- |",
            ]
            for pillar in (result.environment, result.social, result.governance):
                detail = pillar.details[0] if pillar.details else "-"
                lines.append(f"| {pillar.label} | {pillar.grade} | {pillar.score:.0f} | {detail} |")
            return "\n".join(lines)
        except (ImportError, AttributeError, TypeError, ValueError) as e:
            return f"ESG 분석 실패: {e}"

    register_tool(
        "get_esg",
        get_esg,
        "ESG(환경·사회·지배구조) 3축 종합 분석을 실행합니다. "
        "각 축별 점수(0~100)와 등급(A~E), 가중평균 종합 등급을 반환합니다. "
        "사용 시점: 'ESG 평가', '환경 리스크', '지배구조 어때?', '사회적 책임' 질문. "
        "사용하지 말 것: 재무 건전성은 get_insight가 적절합니다.",
        {"type": "object", "properties": {}},
        category="analysis",
        questionTypes=("ESG", "리스크", "지배구조", "종합"),
        priority=70,
    )

    # ── get_supply_chain ──

    def get_supply_chain() -> str:
        """공급망 분석."""
        try:
            from dartlab.engines.analysis.supply.risk import analyze_supply_chain

            result = analyze_supply_chain(company)
            if result is None:
                return "공급망 분석에 필요한 공시 데이터가 부족합니다."
            lines = [
                f"공급망 리스크: {result.riskScore:.0f}점 / 매출 집중도(HHI): {result.concentration:.2f}",
                "",
            ]
            if result.customers:
                lines.append("**주요 고객:**")
                for c in result.customers[:5]:
                    lines.append(f"- {c.target} (신뢰도 {c.confidence:.0%})")
            if result.suppliers:
                lines.append("**주요 공급사:**")
                for s in result.suppliers[:5]:
                    lines.append(f"- {s.target} (신뢰도 {s.confidence:.0%})")
            if result.riskFactors:
                lines.append("**리스크 요인:**")
                for rf in result.riskFactors[:3]:
                    lines.append(f"- {rf}")
            return "\n".join(lines)
        except (ImportError, AttributeError, TypeError, ValueError) as e:
            return f"공급망 분석 실패: {e}"

    register_tool(
        "get_supply_chain",
        get_supply_chain,
        "기업의 공급망 구조와 리스크를 분석합니다. "
        "주요 고객/공급사 목록, 매출 집중도(HHI), 공급망 리스크 점수를 반환합니다. "
        "사용 시점: '공급망 리스크', '고객 집중도', '주요 거래처', '공급사 의존' 질문. "
        "사용하지 말 것: 매출 구성 자체는 get_data('segments')가 적절합니다.",
        {"type": "object", "properties": {}},
        category="analysis",
        questionTypes=("공급망", "사업", "리스크", "종합"),
        priority=65,
    )

    # ── get_disclosure_changes ──

    def get_disclosure_changes(topic: str = "") -> str:
        """공시 변화 감지."""
        try:
            from dartlab.engines.analysis.watch.scanner import scan_company

            result = scan_company(company, topic=topic or None)
            if result is None:
                return "공시 변화 감지에 필요한 sections 데이터가 부족합니다."
            if not result.scored:
                return "최근 공시에서 유의미한 변화가 감지되지 않았습니다."
            lines = ["| 순위 | 항목 | 중요도 | 변화율 |", "| --- | --- | --- | --- |"]
            for i, sc in enumerate(result.scored[:10], 1):
                lines.append(f"| {i} | {sc.topic} | {sc.score:.0f}점 | {sc.changeRate:.0%} |")
            return "\n".join(lines)
        except (ImportError, AttributeError, TypeError, ValueError) as e:
            return f"공시 변화 감지 실패: {e}"

    register_tool(
        "get_disclosure_changes",
        get_disclosure_changes,
        "최근 공시에서 무엇이 바뀌었는지 중요도 순으로 보여줍니다. "
        "sections diff + 중요도 스코어링(0~100)으로 주목할 변화를 탐지합니다. "
        "사용 시점: '뭐가 바뀌었어?', '최근 변화', '공시 변경 사항', '주목할 부분' 질문. "
        "topic 파라미터로 특정 항목(예: 'riskManagement')만 필터 가능.",
        {
            "type": "object",
            "properties": {
                "topic": {
                    "type": "string",
                    "description": "특정 topic 필터 (비워두면 전체 스캔)",
                    "default": "",
                },
            },
        },
        category="analysis",
        questionTypes=("변화", "공시", "리스크", "종합"),
        priority=65,
    )

    # ── run_valuation ──

    def run_valuation() -> str:
        """종합 밸류에이션."""
        stockCode = getattr(company, "stockCode", None)
        if not stockCode:
            return "종목코드가 없어 밸류에이션을 실행할 수 없습니다."
        try:
            from dartlab.engines.analysis.analyst.valuation import fullValuation

            result = fullValuation(company)
            if result is None:
                return "밸류에이션에 필요한 재무 데이터가 부족합니다."
            if isinstance(result, dict):
                lines = []
                if "targetPrice" in result:
                    lines.append(f"목표 주가: {result['targetPrice']:,.0f}원")
                if "methods" in result:
                    lines.append("")
                    for method in result["methods"]:
                        name = method.get("name", "")
                        value = method.get("value", 0)
                        weight = method.get("weight", 0)
                        lines.append(f"- {name}: {value:,.0f}원 (가중 {weight:.0%})")
                return "\n".join(lines) if lines else str(result)[:3000]
            return str(result)[:3000]
        except (ImportError, AttributeError, TypeError, ValueError, ZeroDivisionError) as e:
            return f"밸류에이션 실패: {e}"

    register_tool(
        "run_valuation",
        run_valuation,
        "DCF, DDM, 상대가치(PER/PBR) 등 다중 모델로 적정 주가를 산출합니다. "
        "각 모델의 산출 근거와 가중평균 목표가를 반환합니다. "
        "사용 시점: '적정 주가', '목표가', 'DCF', '밸류에이션', '저평가/고평가' 질문. "
        "사용하지 말 것: 단순 PER/PBR 비율은 compute_ratios가 빠릅니다.",
        {"type": "object", "properties": {}},
        category="analysis",
        questionTypes=("밸류에이션", "투자", "종합"),
        priority=75,
    )

    # ── run_forecast ──

    def run_forecast_tool() -> str:
        """실적 예측."""
        try:
            from dartlab.engines.analysis.analyst.forecast import forecastAll

            result = forecastAll(company)
            if result is None:
                return "실적 예측에 필요한 데이터가 부족합니다."
            if isinstance(result, dict):
                lines = ["| 지표 | 예측값 | 성장률 |", "| --- | --- | --- |"]
                for metric, data in result.items():
                    if isinstance(data, dict):
                        value = data.get("forecast", data.get("value", "-"))
                        growth = data.get("growth", "-")
                        if isinstance(value, (int, float)):
                            value = f"{value:,.0f}"
                        if isinstance(growth, float):
                            growth = f"{growth:+.1%}"
                        lines.append(f"| {metric} | {value} | {growth} |")
                return "\n".join(lines) if len(lines) > 2 else str(result)[:3000]
            return str(result)[:3000]
        except (ImportError, AttributeError, TypeError, ValueError) as e:
            return f"실적 예측 실패: {e}"

    register_tool(
        "run_forecast",
        run_forecast_tool,
        "매출, 영업이익, 순이익의 향후 실적을 예측합니다. "
        "과거 추세와 성장률 기반으로 3년 예측치와 성장률을 반환합니다. "
        "사용 시점: '향후 실적', '매출 전망', '이익 예측', '성장 가능성' 질문.",
        {"type": "object", "properties": {}},
        category="analysis",
        questionTypes=("밸류에이션", "성장성", "투자"),
        priority=70,
    )

    # ── run_stress_test ──

    def run_stress_test_tool() -> str:
        """스트레스 테스트."""
        try:
            from dartlab.engines.analysis.analyst.simulation import stressTest

            result = stressTest(company)
            if result is None:
                return "스트레스 테스트에 필요한 데이터가 부족합니다."
            return str(result)[:3000]
        except (ImportError, AttributeError, TypeError, ValueError) as e:
            return f"스트레스 테스트 실패: {e}"

    register_tool(
        "run_stress_test",
        run_stress_test_tool,
        "경기침체, 금리 상승, 매출 급감 등 극단 시나리오에서의 재무 영향을 시뮬레이션합니다. "
        "사용 시점: '위기 상황', '스트레스 테스트', '최악의 경우', '충격 시나리오' 질문.",
        {"type": "object", "properties": {}},
        category="analysis",
        questionTypes=("리스크", "투자"),
        priority=55,
    )

    # ── run_monte_carlo ──

    def run_monte_carlo_tool() -> str:
        """몬테카를로 시뮬레이션."""
        try:
            from dartlab.engines.analysis.analyst.simulation import monteCarloForecast

            result = monteCarloForecast(company)
            if result is None:
                return "몬테카를로 시뮬레이션에 필요한 데이터가 부족합니다."
            return str(result)[:3000]
        except (ImportError, AttributeError, TypeError, ValueError) as e:
            return f"몬테카를로 시뮬레이션 실패: {e}"

    register_tool(
        "run_monte_carlo",
        run_monte_carlo_tool,
        "확률적 시뮬레이션으로 매출/이익의 분포와 신뢰구간을 추정합니다. "
        "사용 시점: '확률 분석', '몬테카를로', '시뮬레이션', '불확실성' 질문.",
        {"type": "object", "properties": {}},
        category="analysis",
        questionTypes=("밸류에이션", "리스크"),
        priority=50,
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
        category="export",
        priority=40,
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
        category="export",
        priority=30,
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
        category="export",
        priority=35,
        dependsOn=("list_templates",),
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
        category="export",
        priority=30,
    )
