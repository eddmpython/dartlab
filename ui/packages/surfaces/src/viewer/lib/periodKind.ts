// computePeriodKind · 회사별 보고서 유형 보정 (사업보고서 vs 분기/반기). 공시뷰어 "연간만" 필터용.
//
// 연간보고서(사업보고서)는 회계연도-말 분기에 위치하고 분기/반기보다 본문(비빈 셀)이 많다. 완전연도(분기≥3 보유)의
// 분기별 비빈셀 median 중 dominant 분기를 annual 로 검출 → 비-12월 결산도 자동 흡수(3월결산=Q1, 6월결산=Q2).
// in-progress·bookend(분기<3) 연도는 표본 제외, dominance 불명확하면 Q4(12월 결산) fallback. period 분기 유도보다 견고.

const quarterOf = (p: string): number => {
	const m = /Q([1-4])$/.exec(p);
	return m ? parseInt(m[1], 10) : 0;
};

function median(xs: number[]): number {
	if (!xs.length) return 0;
	const s = [...xs].sort((a, b) => a - b);
	const mid = Math.floor(s.length / 2);
	return s.length % 2 ? s[mid] : (s[mid - 1] + s[mid]) / 2;
}

export function computePeriodKind(periods: string[], cellCount: Record<string, number>): Record<string, 'annual' | 'quarter'> {
	const qByYear = new Map<string, Set<number>>();
	for (const p of periods) {
		const q = quarterOf(p);
		if (!q) continue;
		const y = p.slice(0, 4);
		let s = qByYear.get(y);
		if (!s) qByYear.set(y, (s = new Set()));
		s.add(q);
	}
	const complete = new Set([...qByYear].filter(([, s]) => s.size >= 3).map(([y]) => y));
	const byQ: Record<number, number[]> = { 1: [], 2: [], 3: [], 4: [] };
	for (const p of periods) {
		const q = quarterOf(p);
		if (q && complete.has(p.slice(0, 4))) byQ[q].push(cellCount[p] ?? 0);
	}
	const med = [1, 2, 3, 4].map((q) => ({ q, m: median(byQ[q]) })).sort((a, b) => b.m - a.m);
	// dominant(상위 median > 1.3× 차순위) 분기 = annual, 아니면 Q4(12월 결산) fallback.
	const annualQ = med[0].m > 0 && med[0].m > 1.3 * (med[1].m || 0) ? med[0].q : 4;
	const out: Record<string, 'annual' | 'quarter'> = {};
	for (const p of periods) out[p] = quarterOf(p) === annualQ ? 'annual' : 'quarter';
	return out;
}
