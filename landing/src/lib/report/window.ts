// 보고서 전용 분기/연간 분석 윈도 엔진 · build.ts 에서 격리(순수). 후행분기 정합성 가드(YTD 오염·이상치 제외).
import type { TerminalFinance, Num } from '@dartlab/ui-contracts';
import { finite } from './series';
import { pYear } from './format';

// ── 분기 데이터층 · 최근 N분기 윈도 + 후행분기 정합성 가드(YTD 오염·이상치 제외) ──
// 어댑터 standalone() 가 Q2~Q4 누계→단일분기를 정규화하나, 최신연도 Q1 은 비교 대상이 없어
// 원천 오염(영업이익률 regime 붕괴 등)을 못 거른다 → 후행 1~2분기를 본업 마진 범위로 검증해
// 벗어나면 분석 윈도에서 제외하고 각주(honest-skip 의 분기 버전). 정상 분기는 절대 삭제 안 함.
export interface QWindow {
	idx: number[];
	periods: string[];
	pick: (series: Num[]) => Num[];
	yoy: (series: Num[]) => Num[]; // 전년동기(4분기 전) 대비 %
	qoq: (series: Num[]) => Num[]; // 직전 분기 대비 %
	excluded: { period: string; opm: Num }[];
}
export function quarterWindow(tfQ: TerminalFinance, want = 8): QWindow | null {
	const P = tfQ.periods;
	const n = P.length;
	if (n < 2) return null;
	const opmFull = tfQ.ratios.find((r) => r.key === 'opm')?.values ?? [];
	const revFull = tfQ.statements.IS.find((r) => r.key === 'revenue')?.values ?? [];
	// 기준 범위 = 후행 2분기를 제외한 몸통의 영업이익률·매출 범위. 허용 버퍼는 *몸통 변동성(MAD)*
	// 기반 · 저마진 업종은 빡빡하게, 변동 큰 업종은 느슨하게(고정 ±12%p 매직넘버 제거, 종목 무관 규율).
	const bodyEnd = Math.max(1, n - 2);
	const bodyOpm = finite(opmFull.slice(0, bodyEnd));
	const bodyRev = finite(revFull.slice(0, bodyEnd));
	const opmMax = bodyOpm.length ? Math.max(...bodyOpm) : Infinity;
	const opmMin = bodyOpm.length ? Math.min(...bodyOpm) : -Infinity;
	const revMax = bodyRev.length ? Math.max(...bodyRev) : Infinity;
	const medOf = (a: number[]): number => { const s = [...a].sort((x, y) => x - y); return s.length ? s[Math.floor((s.length - 1) / 2)] : 0; };
	const opmMed = bodyOpm.length ? medOf(bodyOpm) : 0;
	const opmMad = bodyOpm.length ? medOf(bodyOpm.map((x) => Math.abs(x - opmMed))) : 0;
	const buf = Math.min(25, Math.max(8, 3 * opmMad)); // %p · 몸통 범위 밖 추가 허용폭
	const excluded: { period: string; opm: Num }[] = [];
	let end = n; // exclusive 상한
	for (let i = n - 1; i >= Math.max(1, n - 2); i--) {
		if (end !== i + 1) break; // 연속 후행만
		const o = opmFull[i];
		const r = revFull[i];
		const badOpm = o != null && Number.isFinite(o) && ((o as number) > opmMax + buf || (o as number) < opmMin - buf);
		const badRev = r != null && Number.isFinite(r) && (r as number) > revMax * 1.4;
		if (badOpm || badRev) {
			excluded.unshift({ period: P[i], opm: o });
			end = i;
		} else break;
	}
	const start = Math.max(0, end - want);
	const idx = Array.from({ length: end - start }, (_, k) => start + k);
	if (idx.length < 2) return null;
	const pick = (series: Num[]): Num[] => idx.map((i) => series[i] ?? null);
	const yoyFull = (series: Num[]): Num[] =>
		series.map((_, i) => {
			const cur = series[i];
			const prev = i >= 4 ? series[i - 4] : null;
			return cur != null && prev != null && Number.isFinite(cur) && Number.isFinite(prev) && (prev as number) !== 0 ? +(((((cur as number) - (prev as number)) / Math.abs(prev as number)) * 100)).toFixed(1) : null;
		});
	const qoqFull = (series: Num[]): Num[] =>
		series.map((_, i) => {
			const cur = series[i];
			const prev = i >= 1 ? series[i - 1] : null;
			return cur != null && prev != null && Number.isFinite(cur) && Number.isFinite(prev) && (prev as number) !== 0 ? +(((((cur as number) - (prev as number)) / Math.abs(prev as number)) * 100)).toFixed(1) : null;
		});
	return { idx, periods: idx.map((i) => P[i]), pick, yoy: (s) => pick(yoyFull(s)), qoq: (s) => pick(qoqFull(s)), excluded };
}

// 연간 윈도 · QWindow 와 동형 인터페이스(분기/연간 단일 코드경로). YoY lag=1년.
export function annualWindow(tfA: TerminalFinance, want = 6): QWindow | null {
	const P = tfA.periods.map(pYear);
	const n = Math.min(want, P.length);
	if (n < 2) return null;
	const start = P.length - n;
	const idx = Array.from({ length: n }, (_, k) => start + k);
	const pick = (s: Num[]): Num[] => idx.map((i) => s[i] ?? null);
	const yoyFull = (s: Num[]): Num[] => s.map((_, i) => { const c = s[i], p = i >= 1 ? s[i - 1] : null; return c != null && p != null && Number.isFinite(c) && Number.isFinite(p) && (p as number) !== 0 ? +((((c as number) - (p as number)) / Math.abs(p as number)) * 100).toFixed(1) : null; });
	return { idx, periods: idx.map((i) => P[i]), pick, yoy: (s) => pick(yoyFull(s)), qoq: (s) => pick(yoyFull(s)), excluded: [] };
}
