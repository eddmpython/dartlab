import type { MetricDef } from './types';
import { fmtPct } from '@dartlab/ui-format/pct';

export type FinanceMetricGroup =
	| 'financeIncome'
	| 'financeBalance'
	| 'financeCashflow'
	| 'financeRatio'
	| 'financeGrowth';

export interface FinanceAccountSpec {
	id: string;
	label: string;
	group: Exclude<FinanceMetricGroup, 'financeRatio' | 'financeGrowth'>;
	statement: 'IS' | 'BS' | 'CF';
	higherBetter?: boolean;
	ids: readonly string[];
	names: readonly string[];
}

export const FINANCE_COMPLETED_YEARS = ['2022', '2023', '2024', '2025'] as const;

export const FINANCE_ACCOUNTS: readonly FinanceAccountSpec[] = [
	{
		id: 'sales',
		label: '매출액',
		group: 'financeIncome',
		statement: 'IS',
		higherBetter: true,
		ids: ['ifrs-full_Revenue', 'dart_OperatingRevenue'],
		names: ['매출액', '수익(매출액)', '영업수익']
	},
	{
		id: 'cost_of_sales',
		label: '매출원가',
		group: 'financeIncome',
		statement: 'IS',
		higherBetter: false,
		ids: ['ifrs-full_CostOfSales'],
		names: ['매출원가']
	},
	{
		id: 'gross_profit',
		label: '매출총이익',
		group: 'financeIncome',
		statement: 'IS',
		higherBetter: true,
		ids: ['ifrs-full_GrossProfit'],
		names: ['매출총이익']
	},
	{
		id: 'operating_expenses',
		label: '영업비용',
		group: 'financeIncome',
		statement: 'IS',
		higherBetter: false,
		ids: [
			'ifrs-full_OperatingExpense',
			'dart_OperatingExpenses',
			'dart_TotalSellingGeneralAdministrativeExpenses'
		],
		names: ['영업비용', '판매비와관리비', '판매비 및 관리비']
	},
	{
		id: 'operating_profit',
		label: '영업이익',
		group: 'financeIncome',
		statement: 'IS',
		higherBetter: true,
		ids: ['dart_OperatingIncomeLoss', 'ifrs-full_ProfitLossFromOperatingActivities'],
		names: ['영업이익', '영업이익(손실)', '영업손익']
	},
	{
		id: 'finance_income',
		label: '금융수익',
		group: 'financeIncome',
		statement: 'IS',
		higherBetter: true,
		ids: ['ifrs-full_FinanceIncome', 'ifrs-full_RevenueFromInterest', 'dart_InterestIncomeFinanceIncome'],
		names: ['금융수익', '이자수익']
	},
	{
		id: 'finance_costs',
		label: '금융비용',
		group: 'financeIncome',
		statement: 'IS',
		higherBetter: false,
		ids: ['ifrs-full_FinanceCosts', 'ifrs-full_InterestExpense', 'dart_InterestExpenseFinanceExpense'],
		names: ['금융비용', '금융원가', '이자비용']
	},
	{
		id: 'profit_before_tax',
		label: '법인세전순이익',
		group: 'financeIncome',
		statement: 'IS',
		higherBetter: true,
		ids: ['ifrs-full_ProfitLossBeforeTax'],
		names: ['법인세차감전순이익', '법인세비용차감전순이익']
	},
	{
		id: 'income_tax_expense',
		label: '법인세비용',
		group: 'financeIncome',
		statement: 'IS',
		higherBetter: false,
		ids: ['ifrs-full_IncomeTaxExpenseContinuingOperations'],
		names: ['법인세비용']
	},
	{
		id: 'net_income',
		label: '당기순이익',
		group: 'financeIncome',
		statement: 'IS',
		higherBetter: true,
		ids: ['ifrs-full_ProfitLoss'],
		names: ['당기순이익', '당기순이익(손실)']
	},
	{
		id: 'cash_and_cash_equivalents',
		label: '현금및현금성자산',
		group: 'financeBalance',
		statement: 'BS',
		higherBetter: true,
		ids: ['ifrs-full_CashAndCashEquivalents'],
		names: ['현금및현금성자산']
	},
	{
		id: 'current_assets',
		label: '유동자산',
		group: 'financeBalance',
		statement: 'BS',
		higherBetter: true,
		ids: ['ifrs-full_CurrentAssets'],
		names: ['유동자산']
	},
	{
		id: 'inventories',
		label: '재고자산',
		group: 'financeBalance',
		statement: 'BS',
		higherBetter: false,
		ids: ['ifrs-full_Inventories', 'ifrs-full_InventoriesTotal'],
		names: ['재고자산']
	},
	{
		id: 'trade_receivables',
		label: '매출채권',
		group: 'financeBalance',
		statement: 'BS',
		higherBetter: false,
		ids: ['ifrs-full_TradeAndOtherCurrentReceivables', 'dart_ShortTermTradeReceivable'],
		names: ['매출채권', '매출채권및기타채권', '매출채권 및 기타채권']
	},
	{
		id: 'noncurrent_assets',
		label: '비유동자산',
		group: 'financeBalance',
		statement: 'BS',
		higherBetter: true,
		ids: ['ifrs-full_NoncurrentAssets'],
		names: ['비유동자산']
	},
	{
		id: 'property_plant_and_equipment',
		label: '유형자산',
		group: 'financeBalance',
		statement: 'BS',
		higherBetter: true,
		ids: ['ifrs-full_PropertyPlantAndEquipment'],
		names: ['유형자산']
	},
	{
		id: 'intangible_assets',
		label: '무형자산',
		group: 'financeBalance',
		statement: 'BS',
		higherBetter: true,
		ids: ['ifrs-full_IntangibleAssetsOtherThanGoodwill', 'ifrs-full_IntangibleAssetsAndGoodwill'],
		names: ['무형자산']
	},
	{
		id: 'current_liabilities',
		label: '유동부채',
		group: 'financeBalance',
		statement: 'BS',
		higherBetter: false,
		ids: ['ifrs-full_CurrentLiabilities'],
		names: ['유동부채']
	},
	{
		id: 'trade_payables',
		label: '매입채무',
		group: 'financeBalance',
		statement: 'BS',
		higherBetter: false,
		ids: ['ifrs-full_TradeAndOtherCurrentPayables', 'dart_ShortTermTradePayables'],
		names: ['매입채무', '매입채무및기타채무', '매입채무 및 기타채무']
	},
	{
		id: 'noncurrent_liabilities',
		label: '비유동부채',
		group: 'financeBalance',
		statement: 'BS',
		higherBetter: false,
		ids: ['ifrs-full_NoncurrentLiabilities'],
		names: ['비유동부채']
	},
	{
		id: 'total_stockholders_equity',
		label: '자본총계',
		group: 'financeBalance',
		statement: 'BS',
		higherBetter: true,
		ids: ['ifrs-full_Equity'],
		names: ['자본총계']
	},
	{
		id: 'retained_earnings',
		label: '이익잉여금',
		group: 'financeBalance',
		statement: 'BS',
		higherBetter: true,
		ids: ['ifrs-full_RetainedEarnings'],
		names: ['이익잉여금']
	},
	{
		id: 'operating_cashflow',
		label: '영업활동현금흐름',
		group: 'financeCashflow',
		statement: 'CF',
		higherBetter: true,
		ids: ['ifrs-full_CashFlowsFromUsedInOperatingActivities'],
		names: ['영업활동현금흐름', '영업활동으로 인한 현금흐름']
	},
	{
		id: 'investing_cashflow',
		label: '투자활동현금흐름',
		group: 'financeCashflow',
		statement: 'CF',
		higherBetter: false,
		ids: ['ifrs-full_CashFlowsFromUsedInInvestingActivities'],
		names: ['투자활동현금흐름', '투자활동으로 인한 현금흐름']
	},
	{
		id: 'financing_cashflow',
		label: '재무활동현금흐름',
		group: 'financeCashflow',
		statement: 'CF',
		ids: ['ifrs-full_CashFlowsFromUsedInFinancingActivities'],
		names: ['재무활동현금흐름', '재무활동으로 인한 현금흐름']
	},
	{
		id: 'cash_and_cash_equivalents_at_the_end_of_year',
		label: '기말현금',
		group: 'financeCashflow',
		statement: 'CF',
		higherBetter: true,
		ids: ['ifrs-full_CashAndCashEquivalentsAtEndOfPeriodCf'],
		names: ['기말현금및현금성자산']
	},
	{
		id: 'cash_and_cash_equivalents_beginning',
		label: '기초현금',
		group: 'financeCashflow',
		statement: 'CF',
		higherBetter: true,
		ids: ['dart_CashAndCashEquivalentsAtBeginningOfPeriodCf', 'ifrs-full_CashAndCashEquivalentsAtBeginningOfPeriodCf'],
		names: ['기초현금및현금성자산']
	},
	{
		id: 'changes_in_operating_assets_and_liabilities',
		label: '영업자산부채변동',
		group: 'financeCashflow',
		statement: 'CF',
		ids: [
			'dart_AdjustmentsForChangesInOperatingAssetsAndLiabilities',
			'dart_AdjustmentsForAssetsLiabilitiesOfOperatingActivities'
		],
		names: ['영업자산부채변동', '영업자산부채의변동', '영업활동으로인한자산부채의변동']
	},
	{
		id: 'depreciation',
		label: '감가상각비',
		group: 'financeCashflow',
		statement: 'CF',
		higherBetter: false,
		ids: [
			'ifrs-full_AdjustmentsForDepreciationExpense',
			'dart_AdjustmentsForDepreciationExpense',
			'ifrs-full_AdjustmentsForDepreciationAndAmortisationExpense'
		],
		names: ['감가상각비']
	},
	{
		id: 'net_increase_decrease_in_cash_and_cash_equivalents',
		label: '현금순증감',
		group: 'financeCashflow',
		statement: 'CF',
		ids: [
			'ifrs-full_IncreaseDecreaseInCashAndCashEquivalents',
			'ifrs-full_IncreaseDecreaseInCashAndCashEquivalentsBeforeEffectOfExchangeRateChanges'
		],
		names: ['현금및현금성자산순증감', '현금및현금성자산의순증감', '현금및현금성자산의증감']
	}
] as const;

