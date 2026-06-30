// 증권사 필수·klinecharts 미내장 커스텀 지표 · ICHI(일목균형표)·ENV(Envelope). econOverlay 등록 패턴.
// ICHI 핵심: 선행스팬은 calc 단계에서 +기준기간 선-시프트(이력 구간은 기본 figure 가 그림 = y축 range·툴팁 자동),
//   draw 는 구름 fill + 미래 구간 연장만 그리고 return false → 기본 5선이 구름 "위에" 렌더(klinecharts 는
//   draw 를 figures 보다 먼저 실행). 미래 x 좌표는 dataIndexToCoordinate 가 길이 클램프 없는 순수 산술이라 외삽 가능.
// styles.lines 는 deep-merge 안 됨 · color/size/style/smooth/dashedValue 완전 지정(누락 = 내부 draw 크래시).
type Num = number | null;

const hhll = (highs: number[], lows: number[], i: number, p: number): [number, number] | null => {
	if (i < p - 1) return null;
	let hh = -Infinity;
	let ll = Infinity;
	for (let j = i - p + 1; j <= i; j++) {
		if (highs[j] > hh) hh = highs[j];
		if (lows[j] < ll) ll = lows[j];
	}
	return [hh, ll];
};

const line = (color: string, dashed = false) => ({ color, size: 1, style: dashed ? 'dashed' : 'solid', smooth: false, dashedValue: [4, 4] });

interface IchiDatum {
	conv?: number;
	base?: number;
	chikou?: number;
	spanA?: number;
	spanB?: number;
	_a?: number; // 비-figure 원시값 · draw 미래 연장용 (y축 range 미기여)
	_b?: number;
}

