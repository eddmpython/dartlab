// 백테스트 차트 레이어 · klinecharts 커스텀 지표 2종 (단일 draw 가 N개를 직접 그림 · overlay 대량생성 금지).
//   BT_TRADES: candle_pane 매수▲/매도▼ 마커 (N≥2 = 포커스 1전략만, LOD 2단). figures:[] → y축 무왜곡.
//   BT_EQUITY: 서브 페인 다전략 에쿼티 · figures:[] + 신규 공유 절대축 draw.
// ⚠ 공유 절대축(terminal-strategy-lab 01 §1.1): figures:[{eq},{bh}] 의 klinecharts 자동 공유축을
//   figures:[]+draw 로 바꾸면 잃는다 → draw 안에서 전 라인(N전략+combo+B&H) 공통 lo/hi 계산 →
//   bounding 높이에 직접 픽셀 매핑(시작=100 절대값 비교, per-series 정규화 금지). CMP/ECON 엔 없는 신규.
//   combo 거래 부재(01 §1.2) → 거래 KPI 는 UI 에서 "·", 여기선 equity 라인만.
// extendData 로 N슬롯 전달(CMP 패턴) · 모듈 Map 폐기.
import type { Candle } from '@dartlab/ui-contracts';
import type { PortfolioBtResult } from '../lib/backtest';
import type { StrategySlot } from '../lib/backtest';

export const BT_TRADES = 'BT_TRADES';
export const BT_EQUITY = 'BT_EQUITY';
// 전략 슬롯 ≤3 색 (캔들 상승/하락·combo·B&H 와 구분). combo=마젠타, B&H=회색.
// 3번째는 보라(#a78bfa) · 라임(#a3e635)은 손익 초록(--up #34d399)과 혼동돼 제거.
export const STRAT_COLORS = ['#fbbf24', '#38bdf8', '#a78bfa'];
export const COMBO_COLOR = '#e879f9';
export const BH_COLOR = '#8b919e';

export interface BtStrategyVis {
	id: string;
	color: string;
	label: string;
	equity: (number | null)[]; // candles-aligned (extend.ts 와 동일 인덱스)
	trades: { ts: number; side: 'B' | 'S'; px: number; stop: boolean }[];
	// 보유기간 승패 밴드 · 진입~청산(미청산=마지막봉) 구간. 마커가 사라지는 줌아웃에도 읽힘(차트에 직접 '언제 들고 있었고 이겼나').
	holds: { entryTs: number; exitTs: number | null; ret: number; open: boolean }[];
}
export interface BtLayerExtend {
	ts: number[]; // candles timestamps(ms) · equity 배열 인덱스 정렬 + kLineDataList ts 매칭용
	strategies: BtStrategyVis[];
	combo: { equity: (number | null)[]; color: string } | null;
	bh: (number | null)[];
	mdd: { peak: number; recover: number | null } | null; // combo(없으면 포커스) 기준 · 에쿼티 음영
	oosSplitTs: number | null;
	focus: number; // BT_TRADES 마커 포커스 슬롯
	// ★펀더게이트 moat 시각화(W2) · 포커스 전략의 재무 게이트 활성 구간(초록 배경 틴트, 공시일 이후 PIT 계단).
	gate: { active: (0 | 1)[]; label: string } | null; // candles-aligned(ext.ts 정렬). 가격 백테스터가 못 그리는 panel 레이어.
}

type EqRow = { e: (number | null)[]; c: number | null; b: number | null } | null;

const toMs = (t: string) => Date.UTC(+t.slice(0, 4), +t.slice(4, 6) - 1, +t.slice(6, 8));

/** candles ts → equity 인덱스 매핑(extend.ts 기준). */
function tsIndexMap(ext: BtLayerExtend): Map<number, number> {
	const m = new Map<number, number>();
	ext.ts.forEach((t, k) => m.set(t, k));
	return m;
}

