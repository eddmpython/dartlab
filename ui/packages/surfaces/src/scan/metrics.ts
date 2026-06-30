/**
 * Scan Studio metric catalog.
 *
 * 기본 ecosystem 지표와 런타임 parquet 지표를 한 곳에서 정의한다.
 */

import { fmtPrice } from '@dartlab/ui-format/krw';
import { fmtPct, fmtMul } from '@dartlab/ui-format/pct';
import type { MetricDef } from './types';
import { buildFinanceMetricDefs, type FinanceMetricGroup } from './financeAccounts';

export type MetricGroup =
	| 'identity'
	| 'income'
	| 'health'
	| 'governance'
	| 'quality'
	| 'workforce'
	| 'changes'
	| FinanceMetricGroup
	| 'price'
	| 'valuation'
	| 'disclosure';

export const GROUP_META: Record<MetricGroup, { label: string; color: string }> = {
	identity: { label: '식별', color: '#94a3b8' },
	income: { label: '손익', color: '#60a5fa' },
	health: { label: '재무건전성', color: '#22c55e' },
	governance: { label: '거버넌스', color: '#a78bfa' },
	quality: { label: '이익질', color: '#fbbf24' },
	workforce: { label: '인적', color: '#f472b6' },
	changes: { label: '변화', color: '#ec4899' },
	financeIncome: { label: '손익계산서', color: '#38bdf8' },
	financeBalance: { label: '재무상태표', color: '#22d3ee' },
	financeCashflow: { label: '현금흐름', color: '#34d399' },
	financeRatio: { label: '재무비율', color: '#f59e0b' },
	financeGrowth: { label: '성장률', color: '#f97316' },
	price: { label: '주가', color: '#ea4647' },
	valuation: { label: '가치', color: '#10b981' },
	disclosure: { label: '공시 변경', color: '#c084fc' }
};

const pct = (withSign = false) => (v: unknown) =>
	typeof v === 'number' ? fmtPct(v, { withSign }) : '·';

const wonAsEok = (v: unknown) => {
	if (typeof v !== 'number' || !Number.isFinite(v)) return '·';
	const eok = v / 1e8;
	const abs = Math.abs(eok);
	const maximumFractionDigits = abs >= 100 ? 0 : 1;
	return `${eok.toLocaleString('ko-KR', { maximumFractionDigits })}억원`;
};

