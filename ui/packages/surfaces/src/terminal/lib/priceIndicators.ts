// 주가 + 보조지표 · OHLCV raw 에 indicators.ts(SSOT)로 MA·RSI·MACD·볼린저·거래량이평·ATR 컬럼을 더한다.
// 데이터센터(다운로드·라이브 API)와 워커(라이브 변환 CSV)가 공유. 브라우저·워커 동일 변환, 베이크 0.
import { sma, rsi, macd, bollinger, atr, volSma } from './indicators';

const n = (v: unknown): number => {
	const x = Number(v);
	return Number.isFinite(x) ? x : NaN;
};
const r2 = (v: number | null | undefined): number | null =>
	v == null || !Number.isFinite(v) ? null : Math.round(v * 100) / 100;

// 출력 컬럼 순서(헤더 SSOT) · raw OHLCV 다음 지표.
export const PRICE_IND_COLS = [
	'date', 'name', 'close', 'volume',
	'MA5', 'MA20', 'MA60', 'RSI14', 'MACD', 'MACD_signal', 'MACD_hist',
	'BB_mid', 'BB_upper', 'BB_lower', 'VolMA20', 'ATR14'
];

export function priceWithIndicators(rows: Record<string, unknown>[]): Record<string, unknown>[] {
	if (!rows.length) return [];
	const close = rows.map((r) => n(r.close));
	const high = rows.map((r) => n(r.high));
	const low = rows.map((r) => n(r.low));
	const vol = rows.map((r) => n(r.volume));
	const ma5 = sma(close, 5), ma20 = sma(close, 20), ma60 = sma(close, 60);
	const r14 = rsi(close, 14);
	const m = macd(close);
	const bb = bollinger(close, 20, 2);
	const vma = volSma(vol, 20);
	const a14 = atr(high, low, close, 14);
	return rows.map((row, i) => ({
		date: row.date,
		name: row.name ?? '',
		close: row.close,
		volume: row.volume,
		MA5: r2(ma5[i]),
		MA20: r2(ma20[i]),
		MA60: r2(ma60[i]),
		RSI14: r2(r14[i]),
		MACD: r2(m.line[i]),
		MACD_signal: r2(m.signal[i]),
		MACD_hist: r2(m.hist[i]),
		BB_mid: r2(bb.mid[i]),
		BB_upper: r2(bb.upper[i]),
		BB_lower: r2(bb.lower[i]),
		VolMA20: r2(vma[i]),
		ATR14: r2(a14[i])
	}));
}

// 단일 값 시계열(경제지표·지수)용 · value 컬럼에 MA·RSI·MACD·볼린저. 고저·거래량이 없어 ATR·스토캐스틱·거래량이평은 제외.
export const VALUE_IND_COLS = ['date', 'value', 'MA5', 'MA20', 'MA60', 'RSI14', 'MACD', 'MACD_signal', 'MACD_hist', 'BB_mid', 'BB_upper', 'BB_lower'];
export function valueWithIndicators(rows: Record<string, unknown>[], valueCol: string, dateCol: string): Record<string, unknown>[] {
	if (!rows.length) return [];
	const v = rows.map((r) => n(r[valueCol]));
	const ma5 = sma(v, 5), ma20 = sma(v, 20), ma60 = sma(v, 60);
	const r14 = rsi(v, 14);
	const m = macd(v);
	const bb = bollinger(v, 20, 2);
	return rows.map((row, i) => ({
		date: row[dateCol],
		value: row[valueCol],
		MA5: r2(ma5[i]),
		MA20: r2(ma20[i]),
		MA60: r2(ma60[i]),
		RSI14: r2(r14[i]),
		MACD: r2(m.line[i]),
		MACD_signal: r2(m.signal[i]),
		MACD_hist: r2(m.hist[i]),
		BB_mid: r2(bb.mid[i]),
		BB_upper: r2(bb.upper[i]),
		BB_lower: r2(bb.lower[i])
	}));
}
