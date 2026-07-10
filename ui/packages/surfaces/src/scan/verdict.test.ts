/**
 * 판정격자 골든 벡터.
 *
 * 회귀핀 3 종은 구 evalCond(+page.svelte:275-282) 의 실측 결함을 못박는다.
 * 이 테스트가 빨개지면 결측 정직이 무너진 것이다.
 */

import { describe, it, expect } from 'vitest';
import {
	buildVerdictGrid,
	coverageStats,
	evalVerdict,
	nearMiss,
	relaxThreshold,
	type Verdict
} from './verdict';
import type { FilterCond, MetricDef, ScanNode } from './types';

const defs: Record<string, MetricDef> = {
	roe: { key: 'roe', label: 'ROE', group: 'income', type: 'number', unit: '%', definition: '', source: 'ecosystem' },
	marketCap: {
		key: 'marketCap',
		label: '시가총액',
		group: 'valuation',
		type: 'number',
		unit: '억원',
		definition: '',
		source: 'valuation'
	},
	grade: { key: 'grade', label: '등급', group: 'quality', type: 'enum', definition: '', source: 'ecosystem' }
};

const node = (over: Record<string, unknown>): ScanNode =>
	({ id: '000000', label: 'x', industry: 'i', ...over }) as ScanNode;

describe('회귀핀 · 결측은 어떤 연산자에서도 UNKNOWN', () => {
	// 핀 1. 구 코드: `null != 5` -> true -> 결측이 PASS 로 통과했다.
	it('!= 에서 결측이 PASS 로 새지 않는다', () => {
		const v = evalVerdict(node({ roe: null }), { metric: 'roe', op: '!=', value: 5 }, defs);
		expect(v).toBe<Verdict>('UNKNOWN');
	});

	// 핀 2. 구 코드: `num === null -> false` -> 결측이 FAIL 로 위조됐다.
	it('>= 에서 결측이 FAIL 로 위조되지 않는다', () => {
		const v = evalVerdict(node({ roe: undefined }), { metric: 'roe', op: '>=', value: 5 }, defs);
		expect(v).toBe<Verdict>('UNKNOWN');
	});

	it('between 에서도 결측은 UNKNOWN', () => {
		const v = evalVerdict(node({ roe: null }), { metric: 'roe', op: 'between', value: 1, value2: 9 }, defs);
		expect(v).toBe<Verdict>('UNKNOWN');
	});

	it('exists 는 결측을 판정할 수 있으므로 FAIL', () => {
		expect(evalVerdict(node({ roe: null }), { metric: 'roe', op: 'exists' }, defs)).toBe<Verdict>('FAIL');
		expect(evalVerdict(node({ roe: 3 }), { metric: 'roe', op: 'exists' }, defs)).toBe<Verdict>('PASS');
	});

	it('negate 는 PASS/FAIL 만 뒤집고 UNKNOWN 은 그대로', () => {
		expect(evalVerdict(node({ roe: null }), { metric: 'roe', op: '>=', value: 5, negate: true }, defs)).toBe<Verdict>(
			'UNKNOWN'
		);
		expect(evalVerdict(node({ roe: 9 }), { metric: 'roe', op: '>=', value: 5, negate: true }, defs)).toBe<Verdict>(
			'FAIL'
		);
	});
});

describe('회귀핀 · 억원 스케일이 모든 수치 연산자에 적용', () => {
	// 핀 3. 구 코드: ==/!= 만 raw 값(1e11)을 비교해 억원 입력(1000)과 영원히 불일치.
	it('== 가 억원 입력을 raw 원과 비교하지 않는다', () => {
		const n = node({ marketCap: 1000 * 1e8 }); // 1000 억원
		expect(evalVerdict(n, { metric: 'marketCap', op: '==', value: 1000 }, defs)).toBe<Verdict>('PASS');
	});

	it('!= 도 같은 스케일을 쓴다', () => {
		const n = node({ marketCap: 1000 * 1e8 });
		expect(evalVerdict(n, { metric: 'marketCap', op: '!=', value: 1000 }, defs)).toBe<Verdict>('FAIL');
	});

	it('>= 와 == 의 스케일이 일치한다', () => {
		const n = node({ marketCap: 1000 * 1e8 });
		expect(evalVerdict(n, { metric: 'marketCap', op: '>=', value: 1000 }, defs)).toBe<Verdict>('PASS');
		expect(evalVerdict(n, { metric: 'marketCap', op: '>=', value: 1001 }, defs)).toBe<Verdict>('FAIL');
	});
});

