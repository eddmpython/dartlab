"""DartLab 분석 도구 레지스트리 — OpenAI function calling 형식.

LLM 에이전트가 사용할 수 있는 도구를 등록·관리한다.
Company 인스턴스에 바인딩된 도구를 생성하여 tool calling에 사용.
"""

from __future__ import annotations

import json
from typing import Any, Callable

import polars as pl

_TOOL_REGISTRY: dict[str, dict[str, Any]] = {}


def register_tool(
	name: str,
	func: Callable[..., str],
	description: str,
	parameters: dict,
) -> None:
	"""도구 등록."""
	_TOOL_REGISTRY[name] = {
		"function": func,
		"schema": {
			"type": "function",
			"function": {
				"name": name,
				"description": description,
				"parameters": parameters,
			},
		},
	}


def get_tool_schemas() -> list[dict]:
	"""등록된 도구의 OpenAI function calling 스키마 목록."""
	return [t["schema"] for t in _TOOL_REGISTRY.values()]


def execute_tool(name: str, arguments: dict) -> str:
	"""도구 실행. 결과는 문자열(마크다운)로 반환."""
	if name not in _TOOL_REGISTRY:
		return f"오류: '{name}' 도구를 찾을 수 없습니다."
	try:
		return _TOOL_REGISTRY[name]["function"](**arguments)
	except Exception as e:
		return f"도구 실행 오류 ({name}): {e}"


def clear_registry() -> None:
	"""등록된 모든 도구 제거 (테스트용)."""
	_TOOL_REGISTRY.clear()


def _df_to_md(df: pl.DataFrame, max_rows: int = 15) -> str:
	"""DataFrame → 마크다운 테이블."""
	if df is None or df.height == 0:
		return "(데이터 없음)"

	from dartlab.engines.llmAnalyzer.context import df_to_markdown

	return df_to_markdown(df, max_rows=max_rows)


