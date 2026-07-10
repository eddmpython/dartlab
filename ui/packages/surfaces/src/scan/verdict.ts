/**
 * Scan Studio 판정격자 (VerdictGrid) · 조건 x 종목 판정의 단일 SSOT.
 *
 * 스크리너는 필터의 곱이 아니다. 조건마다 종목을 PASS / FAIL / UNKNOWN 으로 판정한
 * 격자가 원시개념이고, 통과 목록(members)은 그 격자의 요약 하나일 뿐이다. 근접후보
 * (nearMiss) · 깔때기(funnel) · 커버리지(coverage)는 전부 같은 격자의 파생이라
 * 새 데이터 fetch 가 0 이다.
 *
 * UNKNOWN 이 3 번째 상태인 이유:
 *   결측(null)을 FAIL 로 접으면 "조건 미달로 탈락" 과 "데이터가 없어서 판정 불가" 가
 *   뭉개진다. 그러면 사용자는 임계값을 잘못 조정한다. missing > wrong.
 *
 * 이 모듈이 고치는 기존 결함 2 종 (구 evalCond, +page.svelte):
 *   1. 비대칭 결측 . null 이 >= / <= / between 에선 FAIL 인데 != 에선 PASS 였다
 *      (`null != 5` 가 참). 이제 모든 연산자에서 UNKNOWN 이다.
 *   2. 단위 우회 . == / != 만 raw 값을 비교해 억원 스케일(1e8 나눗셈)이 적용되지
 *      않았다. 시가총액 `== 1000`(억원)이 raw 1e11 과 비교되어 영원히 0 건이었다.
 *      이제 모든 수치 연산자가 같은 정규화(normalizeNumeric)를 거친다.
 */

import type { FilterCond, MetricDef, ScanNode } from './types';

/** 한 조건에 대한 한 종목의 판정. UNKNOWN = 데이터 부재로 판정 불가. */
export type Verdict = 'PASS' | 'FAIL' | 'UNKNOWN';

/** 종목 1 행의 조건별 판정 + 요약. conds 순서와 verdicts 인덱스가 1:1. */
export interface RowVerdict {
	node: ScanNode;
	verdicts: Verdict[];
	passCount: number;
	failCount: number;
	unknownCount: number;
}

/** 조건 1 개의 깔때기 한 칸. */
export interface FunnelStep {
	cond: FilterCond;
	/** 이 조건을 통과한 종목 수 (이 조건 단독 기준). */
	pass: number;
	/** 조건 미달로 탈락. */
	fail: number;
	/** 데이터 부재로 판정 불가. fail 이 아니다. */
	unknown: number;
	/** 조건 0..i 를 모두 PASS 한 누적 생존 수. */
	survivors: number;
}

/** 컬럼 1 개의 결측 성적표. */
export interface CoverageStat {
	metric: string;
	valid: number;
	total: number;
}

export interface VerdictGrid {
	rows: RowVerdict[];
	conds: FilterCond[];
	/** 전 조건 PASS. UNKNOWN 이 하나라도 있으면 members 가 아니다. */
	members: ScanNode[];
	funnel: FunnelStep[];
	/** 유니버스 크기 (조건 적용 전). */
	universe: number;
	/** UNKNOWN 때문에 판정 불가로 members 에서 빠진 종목 수. */
	excludedForMissing: number;
}

/**
 * 조건의 사람용 표기. 필터칩과 판정 리본이 같은 문구를 쓰도록 여기 한 곳에 둔다.
 * (전에는 +page.svelte 와 리본이 각자 만들어 표기가 갈렸다.)
 */
export function condLabel(cond: FilterCond, defs: Record<string, MetricDef>): string {
	const def = defs[cond.metric];
	const label = def?.label ?? cond.metric;
	const unit = def?.unit ?? '';
	const fmt = (value: unknown) => {
		if (typeof value !== 'number') return String(value ?? '');
		const formatted = value.toLocaleString('ko-KR', { maximumFractionDigits: 2 });
		return unit ? `${formatted}${unit}` : formatted;
	};
	const prefix = cond.negate ? '제외 ' : '';
	if (cond.op === 'between') return `${prefix}${label} ${fmt(cond.value)}~${fmt(cond.value2)}`;
	if (cond.op === 'contains') return `${prefix}${label} 포함: ${cond.value ?? ''}`;
	if (cond.op === 'in') {
		const values = Array.isArray(cond.value) ? cond.value.join(', ') : String(cond.value ?? '');
		return `${prefix}${label}: ${values}`;
	}
	if (cond.op === 'exists') return `${prefix}${label} 값 있음`;
	return `${prefix}${label} ${cond.op} ${fmt(cond.value)}`;
}

