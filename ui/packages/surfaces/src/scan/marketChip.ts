/**
 * 시장 구분 (KOSPI / KOSDAQ / KONEX) · 색·라벨 lookup.
 *
 * ecosystem.json 의 노드 `market` 필드 (빌드 시 KRX 데이터 join).
 * 미지정 시 'UNKNOWN' / 회색.
 */

export type Market = 'KOSPI' | 'KOSDAQ' | 'KONEX' | 'UNKNOWN';

export const MARKET_INFO: Record<Market, { color: string; label: string }> = {
	KOSPI: { color: '#3b82f6', label: 'KOSPI' },
	KOSDAQ: { color: '#fbbf24', label: 'KOSDAQ' },
	KONEX: { color: '#94a3b8', label: 'KONEX' },
	UNKNOWN: { color: '#475569', label: '·' }
};

/** 노드의 market 필드를 정규화. 'KOSPI'/'KOSDAQ'/'KONEX' 외엔 'UNKNOWN'.
 *
 * KRX 가 'KOSDAQ GLOBAL' 같은 sub-segment 라벨도 쓰므로 substring 매칭 사용.
 */
export function normalizeMarket(raw: unknown): Market {
	if (typeof raw !== 'string') return 'UNKNOWN';
	const upper = raw.toUpperCase();
	if (upper.includes('KONEX') || upper.includes('코넥스') || upper === 'KNX') return 'KONEX';
	if (upper.includes('KOSDAQ') || upper.includes('코스닥') || upper === 'KSQ') return 'KOSDAQ';
	if (upper.includes('KOSPI') || upper.includes('유가증권') || upper === 'STK') return 'KOSPI';
	return 'UNKNOWN';
}

export function marketColor(raw: unknown): string {
	return MARKET_INFO[normalizeMarket(raw)].color;
}

export function marketLabel(raw: unknown): string {
	return MARKET_INFO[normalizeMarket(raw)].label;
}