let registered = false;
export function registerBtIndicators(kc: { registerIndicator: (t: unknown) => void }): void {
	if (registered) return;
	registered = true;

	kc.registerIndicator({
		name: BT_TRADES,
		shortName: 'BT',
		figures: [],
		calc: (list: { timestamp: number }[]) => list.map(() => ({})),
		draw: ({ ctx, indicator, kLineDataList, visibleRange, barSpace, xAxis, yAxis, bounding }: any): boolean => {
			const ext = indicator.extendData as BtLayerExtend | null;
			// OOS 검증 구간 음영 + 분할선 (배경 → 마커보다 먼저). 분할은 전 슬롯 공통(동일 candles·window·frac).
			if (ext?.oosSplitTs != null && bounding) {
				const f0 = Math.max(0, visibleRange.from);
				const t0 = Math.min(kLineDataList.length, visibleRange.to);
				let splitX = null;
				for (let i = f0; i < t0; i++) { if (kLineDataList[i]?.timestamp >= ext.oosSplitTs) { splitX = xAxis.convertToPixel(i); break; } }
				if (splitX != null) {
					ctx.fillStyle = 'rgba(96,165,250,0.06)';
					ctx.fillRect(splitX, 0, Math.max(1, bounding.width - splitX), bounding.height);
					ctx.save();
					ctx.strokeStyle = 'rgba(96,165,250,0.55)'; ctx.lineWidth = 1; ctx.setLineDash([3, 3]);
					ctx.beginPath(); ctx.moveTo(splitX, 0); ctx.lineTo(splitX, bounding.height); ctx.stroke(); ctx.setLineDash([]);
					ctx.font = '11px monospace';
					ctx.fillStyle = '#8b919e'; ctx.textAlign = 'right'; ctx.fillText('학습', splitX - 4, 13);
					ctx.fillStyle = '#60a5fa'; ctx.textAlign = 'left'; ctx.fillText('검증', splitX + 4, 13);
					ctx.restore();
				}
			}
			if (!ext?.strategies?.length) return true;
			// N≥2 = 포커스 1전략만(클러터 차단). N=1 = 그 전략.
			const s = ext.strategies[ext.focus] ?? ext.strategies[0];
			if (!s) return true;
			// 보유기간 승패 밴드 (배경·LOD 무관) · 진입~청산(미청산=마지막봉) 구간을 승=초록·패=빨강 저알파. 줌아웃에도 '언제 들고 이겼나' 직독.
			if (s.holds?.length && bounding) {
				const idxMap = new Map<number, number>();
				for (let bi = 0; bi < kLineDataList.length; bi++) idxMap.set(kLineDataList[bi].timestamp, bi);
				const vf = Math.max(0, visibleRange.from);
				const lastIdx = Math.min(kLineDataList.length, visibleRange.to) - 1;
				for (const h of s.holds) {
					let ei = idxMap.get(h.entryTs);
					if (ei == null && kLineDataList[vf] && h.entryTs <= kLineDataList[vf].timestamp) ei = vf; // 진입이 창 이전 → 창 시작 클램프
					if (ei == null) continue;
					const xiRaw = h.exitTs != null ? idxMap.get(h.exitTs) : lastIdx;
					const xi = xiRaw == null ? lastIdx : xiRaw;
					const f = Math.max(vf, ei);
					const t = Math.min(lastIdx, xi);
					if (t < f) continue;
					const x0 = xAxis.convertToPixel(f);
					const x1 = xAxis.convertToPixel(t);
					ctx.fillStyle = h.open ? 'rgba(139,145,158,0.05)' : h.ret > 0 ? 'rgba(52,211,153,0.07)' : h.ret < 0 ? 'rgba(240,97,111,0.07)' : 'rgba(139,145,158,0.05)';
					ctx.fillRect(x0, 0, Math.max(1, x1 - x0), bounding.height);
				}
			}
			if (barSpace.bar < 2) return true; // LOD-1: 초줌아웃 = 마커 생략(밴드·에쿼티가 성과 전달)
			// 펀더게이트 배경 틴트(W2 moat) · 재무 게이트 활성 구간 초록(공시일 이후 PIT 계단). 마커보다 먼저(배경).
			if (ext.gate?.active?.length && bounding) {
				const gmap = new Map<number, 0 | 1>();
				ext.ts.forEach((t, k) => gmap.set(t, ext.gate!.active[k] ?? 0));
				const gf = Math.max(0, visibleRange.from);
				const gt = Math.min(kLineDataList.length, visibleRange.to);
				ctx.fillStyle = 'rgba(120,140,170,0.12)'; // 중립 청회 · 손익 초록과 인지 분리(게이트=재무건강 구간, 수익 아님)
				let runX0: number | null = null;
				for (let gi = gf; gi <= gt; gi++) {
					const on = gi < gt && gmap.get(kLineDataList[gi]?.timestamp) === 1;
					if (on && runX0 == null) runX0 = xAxis.convertToPixel(gi);
					else if (!on && runX0 != null) { const gx1 = xAxis.convertToPixel(gi); ctx.fillRect(runX0, 0, Math.max(1, gx1 - runX0), bounding.height); runX0 = null; }
				}
				if (ext.gate.label) { ctx.save(); ctx.font = '11px monospace'; ctx.fillStyle = 'rgba(120,140,170,0.85)'; ctx.textAlign = 'left'; ctx.fillText(String.fromCharCode(9636) + ' ' + ext.gate.label, 6, bounding.height - 6); ctx.restore(); }
			}
			const tmap = new Map(s.trades.map((tr) => [tr.ts, tr]));
			const label = barSpace.bar >= 12 && ext.strategies.length === 1; // LOD-2: 라벨은 단일전략·충분 줌만
			const from = Math.max(0, visibleRange.from);
			const to = Math.min(kLineDataList.length, visibleRange.to);
			ctx.font = '10px monospace'; ctx.textAlign = 'center';
				// 마커 가격 라벨 · 반투명 배경칩으로 캔들 위 대비 확보(가독).
				const labelChip = (txt: string, cx: number, cy: number) => {
					const w = ctx.measureText(txt).width;
					ctx.fillStyle = 'rgba(10,14,21,0.72)';
					ctx.fillRect(cx - w / 2 - 3, cy - 9, w + 6, 12);
					ctx.fillStyle = '#aeb6c2';
					ctx.fillText(txt, cx, cy);
				};
			for (let i = from; i < to; i++) {
				const d = kLineDataList[i];
				const m = tmap.get(d.timestamp);
				if (!m) continue;
				const x = xAxis.convertToPixel(i);
				const sz = 5.5;
				ctx.beginPath();
				if (m.side === 'B') {
					const y = yAxis.convertToPixel(d.low) + 12;
					ctx.fillStyle = s.color;
					ctx.moveTo(x, y - sz); ctx.lineTo(x - sz, y + sz); ctx.lineTo(x + sz, y + sz); ctx.closePath(); ctx.fill();
					if (label) labelChip(m.px.toLocaleString('en-US', { maximumFractionDigits: 0 }), x, y + sz + 12);
				} else {
					const y = yAxis.convertToPixel(d.high) - 12;
					ctx.fillStyle = m.stop ? '#f0616f' : s.color; // 손절 청산은 빨강 구분(P2)
					ctx.moveTo(x, y + sz); ctx.lineTo(x - sz, y - sz); ctx.lineTo(x + sz, y - sz); ctx.closePath(); ctx.fill();
					if (label) labelChip(m.px.toLocaleString('en-US', { maximumFractionDigits: 0 }), x, y - sz - 5);
				}
			}
			return true;
		}
	});

	kc.registerIndicator({
		name: BT_EQUITY,
		shortName: 'BT EQ',
		figures: [], // ⛔ 축 range 기여 0 · 공유 절대축은 draw 가 직접 계산(§1.1)
		calc: (dataList: { timestamp: number }[], indicator: { extendData?: BtLayerExtend | null }): EqRow[] => {
			const ext = indicator.extendData;
			const out: EqRow[] = dataList.map(() => null);
			if (!ext?.strategies?.length) return out;
			const idx = tsIndexMap(ext);
			for (let i = 0; i < dataList.length; i++) {
				const k = idx.get(dataList[i].timestamp);
				if (k == null) continue;
				out[i] = {
					e: ext.strategies.map((s) => s.equity[k] ?? null),
					c: ext.combo ? ext.combo.equity[k] ?? null : null,
					b: ext.bh[k] ?? null
				};
			}
			return out;
		},
		draw: ({ ctx, indicator, visibleRange, xAxis, bounding }: any): boolean => {
			const ext = indicator.extendData as BtLayerExtend | null;
			const result = indicator.result as EqRow[];
			if (!ext?.strategies?.length || !result?.length) return true;
			const from = Math.max(0, visibleRange.from);
			const to = Math.min(result.length, visibleRange.to);
			const H = bounding.height;
			const padY = 8;

			// 1. 공유 절대축 · 가시구간 전 라인(N전략+combo+B&H) 공통 lo/hi (per-series 정규화 금지, 절대수익 비교)
			let lo = Infinity; let hi = -Infinity;
			for (let i = from; i < to; i++) {
				const r = result[i]; if (!r) continue;
				for (const v of r.e) if (v != null) { if (v < lo) lo = v; if (v > hi) hi = v; }
				if (r.c != null) { if (r.c < lo) lo = r.c; if (r.c > hi) hi = r.c; }
				if (r.b != null) { if (r.b < lo) lo = r.b; if (r.b > hi) hi = r.b; }
			}
			if (!Number.isFinite(lo) || !Number.isFinite(hi) || hi <= lo) return true;
			const yOf = (v: number) => padY + (H - 2 * padY) * (1 - (v - lo) / (hi - lo));

			// 2. 수중(underwater) 연속 음영 · 포커스 전략 고점(high-water mark) 대비 하락분을 equity 라인 아래 채움.
			//    (이전: 최악 1구간 full-height 음영 → 연속 수중으로 교체. 깊이뿐 아니라 '물밑에 얼마나 오래' 머물렀는지를
			//     차트에서 직접 읽힘. 공유 절대축 위 · 고점/equity 모두 같은 axis 값이라 스케일 충돌 0. focus 1전략만 클러터 차단.)
			{
				const fi = ext.focus;
				const peakAt: (number | null)[] = new Array(to).fill(null);
				let pk = -Infinity;
				for (let i = 0; i < to; i++) {
					const v = result[i]?.e[fi] ?? null;
					if (v != null) { if (v > pk) pk = v; peakAt[i] = pk; }
				}
				ctx.save();
				ctx.beginPath();
				let started = false;
				for (let i = from; i < to; i++) {
					const p = peakAt[i]; const v = result[i]?.e[fi] ?? null;
					if (p == null || v == null) continue;
					const x = xAxis.convertToPixel(i); const y = yOf(p);
					if (!started) { ctx.moveTo(x, y); started = true; } else ctx.lineTo(x, y);
				}
				if (started) {
					for (let i = to - 1; i >= from; i--) {
						const v = result[i]?.e[fi] ?? null;
						if (v == null) continue;
						ctx.lineTo(xAxis.convertToPixel(i), yOf(v));
					}
					ctx.closePath();
					ctx.fillStyle = 'rgba(240,97,111,0.12)'; // 하락 빨강 저알파 · equity 라인 아래 수중 영역
					ctx.fill();
					// 고점 라인(수중 기준선) · 아주 연한 빨강 점선
					ctx.strokeStyle = 'rgba(240,97,111,0.28)'; ctx.lineWidth = 1; ctx.setLineDash([2, 3]);
					ctx.beginPath();
					let s2 = false;
					for (let i = from; i < to; i++) {
						const p = peakAt[i]; if (p == null) continue;
						const x = xAxis.convertToPixel(i); const y = yOf(p);
						if (!s2) { ctx.moveTo(x, y); s2 = true; } else ctx.lineTo(x, y);
					}
					ctx.stroke(); ctx.setLineDash([]);
				}
				ctx.restore();
			}

			// 2.5 B&H 대비 초과 음영 · 포커스 전략과 B&H 라인 사이 영역(최종 초과 부호로 틴트). 끝점 %p 를 시계열 면적으로(시장 대비 앞/뒤).
			{
				const fi = ext.focus;
				let lastS: number | null = null;
				let lastB: number | null = null;
				for (let i = to - 1; i >= from; i--) {
					const r = result[i];
					if (!r) continue;
					if (lastS == null && r.e[fi] != null) lastS = r.e[fi];
					if (lastB == null && r.b != null) lastB = r.b;
					if (lastS != null && lastB != null) break;
				}
				if (lastS != null && lastB != null) {
					ctx.beginPath();
					let st = false;
					for (let i = from; i < to; i++) {
						const r = result[i];
						if (!r || r.e[fi] == null) continue;
						const x = xAxis.convertToPixel(i);
						const y = yOf(r.e[fi]!);
						if (!st) { ctx.moveTo(x, y); st = true; } else ctx.lineTo(x, y);
					}
					if (st) {
						for (let i = to - 1; i >= from; i--) {
							const r = result[i];
							if (!r || r.b == null) continue;
							ctx.lineTo(xAxis.convertToPixel(i), yOf(r.b!));
						}
						ctx.closePath();
						ctx.fillStyle = lastS >= lastB ? 'rgba(52,211,153,0.06)' : 'rgba(167,139,250,0.07)'; // 우위=초록·열위=보라(수중 낙폭 빨강과 분리)
						ctx.fill();
					}
				}
			}

			// 3. 100 기준선(시작=100 → 손익분기) · 가시범위 안일 때만
			if (lo <= 100 && hi >= 100) {
				ctx.save(); ctx.strokeStyle = 'rgba(139,145,158,0.25)'; ctx.lineWidth = 1; ctx.setLineDash([2, 3]);
				const y100 = yOf(100); ctx.beginPath(); ctx.moveTo(0, y100); ctx.lineTo(bounding.width, y100); ctx.stroke(); ctx.setLineDash([]); ctx.restore();
			}

			const polyline = (pick: (r: NonNullable<EqRow>) => number | null, color: string, width: number, dash: boolean) => {
				ctx.strokeStyle = color; ctx.lineWidth = width; ctx.setLineDash(dash ? [4, 4] : []);
				ctx.beginPath();
				let started = false;
				for (let i = from; i < to; i++) {
					const r = result[i]; if (!r) continue;
					const v = pick(r); if (v == null) continue;
					const x = xAxis.convertToPixel(i); const y = yOf(v);
					if (started) ctx.lineTo(x, y); else { ctx.moveTo(x, y); started = true; }
				}
				ctx.stroke(); ctx.setLineDash([]);
			};

			// 4. B&H 회색 점선 (맨 아래)
			polyline((r) => r.b, BH_COLOR, 1, true);
			// 5. 전략 N (포커스는 약간 굵게)
			ext.strategies.forEach((s, si) => polyline((r) => r.e[si] ?? null, s.color, si === ext.focus ? 1.7 : 1.2, false));
			// 6. combo 굵게 (맨 위)
			if (ext.combo) polyline((r) => r.c, ext.combo.color, 2.3, false);

			// 7. 범례 (좌상단) · 전략 라벨 + 마지막 값
			ctx.font = '11px monospace'; ctx.textAlign = 'left';
			let ly = 13;
			const lastOf = (pick: (r: NonNullable<EqRow>) => number | null): number | null => {
				for (let i = to - 1; i >= from; i--) { const r = result[i]; if (r) { const v = pick(r); if (v != null) return v; } }
				return null;
			};
			const legend = (color: string, text: string, v: number | null) => {
				ctx.fillStyle = color;
				ctx.fillText(`${text}${v != null ? ' ' + (v - 100 >= 0 ? '+' : '') + (v - 100).toFixed(1) + '%' : ''}`, 6, ly);
				ly += 13;
			};
			if (ext.combo) legend(ext.combo.color, '조합', lastOf((r) => r.c));
			ext.strategies.forEach((s, si) => legend(s.color, s.label, lastOf((r) => r.e[si] ?? null)));
			legend(BH_COLOR, 'B&H', lastOf((r) => r.b));
			return true;
		}
	});
}