const baseMetrics: MetricDef[] = [
	{
		key: 'label',
		label: '회사명',
		group: 'identity',
		type: 'text',
		definition: '회사명. 클릭 시 회사 대시보드 진입.',
		source: 'ecosystem'
	},
	{
		key: 'id',
		label: '종목코드',
		group: 'identity',
		type: 'text',
		definition: '거래소 종목코드.',
		source: 'ecosystem'
	},
	{
		key: 'market',
		label: '시장',
		group: 'identity',
		type: 'enum',
		definition: '상장 시장. KOSPI, KOSDAQ, KONEX.',
		source: 'ecosystem'
	},
	{
		key: 'industryName',
		label: '산업',
		group: 'identity',
		type: 'enum',
		definition: 'dartlab 산업 분류.',
		source: 'ecosystem'
	},
	{
		key: 'product',
		label: '제품',
		group: 'identity',
		type: 'text',
		definition: '최신 주요 제품 및 서비스 공시 preview.',
		source: 'productIndex'
	},
	{
		key: 'stageName',
		label: '단계',
		group: 'identity',
		type: 'enum',
		definition: '산업 가치사슬 단계.',
		source: 'ecosystem'
	},
	{
		key: 'role',
		label: '역할',
		group: 'identity',
		type: 'text',
		definition: '산업 내 역할.',
		source: 'ecosystem'
	},
	{
		key: 'marketShare',
		label: '상장사매출비중',
		group: 'identity',
		type: 'number',
		unit: '%',
		definition: 'KSIC 산업 노드 내 상장 구성사 매출 합 대비 비중. 비상장·수입 제외라 실제 시장점유율 아님.',
		higherBetter: true,
		source: 'ecosystem',
		format: pct()
	},
	{
		key: 'industryRank',
		label: '산업 순위',
		group: 'identity',
		type: 'number',
		unit: '위',
		definition: '산업 내 매출 순위. 1위가 가장 높다.',
		higherBetter: false,
		source: 'ecosystem',
		format: (v) => (typeof v === 'number' ? `${v}위` : '·')
	},
	{
		key: 'revenue',
		label: '매출액',
		group: 'income',
		type: 'number',
		unit: '억원',
		definition: '직전 사업연도 매출액. 표시는 억원 단위로 고정.',
		higherBetter: true,
		source: 'ecosystem',
		format: wonAsEok,
		distribution: 'log'
	},
	{
		key: 'opMargin',
		label: '영업이익률',
		group: 'income',
		type: 'number',
		unit: '%',
		definition: '영업이익 ÷ 매출액.',
		higherBetter: true,
		source: 'ecosystem',
		format: pct()
	},
	{
		key: 'roe',
		label: 'ROE',
		group: 'income',
		type: 'number',
		unit: '%',
		definition: '당기순이익 ÷ 자본총계.',
		higherBetter: true,
		source: 'ecosystem',
		format: pct()
	},
	{
		key: 'revenueYoyPct',
		label: '매출 YoY',
		group: 'income',
		type: 'number',
		unit: '%',
		definition: '직전 사업연도 매출 성장률.',
		higherBetter: true,
		source: 'ecosystem',
		format: pct(true)
	},
	{
		key: 'revCagr',
		label: '매출 CAGR',
		group: 'income',
		type: 'number',
		unit: '%',
		definition: '장기 매출 연평균 성장률.',
		higherBetter: true,
		source: 'ecosystem',
		format: pct(true)
	},
	{
		key: 'debtRatio',
		label: '부채비율',
		group: 'health',
		type: 'number',
		unit: '%',
		definition: '부채총계 ÷ 자본총계.',
		higherBetter: false,
		source: 'ecosystem',
		format: pct()
	},
	{
		key: 'icr',
		label: '이자보상배율',
		group: 'health',
		type: 'number',
		unit: '배',
		definition: '영업이익 ÷ 이자비용.',
		higherBetter: true,
		source: 'ecosystem',
		format: (v) => (typeof v === 'number' ? fmtMul(v, 1) : '·')
	},
	{
		key: 'profGrade',
		label: '수익성 등급',
		group: 'health',
		type: 'enum',
		definition: '수익성 종합 등급.',
		values: ['우수', '양호', '보통', '저수익', '적자'],
		higherBetter: true,
		source: 'ecosystem'
	},
	{
		key: 'debtGrade',
		label: '부채 등급',
		group: 'health',
		type: 'enum',
		definition: '부채 위험 등급.',
		values: ['안전', '관찰', '주의', '고위험'],
		higherBetter: true,
		source: 'ecosystem'
	},
	{
		key: 'growthGrade',
		label: '성장 등급',
		group: 'health',
		type: 'enum',
		definition: '성장성 등급.',
		values: ['고성장', '성장', '정체', '역성장'],
		higherBetter: true,
		source: 'ecosystem'
	},
	{
		key: 'govGrade',
		label: '거버넌스 등급',
		group: 'governance',
		type: 'enum',
		definition: '대주주·이사회·내부거래 종합 등급.',
		values: ['A', 'B', 'C', 'D', 'E'],
		higherBetter: true,
		source: 'ecosystem'
	},
	{
		key: 'holderPct',
		label: '대주주 지분',
		group: 'governance',
		type: 'number',
		unit: '%',
		definition: '최대주주와 특수관계인 합산 지분율.',
		source: 'ecosystem',
		format: pct()
	},
	{
		key: 'holderChange',
		label: '지분 변화',
		group: 'governance',
		type: 'number',
		unit: '%p',
		definition: '직전 1년 대주주 지분 변화.',
		source: 'ecosystem',
		format: (v) => (typeof v === 'number' ? fmtPct(v, { withSign: true, suffix: '%p' }) : '·')
	},
	{
		key: 'stability',
		label: '경영 안정성',
		group: 'governance',
		type: 'enum',
		definition: '경영진 변동·내부거래 패턴 종합.',
		values: ['안정', '보통', '불안정'],
		higherBetter: true,
		source: 'ecosystem'
	},
	{
		key: 'qualGrade',
		label: '이익질 등급',
		group: 'quality',
		type: 'enum',
		definition: '발생주의와 현금흐름 일치도.',
		values: ['우수', '양호', '보통', '주의', '위험'],
		higherBetter: true,
		source: 'ecosystem'
	},
	{
		key: 'liqGrade',
		label: '유동성 등급',
		group: 'quality',
		type: 'enum',
		definition: '단기 부채 상환 능력.',
		values: ['우수', '양호', '보통', '주의', '위험'],
		higherBetter: true,
		source: 'ecosystem'
	},
	{
		key: 'cfPattern',
		label: '현금흐름 패턴',
		group: 'quality',
		type: 'enum',
		definition: 'OCF / ICF / FCF 부호 조합 패턴.',
		source: 'ecosystem'
	},
	{
		key: 'auditRisk',
		label: '감사 위험',
		group: 'quality',
		type: 'enum',
		definition: '감사인 변경·한정의견·재무재작성 회계 신호.',
		values: ['저위험', '중위험', '고위험'],
		higherBetter: false,
		source: 'ecosystem'
	},
	{
		key: 'capClass',
		label: '자본 분류',
		group: 'quality',
		type: 'enum',
		definition: '자본 운용 패턴.',
		source: 'ecosystem'
	},
	{
		key: 'empCount',
		label: '임직원',
		group: 'workforce',
		type: 'number',
		unit: '명',
		definition: '직전 사업연도 평균 임직원 수.',
		source: 'ecosystem',
		format: (v) => (typeof v === 'number' ? `${v.toLocaleString('ko-KR')}명` : '·'),
		distribution: 'log'
	},
	{
		key: 'roeDelta',
		label: 'ROE 변화',
		group: 'changes',
		type: 'number',
		unit: '%p',
		definition: '직전 사업연도 ROE 변화.',
		higherBetter: true,
		source: 'ecosystem',
		format: (v) => (typeof v === 'number' ? fmtPct(v, { withSign: true, suffix: '%p' }) : '·')
	},
	{
		key: 'opMarginDelta',
		label: '영업이익률 변화',
		group: 'changes',
		type: 'number',
		unit: '%p',
		definition: '직전 사업연도 영업이익률 변화.',
		higherBetter: true,
		source: 'ecosystem',
		format: (v) => (typeof v === 'number' ? fmtPct(v, { withSign: true, suffix: '%p' }) : '·')
	},
	{
		key: 'debtRatioDelta',
		label: '부채비율 변화',
		group: 'changes',
		type: 'number',
		unit: '%p',
		definition: '직전 사업연도 부채비율 변화. 음수는 개선.',
		higherBetter: false,
		source: 'ecosystem',
		format: (v) => (typeof v === 'number' ? fmtPct(v, { withSign: true, suffix: '%p' }) : '·')
	},
	{
		key: 'currentPrice',
		label: '현재가',
		group: 'price',
		type: 'number',
		unit: '원',
		definition: '직전 거래일 종가.',
		source: 'prices',
		format: (v) => (typeof v === 'number' ? fmtPrice(v) : '·')
	},
	{
		key: 'marketCap',
		label: '시가총액',
		group: 'price',
		type: 'number',
		unit: '억원',
		definition: '직전 거래일 시가총액. 표시는 억원 단위로 고정.',
		higherBetter: true,
		source: 'prices',
		format: wonAsEok,
		distribution: 'log'
	},
	{
		key: 'return1m',
		label: '1M 수익률',
		group: 'price',
		type: 'number',
		unit: '%',
		definition: '직전 1개월 주가 수익률.',
		higherBetter: true,
		source: 'prices',
		format: pct(true)
	},
	{
		key: 'return3m',
		label: '3M 수익률',
		group: 'price',
		type: 'number',
		unit: '%',
		definition: '직전 3개월 주가 수익률.',
		higherBetter: true,
		source: 'prices',
		format: pct(true)
	},
	{
		key: 'return1y',
		label: '1Y 수익률',
		group: 'price',
		type: 'number',
		unit: '%',
		definition: '직전 1년 주가 수익률.',
		higherBetter: true,
		source: 'prices',
		format: pct(true)
	},
	{
		key: 'volatility1y',
		label: '1Y 변동성',
		group: 'price',
		type: 'number',
		unit: '%',
		definition: '직전 1년 일별 수익률 연환산 표준편차.',
		higherBetter: false,
		source: 'prices',
		format: pct()
	},
	{
		key: 'week52High',
		label: '52주 고가',
		group: 'price',
		type: 'number',
		unit: '원',
		definition: '직전 52주 고가.',
		higherBetter: true,
		source: 'prices',
		format: (v) => (typeof v === 'number' ? fmtPrice(v) : '·')
	},
	{
		key: 'week52Low',
		label: '52주 저가',
		group: 'price',
		type: 'number',
		unit: '원',
		definition: '직전 52주 저가.',
		higherBetter: false,
		source: 'prices',
		format: (v) => (typeof v === 'number' ? fmtPrice(v) : '·')
	},
	{
		key: 'volumeAvg30d',
		label: '30D 거래량',
		group: 'price',
		type: 'number',
		unit: '주',
		definition: '직전 30거래일 평균 거래량.',
		higherBetter: true,
		source: 'prices',
		format: (v) => (typeof v === 'number' ? v.toLocaleString('ko-KR') : '·'),
		distribution: 'log'
	},
	{
		key: 'spark30',
		label: '30D 추세',
		group: 'price',
		type: 'text',
		definition: '직전 30거래일 종가 추이.',
		source: 'prices'
	},
	{
		key: 'spark60',
		label: '60D 추세',
		group: 'price',
		type: 'text',
		definition: '직전 60거래일 종가 추이.',
		source: 'prices'
	},
	{
		key: 'spark',
		label: '1Y 추세',
		group: 'price',
		type: 'text',
		definition: '직전 1년 종가 추이.',
		source: 'prices'
	},
	{
		key: 'per',
		label: 'PER',
		group: 'valuation',
		type: 'number',
		unit: '배',
		definition: '주가 ÷ 주당순이익.',
		higherBetter: false,
		source: 'valuation',
		format: (v) => (typeof v === 'number' ? fmtMul(v, 1) : '·')
	},
	{
		key: 'pbr',
		label: 'PBR',
		group: 'valuation',
		type: 'number',
		unit: '배',
		definition: '주가 ÷ 주당순자산.',
		higherBetter: false,
		source: 'valuation',
		format: (v) => (typeof v === 'number' ? fmtMul(v, 2) : '·')
	},
	{
		key: 'dividendYield',
		label: '배당수익률',
		group: 'valuation',
		type: 'number',
		unit: '%',
		definition: '주당 배당금 ÷ 주가.',
		higherBetter: true,
		source: 'valuation',
		format: pct()
	},
	{
		key: 'numericChanges1y',
		label: '재무 변경',
		group: 'disclosure',
		type: 'number',
		unit: '건',
		definition: '직전 1년 재무 정정·변경 건수.',
		source: 'changes',
		format: (v) => (typeof v === 'number' ? `${v}건` : '·')
	},
	{
		key: 'structuralChanges1y',
		label: '구조 변경',
		group: 'disclosure',
		type: 'number',
		unit: '건',
		definition: '직전 1년 사업구조 변경 건수.',
		source: 'changes',
		format: (v) => (typeof v === 'number' ? `${v}건` : '·')
	},
	{
		key: 'totalChanges1y',
		label: '공시 변경',
		group: 'disclosure',
		type: 'number',
		unit: '건',
		definition: '직전 1년 전체 공시 변경 건수.',
		higherBetter: false,
		source: 'report',
		format: (v) => (typeof v === 'number' ? `${v}건` : '·')
	},
	{
		key: 'recentChangeYear',
		label: '최근 변경연도',
		group: 'disclosure',
		type: 'number',
		unit: '년',
		definition: '공시 변경 데이터의 최근 연도.',
		higherBetter: false,
		source: 'report',
		format: (v) => (typeof v === 'number' ? `${v}` : '·')
	}
];

export const METRICS_DEF = [...baseMetrics, ...buildFinanceMetricDefs()] as readonly MetricDef[];

export type MetricKey = string;
export type MetricKeyLiteral = (typeof METRICS_DEF)[number]['key'];

export const METRICS_BY_KEY: Record<string, MetricDef> = Object.fromEntries(METRICS_DEF.map((m) => [m.key, m]));

export const METRICS_BY_GROUP: Record<string, MetricDef[]> = METRICS_DEF.reduce(
	(acc, m) => {
		(acc[m.group] ||= []).push(m);
		return acc;
	},
	{} as Record<string, MetricDef[]>
);

export const DEFAULT_COLUMNS: string[] = [
	'label',
	'id',
	'market',
	'industryName',
	'product',
	'currentPrice',
	'marketCap',
	'spark30',
	'spark',
	'per',
	'pbr',
	'roe',
	'opMargin',
	'debtRatio',
	'qualGrade',
	'return1y',
	'dividendYield'
];

export const PINNED_COLUMNS: string[] = ['label'];
