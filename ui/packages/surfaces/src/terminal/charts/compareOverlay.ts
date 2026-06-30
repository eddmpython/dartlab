// 종목비교 오버레이 · 피어 종가를 "가시 구간 첫 공통 봉" 기준으로 본주 종가에 리베이스해 캔들 페인에
// 그린다 (HTS 비교차트 동작). figures: [] = y축 range 무왜곡 (econOverlay 패턴).
//   yAxis.convertToPixel(본주기준가 × 피어상대비) 라 일반·로그·% 축 전부 정확 정렬 · % 축 기준점이
//   가시 첫 봉 종가이므로 본주 캔들과 같은 % 자를 공유하고, 팬/줌마다 자동 재기준(구독 불필요).
// 피어 캔들은 호출측이 수정주가 보정을 마친 시계열을 넣는다 · 피어 분할이 상대수익률을 왜곡하지 않게.
import type { Candle } from '@dartlab/ui-contracts';

export const CMP_INDICATOR = 'CMP';
// 캔들 상승/하락·ECON 팔레트와 충돌하지 않는 고정 3색 (compares 상한 3)
export const CMP_COLORS = ['#38bdf8', '#f472b6', '#a3e635'];

export interface CmpExtend {
	peers: { code: string; name: string; candles: Candle[] }[];
}
type CmpDatum = Record<string, number>; // 피어 code → forward-fill 종가. 결측 = 키 없음.

const tsToYmd = (ts: number): string => {
	const d = new Date(ts);
	return `${d.getUTCFullYear()}${String(d.getUTCMonth() + 1).padStart(2, '0')}${String(d.getUTCDate()).padStart(2, '0')}`;
};

let registered = false;
export function registerCmpIndicator(kc: { registerIndicator: (t: unknown) => void }): void {
	if (registered) return;
	registered = true;
	kc.registerIndicator({
		name: CMP_INDICATOR,
		shortName: 'VS',
		figures: [], // ⛔ 축 range 기여 0
		calc: (dataList: { timestamp: number }[], indicator: { extendData?: CmpExtend | null }): CmpDatum[] => {
			const ext = indicator.extendData;
			const out: CmpDatum[] = dataList.map(() => ({}));
			if (!ext?.peers?.length) return out;
			const ymds = dataList.map((k) => tsToYmd(k.timestamp));
			for (const peer of ext.peers) {
				const cs = peer.candles;
				let j = 0;
				let v: number | null = null;
				for (let i = 0; i < out.length; i++) {
					while (j < cs.length && cs[j].t <= ymds[i]) v = cs[j++].c;
					if (v != null) out[i][peer.code] = v; // 첫 관측 전 = 결측 (상장 전 백필 금지)
				}
			}
			return out;
		},
		draw: ({ ctx, indicator, kLineDataList, visibleRange, xAxis, yAxis }: any): boolean => {
			const ext = indicator.extendData as CmpExtend | null;
			const result = indicator.result as CmpDatum[];
			if (!ext?.peers?.length || !result?.length) return true;
			const from = Math.max(0, visibleRange.from);
			const to = Math.min(result.length, visibleRange.to);
			ext.peers.forEach((peer, pi) => {
				// 기준점 = 가시 구간에서 본주·피어 모두 값이 있는 첫 봉
				let a = -1;
				for (let i = from; i < to; i++) {
					if (result[i]?.[peer.code] != null && kLineDataList[i]?.close != null) { a = i; break; }
				}
				if (a < 0) return;
				const v0 = result[a][peer.code];
				const base = kLineDataList[a].close;
				if (!v0 || !base) return;
				ctx.strokeStyle = CMP_COLORS[pi] ?? '#8b919e';
				ctx.lineWidth = 1.5;
				ctx.setLineDash([]);
				ctx.beginPath();
				let started = false;
				for (let i = a; i < to; i++) {
					const v = result[i]?.[peer.code];
					if (v == null) continue;
					const x = xAxis.convertToPixel(i);
					const y = yAxis.convertToPixel(base * (v / v0));
					if (started) ctx.lineTo(x, y);
					else { ctx.moveTo(x, y); started = true; }
				}
				ctx.stroke();
			});
			return true;
		},
		createTooltipDataSource: ({ indicator, crosshair }: any) => {
			const ext = indicator.extendData as CmpExtend | null;
			const result = indicator.result as CmpDatum[];
			const i = crosshair?.dataIndex ?? result.length - 1;
			const values = (ext?.peers ?? []).flatMap((peer, pi) => {
				const v = result[i]?.[peer.code];
				if (v == null) return [];
				const color = CMP_COLORS[pi] ?? '#8b919e';
				return [{ title: { text: `${peer.name} `, color }, value: { text: v.toLocaleString(), color } }];
			});
			return { name: 'VS', calcParamsText: '', values, icons: [] };
		}
	});
}