/** 값 존재 여부. 빈 문자열도 부재로 본다 (그리드가 '·' 로 렌더하는 것과 일치). */
export function hasValue(v: unknown): boolean {
	if (v === null || v === undefined) return false;
	if (typeof v === 'number') return Number.isFinite(v);
	if (typeof v === 'string') return v.trim().length > 0;
	return true;
}

/**
 * 수치 비교용 정규화. 그리드가 억원으로 표시하는 컬럼은 필터 입력도 억원이므로
 * 원 단위 raw 를 1e8 로 나눈다. 모든 수치 연산자가 이 한 곳을 거친다.
 */
export function normalizeNumeric(node: ScanNode, metricKey: string, defs: Record<string, MetricDef>): number | null {
	const raw = (node as Record<string, unknown>)[metricKey];
	const num = typeof raw === 'number' ? raw : Number(raw);
	if (!Number.isFinite(num)) return null;
	return defs[metricKey]?.unit === '억원' ? num / 1e8 : num;
}

const NUMERIC_OPS = new Set(['>=', '<=', '==', '!=', 'between']);

/**
 * 한 종목 x 한 조건 판정. 결측은 어떤 연산자에서도 UNKNOWN 이다.
 *
 * 예외 2 종 (결측이 UNKNOWN 이 아닌 경우):
 *   - `exists` 는 결측 자체를 묻는 조건이므로 결측 = FAIL (판정 가능).
 *   - `negate` 는 PASS/FAIL 만 뒤집는다. UNKNOWN 은 뒤집히지 않는다
 *     (모르는 것의 부정도 모르는 것이다).
 */
export function evalVerdict(node: ScanNode, cond: FilterCond, defs: Record<string, MetricDef>): Verdict {
	const raw = (node as Record<string, unknown>)[cond.metric];
	const present = hasValue(raw);

	if (cond.op === 'exists') {
		return applyNegate(present ? 'PASS' : 'FAIL', cond.negate);
	}
	if (!present) return 'UNKNOWN';

	let result: boolean;
	if (cond.op === 'contains') {
		const query = String(cond.value ?? '').trim().toLowerCase();
		result = query.length > 0 && String(raw).toLowerCase().includes(query);
	} else if (cond.op === 'in') {
		const values = Array.isArray(cond.value) ? cond.value.map(String) : [];
		result = values.includes(String(raw));
	} else if (NUMERIC_OPS.has(cond.op) && defs[cond.metric]?.type === 'number') {
		const num = normalizeNumeric(node, cond.metric, defs);
		if (num === null) return 'UNKNOWN';
		if (cond.op === 'between') {
			const a = Number(cond.value);
			const b = Number(cond.value2);
			if (!Number.isFinite(a) || !Number.isFinite(b)) return 'UNKNOWN';
			result = num >= a && num <= b;
		} else {
			const target = Number(cond.value);
			if (!Number.isFinite(target)) return 'UNKNOWN';
			if (cond.op === '>=') result = num >= target;
			else if (cond.op === '<=') result = num <= target;
			else if (cond.op === '==') result = num === target;
			else result = num !== target;
		}
	} else {
		// 비수치 컬럼의 == / != 는 문자열 동치. 느슨한 비교(==)를 쓰지 않는다.
		const lhs = String(raw);
		const rhs = String(cond.value ?? '');
		if (cond.op === '==') result = lhs === rhs;
		else if (cond.op === '!=') result = lhs !== rhs;
		else return 'UNKNOWN';
	}
	return applyNegate(result ? 'PASS' : 'FAIL', cond.negate);
}

function applyNegate(v: Verdict, negate: boolean | undefined): Verdict {
	if (!negate || v === 'UNKNOWN') return v;
	return v === 'PASS' ? 'FAIL' : 'PASS';
}

