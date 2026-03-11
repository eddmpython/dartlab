"""Company → Excel (.xlsx) 내보내기.

Company의 모든 property를 동적으로 스캔하여 DataFrame이면 시트로 생성.
finance 시계열(IS/BS/CF)은 연도별 피벗, 나머지는 원본 DataFrame 그대로.

사용법::

    from dartlab import Company
    c = Company("005930")
    c.toExcel()                          # 005930_삼성전자.xlsx (전체)
    c.toExcel("output.xlsx")             # 지정 경로
    c.toExcel(modules=["IS", "BS"])      # 시트 선택
    c.toExcel(modules=["dividend", "audit", "employee"])  # 원하는 모듈만

    # 템플릿 기반 내보내기
    from dartlab.export.template import PRESETS
    exportWithTemplate(c, PRESETS["summary"])
    exportWithTemplate(c, PRESETS["governance"], "output.xlsx")
"""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING, Optional

import polars as pl
from openpyxl import Workbook
from openpyxl.styles import Alignment, Font, PatternFill
from openpyxl.utils import get_column_letter

if TYPE_CHECKING:
	from dartlab.company import KRCompany as Company
	from dartlab.export.template import ExcelTemplate


_HEADER_FONT = Font(bold=True, color="FFFFFF", size=11)
_HEADER_FILL = PatternFill(start_color="2F5496", end_color="2F5496", fill_type="solid")
_HEADER_ALIGN = Alignment(horizontal="center", vertical="center")
_ACCOUNT_FONT = Font(bold=True, size=10)
_NEGATIVE_FMT = '#,##0;[Red]-#,##0'
_NUMBER_FMT = '#,##0'

_SJ_LABELS = {"IS": "손익계산서", "BS": "재무상태표", "CF": "현금흐름표", "RATIO": "재무비율"}

_ACCOUNT_LABELS_OVERRIDE: dict[str, str] = {
	"owners_of_parent_equity": "자본총계(지배)",
	"operating_cashflow": "영업활동CF",
	"investing_cashflow": "투자활동CF",
	"cash_flows_from_financing_activities": "재무활동CF",
	"capex": "유형자산취득",
	"rnd_expenses": "연구개발비",
	"amortization": "무형자산상각비",
}

_RATIO_LABELS: dict[str, str] = {
	"roe": "ROE (%)",
	"roa": "ROA (%)",
	"operatingMargin": "영업이익률 (%)",
	"netMargin": "순이익률 (%)",
	"grossMargin": "매출총이익률 (%)",
	"ebitdaMargin": "EBITDA마진 (%)",
	"costOfSalesRatio": "매출원가율 (%)",
	"sgaRatio": "판관비율 (%)",
	"debtRatio": "부채비율 (%)",
	"currentRatio": "유동비율 (%)",
	"quickRatio": "당좌비율 (%)",
	"equityRatio": "자기자본비율 (%)",
	"interestCoverage": "이자보상배율 (x)",
	"netDebtRatio": "순차입금비율 (%)",
	"noncurrentRatio": "비유동비율 (%)",
	"revenueGrowth": "매출성장률 (%)",
	"operatingProfitGrowth": "영업이익성장률 (%)",
	"netProfitGrowth": "순이익성장률 (%)",
	"assetGrowth": "자산성장률 (%)",
	"equityGrowthRate": "자본성장률 (%)",
	"totalAssetTurnover": "총자산회전율 (x)",
	"inventoryTurnover": "재고자산회전율 (x)",
	"receivablesTurnover": "매출채권회전율 (x)",
	"payablesTurnover": "매입채무회전율 (x)",
	"fcf": "FCF",
	"operatingCfMargin": "영업CF마진 (%)",
	"operatingCfToNetIncome": "영업CF/순이익 (%)",
	"capexRatio": "CAPEX비율 (%)",
	"dividendPayoutRatio": "배당성향 (%)",
	"revenue": "매출",
	"operatingProfit": "영업이익",
	"netProfit": "순이익",
	"totalAssets": "총자산",
	"totalEquity": "자본총계",
	"operatingCashflow": "영업CF",
}

