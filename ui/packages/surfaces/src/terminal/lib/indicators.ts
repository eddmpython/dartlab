// 보조지표 · OHLCV close 배열에서 클라이언트 계산 (gather 지표는 Python 서버용이라 브라우저는 직접 산출).
export function sma(a: number[], p: number): (number | null)[] {
	const o: (number | null)[] = [];
	for (let i = 0; i < a.length; i++) {
		if (i < p - 1) {
			o.push(null);
			continue;
		}
		let s = 0;
		for (let j = i - p + 1; j <= i; j++) s += a[j];
		o.push(s / p);
	}
	return o;
}
export function ema(a: number[], p: number): number[] {
	const k = 2 / (p + 1);
	const o: number[] = [];
	let pr = 0;
	a.forEach((v, i) => {
		pr = i === 0 ? v : v * k + pr * (1 - k);
		o.push(pr);
	});
	return o;
}
export function rsi(a: number[], p = 14): (number | null)[] {
	const o: (number | null)[] = [null];
	let g = 0;
	let l = 0;
	for (let i = 1; i < a.length; i++) {
		const c = a[i] - a[i - 1];
		const u = Math.max(c, 0);
		const d = Math.max(-c, 0);
		if (i <= p) {
			g += u;
			l += d;
			if (i === p) {
				g /= p;
				l /= p;
				o.push(100 - 100 / (1 + g / (l || 1e-9)));
			} else o.push(null);
		} else {
			g = (g * (p - 1) + u) / p;
			l = (l * (p - 1) + d) / p;
			o.push(100 - 100 / (1 + g / (l || 1e-9)));
		}
	}
	return o;
}
export interface Macd {
	line: number[];
	signal: number[];
	hist: number[];
}
export function macd(a: number[], fast = 12, slow = 26, sig = 9): Macd {
	const eFast = ema(a, fast);
	const eSlow = ema(a, slow);
	const line = eFast.map((v, i) => v - eSlow[i]);
	const signal = ema(line, sig);
	const hist = line.map((v, i) => v - signal[i]);
	return { line, signal, hist };
}
export interface Stochastic {
	k: (number | null)[];
	d: (number | null)[];
}
export function stochastic(highs: number[], lows: number[], closes: number[], kP = 14, dP = 3): Stochastic {
	const k: (number | null)[] = [];
	for (let i = 0; i < closes.length; i++) {
		if (i < kP - 1) {
			k.push(null);
			continue;
		}
		let hh = -Infinity;
		let ll = Infinity;
		for (let j = i - kP + 1; j <= i; j++) {
			hh = Math.max(hh, highs[j]);
			ll = Math.min(ll, lows[j]);
		}
		k.push(hh === ll ? 50 : ((closes[i] - ll) / (hh - ll)) * 100);
	}
	const d: (number | null)[] = [];
	for (let i = 0; i < k.length; i++) {
		if (i < kP - 1 + dP - 1) {
			d.push(null);
			continue;
		}
		let s = 0;
		let c = 0;
		for (let j = i - dP + 1; j <= i; j++) {
			const v = k[j];
			if (v != null) {
				s += v;
				c++;
			}
		}
		d.push(c ? s / c : null);
	}
	return { k, d };
}
export function obv(closes: number[], vols: number[]): number[] {
	const o: number[] = [0];
	for (let i = 1; i < closes.length; i++) {
		const prev = o[i - 1];
		o.push(closes[i] > closes[i - 1] ? prev + vols[i] : closes[i] < closes[i - 1] ? prev - vols[i] : prev);
	}
	return o;
}
export interface Bollinger {
	mid: (number | null)[];
	upper: (number | null)[];
	lower: (number | null)[];
}
// ATR(평균진폭) · Wilder 평활. 고저종 입력. 변동성 손절·채널·필터의 기반(종가만 쓰는 6프리셋의 약점 보강).
export function atr(highs: number[], lows: number[], closes: number[], p = 14): (number | null)[] {
	const tr: number[] = [];
	for (let i = 0; i < closes.length; i++) {
		if (i === 0) { tr.push(highs[i] - lows[i]); continue; }
		const pc = closes[i - 1];
		tr.push(Math.max(highs[i] - lows[i], Math.abs(highs[i] - pc), Math.abs(lows[i] - pc)));
	}
	const out: (number | null)[] = [];
	let prev = 0;
	for (let i = 0; i < tr.length; i++) {
		if (i < p - 1) { out.push(null); continue; }
		if (i === p - 1) { let s = 0; for (let j = 0; j < p; j++) s += tr[j]; prev = s / p; out.push(prev); continue; }
		prev = (prev * (p - 1) + tr[i]) / p; // Wilder
		out.push(prev);
	}
	return out;
}
// 거래량 단순이평 · 거래량 확인(fake breakout 제거)용. volRatio = vol / volSma 로 쓴다.
export function volSma(vols: number[], p = 20): (number | null)[] {
	return sma(vols, p);
}
// 실현 변동성(연환산 %) · 종가 로그수익 표준편차 × √252 × 100. 변동성 필터·저변동 전략.
export function realizedVol(closes: number[], p = 20): (number | null)[] {
	const out: (number | null)[] = [];
	for (let i = 0; i < closes.length; i++) {
		if (i < p) { out.push(null); continue; }
		const rets: number[] = [];
		for (let j = i - p + 1; j <= i; j++) if (closes[j - 1] > 0 && closes[j] > 0) rets.push(Math.log(closes[j] / closes[j - 1]));
		if (rets.length < 2) { out.push(null); continue; }
		const m = rets.reduce((a, r) => a + r, 0) / rets.length;
		const v = rets.reduce((a, r) => a + (r - m) ** 2, 0) / (rets.length - 1);
		out.push(Math.sqrt(v) * Math.sqrt(252) * 100);
	}
	return out;
}
export function bollinger(a: number[], p = 20, mult = 2): Bollinger {
	const mid = sma(a, p);
	const upper: (number | null)[] = [];
	const lower: (number | null)[] = [];
	for (let i = 0; i < a.length; i++) {
		const m = mid[i];
		if (m == null) {
			upper.push(null);
			lower.push(null);
			continue;
		}
		let s = 0;
		for (let j = i - p + 1; j <= i; j++) s += (a[j] - m) ** 2;
		const sd = Math.sqrt(s / p);
		upper.push(m + mult * sd);
		lower.push(m - mult * sd);
	}
	return { mid, upper, lower };
}
