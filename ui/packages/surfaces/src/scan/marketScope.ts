/**
 * DART(KR) + EDGAR(US) 동시 조회의 안전장치.
 *
 * 두 시장을 한 표에 놓는 것은 쉽다. 어려운 것은 **섞으면 안 되는 것을 못 섞게 만드는 일**이다.
 * 실측된 함정 셋:
 *
 *   1. 통화 스케일 . KR revenue 는 원 raw(1e11~1e14), US 는 조 USD(0.41). 같은 컬럼에서
 *      정렬하면 US 가 전부 하단으로 깔린다. 실제로 terminal 의 mergedIndex
 *      (routeLoad.ts:74)가 이 두 단위를 한 배열에 담고 있는데, 지금 오답이 안 나는 이유는
 *      가드가 아니라 "산업 문자열이 한글 vs 영문이라 우연히 안 겹친다" 는 암묵 불변식뿐이다.
 *   2. 단위 표기 . wonAsEok(metrics.ts)는 무조건 1e8 로 나누고 "억원" 을 붙인다. USD 가 오면
 *      억원으로 오표기된다.
 *   3. 상대지표 . 백분위·z-score·산업순위는 KR 34 KSIC 분포에 종속이다. US 를 그 분포에
 *      끼우면 분포 자체가 없다.
 *
 * 그래서 규칙은 하나다.
 *   **무차원(비율·등급)만 시장을 가로질러 비교한다. 절대금액과 상대지표는 시장 안에서만.**
 *
 * 이 규칙은 손 선별이 아니라 단위에서 기계적으로 도출된다(crossMarketComparable).
 */

import type { MetricDef, ScanNode } from './types';

/** 1급 시장 차원. KOSPI/KOSDAQ/KONEX 는 KR 의 하위시장이라 이것과 층이 다르다. */
export type Market = 'KR' | 'US';

/** 사용자가 고르는 조회 범위. */
export type MarketScope = 'KR' | 'US' | 'ALL';

/** 시장별 통화. 절대금액 표기는 반드시 이걸 따른다. */
export const MARKET_CURRENCY: Record<Market, 'KRW' | 'USD'> = { KR: 'KRW', US: 'USD' };

export const MARKET_LABEL: Record<MarketScope, string> = { KR: '한국', US: '미국', ALL: '전체' };

/**
 * 노드의 1급 시장. US 노드는 로더가 market='US' 를 명시한다.
 * 그 외(KOSPI/KOSDAQ/KONEX/미지정)는 전부 KR 이다.
 */
export function nodeMarket(node: ScanNode): Market {
	return (node as Record<string, unknown>).market === 'US' ? 'US' : 'KR';
}

/**
 * 무차원 단위 목록. 이 단위를 가진 값은 시장을 가로질러 같은 뜻이다.
 * ROE 15% 는 서울에서도 뉴욕에서도 15% 다.
 */
const DIMENSIONLESS_UNITS = new Set(['%', '배', '점', '%p']);

/**
 * 이 지표를 KR 과 US 가 한 컬럼에서 정렬·비교해도 되는가.
 * 단위에서 기계적으로 도출한다(손 선별 0). enum(등급)도 무차원이다.
 *
 * 주의: 회계기준 차이(IFRS vs US GAAP)는 이 함수가 해결하지 않는다. 무차원이라는 것은
 * "스케일이 같다" 이지 "정의가 같다" 가 아니다. 그래서 UI 는 전체 보기에서 시장 칩을
 * 항상 보여 사용자가 기준 차이를 인지하게 한다.
 */
export function crossMarketComparable(def: MetricDef | undefined): boolean {
	if (!def) return false;
	if (def.type === 'enum') return true;
	if (def.type === 'number') return DIMENSIONLESS_UNITS.has(def.unit ?? '');
	return false; // text/series 는 정렬 대상이 아니다
}

