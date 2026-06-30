// 경제지표 캔들 오버레이 · Bloomberg식 "보이지 않는 독립축"을 페인 내부에 구현.
//   figures: [] → klinecharts y축 range 계산(figures[].key 만 참조)에 0 기여 = 캔들 스케일 무왜곡.
//   draw: 가시범위 기준 시리즈별 min-max 자기정규화 폴리라인 · 팬/줌마다 자동 re-fit (Bloomberg normalized).
//   tooltip: 리베이스 허구 숫자가 아닌 원시값(1,385원 · 3.50%) 표기.
// 비율 rebase(v/v₀·close₀)는 0 교차 시리즈(T10Y2Y·YoY)에서 수학적으로 붕괴 · 기각 근거.
// 날짜 정렬: 캔들 날짜축에 two-pointer forward-fill (첫 관측 전 = 결측, look-ahead 방지).
import type { MacroPoint, MacroSeriesDef } from '@dartlab/ui-contracts';
import type { Lang } from '../lib/types';

export const ECON_INDICATOR = 'ECON';
// 캔들 상승 #34d399 / 하락 #f0616f / 마커 amber #ec4899 와 충돌하지 않는 고정 팔레트.
export const ECON_COLORS: Record<string, string> = {
	// 한국 (ECOS)
	USDKRW: '#60a5fa',
	JPYKRW: '#5eead4',
	EURKRW: '#7dd3fc',
	BASE_RATE: '#c084fc',
	CPI: '#f472b6',
	EXPORT: '#a3e635',
	EXPORT_PRICE: '#bef264',
	IPI: '#fda4af',
	CLI: '#2dd4bf',
	CSI: '#d8b4fe',
	M2: '#fcd34d',
	HOUSE_PRICE: '#f9a8d4',
	PPI_SEMI: '#6ee7b7',
	PPI_MFG: '#4ade80',
	PPI_CHEM: '#34d3a6',
	PPI_STEEL: '#94d3c0',
	PPI_AUTO: '#a7f3d0',
	PPI_DISPLAY: '#67e8f9',
	PPI_ELEC: '#5eead4',
	PPI_MACHINE: '#7dd3bc',
	PPI_OIL: '#bbf7d0',
	// 미국 (FRED)
	FEDFUNDS: '#38bdf8',
	DGS2: '#a5b4fc',
	DGS10: '#818cf8',
	DGS30: '#c4b5fd',
	T10Y2Y: '#94a3b8',
	T10Y3M: '#cbd5e1',
	T10YIE: '#f0abfc',
	CPIAUCSL: '#e879f9',
	CPILFESL: '#f5d0fe',
	PCEPI: '#ddd6fe',
	UNRATE: '#fde68a',
	PAYEMS: '#86efac',
	INDPRO: '#99f6e4',
	BAMLH0A0HYM2: '#fbcfe8',
	BAA10Y: '#cffafe',
	NFCI: '#e9d5ff',
	DTWEXBGS: '#bae6fd',
	SP500: '#93c5fd',
	NASDAQCOM: '#a78bfa',
	VIXCLS: '#fca5a5',
	DCOILWTICO: '#fed7aa',
	PCOPPUSDM: '#facc15',
	// 국내 시장지수(베타 오버레이) · marketIndex.ts MARKET_INDEX_COLORS 와 일치(amber/orange 시장 톤)
	'idx:KOSPI/코스피': '#fbbf24',
	'idx:KOSDAQ/코스닥': '#fb923c'
};

export interface EconExtend {
	lang: Lang;
	series: { def: MacroSeriesDef; points: MacroPoint[] }[];
}
type EconDatum = Record<string, number>; // seriesId → forward-fill 값. 결측 = 키 없음.

const tsToYmd = (ts: number): string => {
	const d = new Date(ts);
	return `${d.getUTCFullYear()}${String(d.getUTCMonth() + 1).padStart(2, '0')}${String(d.getUTCDate()).padStart(2, '0')}`;
};

const fmt = (v: number, def: MacroSeriesDef): string =>
	`${v.toLocaleString('en-US', { minimumFractionDigits: def.digits ?? 2, maximumFractionDigits: def.digits ?? 2 })}${def.unit === 'pt' ? '' : def.unit}`;