_CATEGORY_LABELS: dict[str, str] = {
	"profitability": "수익성",
	"stability": "안정성",
	"growth": "성장성",
	"efficiency": "효율성",
	"cashflow": "현금흐름",
	"absolute": "절대지표",
}


def _buildAccountLabels() -> dict[str, str]:
	"""mapper.labelMap() 기반 + override 합성."""
	try:
		from dartlab.engines.dart.finance.mapper import AccountMapper
		labels = dict(AccountMapper.get().labelMap())
	except (ImportError, FileNotFoundError):
		labels = {}
	labels.update(_ACCOUNT_LABELS_OVERRIDE)
	return labels


_ACCOUNT_LABELS: dict[str, str] = {}


def _getAccountLabels() -> dict[str, str]:
	"""lazy 초기화."""
	global _ACCOUNT_LABELS
	if not _ACCOUNT_LABELS:
		_ACCOUNT_LABELS = _buildAccountLabels()
	return _ACCOUNT_LABELS

_FINANCE_SHEETS = frozenset({"IS", "BS", "CF"})
_SPECIAL_SHEETS = frozenset({"ratios"})


def _autoWidth(ws, minWidth: int = 12, maxWidth: int = 30) -> None:
	for col in ws.columns:
		colLetter = get_column_letter(col[0].column)
		best = minWidth
		for cell in col:
			if cell.value is not None:
				length = len(str(cell.value))
				if isinstance(cell.value, (int, float)):
					length = max(length, 14)
				if length > best:
					best = length
		ws.column_dimensions[colLetter].width = min(best + 2, maxWidth)


def _writeHeaders(ws, headers: list[str]) -> None:
	for colIdx, header in enumerate(headers, 1):
		cell = ws.cell(row=1, column=colIdx, value=header)
		cell.font = _HEADER_FONT
		cell.fill = _HEADER_FILL
		cell.alignment = _HEADER_ALIGN


def _writeFinanceSheet(
	wb: Workbook,
	sjDiv: str,
	series: dict[str, dict[str, list[Optional[float]]]],
	years: list[str],
	*,
	label: str = "",
	columns: list[str] | None = None,
	yearFilter: list[str] | None = None,
) -> None:
	sheetLabel = label or _SJ_LABELS.get(sjDiv, sjDiv)
	ws = wb.create_sheet(title=sheetLabel[:31])

	stmtData = series.get(sjDiv, {})
	if not stmtData:
		return

	displayYears = years
	yearIndices: list[int] | None = None
	if yearFilter:
		yearIndices = [i for i, y in enumerate(years) if y in yearFilter]
		displayYears = [years[i] for i in yearIndices]

	_writeHeaders(ws, ["계정"] + displayYears)

	row = 2
	for snakeId, vals in stmtData.items():
		if columns and snakeId not in columns:
			continue
		effectiveVals = [vals[i] for i in yearIndices] if yearIndices else vals
		if not any(v is not None for v in effectiveVals):
			continue
		ws.cell(row=row, column=1, value=_getAccountLabels().get(snakeId, snakeId)).font = _ACCOUNT_FONT
		for colIdx, val in enumerate(effectiveVals, 2):
			if val is not None:
				cell = ws.cell(row=row, column=colIdx, value=round(val))
				cell.number_format = _NEGATIVE_FMT
		row += 1

	_autoWidth(ws)
	ws.freeze_panes = "B2"


