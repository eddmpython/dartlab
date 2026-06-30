// 시장 관점 계산 · 베타(OLS)·상대강도·PER 자기역사. 신규 '추가개발'(엔진 개념 부족분).
// runtime 패키지(터미널 공유) 미변경 · 보고서 전용 순수함수로 격리.
import type { Candle } from '@dartlab/ui-contracts';

export interface BetaResult {
	beta: number;
	r2: number;
	days: number; // 정렬된 거래일 수(베타 회귀 윈도)
}

/** 일간 수익률 회귀 β = Cov(r_i, r_m)/Var(r_m). 시장 캔들과 *날짜 정렬*된 구간만 사용. */
export function calcBeta(stock: Candle[], market: Candle[], maxDays = 500): BetaResult | null {
	if (!stock?.length || !market?.length) return null;
	const mMap = new Map<string, number>();
	for (const c of market) if (Number.isFinite(c.c) && c.c > 0) mMap.set(c.t, c.c);
	const sSorted = [...stock].filter((c) => Number.isFinite(c.c) && c.c > 0).sort((a, b) => a.t.localeCompare(b.t));
	const aligned: { sc: number; mc: number }[] = [];
	for (const c of sSorted) {
		const mc = mMap.get(c.t);
		if (mc != null) aligned.push({ sc: c.c, mc });
	}
	const tail = aligned.slice(-maxDays);
	if (tail.length < 60) return null; // 최소 ~3개월 거래일
	const rs: number[] = [];
	const rm: number[] = [];
	for (let i = 1; i < tail.length; i++) {
		rs.push(tail[i].sc / tail[i - 1].sc - 1);
		rm.push(tail[i].mc / tail[i - 1].mc - 1);
	}
	const n = rs.length;
	const mean = (a: number[]) => a.reduce((x, y) => x + y, 0) / a.length;
	const ms = mean(rs);
	const mm = mean(rm);
	let cov = 0;
	let varm = 0;
	let vars = 0;
	for (let i = 0; i < n; i++) {
		cov += (rs[i] - ms) * (rm[i] - mm);
		varm += (rm[i] - mm) ** 2;
		vars += (rs[i] - ms) ** 2;
	}
	if (varm === 0) return null;
	const beta = cov / varm;
	const r2 = vars > 0 ? (cov * cov) / (varm * vars) : 0;
	return { beta, r2, days: tail.length };
}

/** 연말(각 캘린더 연도 마지막 거래일) 종가 맵 · PER/PBR 자기역사 매칭용. */
export function yearEndCloses(candles: Candle[]): Map<string, number> {
	const byYear = new Map<string, { t: string; c: number }>();
	for (const c of candles) {
		if (!Number.isFinite(c.c) || c.c <= 0 || c.t.length < 4) continue;
		const y = c.t.slice(0, 4);
		const prev = byYear.get(y);
		if (!prev || c.t > prev.t) byYear.set(y, { t: c.t, c: c.c });
	}
	const out = new Map<string, number>();
	for (const [y, v] of byYear) out.set(y, v.c);
	return out;
}

/** 52주(최근 250 거래일) 고저·현재가·1년 수익률. */
export function priceSummary(candles: Candle[]): { last: number; hi: number; lo: number; ret1y: number | null; tv: number | null } | null {
	const s = [...candles].filter((c) => Number.isFinite(c.c) && c.c > 0).sort((a, b) => a.t.localeCompare(b.t));
	if (!s.length) return null;
	const win = s.slice(-250);
	const closes = win.map((c) => c.c);
	const last = closes[closes.length - 1];
	const hi = Math.max(...win.map((c) => c.h || c.c));
	const lo = Math.min(...win.map((c) => c.l || c.c));
	const first = closes[0];
	const ret1y = first > 0 ? last / first - 1 : null;
	const tv = win[win.length - 1].tv ?? null;
	return { last, hi, lo, ret1y, tv };
}