/** PortfolioBtResult + 슬롯 메타 → extendData 페이로드 (null = 해제). */
export function buildBtExtend(
	pf: PortfolioBtResult | null,
	candles: Candle[],
	slots: StrategySlot[],
	focus: number,
	gate: { active: (0 | 1)[]; label: string } | null = null
): BtLayerExtend | null {
	if (!pf || !pf.slots.length || !candles.length) return null;
	const metaById = new Map(slots.map((s) => [s.id, s]));
	const strategies: BtStrategyVis[] = pf.slots.map(({ id, result }, si) => {
		const meta = metaById.get(id);
		const trades: BtStrategyVis['trades'] = [];
		const holds: BtStrategyVis['holds'] = [];
		for (const tr of result.trades) {
			trades.push({ ts: toMs(tr.entryT), side: 'B', px: tr.entryPx, stop: false });
			// 손절 청산(exitReason='stop')은 빨강 마커로 구분(S2). take/signal/finalMark 는 전략색.
			if (tr.exitT && tr.exitPx != null) trades.push({ ts: toMs(tr.exitT), side: 'S', px: tr.exitPx, stop: tr.exitReason === 'stop' });
			holds.push({ entryTs: toMs(tr.entryT), exitTs: tr.exitT ? toMs(tr.exitT) : null, ret: tr.retPct, open: tr.open });
		}
		return { id, color: meta?.color ?? STRAT_COLORS[si % STRAT_COLORS.length], label: meta?.label ?? `전략${si + 1}`, equity: result.equity, trades, holds };
	});
	// MDD 음영 = combo 우선, 없으면 포커스 슬롯
	const ddSrc = pf.combo?.mddWindow ?? pf.slots[Math.min(focus, pf.slots.length - 1)]?.result.mddWindow ?? null;
	const mdd = ddSrc && candles[ddSrc.peakIdx]
		? { peak: toMs(candles[ddSrc.peakIdx].t), recover: ddSrc.recoverIdx != null && candles[ddSrc.recoverIdx] ? toMs(candles[ddSrc.recoverIdx].t) : null }
		: null;
	const oos = pf.slots[0]?.result.oos;
	return {
		ts: candles.map((c) => toMs(c.t)),
		strategies,
		combo: pf.combo ? { equity: pf.combo.equity, color: COMBO_COLOR } : null,
		bh: pf.bhEquity,
		mdd,
		oosSplitTs: oos ? toMs(oos.splitT) : null,
		focus: Math.min(Math.max(0, focus), Math.max(0, pf.slots.length - 1)),
		gate
	};
}

const created = new WeakMap<object, boolean>();

/** 지표 2종 생성(미존재 시) + extendData 신참조로 재계산 트리거(CMP 식). ext=null 도 전달(빈 그림). */
export function applyBt(chart: any, ext: BtLayerExtend | null): void {
	if (!created.get(chart)) {
		const a = chart.createIndicator({ name: BT_TRADES }, true, { id: 'candle_pane' });
		const b = chart.createIndicator({ name: BT_EQUITY }, false, { id: 'pane_BT', height: 108, minHeight: 72, dragEnabled: true });
		created.set(chart, !!(a || b));
	}
	try {
		chart.overrideIndicator({ name: BT_TRADES, extendData: ext }, 'candle_pane');
		chart.overrideIndicator({ name: BT_EQUITY, extendData: ext }, 'pane_BT');
	} catch { /* */ }
}

/** 지표 2종 제거. */
export function clearBt(chart: any): void {
	if (!created.get(chart)) return;
	created.delete(chart);
	try { chart.removeIndicator('candle_pane', BT_TRADES); } catch { /* */ }
	try { chart.removeIndicator('pane_BT', BT_EQUITY); } catch { /* */ }
}
