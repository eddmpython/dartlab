// 백테스트 차트 좌표 SSOT · 손수 SVG 다벌 중복 제거 + preserveAspectRatio="none" 왜곡 박멸의 단일 진입점.
// 순수함수(Svelte·DOM 의존 0) · 브라우저 없이 좌표 수식을 단위검증할 수 있다(chartFrame.test.ts).
// EquityChart·MonthlyReturnsHeatmap 등 모달 차트가 import. 실측 px 좌표는 각 컴포넌트가 clientWidth 로 인라인.

/**
 * nice 눈금 배열 · [lo,hi] 범위를 1/2/5 배수 step 으로 스냅해 target 개 근처 눈금을 만든다.
 * y축 가로 그리드(정량 비교의 핵심). 빈/역전 범위는 [] (호출부에서 그리드 생략).
 */
export function niceTicks(lo: number, hi: number, target = 5): number[] {
	if (!Number.isFinite(lo) || !Number.isFinite(hi) || hi <= lo || target < 1) return [];
	const raw = (hi - lo) / target;
	const mag = Math.pow(10, Math.floor(Math.log10(raw)));
	const norm = raw / mag;
	const step = (norm >= 5 ? 5 : norm >= 2 ? 2 : 1) * mag;
	const first = Math.ceil(lo / step - 1e-9) * step;
	const out: number[] = [];
	for (let v = first; v <= hi + step * 1e-6; v += step) out.push(+v.toFixed(6));
	return out;
}

/**
 * 연 경계 인덱스(ts[i] 의 YYYY 가 바뀌는 지점) · x축 세로 그리드/연도 라벨. ts=YYYYMMDD, candles 정렬.
 * 라벨이 max 개를 넘으면 균등 솎음(LOD) · 장기 구간에서 라벨 겹침 방지.
 */
export function yearTicks(ts: string[], max = 8): { idx: number; label: string }[] {
	if (ts.length < 1) return [];
	const out: { idx: number; label: string }[] = [];
	for (let i = 0; i < ts.length; i++) {
		if (i === 0 || ts[i].slice(0, 4) !== ts[i - 1].slice(0, 4)) out.push({ idx: i, label: ts[i].slice(0, 4) });
	}
	if (out.length <= max) return out;
	const stride = Math.ceil(out.length / max);
	return out.filter((_, k) => k % stride === 0);
}

/**
 * 마우스 x(px) → 최근접 데이터 인덱스(크로스헤어/호버). padL=좌측 축 여백, plotW=플롯 폭.
 * 범위 밖은 0..n-1 로 clamp.
 */
export function nearestIdx(mx: number, padL: number, plotW: number, n: number): number {
	if (n <= 1 || plotW <= 0) return 0;
	const r = Math.round(((mx - padL) / plotW) * (n - 1));
	return Math.max(0, Math.min(n - 1, r));
}

/**
 * 월별 수익률 매트릭스 · 월말 equity 비율(직전 월말 대비). 첫 달은 구간 시작값(eq[0]) 기준 근사.
 * equity=평가창 non-null 슬라이스, ts=동일 인덱스 YYYYMMDD. 결측 월은 null(거짓 0% 금지).
 * 색·정렬은 호출부(히트맵)가 결정 · 여기선 사실 행렬만(argmax 강조 없음).
 */
export interface MonthlyReturns {
	years: number[]; // 오름차순 고정(시간 순서 · 수익순 정렬 금지)
	cell: (year: number, month: number) => number | null; // month 1..12, ret%
	ytd: (year: number) => number | null; // 연 누적(월 복리, 결측 스킵)
}
export function monthlyReturns(equity: number[], ts: string[]): MonthlyReturns {
	const n = Math.min(equity.length, ts.length);
	const cells = new Map<string, number | null>();
	const ytdMap = new Map<number, number | null>();
	if (n >= 2) {
		const monthEnd: { y: number; m: number; idx: number }[] = [];
		for (let i = 0; i < n; i++) {
			if (i === n - 1 || ts[i].slice(0, 6) !== ts[i + 1].slice(0, 6)) {
				monthEnd.push({ y: +ts[i].slice(0, 4), m: +ts[i].slice(4, 6), idx: i });
			}
		}
		let prev = equity[0];
		for (const me of monthEnd) {
			const cur = equity[me.idx];
			const ret = cur != null && prev ? (cur / prev - 1) * 100 : null;
			cells.set(`${me.y}-${me.m}`, ret);
			if (cur != null) prev = cur;
		}
		const years = [...new Set(monthEnd.map((me) => me.y))].sort((a, b) => a - b);
		for (const y of years) {
			let acc = 1;
			let any = false;
			for (let m = 1; m <= 12; m++) {
				const r = cells.get(`${y}-${m}`);
				if (r != null) {
					acc *= 1 + r / 100;
					any = true;
				}
			}
			ytdMap.set(y, any ? (acc - 1) * 100 : null);
		}
		return { years, cell: (y, m) => cells.get(`${y}-${m}`) ?? null, ytd: (y) => ytdMap.get(y) ?? null };
	}
	return { years: [], cell: () => null, ytd: () => null };
}