/** 격자 1 회 순회로 rows / members / funnel 을 동시에 만든다. */
export function buildVerdictGrid(
	nodes: ScanNode[],
	conds: FilterCond[],
	defs: Record<string, MetricDef>
): VerdictGrid {
	const rows: RowVerdict[] = new Array(nodes.length);
	const members: ScanNode[] = [];
	let excludedForMissing = 0;

	for (let i = 0; i < nodes.length; i++) {
		const node = nodes[i];
		const verdicts: Verdict[] = new Array(conds.length);
		let pass = 0;
		let fail = 0;
		let unknown = 0;
		for (let c = 0; c < conds.length; c++) {
			const v = evalVerdict(node, conds[c], defs);
			verdicts[c] = v;
			if (v === 'PASS') pass++;
			else if (v === 'FAIL') fail++;
			else unknown++;
		}
		rows[i] = { node, verdicts, passCount: pass, failCount: fail, unknownCount: unknown };
		if (fail === 0 && unknown === 0) members.push(node);
		else if (fail === 0 && unknown > 0) excludedForMissing++;
	}

	return {
		rows,
		conds,
		members,
		funnel: buildFunnel(rows, conds),
		universe: nodes.length,
		excludedForMissing
	};
}

/**
 * 조건별 (통과 / 탈락 / 판정불능) 과 누적 생존자.
 * survivors 는 조건 0..i 를 전부 PASS 한 수라 앞 조건의 순서에 의존한다 (워터폴).
 */
export function buildFunnel(rows: RowVerdict[], conds: FilterCond[]): FunnelStep[] {
	return conds.map((cond, i) => {
		let pass = 0;
		let fail = 0;
		let unknown = 0;
		let survivors = 0;
		for (const row of rows) {
			const v = row.verdicts[i];
			if (v === 'PASS') pass++;
			else if (v === 'FAIL') fail++;
			else unknown++;
			if (row.verdicts.slice(0, i + 1).every((x) => x === 'PASS')) survivors++;
		}
		return { cond, pass, fail, unknown, survivors };
	});
}

/**
 * FAIL 이 정확히 k 개이고 UNKNOWN 이 0 인 행. 스크리너에서 가장 값진 산출물이다.
 *
 * UNKNOWN 을 배제하는 이유: 데이터가 없어서 못 넘은 것을 "아깝게 놓쳤다" 고 부르면 거짓말이다.
 *
 * 조건이 k 개 이하면 빈 목록이다. 조건 1 개에서 "1 개만 놓친 종목" 은 그냥 탈락자 전원이라
 * (실측: US 단일조건에서 6,028 사) 정보가 0 이다. 조건을 지우면 볼 수 있는 것을 근접후보라
 * 부르지 않는다.
 */
export function nearMiss(grid: VerdictGrid, k = 1): RowVerdict[] {
	if (grid.conds.length <= k) return [];
	return grid.rows.filter((r) => r.failCount === k && r.unknownCount === 0);
}

/** 컬럼별 유효 표본 수. "이 지표는 2,664 사 중 78 사에만 있다" 를 화면이 말하게 한다. */
export function coverageStats(nodes: ScanNode[], metrics: string[]): CoverageStat[] {
	return metrics.map((metric) => {
		let valid = 0;
		for (const n of nodes) if (hasValue((n as Record<string, unknown>)[metric])) valid++;
		return { metric, valid, total: nodes.length };
	});
}

/**
 * 한 조건의 임계값을 흔들어 목표 종목 수를 만드는 값을 역산한다.
 * 수치 조건(>= / <=)만 대상. 조건을 못 찾으면 null (억지 추정 금지).
 *
 * "40 종목이 되려면 ICR 을 2.0 에서 1.6 으로" 를 화면이 제안하게 한다.
 */
export function relaxThreshold(
	nodes: ScanNode[],
	conds: FilterCond[],
	condIndex: number,
	targetCount: number,
	defs: Record<string, MetricDef>
): number | null {
	const cond = conds[condIndex];
	if (!cond || (cond.op !== '>=' && cond.op !== '<=') || cond.negate) return null;

	// 다른 조건을 모두 PASS 한 종목만 후보. 그 종목들의 이 컬럼 값 분포에서 임계를 뽑는다.
	const others = conds.filter((_, i) => i !== condIndex);
	const values: number[] = [];
	for (const node of nodes) {
		if (others.some((c) => evalVerdict(node, c, defs) !== 'PASS')) continue;
		const v = normalizeNumeric(node, cond.metric, defs);
		if (v !== null) values.push(v);
	}
	if (values.length === 0) return null;

	// >= 면 큰 값이 통과. 내림차순 targetCount 번째 값이 목표를 만드는 임계.
	values.sort((a, b) => (cond.op === '>=' ? b - a : a - b));
	if (values.length < targetCount) return values[values.length - 1];
	return values[targetCount - 1];
}
