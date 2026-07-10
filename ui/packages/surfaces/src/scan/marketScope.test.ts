/**
 * DART + EDGAR 동시 조회의 안전장치 벡터.
 *
 * 여기가 빨개지면 KR 원화와 US 달러가 한 컬럼에서 정렬될 수 있다는 뜻이다.
 * terminal 의 mergedIndex(routeLoad.ts:74)가 그 상태이며, 지금 오답이 안 나는 이유는
 * 가드가 아니라 "산업 문자열이 한글 vs 영문이라 우연히 안 겹친다" 는 우연뿐이다.
 */

import { describe, it, expect } from 'vitest';
import {
	US_FIELDS,
	cellApplicability,
	crossMarketComparable,
	inScope,
	nodeMarket,
	percentilesByMarket,
	sortAllowed,
	sortBlockedReason
} from './marketScope';
import type { MetricDef, ScanNode } from './types';

const def = (over: Partial<MetricDef>): MetricDef =>
	({ key: 'k', label: 'L', group: 'g', type: 'number', definition: '', source: 'ecosystem', ...over }) as MetricDef;

const kr = (over: Record<string, unknown> = {}): ScanNode =>
	({ id: '005930', label: '삼성전자', industry: '반도체', ...over }) as ScanNode;
const us = (over: Record<string, unknown> = {}): ScanNode =>
	({ id: 'AAPL', label: 'Apple Inc.', industry: 'SIC:manufacturing', market: 'US', ...over }) as ScanNode;

describe('시장 판별', () => {
	it('market 이 US 인 노드만 US', () => {
		expect(nodeMarket(us())).toBe('US');
		expect(nodeMarket(kr())).toBe('KR');
		expect(nodeMarket(kr({ market: 'KOSPI' }))).toBe('KR');
		expect(nodeMarket(kr({ market: 'KOSDAQ' }))).toBe('KR');
	});

	it('inScope 는 ALL 에서 둘 다 통과', () => {
		expect(inScope(kr(), 'ALL')).toBe(true);
		expect(inScope(us(), 'ALL')).toBe(true);
		expect(inScope(us(), 'KR')).toBe(false);
		expect(inScope(kr(), 'US')).toBe(false);
	});
});

describe('교차시장 비교 가능성은 단위에서 도출된다 (손 선별 0)', () => {
	it('무차원 단위는 비교 가능', () => {
		expect(crossMarketComparable(def({ unit: '%' }))).toBe(true);
		expect(crossMarketComparable(def({ unit: '배' }))).toBe(true);
		expect(crossMarketComparable(def({ unit: '점' }))).toBe(true);
	});

	it('통화·수량 단위는 비교 불가', () => {
		expect(crossMarketComparable(def({ unit: '억원' }))).toBe(false);
		expect(crossMarketComparable(def({ unit: '원' }))).toBe(false);
		expect(crossMarketComparable(def({ unit: '명' }))).toBe(false);
		expect(crossMarketComparable(def({ unit: '주' }))).toBe(false);
	});

	it('등급(enum)은 무차원이라 비교 가능', () => {
		expect(crossMarketComparable(def({ type: 'enum', unit: undefined }))).toBe(true);
	});

	it('단위 없는 숫자는 비교 불가 (안전측)', () => {
		expect(crossMarketComparable(def({ unit: undefined }))).toBe(false);
	});
});

describe('전체 보기에서 통화 컬럼 정렬은 막힌다', () => {
	const money = def({ key: 'marketCap', label: '시가총액', unit: '억원' });
	const ratio = def({ key: 'roe', label: 'ROE', unit: '%' });

	it('단일 시장 보기에서는 무엇이든 정렬 가능', () => {
		expect(sortAllowed(money, 'KR')).toBe(true);
		expect(sortAllowed(money, 'US')).toBe(true);
	});

	it('전체 보기에서 통화 컬럼은 정렬 불가', () => {
		expect(sortAllowed(money, 'ALL')).toBe(false);
	});

	it('전체 보기에서도 무차원 컬럼은 정렬 가능', () => {
		expect(sortAllowed(ratio, 'ALL')).toBe(true);
	});

	it('막힌 이유를 문장으로 말한다 (조용한 비활성화 금지)', () => {
		expect(sortBlockedReason(money, 'ALL')).toContain('시가총액');
		expect(sortBlockedReason(ratio, 'ALL')).toBeNull();
		expect(sortBlockedReason(money, 'KR')).toBeNull();
	});

	it('text/series 는 정렬 대상이 아니라 막지 않는다', () => {
		expect(sortAllowed(def({ type: 'text' }), 'ALL')).toBe(true);
		expect(sortAllowed(def({ type: 'series' }), 'ALL')).toBe(true);
	});
});

describe('셀 적용가능성 · 결측과 시장 비적용은 다른 사실', () => {
	it('KR 행은 모든 컬럼이 적용 대상 (없으면 결측)', () => {
		expect(cellApplicability(kr(), 'govScore')).toBe('applicable');
		expect(cellApplicability(kr(), 'roe')).toBe('applicable');
	});

	it('US 행은 US_FIELDS 밖이면 시장 비적용', () => {
		expect(cellApplicability(us(), 'roe')).toBe('applicable');
		expect(cellApplicability(us(), 'govScore')).toBe('notInMarket');
		expect(cellApplicability(us(), 'per')).toBe('notInMarket');
	});

	it('US_FIELDS 는 로더가 만드는 무차원 필드를 포함한다', () => {
		for (const k of ['roe', 'roa', 'opMargin', 'netMargin', 'debtRatio', 'profGrade']) {
			expect(US_FIELDS.has(k), `${k} 가 빠지면 US 행에서 NA 로 잘못 표기된다`).toBe(true);
		}
	});
});

describe('백분위는 시장 안에서만 뽑는다', () => {
	const defs = { roe: def({ key: 'roe', unit: '%', higherBetter: true }) };
	// KR 은 0~19, US 는 100~119. 섞으면 KR 이 전부 하위로 깔린다.
	const nodes: ScanNode[] = [
		...Array.from({ length: 20 }, (_, i) => kr({ id: `K${i}`, roe: i })),
		...Array.from({ length: 20 }, (_, i) => us({ id: `U${i}`, roe: 100 + i }))
	];

	it('KR 과 US 가 각자의 분포를 갖는다', () => {
		const p = percentilesByMarket(nodes, ['roe'], defs);
		const krP = p.get('KR')!.get('roe')!;
		const usP = p.get('US')!.get('roe')!;
		expect(krP.p90).toBeLessThan(usP.p10);
		expect(krP.p10).toBeLessThan(krP.p90);
	});

	it('표본이 부족한 시장은 분포를 만들지 않는다 (억지 추정 금지)', () => {
		const few = [kr({ roe: 1 }), kr({ roe: 2 })];
		const p = percentilesByMarket(few, ['roe'], defs);
		expect(p.get('KR')?.has('roe')).toBe(false);
	});

	it('노드가 없는 시장은 아예 항목이 없다', () => {
		const p = percentilesByMarket(nodes.filter((n) => nodeMarket(n) === 'KR'), ['roe'], defs);
		expect(p.has('US')).toBe(false);
	});
});