def _writeRatiosSheet(wb: Workbook, c: Company, *, label: str = "") -> None:
	from dartlab.engines.common.finance.ratios import RATIO_CATEGORIES, calcRatioSeries, toSeriesDict

	annualResult = c.annual
	if annualResult is None:
		return
	annualSeries, years = annualResult
	rs = calcRatioSeries(annualSeries, years)
	ratioSeriesDict, _ = toSeriesDict(rs)
	ratioData = ratioSeriesDict.get("RATIO", {})
	if not ratioData:
		return

	ws = wb.create_sheet(title=(label or "재무비율")[:31])
	_writeHeaders(ws, ["지표"] + years)

	_CATEGORY_FILL = PatternFill(start_color="D6E4F0", end_color="D6E4F0", fill_type="solid")
	_CATEGORY_FONT = Font(bold=True, size=11, color="1F3864")

	_ABS_FIELDS = {"fcf", "revenue", "operatingProfit", "netProfit",
		"totalAssets", "totalEquity", "operatingCashflow"}

	row = 2
	for catKey, fields in RATIO_CATEGORIES:
		catFields = [f for f in fields if f in ratioData]
		if not catFields:
			continue

		catLabel = _CATEGORY_LABELS.get(catKey, catKey)
		cell = ws.cell(row=row, column=1, value=catLabel)
		cell.font = _CATEGORY_FONT
		cell.fill = _CATEGORY_FILL
		for colIdx in range(2, len(years) + 2):
			ws.cell(row=row, column=colIdx).fill = _CATEGORY_FILL
		row += 1

		for fieldName in catFields:
			vals = ratioData[fieldName]
			displayLabel = _RATIO_LABELS.get(fieldName, fieldName)
			ws.cell(row=row, column=1, value=displayLabel).font = _ACCOUNT_FONT
			isAbs = fieldName in _ABS_FIELDS
			for colIdx, val in enumerate(vals, 2):
				if val is not None:
					cell = ws.cell(row=row, column=colIdx, value=round(val) if isAbs else round(val, 2))
					cell.number_format = _NEGATIVE_FMT if isAbs else '0.00'
			row += 1

	_autoWidth(ws)
	ws.freeze_panes = "B2"


def _writeDataFrameSheet(
	wb: Workbook,
	title: str,
	df: pl.DataFrame,
	*,
	columns: list[str] | None = None,
	maxRows: int = 0,
) -> None:
	if df.height == 0:
		return

	if columns:
		validCols = [c for c in columns if c in df.columns]
		if validCols:
			df = df.select(validCols)

	if maxRows > 0:
		df = df.head(maxRows)

	safeTitle = title[:31]
	existing = {ws.title for ws in wb.worksheets}
	if safeTitle in existing:
		safeTitle = safeTitle[:28] + "_2"

	ws = wb.create_sheet(title=safeTitle)
	_writeHeaders(ws, df.columns)

	for rowIdx, row in enumerate(df.iter_rows(named=True), 2):
		for colIdx, colName in enumerate(df.columns, 1):
			val = row[colName]
			if val is None:
				continue
			cell = ws.cell(row=rowIdx, column=colIdx, value=val)
			if isinstance(val, float):
				if abs(val) >= 1000:
					cell.number_format = _NEGATIVE_FMT
				else:
					cell.number_format = '0.00'
			elif isinstance(val, int):
				cell.number_format = _NUMBER_FMT

	_autoWidth(ws)
	ws.freeze_panes = "A2"


def _getAvailableModules(c: Company) -> list[tuple[str, str]]:
	from dartlab.company import _ALL_PROPERTIES
	available = []
	for name, label in _ALL_PROPERTIES:
		available.append((name, label))
	available.append(("ratios", "재무비율"))
	return available


def _resolveData(c: Company, moduleName: str) -> pl.DataFrame | None:
	if moduleName == "ratios":
		return None
	try:
		data = getattr(c, moduleName, None)
	except Exception:
		return None
	if isinstance(data, pl.DataFrame) and data.height > 0:
		return data
	return None


