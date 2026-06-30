// 앵커드 VWAP · 앵커 시점부터 현재까지 (h+l+c)/3 거래량가중 평균 누적선 (기관 평단 추정).
// registerOverlay 기반: 매 paint 재계산이라 앵커 드래그·봉주기 전환·수정주가 토글 자동 추종.
// 측정룰러(MEASURE)도 본 파일 · 2점 구간 Δ가격·%·봉수·일수 즉석 표기, 영속 제외(선택 해제 시 제거).
// 포지션 R:R 도구(positionTool)도 본 파일 · 3점(진입→손절→목표) 리스크/리워드 박스 (TV Long/Short Position).
import { viewCandles, viewIndexOf } from './seriesBus';

export const AVWAP_NAME = 'anchoredVWAP';
export const MEASURE_NAME = 'MEASURE';
export const POSITION_NAME = 'positionTool';
export const TEXT_NAME = 'TEXTNOTE';

let registered = false;
export function registerWorkOverlays(kc: { registerOverlay: (t: unknown) => void }): void {
	if (registered) return;
	registered = true;

	kc.registerOverlay({
		name: AVWAP_NAME,
		totalStep: 2, // 앵커 1점이면 완성
		needDefaultPointFigure: true,
		createPointFigures: ({ overlay, xAxis, yAxis }: any) => {
			const pt = overlay.points?.[0];
			if (pt?.timestamp == null) return [];
			const cs = viewCandles();
			if (!cs.length) return [];
			let i0 = viewIndexOf(pt.timestamp);
			if (i0 == null) {
				// 집계 전환 직후 등 timestamp 불일치 · 앵커 이후 첫 봉으로 근접 스냅
				i0 = cs.findIndex((k) => Date.UTC(+k.t.slice(0, 4), +k.t.slice(4, 6) - 1, +k.t.slice(6, 8)) >= pt.timestamp);
				if (i0 < 0) return [];
			}
			const coords: { x: number; y: number }[] = [];
			let pv = 0;
			let vv = 0;
			let last = 0;
			for (let i = i0; i < cs.length; i++) {
				const k = cs[i];
				pv += ((k.h + k.l + k.c) / 3) * k.v;
				vv += k.v;
				if (!vv) continue;
				last = pv / vv;
				coords.push({ x: xAxis.convertToPixel(i), y: yAxis.convertToPixel(last) });
			}
			if (coords.length < 2) return [];
			const end = coords[coords.length - 1];
			return [
				{ type: 'line', attrs: { coordinates: coords }, styles: { color: '#fbbf24', size: 1.5 } },
				{ type: 'text', attrs: { x: end.x, y: end.y - 4, text: `AVWAP ${Math.round(last).toLocaleString()}`, align: 'right', baseline: 'bottom' }, ignoreEvent: true, styles: { color: '#0b0e14', backgroundColor: '#fbbf24' } }
			];
		}
	});

	kc.registerOverlay({
		name: MEASURE_NAME,
		totalStep: 3, // 2점
		needDefaultPointFigure: true,
		createPointFigures: ({ overlay, coordinates }: any) => {
			if (!coordinates || coordinates.length < 2) return [];
			const [a, b] = coordinates;
			const [pa, pb] = overlay.points ?? [];
			const v0 = pa?.value ?? 0;
			const v1 = pb?.value ?? 0;
			const up = v1 >= v0;
			const pct = v0 ? (v1 / v0 - 1) * 100 : 0;
			const i0 = pa?.timestamp != null ? viewIndexOf(pa.timestamp) : undefined;
			const i1 = pb?.timestamp != null ? viewIndexOf(pb.timestamp) : undefined;
			const bars = i0 != null && i1 != null ? Math.abs(i1 - i0) : null;
			const days = pa?.timestamp != null && pb?.timestamp != null ? Math.round(Math.abs(pb.timestamp - pa.timestamp) / 86400000) : null;
			const col = up ? '#34d399' : '#f0616f';
			const label = `${up ? '+' : ''}${(v1 - v0).toLocaleString(undefined, { maximumFractionDigits: 0 })} (${pct >= 0 ? '+' : ''}${pct.toFixed(2)}%)${bars != null ? ` · ${bars}봉` : ''}${days != null ? ` · ${days}d` : ''}`;
			return [
				{
					type: 'rect',
					attrs: { x: Math.min(a.x, b.x), y: Math.min(a.y, b.y), width: Math.abs(b.x - a.x), height: Math.abs(b.y - a.y) },
					styles: { style: 'stroke_fill', color: up ? 'rgba(52,211,153,0.08)' : 'rgba(240,97,111,0.08)', borderColor: col, borderSize: 1, borderStyle: 'dashed', borderDashedValue: [3, 3] }
				},
				{ type: 'text', attrs: { x: (a.x + b.x) / 2, y: Math.min(a.y, b.y) - 5, text: label, align: 'center', baseline: 'bottom' }, ignoreEvent: true, styles: { color: '#0b0e14', backgroundColor: col } }
			];
		}
	});

	// 텍스트 주석 · 1점 + extendData 문자열. 입력·수정은 PriceChart 인라인 에디터(onDrawEnd/더블클릭 → 팝오버).
	kc.registerOverlay({
		name: TEXT_NAME,
		totalStep: 2, // 1점이면 완성
		needDefaultPointFigure: true,
		createPointFigures: ({ overlay, coordinates }: any) => {
			const c0 = coordinates?.[0];
			if (!c0) return [];
			const t = typeof overlay.extendData === 'string' && overlay.extendData ? overlay.extendData : '…';
			return [{
				type: 'text',
				attrs: { x: c0.x, y: c0.y - 6, text: t, align: 'center', baseline: 'bottom' },
				styles: {
					color: '#fbbf24', size: 12, family: 'var(--mono, monospace)', weight: 600,
					backgroundColor: 'rgba(11,14,20,0.88)', borderColor: 'rgba(251,191,36,0.5)', borderSize: 1, borderRadius: 3,
					paddingLeft: 6, paddingRight: 6, paddingTop: 3, paddingBottom: 3
				}
			}];
		}
	});

	// 롱/숏 포지션 R:R · 진입~손절 = 위험(빨강 반투명), 진입~목표 = 보상(초록 반투명).
	// 라벨 = 롱/숏 + R:R 1:x + 진입/손절/목표 가격. 3점 영속(drawStore 자동 탑승)·드래그 편집 추종.
	kc.registerOverlay({
		name: POSITION_NAME,
		totalStep: 4, // 3점 · 진입·손절·목표
		needDefaultPointFigure: true,
		createPointFigures: ({ overlay, coordinates }: any) => {
			if (!coordinates || coordinates.length < 2) return [];
			const [pe, ps, pt] = overlay.points ?? [];
			const entry = pe?.value;
			const stop = ps?.value;
			const target = pt?.value;
			if (entry == null || stop == null) return [];
			const xs = coordinates.map((c: { x: number }) => c.x);
			const x0 = Math.min(...xs);
			const w = Math.max(Math.max(...xs) - x0, 90); // 점들이 수직으로 겹쳐도 최소 박스 폭 확보
			const yE = coordinates[0].y;
			const yS = coordinates[1].y;
			const fmt = (v: number) => Math.round(v).toLocaleString();
			const box = (yA: number, yB: number, fill: string, border: string) => ({
				type: 'rect',
				attrs: { x: x0, y: Math.min(yA, yB), width: w, height: Math.max(Math.abs(yB - yA), 1) },
				styles: { style: 'stroke_fill', color: fill, borderColor: border, borderSize: 1 }
			});
			const figs: unknown[] = [box(yE, yS, 'rgba(240,97,111,0.12)', 'rgba(240,97,111,0.65)')];
			if (target != null && coordinates.length >= 3) {
				const yT = coordinates[2].y;
				figs.push(box(yE, yT, 'rgba(52,211,153,0.12)', 'rgba(52,211,153,0.65)'));
				const risk = Math.abs(entry - stop);
				const rr = risk > 0 ? Math.abs(target - entry) / risk : null;
				const long = target >= entry;
				figs.push({
					type: 'text',
					attrs: {
						x: x0 + w / 2,
						y: Math.min(yE, yS, yT) - 5,
						text: `${long ? '롱' : '숏'} R:R 1:${rr != null ? rr.toFixed(1) : '·'} · 진입 ${fmt(entry)} · 손절 ${fmt(stop)} · 목표 ${fmt(target)}`,
						align: 'center',
						baseline: 'bottom'
					},
					ignoreEvent: true,
					styles: { color: '#0b0e14', backgroundColor: long ? '#34d399' : '#f0616f' }
				});
			} else {
				figs.push({
					type: 'text',
					attrs: { x: x0 + w / 2, y: Math.min(yE, yS) - 5, text: `진입 ${fmt(entry)} · 손절 ${fmt(stop)} → 목표?`, align: 'center', baseline: 'bottom' },
					ignoreEvent: true,
					styles: { color: '#0b0e14', backgroundColor: '#f0616f' }
				});
			}
			return figs;
		}
	});
}