let registered = false;
export function registerEconIndicator(kc: { registerIndicator: (t: unknown) => void }): void {
	if (registered) return;
	registered = true;
	kc.registerIndicator({
		name: ECON_INDICATOR,
		shortName: 'ECON',
		figures: [], // ⛔ 축 range 기여 0 · calcRange 는 figures[].key 만 본다
		calc: (dataList: { timestamp: number }[], indicator: { extendData?: EconExtend | null }): EconDatum[] => {
			const ext = indicator.extendData;
			const out: EconDatum[] = dataList.map(() => ({}));
			if (!ext?.series?.length) return out;
			const ymds = dataList.map((k) => tsToYmd(k.timestamp));
			for (const { def, points } of ext.series) {
				let j = 0;
				let v: number | null = null;
				for (let i = 0; i < out.length; i++) {
					while (j < points.length && points[j].d <= ymds[i]) v = points[j++].v;
					if (v != null) out[i][def.id] = v; // 첫 관측 전 = 결측 (백필 금지)
				}
			}
			return out;
		},
		draw: ({ ctx, indicator, visibleRange, bounding, xAxis }: any): boolean => {
			const ext = indicator.extendData as EconExtend | null;
			const result = indicator.result as EconDatum[];
			if (!ext?.series?.length || !result?.length) return true;
			const from = Math.max(0, visibleRange.from);
			const to = Math.min(result.length, visibleRange.to);
			const padY = bounding.height * 0.08;
			const top = bounding.top + padY;
			const h = bounding.height - padY * 2;
			ctx.save();
			ctx.font = '10px ui-sans-serif, system-ui, sans-serif';
			ctx.textBaseline = 'middle';
			for (const { def } of ext.series) {
				// 관측 정점만 수집 · 월간 forward-fill 의 계단(square wave) 제거. 값이 바뀌는 지점 + 마지막 가시 인덱스를
				// 경사로 연결해 추세선으로 (저빈도 시리즈를 일봉 축에 얹을 때의 표준 표현). 일봉 시리즈는 매 봉 달라 동일 동작.
				const verts: { x: number; v: number }[] = [];
				let lastV: number | null = null;
				let lastX = 0;
				for (let i = from; i < to; i++) {
					const v = result[i]?.[def.id];
					if (v == null) continue;
					lastX = xAxis.convertToPixel(i);
					if (v !== lastV) { verts.push({ x: lastX, v }); lastV = v; }
				}
				if (!verts.length) continue;
				if (lastV != null && verts[verts.length - 1].x !== lastX) verts.push({ x: lastX, v: lastV }); // 현재값까지 평탄 연장
				let lo = Infinity;
				let hi = -Infinity;
				for (const p of verts) { if (p.v < lo) lo = p.v; if (p.v > hi) hi = p.v; }
				const span = hi - lo;
				const yOf = (v: number): number => (span === 0 ? top + h / 2 : top + ((hi - v) / span) * h);
				const color = ECON_COLORS[def.id] ?? '#8b919e';
				ctx.strokeStyle = color;
				ctx.lineWidth = 1.4;
				ctx.setLineDash([]);
				ctx.beginPath();
				verts.forEach((p, k) => (k ? ctx.lineTo(p.x, yOf(p.v)) : ctx.moveTo(p.x, yOf(p.v))));
				ctx.stroke();
				// 선 끝(현재)에 값 라벨 · 정규화 선의 높이가 무슨 값인지 읽히게(주가축 아님을 명시·"보이지 않는 축" → 읽히는 축).
				const tip = verts[verts.length - 1];
				ctx.fillStyle = color;
				ctx.textAlign = 'right';
				ctx.fillText(fmt(tip.v, def), tip.x - 3, yOf(tip.v) - 6);
			}
			ctx.restore();
			return true; // 기본 figure 렌더 생략 (그릴 figure 도 없음)
		},
		createTooltipDataSource: ({ indicator, crosshair }: any) => {
			const ext = indicator.extendData as EconExtend | null;
			const result = indicator.result as EconDatum[];
			const i = crosshair?.dataIndex ?? result.length - 1;
			const values = (ext?.series ?? []).flatMap(({ def }) => {
				const v = result[i]?.[def.id];
				if (v == null) return [];
				const color = ECON_COLORS[def.id] ?? '#8b919e';
				return [{ title: { text: `${ext!.lang === 'en' ? def.en : def.kr} `, color }, value: { text: fmt(v, def), color } }];
			});
			return { name: 'ECON', calcParamsText: '', values, icons: [] };
		}
	});
}
