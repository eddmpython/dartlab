// 종목 ↔ 거시 동행(상관) · "어떤 거시가 이 종목과 같이 움직였나" 발견용.
// ⚠ 상관(co-movement)일 뿐 인과(견인) 아님 · UI 라벨로 명시(04 §8 정직 척추).
// 방법: 월말 종가 MoM 수익률 vs 거시 월말값 1차차분(diff). 겹치는 월(최소 minN)에 Pearson. 부호 유의(역상관 포함).
//   Pearson 은 스케일 불변이라 거시 단위(원·%·pt) 혼재 무관. 둘 다 1차차분이라 추세 공선형(가짜 상관) 완화.
import type { Candle, MacroPoint } from '@dartlab/ui-contracts';

const ymOf = (d: string): string => d.slice(0, 6);

/** YYYYMM → 그 달 마지막 종가. 입력 오름차순 가정(뒤 = 최신) → 같은 달 마지막 write 가 월말. */
function monthEndClose(candles: Candle[]): Map<string, number> {
	const m = new Map<string, number>();
	for (const k of candles) if (k.t && Number.isFinite(k.c)) m.set(ymOf(k.t), k.c);
	return m;
}
/** YYYYMM → 그 달 마지막 거시값. */
function monthEndVal(points: MacroPoint[]): Map<string, number> {
	const m = new Map<string, number>();
	for (const p of points) if (p.d && Number.isFinite(p.v)) m.set(ymOf(p.d), p.v);
	return m;
}

function pearson(xs: number[], ys: number[]): number {
	const n = xs.length;
	if (n < 2) return 0;
	let sx = 0, sy = 0, sxx = 0, syy = 0, sxy = 0;
	for (let i = 0; i < n; i++) {
		const x = xs[i];
		const y = ys[i];
		sx += x; sy += y; sxx += x * x; syy += y * y; sxy += x * y;
	}
	const cov = sxy - (sx * sy) / n;
	const vx = sxx - (sx * sx) / n;
	const vy = syy - (sy * sy) / n;
	const den = Math.sqrt(vx * vy);
	return den === 0 ? 0 : cov / den;
}

export interface CoMovePoint {
	ym: string;
	stockReturn: number;
	macroDiff: number;
}

export interface CoMover {
	id: string;
	corr: number; // [-1,1] 부호 = 정/역 동행
	n: number; // 겹친 월 수
	points: CoMovePoint[]; // x=macroDiff, y=stockReturn. UI 산점도용 최근 표본.
}

/**
 * 종목 캔들 ↔ 거시 시리즈들의 동행 순위(|corr| 내림차순).
 * @param windowMonths 최근 개월 한도(0=가용 전체). 캔들 prop 이 이미 ~2년 bounded 라 기본 0.
 * @param minN 최소 겹침 월(통계 안정 하한).
 */
export function rankCoMovers(
	candles: Candle[],
	series: { id: string; points: MacroPoint[] }[],
	windowMonths = 0,
	minN = 12
): CoMover[] {
	if (!candles.length) return [];
	const closeByMonth = monthEndClose(candles);
	const allMonths = [...closeByMonth.keys()].sort();
	const win = windowMonths > 0 ? allMonths.slice(-windowMonths) : allMonths;
	if (win.length < minN + 1) return [];
	// 종목 월수익률
	const stockRet = new Map<string, number>();
	for (let i = 1; i < win.length; i++) {
		const a = closeByMonth.get(win[i - 1]);
		const b = closeByMonth.get(win[i]);
		if (a != null && b != null && a > 0) stockRet.set(win[i], b / a - 1);
	}
	const out: CoMover[] = [];
	for (const s of series) {
		const valByMonth = monthEndVal(s.points);
		const xs: number[] = [];
		const ys: number[] = [];
		const points: CoMovePoint[] = [];
		for (let i = 1; i < win.length; i++) {
			const r = stockRet.get(win[i]);
			const cur = valByMonth.get(win[i]);
			const prev = valByMonth.get(win[i - 1]);
			if (r == null || cur == null || prev == null) continue;
			const macroDiff = cur - prev;
			xs.push(r);
			ys.push(macroDiff); // 거시 1차차분
			points.push({ ym: win[i], stockReturn: +r.toFixed(4), macroDiff: +macroDiff.toFixed(4) });
		}
		if (xs.length < minN) continue;
		const c = pearson(xs, ys);
		if (Number.isFinite(c)) out.push({ id: s.id, corr: +c.toFixed(2), n: xs.length, points: points.slice(-96) });
	}
	out.sort((a, b) => Math.abs(b.corr) - Math.abs(a.corr));
	return out;
}