let registered = false;
export function registerExtraIndicators(kc: { registerIndicator: (t: unknown) => void }): void {
	if (registered) return;
	registered = true;

	kc.registerIndicator({
		name: 'ICHI',
		shortName: 'ICHI',
		series: 'price',
		precision: 0,
		calcParams: [9, 26, 52],
		figures: [
			{ key: 'conv', title: '전환 ', type: 'line' },
			{ key: 'base', title: '기준 ', type: 'line' },
			{ key: 'chikou', title: '후행 ', type: 'line' },
			{ key: 'spanA', title: '선행A ', type: 'line' },
			{ key: 'spanB', title: '선행B ', type: 'line' }
		],
		styles: { lines: [line('#f0616f'), line('#5b9bf0'), line('#8b919e', true), line('#34d399'), line('#c084fc')] },
		calc: (dataList: { high: number; low: number; close: number }[], indicator: { calcParams: number[] }): IchiDatum[] => {
			const [p1, p2, p3] = indicator.calcParams;
			const highs = dataList.map((d) => d.high);
			const lows = dataList.map((d) => d.low);
			const n = dataList.length;
			const rawA: Num[] = new Array(n).fill(null);
			const rawB: Num[] = new Array(n).fill(null);
			const out: IchiDatum[] = new Array(n);
			for (let i = 0; i < n; i++) {
				const h1 = hhll(highs, lows, i, p1);
				const h2 = hhll(highs, lows, i, p2);
				const h3 = hhll(highs, lows, i, p3);
				const conv = h1 ? (h1[0] + h1[1]) / 2 : null;
				const base = h2 ? (h2[0] + h2[1]) / 2 : null;
				rawA[i] = conv != null && base != null ? (conv + base) / 2 : null;
				rawB[i] = h3 ? (h3[0] + h3[1]) / 2 : null;
				const d: IchiDatum = {};
				if (conv != null) d.conv = conv;
				if (base != null) d.base = base;
				if (i + p2 < n) d.chikou = dataList[i + p2].close;
				const a = i - p2 >= 0 ? rawA[i - p2] : null; // 선행 = +p2 선-시프트
				const b = i - p2 >= 0 ? rawB[i - p2] : null;
				if (a != null) d.spanA = a;
				if (b != null) d.spanB = b;
				if (rawA[i] != null) d._a = rawA[i] as number;
				if (rawB[i] != null) d._b = rawB[i] as number;
				out[i] = d;
			}
			return out;
		},
		draw: ({ ctx, indicator, visibleRange, xAxis, yAxis }: any): boolean => {
			const result = indicator.result as IchiDatum[];
			const n = result.length;
			if (!n) return false;
			const p2 = indicator.calcParams[1] ?? 26;
			// 구름 좌표 수집: 이력(i<n: spanA/spanB) + 미래(i>=n: result[i-p2]._a/_b · calc 산출 재사용, 즉석 재계산 0)
			const from = Math.max(0, visibleRange.from);
			const to = Math.min(n + p2, visibleRange.realTo ?? visibleRange.to + p2);
			const pts: { x: number; a: number; b: number }[] = [];
			for (let i = from; i < to; i++) {
				const a = i < n ? result[i]?.spanA : result[i - p2]?._a;
				const b = i < n ? result[i]?.spanB : result[i - p2]?._b;
				if (a == null || b == null) continue;
				pts.push({ x: xAxis.convertToPixel(i), a: yAxis.convertToPixel(a), b: yAxis.convertToPixel(b) });
			}
			// 부호 전환 지점에서 분할해 양운/음운 fill
			let seg: typeof pts = [];
			const flush = () => {
				if (seg.length < 2) { seg = []; return; }
				ctx.beginPath();
				ctx.moveTo(seg[0].x, seg[0].a);
				for (let i = 1; i < seg.length; i++) ctx.lineTo(seg[i].x, seg[i].a);
				for (let i = seg.length - 1; i >= 0; i--) ctx.lineTo(seg[i].x, seg[i].b);
				ctx.closePath();
				ctx.fillStyle = seg[0].a <= seg[0].b ? 'rgba(52,211,153,0.10)' : 'rgba(240,97,111,0.10)';
				ctx.fill();
				seg = [];
			};
			let bull: boolean | null = null;
			for (const p of pts) {
				const nowBull = p.a <= p.b; // 픽셀 y 는 아래로 증가 · a 픽셀이 작으면 spanA 가 위(양운)
				if (bull != null && nowBull !== bull) flush();
				bull = nowBull;
				seg.push(p);
			}
			flush();
			// 미래 구간 선행A/B 라인 연장 (이력 구간 선은 기본 figure 가 그림)
			const future = pts.filter((_, idx) => from + idx >= n - 1);
			if (future.length >= 2) {
				ctx.lineWidth = 1;
				ctx.setLineDash([]);
				ctx.strokeStyle = '#34d399';
				ctx.beginPath();
				future.forEach((p, i) => (i ? ctx.lineTo(p.x, p.a) : ctx.moveTo(p.x, p.a)));
				ctx.stroke();
				ctx.strokeStyle = '#c084fc';
				ctx.beginPath();
				future.forEach((p, i) => (i ? ctx.lineTo(p.x, p.b) : ctx.moveTo(p.x, p.b)));
				ctx.stroke();
			}
			return false; // 기본 figures(5선)가 구름 위에 렌더
		}
	});

	kc.registerIndicator({
		name: 'TVAL',
		shortName: 'TVAL',
		series: 'volume',
		// turnover 는 toK 에서 억 단위로 변환 · 축약(K/M) 대신 콤마 정수가 한국 단위 관행
		shouldFormatBigNumber: false,
		precision: 0,
		minValue: 0,
		figures: [
			{
				key: 'tval',
				title: '대금(억) ',
				type: 'bar',
				baseValue: 0,
				styles: (data: { current?: { kLineData?: { close: number; open: number } } }) => {
					const k = data.current?.kLineData;
					return { color: !k || k.close === k.open ? '#8b919e' : k.close > k.open ? '#34d399' : '#f0616f' };
				}
			}
		],
		calc: (dataList: { turnover?: number }[]) => dataList.map((d) => ({ tval: d.turnover ?? null }))
	});

	kc.registerIndicator({
		name: 'ENV',
		shortName: 'ENV',
		series: 'price',
		precision: 0,
		calcParams: [20, 6],
		figures: [
			{ key: 'up', title: '상단 ', type: 'line' },
			{ key: 'mid', title: '중심 ', type: 'line' },
			{ key: 'lo', title: '하단 ', type: 'line' }
		],
		styles: { lines: [line('#fbbf24'), line('#8b919e', true), line('#fbbf24')] },
		calc: (dataList: { close: number }[], indicator: { calcParams: number[] }) => {
			const [p, pct] = indicator.calcParams;
			let sum = 0;
			return dataList.map((d, i) => {
				sum += d.close;
				if (i >= p) sum -= dataList[i - p].close;
				if (i < p - 1) return {};
				const mid = sum / p;
				return { mid, up: mid * (1 + pct / 100), lo: mid * (1 - pct / 100) };
			});
		}
	});
}