def exportToExcel(
	c: Company,
	outputPath: str | Path | None = None,
	modules: list[str] | None = None,
) -> str:
	"""Company 데이터를 .xlsx로 내보낸다.

	Args:
		c: Company 인스턴스.
		outputPath: 저장 경로. None이면 현재 디렉토리에 '{종목코드}_{회사명}.xlsx'.
		modules: 포함할 모듈 목록. None이면 데이터가 있는 모든 모듈.
			finance: "IS", "BS", "CF" (연도별 시계열 피벗)
			비율: "ratios"
			나머지: Company property 이름 (dividend, audit, employee, executive, ...)

	Returns:
		저장된 파일 경로 (str).
	"""
	allModules = _getAvailableModules(c)
	allNames = {name for name, _ in allModules}
	labelMap = {name: label for name, label in allModules}

	if modules is None:
		targetModules = [name for name, _ in allModules]
	else:
		targetModules = [m for m in modules if m in allNames]

	wb = Workbook()
	wb.remove(wb.active)

	financeModules = [m for m in targetModules if m in _FINANCE_SHEETS]
	if financeModules and c._hasFinance:
		from dartlab.engines.dart.finance.pivot import buildAnnual
		result = buildAnnual(c.stockCode)
		if result:
			series, years = result
			for sjDiv in financeModules:
				if sjDiv in series:
					_writeFinanceSheet(wb, sjDiv, series, years)

	if "ratios" in targetModules and c._hasFinance:
		_writeRatiosSheet(wb, c)

	for moduleName in targetModules:
		if moduleName in _FINANCE_SHEETS or moduleName in _SPECIAL_SHEETS:
			continue
		df = _resolveData(c, moduleName)
		if df is not None:
			label = labelMap.get(moduleName, moduleName)
			_writeDataFrameSheet(wb, label, df)

	if not wb.sheetnames:
		raise ValueError(f"{c.stockCode} ({c.corpName}): 내보낼 데이터 없음")

	if outputPath is None:
		safeName = c.corpName.replace("/", "_").replace("\\", "_")
		outputPath = Path.cwd() / f"{c.stockCode}_{safeName}.xlsx"
	else:
		outputPath = Path(outputPath)

	wb.save(str(outputPath))
	return str(outputPath)


def exportWithTemplate(
	c: Company,
	template: ExcelTemplate,
	outputPath: str | Path | None = None,
) -> str:
	"""템플릿 기반 Excel 내보내기.

	SheetSpec별로 소스를 로드하고, columns/years 필터를 적용하여 시트를 생성한다.

	Args:
		c: Company 인스턴스.
		template: ExcelTemplate (시트 구성 정의).
		outputPath: 저장 경로. None이면 자동 생성.

	Returns:
		저장된 파일 경로 (str).
	"""
	wb = Workbook()
	wb.remove(wb.active)

	annualCache: tuple[dict, list[str]] | None = None

	for spec in template.sheets:
		source = spec.source

		if source in _FINANCE_SHEETS:
			if not c._hasFinance:
				continue
			if annualCache is None:
				from dartlab.engines.dart.finance.pivot import buildAnnual
				result = buildAnnual(c.stockCode)
				if result is None:
					continue
				annualCache = result
			series, years = annualCache
			if source in series:
				_writeFinanceSheet(
					wb, source, series, years,
					label=spec.label,
					columns=spec.columns or None,
					yearFilter=spec.years or None,
				)
			continue

		if source == "ratios":
			if c._hasFinance:
				_writeRatiosSheet(wb, c, label=spec.label)
			continue

		df = _resolveData(c, source)
		if df is not None:
			_writeDataFrameSheet(
				wb, spec.label, df,
				columns=spec.columns or None,
				maxRows=spec.maxRows,
			)

	if not wb.sheetnames:
		raise ValueError(f"{c.stockCode} ({c.corpName}): 템플릿 '{template.name}'에 해당하는 데이터 없음")

	if outputPath is None:
		safeName = c.corpName.replace("/", "_").replace("\\", "_")
		templateSafe = template.name.replace("/", "_").replace("\\", "_")
		outputPath = Path.cwd() / f"{c.stockCode}_{safeName}_{templateSafe}.xlsx"
	else:
		outputPath = Path(outputPath)

	wb.save(str(outputPath))
	return str(outputPath)


def listAvailableModules(c: Company) -> list[dict[str, str]]:
	"""내보내기 가능한 모듈 목록 반환 (GUI/API용).

	registry의 requires 필드로 빠르게 판정 (property 호출 없음).
	"""
	from dartlab.core.registry import getEntry

	_DATA_FLAGS = {
		"docs": c._hasDocs,
		"finance": c._hasFinance,
		"report": c._hasReport,
	}

	result = []
	for name, label in _getAvailableModules(c):
		entry = getEntry(name)
		if entry is not None and entry.requires:
			if not _DATA_FLAGS.get(entry.requires, False):
				continue
		elif name in _FINANCE_SHEETS or name == "ratios":
			if not c._hasFinance:
				continue
		result.append({"name": name, "label": label})
	return result
