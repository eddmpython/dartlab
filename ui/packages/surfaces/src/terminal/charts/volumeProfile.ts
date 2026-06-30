// 매물대 (Volume Profile) · 가시 구간 거래대금(폴백 거래량) 가중 가격대 분포 + POC 수평선.
// registerIndicator figures:[] + draw 전용 (econOverlay 패턴 · 캔들 y축 무왜곡, 줌·스크롤마다
// draw 재호출 = 자동 재계산, 구독 0). 로그축은 convertFrom/ToPixel 이 변환을 흡수한다.
export const VP_INDICATOR = 'VPVR';

const BINS = 24;
const MAX_WIDTH_RATIO = 0.18; // 최대 막대 폭 = 페인 폭의 18% (우측 정렬)

let registered = false;
export function registerVolumeProfile(kc: { registerIndicator: (t: unknown) => void }): void {
	if (registered) return;
	registered = true;
	kc.registerIndicator({
		name: VP_INDICATOR,
		shortName: 'VP',
		series: 'price',
		figures: [],
		calc: (dataList: unknown[]) => dataList.map(() => ({})),
		draw: ({ ctx, kLineDataList, visibleRange, bounding, yAxis }: any): boolean => {
			const from = Math.max(0, visibleRange.from);
			const to = Math.min(kLineDataList.length, visibleRange.to);
			if (to - from < 2) return false;
			const pTop = yAxis.convertFromPixel(0);
			const pBot = yAxis.convertFromPixel(bounding.height);
			const hi = Math.max(pTop, pBot);
			const lo = Math.min(pTop, pBot);
			if (!(hi > lo)) return false;
			const bins = new Array(BINS).fill(0);
			const upBins = new Array(BINS).fill(0);
			for (let i = from; i < to; i++) {
				const k = kLineDataList[i];
				if (!k) continue;
				const px = (k.high + k.low + k.close) / 3;
				if (px < lo || px > hi) continue;
				const w = k.turnover ?? k.volume ?? 0;
				const bi = Math.min(BINS - 1, Math.floor(((px - lo) / (hi - lo)) * BINS));
				bins[bi] += w;
				if (k.close >= k.open) upBins[bi] += w;
			}
			let maxW = 0;
			let pocI = -1;
			for (let i = 0; i < BINS; i++) {
				if (bins[i] > maxW) {
					maxW = bins[i];
					pocI = i;
				}
			}
			if (!maxW) return false;
			const maxPx = bounding.width * MAX_WIDTH_RATIO;
			for (let i = 0; i < BINS; i++) {
				if (!bins[i]) continue;
				const yLo = yAxis.convertToPixel(lo + (i / BINS) * (hi - lo));
				const yHi = yAxis.convertToPixel(lo + ((i + 1) / BINS) * (hi - lo));
				const y = Math.min(yLo, yHi);
				const h = Math.max(1, Math.abs(yLo - yHi) - 1);
				const w = (bins[i] / maxW) * maxPx;
				const upW = w * (upBins[i] / bins[i]);
				const x0 = bounding.width - w;
				ctx.fillStyle = 'rgba(52,211,153,0.18)';
				ctx.fillRect(x0, y, upW, h);
				ctx.fillStyle = 'rgba(240,97,111,0.18)';
				ctx.fillRect(x0 + upW, y, w - upW, h);
			}
			const pocY = yAxis.convertToPixel(lo + ((pocI + 0.5) / BINS) * (hi - lo));
			ctx.strokeStyle = 'rgba(236, 72, 153,0.85)';
			ctx.lineWidth = 1;
			ctx.setLineDash([2, 2]);
			ctx.beginPath();
			ctx.moveTo(bounding.width - maxPx, pocY);
			ctx.lineTo(bounding.width, pocY);
			ctx.stroke();
			ctx.setLineDash([]);
			return false;
		}
	});
}