def register_defaults(company: Any) -> None:
	"""Company 인스턴스에 바인딩된 기본 분석 도구 등록."""
	clear_registry()

	# 0. list_modules: 사용 가능한 모듈 목록 조회
	def list_modules() -> str:
		from dartlab.engines.llmAnalyzer.context import scan_available_modules
		modules = scan_available_modules(company)
		if not modules:
			return "사용 가능한 데이터 모듈이 없습니다."
		lines = ["| 모듈명 | 설명 | 유형 | 행수 |", "| --- | --- | --- | --- |"]
		for m in modules:
			lines.append(f"| `{m['name']}` | {m['label']} | {m.get('type', '-')} | {m.get('rows', '-')} |")
		return "\n".join(lines)

	register_tool(
		"list_modules",
		list_modules,
		"이 기업에서 조회 가능한 모든 데이터 모듈 목록을 반환합니다. "
		"어떤 데이터가 있는지 모를 때 먼저 호출하세요.",
		{"type": "object", "properties": {}},
	)

	# 1. get_data: 파서 모듈 데이터 조회
	def get_data(module_name: str) -> str:
		data = getattr(company, module_name, None)
		if data is None:
			# 유사한 모듈명 제안
			from dartlab.engines.llmAnalyzer.metadata import MODULE_META
			suggestions = [
				f"`{n}` ({m.label})"
				for n, m in MODULE_META.items()
				if module_name.lower() in n.lower() or module_name.lower() in m.label.lower()
			]
			msg = f"'{module_name}' 데이터가 없습니다."
			if suggestions:
				msg += f" 유사한 모듈: {', '.join(suggestions[:5])}"
			msg += " `list_modules` 도구로 사용 가능한 모듈을 확인하세요."
			return msg
		if isinstance(data, pl.DataFrame):
			return _df_to_md(data)
		if isinstance(data, dict):
			return "\n".join(f"- {k}: {v}" for k, v in data.items())
		if isinstance(data, list):
			return "\n".join(f"- {item}" for item in data[:20])
		return str(data)[:2000]

	register_tool(
		"get_data",
		get_data,
		"기업의 재무/공시 데이터를 조회합니다. "
		"주요 module_name: "
		"BS(재무상태표), IS(손익계산서), CF(현금흐름표), fsSummary(재무요약), "
		"dividend(배당), audit(감사의견), majorHolder(최대주주), "
		"executive(임원), employee(직원), rnd(R&D), segment(사업부문), "
		"productService(주요제품), salesOrder(매출수주), "
		"bond(채무증권), shareCapital(주식현황), capitalChange(자본변동), "
		"contingentLiability(우발부채), sanction(제재현황), "
		"subsidiary(자회사투자), affiliateGroup(계열사), "
		"boardOfDirectors(이사회), executivePay(임원보수), "
		"tangibleAsset(유형자산), costByNature(비용성격별분류), "
		"riskDerivative(위험관리), internalControl(내부통제), "
		"business(사업의내용), mdna(MD&A), companyOverviewDetail(회사개요). "
		"모듈명을 모르면 먼저 `list_modules`를 호출하세요.",
		{
			"type": "object",
			"properties": {
				"module_name": {
					"type": "string",
					"description": "조회할 모듈명 (예: BS, IS, CF, dividend, audit, fsSummary)",
				},
			},
			"required": ["module_name"],
		},
	)

	# 1b. search_data: 키워드로 데이터 검색
	def search_data(keyword: str) -> str:
		"""모든 모듈을 검색하여 키워드와 관련된 데이터를 찾습니다."""
		from dartlab.engines.llmAnalyzer.metadata import MODULE_META
		results = []
		keyword_lower = keyword.lower()

		for name, meta in MODULE_META.items():
			try:
				data = getattr(company, name, None)
				if data is None:
					continue
				if isinstance(data, pl.DataFrame) and data.height > 0:
					# 컬럼명에서 검색
					matched_cols = [c for c in data.columns if keyword_lower in c.lower()]
					# 계정명 컬럼에서 검색
					if "계정명" in data.columns:
						matched_rows = data.filter(
							pl.col("계정명").str.contains(f"(?i){keyword}")
						)
						if matched_rows.height > 0:
							results.append(f"### {meta.label} (`{name}`) — 계정명 매칭 {matched_rows.height}건")
							results.append(_df_to_md(matched_rows, max_rows=10))
					elif matched_cols:
						results.append(f"### {meta.label} (`{name}`) — 컬럼 매칭: {', '.join(matched_cols)}")
				elif isinstance(data, dict):
					matched_keys = [k for k in data if keyword_lower in str(k).lower() or keyword_lower in str(data[k]).lower()]
					if matched_keys:
						results.append(f"### {meta.label} (`{name}`)")
						for k in matched_keys[:5]:
							results.append(f"- {k}: {data[k]}")
			except Exception:
				continue

		if not results:
			return f"'{keyword}'와 관련된 데이터를 찾지 못했습니다. 다른 키워드를 시도하거나 `list_modules`로 사용 가능한 데이터를 확인하세요."
		return "\n\n".join(results)

	register_tool(
		"search_data",
		search_data,
		"키워드로 모든 데이터 모듈을 검색합니다. "
		"특정 계정과목(예: '매출액', '부채'), 지표명, 또는 컬럼명으로 검색합니다. "
		"어떤 모듈에 데이터가 있는지 모를 때 유용합니다.",
		{
			"type": "object",
			"properties": {
				"keyword": {
					"type": "string",
					"description": "검색할 키워드 (예: '매출', '부채비율', 'R&D', '이자비용')",
				},
			},
			"required": ["keyword"],
		},
	)

	# 2. compute_ratios: 재무비율 계산
	def compute_ratios() -> str:
		from dartlab.tools.table import ratio_table

		bs = getattr(company, "BS", None)
		is_ = getattr(company, "IS", None)
		if not isinstance(bs, pl.DataFrame) or not isinstance(is_, pl.DataFrame):
			return "BS 또는 IS 데이터가 없어 재무비율을 계산할 수 없습니다."
		result = ratio_table(bs, is_)
		return _df_to_md(result)

	register_tool(
		"compute_ratios",
		compute_ratios,
		"재무상태표(BS)와 손익계산서(IS)로 핵심 재무비율을 계산합니다. "
		"부채비율, 유동비율, 영업이익률, 순이익률, ROE, ROA를 연도별로 반환.",
		{"type": "object", "properties": {}},
	)

	# 3. detect_anomalies: 이상치 탐지
	def find_anomalies(module_name: str, threshold_pct: float = 50.0) -> str:
		from dartlab.engines.llmAnalyzer.aiParser import detect_anomalies

		data = getattr(company, module_name, None)
		if not isinstance(data, pl.DataFrame):
			return f"'{module_name}' DataFrame 데이터가 없습니다."
		anomalies = detect_anomalies(data, use_llm=False, threshold_pct=threshold_pct)
		if not anomalies:
			return f"'{module_name}'에서 이상치가 발견되지 않았습니다."
		lines = []
		for a in anomalies:
			lines.append(
				f"- [{a.severity}] {a.column} {a.year}: "
				f"{a.description} (변동 {a.change_pct:+.1f}%)"
			)
		return "\n".join(lines)

	register_tool(
		"detect_anomalies",
		find_anomalies,
		"재무 데이터에서 이상치(급격한 변동, 부호 반전)를 탐지합니다.",
		{
			"type": "object",
			"properties": {
				"module_name": {
					"type": "string",
					"description": "분석할 모듈명 (예: BS, IS, CF)",
				},
				"threshold_pct": {
					"type": "number",
					"description": "이상치 판정 기준 YoY 변동률 (기본 50%)",
					"default": 50.0,
				},
			},
			"required": ["module_name"],
		},
	)

	# 4. compute_growth: 성장률 매트릭스
	def compute_growth(module_name: str) -> str:
		from dartlab.tools.table import pivot_accounts, growth_matrix

		data = getattr(company, module_name, None)
		if not isinstance(data, pl.DataFrame):
			return f"'{module_name}' DataFrame 데이터가 없습니다."

		pivoted = pivot_accounts(data)
		if "year" not in pivoted.columns:
			return "연도 데이터가 부족하여 성장률을 계산할 수 없습니다."

		result = growth_matrix(pivoted)
		return _df_to_md(result)

	register_tool(
		"compute_growth",
		compute_growth,
		"다기간 CAGR(복합연간성장률) 매트릭스를 계산합니다. 1Y, 2Y, 3Y, 5Y 성장률 반환.",
		{
			"type": "object",
			"properties": {
				"module_name": {
					"type": "string",
					"description": "분석할 모듈명 (예: IS, dividend)",
				},
			},
			"required": ["module_name"],
		},
	)

	# 5. yoy_analysis: YoY 변동 분석
	def yoy_analysis(module_name: str) -> str:
		from dartlab.tools.table import pivot_accounts, yoy_change

		data = getattr(company, module_name, None)
		if not isinstance(data, pl.DataFrame):
			return f"'{module_name}' DataFrame 데이터가 없습니다."

		# 계정명 구조면 피벗
		if "계정명" in data.columns:
			data = pivot_accounts(data)

		if "year" not in data.columns:
			return "year 컬럼이 없어 YoY 분석을 할 수 없습니다."

		result = yoy_change(data)
		return _df_to_md(result)

	register_tool(
		"yoy_analysis",
		yoy_analysis,
		"데이터의 전년 대비(YoY) 변동률을 계산합니다.",
		{
			"type": "object",
			"properties": {
				"module_name": {
					"type": "string",
					"description": "분석할 모듈명 (예: IS, BS, dividend)",
				},
			},
			"required": ["module_name"],
		},
	)

	# 6. get_summary_stats: 요약 통계
	def get_summary(module_name: str) -> str:
		from dartlab.tools.table import pivot_accounts, summary_stats

		data = getattr(company, module_name, None)
		if not isinstance(data, pl.DataFrame):
			return f"'{module_name}' DataFrame 데이터가 없습니다."

		if "계정명" in data.columns:
			data = pivot_accounts(data)

		result = summary_stats(data)
		return _df_to_md(result)

	register_tool(
		"get_summary",
		get_summary,
		"데이터의 요약 통계(평균, 최솟값, 최댓값, 표준편차, CAGR, 추세)를 계산합니다.",
		{
			"type": "object",
			"properties": {
				"module_name": {
					"type": "string",
					"description": "분석할 모듈명 (예: IS, BS, dividend)",
				},
			},
			"required": ["module_name"],
		},
	)

	# 7b. get_report_data: 정기보고서 데이터 조회
	def get_report_data(api_type: str) -> str:
		"""reportEngine의 apiType별 정제 데이터를 조회합니다."""
		report = getattr(company, "report", None)
		if report is None:
			return "정기보고서 데이터가 없습니다."
		df = report.extract(api_type)
		if df is None:
			from dartlab.engines.reportEngine.types import API_TYPE_LABELS
			available = ", ".join(f"`{k}` ({v})" for k, v in list(API_TYPE_LABELS.items())[:10])
			return f"'{api_type}' 데이터가 없습니다. 사용 가능한 타입 예시: {available}"
		return _df_to_md(df)

	register_tool(
		"get_report_data",
		get_report_data,
		"OpenDART 정기보고서 API 데이터를 조회합니다. "
		"api_type 예시: dividend(배당), employee(직원현황), executive(임원현황), "
		"majorHolder(최대주주), auditOpinion(감사의견), capitalChange(증자감자), "
		"corporateBond(회사채), stockTotal(주식총수), treasuryStock(자기주식), "
		"investedCompany(타법인출자), outsideDirector(사외이사), "
		"executivePayAllTotal(임원보수전체), topPay(5억이상 개인보수). "
		"docsParser와 다르게 정기보고서 API의 표준화된 수치를 제공합니다.",
		{
			"type": "object",
			"properties": {
				"api_type": {
					"type": "string",
					"description": "조회할 API 타입 (예: dividend, employee, majorHolder)",
				},
			},
			"required": ["api_type"],
		},
	)

	# 7. get_company_info: 기업 기본 정보
	def get_company_info() -> str:
		info_parts = [
			f"기업명: {company.corpName}",
			f"종목코드: {company.stockCode}",
		]
		overview = getattr(company, "companyOverview", None)
		if isinstance(overview, dict):
			for key in ("ceo", "mainBusiness", "indutyName", "foundedDate"):
				if overview.get(key):
					info_parts.append(f"{key}: {overview[key]}")
		return "\n".join(info_parts)

	register_tool(
		"get_company_info",
		get_company_info,
		"기업의 기본 정보(기업명, 종목코드, 대표자, 업종 등)를 조회합니다.",
		{"type": "object", "properties": {}},
	)
