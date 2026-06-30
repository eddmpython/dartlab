// 차트 적용 시계열 버스 · PriceChart.reapply() 가 publish, AVWAP·측정룰러 overlay 가 구독.
// 보정(수정주가)·집계(주/월봉) 후 시리즈라 토글·전환을 자동 추종. btLayer publishBt 와 동일 패턴.
import type { Candle } from '@dartlab/ui-contracts';

let view: Candle[] = [];
let idxByTs = new Map<number, number>();

/** 차트에 적용된 표시 시계열 발행 · toMs 는 PriceChart 의 타임스탬프 변환과 동일해야 한다. */
export function publishView(candles: Candle[], toMs: (t: string) => number): void {
	view = candles;
	idxByTs = new Map();
	for (let i = 0; i < candles.length; i++) idxByTs.set(toMs(candles[i].t), i);
}

/** 현재 표시 시계열 (오름차순). */
export function viewCandles(): Candle[] {
	return view;
}

/** timestamp → 표시 시계열 인덱스. 정확 일치 없으면 undefined. */
export function viewIndexOf(ts: number): number | undefined {
	return idxByTs.get(ts);
}
