// 거시 시뮬 TS 런타임 계산 · Python 정본(src/dartlab/macro/simulate) golden parity.
// 같은 결정론 패널(난수 0)에서 Python forwardFan 값과 byte 수준 일치 검증 → drift 차단.
// golden = `uv run python ... estimateBvar/forwardFan` (해석적이라 재현 정확).
import { describe, expect, it } from 'vitest';
import { conditionalPath, estimateBvar, forwardFan, maxCompanionModulus, type SimVarSpec } from './macroSimCompute';

// Python 과 동일 recurrence 고정 패널 (T=48, N=3).
function fixedPanel(): number[][] {
	const T = 48, N = 3;
	const panel: number[][] = [[0.1, 0.2, 3.0]];
	for (let t = 1; t < T; t++) {
		const prev = panel[t - 1];
		const row: number[] = [];
		for (let i = 0; i < N; i++) row.push(0.6 * prev[i] - 0.1 * prev[(i + 1) % 3] + 0.05 * (((t * 7 + i * 13) % 11 - 5) / 10));
		panel.push(row);
	}
	return panel;
}
const SPECS: SimVarSpec[] = [
	{ id: 'A', label: 'A', transform: 'logdiff100' },
	{ id: 'B', label: 'B', transform: 'logdiff100' },
	{ id: 'C', label: 'C', transform: 'level' }
];
const TOL = 1e-5;

describe('macroSimCompute · Python golden parity (해석적 BVAR, 결정론)', () => {
	const panel = fixedPanel();
	const fit = estimateBvar(panel, SPECS, 4, 0.3, [100, 100, 3]);

	it('추정 안정·companion eig Python 근사(Gelfand 범위)', () => {
		expect(fit).not.toBeNull();
		// Gelfand(Frobenius) 추정 · exact eig 0.734461 을 ~수% 과대평가(차원인자). 게이트(<1)·범위 일치.
		const eig = maxCompanionModulus(fit!);
		expect(eig).toBeGreaterThan(0.70);
		expect(eig).toBeLessThan(0.80);
	});

	it('fan q50/q5/q95 Python golden 일치 (변수 A·C, h=0/5/11)', () => {
		const fan = forwardFan(fit!, panel, 12);
		const a = fan['A'], c = fan['C'];
		// A
		[[0, 0.00822], [5, 0.001968], [11, 0.000254]].forEach(([h, g]) => expect(a.q50[h]).toBeCloseTo(g, 5));
		[[0, -0.011145], [5, -0.020121], [11, -0.021924]].forEach(([h, g]) => expect(a.q5[h]).toBeCloseTo(g, 5));
		[[0, 0.027585], [5, 0.024057], [11, 0.022432]].forEach(([h, g]) => expect(a.q95[h]).toBeCloseTo(g, 5));
		// C
		[[0, 0.007566], [5, -0.001677], [11, -0.000064]].forEach(([h, g]) => expect(c.q50[h]).toBeCloseTo(g, 5));
		[[0, -0.005705], [5, -0.021327], [11, -0.019822]].forEach(([h, g]) => expect(c.q5[h]).toBeCloseTo(g, 5));
		[[0, 0.020838], [5, 0.017974], [11, 0.019694]].forEach(([h, g]) => expect(c.q95[h]).toBeCloseTo(g, 5));
	});

	it('logdiff 레벨 누적 Python golden 일치 (A level_q50[11])', () => {
		const fan = forwardFan(fit!, panel, 12);
		expect(fan['A'].level_q50![11]).toBeCloseTo(100.006994, 4);
	});

	it('밴드 단조 확대 + 분위 순서', () => {
		const fan = forwardFan(fit!, panel, 12);
		for (const lab of ['A', 'B', 'C']) {
			const r = fan[lab];
			for (let h = 0; h < 12; h++) expect(r.q5[h]).toBeLessThanOrEqual(r.q50[h] + TOL);
			const w = (h: number) => r.q95[h] - r.q5[h];
			for (let h = 0; h < 11; h++) expect(w(h + 1)).toBeGreaterThanOrEqual(w(h) - TOL);
		}
	});

	// 시나리오 조건부 · Python conditionalPath(condIdx=2·δ=[0.5]*4·H=12) golden.
	it('조건부 경로 Python golden 일치 (자유변수 A·조건변수 C)', () => {
		const cp = conditionalPath(fit!, panel, 2, [0.5, 0.5, 0.5, 0.5], 12);
		const a = cp['A'], c = cp['C'];
		// 자유 변수 A · 정책 충격 경로에 반응
		[[0, 0.250891], [5, 0.109995], [11, 0.006392]].forEach(([h, g]) => expect(a.q50[h]).toBeCloseTo(g, 5));
		[[0, 0.236329], [5, 0.088677], [11, -0.015774]].forEach(([h, g]) => expect(a.q5[h]).toBeCloseTo(g, 5));
		[[0, 0.265452], [5, 0.131313], [11, 0.028558]].forEach(([h, g]) => expect(a.q95[h]).toBeCloseTo(g, 5));
		// 조건 변수 C · q50 golden + h=0..3 하드 고정(밴드 붕괴: q5==q95)
		[[0, 0.507566], [5, 0.093224], [11, 0.002699]].forEach(([h, g]) => expect(c.q50[h]).toBeCloseTo(g, 5));
		for (let h = 0; h < 4; h++) expect(c.q95[h] - c.q5[h]).toBeCloseTo(0, 6);
	});

	it('조건부 logdiff 레벨 누적 Python golden 일치 (A level_q50[11])', () => {
		const cp = conditionalPath(fit!, panel, 2, [0.5, 0.5, 0.5, 0.5], 12);
		expect(cp['A'].level_q50![11]).toBeCloseTo(101.203293, 4);
	});
});
