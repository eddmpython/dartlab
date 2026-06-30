/**
 * Scan Studio 프리셋 라이브러리 · ⌘K 모달용.
 *
 * 한 클릭으로 conds + sorts + cols 자동 입력. 자연어 한국어 + 한 줄 설명.
 *
 * 원칙:
 *  - PR-A 는 ecosystem.json 만 의존하는 안정 프리셋만 (7 개).
 *  - PR-B 에서 PER/배당 등 valuation 의존 프리셋 추가.
 *  - 깨진 프리셋 (qoq/consecutive/turnaround/oversold/new-high) 폐기됨.
 *
 * SSOT: 다른 곳에서 프리셋 정의 금지.
 */

import type { FilterCond, SortKey } from './types';
import type { MetricKey } from './metrics';

export type RuntimeLoader = 'finance5y' | 'priceTrend' | 'report' | 'valuation';

export interface Preset {
	id: string;
	title: string;
	subtitle: string;
	desc: string;
	category: 'theme' | 'safety' | 'leader' | 'risk';
	conds: FilterCond[];
	sorts: SortKey[];
	/** 적용 시 추가로 보일 컬럼 (기본 컬럼셋 위에 union) */
	cols?: MetricKey[];
	/** 적용 시 필요한 런타임 데이터 로더. */
	loaders?: RuntimeLoader[];
}

export const PRESETS: Preset[] = [
	{
		id: 'real-money-makers',
		title: '진짜 돈 버는 회사',
		subtitle: '4축 흑자 + 수익성',
		desc: '영업이익률 + ROE + 매출 YoY + 흑자 4축 동시 만족 · 실력으로 돈 버는 회사',
		category: 'theme',
		conds: [
			{ metric: 'opMargin', op: '>=', value: 5 },
			{ metric: 'roe', op: '>=', value: 5 },
			{ metric: 'revenueYoyPct', op: '>=', value: 0 },
			{ metric: 'profGrade', op: '!=', value: '적자' }
		],
		sorts: [
			{ key: 'roe', dir: 'desc' },
			{ key: 'opMargin', dir: 'desc' }
		],
		cols: [
			'profGrade',
			'revenue',
			'fin_sales_2025',
			'fin_operating_profit_2025',
			'fin_ratio_op_margin_2025',
			'fin_growth_sales_cagr'
		],
		loaders: ['finance5y']
	},
	{
		id: 'quality-compounder',
		title: 'Quality Compounder',
		subtitle: '높은 ROE + 안전 부채 + 우량',
		desc: 'ROE 15%↑ + 부채비율 100%↓ + 이익질 양호 이상 · 장기 복리 우량주',
		category: 'theme',
		conds: [
			{ metric: 'roe', op: '>=', value: 15 },
			{ metric: 'debtRatio', op: '<=', value: 100 },
			{ metric: 'qualGrade', op: '!=', value: '주의' },
			{ metric: 'qualGrade', op: '!=', value: '위험' }
		],
		sorts: [{ key: 'roe', dir: 'desc' }],
		cols: [
			'qualGrade',
			'icr',
			'fin_ratio_roe_2025',
			'fin_ratio_debt_ratio_2025',
			'fin_ratio_current_ratio_2025'
		],
		loaders: ['finance5y']
	},
	{
		id: 'growth-and-safety',
		title: '성장 + 안전',
		subtitle: '매출 성장 + 부채 통제',
		desc: 'CAGR 15%↑ + 부채 80%↓ + 매출 YoY 10%↑ · 빠르게 크면서 빚 안 늘리는 회사',
		category: 'theme',
		conds: [
			{ metric: 'revCagr', op: '>=', value: 15 },
			{ metric: 'debtRatio', op: '<=', value: 80 },
			{ metric: 'revenueYoyPct', op: '>=', value: 10 }
		],
		sorts: [{ key: 'revCagr', dir: 'desc' }],
		cols: [
			'revCagr',
			'growthGrade',
			'fin_sales_2025',
			'fin_operating_profit_2025',
			'fin_growth_sales_cagr',
			'fin_growth_operating_profit_cagr',
			'fin_growth_sales_yoy_latest'
		],
		loaders: ['finance5y']
	},
	{
		id: 'low-debt-high-icr',
		title: '저부채 + 이자안전',
		subtitle: '부채 50%↓ + ICR 5↑',
		desc: '부채비율 50% 이하 + 이자보상배율 5배↑ · 이자 갚고도 남는 안전 회사',
		category: 'safety',
		conds: [
			{ metric: 'debtRatio', op: '<=', value: 50 },
			{ metric: 'icr', op: '>=', value: 5 }
		],
		sorts: [{ key: 'icr', dir: 'desc' }],
		cols: [
			'debtGrade',
			'icr',
			'fin_ratio_debt_ratio_2025',
			'fin_ratio_current_ratio_2025',
			'fin_current_liabilities_2025',
			'fin_noncurrent_liabilities_2025'
		],
		loaders: ['finance5y']
	},
	{
		id: 'high-roe-strong-margin',
		title: '고ROE + 고마진',
		subtitle: 'ROE 20%↑ + 영업이익률 10%↑',
		desc: 'ROE 20% 이상 + 영업이익률 10% 이상 · 수익성·자본효율 동시 우수',
		category: 'leader',
		conds: [
			{ metric: 'roe', op: '>=', value: 20 },
			{ metric: 'opMargin', op: '>=', value: 10 }
		],
		sorts: [{ key: 'roe', dir: 'desc' }],
		cols: ['profGrade', 'fin_ratio_op_margin_2025', 'fin_ratio_roe_2025', 'fin_growth_operating_profit_cagr'],
		loaders: ['finance5y']
	},
	{
		id: 'industry-leader',
		title: '산업 리더',
		subtitle: '산업 순위 3위↑ + 흑자',
		desc: '산업 내 매출 3위 이내 + 상장사매출비중 10%↑ + 영업이익 흑자 · 상장사 풀 내 상위 회사',
		category: 'leader',
		conds: [
			{ metric: 'industryRank', op: '<=', value: 3 },
			{ metric: 'marketShare', op: '>=', value: 10 },
			{ metric: 'opMargin', op: '>=', value: 0 }
		],
		sorts: [
			{ key: 'marketShare', dir: 'desc' },
			{ key: 'revenue', dir: 'desc' }
		],
		cols: ['marketShare', 'industryRank', 'fin_sales_2025', 'fin_growth_sales_cagr'],
		loaders: ['finance5y']
	},
	{
		id: 'risk-watch',
		title: '이상 신호',
		subtitle: '감사·부채 위험 + ROE 급변',
		desc: '감사 고위험 또는 부채 고위험 또는 ROE Δ -5%p 이하 · 주의 필요한 회사',
		category: 'risk',
		conds: [{ metric: 'auditRisk', op: '==', value: '고위험' }],
		sorts: [{ key: 'roeDelta', dir: 'asc' }],
		cols: ['auditRisk', 'debtGrade', 'roeDelta', 'numericChanges1y', 'structuralChanges1y', 'totalChanges1y'],
		loaders: ['report']
	}
];

export const PRESETS_BY_ID = new Map(PRESETS.map((p) => [p.id, p]));

export const PRESET_CATEGORIES: { key: Preset['category']; label: string; color: string }[] = [
	{ key: 'theme', label: '테마', color: '#ea4647' },
	{ key: 'safety', label: '안전', color: '#22c55e' },
	{ key: 'leader', label: '리더', color: '#ec4899' },
	{ key: 'risk', label: '위험', color: '#a78bfa' }
];