/**
 * US 노드가 실제로 가진 필드. 로더(edgarNodes)가 만드는 키와 반드시 일치한다.
 * 여기 없는 키를 US 행에서 조회하면 "결측" 이 아니라 "이 시장엔 그 개념이 없다" 이다.
 * 둘을 같은 '·' 로 그리면 사용자는 데이터가 언젠가 채워질 거라 오해한다.
 */
export const US_FIELDS: ReadonlySet<string> = new Set([
	'id',
	'label',
	'market',
	'submarket',
	'industry',
	'industryName',
	'industryScheme',
	'currency',
	'color',
	'sic',
	'cik',
	'fy',
	// 무차원 (KR 과 같은 뜻)
	'roe',
	'roa',
	'opMargin',
	'netMargin',
	'debtRatio',
	'profGrade',
	// 절대금액 (USD. 시장 안에서만 비교)
	'revenue',
	'operatingProfit',
	'netProfit',
	'totalAssets',
	'totalEquity'
]);

/** 셀 렌더 3-state. 결측('·')과 시장 비적용('NA')은 다른 사실이다. */
export type CellApplicability = 'applicable' | 'notInMarket';

export function cellApplicability(node: ScanNode, metricKey: string): CellApplicability {
	if (nodeMarket(node) === 'KR') return 'applicable';
	return US_FIELDS.has(metricKey) ? 'applicable' : 'notInMarket';
}

/** 조회 범위에 맞는 노드만. */
export function inScope(node: ScanNode, scope: MarketScope): boolean {
	return scope === 'ALL' || nodeMarket(node) === scope;
}

/**
 * 이 정렬키가 지금 범위에서 정직한가.
 * 전체 보기에서 절대금액으로 단일 정렬하면 통화 스케일차(약 1300 배)로 한 시장이 통째
 * 하단에 깔린다. 그것은 랭킹이 아니라 통화 목록이다. 그래서 막는다.
 */
export function sortAllowed(def: MetricDef | undefined, scope: MarketScope): boolean {
	if (scope !== 'ALL') return true;
	if (!def) return true;
	if (def.type === 'text' || def.type === 'series') return true;
	return crossMarketComparable(def);
}

/** 막힌 이유를 화면이 말하게 한다. 조용히 비활성화하지 않는다. */
export function sortBlockedReason(def: MetricDef, scope: MarketScope): string | null {
	if (sortAllowed(def, scope)) return null;
	return `${def.label} 은 통화 단위 지표라 전체 보기에서 정렬할 수 없습니다. 시장을 하나 고르세요.`;
}

/**
 * 백분위는 시장 안에서만 뽑는다. KR 분포에 US 를 끼우거나 그 반대를 하지 않는다.
 * 반환 = market -> (metricKey -> {p10, p90}).
 */
export function percentilesByMarket(
	nodes: ScanNode[],
	metricKeys: string[],
	defs: Record<string, MetricDef>,
	minSample = 10
): Map<Market, Map<string, { p10: number; p90: number; higherBetter?: boolean }>> {
	const out = new Map<Market, Map<string, { p10: number; p90: number; higherBetter?: boolean }>>();
	for (const market of ['KR', 'US'] as Market[]) {
		const sub = nodes.filter((n) => nodeMarket(n) === market);
		if (sub.length === 0) continue;
		const inner = new Map<string, { p10: number; p90: number; higherBetter?: boolean }>();
		for (const key of metricKeys) {
			const def = defs[key];
			if (!def || def.type !== 'number') continue;
			const values: number[] = [];
			for (const n of sub) {
				const v = (n as Record<string, unknown>)[key];
				if (typeof v === 'number' && Number.isFinite(v)) values.push(v);
			}
			if (values.length < minSample) continue;
			values.sort((a, b) => a - b);
			inner.set(key, {
				p10: values[Math.floor(values.length * 0.1)],
				p90: values[Math.floor(values.length * 0.9)],
				higherBetter: def.higherBetter
			});
		}
		out.set(market, inner);
	}
	return out;
}