describe('enum / text 조건', () => {
	it('enum == 는 문자열 동치 (느슨한 비교 금지)', () => {
		expect(evalVerdict(node({ grade: 'A' }), { metric: 'grade', op: '==', value: 'A' }, defs)).toBe<Verdict>('PASS');
		expect(evalVerdict(node({ grade: 'A' }), { metric: 'grade', op: '==', value: 'B' }, defs)).toBe<Verdict>('FAIL');
	});

	it('in 은 값 목록 포함 여부', () => {
		expect(evalVerdict(node({ grade: 'A' }), { metric: 'grade', op: 'in', value: ['A', 'B'] }, defs)).toBe<Verdict>(
			'PASS'
		);
		expect(evalVerdict(node({ grade: 'C' }), { metric: 'grade', op: 'in', value: ['A', 'B'] }, defs)).toBe<Verdict>(
			'FAIL'
		);
	});

	it('빈 문자열은 결측으로 본다', () => {
		expect(evalVerdict(node({ grade: '  ' }), { metric: 'grade', op: '==', value: 'A' }, defs)).toBe<Verdict>(
			'UNKNOWN'
		);
	});
});

describe('격자 파생', () => {
	const nodes = [
		node({ id: 'pass', roe: 10, marketCap: 5000 * 1e8 }),
		node({ id: 'near', roe: 10, marketCap: 100 * 1e8 }), // 조건 1개만 실패
		node({ id: 'miss', roe: null, marketCap: 5000 * 1e8 }), // 결측 -> UNKNOWN
		node({ id: 'both', roe: 1, marketCap: 100 * 1e8 }) // 둘 다 실패
	];
	const conds: FilterCond[] = [
		{ metric: 'roe', op: '>=', value: 5 },
		{ metric: 'marketCap', op: '>=', value: 1000 }
	];

	it('members 는 전 조건 PASS 만', () => {
		const g = buildVerdictGrid(nodes, conds, defs);
		expect(g.members.map((n) => n.id)).toEqual(['pass']);
	});

	it('결측 종목은 fail 이 아니라 excludedForMissing 으로 계상', () => {
		const g = buildVerdictGrid(nodes, conds, defs);
		expect(g.excludedForMissing).toBe(1);
		const missRow = g.rows.find((r) => r.node.id === 'miss')!;
		expect(missRow.unknownCount).toBe(1);
		expect(missRow.failCount).toBe(0);
	});

	it('nearMiss(1) 은 FAIL 1 + UNKNOWN 0 만 (결측 종목 제외)', () => {
		const g = buildVerdictGrid(nodes, conds, defs);
		expect(nearMiss(g, 1).map((r) => r.node.id)).toEqual(['near']);
	});

	it('funnel 의 pass/fail/unknown 합이 유니버스 크기와 같다', () => {
		const g = buildVerdictGrid(nodes, conds, defs);
		for (const step of g.funnel) {
			expect(step.pass + step.fail + step.unknown).toBe(g.universe);
		}
	});

	it('funnel survivors 는 단조 비증가', () => {
		const g = buildVerdictGrid(nodes, conds, defs);
		for (let i = 1; i < g.funnel.length; i++) {
			expect(g.funnel[i].survivors).toBeLessThanOrEqual(g.funnel[i - 1].survivors);
		}
		expect(g.funnel[g.funnel.length - 1].survivors).toBe(g.members.length);
	});

	it('조건 0 개면 전원 members', () => {
		const g = buildVerdictGrid(nodes, [], defs);
		expect(g.members.length).toBe(nodes.length);
		expect(nearMiss(g, 1)).toEqual([]);
	});

	it('coverage 는 유효 표본만 센다', () => {
		const [roeCov] = coverageStats(nodes, ['roe']);
		expect(roeCov).toEqual({ metric: 'roe', valid: 3, total: 4 });
	});
});

describe('임계 역산 (relaxThreshold)', () => {
	const nodes = [
		node({ roe: 20, marketCap: 5000 * 1e8 }),
		node({ roe: 15, marketCap: 5000 * 1e8 }),
		node({ roe: 12, marketCap: 5000 * 1e8 }),
		node({ roe: 3, marketCap: 5000 * 1e8 })
	];
	const conds: FilterCond[] = [
		{ metric: 'roe', op: '>=', value: 18 },
		{ metric: 'marketCap', op: '>=', value: 1000 }
	];

	it('목표 3 사가 되는 roe 임계를 역산', () => {
		expect(relaxThreshold(nodes, conds, 0, 3, defs)).toBe(12);
	});

	it('목표가 후보보다 크면 가장 느슨한 값', () => {
		expect(relaxThreshold(nodes, conds, 0, 99, defs)).toBe(3);
	});

	it('수치 조건이 아니면 null (억지 추정 금지)', () => {
		const c: FilterCond[] = [{ metric: 'grade', op: '==', value: 'A' }];
		expect(relaxThreshold(nodes, c, 0, 3, defs)).toBeNull();
	});
});