export function financeMetricKey(accountId: string, year: string): string {
	return `fin_${accountId}_${year}`;
}

export function financeRatioKey(ratioId: string, year: string): string {
	return `fin_ratio_${ratioId}_${year}`;
}

export function financeGrowthKey(growthId: string): string {
	return `fin_growth_${growthId}`;
}

function pctFormat(withSign = false) {
	return (v: unknown) => (typeof v === 'number' ? fmtPct(v, { withSign }) : '·');
}

function fmtWonAsEok(v: unknown): string {
	if (typeof v !== 'number' || !Number.isFinite(v)) return '·';
	const eok = v / 1e8;
	const abs = Math.abs(eok);
	const maximumFractionDigits = abs >= 100 ? 0 : 1;
	return `${eok.toLocaleString('ko-KR', { maximumFractionDigits })}억원`;
}

export function buildFinanceMetricDefs(): MetricDef[] {
	const accountDefs = FINANCE_ACCOUNTS.flatMap((account) =>
		FINANCE_COMPLETED_YEARS.map(
			(year): MetricDef => ({
				key: financeMetricKey(account.id, year),
				label: `${year}년\n${account.label}`,
				group: account.group,
				type: 'number',
				unit: '억원',
				definition: `${year}년 ${account.label}. 기존 finance-lite 연간값을 런타임에 펼친 정렬 가능 숫자 컬럼. 표시는 억원 단위로 고정.`,
				higherBetter: account.higherBetter,
				source: 'finance5y',
				format: fmtWonAsEok,
				distribution: account.id === 'sales' || account.group === 'financeBalance' ? 'log' : 'linear'
			})
		)
	);
	const ratioDefs: MetricDef[] = FINANCE_COMPLETED_YEARS.flatMap((year) => [
		{
			key: financeRatioKey('op_margin', year),
			label: `${year}년\n영업이익률`,
			group: 'financeRatio',
			type: 'number',
			unit: '%',
			definition: `${year}년 영업이익 ÷ 매출액.`,
			higherBetter: true,
			source: 'finance5y',
			format: pctFormat()
		},
		{
			key: financeRatioKey('net_margin', year),
			label: `${year}년\n순이익률`,
			group: 'financeRatio',
			type: 'number',
			unit: '%',
			definition: `${year}년 당기순이익 ÷ 매출액.`,
			higherBetter: true,
			source: 'finance5y',
			format: pctFormat()
		},
		{
			key: financeRatioKey('roe', year),
			label: `${year}년\nROE`,
			group: 'financeRatio',
			type: 'number',
			unit: '%',
			definition: `${year}년 당기순이익 ÷ 자본총계.`,
			higherBetter: true,
			source: 'finance5y',
			format: pctFormat()
		},
		{
			key: financeRatioKey('debt_ratio', year),
			label: `${year}년\n부채비율`,
			group: 'financeRatio',
			type: 'number',
			unit: '%',
			definition: `${year}년 부채총계 ÷ 자본총계. 부채총계는 유동부채 + 비유동부채.`,
			higherBetter: false,
			source: 'finance5y',
			format: pctFormat()
		},
		{
			key: financeRatioKey('current_ratio', year),
			label: `${year}년\n유동비율`,
			group: 'financeRatio',
			type: 'number',
			unit: '%',
			definition: `${year}년 유동자산 ÷ 유동부채.`,
			higherBetter: true,
			source: 'finance5y',
			format: pctFormat()
		}
	]);
	const growthDefs: MetricDef[] = [
		['sales_cagr', '매출 CAGR', '2022-2025 매출액 연평균 성장률.', true],
		['operating_profit_cagr', '영업이익 CAGR', '2022-2025 영업이익 연평균 성장률.', true],
		['net_income_cagr', '순이익 CAGR', '2022-2025 당기순이익 연평균 성장률.', true],
		['sales_yoy_latest', '매출 YoY', '최근 2개 연도 매출액 변화율.', true],
		['operating_profit_yoy_latest', '영업이익 YoY', '최근 2개 연도 영업이익 변화율.', true],
		['net_income_yoy_latest', '순이익 YoY', '최근 2개 연도 당기순이익 변화율.', true]
	].map(
		([id, label, definition, higherBetter]): MetricDef => ({
			key: financeGrowthKey(String(id)),
			label: String(label),
			group: 'financeGrowth',
			type: 'number',
			unit: '%',
			definition: String(definition),
			higherBetter: Boolean(higherBetter),
			source: 'finance5y',
			format: pctFormat(true)
		})
	);
	return [...accountDefs, ...ratioDefs, ...growthDefs];
}
